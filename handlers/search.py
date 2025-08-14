from aiogram import Dispatcher, types
from aiogram.fsm.context import FSMContext
from keyboards import get_back_to_main_menu
from utils.helpers import send_article_content, format_search_results_text
from config import user_data, MAX_ARTICLES  # Убедимся, что MAX_ARTICLES импортируется
from parser import search_articles
from states import SearchStates
import logging
from aiogram.utils.keyboard import InlineKeyboardBuilder

logger = logging.getLogger(__name__)

async def handle_search(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.edit_text(
        "🔍 **Поиск по статьям**\n\n"
        "Введите ключевые слова для поиска:\n"
        "Например: 'трудовой договор', 'отпуск', 'налоги' и т.д.",
        reply_markup=get_back_to_main_menu()
    )
    await state.set_state(SearchStates.WAITING_FOR_QUERY)

async def process_search_query(message: types.Message, state: FSMContext):
    query = message.text.strip()
    if len(query) < 2:
        await message.answer("❌ Запрос должен содержать минимум 2 символа. Попробуйте снова:")
        return
    
    try:
        await message.answer("🔍 Ищу статьи по вашему запросу...")
        articles = await search_articles(query, "ru")
        
        if not articles:
            await message.answer(
                f"❌ По запросу '{query}' ничего не найдено.\n"
                "Попробуйте изменить ключевые слова.",
                reply_markup=get_back_to_main_menu()
            )
            await state.clear()
            return
        
        user_data[message.from_user.id] = {"search_results": articles, "search_query": query}
        
        builder = InlineKeyboardBuilder()
        for i in range(min(len(articles), MAX_ARTICLES)):
            title_short = articles[i]["title"][:40] + "..." if len(articles[i]["title"]) > 40 else articles[i]["title"]
            builder.add(types.InlineKeyboardButton(
                text=f"📄 {title_short}",
                callback_data=f"search_article_{i}"
            ))
        builder.add(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
        builder.adjust(1)
        
        results_text = format_search_results_text(articles, query)
        
        await message.answer(results_text, reply_markup=builder.as_markup(), parse_mode='Markdown')
        await state.clear()
        
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        await message.answer(
            "❌ Произошла ошибка при поиске. Попробуйте позже.",
            reply_markup=get_back_to_main_menu()
        )
        await state.clear()

async def handle_search_article(callback: types.CallbackQuery):
    await callback.answer()
    try:
        idx = int(callback.data.split("_")[2])
        user_search_results = user_data.get(callback.from_user.id, {}).get("search_results", [])
        
        if 0 <= idx < len(user_search_results):
            await send_article_content(callback.from_user.id, user_search_results[idx])
        else:
            await callback.message.answer("❌ Статья не найдена", reply_markup=get_back_to_main_menu())
    except (IndexError, ValueError) as e:
        logger.error(f"Ошибка обработки результата поиска: {e}")
        await callback.message.answer("❌ Ошибка: неверный идентификатор статьи", reply_markup=get_back_to_main_menu())

def register_search_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_search, lambda c: c.data == "kadrovik_search")
    dp.message.register(process_search_query, SearchStates.WAITING_FOR_QUERY)
    dp.callback_query.register(handle_search_article, lambda c: c.data.startswith("search_article_"))