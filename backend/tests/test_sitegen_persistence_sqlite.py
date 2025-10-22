from importlib import reload


def test_sitegen_persists_with_sqlite(monkeypatch, client):
    # Use DB store with in-memory SQLite
    monkeypatch.setenv("SITEGEN_STORE", "db")
    monkeypatch.setenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")
    # No API key to keep calls simple in this test
    monkeypatch.delenv("SITEGEN_API_KEY", raising=False)

    import backend.modules.sitegen.routes as routes

    reload(routes)  # pick up env

    r = client.post("/sitegen/run", json={"project_id": "p-sqlite", "payload": {"x": 1}})
    assert r.status_code == 200
    tid = r.json()["task_id"]

    st = client.get(f"/sitegen/status/{tid}")
    assert st.status_code == 200
    body = st.json()
    assert body["state"] == "DONE"
    assert body["result"]["ok"] is True

    # Optional: verify the route reports store=db
    mx = client.get("/sitegen/metrics")
    assert mx.json().get("store") == "db"
