from pathlib import Path

def load_brains_text(brains_dir: str) -> str:
    p = Path(brains_dir)
    parts = []
    for name in [
        "SPORTS_MATCH_RED_FLAGS.txt",
        "SPORTS_ANALYTICS_BRAIN.txt",
        "SPORTS_MATCH_ANALYSIS_ENGINE.txt",
        "SPORTS_BETTING_MARKET_INTELLIGENCE.txt",
        "SPORTS_SUPER_INTELLIGENCE_CORE.txt",
    ]:
        fp = p / name
        if fp.exists():
            parts.append(fp.read_text(encoding="utf-8", errors="ignore"))
    return "\n\n".join(parts).strip()

MATCH_EXTRACT_SYSTEM = (
    "Ты извлекаешь данные о футбольном матче из текста или скрина.\n"
    "Верни строго JSON:\n"
    "{"
    "\"match\":\"Команда A vs Команда B\","
    "\"league\":\"...\","
    "\"datetime\":\"...\","
    "\"notes\":\"кратко (коэфф/рынок если видно)\""
    "}\n"
    "Если данных недостаточно — все поля оставь пустыми строками, но JSON верни."
)

FORECAST_SYSTEM_PREFIX = (
    "Ты — премиальный спортивный аналитик.\n"
    "Дай аккуратный вероятностный анализ. Никогда не обещай 100%.\n"
    "Всегда: красные флаги, риски, и рекомендацию 'ставить/не ставить/пропустить'.\n"
)

def build_forecast_system(brains_pack: str) -> str:
    return FORECAST_SYSTEM_PREFIX + "\n\n" + brains_pack

def build_forecast_user(match_text: str) -> str:
    return (
        f"Матч для анализа:\n{match_text}\n\n"
        "Требования к ответу:\n"
        "1) Короткое резюме (2-3 строки)\n"
        "2) Вероятности ключевых исходов (в %)\n"
        "3) Лучшие рынки (1-3 варианта)\n"
        "4) Факторы (форма, мотивация, стили, травмы/состав если известно, календарь)\n"
        "5) Красные флаги (если есть)\n"
        "6) Риски и когда НЕ ставить\n"
        "7) Итог: СТАВИТЬ / НЕ СТАВИТЬ / ПРОПУСТИТЬ + уверенность (A/B/C)\n"
    )
