.DEFAULT_GOAL := help

# ============== Help ==============
help:
	@echo ""
	@echo "============================================================"
	@echo "============================================================"
	@echo "                 OpenFunnel-GTM Commands                    "
	@echo ""
	@echo "------------------------ TARGETS ---------------------------"
	@echo "make up              start all services"
	@echo "------------------------------------------------------------"
	@echo "make down            stop all services"
	@echo "------------------------------------------------------------"
	@echo "make logs            follow logs"
	@echo "------------------------------------------------------------"
	@echo "make api             start only api + deps"
	@echo "------------------------------------------------------------"
	@echo "make workers         start only workers + deps"
	@echo "------------------------------------------------------------"
	@echo "make scraper_worker  start only scraper worker + deps"
	@echo "------------------------------------------------------------"
	@echo "make extract_worker  start only extractor worker + deps"
	@echo "------------------------------------------------------------"
	@echo "make reaper_worker   start only reaper worker + deps"
	@echo "------------------------------------------------------------"
	@echo "make db              start postgres only"
	@echo "------------------------------------------------------------"
	@echo "make redis           start redis only"
	@echo "------------------------------------------------------------"
	@echo "make migrate         start alembic"
	@echo "------------------------------------------------------------"
	@echo "make migration       new migration"
	@echo "------------------------------------------------------------"
	@echo "------------------------- ENV VARS -------------------------"
	@echo "SCRAPER_WORKERS=N     Number of scraper workers"
	@echo "EXTRACTOR_WORKERS=N   Number of extractor workers"
	@echo "============================================================"
	@echo "============================================================"
	@echo ""

# ============== Config ==============
SCRAPER_WORKERS ?= 1
EXTRACTOR_WORKERS ?= 1


# ======= Main Entrypoint ========
up:
	@echo ""
	@echo "============================================================"
	@echo "STARTING SERVICES..."
	docker compose up --build \
		--scale worker_scraper=${SCRAPER_WORKERS} \
		--scale worker_extractor=${EXTRACTOR_WORKERS} \
		postgres redis ollama api frontend worker_scraper worker_extractor

# ======= Other Commands ========
down:
	docker compose down

logs:
	docker compose logs -f

api:
	@echo ""
	@echo "============================================================"
	@echo "STARTING SERVICES..."
	docker compose up --build postgres redis ollama api

workers:
	docker compose up --build \
		--scale worker_scraper=${SCRAPER_WORKERS} \
		--scale worker_extractor=${EXTRACTOR_WORKERS} \
		postgres redis ollama worker_scraper worker_extractor

scraper_worker:
	docker compose up --build \
		--scale worker_scraper=${SCRAPER_WORKERS} \
		postgres redis ollama worker_scraper

extractor_worker:
	docker compose up --build \
		--scale worker_extractor=${EXTRACTOR_WORKERS} \
		postgres redis ollama worker_extractor

db:
	docker compose up postgres

redis:
	docker compose up redis

migrate:
	docker compose exec api alembic upgrade head

migration:
	docker compose exec api alembic revision -m "init" --autogenerate
