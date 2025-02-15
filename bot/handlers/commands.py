# bot/handlers/commands.py
from aiogram import types, Dispatcher
from bot.utils import generate_group_code
from bot.database.models import create_group_if_not_exists, add_user_to_group
from bot.handlers.inline import show_movie

async def cmd_start(message: types.Message):
    """
    /start — начало работы бота, краткая справка по доступным командам.
    """
    commands_text = (
        "Привет! Я бот для совместного выбора фильмов.\n\n"
        "<b>Доступные команды:</b>\n"
        "/start — показать это сообщение\n"
        "/new_group — создать новую группу и автоматически в неё войти\n"
        "/join_group &lt;код&gt; — присоединиться к группе\n"
        "/next_movie — предложить фильм для оценки\n"
        "/common_movies — показать фильмы, которые все участники группы хотят посмотреть\n"
    )
    await message.answer(commands_text)

async def cmd_new_group(message: types.Message):
    """
    Создаёт новую группу, привязывает к user_id, генерирует код.
    """
    user_id = message.from_user.id
    new_code = generate_group_code()
    # Создаём группу и автоматически добавляем создателя
    create_group_if_not_exists(new_code, user_id)

    await message.answer(
        f"Новая группа создана! Код группы: <b>{new_code}</b>\n"
        "Отправьте этот код друзьям, чтобы они присоединились. "
        "Можете начать выбирать фильмы командой /next_movie."
    )

async def cmd_join_group(message: types.Message):
    """
    /join_group <код> — пользователь присоединяется к существующей группе,
    затем сразу предлагаем фильм.
    """
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Вы не указали код группы. Используйте /join_group &lt;код&gt;")
        return

    group_code = parts[1]
    success = add_user_to_group(group_code, user_id)
    if success:
        await message.answer(f"Вы успешно присоединились к группе с кодом {group_code}!")
        # Предложить фильм сразу
        await show_movie(message)
    else:
        await message.answer("Группа с таким кодом не найдена.")

def register_handlers_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "help"])
    dp.register_message_handler(cmd_new_group, commands=["new_group"])
    dp.register_message_handler(cmd_join_group, commands=["join_group"])
