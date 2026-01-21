from __future__ import annotations
from typing import Any, Literal, Optional
import httpx

Source = Literal["greenhouse", "lever"]

def greenhouse_jobs_list(board: str, limit: int, timeout_sec: int) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    r = httpx.get(url, timeout=timeout_sec)
    if r.status_code == 404:
        return []

    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobs", [])
    return jobs[:limit]

def fetch_url(url: str, timeout_sec: int) -> tuple[int, str | None, dict[str, Any] | None, str]:
    with httpx.Client(follow_redirects=True, timeout=timeout_sec) as client:
        r = client.get(url, headers={"user-agent": "openfunnel-takehome/0.1"})
        content_type = r.headers.get("content-type")
        headers_json = dict(r.headers)
        return r.status_code, content_type, headers_json, r.text, str(r.url)
