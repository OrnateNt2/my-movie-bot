import requests, random
from config import KINOPOISK_API_KEY

API_BASE = "https://api.kinopoisk.dev/v1.4/movie"

def get_random_movie_by_filters(content_type=None, limit=20):
    if not KINOPOISK_API_KEY:
        return None
    headers = {"X-API-KEY": KINOPOISK_API_KEY, "accept": "application/json"}
    params = {"rating.kp": "5-10", "limit": limit, "page": 1}
    if content_type:
        params["type"] = content_type
    try:
        r = requests.get(API_BASE, headers=headers, params=params, timeout=10)
        if not r.ok:
            return None
        data = r.json()
        docs = data.get("docs", [])
        if not docs:
            return None
        return random.choice(docs)
    except:
        return None

def get_movie_info_by_id(movie_id):
    if not KINOPOISK_API_KEY:
        return None
    headers = {"X-API-KEY": KINOPOISK_API_KEY, "accept": "application/json"}
    url = f"{API_BASE}/{movie_id}"
    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            movie = r.json()
            return {
                "id": movie.get("id"),
                "title": movie.get("name"),
                "year": movie.get("year"),
                "description": movie.get("description", "")
            }
    except:
        pass
    return None
