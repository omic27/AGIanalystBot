from aiogram import Bot
from aiogram.types import Message
import aiosqlite
from .db import get_or_create_topic, save_topic
from .utils import safe_topic_title

async def ensure_user_topic(bot: Bot, db: aiosqlite.Connection, admin_chat_id: int, user_id: int, username: str | None) -> int:
    row = await get_or_create_topic(db, user_id)
    if row:
        return int(row[0])

    title = safe_topic_title(user_id, username)
    topic = await bot.create_forum_topic(chat_id=admin_chat_id, name=title)
    topic_id = topic.message_thread_id
    await save_topic(db, user_id, topic_id, title)
    return topic_id

async def forward_to_topic(bot: Bot, admin_chat_id: int, topic_id: int, msg: Message, prefix: str | None = None):
    # Forward any kind of content with context message
    if prefix:
        await bot.send_message(chat_id=admin_chat_id, message_thread_id=topic_id, text=prefix)

    await msg.forward(chat_id=admin_chat_id, message_thread_id=topic_id)
