# bot/utils.py
import random
import string

def generate_group_code(length=6):
    """Генерирует случайный код для группы."""
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def format_movie_info(movie_data: dict) -> str:
    """Формируем текст для отображения информации о фильме."""
    title = movie_data.get("title", "Без названия")
    year = movie_data.get("year", "—")
    desc = movie_data.get("description", "—")
    rating_kp = movie_data.get("rating_kp", "—")
    genres_list = movie_data.get("genres", [])
    genres = ", ".join(genres_list) if genres_list else "—"

    text = (
        f"<b>{title}</b> ({year})\n"
        f"Рейтинг KP: {rating_kp}\n"
        f"Жанры: {genres}\n\n"
        f"{desc}"
    )
    return text
