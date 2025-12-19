import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from .config import get_settings
from .db import init_db
import aiosqlite
from .scheduler import setup_scheduler

from .handlers import start, menu, payment, support, forecast, admin

async def main():
    settings = get_settings()
    bot = Bot(token=settings.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    await init_db()

    # роутеры
    dp.include_router(start.router)
    dp.include_router(menu.router)
    dp.include_router(payment.router)
    dp.include_router(admin.router)
    dp.include_router(forecast.router)
    dp.include_router(support.router)

    # scheduler (reminders table)
    db = await aiosqlite.connect("bot.sqlite3")
    sched = setup_scheduler(bot, db)
    sched.start()

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
