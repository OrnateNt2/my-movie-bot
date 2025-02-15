# bot/database/models.py
import sqlite3
import os
from config import DATABASE_PATH, MIN_RATING_THRESHOLD

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            creator_id INTEGER
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_code TEXT NOT NULL,
            user_id INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_code TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            movie_id INTEGER NOT NULL,
            rating INTEGER NOT NULL
        )
    """)
    return conn

def create_group_if_not_exists(group_code: str, creator_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM groups WHERE code = ?", (group_code,))
    row = cursor.fetchone()
    if not row:
        # Создаём новую группу
        cursor.execute(
            "INSERT INTO groups (code, creator_id) VALUES (?, ?)",
            (group_code, creator_id)
        )
        # Добавляем создателя в таблицу group_users
        cursor.execute(
            "INSERT INTO group_users (group_code, user_id) VALUES (?, ?)",
            (group_code, creator_id)
        )
    conn.commit()
    conn.close()

def add_user_to_group(group_code: str, user_id: int) -> bool:
    """
    Возвращает True, если пользователь успешно добавлен
    или уже находится в группе. False, если группы не существует.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT code FROM groups WHERE code = ?", (group_code,))
    group_exists = cursor.fetchone()
    if not group_exists:
        conn.close()
        return False

    # Проверяем, не добавлен ли пользователь уже
    cursor.execute(
        "SELECT id FROM group_users WHERE group_code = ? AND user_id = ?",
        (group_code, user_id)
    )
    row = cursor.fetchone()
    if not row:
        cursor.execute(
            "INSERT INTO group_users (group_code, user_id) VALUES (?, ?)",
            (group_code, user_id)
        )
    conn.commit()
    conn.close()
    return True

def get_user_group(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT group_code
        FROM group_users
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def save_movie_rating(user_id: int, movie_id: int, rating: int):
    """
    Сохраняем рейтинг фильма пользователем. Если уже есть запись — не меняем,
    т.к. в условии сказано, что менять оценку нельзя.
    """
    group_code = get_user_group(user_id)
    if not group_code:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM ratings
        WHERE group_code = ? AND user_id = ? AND movie_id = ?
    """, (group_code, user_id, movie_id))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO ratings (group_code, user_id, movie_id, rating)
            VALUES (?, ?, ?, ?)
        """, (group_code, user_id, movie_id, rating))
        conn.commit()
    conn.close()

def get_common_movies_for_group(group_code: str):
    """
    Ищем фильмы, у которых рейтинг >= MIN_RATING_THRESHOLD от всех участников группы.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Кол-во участников
    cursor.execute("""
        SELECT COUNT(*) FROM group_users
        WHERE group_code = ?
    """, (group_code,))
    (user_count,) = cursor.fetchone()  # кортеж (число,)

    # Ищем фильм, у которого есть нужный рейтинг от каждого участника
    query = """
        SELECT movie_id
        FROM ratings
        WHERE group_code = ?
          AND rating >= ?
        GROUP BY movie_id
        HAVING COUNT(DISTINCT user_id) = ?
    """
    cursor.execute(query, (group_code, MIN_RATING_THRESHOLD, user_count))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return []

    movie_ids = [row[0] for row in rows]

    # Подтягиваем инфу о каждом фильме из Кинопоиска
    from bot.services.kinopoisk_api import get_movie_info_by_id
    results = []
    for mid in movie_ids:
        info = get_movie_info_by_id(mid)
        if info:
            results.append(info)
        else:
            results.append({"id": mid, "title": f"MovieID {mid}", "year": None})
    return results
