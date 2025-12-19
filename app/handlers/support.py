from aiogram import Router, F
from aiogram.types import Message
import aiosqlite

from ..config import get_settings
from ..forum_router import ensure_user_topic, forward_to_topic

router = Router()

# Любое сообщение от пользователя (кроме команд) — в его ветку
@router.message(F.chat.type == "private")
async def user_any_to_support(m: Message):
    # Чтобы не мешать сценарию оплаты и прогнозов — в этих сценариях мы либо возвращаемся, либо фильтруем.
    # Здесь отправляем в ветку как "Support stream".
    settings = get_settings()
    async with aiosqlite.connect("bot.sqlite3") as db:
        topic_id = await ensure_user_topic(m.bot, db, settings.ADMIN_CHAT_ID, m.from_user.id, m.from_user.username)

    await forward_to_topic(
        m.bot, settings.ADMIN_CHAT_ID, topic_id, m,
        prefix=f"🆘 Сообщение пользователя (support stream). user_id={m.from_user.id}"
    )

# Ответ админа в топике -> пользователю
@router.message(F.chat.id == get_settings().ADMIN_CHAT_ID)
async def admin_reply_from_topic(m: Message):
    # работаем только если это сообщение в теме (ветке)
    if not m.message_thread_id:
        return
    if not m.reply_to_message:
        return

    # Пытаемся вытащить user_id из закрепленного паттерна: "user_id=123"
    # или из темы, т.к. title содержит (id)
    # MVP: ищем в reply_to_message.text / caption
    text_src = (m.reply_to_message.text or m.reply_to_message.caption or "")
    import re
    mm = re.search(r"user_id=(\d+)", text_src)
    if not mm:
        return

    user_id = int(mm.group(1))

    # Отправляем пользователю копию сообщения админа (любой тип)
    await m.copy_to(chat_id=user_id)
