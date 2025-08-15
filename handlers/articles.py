from aiogram import Dispatcher, types
from config import user_data, MAX_ARTICLES
from keyboards import get_main_menu, get_back_to_main_menu
from utils.helpers import send_article_content, fetch_topics, fetch_topic_articles
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

async def handle_latest_articles(callback: types.CallbackQuery):
    """Обработчик кнопки Все темы 34"""
    await callback.answer()
    try:
        await callback.message.edit_text("🔄 Загружаю список тем с kadrovik.uz...")
        
        topics = await fetch_topics()
        
        if not topics:
            await callback.message.edit_text(
                "❌ Не удалось загрузить список тем.\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=get_back_to_main_menu()
            )
            return
        
        user_data[callback.from_user.id] = {"topics": topics}
        
        builder = InlineKeyboardBuilder()
        for i, topic in enumerate(topics):
            title_short = topic['title'][:45] + '...' if len(topic['title']) > 45 else topic['title']
            builder.add(types.InlineKeyboardButton(
                text=f"📚 {title_short}",
                callback_data=f"topic_{i}"
            ))
        
        builder.add(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        builder.adjust(1)
        
        topics_list = "\n".join(f"{i+1}. {topic['title']}" for i, topic in enumerate(topics))
        await callback.message.edit_text(
            f"📚 <b>Все темы 34</b>\n\n{topics_list}\n\nВыберите тему для просмотра статей:",
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки тем: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке тем.\n"
            "Попробуйте позже.",
            reply_markup=get_back_to_main_menu()
        )

async def handle_topic(callback: types.CallbackQuery):
    """Обработчик выбора темы"""
    await callback.answer()
    logger.info(f"Обработка callback: {callback.data}")
    try:
        idx = int(callback.data.split("_")[1])
        user_topics = user_data.get(callback.from_user.id, {}).get("topics", [])
        
        if 0 <= idx < len(user_topics):
            topic = user_topics[idx]
            await callback.message.edit_text(f"🔄 Загружаю статьи из темы '{topic['title']}'...")
            
            articles = await fetch_topic_articles(topic['url'])
            
            if not articles:
                await callback.message.edit_text(
                    f"❌ Не удалось загрузить статьи из темы '{topic['title']}'.\n"
                    "Попробуйте позже или выберите другую тему.",
                    reply_markup=InlineKeyboardBuilder().add(
                        types.InlineKeyboardButton(text="◶️ К темам", callback_data="kadrovik_latest")
                    ).as_markup()
                )
                return
            
            user_data[callback.from_user.id]["topic_articles"] = articles
            
            builder = InlineKeyboardBuilder()
            for i, article in enumerate(articles[:MAX_ARTICLES]):
                title_short = article["title"][:45] + "..." if len(article["title"]) > 45 else article["title"]
                builder.add(types.InlineKeyboardButton(
                    text=f"📄 {title_short}",
                    callback_data=f"topic_article_{i}"
                ))
            
            builder.row(
                types.InlineKeyboardButton(text="◶️ К темам", callback_data="kadrovik_latest"),
                types.InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")
            )
            builder.adjust(1)
            
            articles_text = f"📚 <b>{topic['title']}</b>\n\n"
            articles_text += f"📊 Найдено статей: {len(articles)}\n\n"
            
            for i, article in enumerate(articles[:5]):
                articles_text += f"{i+1}. **{article['title']}**\n"
                if article.get("date"):
                    articles_text += f"   📅 {article['date']}\n\n"
            
            if len(articles) > 5:
                articles_text += f"... и еще {len(articles) - 5} статей\n\n"
                
            articles_text += "👆 **Выберите статью для чтения:**"
            
            await callback.message.edit_text(
                articles_text,
                reply_markup=builder.as_markup(),
                parse_mode='Markdown'
            )
        else:
            await callback.message.answer("❌ Тема не найдена", reply_markup=get_back_to_main_menu())
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки темы: {e}")
        await callback.message.answer("❌ Ошибка: неверный идентификатор темы", reply_markup=get_back_to_main_menu())

async def handle_topic_article(callback: types.CallbackQuery):
    """Обработчик выбора статьи из темы"""
    await callback.answer()
    logger.info(f"Обработка callback для статьи: {callback.data}")
    try:
        parts = callback.data.split("_")
        if not parts or len(parts) != 3 or parts[0] != "topic" or parts[1] != "article":
            logger.error(f"Неверный формат callback_data: {callback.data}")
            await callback.message.answer("❌ Неверный формат команды", reply_markup=get_back_to_main_menu())
            return
        
        idx = int(parts[2])  # Извлекаем индекс из topic_article_<index>
        user_articles = user_data.get(callback.from_user.id, {}).get("topic_articles", [])
        
        if 0 <= idx < len(user_articles):
            await send_article_content(callback.from_user.id, user_articles[idx])
        else:
            await callback.message.answer("❌ Статья не найдена", reply_markup=get_back_to_main_menu())
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки статьи: {e}")
        await callback.message.answer("❌ Ошибка: неверный идентификатор статьи", reply_markup=get_back_to_main_menu())

def register_articles_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_latest_articles, lambda c: c.data == "kadrovik_latest")
    dp.callback_query.register(handle_topic, lambda c: c.data.startswith("topic_") and not c.data.startswith("topic_article_"))
    dp.callback_query.register(handle_topic_article, lambda c: c.data.startswith("topic_article_"))