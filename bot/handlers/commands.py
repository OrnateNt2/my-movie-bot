# bot/handlers/commands.py
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from bot.utils import generate_group_code
from bot.database.models import (
    create_group_with_name,
    add_user_to_group,
    get_all_groups_for_user,
)
from bot.handlers.inline import show_movie

class GroupCreation(StatesGroup):
    waiting_for_group_name = State()

async def cmd_start(message: types.Message):
    commands_text = (
        "Привет! Я бот для совместного выбора фильмов.\n\n"
        "<b>Команды:</b>\n"
        "/start — показать это сообщение\n"
        "/new_group — создать новую группу (запросит название)\n"
        "/join_group &lt;код&gt; — присоединиться к группе\n"
        "/my_groups — вывести список ваших групп (с кнопками)\n"
        "/next_movie — предложить фильм (использует активную группу)\n"
        "/common_movies — показать общие фильмы (для активной группы)\n"
    )
    await message.answer(commands_text)


async def cmd_new_group(message: types.Message, state: FSMContext):
    """
    Запрашиваем название новой группы (FSM).
    """
    await message.answer("Введите название вашей новой группы:")
    await GroupCreation.waiting_for_group_name.set()

async def group_name_received(message: types.Message, state: FSMContext):
    """
    Пользователь присылает название -> создаём группу, делаем её активной.
    """
    user_id = message.from_user.id
    group_name = message.text.strip()
    if not group_name:
        await message.answer("Название группы не может быть пустым. Попробуйте ещё раз.")
        return

    code = generate_group_code()
    create_group_with_name(code, user_id, group_name)

    await message.answer(
        f"Группа <b>{group_name}</b> создана!\n"
        f"Код группы: <b>{code}</b>\n"
        "Отправьте его друзьям, чтобы они присоединились.\n"
        "Теперь эта группа активна для вас. Используйте /next_movie."
    )
    await state.finish()

async def cmd_join_group(message: types.Message):
    """
    /join_group &lt;код&gt; — присоединиться к группе по коду (is_active=0).
    """
    user_id = message.from_user.id
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Нужно указать код группы: /join_group &lt;код&gt;")
        return

    group_code = parts[1]
    success = add_user_to_group(group_code, user_id)
    if success:
        await message.answer(
            f"Вы присоединились к группе с кодом <b>{group_code}</b>.\n"
            "Посмотреть все группы и переключиться на нужную: /my_groups"
        )
    else:
        await message.answer("Группа с таким кодом не найдена.")

async def cmd_my_groups(message: types.Message):
    """
    Показываем список групп пользователя, добавляя inline-кнопки для:
    - Сделать активной: <название>
    - Покинуть: <название>
    """
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    user_id = message.from_user.id
    groups = get_all_groups_for_user(user_id)
    if not groups:
        await message.answer("Вы не состоите ни в одной группе. /new_group или /join_group &lt;код&gt;.")
        return

    text = "<b>Ваши группы:</b>\n"
    markup = InlineKeyboardMarkup(row_width=2)
    for code, gname, active in groups:
        name = gname if gname else "Без названия"
        active_mark = " (активная)" if active else ""
        text += f"• {name}{active_mark} [код: {code}]\n"

        # Две кнопки:
        # 1) Активная / Сделать активной: <название>
        if active:
            btn_active = InlineKeyboardButton(
                text=f"Активная ✅",
                callback_data="no_action"
            )
        else:
            btn_active = InlineKeyboardButton(
                text=f"Сделать активной: {name}",
                callback_data=f"switch_group:{code}"
            )
        # 2) Покинуть группу
        btn_leave = InlineKeyboardButton(
            text=f"Покинуть: {name}",
            callback_data=f"leave_group:{code}"
        )
        markup.row(btn_active, btn_leave)

    await message.answer(text, reply_markup=markup)

def register_handlers_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "help"], state="*")
    dp.register_message_handler(cmd_new_group, commands=["new_group"], state="*")
    dp.register_message_handler(group_name_received, state=GroupCreation.waiting_for_group_name)
    dp.register_message_handler(cmd_join_group, commands=["join_group"], state="*")
    dp.register_message_handler(cmd_my_groups, commands=["my_groups"], state="*")
