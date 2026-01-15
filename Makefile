SHELL := /bin/bash

.PHONY: up down logs migrate api ui seed worker-scrape worker-extract format lint test

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
	docker compose up --build worker_scrape

worker-extract:
	docker compose up --build worker_extract

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
