import aiosqlite
import asyncio
import sqlite3


class DataBase:
    def __init__(self):
        self.db_name = 'for_avito.db'
        self.connection: aiosqlite.Connection | None = None


    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row


    # --- Взаимодефствие с БД в которой храняться обьявлениями авито
    async def create_table(self):
        await self.connection.execute("""
            CREATE TABLE IF NOT EXISTS for_avito(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT,
                title TEXT,
                description TEXT,
                price TEXT,
                url TEXT,
                ad_time TEXT,
                seller TEXT,
                seller_grade TEXT
            )
        """)
        await self.connection.commit()


    async def insert_ads(self, ads: list):
        """ Вставляем обьявления """
        values = [
            (
                ad.get("image"),
                ad.get("title"),
                ad.get("description"),
                ad.get("price"),
                ad.get("url"),
                ad.get("ad_time"),
                ad.get("seller"),
                ad.get("seller_grade"),
            )
            for ad in ads
        ]
        await self.connection.executemany("""
            INSERT INTO for_avito(image, title, description, price, url, ad_time, seller, seller_grade)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, values)
        await self.connection.commit()


    async def count_ads(self) -> int:
        """Считает количество объявлений в базе"""
        async with self.connection.execute("SELECT COUNT(*) FROM for_avito") as cursor:
            row = await cursor.fetchone()
            return row[0]


    # --- Взаимодействие с таблицей админов
    async def get_admin_url(self, tg_id: int) -> str | None:
        async with self.connection.execute("""
            SELECT url FROM admins_avito_url WHERE admin_tg = ?
        """, (tg_id,)) as cursor:
            row = await cursor.fetchone()
            return row["url"] if row else None


    async def add_admin(self, tg_id: int):
        await self.connection.execute("""
            INSERT OR IGNORE INTO admins_avito_url(admin_tg) VALUES (?)
        """, (tg_id,))
        await self.connection.commit()


    async def current_url(self, tg_id: int) -> str:
        """ Текущий url админа """
        async with self.connection.execute(
            "SELECT url FROM admins_avito_url WHERE admin_tg = ?", (tg_id, )) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


    async def create_admins_table(self):
        try:
            await self.connection.execute("""
                CREATE TABLE IF NOT EXISTS admins_avito_url(
                    admin_tg INTEGER NOT NULL PRIMARY KEY,
                    url TEXT
                )
            """)
            await self.connection.commit()
        except Exception as e:
            print(f'Ошибка при создании бд: {e}')
        else:
            print('Таблица данных  с url админов создана')


    async def change_url(self, tg_id: int, url: str):
        await self.connection.execute("""
            UPDATE admins_avito_url 
            SET url = ? 
            WHERE admin_tg = ?
        """, (url, tg_id))
        await self.connection.commit()


    # --- Закрытие бд
    async def close(self):
        try:
            await self.connection.close()
            print('Соединение с БД закрыто')
        except Exception as e:
            print(f'Ошибка при закрытии соединения: {e}')


async def main():
    db = DataBase()
    await db.connect()
    await db.create_admins_table()
    await db.create_table()


    # Добавление в таблицу:
    await db.add_admin(5186771276)
    await db.change_url(5186771276, "https://avito.ru/example")
    await db.close()


if __name__ == '__main__':
    asyncio.run(main())
