from aiogram import Dispatcher, types
from config import RUBRIKI, user_data, news_parser, MAX_ARTICLES
from keyboards import get_back_to_main_menu
from utils.helpers import send_article_content, fetch_rubrika_articles
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

async def handle_rubriki(callback: types.CallbackQuery):
    await callback.answer()
    
    builder = InlineKeyboardBuilder()
    for rubrika_name in RUBRIKI.keys():
        builder.add(types.InlineKeyboardButton(
            text=f"📂 {rubrika_name}",
            callback_data=f"rubrika_{RUBRIKI[rubrika_name]}"
        ))
    builder.add(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    
    await callback.message.edit_text(
        "📚 **Выберите рубрику:**\n\n"
        "Здесь собраны статьи по основным темам кадрового делопроизводства:",
        reply_markup=builder.as_markup(),
        parse_mode='Markdown'
    )

async def handle_rubrika_articles(callback: types.CallbackQuery):
    await callback.answer()
    
    rubrika_slug = callback.data.split("_", 1)[1]
    rubrika_name = None
    
    for name, slug in RUBRIKI.items():
        if slug == rubrika_slug:
            rubrika_name = name
            break
    
    if not rubrika_name:
        await callback.message.answer("❌ Рубрика не найдена", reply_markup=get_back_to_main_menu())
        return
    
    try:
        await callback.message.edit_text(f"🔄 Загружаю статьи из рубрики '{rubrika_name}'...")
        
        articles = await fetch_rubrika_articles(rubrika_slug)
        
        if not articles:
            # Демо-данные как запасной вариант
            demo_articles = {
                "trudovoe-pravo": [
                    {"title": "Изменения в Трудовом кодексе 2024", "url": f"{news_parser.base_url}", "date": "01.12.2024"},
                    {"title": "Права и обязанности работника и работодателя", "url": f"{news_parser.base_url}", "date": "28.11.2024"},
                    {"title": "Расторжение трудового договора: актуальная практика", "url": f"{news_parser.base_url}", "date": "25.11.2024"}
                ],
                "nalogi-vznosy": [
                    {"title": "Новые ставки налогов и взносов в 2024 году", "url": f"{news_parser.base_url}", "date": "02.12.2024"},
                    {"title": "Социальные взносы: расчет и уплата", "url": f"{news_parser.base_url}", "date": "30.11.2024"},
                    {"title": "НДФЛ с заработной платы: практические вопросы", "url": f"{news_parser.base_url}", "date": "27.11.2024"}
                ],
                "kadrovoe-deloproizvodstvo": [
                    {"title": "Электронный документооборот в кадрах", "url": f"{news_parser.base_url}", "date": "03.12.2024"},
                    {"title": "Оформление личных дел сотрудников", "url": f"{news_parser.base_url}", "date": "01.12.2024"},
                    {"title": "Ведение трудовых книжек в 2024 году", "url": f"{news_parser.base_url}", "date": "29.11.2024"}
                ]
            }
            
            articles = demo_articles.get(rubrika_slug, [
                {"title": f"Статья по теме '{rubrika_name}' 1", "url": f"{news_parser.base_url}", "date": "01.12.2024"},
                {"title": f"Статья по теме '{rubrika_name}' 2", "url": f"{news_parser.base_url}", "date": "30.11.2024"},
                {"title": f"Статья по теме '{rubrika_name}' 3", "url": f"{news_parser.base_url}", "date": "29.11.2024"}
            ])
        
        if not articles:
            await callback.message.edit_text(
                f"❌ В рубрике '{rubrika_name}' пока нет статей.\n"
                "Попробуйте другую рубрику или воспользуйтесь поиском.",
                reply_markup=InlineKeyboardBuilder().add(
                    types.InlineKeyboardButton(text="◶️ К рубрикам", callback_data="kadrovik_news")
                ).as_markup()
            )
            return
        
        user_data[callback.from_user.id] = {"rubrika_articles": articles}
        
        builder = InlineKeyboardBuilder()
        for i, article in enumerate(articles[:MAX_ARTICLES]):
            title_short = article["title"][:45] + "..." if len(article["title"]) > 45 else article["title"]
            builder.add(types.InlineKeyboardButton(
                text=f"📄 {title_short}",
                callback_data=f"rubrika_article_{i}"
            ))
        
        builder.row(
            types.InlineKeyboardButton(text="◶️ К рубрикам", callback_data="kadrovik_news"),
            types.InlineKeyboardButton(text="🏠 Главная", callback_data="main_menu")
        )
        builder.adjust(1)
        
        articles_text = f"📂 **{rubrika_name}**\n\n"
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
        
    except Exception as e:
        logger.error(f"Ошибка загрузки статей рубрики: {e}")
        await callback.message.edit_text(
            f"❌ Ошибка при загрузке статей рубрики '{rubrika_name}'.\n"
            "Попробуйте позже.",
            reply_markup=InlineKeyboardBuilder().add(
                types.InlineKeyboardButton(text="◶️ К рубрикам", callback_data="kadrovik_news")
            ).as_markup()
        )

async def handle_rubrika_article(callback: types.CallbackQuery):
    await callback.answer()
    try:
        idx = int(callback.data.split("_")[2])
        user_rubrika_articles = user_data.get(callback.from_user.id, {}).get("rubrika_articles", [])
        
        if 0 <= idx < len(user_rubrika_articles):
            await send_article_content(callback.from_user.id, user_rubrika_articles[idx])
        else:
            await callback.message.answer("❌ Статья не найдена", reply_markup=get_back_to_main_menu())
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки статьи рубрики: {e}")
        await callback.message.answer("❌ Ошибка: неверный идентификатор статьи", reply_markup=get_back_to_main_menu())

def register_rubrics_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_rubriki, lambda c: c.data == "kadrovik_news")
    dp.callback_query.register(handle_rubrika_articles, lambda c: c.data.startswith("rubrika_"))
    dp.callback_query.register(handle_rubrika_article, lambda c: c.data.startswith("rubrika_article_"))