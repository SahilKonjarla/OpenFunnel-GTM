from __future__ import annotations
from typing import Any
from .http import fetch_json

def board_url(company_slug: str) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

def job_url(company_slug: str, job_id: int) -> str:
    return f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"

def fetch_board(company_slug: str):
    return fetch_json(board_url(company_slug))

def fetch_job(company_slug: str, job_id: int):
    return fetch_json(job_url(company_slug, job_id))
