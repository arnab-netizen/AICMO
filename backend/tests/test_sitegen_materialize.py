from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_materialize_minimal():
    spec = {"pages": [{"slug": "home"}, {"slug": "about"}]}
    r = client.post("/sitegen/materialize", json=spec)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["pages"] == ["home", "about"]
