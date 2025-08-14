from aiogram import Dispatcher, types
from keyboards import get_main_menu, get_back_to_main_menu
from user_manager import UserManager
import logging

logger = logging.getLogger(__name__)

user_manager = UserManager()

async def handle_help(callback: types.CallbackQuery):
    await callback.answer()
    help_text = """
📋 **Помощь по использованию бота**

🤖 **Основные функции:**
• 📰 **Актуальные статьи** - последние публикации с kadrovik.uz
• 📚 **Рубрики** - статьи по темам (трудовое право, налоги, отпуска и др.)
• 🔍 **Поиск** - найти статьи по ключевым словам
• 🗞️ **Новости** - свежие новости для кадровиков

💡 **Как пользоваться:**
1. Выберите нужную функцию в главном меню
2. Следуйте инструкциям бота
3. Читайте статьи прямо в Telegram или переходите на сайт

🔍 **Советы по поиску:**
• Используйте конкретные термины: "трудовой договор", "отпуск", "больничный"
• Можно искать по фразам: "расчет зарплаты"
• Поиск работает по заголовкам и содержимому статей

📞 **Нужна помощь?**
Если возникли проблемы, попробуйте:
• Вернуться в главное меню
• Перезапустить бота командой /start
• Обратиться к администратору

🌐 **Источник:** kadrovik.uz
    """
    
    await callback.message.edit_text(
        help_text,
        reply_markup=get_back_to_main_menu(),
        parse_mode='Markdown'
    )

async def handle_about(callback: types.CallbackQuery):
    await callback.answer()
    about_text = """
🤖 **О боте KADROVIK.UZ**

📋 **Описание:**
Этот бот предоставляет быстрый доступ к актуальной информации для кадровых работников Узбекистана.

🎯 **Назначение:**
• Оперативное получение новостей кадрового законодательства
• Поиск нужной информации по кадровым вопросам
• Удобный доступ к материалам с сайта kadrovik.uz

⚡ **Возможности:**
• Просмотр последних статей и новостей
• Поиск по базе статей
• Навигация по тематическим рубрикам
• Получение полного текста статей

🌐 **Источник данных:** 
kadrovik.uz - ведущий ресурс для кадровиков Узбекистана

📅 **Версия:** 2.0
🛠️ **Статус:** Активная разработка

💬 **Обратная связь:**
Если у вас есть предложения по улучшению бота, напишите администратору.
    """
    
    await callback.message.edit_text(
        about_text,
        reply_markup=get_back_to_main_menu(),
        parse_mode='Markdown'
    )

async def handle_main_menu(callback: types.CallbackQuery):
    await callback.answer()
    user_id = str(callback.from_user.id)
    user = user_manager.get_user(user_id)
    
    welcome_text = f"👋 Добро пожаловать, {user['name'] if user else 'пользователь'}!\n\n"
    welcome_text += "🤖 **KADROVIK.UZ BOT**\n"
    welcome_text += "Ваш помощник в мире кадрового делопроизводства\n\n"
    welcome_text += "📋 Выберите нужную функцию:"
    
    await callback.message.edit_text(
        welcome_text,
        reply_markup=get_main_menu(),
        parse_mode='Markdown'
    )

async def handle_unknown_message(message: types.Message):
    await message.answer(
        "❓ Извините, я не понимаю эту команду.\n"
        "Используйте меню для навигации или команду /start для начала работы.",
        reply_markup=get_main_menu()
    )

def register_general_handlers(dp: Dispatcher):
    dp.callback_query.register(handle_help, lambda c: c.data == "help")
    dp.callback_query.register(handle_about, lambda c: c.data == "about")
    dp.callback_query.register(handle_main_menu, lambda c: c.data == "main_menu")
    dp.message.register(handle_unknown_message)