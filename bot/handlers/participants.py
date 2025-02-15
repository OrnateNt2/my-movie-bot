from aiogram import types,Dispatcher
from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,CallbackQuery
from bot.database.models import(get_user_active_group,get_group_creator_id,get_group_users,leave_group)
async def show_participants(message:types.Message):
    user_id=message.from_user.id
    group_code=get_user_active_group(user_id)
    if not group_code:
        await message.answer("Нет активной группы.")
        return
    creator_id=get_group_creator_id(group_code)
    is_creator=(creator_id==user_id)
    users=get_group_users(group_code)
    if not users:
        await message.answer("Нет участников?")
        return
    text="Участники:\n"
    kb=InlineKeyboardMarkup()
    for(uid,uname,active)in users:
        name_display=uname or f"id{uid}"
        mark=" (Вы)"if uid==user_id else""
        amark=" *"if active else""
        text+=f"• {name_display}{mark}{amark}\n"
        if is_creator and uid!=user_id:
            btn=InlineKeyboardButton(f"Исключить {name_display}",callback_data=f"remove_user:{uid}")
            kb.add(btn)
    note="\n(* пометка если у пользователя эта группа тоже активна)\nТолько создатель может исключать участников."
    await message.answer(text+note,reply_markup=kb)
async def remove_user_cb(call:CallbackQuery):
    data=call.data.split(":")
    if len(data)<2:
        await call.answer("Нет данных")
        return
    target_user_id=int(data[1])
    admin_id=call.from_user.id
    group_code=get_user_active_group(admin_id)
    if not group_code:
        await call.answer("Нет активной группы.")
        return
    if get_group_creator_id(group_code)!=admin_id:
        await call.answer("Вы не создатель.")
        return
    ok=leave_group(target_user_id,group_code)
    if ok:
        await call.answer("Участник исключён!")
        await call.message.edit_reply_markup()
        await call.message.answer("Список обновлён.")
    else:
        await call.answer("Не удалось исключить.")
def register_handlers_participants(dp:Dispatcher):
    dp.register_callback_query_handler(remove_user_cb,lambda c:c.data.startswith("remove_user:"))
