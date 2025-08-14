import asyncio
import logging
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import re

class KadrovikNewsParser:
    def __init__(self):
        self.base_url = "https://kadrovik.uz"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        self.news_cache = []

    async def get_page_content(self, url):
        """Получает содержимое страницы"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=self.headers, timeout=15) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logging.error(f"Ошибка получения страницы {url}: {response.status}")
                        return None
        except asyncio.TimeoutError:
            logging.error(f"Таймаут при запросе к {url}")
            return None
        except Exception as e:
            logging.error(f"Ошибка при запросе к {url}: {e}")
            return None

    def clean_text(self, text):
        """Очищает текст от лишних символов"""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'[^\w\s\-.,!?():;]', '', text)
        return text

    def parse_main_page(self, html_content):
        """Парсит главную страницу и извлекает новости"""
        # ... (весь код метода parse_main_page) ...
        return news_items[:10]

    async def get_news(self):
        """Получает список новостей"""
        html_content = await self.get_page_content(self.base_url)
        if html_content:
            news_list = self.parse_main_page(html_content)
            self.news_cache = news_list
            return news_list
        return []

    async def get_article_content(self, url):
        """Получает полный текст статьи"""
        # ... (весь код метода get_article_content) ...
        return content