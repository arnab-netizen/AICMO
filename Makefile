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

.PHONY: core-dev core-test
core-dev: ; pip install -e ./capsule-core
core-test: ; pytest -q capsule-core/tests

seed:
	docker exec -i pg psql -U appuser -d appdb < backend/sql/seed_demo.sql
