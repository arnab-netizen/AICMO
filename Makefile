PY?=python3
PORT?=8000
DB?=$(DATABASE_URL)

.PHONY: setup migrate run smoke test metrics

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

migrate:
	psql "$(DB)" -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
	psql "$(DB)" -f backend/migrations/0001_capsule_shared.sql || true
	psql "$(DB)" -f backend/migrations/0002_copyhook.sql       || true
	psql "$(DB)" -f backend/migrations/0003_shared_extras.sql
	psql "$(DB)" -f backend/migrations/0004_visualgen_policy.sql

run:
	uvicorn backend.app:app --reload --port $(PORT)

smoke:
	curl -s http://localhost:$(PORT)/health
	curl -s http://localhost:$(PORT)/api/copyhook/run -H 'content-type: application/json' -d '{"project_id":"11111111-1111-1111-1111-111111111111","goal":"landing hero","constraints":{"brand":"Acme","tone":"confident, simple","must_avoid":[]}}' | jq .
	curl -s http://localhost:$(PORT)/api/visualgen/run -H 'content-type: application/json' -d '{"project_id":"22222222-2222-2222-2222-222222222222","goal":"3 creatives","constraints":{"brand":"Acme","size":"1200x628","count":3}}' | jq .

test:
	PYTHONPATH=. pytest -q backend/modules/copyhook/tests backend/modules/visualgen/tests backend/tools/tests

metrics:
	curl -s http://localhost:$(PORT)/metrics | grep -E "capsule_runs_total|capsule_runtime_seconds" -n || true
.PHONY: minimal-test full-test test api run-minimal

api:
	uvicorn backend.app:app --reload --port 8080

minimal-test:
	PYTHONPATH=. pytest -q backend/minimal_tests

.PHONY: up-temporal down-temporal e2e-test

up-temporal:
	docker compose -f docker/temporal-compose.yml up -d

down-temporal:
	docker compose -f docker/temporal-compose.yml down -v

e2e-test: up-temporal
	# Requires temporal stack running; admin-tools gate ensures readiness
	# TEMPORAL_ADDRESS defaults to 127.0.0.1:7233 for host-run workers/tests
	TEMPORAL_E2E=1 PYTHONPATH=. pytest -q backend/minimal_tests/test_temporal_smoke.py
	curl -s http://localhost:8000/sites/founder-os/spec | jq .

test:
	pytest -q

.PHONY: ui
ui:
	python -m venv .venv && . .venv/bin/activate && \
	pip install -r requirements-streamlit.txt && \
	streamlit run app.py

.PHONY: core-dev core-test
core-dev: ; pip install -e ./capsule-core
core-test: ; pytest -q capsule-core/tests

seed:
	docker exec -i pg psql -U appuser -d appdb < backend/sql/seed_demo.sql

.PHONY: db-up db-down db-migrate db-seed smoke-versions smoke-telemetry test-versions test-taste

db-up:
	docker run -d --rm --name aicmo-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector:latest

db-down:
	docker stop aicmo-pg || true

db-migrate:
	@if [ -z "$$DB_URL" ]; then echo "Set DB_URL first"; exit 1; fi; \
	psql "$$DB_URL" -c "CREATE EXTENSION IF NOT EXISTS vector;" && \
	psql "$$DB_URL" -f db/migrations/2025-10-19_add_taste_intelligence.sql

db-seed:
	@if [ -z "$$DB_URL" ]; then echo "Set DB_URL first"; exit 1; fi; \
	python -m backend.tools.seed_taste_demo

smoke-versions:
	python -m backend.tools.smoke_versions

smoke-telemetry:
	python -m backend.tools.smoke_telemetry

test-versions:
	pytest -q backend/tests/test_version_endpoints.py

test-taste:
	pytest -q backend/tests/test_taste_endpoints_integration.py

# --- DB migrations (Alembic) ---
.PHONY: migrate migrate-down

# Use ALEMBIC_CONFIG if set, else default to backend/alembic.ini
migrate:
	@[ -n "$$DB_URL" ] || (echo "Set DB_URL before running migrations"; exit 1)
	@echo "Ensuring pgvector extension..."
	@psql "$$DB_URL" -c "CREATE EXTENSION IF NOT EXISTS vector;" >/dev/null 2>&1 || true
	@echo "Running Alembic upgrade..."
	@alembic -c "$${ALEMBIC_CONFIG:-backend/alembic.ini}" upgrade head
	@echo "Migrations complete."

migrate-down:
	@[ -n "$$DB_URL" ] || (echo "Set DB_URL before running migrations"; exit 1)
	@alembic -c "$${ALEMBIC_CONFIG:-backend/alembic.ini}" downgrade -1
