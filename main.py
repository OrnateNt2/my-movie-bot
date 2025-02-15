import logging
import os
import asyncio
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.redis import RedisStorage2
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.types import ParseMode
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токенов и параметров из окружения
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Проверка наличия токена
if not TELEGRAM_BOT_TOKEN:
    logger.error("TELEGRAM_BOT_TOKEN не найден! Укажите его в .env")
    exit(1)

# Инициализация хранилища FSM в Redis
storage = RedisStorage2(host=REDIS_HOST, port=REDIS_PORT, db=5)

# Инициализация бота и диспетчера
bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(bot, storage=storage)

# Импорт хендлеров
from bot.handlers.menu import register_handlers_menu
from bot.handlers.commands import register_handlers_commands
from bot.handlers.inline import register_handlers_inline
from bot.handlers.filters import register_filters, register_filter_callbacks
from bot.handlers.participants import register_handlers_participants

async def on_startup(dp):
    """ Функция выполняется при запуске бота """
    logger.info("Бот запущен!")
    register_handlers_menu(dp)
    register_handlers_commands(dp)
    register_handlers_inline(dp)
    register_filters(dp)
    register_filter_callbacks(dp)
    register_handlers_participants(dp)

async def on_shutdown(dp):
    """ Функция выполняется при завершении работы бота """
    logger.warning("Бот завершает работу...")

if __name__ == "__main__":
    try:
        executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown, skip_updates=True)
    except Exception as e:
        logger.error(f"Ошибка запуска бота: {e}")
