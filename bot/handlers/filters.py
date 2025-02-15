from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from bot.keyboards.inline_filter_presets import preset_filter_keyboard
from bot.database.models import get_user_active_group, get_group_creator_id, update_group_filters

class FilterSetup(StatesGroup):
    waiting_for_rating_min = State()
    waiting_for_rating_max = State()
    waiting_for_year_start = State()
    waiting_for_year_end = State()
    waiting_for_type = State()

async def cmd_setup_filters(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    group_code = get_user_active_group(user_id)
    if not group_code:
        await message.answer("Нет активной группы! Сделайте её активной через Мои группы.")
        return
    if get_group_creator_id(group_code) != user_id:
        await message.answer("Только создатель группы может менять фильтры.")
        return
    await message.answer("Выберите пресет фильтра или нажмите «Настроить вручную»:", reply_markup=preset_filter_keyboard())

async def preset_filter_cb(call: types.CallbackQuery, state: FSMContext):
    data = call.data.split(":", 1)
    if len(data) < 2:
        await call.answer("Некорректные данные.")
        return
    preset = data[1]  # Например, "top250", "top500", "popular", или "manual"
    user_id = call.from_user.id
    from bot.database.models import get_user_active_group
    group_code = get_user_active_group(user_id)
    if preset != "manual":
        if preset == "top250":
            update_group_filters(group_code, "movie", 7, 10, None, None)
        elif preset == "top500":
            update_group_filters(group_code, "movie", 7, 10, None, None)
        elif preset == "popular":
            update_group_filters(group_code, "", 5, 10, None, None)
        await call.answer("Фильтр обновлён!")
        await call.message.edit_text("Фильтр обновлён!")
    else:
        await call.message.edit_text("Введите минимальный рейтинг (например, 5):")
        await FilterSetup.waiting_for_rating_min.set()

async def filter_rating_min(message: types.Message, state: FSMContext):
    try:
        rating_min = int(message.text.strip())
    except:
        rating_min = 5
    await state.update_data(rating_min=rating_min)
    await message.answer("Введите максимальный рейтинг (например, 10):")
    await FilterSetup.waiting_for_rating_max.set()

async def filter_rating_max(message: types.Message, state: FSMContext):
    try:
        rating_max = int(message.text.strip())
    except:
        rating_max = 10
    await state.update_data(rating_max=rating_max)
    await message.answer("Введите год выпуска от (или 0 для пропуска):")
    await FilterSetup.waiting_for_year_start.set()

async def filter_year_start(message: types.Message, state: FSMContext):
    try:
        year_start = int(message.text.strip())
    except:
        year_start = 0
    await state.update_data(year_start=year_start)
    await message.answer("Введите год выпуска до (или 0 для пропуска):")
    await FilterSetup.waiting_for_year_end.set()

async def filter_year_end(message: types.Message, state: FSMContext):
    try:
        year_end = int(message.text.strip())
    except:
        year_end = 0
    await state.update_data(year_end=year_end)
    await message.answer("Введите тип контента: movie (фильм), tv-series (сериал), cartoon (мультфильм) или оставьте пустым:")
    await FilterSetup.waiting_for_type.set()

async def filter_type(message: types.Message, state: FSMContext):
    content_type = message.text.strip()
    data = await state.get_data()
    rating_min = data.get("rating_min", 5)
    rating_max = data.get("rating_max", 10)
    year_start = data.get("year_start", None)
    year_end = data.get("year_end", None)
    user_id = message.from_user.id
    from bot.database.models import get_user_active_group, update_group_filters
    group_code = get_user_active_group(user_id)
    update_group_filters(group_code, content_type, rating_min, rating_max, year_start if year_start != 0 else None, year_end if year_end != 0 else None)
    await message.answer("Фильтры обновлены!")
    await state.finish()

def register_filters(dp: Dispatcher):
    dp.register_message_handler(cmd_setup_filters, lambda msg: msg.text=="Настроить фильтры", state="*")
    dp.register_message_handler(filter_rating_min, state=FilterSetup.waiting_for_rating_min)
    dp.register_message_handler(filter_rating_max, state=FilterSetup.waiting_for_rating_max)
    dp.register_message_handler(filter_year_start, state=FilterSetup.waiting_for_year_start)
    dp.register_message_handler(filter_year_end, state=FilterSetup.waiting_for_year_end)
    dp.register_message_handler(filter_type, state=FilterSetup.waiting_for_type)

def register_filter_callbacks(dp: Dispatcher):
    dp.register_callback_query_handler(preset_filter_cb, lambda c: c.data.startswith("set_preset:"))
