from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.config import ADMIN_IDS
from src.db.session import async_session
from src.db import repositories as repo
from src.handlers.user import _event_label

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


class AddEventFlow(StatesGroup):
    enter_name = State()
    enter_date = State()
    enter_time = State()
    enter_location = State()


class BlockFlow(StatesGroup):
    enter_id = State()


class UnblockFlow(StatesGroup):
    enter_id = State()


class RemoveEventFlow(StatesGroup):
    select_event = State()


@router.message(Command("admin"))
@router.message(F.text == "🔧 תפריט מנהל")
async def admin_menu(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ אין לך הרשאות מנהל.")
        return
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ הוספת אירוע", callback_data="admin_addevent")],
        [InlineKeyboardButton(text="🗑 הסרת אירוע", callback_data="admin_removeevent")],
        [InlineKeyboardButton(text="🚫 חסימת משתמש", callback_data="admin_block")],
        [InlineKeyboardButton(text="🔓 שחרור חסימה", callback_data="admin_unblock")],
    ])
    await message.answer("🔧 <b>תפריט מנהל:</b>", reply_markup=keyboard)


# --- Admin menu callbacks ---

@router.callback_query(F.data == "admin_addevent")
async def admin_add_event_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ אין לך הרשאות מנהל.", show_alert=True)
        return
    await callback.message.edit_text("📝 הזינו את <b>שם האירוע</b>:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(AddEventFlow.enter_name)
    await callback.answer()


@router.callback_query(F.data == "admin_removeevent")
async def admin_remove_event_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ אין לך הרשאות מנהל.", show_alert=True)
        return

    async with async_session() as session:
        active_events = await repo.get_active_events(session)

    if not active_events:
        await callback.message.edit_text("אין אירועים פעילים.")
        await callback.answer()
        return

    keyboard = []
    for event in active_events:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"rmev_{event.id}")])

    await callback.message.edit_text("🗑 בחרו אירוע להסרה:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(RemoveEventFlow.select_event)
    await callback.answer()


@router.callback_query(F.data == "admin_block")
async def admin_block_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ אין לך הרשאות מנהל.", show_alert=True)
        return
    await callback.message.edit_text("🚫 שלחו את <b>מזהה הטלגרם</b> (Telegram ID) של המשתמש לחסימה:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(BlockFlow.enter_id)
    await callback.answer()


@router.callback_query(F.data == "admin_unblock")
async def admin_unblock_cb(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ אין לך הרשאות מנהל.", show_alert=True)
        return
    await callback.message.edit_text("🔓 שלחו את <b>מזהה הטלגרם</b> (Telegram ID) של המשתמש לשחרור:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(UnblockFlow.enter_id)
    await callback.answer()


# --- Add Event flow ---

@router.message(Command("addevent"))
async def admin_add_event_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ אין לך הרשאות מנהל.")
        return
    await message.answer("📝 הזינו את <b>שם האירוע</b>:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(AddEventFlow.enter_name)


@router.message(AddEventFlow.enter_name)
async def add_event_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("🗓 הזינו את <b>תאריך האירוע</b> (לדוגמה: 15/03/2026):")
    await state.set_state(AddEventFlow.enter_date)


@router.message(AddEventFlow.enter_date)
async def add_event_date(message: Message, state: FSMContext):
    await state.update_data(date=message.text)
    await message.answer("🕐 הזינו <b>שעה</b> (לדוגמה: 20:00):")
    await state.set_state(AddEventFlow.enter_time)


@router.message(AddEventFlow.enter_time)
async def add_event_time(message: Message, state: FSMContext):
    await state.update_data(time=message.text)
    await message.answer("📍 הזינו <b>מיקום</b> (או שלחו 'דלג'):")
    await state.set_state(AddEventFlow.enter_location)


@router.message(AddEventFlow.enter_location)
async def add_event_location(message: Message, state: FSMContext):
    location = message.text
    if location in ("דלג", "skip", "-"):
        location = None

    data = await state.get_data()

    async with async_session() as session:
        event_id = await repo.add_event(session, data["name"], data["date"], data["time"], location)

    await message.answer(
        f"✅ האירוע נוסף בהצלחה!\n\n"
        f"📅 {data['name']}\n"
        f"🗓 {data['date']}\n"
        f"🕐 {data['time']}\n"
        f"📍 {location or 'לא צוין'}\n"
        f"🆔 מזהה: {event_id}"
    )
    await state.clear()


# --- Remove Event flow ---

@router.message(Command("removeevent"))
async def admin_remove_event_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ אין לך הרשאות מנהל.")
        return

    async with async_session() as session:
        active_events = await repo.get_active_events(session)

    if not active_events:
        await message.answer("אין אירועים פעילים.")
        return

    keyboard = []
    for event in active_events:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"rmev_{event.id}")])

    await message.answer("🗑 בחרו אירוע להסרה:", reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await state.set_state(RemoveEventFlow.select_event)


@router.callback_query(RemoveEventFlow.select_event, F.data.startswith("rmev_"))
async def remove_event_selected(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        event = await repo.get_event(session, event_id)
        await repo.remove_event(session, event_id)

    await callback.message.edit_text(f"✅ האירוע <b>{event.name}</b> הוסר.")
    await state.clear()
    await callback.answer()


# --- Block / Unblock ---

@router.message(Command("blockuser"))
async def admin_block_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ אין לך הרשאות מנהל.")
        return
    await message.answer("🚫 שלחו את <b>מזהה הטלגרם</b> (Telegram ID) של המשתמש לחסימה:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(BlockFlow.enter_id)


@router.message(BlockFlow.enter_id)
async def block_user_id(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ מזהה לא תקין. שלחו מספר בלבד.")
        return

    async with async_session() as session:
        await repo.block_user(session, target_id)

    await message.answer(f"✅ המשתמש {target_id} נחסם בהצלחה.")
    await state.clear()


@router.message(Command("unblockuser"))
async def admin_unblock_cmd(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ אין לך הרשאות מנהל.")
        return
    await message.answer("🔓 שלחו את <b>מזהה הטלגרם</b> (Telegram ID) של המשתמש לשחרור:\n\nאו לחצו ❌ ביטול.")
    await state.set_state(UnblockFlow.enter_id)


@router.message(UnblockFlow.enter_id)
async def unblock_user_id(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ מזהה לא תקין. שלחו מספר בלבד.")
        return

    async with async_session() as session:
        await repo.unblock_user(session, target_id)

    await message.answer(f"✅ המשתמש {target_id} שוחרר מחסימה.")
    await state.clear()


# --- Cancel (shared) ---

@router.message(Command("cancel"))
@router.message(F.text == "❌ ביטול")
@router.message(F.text == "❌ ביטול וחזרה להתחלה")
async def cancel(message: Message, state: FSMContext):
    from src.handlers.user import get_main_keyboard
    await state.clear()
    keyboard = get_main_keyboard(message.from_user.id)
    await message.answer("❌ הפעולה בוטלה. חזרת לתפריט הראשי.", reply_markup=keyboard)
