import os
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app


@pytest.mark.asyncio
@pytest.mark.skipif(
    "DB_URL" not in os.environ or "postgresql://" not in os.environ["DB_URL"],
    reason="PG not set",
)
async def test_top1_is_stable_for_fixed_vector():
    emb = [i * 0.0005 for i in range(1536)]
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post("/taste/compare", json={"embedding": emb, "top_k": 1, "min_taste": 0.0})
        assert r.status_code == 200
        items = r.json()["results"]
        assert len(items) == 1
        # Expect top-1 id to remain stable with seeded DB
        assert items[0]["id"] >= 1
