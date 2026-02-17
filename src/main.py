import logging
import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import BOT_TOKEN, WEBHOOK_BASE_URL, WEBHOOK_SECRET
from src.handlers import user, seller, admin
from src.scraper import fetch_future_beitar_games
from src.db.repositories import sync_scraped_events
from src.db.session import async_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    # Admin cancel must be registered first so it catches ❌ ביטול during FSM states
    dp.include_router(admin.router)
    dp.include_router(seller.router)
    dp.include_router(user.router)
    return dp


SYNC_INTERVAL = 60 * 60 * 24 * 14  # 2 weeks in seconds


async def sync_beitar_events():
    """Fetch future Beitar games from 365scores and sync to DB."""
    try:
        games = await fetch_future_beitar_games()
        if games:
            async with async_session() as session:
                added = await sync_scraped_events(session, games)
                logger.info("Event sync complete: %d new events added", added)
    except Exception:
        logger.exception("Failed to sync Beitar events")


async def periodic_sync():
    """Run event sync every 2 weeks."""
    while True:
        await asyncio.sleep(SYNC_INTERVAL)
        logger.info("Running periodic Beitar events sync")
        await sync_beitar_events()


async def on_startup(bot: Bot):
    await sync_beitar_events()
    asyncio.create_task(periodic_sync())

    if WEBHOOK_BASE_URL:
        webhook_url = f"{WEBHOOK_BASE_URL}/webhook"
        await bot.set_webhook(webhook_url, secret_token=WEBHOOK_SECRET)
        logger.info(f"Webhook set to {webhook_url}")
    else:
        await bot.delete_webhook()
        logger.info("Running in polling mode")


async def main():
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = create_dispatcher()

    dp.startup.register(on_startup)

    if WEBHOOK_BASE_URL:
        # Webhook mode with FastAPI
        from fastapi import FastAPI, Request, Response
        import uvicorn

        app = FastAPI()

        @app.post("/webhook")
        async def webhook_handler(request: Request) -> Response:
            # Verify secret
            if WEBHOOK_SECRET:
                secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
                if secret != WEBHOOK_SECRET:
                    return Response(status_code=403)

            from aiogram.types import Update
            update = Update.model_validate(await request.json(), context={"bot": bot})
            await dp.feed_update(bot, update)
            return Response(status_code=200)

        @app.on_event("startup")
        async def fastapi_startup():
            await on_startup(bot)

        config = uvicorn.Config(app, host="0.0.0.0", port=8000)
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # Polling mode (local development)
        logger.info("Starting bot in polling mode...")
        await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
