SHELL := /bin/bash

.PHONY: up down logs migrate api ui seed worker-scrape worker-extract format lint test

SCRAPE_WORKERS ?= 1
EXTRACT_WORKERS ?= 1

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose run --rm api alembic upgrade head

api:
	docker compose up --build api

worker-scrape:
	docker compose up -d --scale worker_scrape=$(SCRAPE_WORKERS) worker_scrape

worker-extract:
	docker compose up -d --scale worker_extract=$(EXTRACT_WORKERS) worker_extract

seed:
	docker compose run --rm api python -m app.scripts.seed_greenhouse

ui:
	cd frontend && npm install && npm run dev -- --host

format:
	docker compose run --rm api ruff format .

lint:
	docker compose run --rm api ruff check .

test:
	docker compose run --rm api pytest -q

demo:
	$(MAKE) seed
	$(MAKE) worker-extract
	$(MAKE) worker-scrape
	$(MAKE) ui
