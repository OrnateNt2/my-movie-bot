from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def filter_type_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("Фильмы", callback_data="set_filter:movie"),
        InlineKeyboardButton("Сериалы", callback_data="set_filter:tv-series")
    )
    kb.add(
        InlineKeyboardButton("Мультфильмы", callback_data="set_filter:cartoon"),
        InlineKeyboardButton("Без фильтра", callback_data="set_filter:")
    )
    return kb
