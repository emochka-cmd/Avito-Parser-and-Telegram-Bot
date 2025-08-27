import asyncio
import os
from aiogram import Bot, Dispatcher
from admin_handlers import admin_router
from user_handlers import user_router
from database_istance import db


class TelegramBot:
    def __init__(self):
        self.bot = Bot(token=os.getenv('TgBot'))
        self.dp = Dispatcher()

        # Подключаем роутеры
        self.dp.include_router(admin_router)
        self.dp.include_router(user_router)

    async def run(self):
        """Запуск программы"""
        print("Bot started")

        # Подключаемся к базе и создаём таблицу
        await db.connect()
        await db.create_table()

        try:
            await self.dp.start_polling(self.bot)
        finally:
            await db.close()


if __name__ == '__main__':
    bot = TelegramBot()
    asyncio.run(bot.run())
