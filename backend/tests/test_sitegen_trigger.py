from fastapi.testclient import TestClient


def test_sitegen_endpoint_exists(client: TestClient):
    # Use /sitegen/run which is the current endpoint for starting jobs.
    r = client.post("/sitegen/run", json={"project_id": "p", "payload": {}})
    # The endpoint may respond 200/202 in normal operation and 500 if external services
    # (Temporal, etc.) are unavailable in CI; accept any of these as evidence the route exists.
    assert r.status_code in (200, 202, 500)
