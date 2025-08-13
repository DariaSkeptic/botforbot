import sqlite3
from datetime import datetime, timedelta
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_CHAT_ID, SUPPORT_LINK
import logging

router = Router()

WINDOW = timedelta(minutes=30)
MAX_SUBMISSIONS = 2

def init_db():
    conn = sqlite3.connect("antispam.db")
    conn.execute("CREATE TABLE IF NOT EXISTS submissions (user_id INTEGER, timestamp TEXT)")
    conn.commit()
    conn.close()
    logging.info("База антиспама инициализирована")

def _prune(user_id: int):
    conn = sqlite3.connect("antispam.db")
    conn.execute(
        "DELETE FROM submissions WHERE user_id = ? AND timestamp <= ?",
        (user_id, (datetime.utcnow() - WINDOW).isoformat())
    )
    conn.commit()
    conn.close()

def can_submit(user_id: int) -> bool:
    _prune(user_id)
    conn = sqlite3.connect("antispam.db")
    cursor = conn.execute(
        "SELECT COUNT(*) FROM submissions WHERE user_id = ?",
        (user_id,)
    )
    count = cursor.fetchone()[0]
    conn.close()
    return count < MAX_SUBMISSIONS

def mark_submit(user_id: int):
    _prune(user_id)
    conn = sqlite3.connect("antispam.db")
    conn.execute(
        "INSERT INTO submissions (user_id, timestamp) VALUES (?, ?)",
        (user_id, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    logging.info(f"Заявка от user_id={user_id} зарегистрирована")

def minutes_left(user_id: int) -> int:
    _prune(user_id)
    conn = sqlite3.connect("antispam.db")
    cursor = conn.execute(
        "SELECT timestamp FROM submissions WHERE user_id = ? ORDER BY timestamp",
        (user_id,)
    )
    timestamps = cursor.fetchall()
    conn.close()
    if len(timestamps) < MAX_SUBMISSIONS:
        return 0
    release_at = datetime.fromisoformat(timestamps[0][0]) + WINDOW
    delta = (release_at - datetime.utcnow()).total_seconds()
    if delta <= 0:
        return 0
    mins = int(delta // 60) + (1 if delta % 60 else 0)
    return mins

COMPARE_TEXT = (
    "<b>📊 Сравнение пакетов</b>\n\n"
    "<b>Мини-бот — 5 000 ₽</b>\n"
    "• 1–2 функции без сложной логики\n"
    "• Простое меню, выдача файла или сбор заявки\n"
    "• Без интеграций и оплат\n\n"
    "<b>Бот с логикой и интеграциями — 15 000 ₽</b>\n"
    "• Ветвления и условия в сценариях\n"
    "• Интеграции: Google Sheets, CRM, Email, API\n"
    "• Персонализация (например, расчёт по дате рождения)\n\n"
    "<b>Бот под ключ — 30 000 ₽</b>\n"
    "• Всё из пакета «Логика» + базовое оформление в стиле Telegram\n"
    "• Размещение на хостинге и техническая настройка\n"
    "• Контент и тексты — по договорённости (можно готовые материалы клиента)\n"
    "• Готовый к работе бот без необходимости разбираться в коде"
)

TITLES = {
    "mini": "Мини-бот",
    "logic": "Бот с логикой и интеграциями",
    "turnkey": "Бот под ключ",
}

_compare_kb = None

def compare_keyboard():
    global _compare_kb
    if _compare_kb is None:
        kb = InlineKeyboardBuilder()
        kb.button(text="Выбрать Мини-бот", callback_data="pack:choose:mini")
        kb.button(text="Выбрать Логику", callback_data="pack:choose:logic")
        kb.button(text="Выбрать Под ключ", callback_data="pack:choose:turnkey")
        kb.button(text="🔄 Сбросить выбор", callback_data="pack:reset")
        if SUPPORT_LINK:
            kb.button(text="✉️ Написать в поддержку", url=SUPPORT_LINK)
        kb.adjust(1)
        _compare_kb = kb.as_markup()
    return _compare_kb

@router.message(Command("packages"))
async def show_packages(message: types.Message):
    await message.answer(
        COMPARE_TEXT,
        reply_markup=compare_keyboard(),
        disable_web_page_preview=True
    )
    logging.info(f"Показаны пакеты пользователю {message.from_user.id}")

@router.message(F.text.casefold() == "пакеты")
async def show_packages_by_text(message: types.Message):
    await show_packages(message)

@router.callback_query(F.data == "pack:reset")
async def reset_choice(call: types.CallbackQuery):
    await call.message.edit_text(
        COMPARE_TEXT,
        reply_markup=compare_keyboard(),
        disable_web_page_preview=True
    )
    await call.answer("Выбор сброшен")
    logging.info(f"Сброс выбора для {call.from_user.id}")

@router.callback_query(F.data.startswith("pack:choose:"))
async def choose_package(call: types.CallbackQuery):
    try:
        key = call.data.split(":")[-1]
        title = TITLES.get(key, key)
        user = call.from_user
        uid = user.id

        if not can_submit(uid):
            wait = minutes_left(uid)
            msg = "Лимит заявок исчерпан."
            if wait:
                msg += f" Попробуй ещё раз через {wait} мин."
            await call.answer(msg, show_alert=True)
            logging.warning(f"Антиспам: лимит для {uid}")
            return

        admin_text = (
            f"🆕 <b>Заявка на пакет</b>\n"
            f"Пакет: <b>{title}</b>\n"
            f"От: @{user.username or '—'} | {user.full_name} | id={uid}"
        )
        await call.bot.send_message(ADMIN_CHAT_ID, admin_text)
        mark_submit(uid)

        confirm = (
            f"Принято. Пакет <b>{title}</b> зафиксирован.\n"
            "Если промахнулась — жми «🔄 Сбросить выбор» и отправь новую заявку."
        )
        await call.message.edit_text(confirm, reply_markup=compare_keyboard())
        await call.answer("Заявка отправлена")
        logging.info(f"Заявка отправлена от {uid}: {title}")
    except Exception as e:
        logging.error(f"Ошибка в choose_package: {e}")
        await call.answer("Произошла ошибка, попробуйте позже", show_alert=True)