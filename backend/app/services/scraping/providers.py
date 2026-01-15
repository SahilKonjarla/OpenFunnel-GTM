from __future__ import annotations
from typing import Any, Literal, Optional
import httpx

Source = Literal["greenhouse", "lever"]

def greenhouse_jobs_list(board: str, limit: int, timeout_sec: int) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    r = httpx.get(url, timeout=timeout_sec)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobs", [])
    return jobs[:limit] if limit else jobs

def lever_jobs_page(
    company: str,
    limit: int,
    timeout_sec: int,
    offset: Optional[str] = None,
) -> tuple[list[dict[str, Any]], Optional[str], bool]:
    params = {"mode": "json", "limit": str(limit)}
    if offset:
        params["offset"] = offset
    url = f"https://api.lever.co/v0/postings/{company}"
    r = httpx.get(url, params=params, timeout=timeout_sec)
    r.raise_for_status()
    payload = r.json()

    # Lever sometimes returns list (no pagination info) for small sets.
    if isinstance(payload, list):
        return payload, None, False

    jobs = payload.get("data", []) if isinstance(payload, dict) else []
    next_offset = payload.get("next") if isinstance(payload, dict) else None
    has_next = bool(payload.get("hasNext")) if isinstance(payload, dict) else False
    return jobs, next_offset, has_next

def lever_jobs_list(company: str, limit: int, timeout_sec: int) -> list[dict[str, Any]]:
    jobs, _, _ = lever_jobs_page(company=company, limit=limit, timeout_sec=timeout_sec, offset=None)
    return jobs[:limit] if limit else jobs

def fetch_url(url: str, timeout_sec: int) -> tuple[int, str | None, dict[str, Any] | None, str]:
    with httpx.Client(follow_redirects=True, timeout=timeout_sec) as client:
        r = client.get(url, headers={"user-agent": "openfunnel-takehome/0.1"})
        content_type = r.headers.get("content-type")
        headers_json = dict(r.headers)
        return r.status_code, content_type, headers_json, r.text, str(r.url)
