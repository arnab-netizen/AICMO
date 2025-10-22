from fastapi.testclient import TestClient


def test_healthz(client: TestClient):
    r = client.get("/sitegen/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_run_sets_tier_header(client: TestClient):
    r = client.post("/sitegen/run", json={"project_id": "p", "payload": {}})
    assert r.status_code == 200
    assert r.headers.get("X-Tier") in {"free", "pro"}
