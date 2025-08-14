import logging
from io import BytesIO
from aiogram import types
from keyboards import get_back_to_main_menu
from config import MAX_MESSAGE_LENGTH, bot, MAX_ARTICLES
from parser import fetch_article_content, search_articles

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
    # Маппинг slug'ов рубрик на поисковые запросы
    rubrika_queries = {
        "trudovoe-pravo": "трудовое право",
        "nalogi-vznosy": "налоги и взносы",
        "kadrovoe-deloproizvodstvo": "кадровое делопроизводство",
        "otpuska": "отпуска",
        "bolnichnye": "больничные",
        "zarplata": "зарплата",
        "ohrana-truda": "охрана труда",
        "prakticheskie-voprosy": "практические вопросы"
    }
    
    query = rubrika_queries.get(rubrika_slug, rubrika_slug.replace("-", " "))
    print(f"{datetime.now()}: Парсинг рубрики '{rubrika_slug}' с поисковым запросом: {query}")
    
    try:
        # Используем search_articles для получения статей
        articles = await search_articles(query, "ru")
        return articles[:MAX_ARTICLES]
    except Exception as e:
        print(f"{datetime.now()}: Ошибка при парсинге рубрики {rubrika_slug}: {e}")
        return []