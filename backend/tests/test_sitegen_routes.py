from fastapi.testclient import TestClient


def test_draft_minimal(client: TestClient):
    r = client.post("/sitegen/draft", json={"name": "founder-os"})
    assert r.status_code == 200
    data = r.json()
    assert data["site"]["name"] == "founder-os"
    assert data["pages"][0]["slug"] == "home"
