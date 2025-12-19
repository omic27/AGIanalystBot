from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
import aiosqlite

from ..config import get_settings
from ..payments import get_wallet_for_network, get_packages, is_ton
from ..db import create_payment, set_payment_proof
from ..keyboards import packages_kb, pay_after_instruction_kb
from ..texts import PAY_INSTRUCTION_TEMPLATE, PAY_INSTRUCTION_TON_TEMPLATE, PAYMENT_SUBMITTED
from ..forum_router import ensure_user_topic, forward_to_topic
from ..keyboards import admin_payment_kb

router = Router()

# state in memory (MVP)
USER_PAY = {}  # user_id -> payment_id awaiting proof

@router.callback_query(F.data.startswith("pay:net:"))
async def choose_network(c: CallbackQuery):
    settings = get_settings()
    network = c.data.split(":")[-1]
    pkgs = get_packages(settings)
    await c.message.edit_text("Выбери пакет 👇", reply_markup=packages_kb(pkgs, network))
    await c.answer()

@router.callback_query(F.data.startswith("pay:pkg:"))
async def choose_package(c: CallbackQuery):
    settings = get_settings()
    _, _, network, amount_s = c.data.split(":")
    amount = int(amount_s)

    packages = dict(get_packages(settings))
    queries = packages.get(amount)
    if not queries:
        await c.answer("Пакет не найден", show_alert=True)
        return

    wallet = get_wallet_for_network(settings, network)
    if not wallet:
        await c.answer("Кошелек не настроен", show_alert=True)
        return

    async with aiosqlite.connect("bot.sqlite3") as db:
        payment_id, memo = await create_payment(db, c.from_user.id, network, amount, queries, wallet)

    if is_ton(network):
        text = PAY_INSTRUCTION_TON_TEMPLATE.format(amount=amount, queries=queries, wallet=wallet, memo=memo)
    else:
        text = PAY_INSTRUCTION_TEMPLATE.format(amount=amount, queries=queries, network=network, wallet=wallet, memo=memo)

    await c.message.edit_text(text, reply_markup=pay_after_instruction_kb(payment_id), parse_mode="Markdown")
    await c.answer()

@router.callback_query(F.data.startswith("pay:paid:"))
async def user_paid(c: CallbackQuery):
    payment_id = int(c.data.split(":")[-1])
    USER_PAY[c.from_user.id] = payment_id
    await c.message.answer("Ок ✅ Пришли txid или скрин перевода одним сообщением.")
    await c.answer()

@router.message()
async def payment_proof_or_ignore(m: Message):
    # ловим доказательство оплаты, если юзер в режиме "я оплатил"
    user_id = m.from_user.id
    if user_id not in USER_PAY:
        return  # пусть обработают другие хендлеры

    settings = get_settings()
    payment_id = USER_PAY.pop(user_id)

    # proof: txid from text or file_id
    proof = m.text or ""
    if not proof:
        # any media/file
        if m.photo:
            proof = f"photo_file_id:{m.photo[-1].file_id}"
        elif m.document:
            proof = f"doc_file_id:{m.document.file_id}"
        elif m.video:
            proof = f"video_file_id:{m.video.file_id}"
        else:
            proof = "unknown_proof"

    async with aiosqlite.connect("bot.sqlite3") as db:
        await set_payment_proof(db, payment_id, proof)
        topic_id = await ensure_user_topic(m.bot, db, settings.ADMIN_CHAT_ID, user_id, m.from_user.username)

    # В ветку: заявка + кнопки принять/отклонить
    await m.bot.send_message(
        chat_id=settings.ADMIN_CHAT_ID,
        message_thread_id=topic_id,
        text=f"🧾 *Заявка на оплату*\nPayment ID: `{payment_id}`\nПользователь: `{user_id}`\nProof: `{proof}`",
        parse_mode="Markdown",
        reply_markup=admin_payment_kb(payment_id)
    )
    await forward_to_topic(m.bot, settings.ADMIN_CHAT_ID, topic_id, m, prefix="📎 Доказательство оплаты от пользователя:")

    await m.answer(PAYMENT_SUBMITTED)
