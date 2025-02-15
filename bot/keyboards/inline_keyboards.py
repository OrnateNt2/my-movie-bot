from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def movie_rating_keyboard(movie_id):
    kb = InlineKeyboardMarkup(row_width=5)
    btns = []
    for r in range(1, 6):
        btns.append(InlineKeyboardButton(f"{r}⭐", callback_data=f"rate:{movie_id}:{r}"))
    kb.add(*btns)
    return kb
