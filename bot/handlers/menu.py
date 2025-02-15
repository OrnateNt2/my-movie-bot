from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from bot.database.models import create_group_with_name, get_user_active_group, get_common_movies_for_group
from bot.keyboards.reply_keyboards import main_menu
from bot.utils import generate_group_code
from bot.handlers.inline import show_movie_by_user
class GroupCreationFSM:
    waiting_for_name = "waiting_for_name"
async def cmd_start(message: types.Message, state: FSMContext):
    await state.finish()
    text = "Привет! Я бот для совместного выбора фильмов.\n\nНиже меню для основных действий."
    await message.answer(text, reply_markup=main_menu())
async def process_menu(message: types.Message, state: FSMContext):
    text = message.text
    if text == "Создать группу":
        await message.answer("Введите название вашей новой группы:")
        await state.set_state(GroupCreationFSM.waiting_for_name)
    elif text == "Мои группы":
        from bot.handlers.commands import cmd_my_groups
        await cmd_my_groups(message)
    elif text == "Следующий фильм":
        user_id = message.from_user.id
        await show_movie_by_user(message.bot, user_id)
    elif text == "Общие фильмы":
        from bot.database.models import get_common_movies_for_group
        group_code = get_user_active_group(message.from_user.id)
        if not group_code:
            await message.answer("Нет активной группы. Создайте или присоединитесь, затем через Мои группы сделайте её активной.")
            return
        movies = get_common_movies_for_group(group_code)
        if not movies:
            await message.answer("Нет фильмов, удовлетворяющих критериям.")
            return
        msg = "Фильмы, которые все хотят посмотреть:\n"
        for m in movies:
            name = m.get("title") or f"MovieID {m.get('id')}"
            year = m.get("year") or "—"
            msg += f"• {name} ({year})\n"
        await message.answer(msg)
    elif text == "Участники":
        from bot.handlers.participants import show_participants
        await show_participants(message)
    elif text == "Настроить фильтры":
        from bot.handlers.filters import cmd_setup_filters
        await cmd_setup_filters(message, state)
    else:
        await message.answer("Пожалуйста, используйте кнопки меню.", reply_markup=main_menu())
async def group_name_received(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_name = message.from_user.username or f"id{user_id}"
    group_name = message.text.strip()
    if not group_name:
        await message.answer("Название не может быть пустым!")
        return
    code = generate_group_code()
    create_group_with_name(code, user_id, group_name, user_name)
    await message.answer(f"Группа <b>{group_name}</b> создана!\nКод: <b>{code}</b>\nПриглашайте друзей.\nГруппа активна. Нажмите «Следующий фильм»!")
    await state.finish()
def register_handlers_menu(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "help"], state="*")
    dp.register_message_handler(group_name_received, state=GroupCreationFSM.waiting_for_name)
    dp.register_message_handler(process_menu, state="*")
