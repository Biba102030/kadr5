import asyncio
import logging
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config import bot, BOT_TOKEN
from handlers.registration import register_registration_handlers
from handlers.news import register_news_handlers
from handlers.search import register_search_handlers
from handlers.rubrics import register_rubrics_handlers
from handlers.general import register_general_handlers
from handlers.articles import register_articles_handlers  # Добавлен импорт

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация диспетчера
dp = Dispatcher(storage=MemoryStorage())

async def main():
    logger.info("Запуск бота...")
    try:
        # Регистрация обработчиков
        register_registration_handlers(dp)
        register_news_handlers(dp)
        register_search_handlers(dp)
        register_rubrics_handlers(dp)
        register_general_handlers(dp)
        register_articles_handlers(dp)  # Добавлена регистрация

        # Удаляем webhook, если был установлен
        await bot.delete_webhook(drop_pending_updates=True)
        
        # Запускаем polling
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")