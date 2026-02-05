import asyncio
import logging
import os
from typing import Any, Awaitable, Callable
from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from dotenv import load_dotenv
from database import Database
from handlers import router

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware to inject database and bot into handlers"""
    def __init__(self, db: Database, bot: Bot):
        self.db = db
        self.bot = bot
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any]
    ) -> Any:
        data["db"] = self.db
        data["bot"] = self.bot
        return await handler(event, data)


async def main():
    """Main function to run the bot"""
    # Get bot token from environment
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        raise ValueError("BOT_TOKEN environment variable is not set")
    
    # Initialize bot and dispatcher
    bot = Bot(
        token=bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Initialize database
    db = Database()
    await db.connect()
    
    # Register middleware to inject database and bot
    dp.message.middleware(DatabaseMiddleware(db, bot))
    dp.callback_query.middleware(DatabaseMiddleware(db, bot))
    
    # Register router
    dp.include_router(router)
    
    try:
        logger.info("Starting bot...")
        # Start polling
        await dp.start_polling(bot)
    finally:
        await db.close()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
