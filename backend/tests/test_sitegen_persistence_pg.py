import os
import pytest
from importlib import reload


@pytest.mark.skipif(not os.getenv("DATABASE_URL"), reason="DATABASE_URL not set")
def test_sitegen_persists_with_postgres(monkeypatch, client):
    monkeypatch.setenv("SITEGEN_STORE", "db")
    monkeypatch.delenv("SITEGEN_API_KEY", raising=False)

    import backend.modules.sitegen.routes as routes

    reload(routes)

    r = client.post("/sitegen/run", json={"project_id": "p-pg", "payload": {"x": 1}})
    assert r.status_code == 200
    tid = r.json()["task_id"]

    st = client.get(f"/sitegen/status/{tid}")
    assert st.status_code == 200
    assert st.json()["state"] in ("RUNNING", "DONE")
