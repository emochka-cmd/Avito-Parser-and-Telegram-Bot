from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandStart

user_router = Router()


@user_router.message(CommandStart())
async def user_start(message: Message):
    await message.answer("Hello, user!")
