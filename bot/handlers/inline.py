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
    leave_group
)
from bot.utils import format_movie_info

async def show_movie(message: types.Message, genre: str = "комедия"):
    user_id = message.from_user.id
    group_code = get_user_active_group(user_id)
    if not group_code:
        await message.answer(
            "У вас нет активной группы! Создайте /new_group или /join_group &lt;код&gt;, "
            "затем сделайте её активной через /my_groups."
        )
        return

    movie_data = get_random_movie_by_genre(genre)
    if movie_data is None:
        await message.answer("Не удалось найти фильм по заданным критериям. Попробуйте другой жанр.")
        return

    text = format_movie_info(movie_data)
    await message.answer_photo(
        photo=movie_data.get("poster", ""),
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
    await call.message.delete()
    # Показываем следующий
    await show_movie(call.message)

async def show_common_movies(message: types.Message):
    user_id = message.from_user.id
    group_code = get_user_active_group(user_id)
    if not group_code:
        await message.answer(
            "У вас нет активной группы! Создайте /new_group или /join_group &lt;код&gt;, "
            "затем сделайте её активной через /my_groups."
        )
        return

    common_movies = get_common_movies_for_group(group_code)
    if not common_movies:
        await message.answer("Пока нет фильмов, которые все оценили выше порога.")
        return

    text = "Фильмы, которые все хотят посмотреть:\n"
    for m in common_movies:
        title = m.get("title") or f"MovieID {m.get('id')}"
        year = m.get("year") or "—"
        text += f"• {title} ({year})\n"
    await message.answer(text)

# ===== Новые CALLBACKS =====

async def switch_group(call: CallbackQuery):
    # switch_group:<код>
    data = call.data.split(":")
    if len(data) < 2:
        await call.answer("Некорректные данные для переключения.")
        return
    group_code = data[1]
    user_id = call.from_user.id

    success = set_active_group(user_id, group_code)
    if success:
        await call.answer("Группа сделана активной.")
        # Можно отредактировать сообщение, убрав кнопки
        await call.message.edit_reply_markup()
        await call.message.answer(
            f"Текущая активная группа: {group_code}. Теперь /next_movie будет работать в её рамках."
        )
    else:
        await call.answer("Вы не состоите в этой группе.")

async def leave_group_cb(call: CallbackQuery):
    # leave_group:<код>
    data = call.data.split(":")
    if len(data) < 2:
        await call.answer("Некорректные данные для выхода из группы.")
        return
    group_code = data[1]
    user_id = call.from_user.id

    from bot.database.models import leave_group
    ok = leave_group(user_id, group_code)
    if ok:
        await call.answer("Вы покинули группу.")
        await call.message.edit_reply_markup()
        await call.message.answer(
            f"Вы вышли из группы {group_code}. Если это была активная, активная группа теперь не выбрана."
        )
    else:
        await call.answer("Не удалось выйти: вы не состоите в этой группе.")

def register_handlers_inline(dp: Dispatcher):
    dp.register_message_handler(show_movie, commands=["next_movie"])
    dp.register_message_handler(show_common_movies, commands=["common_movies"])

    dp.register_callback_query_handler(rate_movie, lambda c: c.data.startswith("rate:"))
    dp.register_callback_query_handler(switch_group, lambda c: c.data.startswith("switch_group:"))
    dp.register_callback_query_handler(leave_group_cb, lambda c: c.data.startswith("leave_group:"))
