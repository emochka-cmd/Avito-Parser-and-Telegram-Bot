from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from database_istance import db
import asyncio
from ScrollPage import ScrollPage
import validators
import os


class AdminStates(StatesGroup):
    waiting_for_url = State()
    parsing_in_progress = State()

# --- Создаем роутер --- 
admin_router = Router()

# --- Список админов ---
ADMINS = list(map(int, os.getenv("TgAdmins", "0").split(",")))

# --- Ограничиваем роутер только для админов ---
admin_router.message.filter(F.from_user.id.in_(ADMINS))
admin_router.callback_query.filter(F.from_user.id.in_(ADMINS))

active_parser: ScrollPage | None = None

# --- Все клавиатуры: ---
def start_parsing_kb() -> InlineKeyboardMarkup:
    inline_main = [
        [InlineKeyboardButton(text="✅ Да", callback_data='parse_confirm_yes'),
        InlineKeyboardButton(text="❌ Нет", callback_data='parse_confirm_no')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_main)


def stop_parsing_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="⏹ Остановить парсинг", callback_data='stop_parsing')]]
    )

    
def main_kb() -> InlineKeyboardMarkup:
    inline_main = [
        [InlineKeyboardButton(text="📜 Информация о 5 последних объявлениях", callback_data='info_five_ads')],
        [InlineKeyboardButton(text="🔎 Количество новых объявлений по теме", callback_data='ads_count')],
        [InlineKeyboardButton(text="🔄 Включить/Выключить авто-отправку", callback_data='avto')],
        [InlineKeyboardButton(text="🗑️ Стереть все из базы", callback_data='clear_all')],
        [InlineKeyboardButton(text="📥  Скачать HTML код", callback_data='start_parsing')],
        [InlineKeyboardButton(text="📥  Извлечь данные из HTML кода", callback_data='start_parsing')],
        [InlineKeyboardButton(text="🔍 Узнать текущую ссылку для парсинга", callback_data='current_url')],
        [InlineKeyboardButton(text="🔗 Задать новую ссылку для парсинга", callback_data='new_url')],
        [InlineKeyboardButton(text="📊 Сколько всего объявлений", callback_data='ads_total')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_main)


# --- при Start ---
@admin_router.message(CommandStart())
async def admin_start(message: Message):
    await message.answer_sticker('CAACAgIAAxkBAAERTqxombj0GO3zAAFj_8AHu7XfjbmkoeEAAgEBAAJWnb0KIr6fDrjC5jQ2BA')
    await message.answer("👇 Выберите действие:", reply_markup=main_kb())


# --- Start Parsing ---
async def run_scroll_and_notify(sc: ScrollPage, call: CallbackQuery):
    """
    Запускает парсинг и уведомляет пользователя о прогрессе.
    """
    try:
        for idx, html in enumerate(sc.scroll_all_page()):
            await call.message.answer(f"✅ Скачана страница №{idx+1}")

            # сохраняем страницу
            with open(f"page_{idx}.html", "w", encoding="utf-8") as f:
                f.write(html)

            await asyncio.sleep(0)  # отдаём управление циклу

        await call.message.answer("🏁 Парсинг завершён или был заверешен.", reply_markup=main_kb())
    except Exception as e:
        await call.message.answer(f"⚠️ Ошибка во время парсинга: {e}", reply_markup=main_kb())


@admin_router.callback_query(F.data == 'stop_parsing')
async def stop_parsing(call: CallbackQuery):
    global active_parser
    if not active_parser:
        await call.message.answer("⚠️ Парсер не запущен", reply_markup=main_kb())
        return

    active_parser.stop_scroll()
    await call.message.answer("⏹ Парсинг будет остановлен...")

    
@admin_router.callback_query(F.data == 'start_parsing')
async def start_parsing(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    url =  await db.current_url(tg_id=call.from_user.id)

    if not url:
        await call.message.answer("❌ Сначала установите avito URL для парсинга!")
        return

    await state.set_state(AdminStates.parsing_in_progress)
    await state.update_data(url=url)

    await call.message.answer(f"🔍 Начать парсинг по URL:\n{url}\n\nПродолжить?",
        reply_markup=start_parsing_kb())


async def run_parsing(sc: ScrollPage):
    try:
        await sc.scroll_all_page()
    except Exception as e:
        print(f"Ошибка во время парсинга: {e}")


@admin_router.callback_query(F.data == 'parse_confirm_yes')
async def yes_parsing(call:CallbackQuery, state: FSMContext):
    global active_parser
    data = await state.get_data()
    url = data.get('url')

    if not url:
        await call.message.answer("❌ URL не найден. Сначала установите его.")
        await state.clear()
        return

    active_parser = ScrollPage(url=url)

    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer('🔄 Запускаю парсинг...', reply_markup=stop_parsing_kb())

    # Запускаем синхронный ScrollPage в отдельном потоке
    asyncio.create_task(run_scroll_and_notify(active_parser, call))

    await state.clear()


@admin_router.callback_query(F.data == 'parse_confirm_no')
async def no_parsing(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer('Парсинг отменен, список доступных действий 👇', reply_markup=main_kb())

    
# --- Current URL ---
@admin_router.callback_query(F.data == 'current_url')
async def current_url(call: CallbackQuery):
    await call.message.edit_reply_markup(reply_markup=None)
    url = await db.current_url(tg_id=call.from_user.id)
    await call.message.answer(f'Текущая ссылка для парсинга: {url}') 

# --- Код отвечающий за изменение URL ---
@admin_router.callback_query(F.data == 'new_url')
async def change_url(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer('Введите новую Avito ссылку для парсинга:')
    await state.set_state(AdminStates.waiting_for_url)


@admin_router.message(AdminStates.waiting_for_url)
async def save_new_url(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    url = message.text.strip()

    if not validators.url(url):
        await message.answer("❌ Это не похоже на корректный URL. Попробуйте ещё раз:")
        return

    try:
        await db.change_url(tg_id=tg_id, url=url)
        await message.answer("✅ Url для парсинга изменён.")
    except Exception as e:
        print(f'Ошибка при изменении url для парсинга: {e}')
        await message.answer("⚠️ Произошла ошибка при сохранении URL.")
    finally:
        await state.clear()


# --- Количество всех объявлений ---
@admin_router.callback_query(F.data == 'ads_total')
async def ads_total(call: CallbackQuery):
    try:
        await call.message.edit_reply_markup(reply_markup=None)
        total = await db.count_ads()
        await call.message.answer(f'📊 В базе данных сейчас {total} объявлений.')
    except Exception as e:
        print(f'Ошибка при показе количества элементов в БД: {e}')
        await call.message.answer("⚠️ Ошибка при получении данных из базы.")
