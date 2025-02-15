# bot/database/models.py
import sqlite3
from config import DATABASE_PATH, MIN_RATING_THRESHOLD

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            creator_id INTEGER,
            group_name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS group_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_code TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            is_active INTEGER DEFAULT 0
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

def create_group_with_name(group_code: str, creator_id: int, group_name: str):
    """
    Создаёт новую группу (code, creator_id, group_name) и добавляет создателя,
    при этом делаем её активной (is_active=1) и выключаем активность
    в остальных группах пользователя.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Сначала сбрасываем is_active у всех групп данного пользователя
    cursor.execute("""
        UPDATE group_users
        SET is_active = 0
        WHERE user_id = ?
    """, (creator_id,))

    # Теперь создаём запись о группе
    cursor.execute("SELECT code FROM groups WHERE code = ?", (group_code,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO groups (code, creator_id, group_name)
            VALUES (?, ?, ?)
        """, (group_code, creator_id, group_name))

        cursor.execute("""
            INSERT INTO group_users (group_code, user_id, is_active)
            VALUES (?, ?, 1)
        """, (group_code, creator_id))
    conn.commit()
    conn.close()

def add_user_to_group(group_code: str, user_id: int) -> bool:
    """
    Присоединяет пользователя к группе с кодом group_code, делает is_active=0 по умолчанию.
    Возвращает True, если группа существует (и пользователь добавлен/уже есть),
    иначе False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM groups WHERE code = ?", (group_code,))
    group_exists = cursor.fetchone()
    if not group_exists:
        conn.close()
        return False

    # Проверяем, не добавлен ли уже
    cursor.execute("""
        SELECT id FROM group_users
        WHERE group_code = ? AND user_id = ?
    """, (group_code, user_id))
    row = cursor.fetchone()
    if not row:
        # Добавляем с is_active=0
        cursor.execute("""
            INSERT INTO group_users (group_code, user_id, is_active)
            VALUES (?, ?, 0)
        """, (group_code, user_id))
    conn.commit()
    conn.close()
    return True

def get_user_active_group(user_id: int) -> str:
    """
    Возвращает code активной группы (где is_active=1).
    Если нет активной группы — None.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT group_code
        FROM group_users
        WHERE user_id = ? AND is_active=1
        ORDER BY id DESC
        LIMIT 1
    """, (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else None

def set_active_group(user_id: int, group_code: str) -> bool:
    """
    Делает указанную группу активной (is_active=1) для пользователя,
    снимает активность с остальных групп.
    Возвращает True, если удалось, False, если пользователь не состоит
    в этой группе.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Проверяем, состоит ли пользователь в этой группе
    cursor.execute("""
        SELECT id FROM group_users
        WHERE group_code = ? AND user_id = ?
    """, (group_code, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    # Сбрасываем is_active у всех групп
    cursor.execute("""
        UPDATE group_users
        SET is_active = 0
        WHERE user_id = ?
    """, (user_id,))
    # Включаем is_active=1 для нужной
    cursor.execute("""
        UPDATE group_users
        SET is_active = 1
        WHERE group_code = ? AND user_id = ?
    """, (group_code, user_id))
    conn.commit()
    conn.close()
    return True

def get_all_groups_for_user(user_id: int):
    """
    Возвращает список кортежей (group_code, group_name, is_active).
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.code, g.group_name, gu.is_active
        FROM group_users gu
        JOIN groups g ON gu.group_code = g.code
        WHERE gu.user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def leave_group(user_id: int, group_code: str) -> bool:
    """
    Удаляет пользователя из указанной группы. 
    Возвращает True, если пользователь действительно состоял в группе.
    По желанию можно ещё удалить оценки (ratings).
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Проверяем наличие
    cursor.execute("""
        SELECT id FROM group_users
        WHERE user_id = ? AND group_code = ?
    """, (user_id, group_code))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    # Удаляем запись
    cursor.execute("""
        DELETE FROM group_users
        WHERE user_id = ? AND group_code = ?
    """, (user_id, group_code))

    # Если хотите также удалить все оценки пользователя в этой группе:
    # cursor.execute("""
    #     DELETE FROM ratings
    #     WHERE user_id = ? AND group_code = ?
    # """, (user_id, group_code))

    conn.commit()
    conn.close()
    return True

def save_movie_rating(user_id: int, movie_id: int, rating: int):
    """
    Сохраняем оценку для активной группы.
    """
    group_code = get_user_active_group(user_id)
    if not group_code:
        return
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM ratings
        WHERE group_code = ?
          AND user_id = ?
          AND movie_id = ?
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
    Фильмы, которые все участники группы оценили >= MIN_RATING_THRESHOLD.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Считаем, сколько людей в группе
    cursor.execute("""
        SELECT COUNT(*) FROM group_users
        WHERE group_code = ?
    """, (group_code,))
    (user_count,) = cursor.fetchone()

    # Ищем фильмы, у которых рейтинг >= MIN_RATING_THRESHOLD у всех
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

    movie_ids = [r[0] for r in rows]

    from bot.services.kinopoisk_api import get_movie_info_by_id
    results = []
    for mid in movie_ids:
        info = get_movie_info_by_id(mid)
        if info:
            results.append(info)
        else:
            results.append({"id": mid, "title": f"MovieID {mid}", "year": "?"})
    return results
