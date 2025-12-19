from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseModel):
    BOT_TOKEN: str
    ADMIN_CHAT_ID: int
    OWNER_ID: int

    OPENAI_API_KEY: str
    OPENAI_TEXT_MODEL: str = "gpt-4.1-mini"
    OPENAI_VISION_MODEL: str = "gpt-4.1-mini"

    WALLET_USDT_TON: str = ""
    WALLET_USDT_TRON: str = ""
    WALLET_TON: str = ""

    PACKAGES_USD: str = "10:10,25:30,50:70"

    REF_BONUS_1: int = 1
    REF_BONUS_5: int = 5

    FREE_START_QUERIES: int = 3

def get_settings() -> Settings:
    return Settings(
        BOT_TOKEN=os.getenv("BOT_TOKEN", ""),
        ADMIN_CHAT_ID=int(os.getenv("ADMIN_CHAT_ID", "0")),
        OWNER_ID=int(os.getenv("OWNER_ID", "0")),

        OPENAI_API_KEY=os.getenv("OPENAI_API_KEY", ""),
        OPENAI_TEXT_MODEL=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        OPENAI_VISION_MODEL=os.getenv("OPENAI_VISION_MODEL", "gpt-4.1-mini"),

        WALLET_USDT_TON=os.getenv("WALLET_USDT_TON", ""),
        WALLET_USDT_TRON=os.getenv("WALLET_USDT_TRON", ""),
        WALLET_TON=os.getenv("WALLET_TON", ""),

        PACKAGES_USD=os.getenv("PACKAGES_USD", "10:10,25:30,50:70"),

        REF_BONUS_1=int(os.getenv("REF_BONUS_1", "1")),
        REF_BONUS_5=int(os.getenv("REF_BONUS_5", "5")),

        FREE_START_QUERIES=int(os.getenv("FREE_START_QUERIES", "3")),
    )
