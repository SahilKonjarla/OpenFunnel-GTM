# 🧠 OpenFunnel-GTM

A scalable, containerized GTM (Go-to-Market) intelligence platform built with Docker and Python. This project orchestrates services like FastAPI, Redis, Postgres, frontend UI, and distributed worker processes for scraping and extraction.

---

## 📦 Project Structure

- `api` – FastAPI-based backend service
- `frontend` – Web interface
- `worker_scraper` – Scrapes target data sources
- `worker_extractor` – Extracts and processes information
- `postgres` – Relational database
- `redis` – Message broker / cache
- `ollama` – Language model runtime (e.g., LLM-based processing)

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/products/docker-desktop)
- [Make](https://www.gnu.org/software/make/) (pre-installed on most Unix systems)

---

### 🔧 Start All Services

```bash
make up
```
Scale workers at startup:
```bash
SCRAPER_WORKERS=3 EXTRACTOR_WORKERS=2 make up
```

---

## ⚙️ Makefile Targets

| Command               | Description                                  |
|------------------------|----------------------------------------------|
| `make up`              | Start all services (API, workers, DB, frontend) |
| `make down`            | Stop and remove all containers             |
| `make logs`            | View and follow all service logs           |
| `make api`             | Start only the API and its dependencies     |
| `make workers`         | Start both worker services (scraper + extractor) |
| `make scraper_worker`  | Start only the scraper worker(s)           |
| `make extractor_worker`| Start only the extractor worker(s)         |
| `make db`              | Start only the Postgres service            |
| `make redis`           | Start only the Redis service               |

---

## 🧪 Environment Variables

Customize worker scaling:

| Variable            | Description                         | Default |
|---------------------|-------------------------------------|---------|
| `SCRAPER_WORKERS`   | Number of parallel scraper workers  | `1`     |
| `EXTRACTOR_WORKERS` | Number of parallel extractor workers| `1`     |

Example:
```bash
SCRAPER_WORKERS=5 EXTRACTOR_WORKERS=3 make workers
```

---

## ✅ Example Workflows

Start the full stack (default):
```bash
make up
```
Start full stack with custom worker counts:
```bash
SCRAPER_WORKERS=3 EXTRACTOR_WORKERS=2 make up
```
Stop all services:
```bash
make down
```
View logs:
```bash
make logs
```
---

## 🛠️ Notes

- Docker Compose handles orchestration.
- Worker services are stateless and scalable.
- Scaling is handled with `--scale` via environment variables.

---
