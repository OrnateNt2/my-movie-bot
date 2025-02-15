# bot/services/kinopoisk_api.py
import random
import requests
from config import KINOPOISK_API_KEY

API_BASE_URL = "https://api.kinopoisk.dev"
API_URL_MOVIE = f"{API_BASE_URL}/v1.4/movie"
API_URL_SEARCH = f"{API_BASE_URL}/v1.4/movie/search"

def get_random_movie_by_genre(genre: str):
    """
    Делаем запрос к эндпоинту /v1.4/movie
    с фильтрами по жанру (genres.name) и рейтингу kp>=6
    Берём limit=20, выбираем рандомный фильм из полученных.
    """
    if not KINOPOISK_API_KEY:
        return None

    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "accept": "application/json"
    }
    # Пример: берем рейтинг Кинопоиска 6-10, указываем жанр
    params = {
        "genres.name": genre,
        "rating.kp": "6-10",
        "limit": 20,
        "page": 1
    }

    try:
        response = requests.get(API_URL_MOVIE, headers=headers, params=params, timeout=10)
        if not response.ok:
            print("Ошибка при запросе к Кинопоиску:", response.status_code, response.text)
            return None

        data = response.json()
        docs = data.get("docs")
        if not docs:
            return None

        movie = random.choice(docs)
        # Собираем структуру
        return {
            "id": movie.get("id"),
            "title": movie.get("name") or "Без названия",
            "year": movie.get("year"),
            "poster": (movie.get("poster") or {}).get("url", ""),
            "description": movie.get("description", ""),
            "rating_kp": (movie.get("rating") or {}).get("kp"),
            "genres": [g["name"] for g in movie.get("genres", [])],
            "directors": []  # при желании можно смотреть "persons" и фильтровать по enProfession="director"
        }
    except Exception as e:
        print("Ошибка при запросе к Кинопоиску:", e)
        return None

def get_movie_info_by_id(movie_id: int):
    """
    Получить полную информацию о фильме по ID (эндпоинт: /v1.4/movie/{movie_id})
    """
    if not KINOPOISK_API_KEY:
        return None

    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "accept": "application/json"
    }
    url = f"{API_URL_MOVIE}/{movie_id}"

    try:
        response = requests.get(url, headers=headers, timeout=10)
        if not response.ok:
            print("Ошибка при запросе к Кинопоиску:", response.status_code, response.text)
            return None

        movie = response.json()
        return {
            "id": movie.get("id"),
            "title": movie.get("name"),
            "year": movie.get("year"),
            "description": movie.get("description", ""),
            "poster": (movie.get("poster") or {}).get("url", "")
        }
    except Exception as e:
        print("Ошибка при запросе к Кинопоиску (get_movie_info_by_id):", e)
        return None

def get_movie_by_name(title: str, limit: int = 5):
    """
    Пример поиска по названию: /v1.4/movie/search?query=title
    Возвращает первые limit результатов.
    """
    if not KINOPOISK_API_KEY:
        return []

    headers = {
        "X-API-KEY": KINOPOISK_API_KEY,
        "accept": "application/json"
    }
    params = {
        "query": title,
        "page": 1,
        "limit": limit
    }
    try:
        response = requests.get(API_URL_SEARCH, headers=headers, params=params, timeout=10)
        if not response.ok:
            print("Ошибка при запросе к Кинопоиску:", response.status_code, response.text)
            return []

        data = response.json()
        return data.get("docs", [])
    except Exception as e:
        print("Ошибка при поиске по названию:", e)
        return []
