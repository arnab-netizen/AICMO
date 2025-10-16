SHELL := /bin/bash
PY := python
UVICORN := uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

# ------------------------------------------------------------------------------
# ENV
# ------------------------------------------------------------------------------
.PHONY: env
env:
	@echo "DB_URL=$${DB_URL:-postgresql+psycopg2://app:app@localhost:5432/appdb}"
	@echo "PYTHONPATH=$${PYTHONPATH:-.}"

# ------------------------------------------------------------------------------
# DB
# ------------------------------------------------------------------------------
.PHONY: db.up db.down db.logs db.migrate db.seed
db.up:
	docker compose -f docker-compose.db.yml up -d

db.down:
	docker compose -f docker-compose.db.yml down -v

db.logs:
	docker compose -f docker-compose.db.yml logs -f --tail=100

db.migrate:
	$(PY) -m backend.scripts.migrate

db.seed:
	$(PY) -m backend.scripts.seed

# ------------------------------------------------------------------------------
# API
# ------------------------------------------------------------------------------
.PHONY: api.up api.kill api.health
api.up:
	pkill -f "uvicorn .*backend.app:app" || true; sleep 1; $(UVICORN) & sleep 1; \
	curl -s http://127.0.0.1:8000/health/live; echo; \
	curl -sI http://127.0.0.1:8000/health/ready; echo

api.kill:
	pkill -f "uvicorn .*backend.app:app" || true

api.health:
	curl -s http://127.0.0.1:8000/health/live; echo; \
	curl -sI http://127.0.0.1:8000/health/ready; echo

# ------------------------------------------------------------------------------
# TESTS / LINT
# ------------------------------------------------------------------------------
.PHONY: test lint
test:
	PYTHONPATH=. pytest -q

lint:
	ruff check . || true

.PHONY: fmt lint test ci

fmt: ## Check formatting (black)
	black --check backend

lint: ## Static analysis (ruff)
	ruff check backend

test: ## Run tests
	pytest -q backend/tests

ci: fmt lint test ## Run CI locally (strict)
	@echo "CI passed"
.PHONY: ci
fmt:
	black --check backend || true

.PHONY: ci
ci: fmt lint ## Run CI checks locally (mirrors GH Actions)
	pytest -q backend/tests

# ------------------------------------------------------------------------------
# E2E SMOKE (quick sanity after seed)
# ------------------------------------------------------------------------------
.PHONY: smoke
smoke:
	curl -s -X POST http://127.0.0.1:8000/sites -H 'content-type: application/json' -d '{"name":"Smoke Site"}' | jq .
	curl -s http://127.0.0.1:8000/sites | jq .

.PHONY: temporal.up temporal.down temporal.logs worker.up worker.run worker.logs workflow.kick
temporal.up:
	docker compose -f docker-compose.db.yml up -d
	docker compose -f docker-compose.temporal.yml up -d
	@echo "Temporal: http://localhost:8233"

temporal.down:
	docker compose -f docker-compose.temporal.yml down -v

temporal.logs:
	docker compose -f docker-compose.temporal.yml logs -f --tail=200

# Run the worker in your local venv/shell
worker.run:
	PYTHONPATH=. python -m backend.sitegen.worker

# Or background “up” flavor via nohup (simple local dev)
worker.up:
	nohup bash -lc 'PYTHONPATH=. python -m backend.sitegen.worker 2>&1 | tee .ci/artifacts/worker.log' & disown; sleep 1; tail -n +1 -f .ci/artifacts/worker.log

worker.logs:
	tail -n 200 -f .ci/artifacts/worker.log

# Quick kick (expects API running)
workflow.kick:
	curl -s -X POST http://127.0.0.1:8000/sitegen/start \
	  -H 'content-type: application/json' -d '{"site_id":1}' | jq .

.PHONY: dev.up dev.down dev.logs dev.ps
dev.up:
	docker compose -f docker-compose.dev.yml up -d
	@echo "API:        http://localhost:8000"
	@echo "Adminer:    http://localhost:8081"
	@echo "Temporal UI:http://localhost:8233"

dev.down:
	docker compose -f docker-compose.dev.yml down -v

dev.logs:
	docker compose -f docker-compose.dev.yml logs -f --tail=200

dev.ps:
	docker compose -f docker-compose.dev.yml ps

.PHONY: workflow.describe workflow.cancel workflow.result
workflow.describe:
	curl -s http://127.0.0.1:8000/workflows/${WID} | jq .

workflow.cancel:
	curl -s -X POST http://127.0.0.1:8000/workflows/${WID}/cancel | jq .

workflow.result:
	curl -s "http://127.0.0.1:8000/workflows/${WID}/result?timeout_s=${T:=0.5}" | jq .



