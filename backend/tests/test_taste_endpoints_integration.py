import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app

requires_pg = pytest.mark.skipif(
    "DB_URL" not in os.environ or not os.environ["DB_URL"].startswith("postgresql"),
    reason="Postgres DB_URL not set",
)


@requires_pg
@pytest.mark.asyncio
async def test_taste_compare_returns_results():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        emb = [i * 0.001 for i in range(1536)]
        r = await c.post("/taste/compare", json={"embedding": emb, "top_k": 2, "min_taste": 0.0})
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data.get("items", []), list)


@requires_pg
@pytest.mark.asyncio
async def test_taste_record_upserts_without_error():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/taste/record",
            json={
                "asset_id": 1,
                "taste_score": 0.88,
                "emotion_score": 0.66,
                "tone": "minimal",
                "brand_alignment": 0.9,
            },
        )
        assert r.status_code == 200

    @pytest.mark.asyncio
    async def test_compare_rejects_wrong_dimension():
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            r = await c.post(
                "/taste/compare",
                json={"embedding": [0.1, 0.2], "top_k": 2, "min_taste": 0.0},
            )
            assert r.status_code == 422

        @pytest.mark.asyncio
        async def test_compare_rejects_bad_topk():
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
                r = await c.post(
                    "/taste/compare",
                    json={"embedding": [0.0] * 1536, "top_k": 0, "min_taste": 0.0},
                )
                assert r.status_code == 422
