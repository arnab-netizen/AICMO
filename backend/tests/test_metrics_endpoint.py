import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app


@pytest.mark.asyncio
async def test_metrics_exposes_taste_series_names():
    # Using the in-process ASGI transport; no server needed.
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/metrics/")
        assert r.status_code == 200
        text = r.text
        # Just verify that the metric names are registered/exposed.
        assert "taste_compare_requests_total" in text
        assert "taste_compare_success_total" in text
        assert "taste_compare_seconds" in text
