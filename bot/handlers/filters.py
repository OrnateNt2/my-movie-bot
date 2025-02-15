from aiogram import types,Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State,StatesGroup
from bot.database.models import get_user_active_group,get_group_creator_id,update_group_filters

class FilterSetup(StatesGroup):
    waiting_for_genres=State()
    waiting_for_year_start=State()
    waiting_for_year_end=State()
    waiting_for_type=State()

async def cmd_setup_filters(message:types.Message):
    user_id=message.from_user.id
    group_code=get_user_active_group(user_id)
    if not group_code:
        await message.answer("Нет активной группы! Сначала сделайте группу активной в «Мои группы».")
        return
    # Проверяем, что user_id является создателем
    if get_group_creator_id(group_code)!=user_id:
        await message.answer("Только создатель группы может менять настройки.")
        return
    await message.answer("Введите жанры (через запятую). Пример: комедия,драма")
    await FilterSetup.waiting_for_genres.set()

async def filters_genres(message:types.Message,state:FSMContext):
    genres=message.text.strip()
    await state.update_data(genres=genres)
    await message.answer("Введите начальный год (например, 2000). Укажите 0, чтобы пропустить.")
    await FilterSetup.waiting_for_year_start.set()

async def filters_year_start(message:types.Message,state:FSMContext):
    try:
        val=int(message.text.strip())
    except:
        val=0
    await state.update_data(year_start=val)
    await message.answer("Введите конечный год (например, 2023). Укажите 0, чтобы пропустить.")
    await FilterSetup.waiting_for_year_end.set()

async def filters_year_end(message:types.Message,state:FSMContext):
    try:
        val=int(message.text.strip())
    except:
        val=0
    await state.update_data(year_end=val)
    await message.answer("Укажите тип: movie (фильм), tv-series (сериал), cartoon (мультфильм). Или оставьте пустым.")
    await FilterSetup.waiting_for_type.set()

async def filters_type(message:types.Message,state:FSMContext):
    ctype=message.text.strip()
    data=await state.get_data()
    genres=data["genres"]
    ystart=data["year_start"]
    yend=data["year_end"]
    user_id=message.from_user.id
    group_code=get_user_active_group(user_id)
    if not group_code:
        await message.answer("Активная группа не найдена, настройка прервана.")
        await state.finish()
        return
    # Сохраняем
    update_group_filters(
        group_code,
        genres if genres else None,
        ystart if ystart>0 else None,
        yend if yend>0 else None,
        ctype if ctype else None
    )
    await message.answer("Фильтры обновлены! Теперь «Следующий фильм» будет учитывать эти настройки.")
    await state.finish()

def register_filters(dp:Dispatcher):
    dp.register_message_handler(cmd_setup_filters,lambda msg:msg.text=="Настроить фильтры",state="*")
    dp.register_message_handler(filters_genres,state=FilterSetup.waiting_for_genres)
    dp.register_message_handler(filters_year_start,state=FilterSetup.waiting_for_year_start)
    dp.register_message_handler(filters_year_end,state=FilterSetup.waiting_for_year_end)
    dp.register_message_handler(filters_type,state=FilterSetup.waiting_for_type)
