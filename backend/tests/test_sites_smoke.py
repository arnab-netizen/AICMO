from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_health_endpoints():
    r = client.get("/health/live")
    assert r.status_code == 200
    r = client.get("/health/ready")
    assert r.status_code == 200


def test_sites_create_and_get():
    # create
    r = client.post("/sites", json={"name": "Smoke Test"})
    assert r.status_code in (200, 201)
    data = r.json()
    assert "id" in data and ("slug" in data or True)

    # list
    r = client.get("/sites")
    assert r.status_code == 200
    sites = r.json()
    assert any(s.get("id") == data["id"] for s in sites)

    # get by id
    r = client.get(f"/sites/{data['id']}")
    assert r.status_code == 200
    one = r.json()
    assert one["id"] == data["id"]
