from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
import aiosqlite
import json

from ..config import get_settings
from ..openai_client import build_openai
from ..analytics_engine import (
    load_brains_text,
    MATCH_EXTRACT_SYSTEM,
    build_forecast_system,
    build_forecast_user
)
from ..db import spend_query, save_forecast
from ..keyboards import match_confirm_kb, main_menu
from ..texts import NOT_ENOUGH_QUERIES, MATCH_CONFIRM_TEMPLATE
from ..utils import new_payload_id

router = Router()

# in-memory payload storage (MVP)
PENDING_MATCH = {}  # payload_id -> dict(user_id, match_text)

def _extract_text_from_message(m: Message) -> tuple[str, list[str]]:
    # return raw_text + image_urls placeholders
    raw = m.text or m.caption or ""
    image_file_ids = []
    if m.photo:
        image_file_ids.append(m.photo[-1].file_id)
    return raw, image_file_ids

async def extract_match_with_openai(m: Message) -> dict:
    settings = get_settings()
    client = build_openai(settings.OPENAI_API_KEY)

    raw_text, image_file_ids = _extract_text_from_message(m)

    # Если есть фото — используем vision: передаём file_id как "input_image" нельзя напрямую.
    # Поэтому MVP: просим юзера прислать текст, а фото форвардим админам.
    # НО: Чтобы работало сразу — делаем так:
    # 1) если текст есть — извлекаем из текста
    # 2) если только фото — просим пользователя добавить подпись/вставить текст (MVP),
    #    позже подключим нормальную загрузку файла в OpenAI (через file bytes).
    if not raw_text and image_file_ids:
        return {"match": "", "league": "", "datetime": "", "notes": "Нужен текст из матча (скопируй/вставь) или добавь подпись."}

    resp = await client.chat.completions.create(
        model=settings.OPENAI_TEXT_MODEL,
        messages=[
            {"role": "system", "content": MATCH_EXTRACT_SYSTEM},
            {"role": "user", "content": raw_text}
        ],
        temperature=0.2
    )
    content = resp.choices[0].message.content or "{}"
    try:
        data = json.loads(content)
    except Exception:
        data = {"match": "", "league": "", "datetime": "", "notes": content[:200]}
    return data

@router.message(F.chat.type == "private")
async def forecast_input(m: Message):
    # Отсекаем команды
    if m.text and m.text.startswith("/"):
        return

    data = await extract_match_with_openai(m)
    match = (data.get("match") or "").strip()
    league = (data.get("league") or "").strip()
    dt = (data.get("datetime") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not match:
        await m.answer("Не смог уверенно распознать матч 😕\n\nПришли *скопированный текст* из матча (команды/лига/дата).", parse_mode="Markdown")
        return

    extra = ""
    if league:
        extra += f"Лига: {league}\n"
    if dt:
        extra += f"Дата/время: {dt}\n"
    if notes:
        extra += f"Заметки: {notes}\n"

    payload_id = new_payload_id()
    PENDING_MATCH[payload_id] = {
        "user_id": m.from_user.id,
        "match_text": f"{match}\n{extra}".strip()
    }

    await m.answer(
        MATCH_CONFIRM_TEMPLATE.format(match=match, extra=extra),
        reply_markup=match_confirm_kb(payload_id),
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("match:no:"))
async def match_no(c: CallbackQuery):
    payload_id = c.data.split(":")[-1]
    PENDING_MATCH.pop(payload_id, None)
    await c.message.answer("Ок, пришли другой скрин/текст матча 👇")
    await c.answer()

@router.callback_query(F.data.startswith("match:ok:"))
async def match_ok(c: CallbackQuery):
    settings = get_settings()
    payload_id = c.data.split(":")[-1]
    payload = PENDING_MATCH.pop(payload_id, None)
    if not payload or payload["user_id"] != c.from_user.id:
        await c.answer("Сессия устарела, отправь матч заново.", show_alert=True)
        return

    # списываем 1 запрос
    async with aiosqlite.connect("bot.sqlite3") as db:
        ok = await spend_query(db, c.from_user.id, 1)
        if not ok:
            await c.message.answer(NOT_ENOUGH_QUERIES, reply_markup=main_menu(), parse_mode="Markdown")
            await c.answer()
            return

    # грузим brains pack
    brains_pack = load_brains_text("data/brains")
    system = build_forecast_system(brains_pack)
    user_prompt = build_forecast_user(payload["match_text"])

    client = build_openai(settings.OPENAI_API_KEY)
    resp = await client.chat.completions.create(
        model=settings.OPENAI_TEXT_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.4
    )
    answer = resp.choices[0].message.content or "Не получилось сформировать ответ."

    async with aiosqlite.connect("bot.sqlite3") as db:
        await save_forecast(db, c.from_user.id, payload["match_text"], answer)

    await c.message.answer(answer, reply_markup=main_menu())
    await c.answer()
