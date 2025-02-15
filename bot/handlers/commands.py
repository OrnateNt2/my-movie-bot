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
        "<b>Доступные команды:</b>\n"
        "/start — показать это сообщение\n"
        "/new_group — создать новую группу (запросит название)\n"
        "/join_group &lt;код&gt; — присоединиться к группе\n"
        "/next_movie — предложить фильм для оценки в активной группе\n"
        "/common_movies — показать общие фильмы для активной группы\n"
        "/my_groups — показать все группы, в которых вы состоите\n"
    )
    await message.answer(commands_text)

async def cmd_new_group(message: types.Message, state: FSMContext):
    """
    Начинаем процесс создания группы. Просим название.
    """
    await message.answer("Введите название вашей новой группы (например «Киноклуб Соседей»):")
    await GroupCreation.waiting_for_group_name.set()

async def group_name_received(message: types.Message, state: FSMContext):
    """
    Создаём группу, генерируем код, делаем её активной.
    """
    user_id = message.from_user.id
    group_name = message.text.strip()
    if not group_name:
        await message.answer("Название группы не может быть пустым. Попробуйте снова.")
        return

    code = generate_group_code()
    create_group_with_name(code, user_id, group_name)

    await message.answer(
        f"Группа <b>{group_name}</b> создана!\n"
        f"Код группы: <b>{code}</b>\n"
        "Отправьте этот код друзьям, чтобы они присоединились.\n"
        "Эта группа теперь активна для вас. Можете вызвать /next_movie!"
    )

    await state.finish()

async def cmd_join_group(message: types.Message):
    """
    /join_group &lt;код&gt; — присоединиться к группе.
    """
    user_id = message.from_user.id
    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.answer("Не указан код группы. Пример: /join_group &lt;код&gt;")
        return

    group_code = parts[1]
    success = add_user_to_group(group_code, user_id)
    if success:
        await message.answer(
            f"Вы присоединились к группе с кодом <b>{group_code}</b>!\n"
            "Чтобы сделать её активной, используйте /my_groups."
        )
    else:
        await message.answer("Группа с таким кодом не найдена.")

async def cmd_my_groups(message: types.Message):
    """
    Показываем список групп пользователя, добавляем кнопки:
      - «Сделать активной»
      - «Покинуть группу»
    """
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from bot.database.models import get_all_groups_for_user

    user_id = message.from_user.id
    groups = get_all_groups_for_user(user_id)
    if not groups:
        await message.answer("Вы не состоите ни в одной группе. Создайте /new_group или /join_group &lt;код&gt;.")
        return

    text = "Ваши группы:\n"
    markup = InlineKeyboardMarkup(row_width=2)

    # groups — список кортежей (code, group_name, is_active)
    for code, name, active in groups:
        group_name = name if name else "Без названия"
        mark = " (активная)" if active else ""
        text += f"• {group_name} [код: {code}]{mark}\n"

        # Две кнопки в ряду: [Сделать активной / Активная], [Покинуть]
        btns = []
        if active:
            # Уже активна — делаем "Активная" (без callback)
            btns.append(InlineKeyboardButton(
                text="Активная ✅",
                callback_data="no_action"  # заглушка, можно игнорировать
            ))
        else:
            # Кнопка "Сделать активной"
            btns.append(InlineKeyboardButton(
                text="Сделать активной",
                callback_data=f"switch_group:{code}"
            ))
        # Кнопка "Покинуть группу"
        btns.append(InlineKeyboardButton(
            text="Покинуть",
            callback_data=f"leave_group:{code}"
        ))

        markup.row(*btns)

    await message.answer(text, reply_markup=markup)

def register_handlers_commands(dp: Dispatcher):
    dp.register_message_handler(cmd_start, commands=["start", "help"], state="*")
    dp.register_message_handler(cmd_new_group, commands=["new_group"], state="*")
    dp.register_message_handler(group_name_received, state=GroupCreation.waiting_for_group_name)
    dp.register_message_handler(cmd_join_group, commands=["join_group"], state="*")
    dp.register_message_handler(cmd_my_groups, commands=["my_groups"], state="*")
