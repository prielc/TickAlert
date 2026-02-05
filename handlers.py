from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import Database
from datetime import datetime

router = Router()


# FSM States for ticket posting
class TicketPosting(StatesGroup):
    waiting_for_event = State()
    waiting_for_quantity = State()
    waiting_for_price = State()
    waiting_for_details = State()
    waiting_for_contact = State()


@router.message(Command("start"))
async def cmd_start(message: Message, db: Database = None):
    """Handle /start command"""
    user = message.from_user
    
    # Save user to database
    if db:
        await db.add_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name
        )
    
    welcome_text = f"""
שלום {user.first_name}! 👋

<b>ברוכים הבאים ל-TickAlert!</b>

TickAlert היא פלטפורמה לשליחת <b>התראות בזמן אמת</b> על כרטיסים שמתפנים לאירועים סולד־אאוט.

<b>איך זה עובד?</b>
1️⃣ הירשם לאירועים שמעניינים אותך
2️⃣ קבל התראה מיידית כשמישהו מפרסם כרטיס למכירה
3️⃣ פרסם כרטיסים שלך למכירה

<b>הערך המרכזי:</b>
לא לחפש כרטיסים – לקבל התראה ברגע שהם זמינים! ⚡

השתמש ב-/help כדי לראות את כל הפקודות הזמינות.
    """
    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
<b>📋 פקודות זמינות:</b>

<b>אירועים והרשמות:</b>
/events - רשימת כל האירועים הזמינים
/subscribe <מספר_אירוע> - הירשם לאירוע
/unsubscribe <מספר_אירוע> - בטל הרשמה לאירוע
/mysubscriptions - האירועים שאתה רשום אליהם

<b>כרטיסים:</b>
/postticket - פרסם כרטיס למכירה
/mytickets - הכרטיסים שפרסמת

<b>אחר:</b>
/help - הצג הודעה זו
/stats - סטטיסטיקות אישיות

<b>💡 טיפ:</b>
התחל ב-/events כדי לראות את האירועים הזמינים ולהרשם אליהם!
    """
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("events"))
async def cmd_events(message: Message, db: Database = None):
    """List all available events"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    events = await db.get_events(is_active=True)
    
    if not events:
        await message.answer("📅 אין אירועים זמינים כרגע.\n\nהשתמש ב-/help כדי לראות פקודות נוספות.")
        return
    
    events_text = "<b>📅 אירועים זמינים:</b>\n\n"
    
    for event in events:
        event_id, name, description, event_date, category, team, venue, is_active, created_at = event
        events_text += f"<b>#{event_id} - {name}</b>\n"
        if description:
            events_text += f"📝 {description}\n"
        if team:
            events_text += f"⚽ קבוצה: {team}\n"
        if venue:
            events_text += f"📍 מיקום: {venue}\n"
        if event_date:
            events_text += f"📆 תאריך: {event_date}\n"
        events_text += f"הירשם: /subscribe_{event_id}\n\n"
    
    events_text += "\n💡 השתמש ב-/subscribe <מספר> כדי להירשם לאירוע"
    
    await message.answer(events_text, parse_mode="HTML")


@router.message(Command("subscribe"))
async def cmd_subscribe(message: Message, db: Database = None):
    """Subscribe to an event"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    command_args = message.text.split()
    
    if len(command_args) < 2:
        await message.answer(
            "❌ שימוש: /subscribe <מספר_אירוע>\n\n"
            "דוגמה: /subscribe 1\n\n"
            "השתמש ב-/events כדי לראות את רשימת האירועים."
        )
        return
    
    try:
        event_id = int(command_args[1])
    except ValueError:
        await message.answer("❌ מספר אירוע לא תקין. השתמש במספר בלבד.")
        return
    
    # Check if event exists
    event = await db.get_event(event_id)
    if not event:
        await message.answer(f"❌ אירוע #{event_id} לא נמצא.")
        return
    
    # Subscribe user
    success = await db.subscribe_user(user_id, event_id)
    
    if success:
        event_name = event[1]
        await message.answer(
            f"✅ נרשמת בהצלחה לאירוע:\n<b>{event_name}</b>\n\n"
            f"עכשיו תקבל התראה מיידית כשמישהו מפרסם כרטיס למכירה לאירוע זה! 🔔",
            parse_mode="HTML"
        )
    else:
        await message.answer("ℹ️ אתה כבר רשום לאירוע זה.")


@router.message(Command("unsubscribe"))
async def cmd_unsubscribe(message: Message, db: Database = None):
    """Unsubscribe from an event"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    command_args = message.text.split()
    
    if len(command_args) < 2:
        await message.answer(
            "❌ שימוש: /unsubscribe <מספר_אירוע>\n\n"
            "השתמש ב-/mysubscriptions כדי לראות את ההרשמות שלך."
        )
        return
    
    try:
        event_id = int(command_args[1])
    except ValueError:
        await message.answer("❌ מספר אירוע לא תקין.")
        return
    
    success = await db.unsubscribe_user(user_id, event_id)
    
    if success:
        event = await db.get_event(event_id)
        event_name = event[1] if event else f"#{event_id}"
        await message.answer(f"✅ ביטלת הרשמה לאירוע: <b>{event_name}</b>", parse_mode="HTML")
    else:
        await message.answer("❌ לא נמצאה הרשמה לאירוע זה.")


@router.message(Command("mysubscriptions"))
async def cmd_mysubscriptions(message: Message, db: Database = None):
    """Show user's subscriptions"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    subscriptions = await db.get_user_subscriptions(user_id)
    
    if not subscriptions:
        await message.answer(
            "📭 אתה לא רשום לאף אירוע.\n\n"
            "השתמש ב-/events כדי לראות אירועים זמינים ולהרשם אליהם."
        )
        return
    
    subs_text = "<b>📋 האירועים שאתה רשום אליהם:</b>\n\n"
    
    for event in subscriptions:
        event_id, name, description, event_date, category, team, venue, is_active, created_at = event
        subs_text += f"<b>#{event_id} - {name}</b>\n"
        if team:
            subs_text += f"⚽ {team}\n"
        subs_text += f"בטל הרשמה: /unsubscribe_{event_id}\n\n"
    
    await message.answer(subs_text, parse_mode="HTML")


@router.message(Command("postticket"))
async def cmd_postticket(message: Message, state: FSMContext, db: Database = None):
    """Start ticket posting process"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    
    # Check rate limit
    can_post = await db.check_rate_limit(user_id, max_per_day=5)
    if not can_post:
        await message.answer(
            "⏰ הגעת למגבלת הפרסומים היומית (5 כרטיסים ביום).\n"
            "נסה שוב מחר."
        )
        return
    
    # Get events for selection
    events = await db.get_events(is_active=True)
    if not events:
        await message.answer("❌ אין אירועים זמינים כרגע.")
        return
    
    # Create inline keyboard with events
    keyboard_buttons = []
    for event in events[:10]:  # Limit to 10 events
        event_id, name = event[0], event[1]
        keyboard_buttons.append([InlineKeyboardButton(
            text=f"#{event_id} - {name[:30]}",
            callback_data=f"select_event_{event_id}"
        )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(
        "🎫 <b>פרסום כרטיס למכירה</b>\n\n"
        "בחר לאיזה אירוע אתה רוצה לפרסם כרטיס:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.set_state(TicketPosting.waiting_for_event)


@router.callback_query(F.data.startswith("select_event_"))
async def select_event_callback(callback: CallbackQuery, state: FSMContext, db: Database = None):
    """Handle event selection"""
    event_id = int(callback.data.split("_")[-1])
    event = await db.get_event(event_id)
    
    if not event:
        await callback.answer("❌ אירוע לא נמצא", show_alert=True)
        return
    
    await state.update_data(event_id=event_id, event_name=event[1])
    await callback.message.edit_text(
        f"✅ בחרת: <b>{event[1]}</b>\n\n"
        "כמה כרטיסים יש לך למכירה?\n"
        "שלח מספר (לדוגמה: 1 או 2)",
        parse_mode="HTML"
    )
    await state.set_state(TicketPosting.waiting_for_quantity)
    await callback.answer()


@router.message(TicketPosting.waiting_for_quantity)
async def process_quantity(message: Message, state: FSMContext):
    """Process ticket quantity"""
    try:
        quantity = int(message.text)
        if quantity < 1:
            raise ValueError
        await state.update_data(quantity=quantity)
        await message.answer(
            "💰 מה המחיר?\n\n"
            "שלח את המחיר (לדוגמה: 100 ש\"ח או \"מחיר סביר\")"
        )
        await state.set_state(TicketPosting.waiting_for_price)
    except ValueError:
        await message.answer("❌ אנא שלח מספר תקין (1, 2, 3 וכו')")


@router.message(TicketPosting.waiting_for_price)
async def process_price(message: Message, state: FSMContext):
    """Process ticket price"""
    price = message.text
    await state.update_data(price=price)
    await message.answer(
        "📝 פרטים נוספים (אופציונלי):\n\n"
        "שלח פרטים נוספים על הכרטיס, או שלח \"דלג\" כדי להמשיך."
    )
    await state.set_state(TicketPosting.waiting_for_details)


@router.message(TicketPosting.waiting_for_details)
async def process_details(message: Message, state: FSMContext):
    """Process ticket details"""
    details = None if message.text.lower() in ["דלג", "skip", "none"] else message.text
    await state.update_data(details=details)
    await message.answer(
        "📞 פרטי קשר:\n\n"
        "איך אפשר ליצור איתך קשר? (טלפון, טלגרם וכו')\n"
        "או שלח \"דלג\" אם אתה מעדיף שיצרו איתך קשר דרך הטלגרם."
    )
    await state.set_state(TicketPosting.waiting_for_contact)


@router.message(TicketPosting.waiting_for_contact)
async def process_contact(message: Message, state: FSMContext, db: Database = None, bot: Bot = None):
    """Process contact info and post ticket"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        await state.clear()
        return
    
    contact_info = None if message.text.lower() in ["דלג", "skip", "none"] else message.text
    
    data = await state.get_data()
    event_id = data.get("event_id")
    event_name = data.get("event_name")
    quantity = data.get("quantity")
    price = data.get("price")
    details = data.get("details")
    
    user_id = message.from_user.id
    
    # Add ticket to database
    ticket_id = await db.add_ticket(
        user_id=user_id,
        event_id=event_id,
        quantity=quantity,
        price=price,
        details=details,
        contact_info=contact_info
    )
    
    # Get all subscribers for this event
    subscribers = await db.get_event_subscribers(event_id)
    
    # Send notifications to subscribers
    notification_count = 0
    user_name = message.from_user.first_name
    username = f"@{message.from_user.username}" if message.from_user.username else "משתמש"
    
    ticket_text = f"""
🔔 <b>כרטיס חדש זמין!</b>

📅 <b>{event_name}</b>
🎫 כמות: {quantity}
💰 מחיר: {price}
👤 מפרסם: {user_name} {username}
    """
    
    if details:
        ticket_text += f"\n📝 פרטים: {details}"
    if contact_info:
        ticket_text += f"\n📞 קשר: {contact_info}"
    else:
        ticket_text += f"\n📞 יצירת קשר דרך הטלגרם: {username}"
    
    ticket_text += f"\n\n🆔 מספר כרטיס: #{ticket_id}"
    
    for subscriber in subscribers:
        sub_user_id = subscriber[0]
        # Don't notify the person who posted the ticket
        if sub_user_id == user_id:
            continue
        
        # Check if already notified (prevent duplicates)
        if await db.was_notified(ticket_id, sub_user_id):
            continue
        
        try:
            if bot:
                await bot.send_message(sub_user_id, ticket_text, parse_mode="HTML")
                await db.log_notification(ticket_id, sub_user_id)
                notification_count += 1
        except Exception as e:
            # User blocked bot or other error - skip
            pass
    
    await message.answer(
        f"✅ הכרטיס פורסם בהצלחה!\n\n"
        f"📊 נשלחו {notification_count} התראות למנויים לאירוע.\n\n"
        f"🆔 מספר כרטיס: #{ticket_id}\n\n"
        f"השתמש ב-/mytickets כדי לראות את כל הכרטיסים שפרסמת."
    )
    
    await state.clear()


@router.message(Command("mytickets"))
async def cmd_mytickets(message: Message, db: Database = None):
    """Show user's posted tickets"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    tickets = await db.get_user_tickets(user_id)
    
    if not tickets:
        await message.answer(
            "🎫 לא פרסמת כרטיסים עדיין.\n\n"
            "השתמש ב-/postticket כדי לפרסם כרטיס למכירה."
        )
        return
    
    tickets_text = "<b>🎫 הכרטיסים שפרסמת:</b>\n\n"
    
    for ticket in tickets:
        ticket_id, _, event_id, quantity, price, details, contact_info, is_sold, created_at = ticket[:9]
        event_name = ticket[9] if len(ticket) > 9 else "אירוע"
        
        status = "✅ פעיל" if not is_sold else "❌ נמכר"
        tickets_text += f"<b>#{ticket_id} - {event_name}</b> {status}\n"
        tickets_text += f"🎫 כמות: {quantity} | 💰 {price}\n"
        if details:
            tickets_text += f"📝 {details}\n"
        tickets_text += f"📅 פורסם: {created_at[:10]}\n\n"
    
    await message.answer(tickets_text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database = None):
    """Show user statistics"""
    if not db:
        await message.answer("❌ מסד הנתונים לא זמין.")
        return
    
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    subscriptions = await db.get_user_subscriptions(user_id)
    tickets = await db.get_user_tickets(user_id)
    
    stats_text = f"<b>📊 הסטטיסטיקות שלך:</b>\n\n"
    
    if user_data:
        stats_text += f"👤 שם: {user_data[2]}\n"
        if user_data[1]:
            stats_text += f"📱 @{user_data[1]}\n"
        stats_text += f"📅 הצטרף: {user_data[3][:10]}\n\n"
    
    stats_text += f"📋 רשום ל-{len(subscriptions)} אירועים\n"
    stats_text += f"🎫 פרסמת {len(tickets)} כרטיסים\n"
    
    await message.answer(stats_text, parse_mode="HTML")


# Handle callback queries for subscribe/unsubscribe shortcuts
@router.callback_query(F.data.startswith("subscribe_"))
async def subscribe_callback(callback: CallbackQuery, db: Database = None):
    """Handle subscribe callback"""
    if not db:
        await callback.answer("❌ שגיאה", show_alert=True)
        return
    
    event_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    success = await db.subscribe_user(user_id, event_id)
    
    if success:
        event = await db.get_event(event_id)
        event_name = event[1] if event else f"#{event_id}"
        await callback.answer(f"✅ נרשמת ל-{event_name}", show_alert=True)
        await callback.message.edit_text(
            callback.message.text + f"\n\n✅ נרשמת לאירוע זה!"
        )
    else:
        await callback.answer("ℹ️ אתה כבר רשום לאירוע זה", show_alert=True)


@router.callback_query(F.data.startswith("unsubscribe_"))
async def unsubscribe_callback(callback: CallbackQuery, db: Database = None):
    """Handle unsubscribe callback"""
    if not db:
        await callback.answer("❌ שגיאה", show_alert=True)
        return
    
    event_id = int(callback.data.split("_")[-1])
    user_id = callback.from_user.id
    
    success = await db.unsubscribe_user(user_id, event_id)
    
    if success:
        await callback.answer("✅ ביטלת הרשמה", show_alert=True)
    else:
        await callback.answer("❌ לא נמצאה הרשמה", show_alert=True)


# Fallback for unhandled messages
@router.message(F.text)
async def echo_message(message: Message):
    """Handle unhandled text messages"""
    await message.answer(
        "❓ לא הבנתי את ההודעה שלך.\n\n"
        "השתמש ב-/help כדי לראות את כל הפקודות הזמינות."
    )
