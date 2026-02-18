from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command

from src.config import ADMIN_IDS
from src.db.session import async_session
from src.db import repositories as repo

router = Router()


def get_main_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton(text="🔎 מחפש כרטיס"), KeyboardButton(text="💰 מוכר כרטיס")],
        [KeyboardButton(text="📋 אירועים שנרשמתי להתראות"), KeyboardButton(text="🎟 כרטיסים שפרסמתי")],
        [KeyboardButton(text="🔧 תפריט מנהל"), KeyboardButton(text="❓ עזרה"), KeyboardButton(text="❌ ביטול")] if user_id in ADMIN_IDS
        else [KeyboardButton(text="❓ עזרה"), KeyboardButton(text="❌ ביטול")],
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


async def ensure_user(telegram_id: int, username: str | None, first_name: str | None):
    async with async_session() as session:
        await repo.upsert_user(session, telegram_id, username, first_name)


async def is_blocked(telegram_id: int) -> bool:
    async with async_session() as session:
        return await repo.is_blocked(session, telegram_id)


@router.message(Command("start"))
async def start(message: Message):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)
    keyboard = get_main_keyboard(message.from_user.id)
    first_name = message.from_user.first_name or "אורח/ת"
    await message.answer(
        f"🎟 <b>היי {first_name}, ברוכים הבאים ל-TickAlert!</b>\n\n"
        "הבוט עוזר לכם <b>למצוא ולמכור כרטיסים</b> למשחקי ביתר ירושלים.\n"
        "הירשמו לאירוע — וקבלו התראה מיידית כשכרטיס מתפנה!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚽ <b>מה אפשר לעשות כאן?</b>\n\n"
        "💰 <b>מוכר כרטיס</b> — פרסמו כרטיס למכירה\n"
        "🔎 <b>מחפש כרטיס</b> — צפו באירועים והירשמו להתראות\n"
        "📋 <b>האירועים שלי</b> — האירועים שנרשמתם אליהם\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>איך זה עובד?</b>\n\n"
        "1. לחצו על <b>מחפש כרטיס</b> ובחרו אירוע\n"
        "2. הירשמו לקבלת התראות\n"
        "3. כשמישהו מפרסם כרטיס — תקבלו הודעה ישירות לכאן!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>חשוב לדעת:</b>\n\n"
        "• המכירה היא <b>במחיר עלות בלבד</b>. "
        "מוכרים שיפרסמו מחיר מעל עלות — <b>ייחסמו</b>.\n"
        "• הבוט משמש <b>כמתווך בלבד</b> ואינו אחראי על העסקה "
        "בין הקונה למוכר.\n\n"
        "👇 השתמשו בכפתורים למטה להתחיל.",
        reply_markup=keyboard,
    )


@router.message(Command("help"))
@router.message(F.text == "❓ עזרה")
async def help_command(message: Message):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await message.answer(
        "📖 <b>עזרה — TickAlert</b>\n\n"
        "הבוט עוזר לכם <b>למצוא ולמכור כרטיסים</b> למשחקי ביתר ירושלים.\n"
        "הירשמו לאירוע — וקבלו התראה מיידית כשכרטיס מתפנה!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚽ <b>מה אפשר לעשות כאן?</b>\n\n"
        "💰 <b>מוכר כרטיס</b> — פרסמו כרטיס למכירה\n"
        "🔎 <b>מחפש כרטיס</b> — צפו באירועים והירשמו להתראות\n"
        "📋 <b>האירועים שלי</b> — האירועים שנרשמתם אליהם\n"
        "❌ <b>ביטול וחזרה להתחלה</b> — ביטול פעולה וחזרה לתפריט הראשי\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "💡 <b>איך זה עובד?</b>\n\n"
        "1. לחצו על <b>מחפש כרטיס</b> ובחרו אירוע\n"
        "2. הירשמו לקבלת התראות\n"
        "3. כשמישהו מפרסם כרטיס — תקבלו הודעה ישירות לכאן!\n\n"
        "━━━━━━━━━━━━━━━━━━\n"
        "⚠️ <b>חשוב לדעת:</b>\n\n"
        "• המכירה היא <b>במחיר עלות בלבד</b>. "
        "מוכרים שיפרסמו מחיר מעל עלות — <b>ייחסמו</b>.\n"
        "• הבוט משמש <b>כמתווך בלבד</b> ואינו אחראי על העסקה "
        "בין הקונה למוכר.\n\n"
        "💡 <b>טיפ:</b> ככל שתירשמו מוקדם יותר, כך תהיו הראשונים לדעת על כרטיסים חדשים.",
    )


def _event_label(event) -> str:
    label = f"📅 {event.name} — {event.date} {event.time or ''}"
    if event.location:
        label += f" | {event.location}"
    return label.strip()


@router.message(Command("events"))
@router.message(F.text == "🔎 מחפש כרטיס")
async def events(message: Message):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    async with async_session() as session:
        active_events = await repo.get_active_events(session)

    if not active_events:
        await message.answer("אין אירועים זמינים כרגע.")
        return

    active_events = active_events[:5]

    keyboard = []
    for event in active_events:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"event_{event.id}")])

    await message.answer(
        "🎫 <b>אירועים זמינים:</b>\nלחצו על אירוע כדי להירשם לקבלת התראות.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data.startswith("event_"))
async def event_selected(callback: CallbackQuery):
    if await is_blocked(callback.from_user.id):
        await callback.answer("⛔ אתה חסום.", show_alert=True)
        return

    event_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        event = await repo.get_event(session, event_id)
        if not event:
            await callback.message.edit_text("האירוע לא נמצא.")
            await callback.answer()
            return

        registrations = await repo.get_user_registrations(session, callback.from_user.id)

    is_registered = any(r.id == event_id for r in registrations)

    keyboard = []
    if is_registered:
        keyboard.append([InlineKeyboardButton(text="🎫 צפייה בכרטיסים זמינים", callback_data=f"viewtickets_{event_id}")])
        keyboard.append([InlineKeyboardButton(text="❌ ביטול הרשמה", callback_data=f"unreg_{event_id}")])
    else:
        keyboard.append([InlineKeyboardButton(text="✅ הרשמה להתראות", callback_data=f"reg_{event_id}")])

    status = "✅ רשום" if is_registered else "❌ לא רשום"
    text = (
        f"📅 <b>{event.name}</b>\n"
        f"🗓 תאריך: {event.date}\n"
        f"🕐 שעה: {event.time or 'לא צוין'}\n"
        f"📍 מיקום: {event.location or 'לא צוין'}\n\n"
        f"סטטוס: {status}"
    )
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard))
    await callback.answer()


@router.callback_query(F.data.startswith("reg_"))
async def register_event(callback: CallbackQuery):
    if await is_blocked(callback.from_user.id):
        await callback.answer("⛔ אתה חסום.", show_alert=True)
        return

    event_id = int(callback.data.split("_")[1])
    await ensure_user(callback.from_user.id, callback.from_user.username, callback.from_user.first_name)

    async with async_session() as session:
        registered = await repo.register_for_event(session, callback.from_user.id, event_id)
        event = await repo.get_event(session, event_id)

    if registered:
        kb = [[InlineKeyboardButton(text="🎫 צפייה בכרטיסים זמינים", callback_data=f"viewtickets_{event_id}")]]
        await callback.message.edit_text(
            f"✅ נרשמת בהצלחה להתראות!\n\n"
            f"📅 אירוע: <b>{event.name}</b>\n"
            f"🗓 תאריך: {event.date}\n"
            f"🕐 שעה: {event.time or 'לא צוין'}\n"
            f"📍 מיקום: {event.location or 'לא צוין'}",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=kb),
        )
    else:
        await callback.message.edit_text("כבר נרשמת לאירוע זה.")
    await callback.answer()


@router.callback_query(F.data.startswith("unreg_"))
async def unregister_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        unregistered = await repo.unregister_from_event(session, callback.from_user.id, event_id)
        event = await repo.get_event(session, event_id)

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 חזרה לאירועים", callback_data="back_events")]
    ])
    if unregistered:
        await callback.message.edit_text(
            f"❌ הרשמתך לאירוע <b>{event.name}</b> בוטלה.",
            reply_markup=back_kb,
        )
    else:
        await callback.message.edit_text("לא היית רשום לאירוע זה.", reply_markup=back_kb)
    await callback.answer()


@router.message(Command("myevents"))
@router.message(F.text == "📋 אירועים שנרשמתי להתראות")
async def my_events(message: Message):
    if await is_blocked(message.from_user.id):
        await message.answer("⛔ אתה חסום ואינך יכול להשתמש בבוט זה.")
        return
    await ensure_user(message.from_user.id, message.from_user.username, message.from_user.first_name)

    async with async_session() as session:
        registrations = await repo.get_user_registrations(session, message.from_user.id)

    if not registrations:
        await message.answer("לא נרשמת לאף אירוע עדיין.\nלחצו על <b>אירועים זמינים</b> כדי להירשם.")
        return

    keyboard = []
    for event in registrations:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"event_{event.id}")])

    await message.answer(
        "🎫 <b>האירועים שלי:</b>\nלחצו על אירוע לצפייה בכרטיסים זמינים.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )


@router.callback_query(F.data.startswith("viewtickets_"))
async def view_tickets(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        event = await repo.get_event(session, event_id)
        if not event:
            await callback.message.edit_text("האירוע לא נמצא.")
            await callback.answer()
            return
        tickets = await repo.get_active_tickets(session, event_id)

    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 חזרה לאירוע", callback_data=f"event_{event_id}")]
    ])

    if not tickets:
        await callback.message.edit_text(
            f"📅 <b>{event.name}</b>\n\nאין כרטיסים זמינים כרגע לאירוע זה.",
            reply_markup=back_kb,
        )
        await callback.answer()
        return

    lines = [f"📅 <b>{event.name}</b> — כרטיסים זמינים:\n"]
    for t in tickets:
        seller_handle = f"@{t['username']}" if t["username"] else (t["first_name"] or "משתמש")
        lines.append(
            f"━━━━━━━━━━━━━━━\n"
            f"{t['description']}\n"
            f"👤 מוכר: {seller_handle}"
        )
    lines.append("━━━━━━━━━━━━━━━")

    await callback.message.edit_text("\n".join(lines), reply_markup=back_kb)
    await callback.answer()


@router.callback_query(F.data == "back_events")
async def back_to_events(callback: CallbackQuery):
    async with async_session() as session:
        active_events = await repo.get_active_events(session)

    if not active_events:
        await callback.message.edit_text("אין אירועים זמינים כרגע.")
        await callback.answer()
        return

    active_events = active_events[:5]
    keyboard = []
    for event in active_events:
        keyboard.append([InlineKeyboardButton(text=_event_label(event), callback_data=f"event_{event.id}")])

    await callback.message.edit_text(
        "🎫 <b>אירועים זמינים:</b>\nלחצו על אירוע כדי להירשם לקבלת התראות.",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard),
    )
    await callback.answer()
