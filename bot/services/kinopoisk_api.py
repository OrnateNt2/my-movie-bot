import requests
from config import KINOPOISK_API_KEY

API_RANDOM = "https://api.kinopoisk.dev/v1.4/movie/random"

def get_random_movie_random(content_type=None, rating_min=5, rating_max=10, year_start=None, year_end=None):
    if not KINOPOISK_API_KEY:
        return None
    headers = {"X-API-KEY": KINOPOISK_API_KEY, "accept": "application/json"}
    params = {}
    if content_type:
        params["type"] = content_type
    params["rating.kp"] = f"{rating_min}-{rating_max}"
    if year_start and year_end:
        params["year"] = f"{year_start}-{year_end}"
    elif year_start:
        params["year"] = str(year_start)
    try:
        r = requests.get(API_RANDOM, headers=headers, params=params, timeout=10)
        if not r.ok:
            return None
        data = r.json()
        return data
    except:
        return None

def get_movie_info_by_id(movie_id):
    if not KINOPOISK_API_KEY:
        return None
    headers = {"X-API-KEY": KINOPOISK_API_KEY, "accept": "application/json"}
    url = f"https://api.kinopoisk.dev/v1.4/movie/{movie_id}"
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
