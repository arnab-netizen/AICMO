# AICMO
Marketing agent

## 🔐 Admin Token Security Guard

The `/workflows/*` endpoints are protected by an **optional header-based guard**.

| Mode | Env Variable | Behavior |
|------|---------------|-----------|
| Default | (unset) | Guard disabled → all requests allowed |
| Secure Mode | `ADMIN_TOKEN` set | Requests must include matching `x-admin-token` header |

**Example Usage**

```bash
# Guard OFF (default)
unset ADMIN_TOKEN
curl http://127.0.0.1:8000/workflows/health

# Guard ON
export ADMIN_TOKEN="token-123"

# Wrong/missing token → 401
curl -i http://127.0.0.1:8000/workflows/health

# Correct token → 200
curl -i -H "x-admin-token: token-123" http://127.0.0.1:8000/workflows/health
```


The guard logic lives in `backend/security.py`
and is applied automatically via `Depends(require_admin)` in `backend/routers/workflows.py`.

⚙️ Local CI Dry-Run

Run all backend tests locally exactly as in GitHub Actions:

```
make ci


or explicitly:

export PYTHONPATH=$PWD
pytest -q backend/tests
```

## Dev setup

Quick steps for getting a local dev environment ready:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt  # includes -e ./capsule-core
pytest -q
```
