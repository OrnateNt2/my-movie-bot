import sqlite3
from config import DATABASE_PATH, MIN_RATING_THRESHOLD

def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.execute("""CREATE TABLE IF NOT EXISTS groups(
id INTEGER PRIMARY KEY AUTOINCREMENT,
code TEXT UNIQUE NOT NULL,
creator_id INTEGER,
group_name TEXT,
filter_rating_min INTEGER,
filter_rating_max INTEGER,
filter_year_start INTEGER,
filter_year_end INTEGER,
filter_type TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS group_users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
group_code TEXT NOT NULL,
user_id INTEGER NOT NULL,
is_active INTEGER DEFAULT 0,
user_name TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS ratings(
id INTEGER PRIMARY KEY AUTOINCREMENT,
group_code TEXT NOT NULL,
user_id INTEGER NOT NULL,
movie_id INTEGER NOT NULL,
rating INTEGER NOT NULL)""")
    return conn

def create_group_with_name(group_code, creator_id, group_name, creator_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE group_users SET is_active=0 WHERE user_id=?",(creator_id,))
    cur.execute("SELECT code FROM groups WHERE code=?",(group_code,))
    row = cur.fetchone()
    if not row:
        cur.execute("""INSERT INTO groups(code, creator_id, group_name)
VALUES(?,?,?)""",(group_code, creator_id, group_name))
        cur.execute("""INSERT INTO group_users(group_code, user_id, is_active, user_name)
VALUES(?,?,1,?)""",(group_code, creator_id, creator_name))
    conn.commit()
    conn.close()

def add_user_to_group(group_code, user_id, user_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT code FROM groups WHERE code=?",(group_code,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("SELECT id FROM group_users WHERE group_code=? AND user_id=?",(group_code, user_id))
    row = cur.fetchone()
    if not row:
        cur.execute("""INSERT INTO group_users(group_code, user_id, is_active, user_name)
VALUES(?,?,0,?)""",(group_code, user_id, user_name))
    else:
        cur.execute("UPDATE group_users SET user_name=? WHERE group_code=? AND user_id=?",(user_name, group_code, user_id))
    conn.commit()
    conn.close()
    return True

def get_user_active_group(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT group_code FROM group_users WHERE user_id=? AND is_active=1 ORDER BY id DESC LIMIT 1",(user_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_group_creator_id(group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT creator_id FROM groups WHERE code=?",(group_code,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_all_groups_for_user(user_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""SELECT g.code, g.group_name, gu.is_active
FROM group_users gu JOIN groups g ON g.code=gu.group_code WHERE gu.user_id=?""",(user_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def set_active_group(user_id, group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM group_users WHERE group_code=? AND user_id=?",(group_code, user_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("UPDATE group_users SET is_active=0 WHERE user_id=?",(user_id,))
    cur.execute("UPDATE group_users SET is_active=1 WHERE group_code=? AND user_id=?",(group_code, user_id))
    conn.commit()
    conn.close()
    return True

def leave_group(user_id, group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM group_users WHERE group_code=? AND user_id=?",(group_code, user_id))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False
    cur.execute("DELETE FROM group_users WHERE group_code=? AND user_id=?",(group_code, user_id))
    conn.commit()
    conn.close()
    return True

def get_group_users(group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT user_id, user_name, is_active FROM group_users WHERE group_code=?",(group_code,))
    rows = cur.fetchall()
    conn.close()
    return rows

def save_movie_rating(user_id, movie_id, rating):
    group_code = get_user_active_group(user_id)
    if not group_code:
        return
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM ratings WHERE group_code=? AND user_id=? AND movie_id=?",(group_code, user_id, movie_id))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO ratings(group_code, user_id, movie_id, rating) VALUES(?,?,?,?)",(group_code, user_id, movie_id, rating))
        conn.commit()
    conn.close()

def get_common_movies_for_group(group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM group_users WHERE group_code=?",(group_code,))
    (count_users,) = cur.fetchone()
    query = """SELECT movie_id FROM ratings WHERE group_code=? AND rating>=? GROUP BY movie_id HAVING COUNT(DISTINCT user_id)=?"""
    cur.execute(query,(group_code, MIN_RATING_THRESHOLD, count_users))
    rows = cur.fetchall()
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

def update_group_filters(group_code, content_type, rating_min, rating_max, year_start, year_end):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""UPDATE groups SET filter_type=?, filter_rating_min=?, filter_rating_max=?, filter_year_start=?, filter_year_end=? WHERE code=?""",
                (content_type, rating_min, rating_max, year_start, year_end, group_code))
    conn.commit()
    conn.close()

def get_group_filters(group_code):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT filter_type, filter_rating_min, filter_rating_max, filter_year_start, filter_year_end FROM groups WHERE code=?",(group_code,))
    row = cur.fetchone()
    conn.close()
    if row:
        content_type = row[0] if row[0] is not None else ""
        rating_min = row[1] if row[1] is not None else 5
        rating_max = row[2] if row[2] is not None else 10
        year_start = row[3]
        year_end = row[4]
        return (content_type, rating_min, rating_max, year_start, year_end)
    return ("", 5, 10, None, None)
