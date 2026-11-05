# LUMIÈRE — сайт с формой заявки + Telegram-бот

Сайт (HTML/CSS/JS) → бэкенд FastAPI → бот aiogram 3 → сообщение администратору в Telegram.

## Запуск за 5 шагов
1. Установите Python 3.10+ (https://www.python.org/downloads/, на Windows отметьте «Add Python to PATH»).
2. В папке проекта:
   - Windows: `python -m venv .venv` → `.venv\Scripts\activate`
   - macOS/Linux: `python3 -m venv .venv` → `source .venv/bin/activate`
   - затем: `pip install -r requirements.txt`
3. Создайте бота в @BotFather (`/newbot`) и вставьте токен в `.env` → `BOT_TOKEN=...`
4. Запустите `python main.py`, напишите своему боту `/start` — он пришлёт ваш ID.
   Вставьте его в `.env` → `ADMIN_ID=...` и перезапустите (Ctrl+C, затем снова `python main.py`).
5. Откройте http://127.0.0.1:8000 и отправьте тестовую заявку.

Если Telegram недоступен, заявка всё равно сохраняется в `leads.jsonl`, а ошибка пишется в консоль.
