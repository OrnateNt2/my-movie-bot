import random, string
def generate_group_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))
def format_movie_info(movie):
    title = movie.get("title", "Без названия")
    year = movie.get("year", "—")
    desc = movie.get("description", "—")
    rating = movie.get("rating_kp", "—")
    movie_id = movie.get("id")
    link = f"https://www.kinopoisk.ru/film/{movie_id}" if movie_id else ""
    return f"<b>{title}</b> ({year})\nРейтинг KP: {rating}\n{desc}\n<a href='{link}'>Ссылка на Кинопоиск</a>"
