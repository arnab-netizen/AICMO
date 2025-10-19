from fastapi.testclient import TestClient
from backend.app import app


def test_run_requires_api_key_when_set(monkeypatch):
    monkeypatch.setenv("SITEGEN_API_KEY", "secret123")
    # re-import module settings to pick up env (isolation)
    from importlib import reload
    import backend.modules.sitegen.routes as routes

    reload(routes)

    client = TestClient(app)
    r = client.post("/sitegen/run", json={"project_id": "p", "payload": {}}, headers={})
    assert r.status_code == 401

    r2 = client.post(
        "/sitegen/run",
        json={"project_id": "p", "payload": {}},
        headers={"X-API-Key": "secret123"},
    )
    assert r2.status_code == 200


def test_run_works_without_key_if_unset(monkeypatch):
    monkeypatch.delenv("SITEGEN_API_KEY", raising=False)
    from importlib import reload
    import backend.modules.sitegen.routes as routes

    reload(routes)

    client = TestClient(app)
    r = client.post("/sitegen/run", json={"project_id": "p", "payload": {}})
    assert r.status_code == 200
