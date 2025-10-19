import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app


@pytest.mark.asyncio
async def test_health_root_ok():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health")
        assert r.status_code == 200
        assert r.json().get("ok") is True


@pytest.mark.asyncio
async def test_health_db_handles_error(monkeypatch):
    # Make get_engine().begin() explode to simulate DB down
    from backend.db import get_engine

    class Boom:
        def __enter__(self):
            raise RuntimeError("db down")

        def __exit__(self, *a):
            return False

    eng = get_engine()
    monkeypatch.setattr(eng, "begin", lambda: Boom())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/health/db")
        assert r.status_code in (500, 503)
