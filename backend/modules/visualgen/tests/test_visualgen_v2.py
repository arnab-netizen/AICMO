import pytest
import base64
from httpx import AsyncClient
from backend.app import app


def tiny_png_b64():
    # 1x1 PNG
    raw = base64.b64encode(
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc`\x00\x00"
        b"\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    ).decode("ascii")
    return raw


@pytest.mark.asyncio
async def test_visualgen_logo_and_refs_ok():
    async with AsyncClient(app=app, base_url="http://test") as c:
        payload = {
            "project_id": "22222222-2222-2222-2222-222222222222",
            "goal": "3 creative variants",
            "constraints": {
                "brand": "Acme",
                "size": "1200x628",
                "count": 3,
                "logo": {"mime": "image/png", "base64": tiny_png_b64()},
                "brand_primary": "#0ea5e9",
            },
            "sources": [
                {
                    "type": "image_base64",
                    "mime": "image/png",
                    "base64": tiny_png_b64(),
                    "role": "reference",
                }
            ],
        }
        r = await c.post("/api/visualgen/run", json=payload)
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "finished"
        arts = body.get("artifacts", [])
        assert len(arts) == 3
        for a in arts:
            assert a["type"] == "image"
            assert "base64" in a
            assert a["meta"]["size"] == "1200x628"
            assert a["meta"]["brand_applied"]["logo"] is True
            assert a["meta"]["contrast"] >= 4.5
