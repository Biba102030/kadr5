from aiogram import Dispatcher, types
from config import user_data
from keyboards import get_main_menu, get_back_to_main_menu
from parser import fetch_articles_from_site, fetch_article_content
from utils.helpers import send_article_content
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

async def handle_latest_articles(callback: types.CallbackQuery):
    """Обработчик кнопки Актуальные статьи"""
    await callback.answer()
    try:
        await callback.message.edit_text("🔄 Загружаю актуальные статьи с kadrovik.uz...")
        
        # Парсим 5 статей из <ul class="posts-list">
        articles = await fetch_articles_from_site(lang="ru", limit=5)
        
        if not articles:
            await callback.message.edit_text(
                "❌ Не удалось загрузить актуальные статьи с сайта.\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_back_to_main_menu()
            )
            return
        
        # Сохраняем статьи в user_data
        user_data[callback.from_user.id] = {"latest_articles": articles}
        
        builder = InlineKeyboardBuilder()
        for i, article in enumerate(articles):
            title_short = article['title'][:45] + '...' if len(article['title']) > 45 else article['title']
            builder.add(types.InlineKeyboardButton(
                text=f"📄 {title_short}",
                callback_data=f"article_{i}"
            ))
        
        builder.add(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        builder.adjust(1)
        
        articles_list = "\n".join(f"{i+1}. {art['title']}" for i, art in enumerate(articles))
        await callback.message.edit_text(
            f"📰 <b>Актуальные статьи (5 свежих с главной страницы kadrovik.uz)</b>\n\n{articles_list}\n\nВыберите статью для чтения:",
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки актуальных статей: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке статей.\n"
            "Попробуйте позже.",
            reply_markup=get_back_to_main_menu()
        )

async def handle_article(callback: types.CallbackQuery):
    """Обработчик выбора статьи"""
    await callback.answer()
    try:
        idx = int(callback.data.split("_")[1])
        user_articles = user_data.get(callback.from_user.id, {}).get("latest_articles", [])
        
        if 0 <= idx < len(user_articles):
            await send_article_content(callback.from_user.id, user_articles[idx])
        else:
            await callback.message.answer("❌ Статья не найдена", reply_markup=get_back_to_main_menu())
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки статьи: {e}")
        await callback.message.answer("❌ Ошибка: неверный идентификатор статьи", reply_markup=get_back_to_main_menu())

def register_articles_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_latest_articles, lambda c: c.data == "kadrovik_latest")
    dp.callback_query.register(handle_article, lambda c: c.data.startswith("article_"))