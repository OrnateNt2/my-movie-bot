# bot/handlers/inline.py
from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery
from bot.keyboards.inline_keyboards import movie_rating_keyboard
from bot.services.kinopoisk_api import get_random_movie_by_genre
from bot.database.models import (
    save_movie_rating,
    get_common_movies_for_group,
    get_user_active_group,
    set_active_group,
    leave_group,
    get_group_name,
)
from bot.utils import format_movie_info

async def show_movie(message: types.Message, genre: str = "комедия"):
    """
    Если хотим вручную через /next_movie (обычный message-хендлер).
    """
    user_id = message.from_user.id
    await show_movie_by_user(message.bot, user_id, genre)


async def show_movie_by_user(bot, user_id: int, genre: str = "комедия"):
    """
    Вызываем после оценки, чтобы не привязываться к message.from_user.
    """
    group_code = get_user_active_group(user_id)
    if not group_code:
        # Если вдруг нет активной группы
        await bot.send_message(
            user_id,
            "У вас нет активной группы! Создайте новую /new_group или /join_group &lt;код&gt;, "
            "затем сделайте её активной через /my_groups."
        )
        return

    movie_data = get_random_movie_by_genre(genre)
    if not movie_data:
        await bot.send_message(user_id, "Не удалось найти фильм. Попробуйте другой жанр.")
        return

    text = format_movie_info(movie_data)
    # Отправляем новую карточку
    await bot.send_photo(
        chat_id=user_id,
        photo=movie_data.get("poster") or "",
        caption=text,
        reply_markup=movie_rating_keyboard(movie_data["id"])
    )

async def rate_movie(call: CallbackQuery):
    data = call.data.split(":")
    if len(data) < 3:
        await call.answer("Некорректные данные")
        return

    _, movie_id_str, rating_str = data
    user_id = call.from_user.id
    try:
        movie_id = int(movie_id_str)
        rating = int(rating_str)
    except ValueError:
        await call.answer("Неверный формат")
        return

    save_movie_rating(user_id, movie_id, rating)
    await call.answer(f"Оценка: {rating} ⭐")
    # Удаляем сообщение с предыдущим фильмом
    await call.message.delete()

    # Предлагаем следующий фильм (не через call.message, а через user_id)
    await show_movie_by_user(call.bot, user_id)


async def show_common_movies(message: types.Message):
    user_id = message.from_user.id
    group_code = get_user_active_group(user_id)
    if not group_code:
        await message.answer(
            "Нет активной группы! Создайте /new_group или /join_group &lt;код&gt;, "
            "потом /my_groups, чтобы сделать группу активной."
        )
        return

    movies = get_common_movies_for_group(group_code)
    if not movies:
        await message.answer("Нет фильмов, которые все оценили выше порога.")
        return

    text = "Фильмы, которые все хотят посмотреть:\n"
    for m in movies:
        title = m.get("title") or f"MovieID {m.get('id')}"
        year = m.get("year") or "—"
        text += f"• {title} ({year})\n"
    await message.answer(text)


async def switch_group(call: CallbackQuery):
    """
    callback_data = switch_group:<group_code>
    """
    data = call.data.split(":")
    if len(data) < 2:
        await call.answer("Некорректные данные для переключения группы")
        return

    group_code = data[1]
    user_id = call.from_user.id
    ok = set_active_group(user_id, group_code)
    if ok:
        await call.answer("Группа сделана активной")
        await call.message.edit_reply_markup()
        group_name = get_group_name(group_code) or group_code
        await call.message.answer(
            f"Текущая активная группа: <b>{group_name}</b>. Можете использовать /next_movie!"
        )
    else:
        await call.answer("Вы не состоите в этой группе.")


async def leave_group_cb(call: CallbackQuery):
    """
    callback_data = leave_group:<group_code>
    """
    data = call.data.split(":")
    if len(data) < 2:
        await call.answer("Некорректные данные")
        return

    group_code = data[1]
    user_id = call.from_user.id
    success, name = leave_group(user_id, group_code)
    if success:
        await call.answer("Вы покинули группу")
        await call.message.edit_reply_markup()
        gname = name or group_code
        await call.message.answer(
            f"Вы вышли из группы <b>{gname}</b>. Если это была активная группа, переключитесь на другую."
        )
    else:
        await call.answer("Не удалось покинуть группу (вы там не состоите).")

def register_handlers_inline(dp: Dispatcher):
    # Команды
    dp.register_message_handler(show_movie, commands=["next_movie"])
    dp.register_message_handler(show_common_movies, commands=["common_movies"])

    # Callback
    dp.register_callback_query_handler(rate_movie, lambda c: c.data.startswith("rate:"))
    dp.register_callback_query_handler(switch_group, lambda c: c.data.startswith("switch_group:"))
    dp.register_callback_query_handler(leave_group_cb, lambda c: c.data.startswith("leave_group:"))
