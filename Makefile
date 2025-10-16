.PHONY: api seed spec test

api:
	uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000

spec:
	curl -s http://localhost:8000/sites/founder-os/spec | jq .

test:
	pytest -q

seed:
	docker exec -i pg psql -U appuser -d appdb < backend/sql/seed_demo.sql
