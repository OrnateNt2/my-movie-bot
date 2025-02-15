from aiogram import types,Dispatcher
from aiogram.types import CallbackQuery
from bot.keyboards.inline_keyboards import movie_rating_keyboard
from bot.services.kinopoisk_api import get_random_movie_by_filters,get_movie_info_by_id
from bot.database.models import save_movie_rating,get_user_active_group,get_group_filters,set_active_group,leave_group
from bot.utils import format_movie_info

async def show_movie_by_user(bot,user_id):
    group_code=get_user_active_group(user_id)
    if not group_code:
        await bot.send_message(user_id,"Нет активной группы.")
        return
    # Считываем фильтры
    (f_genres,f_start,f_end,f_type)=get_group_filters(group_code)
    movie_data=get_random_movie_by_filters(
        genres=f_genres,
        year_start=f_start,
        year_end=f_end,
        content_type=f_type
    )
    if not movie_data:
        await bot.send_message(user_id,"Не найдены фильмы по заданным фильтрам.")
        return
    text=format_movie_info({
        "title":movie_data.get("name","Без названия"),
        "year":movie_data.get("year"),
        "description":movie_data.get("description",""),
        "rating_kp":(movie_data.get("rating")or{}).get("kp","—"),
        "poster":(movie_data.get("poster")or{}).get("url","")
    })
    poster=(movie_data.get("poster")or{}).get("url","")
    await bot.send_photo(user_id,photo=poster,caption=text,reply_markup=movie_rating_keyboard(movie_data["id"]))

async def rate_movie(call:CallbackQuery):
    data=call.data.split(":")
    if len(data)<3:
        await call.answer("Некорректные данные.")
        return
    _,movie_id_str,rating_str=data
    user_id=call.from_user.id
    try:
        movie_id=int(movie_id_str)
        rating=int(rating_str)
    except:
        await call.answer("Ошибка формата.")
        return
    save_movie_rating(user_id,movie_id,rating)
    await call.answer(f"Оценка: {rating}")
    await call.message.delete()
    await show_movie_by_user(call.bot,user_id)

async def switch_group_cb(call:CallbackQuery):
    data=call.data.split(":")
    if len(data)<2:
        await call.answer("Некорректные данные.")
        return
    group_code=data[1]
    user_id=call.from_user.id
    ok=set_active_group(user_id,group_code)
    if ok:
        await call.answer("Группа сделана активной.")
        await call.message.edit_reply_markup()
        await call.message.answer(f"Текущая активная группа: {group_code}.")
    else:
        await call.answer("Вы не состоите в этой группе.")

async def leave_group_cb(call:CallbackQuery):
    data=call.data.split(":")
    if len(data)<2:
        await call.answer("Некорректно.")
        return
    code=data[1]
    user_id=call.from_user.id
    ok=leave_group(user_id,code)
    if ok:
        await call.answer("Вы покинули группу.")
        await call.message.edit_reply_markup()
        await call.message.answer(f"Вышли из группы: {code}.")
    else:
        await call.answer("Ошибка или вы не в группе.")

def register_handlers_inline(dp:Dispatcher):
    dp.register_callback_query_handler(rate_movie,lambda c:c.data.startswith("rate:"))
    dp.register_callback_query_handler(switch_group_cb,lambda c:c.data.startswith("switch_group:"))
    dp.register_callback_query_handler(leave_group_cb,lambda c:c.data.startswith("leave_group:"))
