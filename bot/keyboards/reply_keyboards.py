from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton("Создать группу"), KeyboardButton("Мои группы"))
    kb.add(KeyboardButton("Следующий фильм"), KeyboardButton("Общие фильмы"))
    kb.add(KeyboardButton("Участники"), KeyboardButton("Настроить фильтры"))
    return kb
