import aiosqlite
import sqlite3


class DataBase:
    def __init__(self):
        self.db_name = 'for_avito.db'
        self.connection: aiosqlite.Connection | None = None

    async def connect(self):
        self.connection = await aiosqlite.connect(self.db_name)
        self.connection.row_factory = sqlite3.Row

    
    async def create_admins_table(self):
        await self.connection.execute( """
            CREATE TABLE IF NOT EXIST admins_avito_url(
            admin_tg INT NOT NULL PRIMARY KEY,
            url TEXT)
        """)
        await self.connection.commit()


    async def add_admin(self, tg_id: int):
        await self.connection.execute( """
        
        """)


    async def create_table(self):
        await self.connection.execute( """
            CREATE TABLE IF NOT EXISTS for_avito(
             id INTEGER PRIMARY KEY AUTOINCREMENT,
                image TEXT,
                title TEXT,
                description TEXT,
                price TEXT,
                url TEXT,
                ad_time TEXT,
                seller TEXT,
                seller_grade TEXT) """)
        
        await self.connection.commit()

    
    async def insert_ads(self, ads: list):
        """ Вставляем обьявление """
        values = [
            (ad.get("image"),
            ad.get("title"),
            ad.get("description"),
            ad.get("price"),
            ad.get("url"),
            ad.get("ad_time"),
            ad.get("seller"),
            ad.get("seller_grade"),

            ) for ad in ads
        ]
        await self.connection.executemany("""
        INSERT INTO for_avito(image, title, description, price, url, ad_time, seller, seller_grade)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?) """, values)
        await self.connection.commit()


    async def count_ads(self) -> int:
        """Считает количество объявлений в базе"""
        async with self.connection.execute("SELECT COUNT(*) FROM for_avito") as cursor:
            row = await cursor.fetchone()
            return row[0]

    async def close(self):
        try:
            print('Соединение с бд закрыто')
            await self.connection.close()
        except Exception as e:
            print(f'Ошибка в закрытии соединения: {e}')