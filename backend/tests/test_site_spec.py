from fastapi.testclient import TestClient
from backend.app import app
from sqlalchemy import text
from backend.db import get_session

client = TestClient(app)


def ensure_seed():
    with get_session() as s:
        slug = "founder-os"
        exists = s.execute(text("select 1 from site where slug=:slug"), {"slug": slug}).fetchone()
        if not exists:
            sid = s.execute(
                text(
                    """
                INSERT INTO site(slug,title) VALUES(:slug,'Founder-OS') RETURNING id
            """
                ),
                {"slug": slug},
            ).scalar_one()
            s.execute(
                text(
                    """
                INSERT INTO page(site_id,path,title,seo)
                VALUES(:sid,'/','Home','{"title":"Founder-OS"}')
                ON CONFLICT (site_id,path) DO NOTHING
            """
                ),
                {"sid": sid},
            )
            s.execute(
                text(
                    """
                INSERT INTO site_section(site_id,"type",props,"order")
                VALUES(:sid,'hero','{"headline":"Ship faster"}',1)
            """
                ),
                {"sid": sid},
            )
            s.commit()


def test_get_site_spec_ok():
    ensure_seed()
    r = client.get("/sites/founder-os/spec")
    assert r.status_code == 200
    data = r.json()
    assert data["slug"] == "founder-os"
    assert isinstance(data["pages"], list)
    assert any(sec["type"] == "hero" for sec in data["sections"])
