# main.py
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import commands, inline

logging.basicConfig(level=logging.INFO)

def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN, parse_mode=types.ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)

    commands.register_handlers_commands(dp)
    inline.register_handlers_inline(dp)

    logging.info("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    main()
