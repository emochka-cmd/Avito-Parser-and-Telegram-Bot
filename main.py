import asyncio
from HtmlParser import Parser
from DataBase import DataBase

async def main():
    # Читаем локальный HTML
    with open("page_1.html", "r", encoding="utf-8") as f:
        html = f.read()

    # Парсим объявления
    parser = Parser(html)
    ads = await parser.parsed()
    print(f"Найдено {len(ads)} объявлений.")

    # Подключаемся к базе данных
    db = DataBase()
    await db.connect()
    await db.create_table()
    await db.insert_ads(ads)

    print("Данные успешно сохранены в базе.")
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())
