from fastapi.testclient import TestClient


def test_materialize_minimal(client: TestClient):
    spec = {"pages": [{"slug": "home"}, {"slug": "about"}]}
    r = client.post("/sitegen/materialize", json=spec)
    assert r.status_code == 200
    data = r.json()
    assert data["ok"] is True
    assert data["pages"] == ["home", "about"]
