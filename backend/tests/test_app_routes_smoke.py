"""Smoke tests to ensure all FastAPI routes don't crash on basic requests."""

from fastapi.routing import APIRoute
from starlette.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_all_routes_do_not_500_on_options():
    """
    For every FastAPI route, send an OPTIONS request and ensure
    we don't get a 5xx error. OPTIONS is safe (no side effects)
    but still exercises routing/middleware.
    """
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue

        # Skip docs/openapi routes
        if any(
            route.path.startswith(prefix)
            for prefix in ["/docs", "/redoc", "/openapi", "/openapi.json"]
        ):
            continue

        resp = client.request("OPTIONS", route.path)
        assert (
            resp.status_code < 500
        ), f"Route {route.path} with methods {route.methods} returned {resp.status_code}"


def test_health_endpoint_returns_200():
    """Verify main health endpoint returns 200."""
    resp = client.get("/health")
    assert resp.status_code == 200


def test_root_endpoint_accessible():
    """Verify root endpoint is accessible (often returns redirect or docs)."""
    resp = client.get("/")
    # Root might be 200, 404, 307, etc. depending on FastAPI setup
    # We just want to ensure it doesn't 500
    assert resp.status_code < 500


def test_openapi_schema_accessible():
    """Verify OpenAPI schema is accessible."""
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "openapi" in data
    assert "paths" in data
