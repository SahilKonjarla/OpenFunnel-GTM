from __future__ import annotations
from typing import Any
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential_jitter

DEFAULT_UA = "openfunnel-takehome/0.1"

@retry(stop=stop_after_attempt(5), wait=wait_exponential_jitter(initial=1, max=20))
def fetch_json(url: str, timeout_sec: int = 20, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any] | None, dict[str, Any], str]:
    h = {"user-agent": DEFAULT_UA}
    if headers:
        h.update(headers)
    with httpx.Client(timeout=timeout_sec, follow_redirects=True) as client:
        r = client.get(url, headers=h)
        content_type = r.headers.get("content-type", "")
        try:
            data = r.json()
        except Exception:
            data = None
        return r.status_code, data, dict(r.headers), content_type
