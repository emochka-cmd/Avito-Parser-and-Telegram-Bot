from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from database_istance import db
import os


# --- Создаем ротуер --- 
admin_router = Router()

# --- Список админов ---
ADMINS = list(map(int, os.getenv("TgAdmins", "0").split(",")))

# --- Ограничиваем роутер только для админов ---
admin_router.message.filter(F.chat.id.in_(ADMINS))
admin_router.callback_query.filter(F.from_user.id.in_(ADMINS))


def main_kb() -> InlineKeyboardMarkup:
    inline_main = [
        [InlineKeyboardButton(text="📜 Информация о 5 последних объявлениях", callback_data='info_five_ads')],
        [InlineKeyboardButton(text="🔎 Количество новых объявлений по теме", callback_data='ads_count')],
        [InlineKeyboardButton(text="🔄 Включить/Выключить авто-отправку", callback_data='avto')],
        [InlineKeyboardButton(text="🗑️ Стереть все из базы", callback_data='clear_all')],
        [InlineKeyboardButton(text="🔗 Задать новую ссылку для парсинга", callback_data='new_url')],
        [InlineKeyboardButton(text="📊 Сколько всего объявлений", callback_data='ads_total')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_main)


@admin_router.message(CommandStart())
async def admin_start(message: Message):
    await message.answer_sticker('CAACAgIAAxkBAAERTqxombj0GO3zAAFj_8AHu7XfjbmkoeEAAgEBAAJWnb0KIr6fDrjC5jQ2BA')
    await message.answer("👇 Выберите действие:", reply_markup=main_kb())




@admin_router.callback_query(F.data == 'ads_total')
async def ads_total(call: CallbackQuery):
    try:
        await call.message.edit_reply_markup(reply_markup=None)
        total = await db.count_ads()  # используем объект базы
        await call.message.answer(text=f'На данный момент в базе данных содержится {total} объявлений.')
    except Exception as e:
        print(f'Ошибка при показе количества элементов в БД: {e}')