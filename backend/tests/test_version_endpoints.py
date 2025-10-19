import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app


@pytest.mark.asyncio
async def test_all_version_endpoints_return_200_and_fields():
    version_routes = []
    for route in app.routes:
        path = getattr(route, "path", "")
        methods = getattr(route, "methods", set())
        if isinstance(path, str) and path.endswith("/version") and ("GET" in methods):
            version_routes.append(path)

    assert version_routes, "No /version endpoints discovered; ensure module routers are mounted."

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for p in version_routes:
            r = await client.get(p)
            assert r.status_code == 200, f"{p} returned {r.status_code}"
            data = r.json()
            assert any(
                k in data for k in ("version", "git", "build")
            ), f"{p} missing version-ish field"
            assert any(
                k in data for k in ("name", "module", "service")
            ), f"{p} missing name-ish field"
