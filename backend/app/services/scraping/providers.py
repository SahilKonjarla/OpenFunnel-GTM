from __future__ import annotations
from typing import Any, Literal
import httpx

Source = Literal["greenhouse", "lever"]

def greenhouse_jobs_list(board: str, limit: int, timeout_sec: int) -> list[dict[str, Any]]:
    url = f"https://boards-api.greenhouse.io/v1/boards/{board}/jobs?content=true"
    r = httpx.get(url, timeout=timeout_sec)
    r.raise_for_status()
    data = r.json()
    jobs = data.get("jobs", [])
    return jobs[:limit]

def lever_jobs_list(company: str, limit: int, timeout_sec: int) -> list[dict[str, Any]]:
    url = f"https://api.lever.co/v0/postings/{company}?mode=json"
    r = httpx.get(url, timeout=timeout_sec)
    r.raise_for_status()
    jobs = r.json()
    return jobs[:limit]

def fetch_url(url: str, timeout_sec: int) -> tuple[int, str | None, dict[str, Any] | None, str]:
    r = httpx.get(url, timeout=timeout_sec, headers={"user-agent": "openfunnel-takehome/0.1"}, follow_redirects=True)
    status = r.status_code
    content_type = r.headers.get("content-type")
    headers_json = dict(r.headers)
    body_text = r.text
    return status, content_type, headers_json, body_text
