import logging
from aiogram import Bot,Dispatcher,executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from config import TELEGRAM_BOT_TOKEN
from bot.handlers.menu import register_handlers_menu
from bot.handlers.commands import register_handlers_commands
from bot.handlers.inline import register_handlers_inline
from bot.handlers.participants import register_handlers_participants
logging.basicConfig(level=logging.INFO)
def main():
    bot=Bot(token=TELEGRAM_BOT_TOKEN,parse_mode="HTML")
    storage=MemoryStorage()
    dp=Dispatcher(bot,storage=storage)
    register_handlers_menu(dp)
    register_handlers_commands(dp)
    register_handlers_inline(dp)
    register_handlers_participants(dp)
    logging.info("Бот запущен...")
    executor.start_polling(dp,skip_updates=True)
if __name__=="__main__":
    main()
