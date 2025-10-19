from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from backend.db import get_session

router = APIRouter(prefix="/sites", tags=["sites"])

SITE_SPEC_SQL = text(
    """
SELECT to_jsonb(sp) AS spec
FROM site_spec sp
WHERE slug = :slug
"""
)


@router.get("/{slug}/spec")
def get_site_spec(slug: str):
    with get_session() as s:
        row = s.execute(SITE_SPEC_SQL, {"slug": slug}).fetchone()
        if not row or not row.spec:
            raise HTTPException(status_code=404, detail="Site not found")
        return row.spec
