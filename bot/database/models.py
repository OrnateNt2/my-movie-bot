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


def get_group_name(group_code: str) -> str:
    """
    Возвращает название группы (group_name) по её коду.
    Если не найдена, вернёт пустую строку.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM groups WHERE code = ?", (group_code,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else ""


def create_group_with_name(group_code: str, creator_id: int, group_name: str):
    """
    Создаёт новую группу (code, creator_id, group_name), 
    делает её активной у создателя (is_active=1), обнуляя прочие.
    """
    conn = get_connection()
    cursor = conn.cursor()
    # Сбрасываем активность у всех групп этого пользователя
    cursor.execute("""
        UPDATE group_users
        SET is_active = 0
        WHERE user_id = ?
    """, (creator_id,))
    
    # Создаём группу
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
    Присоединяет пользователя к группе (is_active=0).
    Возвращает True, если группа существует, иначе False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT code FROM groups WHERE code = ?", (group_code,))
    group_exists = cursor.fetchone()
    if not group_exists:
        conn.close()
        return False

    cursor.execute("""
        SELECT id FROM group_users
        WHERE group_code = ? AND user_id = ?
    """, (group_code, user_id))
    row = cursor.fetchone()
    if not row:
        cursor.execute("""
            INSERT INTO group_users (group_code, user_id, is_active)
            VALUES (?, ?, 0)
        """, (group_code, user_id))
    conn.commit()
    conn.close()
    return True


def get_user_active_group(user_id: int) -> str:
    """
    Возвращает code активной группы (is_active=1).
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
    Делает указанную группу активной. Возвращает True, если пользователь 
    действительно в группе, иначе False.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM group_users
        WHERE group_code = ? AND user_id = ?
    """, (group_code, user_id))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return False

    cursor.execute("""
        UPDATE group_users
        SET is_active = 0
        WHERE user_id = ?
    """, (user_id,))

    cursor.execute("""
        UPDATE group_users
        SET is_active = 1
        WHERE user_id = ? AND group_code = ?
    """, (user_id, group_code))
    conn.commit()
    conn.close()
    return True


def get_all_groups_for_user(user_id: int):
    """
    Возвращает [(code, group_name, is_active), ...].
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT g.code, g.group_name, gu.is_active
        FROM group_users gu
        JOIN groups g ON g.code = gu.group_code
        WHERE gu.user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows


def leave_group(user_id: int, group_code: str) -> tuple[bool, str]:
    """
    Удаляет пользователя из группы. Возвращает (success, group_name).
    success=True, если действительно был в группе.
    
    Если хотите удалить все его оценки, раскомментируйте соответствующий блок.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM group_users
        WHERE user_id = ? AND group_code = ?
    """, (user_id, group_code))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return (False, "")

    # Получаем название группы (чтобы вернуть в ответе)
    group_name = get_group_name(group_code)

    cursor.execute("""
        DELETE FROM group_users
        WHERE user_id = ? AND group_code = ?
    """, (user_id, group_code))

    # Удалять оценки:
    # cursor.execute("""
    #     DELETE FROM ratings
    #     WHERE user_id = ? AND group_code = ?
    # """, (user_id, group_code))

    conn.commit()
    conn.close()
    return (True, group_name)


def save_movie_rating(user_id: int, movie_id: int, rating: int):
    """
    Сохраняем оценку для активной группы пользователя.
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
    Фильмы, у которых рейтинг >= MIN_RATING_THRESHOLD от всех участников группы.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT COUNT(*) FROM group_users
        WHERE group_code = ?
    """, (group_code,))
    (user_count,) = cursor.fetchone()

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
