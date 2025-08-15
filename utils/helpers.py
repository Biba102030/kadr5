import logging
from io import BytesIO
from aiogram import types
from keyboards import get_back_to_main_menu
from config import MAX_MESSAGE_LENGTH, bot, MAX_ARTICLES
from parser import fetch_article_content, search_articles
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

async def send_article_content(chat_id: int, article: dict):
    """Отправляет содержимое статьи с обработкой длинных текстов"""
    try:
        content = article.get("text") if "text" in article and article["text"] else await fetch_article_content(article["url"])
        if not content:
            await bot.send_message(chat_id, "❌ Не удалось загрузить содержимое статьи", reply_markup=get_back_to_main_menu())
            return
        header = f"📰 {article['title']}\n"
        if article.get("date"):
            header += f"📅 {article['date']}\n"
        header += f"🔗 {article['url']}\n\n"
        full_content = header + content
        if len(full_content) > MAX_MESSAGE_LENGTH:
            file = BytesIO(full_content.encode("utf-8"))
            file.name = f"{article['title'][:50]}.txt"
            await bot.send_document(chat_id, file, caption="📄 Статья отправлена файлом из-за большого размера", reply_markup=get_back_to_main_menu())
        else:
            await bot.send_message(chat_id, full_content, reply_markup=get_back_to_main_menu(), disable_web_page_preview=True)
    except Exception as e:
        logger.error(f"Ошибка при отправке статьи: {e}")
        await bot.send_message(chat_id, "❌ Произошла ошибка при обработке статьи", reply_markup=get_back_to_main_menu())

def format_search_results_text(articles, query):
    """Форматирует результаты поиска для отображения"""
    results_text = f"🔍 **Результаты поиска** по запросу '{query}':\n\n"
    for i, article in enumerate(articles[:MAX_ARTICLES]):
        title = article["title"][:57] + "..." if len(article["title"]) > 60 else article["title"]
        results_text += f"{i+1}. **{title}**\n"
        if article.get("date"):
            results_text += f"   📅 {article['date']}\n"
        if article.get("text"):
            text_preview = article["text"][:100] + "..." if len(article["text"]) > 100 else article["text"]
            results_text += f"   📝 {text_preview}\n"
        results_text += "\n"
    results_text += f"📊 Найдено статей: {len(articles)}\nВыберите статью для полного просмотра:"
    return results_text

async def fetch_rubrika_articles(rubrika_slug):
    """Получение статей из рубрики через поиск"""
    rubrika_queries = {
        "trudovoe-pravo": "трудовое право",
        "nalogi-vznosy": "налоги",
        "kadrovoe-deloproizvodstvo": "кадровое делопроизводство",
        "otpuska": "отпуск",
        "bolnichnye": "больничный",
        "zarplata": "зарплата",
        "ohrana-truda": "охрана труда",
        "prakticheskie-voprosy": "практические вопросы"
    }
    
    query = rubrika_queries.get(rubrika_slug, rubrika_slug.replace("-", " "))
    print(f"{datetime.now()}: Парсинг рубрики '{rubrika_slug}' с поисковым запросом: {query}")
    
    try:
        articles = await search_articles(query, "ru")
        return articles[:MAX_ARTICLES]
    except Exception as e:
        print(f"{datetime.now()}: Ошибка при парсинге рубрики {rubrika_slug}: {e}")
        return []

async def fetch_topics():
    """Получение списка тем из <ul class='tax-code__list'>"""
    base_url = "https://kadrovik.uz/"
    print(f"{datetime.now()}: Парсим темы с главной страницы: {base_url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(base_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

        topics = []
        topic_list = soup.select("ul.tax-code__list li.tax-code__list-item a.tax-code__list-link")[:10]  # Ограничение до 10 тем
        if topic_list:
            print(f"{datetime.now()}: Найдено {len(topic_list)} тем в <ul class='tax-code__list'>")
            for item in topic_list:
                url = item['href'] if item.get('href') else ''
                title = item.get_text(strip=True) if item.get_text(strip=True) else 'Без названия'
                
                if not url.startswith("http"):
                    url = base_url.rstrip("/") + "/" + url.lstrip("/")
                
                topics.append({
                    "title": title,
                    "url": url
                })
        
        print(f"{datetime.now()}: Найдено тем: {len(topics)}")
        return topics
    except Exception as e:
        print(f"{datetime.now()}: Ошибка при парсинге тем: {e}")
        return []

async def fetch_topic_articles(topic_url):
    """Получение статей из страницы темы"""
    print(f"{datetime.now()}: Парсим статьи с темы: {topic_url}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with aiohttp.ClientSession() as session:
            async with session.get(topic_url, headers=headers, timeout=aiohttp.ClientTimeout(total=6)) as response:
                response.raise_for_status()
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")

        articles = []
        posts_list = soup.select("ul.rec-selected__content-item li a.rec-block__info-post")
        if posts_list:
            print(f"{datetime.now()}: Найдено {len(posts_list)} статей в теме")
            for item in posts_list[:MAX_ARTICLES]:
                title_tag = item.find('h3', class_='info-post__title-item')
                url_link = item['href'] if item.get('href') else ''
                title = title_tag.get_text(strip=True) if title_tag else 'Без заголовка'
                date = datetime.now().strftime('%d.%m.%Y')

                if not url_link.startswith("http"):
                    url_link = "https://kadrovik.uz/" + url_link.lstrip("/")

                articles.append({
                    "title": title,
                    "content": "",
                    "date": date,
                    "emoji": "📰",
                    "url": url_link
                })
        
        print(f"{datetime.now()}: Найдено статей в теме: {len(articles)}")
        return articles[:MAX_ARTICLES]
    except Exception as e:
        print(f"{datetime.now()}: Ошибка при парсинге статей темы {topic_url}: {e}")
        return []