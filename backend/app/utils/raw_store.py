import os, json
from app.core.config import settings

def store_json(url_hash: str, obj: dict) -> str:
    os.makedirs(settings.raw_store_dir, exist_ok=True)
    path = os.path.join(settings.raw_store_dir, f"{url_hash}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
    return path
