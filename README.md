# OpenFunnel — Job GTM Intelligence Platform (50k scale take-home)

This project builds an end-to-end pipeline to discover, scrape, extract, normalize, and query job postings at scale for GTM teams.
Users can search jobs and extracted signals (role function, summary, tech/skill signals) via API endpoints; the system is designed to scale to 50,000+ postings with distributed workers.

## What this does
- Discovers job posting URLs (Greenhouse / Lever sources)
- Scrapes raw HTML/JSON and stores raw responses
- Runs LLM extraction (local Ollama) into structured fields
- Normalizes skills and links skills ↔ jobs
- Exposes read APIs to filter and retrieve jobs/extractions/skills
- Uses Redis queues + worker crash recovery (inflight + visibility timeout reaper)

## Architecture (high level)
Components:
- api: FastAPI read/query layer + orchestration endpoints (optional)
- postgres: storage for job_postings, raw_responses, extractions, skills, job_skills
- redis: task queue (scrape/extract) with inflight/DLQ + retry semantics
- scraper worker: consumes scrape tasks, fetches postings, stores raw_responses, marks jobs fetched
- extractor worker: consumes extract tasks, loads raw_responses, calls Ollama, validates JSON, writes extractions + skills, marks jobs extracted
- reaper worker: requeues stale inflight tasks (worker crash recovery)

Data lifecycle:
discovered → fetched (raw saved) → extracted (structured + skills saved)

## Quickstart
Prereqs:
- Docker / Docker Compose

Run:
- make up
- make migrate
- make seed (optional: seeds initial discovered job URLs)

Health checks:
- GET /health
- GET /health/db
- GET /health/redis

## Demo (end-to-end via curl)
This demo seeds discovered jobs, enqueues scrape + extract tasks for each job, and then queries results.

1) Run the full pipeline (seed → enqueue scrape/extract)
```bash
curl -s -X POST http://localhost:8000/run/all | jq
```
Response includes:
- run_id
- trace_id
- job_count

2) Wait until extractions complete
```bash
JOB_ID=$(curl -s "http://localhost:8000/job_postings?status=extracted&limit=1" | jq -r '.items[0].id')

curl -s "http://localhost:8000/job_postings/${JOB_ID}" | jq
curl -s "http://localhost:8000/extractions/${JOB_ID}" | jq
curl -s "http://localhost:8000/job_postings/${JOB_ID}/skills" | jq
```
4) Example “search & analytics” queries (API-backed)
```bash
# All extracted roles mentioning a skill (example)
curl -s "http://localhost:8000/job_postings?status=extracted&skill=python&limit=25" | jq

# Company filter (example)
curl -s "http://localhost:8000/job_postings?status=extracted&company_name=Stripe&limit=25" | jq

# Location filter (example)
curl -s "http://localhost:8000/job_postings?status=extracted&location=NYC&limit=25" | jq
```
5)Query results
- List jobs with filters:
  - GET /job_postings?status=extracted&location=NYC&min_comp=200000&seniority=staff
- Get job detail:
  - GET /job_postings/{id}
- Get extraction detail:
  - GET /extractions/{job_posting_id}
- Get skills for job:
  - GET /job_postings/{id}/skills

## How do you handle 50k requests without getting banned?
This system is designed around “polite concurrency + distribution” rather than brute force:
- Concurrency is controlled at the worker level (N scraper workers, each with bounded parallelism)
- Per-host throttling and exponential backoff on 429/5xx
- Request jitter to avoid synchronized bursts
- Rotating User-Agent and honoring redirects
- Optional proxy support (if enabled) for higher scale

Discovery is separated from fetch/extract so rate-limits don’t stall the whole pipeline:
- discovery produces URLs slowly and continuously
- scrape workers fetch with backoff + retries
- extract workers proceed independently from scrape progress

## LLM strategy (high-throughput extraction)
Extraction uses local Ollama for cost-effective throughput:
- Strict JSON schema output + Pydantic validation
- Retries for invalid JSON / malformed responses
- Skills normalization stored separately and linked via join table

Batching strategy:
- Instead of serial calls, extraction is parallelized across many extractor workers
- Each worker processes jobs independently; overall throughput scales horizontally with worker count
- This is “batching by concurrency” (queue-driven), which is the practical approach for 50k jobs

Optional two-tier model plan:
- Small local model for classification/filtering + quick summaries
- Higher-tier model only when confidence is low or extraction fails validation repeatedly

## Estimated LLM cost (token math)
Assumptions (adjustable):
- Average posting length processed: ~1,500–3,000 tokens (after cleaning)
- Output: ~200–400 tokens JSON
- Total per job: ~2,000–3,500 tokens

For 50,000 jobs:
- Total tokens: 100M–175M tokens

Cost scenarios:
- Local Ollama: effectively $0 marginal token cost (compute-bound)
- Paid API model: depends on pricing; the design minimizes paid usage by defaulting to local and only escalating difficult cases

## How would you scale this to 1 million jobs?
1) Add more worker replicas (horizontal scaling)
- Redis queue supports many consumers; Postgres needs indexing + partitioning strategy

2) Improve storage + throughput
- Partition raw_responses by run/date/source
- Add a “cold storage” layer for raw HTML (S3/GCS) + keep only pointers + checksums in Postgres
- Use COPY / bulk inserts for ingestion bursts

3) Stronger discovery
- Multi-source discovery (boards + sitemaps + company career pages)
- Distributed URL frontier with dedupe (canonical_url_hash + checksum)

4) More robust anti-rate-limit posture
- Per-domain adaptive throttling
- Optional proxy pool + circuit breakers
- Content-based caching/dedupe to avoid refetching

5) Extraction efficiency
- Triage/filter stage (cheap) → full extraction (expensive)
- Streaming parsing and smaller contexts (only relevant sections)
- Cache extraction results keyed by raw checksum

## Notes / tradeoffs
- UI is intentionally not included in this submission. The API supports the required search/analytics and can be wired to a frontend.
- The focus is on scalable, fault-tolerant ingestion + extraction and a clean read/query layer.

## Repo layout
- api/ ...
- workers/ (scraper, extractor, reaper)
- db/ (models, migrations)
- scripts/ (seed/discovery helpers)
- docker-compose.yml
- Makefile
