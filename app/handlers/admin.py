from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from ..config import get_settings
from ..db import get_payment, set_payment_status, add_queries
from ..texts import PAYMENT_APPROVED_USER, PAYMENT_REJECTED_USER

router = Router()

@router.callback_query(F.data.startswith("admin:pay:approve:"))
async def admin_approve(c: CallbackQuery):
    settings = get_settings()
    if c.from_user.id != settings.OWNER_ID:
        await c.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(c.data.split(":")[-1])
    async with aiosqlite.connect("bot.sqlite3") as db:
        p = await get_payment(db, payment_id)
        if not p:
            await c.answer("Платеж не найден", show_alert=True)
            return
        _, user_id, network, amount_usd, queries_to_add, wallet, memo, status, proof = p
        if status != "pending":
            await c.answer("Уже обработан", show_alert=True)
            return

        await set_payment_status(db, payment_id, "approved")
        await add_queries(db, int(user_id), int(queries_to_add))

    await c.bot.send_message(chat_id=int(user_id), text=PAYMENT_APPROVED_USER.format(queries=queries_to_add), parse_mode="Markdown")
    await c.message.edit_text((c.message.text or "") + "\n\n✅ Одобрено.")
    await c.answer("Одобрено")

@router.callback_query(F.data.startswith("admin:pay:reject:"))
async def admin_reject(c: CallbackQuery):
    settings = get_settings()
    if c.from_user.id != settings.OWNER_ID:
        await c.answer("Нет доступа", show_alert=True)
        return

    payment_id = int(c.data.split(":")[-1])
    async with aiosqlite.connect("bot.sqlite3") as db:
        p = await get_payment(db, payment_id)
        if not p:
            await c.answer("Платеж не найден", show_alert=True)
            return
        _, user_id, network, amount_usd, queries_to_add, wallet, memo, status, proof = p
        if status != "pending":
            await c.answer("Уже обработан", show_alert=True)
            return
        await set_payment_status(db, payment_id, "rejected")

    await c.bot.send_message(chat_id=int(user_id), text=PAYMENT_REJECTED_USER)
    await c.message.edit_text((c.message.text or "") + "\n\n❌ Отклонено.")
    await c.answer("Отклонено")
