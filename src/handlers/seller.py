import logging
import re
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.db.session import async_session
from src.db import repositories as repo
from src.handlers.user import is_blocked, ensure_user, _event_label

logger = logging.getLogger(__name__)
router = Router()


class SellFlow(StatesGroup):
    select_event = State()
    enter_section = State()
    enter_quantity = State()
    enter_price = State()
    enter_phone = State()


@router.message(Command("sell"))
@router.message(F.text == "💰 פרסום כרטיס")
@router.message(F.text == "💰 פרסום כרטיס למכירה")
async def sell_start(message: Message, state: FSMContext):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    async with async_session() as session:
        active_events = await repo.get_active_events(session)

    if not active_events:
        await message.answer("אין אירועים זמינים כרגע.")
        return

    keyboard = []
    for event in active_events:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"sell_{event.id}")])

    await message.answer(
        "🎫 <b>פרסום כרטיס למכירה</b>\nבחרו את האירוע:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await state.set_state(SellFlow.select_event)


@router.callback_query(SellFlow.select_event, F.data.startswith("sell_"))
async def sell_event_selected(callback: CallbackQuery, state: FSMContext):
    event_id = int(callback.data.split("_")[1])
    await state.update_data(event_id=event_id)

    async with async_session() as session:
        event = await repo.get_event(session, event_id)

    await callback.message.edit_text(
        f"📅 אירוע: <b>{event.name}</b>\n\n🏟 הזינו <b>אזור / יציע</b>:",
    )
    await state.set_state(SellFlow.enter_section)
    await callback.answer()


@router.message(SellFlow.enter_section)
async def sell_section(message: Message, state: FSMContext):
    await state.update_data(section=message.text)
    await message.answer("🎫 הזינו <b>כמות כרטיסים</b>:")
    await state.set_state(SellFlow.enter_quantity)


@router.message(SellFlow.enter_quantity)
async def sell_quantity(message: Message, state: FSMContext):
    await state.update_data(quantity=message.text)
    await message.answer("💰 הזינו <b>מחיר</b> (עלות בלבד):")
    await state.set_state(SellFlow.enter_price)


@router.message(SellFlow.enter_price)
async def sell_price(message: Message, state: FSMContext):
    await state.update_data(price=message.text)
    await message.answer("📞 הזינו <b>מספר טלפון</b> ליצירת קשר:")
    await state.set_state(SellFlow.enter_phone)


def _is_valid_phone(phone: str) -> bool:
    """Validate Israeli phone number: 05X-XXXXXXX (10 digits, with optional dashes/spaces)."""
    digits = re.sub(r"[\s\-]", "", phone)
    return bool(re.fullmatch(r"05\d{8}", digits))


@router.message(SellFlow.enter_phone)
async def sell_phone(message: Message, state: FSMContext, bot: Bot):
    if not _is_valid_phone(message.text):
        await message.answer(
            "❌ מספר טלפון לא תקין.\n"
            "יש להזין מספר ישראלי בפורמט: <b>05X-XXXXXXX</b>\n"
            "לדוגמה: 050-1234567"
        )
        return

    data = await state.get_data()
    phone = message.text
    event_id = data["event_id"]
    section = data["section"]
    quantity = data["quantity"]
    price = data["price"]
    seller_id = message.from_user.id

    async with async_session() as session:
        event = await repo.get_event(session, event_id)
        description = f"אזור / יציע: {section}\nכמות: {quantity}\nמחיר: {price}\nטלפון: {phone}"
        ticket_id = await repo.add_ticket(session, event_id, seller_id, description)
        registered_users = await repo.get_registered_users(session, event_id)

    seller_name = message.from_user.first_name or message.from_user.username or "משתמש"
    seller_handle = f"@{message.from_user.username}" if message.from_user.username else seller_name

    delete_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 מחיקת כרטיס (מצאתי קונה)", callback_data=f"delticket_{ticket_id}")]
    ])
    await message.answer(
        f"✅ הכרטיס פורסם בהצלחה!\n\n"
        f"📅 {event.name}\n"
        f"🏟 אזור / יציע: {section}\n"
        f"🎫 כמות: {quantity}\n"
        f"💰 מחיר: {price}\n"
        f"📞 טלפון: {phone}\n\n"
        "ההתראה נשלחת כעת לכל הרשומים.\n"
        "מצאת קונה? לחצו על הכפתור למטה למחיקת הכרטיס.",
        reply_markup=delete_button,
    )

    alert_text = (
        f"🚨 <b>כרטיס חדש זמין!</b>\n\n"
        f"📅 אירוע: <b>{event.name}</b>\n"
        f"🗓 תאריך: {event.date}\n"
        f"🕐 שעה: {event.time or 'לא צוין'}\n"
        f"🏟 אזור / יציע: {section}\n"
        f"🎫 כמות: {quantity}\n"
        f"💰 מחיר: {price}\n"
        f"📞 טלפון: {phone}\n\n"
        f"👤 מוכר: {seller_handle}\n\n"
        "צרו קשר ישירות עם המוכר!"
    )

    sent_count = 0
    for user_id in registered_users:
        if user_id == seller_id:
            continue
        async with async_session() as session:
            if await repo.is_blocked(session, user_id):
                continue
        try:
            await bot.send_message(user_id, alert_text)
            sent_count += 1
        except Exception as e:
            logger.warning(f"Failed to send alert to {user_id}: {e}")

    logger.info(f"Ticket #{ticket_id} alert sent to {sent_count} users for event {event.name}")
    await state.clear()


@router.callback_query(F.data.startswith("delticket_"))
async def delete_ticket(callback: CallbackQuery, bot: Bot):
    ticket_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        ticket = await repo.get_ticket(session, ticket_id)

        if not ticket:
            await callback.message.edit_text("הכרטיס כבר נמחק.")
            await callback.answer()
            return

        if ticket.seller_telegram_id != callback.from_user.id:
            await callback.answer("רק המוכר יכול למחוק את הכרטיס.", show_alert=True)
            return

        event = await repo.get_event(session, ticket.event_id)
        registered_users = await repo.get_registered_users(session, ticket.event_id)
        await repo.delete_ticket(session, ticket_id)

    await callback.message.edit_text("✅ הכרטיס נמחק בהצלחה.")
    await callback.answer()

    seller_name = callback.from_user.first_name or callback.from_user.username or "משתמש"
    notice_text = (
        f"📢 <b>כרטיס נמכר</b>\n\n"
        f"📅 אירוע: <b>{event.name}</b>\n"
        f"👤 מוכר: {seller_name}\n\n"
        "הכרטיס כבר לא זמין."
    )

    for user_id in registered_users:
        if user_id == callback.from_user.id:
            continue
        try:
            await bot.send_message(user_id, notice_text)
        except Exception as e:
            logger.warning(f"Failed to send delete notice to {user_id}: {e}")


@router.message(Command("mytickets"))
@router.message(F.text == "🎟 הכרטיסים שלי")
async def my_tickets(message: Message):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    async with async_session() as session:
        tickets = await repo.get_seller_tickets(session, message.from_user.id)

    if not tickets:
        await message.answer("אין לך כרטיסים מפורסמים כרגע.")
        return

    lines = ["🎟 <b>הכרטיסים שלי:</b>\n"]
    keyboard = []
    for t in tickets:
        lines.append(
            f"━━━━━━━━━━━━━━━\n"
            f"📅 {t['event_name']}\n"
            f"{t['description']}"
        )
        keyboard.append([InlineKeyboardButton(text=f"🗑 מחק — {t['event_name'][:30]}", callback_data=f"delticket_{t['id']}")])
    lines.append("━━━━━━━━━━━━━━━")

    await message.answer(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
