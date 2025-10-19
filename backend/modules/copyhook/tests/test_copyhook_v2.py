import pytest
from httpx import AsyncClient
from backend.app import app


@pytest.mark.asyncio
async def test_copyhook_happy(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as c:
        payload = {
            "project_id": "11111111-1111-1111-1111-111111111111",
            "goal": "landing hero for fintech B2B",
            "constraints": {"tone": "confident, simple", "brand": "Acme", "must_avoid": []},
        }
        r = await c.post("/api/copyhook/run", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "finished"
        arts = body.get("artifacts", [])
        assert len(arts) >= 1
        meta = arts[0].get("meta", {})
        assert len(meta.get("variants", [])) >= 4
        assert meta.get("seed") is not None
        # platform coverage
        assert any(po["google"] and po["linkedin"] for po in meta["platform_ok"])


@pytest.mark.asyncio
async def test_copyhook_banned(monkeypatch):
    async with AsyncClient(app=app, base_url="http://test") as c:
        payload = {
            "project_id": "11111111-1111-1111-1111-111111111111",
            "goal": "landing hero",
            "constraints": {"brand": "Acme", "must_avoid": ["free forever"]},
        }
        r = await c.post("/api/copyhook/run", json=payload)
        assert r.status_code in (200, 422)
        if r.status_code == 422:
            body = r.json()
            assert body["detail"]["reason"] == "banned_terms"
