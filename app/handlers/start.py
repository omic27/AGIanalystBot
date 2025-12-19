from aiogram import Router, F
from aiogram.types import Message
import aiosqlite

from ..config import get_settings
from ..db import create_user_if_needed
from ..referrals import process_referral
from ..keyboards import main_menu
from ..texts import WELCOME

router = Router()

@router.message(F.text.startswith("/start"))
async def start(m: Message):
    settings = get_settings()
    args = m.text.split(maxsplit=1)
    ref = None
    if len(args) == 2:
        ref = args[1].strip()

    async with aiosqlite.connect("bot.sqlite3") as db:
        await create_user_if_needed(
            db=db,
            user_id=m.from_user.id,
            username=m.from_user.username,
            start_queries=settings.FREE_START_QUERIES,
            referred_by=None
        )
        if ref:
            await process_referral(db, ref, m.from_user.id, settings.REF_BONUS_1, settings.REF_BONUS_5)

    await m.answer(WELCOME, reply_markup=main_menu(), parse_mode="Markdown")
