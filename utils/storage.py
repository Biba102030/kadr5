import json
import os

def load_cache():
    try:
        if os.path.exists("cache.json"):
            with open("cache.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Ошибка загрузки кэша: {e}")
        return {}

def save_cache(cache):
    try:
        with open("cache.json", "w", encoding="utf-8") as f:
            json.dump(cache, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Ошибка сохранения кэша: {e}")