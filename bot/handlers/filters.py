from aiogram import types, Dispatcher
from bot.keyboards.inline_filters import filter_type_keyboard
from bot.database.models import get_user_active_group, get_group_creator_id, update_group_filters

async def cmd_setup_filters(message: types.Message):
    user_id = message.from_user.id
    group_code = get_user_active_group(user_id)
    if not group_code:
        await message.answer("Нет активной группы! Сделайте активной через Мои группы.")
        return
    if get_group_creator_id(group_code) != user_id:
        await message.answer("Только создатель группы может менять фильтры.")
        return
    await message.answer("Выберите тип контента для фильтра:", reply_markup=filter_type_keyboard())

async def set_filter_cb(call: types.CallbackQuery):
    data = call.data.split(":", 1)
    if len(data) < 2:
        await call.answer("Ошибка данных.")
        return
    content_type = data[1]  # Может быть пустым для "Без фильтра"
    user_id = call.from_user.id
    from bot.database.models import get_user_active_group
    group_code = get_user_active_group(user_id)
    if not group_code:
        await call.answer("Нет активной группы.")
        return
    update_group_filters(group_code, content_type)
    await call.answer("Фильтр обновлён!")
    await call.message.edit_text("Фильтр обновлён!")
    
def register_filters(dp: Dispatcher):
    dp.register_message_handler(cmd_setup_filters, lambda msg: msg.text == "Настроить фильтры", state="*")

def register_filter_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(set_filter_cb, lambda c: c.data.startswith("set_filter:"))
