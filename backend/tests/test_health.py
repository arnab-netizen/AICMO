from fastapi.testclient import TestClient
from backend.main import app


def test_health_ok():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json().get("ok") is True
