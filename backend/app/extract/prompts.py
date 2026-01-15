def small_model_prompt(job_text: str) -> str:
    return f"""You are an information extraction assistant.
Extract minimal structured fields from the job posting text.

Return JSON with keys:
summary (string),
role_function (string),
seniority (string or null),
location_city (string or null),
location_state (string or null),
location_country (string or null),
salary_min (int or null),
salary_max (int or null),
salary_currency (string or null),
skills (array of strings).

Job posting:
""" + job_text[:12000]

def high_tier_prompt(job_text: str) -> str:
    return f"""You are a precise information extraction assistant for job postings.
Return STRICT JSON only (no markdown).

Fields:
- summary: 2-3 sentence summary of what the job is about.
- role_function: one of [sales, marketing, engineering, product, data, security, finance, operations, hr, customer_success, other]
- seniority: one of [intern, junior, mid, senior, staff, principal, lead, manager, director, vp, cxo, other] or null
- location_city/state/country if present
- salary_min/salary_max/salary_currency if present
- skills: list of technologies/skills explicitly mentioned.

Job posting:
""" + job_text[:20000]
