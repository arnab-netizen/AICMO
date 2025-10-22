PY?=python3
PORT?=8000
DB?=$(DATABASE_URL)

.PHONY: setup migrate run smoke test metrics
.PHONY: dev-install smoke smoke-dev test test-full migrate migrate-online alembic-sql50 alembic-sql-ts drift-sql alembic-heads
.PHONY: fmt lint type unit-subset dev-install

setup:
	$(PY) -m venv .venv && . .venv/bin/activate && pip install -r backend/requirements.txt

dev-install:
	python -m pip install --upgrade pip
	pip install -r backend/requirements.txt
	if [ -f backend/requirements-dev.txt ]; then pip install -r backend/requirements-dev.txt; fi

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
	pytest -q

test-full:
	pytest --maxfail=1 -q

metrics:
	curl -s http://localhost:$(PORT)/metrics | grep -E "capsule_runs_total|capsule_runtime_seconds" -n || true
.PHONY: minimal-test full-test test api run-minimal

api:
	uvicorn backend.app:app --reload --port 8080

minimal-test:
	PYTHONPATH=. pytest -q backend/minimal_tests

unit-subset:
	PYTHONPATH=. pytest -q \
		backend/tests/test_health_endpoints.py \
		backend/tests/test_db_sqlite.py \
		backend/tests/test_models_asset.py \
		backend/tests/test_taste_service_unit.py \
		backend/tests/test_db_exec_sql_helper.py \
		backend/tests/test_health_db_errors.py \
		backend/tests/test_taste_service_extra.py

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

.PHONY: ui api dev
ui:
	. .venv/bin/activate >/dev/null 2>&1 || python -m venv .venv && . .venv/bin/activate && pip install streamlit httpx
	API_BASE?=http://localhost:8000 streamlit run streamlit_app.py

api:
	uvicorn backend.app:app --port 8000 --reload

dev:   ## run DB reset + API + a hint for UI
	@echo "Resetting DB and starting API…"
	$(MAKE) db-reset
	uvicorn backend.app:app --port 8000 --reload

.PHONY: core-dev core-test
core-dev: ; pip install -e ./capsule-core
core-test: ; pytest -q capsule-core/tests

.PHONY: dev-install-smoke smoke-dev
dev-install-smoke:
	python -m pip install --upgrade pip
	pip install -r backend/requirements.txt
	pip install -e ./capsule-core

smoke-dev:
	SITEGEN_ENABLED=0 python -m backend.tools.smoke_versions

seed:
	docker exec -i pg psql -U appuser -d appdb < backend/sql/seed_demo.sql

.PHONY: db-up db-down db-migrate db-seed smoke-versions smoke-telemetry test-versions test-taste

db-up:
	docker run -d --rm --name aicmo-pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 ankane/pgvector:latest

db-down:
	docker stop aicmo-pg || true

.PHONY: db-reset test-pg
db-reset:
	@echo "Dropping and recreating public schema on DB"
	@psql "$(DB)" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || true

test-pg:
	@echo "Applying alembic migrations against $(DB) and running pytest"
	@alembic -c backend/alembic.ini heads | awk 'END{if(NR!=1){print "Multiple Alembic heads!"; exit 1}}'
	@alembic -c backend/alembic.ini upgrade head
	@PYTHONPATH=. pytest -q

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

.PHONY: ci
ci: db-reset
	@alembic -c backend/alembic.ini heads | awk 'END{ if (NR!=1) { print "Multiple Alembic heads!"; exit 1 } }'
	@PSQL_URL=$$(python -c "import os,re,sys;u=os.environ.get('DATABASE_URL',''); sys.stdout.write(re.sub(r'^(postgresql)(?:\\+[^:]+)?://','postgresql://',u))"); \
	psql "$$PSQL_URL" -Atc "SELECT 1 FROM pg_indexes WHERE tablename='site' AND indexname='ux_site_slug';" | grep 1 >/dev/null; \
	psql "$$PSQL_URL" -Atc "SELECT indexdef FROM pg_indexes WHERE tablename='page' AND indexdef LIKE '%UNIQUE% (site_id, path)%';" | grep UNIQUE >/dev/null; \
	psql "$$PSQL_URL" -Atc "SELECT table_name FROM information_schema.views WHERE table_schema='public' AND table_name='site_spec';" | grep site_spec >/dev/null; \
	@pytest -q

test-versions:
	pytest -q backend/tests/test_version_endpoints.py

test-taste:
	pytest -q backend/tests/test_taste_endpoints_integration.py

# --- DB migrations (Alembic) ---
.PHONY: migrate migrate-down

# Use ALEMBIC_CONFIG if set, else default to backend/alembic.ini
migrate:
	@mkdir -p .alembic_sql
	@ALEMBIC_CONFIG=backend/alembic.ini ALEMBIC_OFFLINE=1 alembic upgrade head --sql > .alembic_sql/preview.sql ; echo "Preview at .alembic_sql/preview.sql"

migrate-online:
	ALEMBIC_CONFIG=backend/alembic.ini alembic upgrade head

migrate-down:
	@[ -n "$$DB_URL" ] || (echo "Set DB_URL before running migrations"; exit 1)
	@alembic -c "$${ALEMBIC_CONFIG:-backend/alembic.ini}" downgrade -1

# Convenience targets for Alembic offline/online
.PHONY: alembic-sql alembic-up drift-sql
alembic-sql:
	ALEMBIC_CONFIG=backend/alembic.ini alembic -c backend/alembic.ini upgrade head --sql | head -n 50

alembic-up:
	python -m pip install -r backend/requirements.txt
	ALEMBIC_CONFIG=backend/alembic.ini alembic -c backend/alembic.ini upgrade head

alembic-sql50:
	ALEMBIC_CONFIG=backend/alembic.ini alembic -c backend/alembic.ini upgrade head --sql | head -n 50

alembic-heads:
	ALEMBIC_CONFIG=backend/alembic.ini alembic heads

alembic-sql-ts:
	@mkdir -p .alembic_sql
	@ts="$$(date -u +'%Y%m%dT%H%M%SZ')"; \
	out=".alembic_sql/upgrade_head_$${ts}.sql"; \
	ALEMBIC_CONFIG=backend/alembic.ini alembic -c backend/alembic.ini upgrade head --sql > "$$out"; \
	echo "Rendered $$out"


.PHONY: drift-sql
drift-sql:
	@mkdir -p .alembic_sql/drift
	@ts="$$(date -u +'%Y%m%dT%H%M%SZ')"; \
	out=".alembic_sql/drift/autogen_$${ts}.sql"; \
	ALEMBIC_CONFIG=backend/alembic.ini ALEMBIC_OFFLINE=1 alembic revision --autogenerate --sql > "$$out"; \
	echo "Wrote $$out"


# Inventory helpers


ifeq ($(origin SEEN_EXT_TARGETS), undefined)
SEEN_EXT_TARGETS=1

.PHONY: inventory ext-scan env-example smoke

inventory:
	python scripts/inventory_external_connections.py

ext-scan:
	@if command -v rg >/dev/null; then \
	  rg -n --no-heading -S -e 'asyncpg|psycopg|sqlalchemy|pgvector|boto3|minio|aiobotocore|redis|rq|celery|pika|kafka|confluent|temporalio|openai|anthropic|vertexai|groq|together|cohere|httpx|requests|stripe|razorpay|paypal|sendgrid|smtp|smtplib|twilio|segment|posthog|mixpanel|sentry|opentelemetry' backend frontend **/*.y?(a)ml || true; \
	  rg -n --no-heading -S -e 'os\\.environ\\[|os\\.getenv\\(|process\\.env\\.' backend frontend || true; \
	else \
	  echo 'ripgrep not found, using git grep fallback'; \
	  git grep -n -E "asyncpg|psycopg|sqlalchemy|pgvector|boto3|minio|aiobotocore|redis|rq|celery|pika|kafka|confluent|temporalio|openai|anthropic|vertexai|groq|together|cohere|httpx|requests|stripe|razorpay|paypal|sendgrid|smtp|smtplib|twilio|segment|posthog|mixpanel|sentry|opentelemetry" -- backend frontend ':/**/*.yml' ':/**/*.yaml' || true; \
	  git grep -n -E "os\\.environ\\[|os\\.getenv\\(|process\\.env\\." -- backend frontend || true; \
	fi

env-example: inventory
	@echo ".env.example regenerated."

smoke:
	./scripts/smoke_local_services.sh
endif
