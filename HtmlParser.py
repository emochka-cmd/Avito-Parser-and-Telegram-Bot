import asyncio
from bs4 import BeautifulSoup


class Parser:
    def __init__(self, html: str):
        self.soup = BeautifulSoup(html, 'lxml')


    async def parsed(self):
        def _get_price(ad):
            # 1. Попробуем meta[itemprop='price']
            price_meta = ad.select_one("meta[itemprop='price']")
            if price_meta and price_meta.get("content"):
                return price_meta["content"].strip()

            # 2. Попробуем span с data-marker='item-price'
            price_span = ad.select_one("span[data-marker='item-price']")
            if price_span:
                text = price_span.get_text(strip=True)
                if text:
                    return text

            # 3. Если ничего не найдено
            return "Договорная"


        result = []

        
        ads = self.soup.select('div[data-marker="item"]')
        for ad in ads:
            # Фото
            img_tag = ad.select_one('[data-marker="item-photo"] img')
            image = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("data-original") if img_tag else None

            # Заголовок
            title_tag = ad.select_one('[data-marker="item-title"]')
            title = title_tag.get_text(strip=True) if title_tag else None

            # Описание
            description_tag = ad.select_one('div[class*="bottomBlock"] p')
            description = description_tag.get_text(strip=True) if description_tag else None

            # Цена
            price = _get_price(ad)

            # Ссылка
            link_tag = ad.select_one('a[data-marker="item-title"]')
            url = "https://www.avito.ru" + link_tag["href"] if link_tag else None

            # Время объявления
            ad_time_tag = ad.select_one('[data-marker="item-date"]')
            ad_time = ad_time_tag.get("datetime") or ad_time_tag.get_text(strip=True) if ad_time_tag else None

            # Продавец
            seller_name_tag = ad.select_one('[data-marker="seller-info/name"]')
            seller_name = seller_name_tag.get_text(strip=True) if seller_name_tag else None

            # Рейтинг продавца
            seller_grade_tag = ad.select_one('[data-marker="seller-info/score"]')
            seller_grade = seller_grade_tag.get_text(strip=True) if seller_grade_tag else None

            result.append({
                "image": image,
                "title": title,
                "description": description,
                "price": price,
                "url": url,
                "ad_time": ad_time,
                "seller": seller_name,
                "seller_grade": seller_grade
            })

        return result


async def main():
    # читаем локальный HTML
    with open("page_1.html", "r", encoding="utf-8") as f:
        html = f.read()

    # создаём парсер
    parser = Parser(html)

    # запускаем парсинг
    ads = await parser.parsed()
    print (len(ads))
    


if __name__ == "__main__":
    asyncio.run(main())