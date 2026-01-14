from __future__ import annotations
from typing import Any
import httpx
import json

def ollama_chat(
        *,
        base_url: str,
        model: str,
        prompt: str,
        timeout_sec: int = 60,
) -> str:
    url = f"{base_url.rstrip('/')}/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    r = httpx.post(url, json=payload, timeout=timeout_sec)
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    return data.get("response", "")

