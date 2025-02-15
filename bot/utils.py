import random, string
def generate_group_code(length=6):
    chars = string.ascii_uppercase + string.digits
    return "".join(random.choice(chars) for _ in range(length))
def format_movie_info(movie):
    title = movie.get("title", "Без названия")
    year = movie.get("year", "—")
    desc = movie.get("description", "—")
    rating = movie.get("rating_kp", "—")
    return f"<b>{title}</b> ({year})\nРейтинг KP: {rating}\n\n{desc}"
