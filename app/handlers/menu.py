from aiogram import Router, F
from aiogram.types import CallbackQuery
import aiosqlite

from ..keyboards import main_menu, pay_network_kb
from ..texts import ASK_MATCH, PAY_MENU, SUPPORT_INTRO
from ..config import get_settings

router = Router()

@router.callback_query(F.data == "menu:back")
async def back(c: CallbackQuery):
    await c.message.edit_text("Главное меню 👇", reply_markup=main_menu())
    await c.answer()

@router.callback_query(F.data == "menu:forecast")
async def go_forecast(c: CallbackQuery):
    await c.message.edit_text(ASK_MATCH, reply_markup=main_menu(), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data == "menu:pay")
async def go_pay(c: CallbackQuery):
    await c.message.edit_text(PAY_MENU, reply_markup=pay_network_kb())
    await c.answer()

@router.callback_query(F.data == "menu:support")
async def go_support(c: CallbackQuery):
    await c.message.edit_text(SUPPORT_INTRO, reply_markup=main_menu())
    await c.answer()

@router.callback_query(F.data == "menu:cabinet")
async def cabinet(c: CallbackQuery):
    async with aiosqlite.connect("bot.sqlite3") as db:
        cur = await db.execute("SELECT queries_balance, ref_code, referrals_count FROM users WHERE user_id=?", (c.from_user.id,))
        row = await cur.fetchone()

    bal, ref_code, refs = row if row else (0, "", 0)
    text = (
        "📊 *Мой кабинет*\n\n"
        f"🔹 Запросов осталось: *{bal}*\n"
        f"👥 Рефералы: *{refs}*\n"
        f"🔗 Твоя ссылка:\n"
        f"`https://t.me/{(await c.bot.get_me()).username}?start={ref_code}`\n"
    )
    await c.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data == "menu:ref")
async def ref(c: CallbackQuery):
    async with aiosqlite.connect("bot.sqlite3") as db:
        cur = await db.execute("SELECT ref_code, referrals_count FROM users WHERE user_id=?", (c.from_user.id,))
        row = await cur.fetchone()

    ref_code, refs = row if row else ("", 0)
    bot_username = (await c.bot.get_me()).username
    text = (
        "👥 *Рефералы*\n\n"
        f"Приглашено: *{refs}*\n\n"
        "Твоя ссылка:\n"
        f"`https://t.me/{bot_username}?start={ref_code}`\n\n"
        "Бонусы начисляются автоматически."
    )
    await c.message.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
    await c.answer()
