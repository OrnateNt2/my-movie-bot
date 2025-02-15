# bot/keyboards/inline_keyboards.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def movie_rating_keyboard(movie_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=5)
    buttons = []
    for rating in range(1, 6):
        btn = InlineKeyboardButton(
            text=f"{rating}⭐",
            callback_data=f"rate:{movie_id}:{rating}"
        )
        buttons.append(btn)
    markup.add(*buttons)
    return markup
