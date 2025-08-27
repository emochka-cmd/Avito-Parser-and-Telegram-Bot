import time
import random
import json
from typing import Dict, Any, Generator
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from fake_useragent import UserAgent


class ScrollPage:
    def __init__(self, url: str = None, cookies: str = 'cookies.json', headless: bool = None):
        """Укажите URL страницы Авито и (опционально) файл cookies"""
        if url is None:
            raise ValueError("Укажите ссылку на страницу Авито. Программа остановлена!")

        self.url = url
        self.cookies = cookies
        self.headless = headless
        self.options = uc.ChromeOptions()
        self._seting_options()

        self.driver = uc.Chrome(options=self.options)
        self.driver.get(url)
        self._load_cookies()
        self.driver.refresh()


        check = self._check_block()
        if check["blocked"] or check["captcha"]:
            print(f"⚠️ Обнаружена защита: {check}")
        else:
            print("✅ Нет блокировок, всё хорошо")

        time.sleep(random.uniform(1.5, 2))


    def _scroll_one_page(self) -> str:
        ads_viewed = 0
        last_count = 0
        try:
            while True:
                # Получаем список объявлений
                ads = self.driver.find_elements(By.CSS_SELECTOR, "div[data-marker='item']")
                current_count = len(ads)

                if current_count == 0:
                    time.sleep(1)
                    continue

                # "Просматриваем" объявления
                while ads_viewed < current_count:
                    try:
                        ad = ads[ads_viewed]
                        # Скроллим к объявлению (будто пользователь долистал до него)
                        self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", ad)
                        time.sleep(random.uniform(0.5, 1.5))
                        ads_viewed += 1
                    except StaleElementReferenceException:
                        ads = self.driver.find_elements(By.CSS_SELECTOR, "div[data-marker='item']")
                        current_count = len(ads)
                        continue

                # Скроллим вниз ещё на один экран
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(2)

                # Ждём подгрузки новых объявлений (или конца)
                ads = self.driver.find_elements(By.CSS_SELECTOR, "div[data-marker='item']")
                if len(ads) <= last_count:
                    print("📄 Достигнут конец страницы (новых объявлений нет)")
                    break

                last_count = len(ads)

        except Exception as e:
            print(f"⚠️ Ошибка при скролле: {e}")
            return ""
        
        return self.driver.page_source


    def scroll_all_page(self) -> Generator:
        try:
            while True:
                try:
                # Ждем загрузки хотя бы одного объявления
                    self.wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-marker="item"]'))
                            )
                    print("✅ Объявления загружены")
                except Exception as e:
                    print(f"⚠️ Таймаут ожидания объявлений: {e}")

                # отдаем текущую страницу
                yield self._scroll_one_page()
                try:
                    next_button = self.driver.find_element(By.CSS_SELECTOR, 'a[data-marker="pagination-button/nextPage"]')

                    if not next_button.is_displayed() or not next_button.is_enabled():
                        print("⚠️ Кнопка 'следующая страница' недоступна")
                        break

                    # скроллим к центру экрана
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                    time.sleep(0.5)

                    print("➡️ Переход на следующую страницу ")
                    self.driver.execute_script("arguments[0].click();", next_button)

                    time.sleep(random.uniform(3, 6))  # ждём подгрузки страницы

                    try:
                        self.wait.until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-marker="item"]'))
                            )
                        print("✅ Новая страница загружена")
                    except Exception as e:
                        print(f"⚠️ Таймаут загрузки новой страницы: {e}")

                except NoSuchElementException:
                    print("✅ Кнопка 'следующая страница' не найдена, конец пагинации")
                    break

        except Exception as e:
            print(f"⚠️ Скролл не выполнен: {e}")
        

    def _seting_options(self) -> None:
        """Настройки UC"""
        self.options.add_argument("--no-sandbox")
        self.options.add_argument("--disable-infobars")
        self.options.add_argument("--start-maximized")
        self.options.add_argument("--lang=ru-RU")

        if self.headless:
            self.options.add_argument("--headless=new")
            self.options.add_argument("--disable-gpu")

        ua = UserAgent()
        self.options.add_argument(f"user-agent={ua.random}")


    def _check_block(self) -> Dict[str, Any]:
        """ Проверка на блок """
        result = {"blocked": False, "captcha": False, "res": "Ok"}
        page_source = self.driver.page_source.lower()
        block_markers = ["access denied", "forbidden", "your request looks automated", "too many requests"]
        captcha_markers = ["captcha", "подтвердите что вы не робот"]
        if any(marker in page_source for marker in block_markers):
            result["blocked"] = True
        if any(marker in page_source for marker in captcha_markers):
            result["captcha"] = True
        return result


    def _save_cookies(self) -> None:
        """Сохраняем куки в JSON"""
        with open(self.cookies, "w", encoding="utf-8") as f:
            json.dump(self.driver.get_cookies(), f, ensure_ascii=False, indent=2)
        print("💾 Cookies сохранены (JSON)")


    def _load_cookies(self) -> None:
        """Загружаем куки из JSON"""
        try:
            with open(self.cookies, "r", encoding="utf-8") as f:
                cookies = json.load(f)
                for cookie in cookies:
                    cookie.pop("sameSite", None)
                    self.driver.add_cookie(cookie)
            print("✅ Cookies найдены и загружены (JSON).")
        except FileNotFoundError:
            print("⚠️ Cookies не найдены, будет создана новая сессия")

        
    def close(self) -> None:
        """Закрываем браузер с сохранением cookies"""
        self._save_cookies()
        self.driver.quit()


if __name__ == '__main__':
    page = ScrollPage(url='https://www.avito.ru/novorossiysk/fototehnika/zerkalnye_fotoapparaty-ASgBAgICAUS~A7AX?cd=1&q=canon+5d+mark+iii')
    try:
        for idx, html in enumerate(page.scroll_all_page(), start=1):
            print(f"Страница {idx} сохранена.")
            print(html[:1000])  # выводим первые 1000 символов, чтобы не захламлять консоль
            # Можно сохранить в файл
            with open(f"page_{idx}.html", "w", encoding="utf-8") as f:
                f.write(html)
    finally:
        page.close()