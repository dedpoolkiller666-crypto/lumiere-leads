"""
Бэкенд сайта на FastAPI.

  • отдаёт сайт из папки static/;
  • принимает заявки: POST /api/lead (JSON);
  • проверяет данные, сохраняет копию в leads.jsonl и пересылает заявку в Telegram;
  • в этом же процессе запускает Telegram-бота.

Запуск:  python main.py   →   http://127.0.0.1:8000
"""
import asyncio
import json
import logging
import re
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field, field_validator

import config
from bot import bot, dp, run_polling, send_lead

log = logging.getLogger("site")
BASE_DIR = Path(__file__).resolve().parent
LEADS_FILE = BASE_DIR / "leads.jsonl"


# ---------- Запуск и остановка бота вместе с сайтом ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_polling()) if bot else None
    yield
    if task:
        try:
            await dp.stop_polling()
        except Exception:
            pass
        task.cancel()
    if bot:
        await bot.session.close()


app = FastAPI(title="LUMIÈRE — заявки", lifespan=lifespan, docs_url=None, redoc_url=None)


# ---------- Модель заявки и проверка полей ----------
class Lead(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=5, max_length=30)
    email: EmailStr
    comment: str = Field(default="", max_length=1000)

    @field_validator("name", "comment", mode="before")
    @classmethod
    def strip_text(cls, v):
        return str(v or "").strip()

    @field_validator("phone")
    @classmethod
    def check_phone(cls, v: str) -> str:
        digits = re.sub(r"\D", "", v)
        if not 10 <= len(digits) <= 15:
            raise ValueError("Введите корректный номер телефона")
        return v.strip()


FIELD_ERRORS = {
    "name": "Укажите имя (минимум 2 символа)",
    "phone": "Введите корректный номер телефона",
    "email": "Введите корректный email",
    "comment": "Комментарий слишком длинный (до 1000 символов)",
}


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    errors = {}
    for err in exc.errors():
        field = str(err["loc"][-1])
        errors[field] = FIELD_ERRORS.get(field, "Проверьте поле")
    return JSONResponse(status_code=422, content={"ok": False, "errors": errors})


# ---------- Простая защита от спама: не больше 5 заявок в минуту с одного IP ----------
_hits: dict[str, deque] = defaultdict(deque)


def too_many(ip: str, limit: int = 5, window: int = 60) -> bool:
    now = time.monotonic()
    q = _hits[ip]
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= limit:
        return True
    q.append(now)
    return False


def save_backup(lead: dict) -> None:
    """Резервная копия каждой заявки — на случай, если Telegram недоступен."""
    try:
        with LEADS_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps({**lead, "time": datetime.now().isoformat(timespec="seconds")}, ensure_ascii=False) + "\n")
    except OSError as exc:
        log.error("Не удалось сохранить заявку в %s: %s", LEADS_FILE.name, exc)


# ---------- API ----------
@app.post("/api/lead")
async def create_lead(lead: Lead, request: Request):
    ip = request.client.host if request.client else "unknown"
    if too_many(ip):
        return JSONResponse(status_code=429, content={"ok": False, "message": "Слишком много заявок. Попробуйте через минуту."})

    data = lead.model_dump()
    save_backup(data)
    delivered = await send_lead(data)  # при ошибке вернёт False и запишет причину в консоль
    if not delivered:
        log.warning("Заявка сохранена в %s, но не доставлена в Telegram", LEADS_FILE.name)
    # Посетителю всегда показываем успех: заявка в любом случае сохранена
    return {"ok": True, "delivered": delivered}


@app.get("/api/health")
async def health():
    return {"ok": True, "bot": bot is not None, "admin": bool(config.ADMIN_ID)}


# Сайт (index.html, css, js). Подключается последним, чтобы не перекрывать /api/*
app.mount("/", StaticFiles(directory=BASE_DIR / "static", html=True), name="static")


if __name__ == "__main__":
    log.info("Сайт: http://%s:%s", config.HOST, config.PORT)
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="info")
