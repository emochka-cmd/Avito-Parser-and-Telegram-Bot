import asyncio
import os
from aiogram import Bot, Dispatcher
from admin_handlers import admin_router
from user_handlers import user_router
from aiogram.fsm.storage.redis import RedisStorage
from database_istance import db


class TelegramBot:
    def __init__(self):
        token = os.getenv('TgBot')
        if not token:
            raise ValueError("❌ Не найден токен TgBot в переменных окружения")
        self.bot = Bot(token=token)


        try:
            self.storage = RedisStorage.from_url("redis://localhost:6379/0")
            print("✅ Redis подключен")
        except Exception as e:
            print(f'❌ Ошибка подключения к redis: {e}')
            self.storage = None

        # Dispatche
        self.dp = Dispatcher(storage=self.storage)

        # Подключаем роутеры
        self.dp.include_router(admin_router)
        self.dp.include_router(user_router)


    async def run(self):
        """Запуск программы"""
        print("🤖 Bot started")

        # Подключаемся к базе и создаём таблицу
        await db.connect()
        await db.create_admins_table()
        await db.create_table()


        try:
            await self.dp.start_polling(self.bot)
        finally:
            await db.close()


if __name__ == '__main__':
    bot = TelegramBot()
    asyncio.run(bot.run())
