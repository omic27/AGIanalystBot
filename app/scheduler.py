from apscheduler.schedulers.asyncio import AsyncIOScheduler
import time
import aiosqlite
from aiogram import Bot

async def send_due_reminders(bot: Bot, db: aiosqlite.Connection):
    now = int(time.time())
    cur = await db.execute("SELECT id, user_id, text FROM reminders WHERE sent=0 AND send_at<=?", (now,))
    rows = await cur.fetchall()
    for rid, user_id, text in rows:
        try:
            await bot.send_message(chat_id=int(user_id), text=text)
            await db.execute("UPDATE reminders SET sent=1 WHERE id=?", (rid,))
        except Exception:
            # ignore for now
            pass
    await db.commit()

def setup_scheduler(bot: Bot, db: aiosqlite.Connection) -> AsyncIOScheduler:
    sched = AsyncIOScheduler()
    # Каждую минуту проверяем таблицу reminders (в будущем ты заполнишь её матчами)
    sched.add_job(send_due_reminders, "interval", minutes=1, args=[bot, db])
    return sched
