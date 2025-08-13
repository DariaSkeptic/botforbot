from typing import Optional
from datetime import datetime
from aiogram import Router, types, F, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from config import ADMIN_CHAT_ID, ADMIN_USER_ID
import logging

router = Router()

_last_non_private_chat_id: Optional[int] = None
_last_non_private_title: Optional[str] = None
_last_non_private_type: Optional[str] = None

def _remember_chat(c: types.Chat):
    global _last_non_private_chat_id, _last_non_private_title, _last_non_private_type
    if c.type in ("group", "supergroup", "channel"):
        _last_non_private_chat_id = c.id
        _last_non_private_title = c.title
        _last_non_private_type = c.type
        logging.info(f"Запомнен чат: id={c.id}, type={c.type}, title={c.title}")

def _is_admin_context(msg: types.Message) -> bool:
    if not msg or not msg.chat or not msg.from_user:
        return False
    in_admin_chat = msg.chat.id == ADMIN_CHAT_ID and msg.from_user.id == ADMIN_USER_ID
    in_admin_dm = msg.chat.type == "private" and msg.from_user.id == ADMIN_USER_ID
    return in_admin_chat or in_admin_dm

def admin_keyboard():
    kb = InlineKeyboardBuilder()
    kb.button(text="📍 Где я?", callback_data="admin:where")
    kb.button(text="🚨 Выйти из последнего чата", callback_data="admin:panic")
    kb.button(text="🧾 Последний чат (id/title)", callback_data="admin:last")
    kb.adjust(1)
    return kb.as_markup()

@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    if not _is_admin_context(message):
        return
    await message.answer("Панель администратора:", reply_markup=admin_keyboard())
    logging.info(f"Админ-панель открыта для {message.from_user.id}")

async def show_where(chat: types.Chat, user: types.User, output: types.Message | types.CallbackQuery):
    text = (
        f"chat.id = <code>{chat.id}</code>\n"
        f"type = <b>{chat.type}</b>\n"
        f"title = {chat.title or '—'}\n"
        f"user = @{user.username or '—'} | id={user.id}"
    )
    if isinstance(output, types.CallbackQuery):
        await output.message.answer(text)
        await output.answer()
    else:
        await output.answer(text)
    logging.info(f"Показана информация о чате для {user.id}")

async def perform_panic(bot: Bot, target_id: Optional[int], output: types.Message | types.CallbackQuery):
    if not target_id:
        text = "Не знаю, из какого чата выходить. Укажи: <code>/panic &lt;chat_id&gt;</code> или дождись сообщения из группы/канала."
        if isinstance(output, types.CallbackQuery):
            await output.message.answer(text)
            await output.answer()
        else:
            await output.answer(text)
        return
    try:
        await bot.leave_chat(target_id)
        text = f"🚨 Вышла из чата {target_id} ({_last_non_private_type or 'unknown'} • {_last_non_private_title or '—'})."
        if isinstance(output, types.CallbackQuery):
            await output.message.answer(text)
            await output.answer()
        else:
            await output.answer(text)
        logging.info(f"Бот покинул чат {target_id}")
    except Exception as e:
        text = f"Не удалось выйти: {e}"
        if isinstance(output, types.CallbackQuery):
            await output.message.answer(text)
            await output.answer()
        else:
            await output.answer(text)
        logging.error(f"Ошибка при выходе из чата {target_id}: {e}")

@router.callback_query(F.data == "admin:where")
async def admin_where(call: types.CallbackQuery):
    if not _is_admin_context(call.message):
        return
    await show_where(call.message.chat, call.from_user, call)

@router.callback_query(F.data == "admin:last")
async def admin_last(call: types.CallbackQuery):
    if not _is_admin_context(call.message):

> Daria Skeptic | Таро | Матрица Судьбы | Украшения:
return
    if _last_non_private_chat_id:
        await call.message.answer(
            f"Последний чат: <code>{_last_non_private_chat_id}</code>\n"
            f"type: {_last_non_private_type or '—'} | title: {_last_non_private_title or '—'}"
        )
    else:
        await call.message.answer("Пока нет ни одной записи о группах/каналах.")
    await call.answer()
    logging.info(f"Показан последний чат для {call.from_user.id}")

@router.callback_query(F.data == "admin:panic")
async def admin_panic(call: types.CallbackQuery):
    if not _is_admin_context(call.message):
        return
    await perform_panic(call.bot, _last_non_private_chat_id, call)

@router.message(Command("where"))
async def where(message: types.Message):
    if not _is_admin_context(message):
        return
    await show_where(message.chat, message.from_user, message)

@router.message(Command("panic"))
async def panic(message: types.Message):
    if not _is_admin_context(message):
        return
    args = message.text.strip().split()
    target_id: Optional[int] = None
    if len(args) >= 2:
        try:
            target_id = int(args[1])
        except ValueError:
            await message.answer("Неверный chat_id. Пример: <code>/panic -1001234567890</code>")
            return
    else:
        target_id = _last_non_private_chat_id
    await perform_panic(message.bot, target_id, message)

@router.message(~F.text.startswith("/"), flags={"block": False})
async def log_any_message(message: types.Message):
    c = message.chat
    u = message.from_user
    _remember_chat(c)
    text = (message.text or message.caption or "").strip()
    logging.info(
        f"[MSG] chat_id={c.id} chat_type={c.type} chat_title={repr(c.title)} "
        f"from_id={u.id} from_user=@{u.username or '—'} len={len(text)}"
    )
    if c.type != "private":
        logging.warning(f"NON_PRIVATE_CHAT: {c.type} | title={c.title!r} | id={c.id}")

@router.my_chat_member(flags={"block": False})
async def my_membership(update: types.ChatMemberUpdated):
    c = update.chat
    _remember_chat(c)
    logging.info(
        f"[MY_CHAT_MEMBER] chat_id={c.id} chat_type={c.type} chat_title={repr(c.title)} "
        f"old={update.old_chat_member.status} -> new={update.new_chat_member.status}"
    )

@router.channel_post(flags={"block": False})
async def log_channel_post(message: types.Message):
    c = message.chat
    _remember_chat(c)
    logging.info(
        f"[CHANNEL_POST] chat_id={c.id} chat_title={repr(c.title)} "
        f"len={len(message.text or message.caption or '')}"
    )
