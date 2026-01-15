from __future__ import annotations
import httpx
from app.core.config import settings

def chat(prompt: str, model: str | None = None) -> str:
    m = model or settings.ollama_model_small
    url = f"{settings.ollama_base_url}/api/generate"
    payload = {"model": m, "prompt": prompt, "stream": False}
    with httpx.Client(timeout=120) as client:
        r = client.post(url, json=payload)
        r.raise_for_status()
        return r.json().get("response", "")
