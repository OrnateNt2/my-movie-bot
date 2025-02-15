from aiogram import types,Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State,StatesGroup
from bot.database.models import(create_group_with_name,add_user_to_group,get_user_active_group,get_common_movies_for_group)
from bot.keyboards.reply_keyboards import main_menu
from bot.utils import generate_group_code
from bot.handlers.inline import show_movie_by_user
class GroupCreation(StatesGroup):
    waiting_for_name=State()
async def cmd_start(message:types.Message,state:FSMContext):
    await state.finish()
    text="Привет! Я бот для совместного выбора фильмов.\n\nНиже есть меню для основных действий."
    await message.answer(text,reply_markup=main_menu())
async def process_menu(message:types.Message,state:FSMContext):
    text=message.text
    if text=="Создать группу":
        await message.answer("Введите название вашей новой группы:")
        await GroupCreation.waiting_for_name.set()
    elif text=="Мои группы":
        from bot.handlers.commands import cmd_my_groups
        await cmd_my_groups(message)
    elif text=="Следующий фильм":
        user_id=message.from_user.id
        await show_movie_by_user(message.bot,user_id,"комедия")
    elif text=="Общие фильмы":
        group_code=get_user_active_group(message.from_user.id)
        if not group_code:
            await message.answer("У вас нет активной группы. Создайте/присоединитесь, затем сделайте её активной в «Мои группы».")
            return
        movies=get_common_movies_for_group(group_code)
        if not movies:
            await message.answer("Нет фильмов, которые все оценили выше порога.")
            return
        msg="Фильмы, которые все хотят посмотреть:\n"
        for m in movies:
            name=m.get("title")or f"MovieID {m.get('id')}"
            year=m.get("year","—")
            msg+=f"• {name} ({year})\n"
        await message.answer(msg)
    elif text=="Участники":
        from bot.handlers.participants import show_participants
        await show_participants(message)
    elif text=="Настроить фильтры":
        from bot.handlers.filters import cmd_setup_filters
        await cmd_setup_filters(message)
    else:
        await message.answer("Пожалуйста, используйте кнопки меню.",reply_markup=main_menu())
async def group_name_received(message:types.Message,state:FSMContext):
    user_id=message.from_user.id
    user_name=message.from_user.username or f"id{user_id}"
    group_name=message.text.strip()
    if not group_name:
        await message.answer("Название не может быть пустым!")
        return
    code=generate_group_code()
    create_group_with_name(code,user_id,group_name,user_name)
    await message.answer(f"Группа <b>{group_name}</b> создана!\nКод группы: <b>{code}</b>\nПриглашайте друзей, пусть введут этот код, чтобы присоединиться.\nТеперь группа активна. Нажмите «Следующий фильм»!")
    await state.finish()
def register_handlers_menu(dp:Dispatcher):
    dp.register_message_handler(cmd_start,commands="start",state="*")
    dp.register_message_handler(cmd_start,commands="help",state="*")
    dp.register_message_handler(group_name_received,state=GroupCreation.waiting_for_name)
    dp.register_message_handler(process_menu,state="*")
