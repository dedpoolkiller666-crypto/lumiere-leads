"""
Telegram-бот на aiogram 3 (асинхронный).

Что делает:
  • /start и /id — присылает ваш Telegram ID (нужен для ADMIN_ID в .env);
  • send_lead() — отправляет администратору заявку с сайта в HTML-формате.

Обычно бот запускается вместе с сайтом командой `python main.py`.
Отдельный запуск `python bot.py` нужен только чтобы узнать свой ID,
пока сайт выключен (одновременно запускать оба нельзя — Telegram вернёт ошибку Conflict).
"""
import asyncio
import html
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.types import Message
from aiogram.utils.token import TokenValidationError

import config

log = logging.getLogger("bot")


def create_bot() -> Bot | None:
    """Создаёт объект бота. Если токен пустой или неверного формата — возвращает None, сайт при этом работает."""
    if not config.BOT_TOKEN or "ВСТАВЬТЕ" in config.BOT_TOKEN:
        return None
    try:
        session = AiohttpSession(proxy=config.TELEGRAM_PROXY) if config.TELEGRAM_PROXY else AiohttpSession()
        return Bot(
            token=config.BOT_TOKEN,
            session=session,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    except TokenValidationError:
        log.error("BOT_TOKEN в .env имеет неверный формат. Скопируйте токен из @BotFather целиком.")
        return None


bot: Bot | None = create_bot()
dp = Dispatcher()


# ---------- Команды бота ----------
@dp.message(CommandStart())
@dp.message(Command("id"))
async def cmd_start(message: Message) -> None:
    user_id = message.from_user.id
    if user_id == config.ADMIN_ID:
        text = (
            "✅ <b>Вы администратор.</b>\n"
            "Новые заявки с сайта будут приходить в этот чат.\n\n"
            f"Ваш ID: <code>{user_id}</code>"
        )
    else:
        text = (
            "👋 Привет! Это бот для заявок с сайта.\n\n"
            f"Ваш Telegram ID: <code>{user_id}</code>\n\n"
            "Скопируйте это число в файл <code>.env</code> → <code>ADMIN_ID=</code> "
            "и перезапустите сайт."
        )
    await message.answer(text)


# ---------- Отправка заявки администратору ----------
def format_lead(lead: dict) -> str:
    """Собирает красивое HTML-сообщение. Все данные пользователя экранируются, чтобы не сломать разметку."""
    e = lambda v: html.escape(str(v or "").strip()) or "—"  # noqa: E731
    return (
        "🔔 <b>Новая заявка с сайта!</b>\n\n"
        f"👤 <b>Имя:</b> {e(lead.get('name'))}\n"
        f"📞 <b>Телефон:</b> {e(lead.get('phone'))}\n"
        f"📧 <b>Email:</b> {e(lead.get('email'))}\n"
        f"💬 <b>Комментарий:</b> {e(lead.get('comment'))}\n\n"
        f"🕒 <i>{datetime.now().strftime('%d.%m.%Y %H:%M')}</i>"
    )


async def send_lead(lead: dict) -> bool:
    """
    Отправляет заявку администратору.
    Возвращает True при успехе и False при любой ошибке — ошибка пишется в консоль, сайт не падает.
    """
    if bot is None:
        log.error("Заявка не отправлена в Telegram: бот не настроен (проверьте BOT_TOKEN в .env)")
        return False
    if not config.ADMIN_ID:
        log.error("Заявка не отправлена в Telegram: не задан ADMIN_ID в .env")
        return False
    try:
        await bot.send_message(
            chat_id=config.ADMIN_ID,
            text=format_lead(lead),
            disable_web_page_preview=True,
            request_timeout=15,
        )
        log.info("Заявка от %s отправлена в Telegram", lead.get("name"))
        return True
    except Exception as exc:  # бот заблокирован, нет сети, неверный ID и т. д.
        log.error("Не удалось отправить заявку в Telegram: %s: %s", type(exc).__name__, exc)
        if "chat not found" in str(exc).lower():
            log.error("Подсказка: сначала напишите своему боту /start, а в ADMIN_ID укажите свой ID")
        return False


async def run_polling() -> None:
    """Слушает команды бота (/start, /id). Ошибки не роняют сайт — только пишутся в консоль."""
    if bot is None:
        return
    try:
        me = await bot.get_me()
        log.info("Бот @%s запущен. Напишите ему /start в Telegram", me.username)
        await dp.start_polling(bot, handle_signals=False)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        log.error("Бот не запустился: %s: %s. Сайт продолжает работать.", type(exc).__name__, exc)


if __name__ == "__main__":
    # Отдельный запуск бота (только чтобы узнать свой ID): python bot.py
    if bot is None:
        raise SystemExit("Укажите BOT_TOKEN в файле .env")
    asyncio.run(run_polling())
