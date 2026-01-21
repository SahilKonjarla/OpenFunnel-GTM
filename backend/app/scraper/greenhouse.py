from __future__ import annotations
from .http import fetch_json

def board_url(company_slug: str) -> str:
    # Build the Greenhouse "jobs board" API URL for a given company slug.\
    return f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs"

def job_url(company_slug: str, job_id: int) -> str:
    # Build the Greenhouse "single job" API URL for a given company slug + job id.
    return f"https://boards-api.greenhouse.io/v1/boards/{company_slug}/jobs/{job_id}"

def fetch_board(company_slug: str):
    # Fetch the full list of jobs from a company's Greenhouse board.
    # Returns parsed JSON (Python dict) from the Greenhouse API response.
    return fetch_json(board_url(company_slug))

def fetch_job(company_slug: str, job_id: int):
    # Fetch a single job posting JSON payload from Greenhouse.
    # Returns parsed JSON (Python dict) from the Greenhouse API response.
    return fetch_json(job_url(company_slug, job_id))
