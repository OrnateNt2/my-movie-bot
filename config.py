# config.py
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
KINOPOISK_API_KEY = os.getenv("KINOPOISK_API_KEY")

# База данных (SQLite)
DATABASE_PATH = "movie_bot.sqlite3"

# Например, оценка от которой считаем, что фильм нравится всем (4 или 5)
MIN_RATING_THRESHOLD = 4
