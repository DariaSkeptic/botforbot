import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat
from aiogram.client.default import DefaultBotProperties
import logging
from config import BOT_TOKEN, ADMIN_CHAT_ID, ADMIN_USER_ID
from packages_with_antispam import init_db

load_dotenv()

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

from start_router import router as start_router
from packages_with_antispam import router as packages_router
from audit_router import router as audit_router

dp.include_router(start_router)
dp.include_router(packages_router)
dp.include_router(audit_router)

async def set_commands():
    public_cmds = [
        BotCommand(command="start", description="Начать"),
        BotCommand(command="packages", description="Пакеты и цены"),
    ]
    await bot.set_my_commands(public_cmds, scope=BotCommandScopeDefault())

    admin_cmds = public_cmds + [
        BotCommand(command="admin", description="Панель администратора"),
        BotCommand(command="where", description="Показать chat.id и тип"),
        BotCommand(command="panic", description="Экстренно выйти из чата"),
    ]
    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=ADMIN_CHAT_ID))
    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=ADMIN_USER_ID))

async def main():
    try:
        logging.info("Инициализация базы антиспама...")
        init_db()
        logging.info("Удаление вебхука...")
        await bot.delete_webhook(drop_pending_updates=True)
        logging.info("Установка команд...")
        await set_commands()
        logging.info("Запуск polling...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Ошибка при запуске бота: {e}")

if __name__ == "__main__":
    asyncio.run(main())