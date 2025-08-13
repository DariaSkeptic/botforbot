import os
from typing import Optional
from urllib.parse import urlparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log"),
    ]
)

def get_bot_token() -> str:
    v = os.getenv("BOT_TOKEN", "").strip()
    if not v:
        raise RuntimeError("BOT_TOKEN не задан в .env")
    return v

def get_admin_chat_id() -> int:
    v = os.getenv("ADMIN_CHAT_ID", "").strip()
    if not v:
        raise RuntimeError("ADMIN_CHAT_ID не задан в .env")
    try:
        return int(v)
    except ValueError:
        raise RuntimeError("ADMIN_CHAT_ID должен быть числом (chat.id)")

def get_admin_user_id() -> int:
    v = os.getenv("ADMIN_USER_ID", "").strip()
    if not v:
        raise RuntimeError("ADMIN_USER_ID не задан в .env")
    try:
        return int(v)
    except ValueError:
        raise RuntimeError("ADMIN_USER_ID должен быть числом (user.id)")

def get_support_link() -> Optional[str]:
    v = os.getenv("SUPPORT_LINK", "").strip()
    if not v:
        return None
    parsed = urlparse(v)
    if parsed.scheme not in ("http", "https"):
        logging.warning("SUPPORT_LINK не является валидным URL — игнорирую")
        return None
    return v

BOT_TOKEN = get_bot_token()
ADMIN_CHAT_ID = get_admin_chat_id()
ADMIN_USER_ID = get_admin_user_id()
SUPPORT_LINK = get_support_link()
