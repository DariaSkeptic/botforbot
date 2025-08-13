from aiogram import Router, types, F
from aiogram.filters import CommandStart
from config import SUPPORT_LINK
import logging

router = Router()

async def _send_start(message: types.Message):
    user = message.from_user
    uname = f"@{user.username}" if user.username else (user.full_name or "друг")
    text = (
        f"Привет, {uname}!\n"
        "Я бот, который поможет тебе оформить заявку на своего собственного бота.\n"
        "Выбери нужный раздел через клавиатуру ниже."
    )
    keyboard = [[types.KeyboardButton(text="Пакеты")]]
    if SUPPORT_LINK:
        keyboard.append([types.KeyboardButton(text="Поддержка")])
    kb = types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        selective=True
    )
    await message.answer(text, reply_markup=kb)
    logging.info(f"Отправлено приветствие пользователю {user.id}")

@router.message(CommandStart())
async def on_start_cmd(message: types.Message):
    await _send_start(message)

@router.message(F.text.casefold() == "старт")
async def on_start_text(message: types.Message):
    await _send_start(message)

@router.message(F.text == "Поддержка")
async def support(message: types.Message):
    if SUPPORT_LINK:
        await message.answer(f"Свяжитесь с поддержкой: {SUPPORT_LINK}")
    else:
        await message.answer("Ссылка на поддержку не настроена.")
    logging.info(f"Обработан запрос поддержки от {message.from_user.id}")