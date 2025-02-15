from aiogram import types, Dispatcher

async def cmd_my_groups(message: types.Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    user_id = message.from_user.id
    from bot.database.models import get_all_groups_for_user
    groups = get_all_groups_for_user(user_id)
    if not groups:
        await message.answer("Вы не состоите ни в одной группе.")
        return
    text = "<b>Ваши группы:</b>\n"
    markup = InlineKeyboardMarkup(row_width=2)
    for code, name, active in groups:
        gname = name if name else "Без названия"
        mark = " (активная)" if active else ""
        text += f"• {gname}{mark} [код: {code}]\n"
        if active:
            btn_active = InlineKeyboardButton("Активная ✅", callback_data="no_action")
        else:
            btn_active = InlineKeyboardButton(f"Сделать активной: {gname}", callback_data=f"switch_group:{code}")
        btn_leave = InlineKeyboardButton(f"Покинуть: {gname}", callback_data=f"leave_group:{code}")
        markup.row(btn_active, btn_leave)
    await message.answer(text, reply_markup=markup)

def register_handlers_commands(dp: Dispatcher):
    pass
