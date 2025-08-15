from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types

def get_main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(
        types.InlineKeyboardButton(text="📚 Все темы 34", callback_data="kadrovik_latest")
    )
    builder.row(
        types.InlineKeyboardButton(text="📚 Рубрики", callback_data="kadrovik_news"),
        types.InlineKeyboardButton(text="🔍 Поиск", callback_data="kadrovik_search")
    )
    builder.row(
        types.InlineKeyboardButton(text="🗞️ Новости", callback_data="news"),
        types.InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")
    )
    builder.row(
        types.InlineKeyboardButton(text="🤖 О боте", callback_data="about")
    )
    return builder.as_markup()

def get_back_to_main_menu():
    builder = InlineKeyboardBuilder()
    builder.add(types.InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()