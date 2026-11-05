"""Настройки проекта. Все секреты читаются из файла .env и никогда не хранятся в коде."""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("config")

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()
TELEGRAM_PROXY: str = os.getenv("TELEGRAM_PROXY", "").strip()
HOST: str = os.getenv("HOST", "127.0.0.1").strip()
PORT: int = int(os.getenv("PORT", "8000"))

try:
    ADMIN_ID: int = int(os.getenv("ADMIN_ID", "0"))
except ValueError:
    ADMIN_ID = 0
    log.error("ADMIN_ID в .env должен быть числом, например 123456789")

if not BOT_TOKEN or "ВСТАВЬТЕ" in BOT_TOKEN:
    log.warning("BOT_TOKEN не задан в .env — сайт заработает, но заявки не будут уходить в Telegram")
if not ADMIN_ID or ADMIN_ID == 123456789:  # 123456789 — пример из .env.example
    ADMIN_ID = 0
    log.warning("ADMIN_ID не задан в .env — напишите боту /start, он пришлёт ваш ID")
