from __future__ import annotations


def build_extraction_prompt(*, html_text: str) -> str:
    return f"""
You are extracting structured fields from a job posting.

Return ONLY valid JSON (no markdown, no commentary).
If a field is unknown, use null.
Skills should be a list of strings.

JSON schema:
{{
  "summary": string|null,
  "seniority": string|null,
  "remote_flag": boolean|null,
  "salary_min": number|null,
  "salary_max": number|null,
  "salary_currency": string|null,
  "hiring_function": string|null,
  "location_city": string|null,
  "location_region": string|null,
  "location_country": string|null,
  "skills": [string]
}}

JOB HTML:
{html_text}
""".strip()
