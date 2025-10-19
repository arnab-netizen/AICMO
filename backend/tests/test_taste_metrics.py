import os
import re
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app import app
from backend.tests.metrics_utils import get_counter


def _get_counter(text: str, name: str) -> int:
    # Parse Prometheus metric value which can be a float (e.g. '1.0').
    m = re.search(rf"^{re.escape(name)}\s+([0-9]+(?:\.[0-9]+)?)\s*$", text, re.M)
    if not m:
        return 0
    try:
        return int(float(m.group(1)))
    except Exception:
        return 0


requires_pg = pytest.mark.skipif(
    "DB_URL" not in os.environ or "postgresql://" not in os.environ.get("DB_URL", ""),
    reason="Postgres DATABASE_URL/DB_URL not set",
)


@pytest.mark.asyncio
@requires_pg
async def test_taste_compare_increments_metrics():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        before = (await c.get("/metrics/")).text

        payload = {"embedding": [0.0] * 1536, "top_k": 1, "min_taste": 0.0}
        r = await c.post("/taste/compare", json=payload)
        assert r.status_code == 200

        after = (await c.get("/metrics/")).text

    b_req = int(get_counter(before, "taste_compare_requests_total"))
    b_ok = int(get_counter(before, "taste_compare_success_total"))
    a_req = int(get_counter(after, "taste_compare_requests_total"))
    a_ok = int(get_counter(after, "taste_compare_success_total"))

    assert a_req >= b_req + 1
    assert a_ok >= b_ok + 1
