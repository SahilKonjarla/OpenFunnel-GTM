from __future__ import annotations
import httpx
from app.core.config import settings

def _openai_chat(prompt: str) -> str:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    url = "https://api.openai.com/v1/responses"
    headers = {"Authorization": f"Bearer {settings.openai_api_key}", "Content-Type": "application/json"}
    payload = {"model": settings.high_tier_model, "input": prompt}
    with httpx.Client(timeout=120) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        out = data.get("output", [])
        texts = []
        for item in out:
            for c in item.get("content", []):
                if c.get("type") in ("output_text", "text"):
                    texts.append(c.get("text", ""))
        return "\n".join(texts).strip()

def chat(prompt: str) -> str:
    return _openai_chat(prompt)
