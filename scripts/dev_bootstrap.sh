#!/usr/bin/env bash
set -euo pipefail

# --- Config (EDIT THESE 3 or export before running) ---
: "${DATABASE_URL:=postgresql+asyncpg://USER:PASS@HOST:5432/DB}"
PY_VER="${PY_VER:-3.11}"

echo "==> Using DATABASE_URL=$DATABASE_URL"
echo "==> Python $PY_VER"

# 1) venv + deps
echo "==> Creating venv and installing backend deps"
python$PY_VER -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r backend/requirements.txt

echo "==> Verifying critical deps"
python - <<'PY'
import fastapi, httpx, pytest, PIL, sqlalchemy, asyncpg
print("deps ok")
PY

# 2) Migrations
echo "==> Applying pgcrypto + migrations"
psql "$DATABASE_URL" -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;"
psql "$DATABASE_URL" -f backend/migrations/0001_capsule_shared.sql || true
psql "$DATABASE_URL" -f backend/migrations/0002_copyhook.sql || true
psql "$DATABASE_URL" -f backend/migrations/0003_shared_extras.sql
psql "$DATABASE_URL" -f backend/migrations/0004_visualgen_policy.sql

# 3) Smoke run (background)
echo "==> Starting app (background)"
(uvicorn backend.app:app --port 8000 --reload >/tmp/aicmo_uvicorn.log 2>&1) &
UV_PID=$!
sleep 2

# 4) Health
echo "==> Health check"
curl -sf http://localhost:8000/health && echo

# 5) Smoke both modules
echo "==> CopyHook smoke"
curl -s http://localhost:8000/api/copyhook/run \
  -H 'content-type: application/json' \
  -d '{"project_id":"11111111-1111-1111-1111-111111111111","goal":"landing hero","constraints":{"brand":"Acme","tone":"confident, simple","must_avoid":[]}}' | jq .

echo "==> VisualGen smoke"
curl -s http://localhost:8000/api/visualgen/run \
  -H 'content-type: application/json' \
  -d '{"project_id":"22222222-2222-2222-2222-222222222222","goal":"3 creatives","constraints":{"brand":"Acme","size":"1200x628","count":3}}' | jq .

# 6) Tests
echo "==> Running tests"
PYTHONPATH=. pytest -q backend/modules/copyhook/tests \
                     backend/modules/visualgen/tests \
                     backend/tools/tests

# 7) Metrics sanity
echo "==> Metrics snippet"
curl -s http://localhost:8000/metrics | grep -E "capsule_runs_total|capsule_runtime_seconds" -n || true

echo "==> Done. Uvicorn logs: /tmp/aicmo_uvicorn.log  PID:$UV_PID"
