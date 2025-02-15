# bot/handlers/inline.py
from aiogram import types, Dispatcher
from aiogram.types import CallbackQuery
from bot.keyboards.inline_keyboards import movie_rating_keyboard
from bot.services.kinopoisk_api import get_random_movie_by_genre
from bot.database.models import save_movie_rating, get_common_movies_for_group
from bot.utils import format_movie_info

# Показ фильма (по умолчанию берем жанр "comedy" или любой другой)
async def show_movie(message: types.Message, genre: str = "комедия"):
    """
    Показываем один случайный фильм по указанному жанру.
    """
    user_id = message.from_user.id
    movie_data = get_random_movie_by_genre(genre)

    if movie_data is None:
        await message.answer("Не удалось найти фильм по выбранному жанру. Попробуйте другой жанр.")
        return

    text = format_movie_info(movie_data)
    # Отправляем сообщение с inline-кнопками рейтинга
    await message.answer_photo(
        photo=movie_data.get("poster", ""),
        caption=text,
        reply_markup=movie_rating_keyboard(movie_data["id"])
    )

# Обработка нажатия на рейтинг (1..5)
async def rate_movie(call: CallbackQuery):
    # Пример callback_data: "rate:12345:5"
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
        await call.answer("Неверный формат рейтинга")
        return

    save_movie_rating(user_id, movie_id, rating)
    await call.answer(f"Оценка: {rating} ⭐")
    # Удалим сообщение, чтобы "прятать" предыдущую карточку
    await call.message.delete()

    # Можно показать следующий фильм
    await show_movie(call.message)

# Показ общих фильмов, которые все оценили >= порога
async def show_common_movies(message: types.Message):
    user_id = message.from_user.id
    from bot.database.models import get_user_group
    group_code = get_user_group(user_id)

    if not group_code:
        await message.answer("Вы ещё не в группе. Создайте её /new_group или /join_group.")
        return

    common_movies = get_common_movies_for_group(group_code)
    if not common_movies:
        await message.answer("Пока нет фильмов, которые все оценили выше заданного порога.")
        return

    text = "Фильмы, которые все хотят посмотреть:\n"
    for movie in common_movies:
        t = movie.get('title') or f"MovieID {movie.get('id')}"
        y = movie.get('year') or "—"
        text += f"• {t} ({y})\n"
    await message.answer(text)

def register_handlers_inline(dp: Dispatcher):
    dp.register_message_handler(show_movie, commands=["next_movie"])
    dp.register_message_handler(show_common_movies, commands=["common_movies"])

    dp.register_callback_query_handler(rate_movie, lambda c: c.data.startswith("rate:"))
