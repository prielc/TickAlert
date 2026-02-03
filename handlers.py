from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database import Database

router = Router()


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
    
    await message.answer(
        f"Hello, {user.first_name}! 👋\n\n"
        "Welcome to TickAlert Bot!\n"
        "Use /help to see available commands."
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    help_text = """
<b>Available Commands:</b>

/start - Start the bot
/help - Show this help message
/stats - Show your statistics

<i>More features coming soon!</i>
    """
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Database = None):
    """Handle /stats command"""
    if not db:
        await message.answer("Database not available.")
        return
    
    user_id = message.from_user.id
    user_data = await db.get_user(user_id)
    
    if user_data:
        await message.answer(
            f"<b>Your Stats:</b>\n\n"
            f"User ID: {user_data[0]}\n"
            f"Username: @{user_data[1] or 'N/A'}\n"
            f"Name: {user_data[2]}\n"
            f"Joined: {user_data[3]}",
            parse_mode="HTML"
        )
    else:
        await message.answer("No data found. Please use /start first.")


@router.message(F.text)
async def echo_message(message: Message):
    """Echo text messages"""
    await message.answer(
        f"You said: {message.text}\n\n"
        "Use /help to see available commands."
    )
