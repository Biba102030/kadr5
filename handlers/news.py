from aiogram import Dispatcher, types
from config import user_data, news_parser
from keyboards import get_main_menu, get_back_to_main_menu
from datetime import datetime
import logging
from keyboards import InlineKeyboardBuilder
from parser import fetch_articles_from_site, fetch_article_content

logger = logging.getLogger(__name__)

async def handle_news_callback(callback: types.CallbackQuery):
    """Обработчик кнопки Новости"""
    try:
        await callback.message.edit_text("🔄 Загружаю новости с kadrovik.uz...")
        
        # Парсим 5 новостей с главной страницы
        news_items = await fetch_articles_from_site(lang="ru", limit=5)
        
        if not news_items:
            await callback.message.edit_text(
                "❌ Не удалось загрузить новости с сайта.\n"
                "Попробуйте позже или обратитесь к администратору.",
                reply_markup=InlineKeyboardBuilder().add(
                    types.InlineKeyboardButton(text="◶️ Назад", callback_data="main_menu")
                ).as_markup()
            )
            return
        
        # Сохраняем новости в user_data
        user_data[callback.from_user.id] = {"news_items": news_items}
        
        builder = InlineKeyboardBuilder()
        for i, news in enumerate(news_items):
            title_short = news['title'][:45] + '...' if len(news['title']) > 45 else news['title']
            builder.add(types.InlineKeyboardButton(
                text=f"📰 {title_short}",
                callback_data=f"news_read_{i}"
            ))
        
        builder.row(
            types.InlineKeyboardButton(text="🔄 Обновить", callback_data="news"),
            types.InlineKeyboardButton(text="◶️ Назад", callback_data="main_menu")
        )
        builder.adjust(1)
        
        message_text = "📰 <b>Новости для кадровиков</b>\n"
        message_text += f"🌐 Источник: {news_parser.base_url}\n\n"
        message_text += f"📊 Найдено: {len(news_items)} новостей\n"
        message_text += f"🕒 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        message_text += "👆 <b>Выберите новость для чтения:</b>\n\n"
        
        for i, news in enumerate(news_items[:3]):
            message_text += f"<b>{i+1}.</b> {news['title']}\n"
            message_text += f"📅 {news['date']}\n\n"
        
        if len(news_items) > 3:
            message_text += f"... и еще {len(news_items) - 3} новостей"
        
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode='HTML'
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_news_callback: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при загрузке новостей.\n"
            "Попробуйте позже.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◶️ Назад", callback_data="main_menu")
            ).as_markup()
        )

async def handle_news_read(callback: types.CallbackQuery, news_index: int):
    """Показывает конкретную новость"""
    try:
        news_items = user_data.get(callback.from_user.id, {}).get("news_items", [])
        if news_index >= len(news_items):
            await callback.answer("❌ Новость не найдена")
            return
        
        news = news_items[news_index]
        
        await callback.message.edit_text("🔄 Загружаю полный текст статьи...")
        
        # Парсим содержимое статьи
        full_content = await fetch_article_content(news['url'])
        
        message_text = f"📰 <b>{news['title']}</b>\n\n"
        message_text += f"📅 <i>Дата: {news['date']}</i>\n"
        message_text += f"🌐 <i>Источник: kadrovik.uz</i>\n\n"
        
        if full_content and len(full_content) > 100:
            content_preview = full_content[:2500]
            message_text += f"📄 <b>Содержание:</b>\n\n{content_preview}"
            if len(full_content) > 2500:
                message_text += "\n\n<i>... статья обрезана для отображения в Telegram</i>"
        else:
            message_text += f"📝 <b>Краткое описание:</b>\n\n{news['content']}"
        
        message_text += f"\n\n🔗 <a href='{news['url']}'>Читать полностью на сайте</a>"
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="◶️ К новостям", callback_data="news"),
            types.InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")
        )
        
        await callback.message.edit_text(
            message_text,
            reply_markup=builder.as_markup(),
            parse_mode='HTML',
            disable_web_page_preview=True
        )
        
    except Exception as e:
        logger.error(f"Ошибка в handle_news_read: {e}")
        await callback.message.edit_text(
            "❌ Ошибка при загрузке статьи.\n"
            "Возможно, статья недоступна.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◶️ К новостям", callback_data="news")
            ).as_markup()
        )

async def handle_news_read_callback(callback: types.CallbackQuery):
    await callback.answer()
    try:
        news_index = int(callback.data.split("_")[2])
        await handle_news_read(callback, news_index)
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки новости: {e}")
        await callback.answer("❌ Ошибка при загрузке новости")

def register_news_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_news_callback, lambda c: c.data == "news")
    dp.callback_query.register(handle_news_read_callback, lambda c: c.data.startswith("news_read_"))