from dotenv import load_dotenv
import os
from aiogram import Bot
from kadrovik_parser import KadrovikNewsParser

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Проверка токена
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not found in .env file")

# Инициализация бота
bot = Bot(token=BOT_TOKEN)

# Константы
MAX_ARTICLES = 10
MAX_MESSAGE_LENGTH = 4000

# Временная заглушка для рубрик
RUBRIKI = {
    "Трудовое право": "trudovoe-pravo",
    "Налоги и взносы": "nalogi-vznosy",
    "Кадровое делопроизводство": "kadrovoe-deloproizvodstvo",
    "Отпуска": "otpuska",
    "Больничные": "bolnichnye",
    "Зарплата": "zarplata",
    "Охрана труда": "ohrana-truda",
    "Практические вопросы": "prakticheskie-voprosy"
}

# Глобальные переменные
user_data = {}
news_parser = KadrovikNewsParser()