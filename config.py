import os
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")
DATABASE_PATH = os.getenv("DATABASE_PATH", "movie_bot.sqlite3")
MIN_RATING_THRESHOLD = int(os.getenv("MIN_RATING_THRESHOLD", "4"))

# Redis настройки
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
