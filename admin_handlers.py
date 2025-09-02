from aiogram.fsm.context import FSMContext
from aiogram import Router, F
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.fsm.state import StatesGroup, State
from database_istance import db
import asyncio
import glob
from ScrollPage import ScrollPage
from HtmlParser import Parser
import validators
import os


class AdminStates(StatesGroup):
    waiting_for_url = State()
    parsing_in_progress = State()
    wait_num = State()
    waitig_message_for_admin = State()


# --- Создаем роутер --- 
admin_router = Router()

# --- Список админов ---
ADMINS = list(map(int, os.getenv("TgAdmins", "0").split(",")))


# --- Владелец бота ---
OWNER = int(os.getenv("Owner", 0))

# --- Ограничиваем роутер только для админов ---
admin_router.message.filter(F.from_user.id.in_(ADMINS))
admin_router.callback_query.filter(F.from_user.id.in_(ADMINS))

active_parser: ScrollPage | None = None

# --- Все клавиатуры: ---

# --- Inline ---
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
        [InlineKeyboardButton(text="🧐 Узнать информацию о обьявлениях", callback_data='get_data')],
        [InlineKeyboardButton(text="📥  Скачать HTML код", callback_data='start_parsing')],
        [InlineKeyboardButton(text="🚀 Извлечь данные из HTML кода", callback_data='extract_data')],
        [InlineKeyboardButton(text="🔍 Узнать текущую ссылку для парсинга", callback_data='current_url')],
        [InlineKeyboardButton(text="🔗 Задать новую ссылку для парсинга", callback_data='new_url')],
        [InlineKeyboardButton(text="📊 Сколько всего объявлений", callback_data='ads_total')],
        [InlineKeyboardButton(text="🗑️ Стереть все из базы", callback_data='clear_all')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=inline_main)


# --- Reply ---
def main_reply_kb() -> ReplyKeyboardMarkup:
    kb_list = [
        [KeyboardButton(text='📝 Меню'), KeyboardButton(text='✏️ Написать админу')]
    ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb_list, resize_keyboard=True, one_time_keyboard=True)
    return keyboard


# --- Логика для reply клавиатур ---
@admin_router.message(F.text == '✏️ Написать админу')
async def reply_write_admin(message: Message, state: FSMContext):
    await message.answer("✍️ Напишите сообщение для администратора. Оно будет переслано ему.")
    await state.set_state(AdminStates.waitig_message_for_admin)


@admin_router.message(F.text == '📝 Меню')
async def send_menu(message: Message):
    await message.answer('📋 Главное меню:', reply_markup=main_kb())


# --- Логика отправки ссобщений администратору ---
@admin_router.message(AdminStates.waitig_message_for_admin)
async def send_message_for_admin(message: Message, state: FSMContext):
    try:
        await message.bot.send_message(OWNER, f"📩 Сообщение от {message.from_user.id}:\n\n{message.text}")
        await message.answer("✅ Ваше сообщение отправлено администратору.", reply_markup=main_reply_kb())
        await state.clear()
    except Exception as e:
        print(f"Ошибка отправки сообщения владельцу: {e}")
    

# --- при Start ---
@admin_router.message(CommandStart())
async def admin_start(message: Message):
    await message.answer_sticker('CAACAgIAAxkBAAERTqxombj0GO3zAAFj_8AHu7XfjbmkoeEAAgEBAAJWnb0KIr6fDrjC5jQ2BA')
    await message.answer("👇 Выберите действие:", reply_markup=main_kb())
    await message.answer("📲 Главное меню доступно на клавиатуре.", reply_markup=main_reply_kb())


# --- Get Data ---
@admin_router.callback_query(F.data == 'get_data')
async def get_data(call: CallbackQuery, state: FSMContext):
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.answer('Введите о скольки обьявлениях хотите получить информацию:', reply_markup=main_reply_kb())
    await state.set_state(AdminStates.wait_num)


@admin_router.message(AdminStates.wait_num)
async def wait_num(message:Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer('Пожалуйста, введите **только число**.')
        return
    num = int(message.text)
    await message.answer(f'Вы запросили информацию о {num} объявлениях:')

    my_dict_list = await db.get_product_data(num=num)

    if not my_dict_list:
        await message.answer("Объявлений не найдено.")
        return

    for idx, ad in enumerate(my_dict_list, start=1):
        text = (
            f"<b>Информация о объявлении {idx}<\b>:\n"
            f"<b>Название:<\b> {ad.get('title')}\n"
            f"<b>Описание:<\b> {ad.get('description')}\n"
            f"<b>Цена:<\b> {ad.get('price')}\n"
            f"<b>Ссылка:<\b> {ad.get('url')}\n"
            f"<b>Дата:<\b> {ad.get('ad_time')}\n"
            f"<b>Продавец:<\b> {ad.get('seller')}\n"
            f"<b>Рейтинг продавца:<\b> {ad.get('seller_grade')}"
        )
        await message.answer(text, parse_mode="HTML", reply_markup=main_reply_kb())
    

# --- Clear all ---
@admin_router.callback_query(F.data == 'clear_all')
async def clear_all_db(call: CallbackQuery):
    await db.deleate_priduct_db()
    await call.message.answer('✅ Бд с товарами успешно удалена', reply_markup=main_reply_kb())


# --- Extract data ---
async def parse_all_html_and_save(db):
    files = sorted(glob.glob("page_*.html"))
    ads_all = []

    for file in files:
        with open(file, "r", encoding="utf-8") as f:
            html = f.read()

        parser = Parser(html)
        ads = await parser.parsed()
        ads_all.extend(ads)

    if ads_all:
        await db.insert_ads(ads_all)
    return len(ads_all)


@admin_router.callback_query(F.data == 'extract_data')
async def exctract_data(call: CallbackQuery):
    """ Запускает извлечение данных из html """
    try:
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("⏳ Извлекаю данные из HTML файлов...")

        before = await db.count_ads()  # сколько было в базе
        total = await parse_all_html_and_save(db)
        after = await db.count_ads()   # сколько стало

        new_count = after - before
        skipped = total - new_count

        if new_count > 0:
            await call.message.answer(
                f"✅ В БД добавлено {new_count} новых объявлений.\n"
                f"⏩ Пропущено как дубликаты: {skipped}",
                reply_markup=main_kb()
            )
        else:
            await call.message.answer("⚠️ Новых объявлений не найдено.", reply_markup=main_kb())

    except Exception as e:
        await call.message.answer(f"⚠️ Ошибка при извлечении: {e}", reply_markup=main_kb())


# --- Start Parsing ---
async def run_scroll_and_notify(sc: ScrollPage, call: CallbackQuery):
    """ Запускает скачивание html """
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
    await call.message.answer(f'Текущая ссылка для парсинга: {url}', reply_markup=main_reply_kb())


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
        await message.answer("✅ Url для парсинга изменён.", reply_markup=main_reply_kb())
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
        await call.message.answer(f'📊 В базе данных сейчас {total} объявлений.', reply_markup=main_reply_kb())
    except Exception as e:
        print(f'Ошибка при показе количества элементов в БД: {e}')
        await call.message.answer("⚠️ Ошибка при получении данных из базы.")
