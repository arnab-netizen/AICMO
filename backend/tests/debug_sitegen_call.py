from fastapi.testclient import TestClient


def test_call(client: TestClient):
    r = client.post("/sitegen/materialize", json={"pages": [{"slug": "home"}]})
    print("status", r.status_code)
    print("text", r.text)
