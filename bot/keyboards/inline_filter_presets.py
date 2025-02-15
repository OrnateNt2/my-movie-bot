from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
def preset_filter_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(InlineKeyboardButton("250 лучших фильмов", callback_data="set_preset:top250"),
           InlineKeyboardButton("500 лучших фильмов", callback_data="set_preset:top500"))
    kb.add(InlineKeyboardButton("Популярные", callback_data="set_preset:popular"),
           InlineKeyboardButton("Без фильтра", callback_data="set_preset:"))
    kb.add(InlineKeyboardButton("Настроить вручную", callback_data="set_preset:manual"))
    return kb
