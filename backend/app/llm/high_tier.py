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

def _anthropic_chat(prompt: str) -> str:
    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": settings.anthropic_api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {"model": settings.high_tier_model, "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]}
    with httpx.Client(timeout=120) as client:
        r = client.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        content = data.get("content", [])
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return "\n".join(texts).strip()

def chat(prompt: str) -> str:
    if settings.high_tier_provider == "anthropic":
        return _anthropic_chat(prompt)
    return _openai_chat(prompt)
