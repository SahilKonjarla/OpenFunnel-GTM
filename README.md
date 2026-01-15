# OpenFunnel – Job GTM Intelligence Platform (Take-Home)

This repo is a complete, runnable reference implementation for the assessment in **Take-Home Assessment: Job GTM Intelligence Platform (Scale: 50k)**.

It implements:

- Scraping engine that can **discover and download job postings** from a real source (Greenhouse job boards) and store **raw JSON** before processing.
- High-throughput **LLM extraction pipeline** with **micro-batching + concurrency**, using:
  - **Ollama** small model (Llama/Mistral) for cheap cleaning/filtering
  - optional **OpenAI/Anthropic** (high-tier) for harder extractions
- Distributed architecture with:
  - **Redis** task queue (visibility timeout + retries)
  - **multiple worker nodes** for scrape/extract
  - **Postgres** for durable storage + indexed search
- UI:
  - A minimal React UI for **search + analytics**, robust filtering, and **highlighting**.

---

## Demo: run locally

### Prereqs
- Docker + Docker Compose
- (optional) OpenAI/Anthropic API keys if you want premium model routing

### 1) Start services
```bash
make up
```

### 2) Apply DB migrations
```bash
make migrate
```

### 3) Start API
```bash
make api
```

API docs: http://localhost:8000/docs

### 4) Start workers (separate terminals)
```bash
make worker-scrape
make worker-extract
```

### 5) Seed scraping jobs
In another terminal:
```bash
make seed
```

### 6) Start UI
```bash
make ui
```

UI: http://localhost:5173

---

## Notes

- By default, the seed list is modest so the demo runs quickly. To approach 50k, expand `backend/seed/greenhouse_companies.txt` with more company slugs.
- You can scale workers with:
  - `docker compose up --scale worker_scrape=4 --scale worker_extract=8`
