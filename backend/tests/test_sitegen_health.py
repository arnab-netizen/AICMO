from fastapi.testclient import TestClient
from backend.app import app


def test_healthz():
    c = TestClient(app)
    r = c.get("/sitegen/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_run_sets_tier_header():
    c = TestClient(app)
    r = c.post("/sitegen/run", json={"project_id": "p", "payload": {}})
    assert r.status_code == 200
    assert r.headers.get("X-Tier") in {"free", "pro"}
