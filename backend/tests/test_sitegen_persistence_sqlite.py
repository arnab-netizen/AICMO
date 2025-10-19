from importlib import reload
from fastapi.testclient import TestClient


def test_sitegen_persists_with_sqlite(monkeypatch):
    # Use DB store with in-memory SQLite
    monkeypatch.setenv("SITEGEN_STORE", "db")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    # No API key to keep calls simple in this test
    monkeypatch.delenv("SITEGEN_API_KEY", raising=False)

    import backend.modules.sitegen.routes as routes

    reload(routes)  # pick up env
    from backend.app import app

    c = TestClient(app)
    r = c.post("/sitegen/run", json={"project_id": "p-sqlite", "payload": {"x": 1}})
    assert r.status_code == 200
    tid = r.json()["task_id"]

    st = c.get(f"/sitegen/status/{tid}")
    assert st.status_code == 200
    body = st.json()
    assert body["state"] == "DONE"
    assert body["result"]["ok"] is True

    # Optional: verify the route reports store=db
    mx = c.get("/sitegen/metrics")
    assert mx.json().get("store") == "db"
