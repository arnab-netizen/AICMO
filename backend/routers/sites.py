from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import text, select
from sqlalchemy.orm import Session
from backend.db import get_session
from backend.models import Site
from sqlalchemy.exc import IntegrityError
from typing import List
from fastapi import Path
from pydantic import BaseModel as PydanticBaseModel
from backend.db import get_engine

router = APIRouter(prefix="/sites", tags=["sites"])

SITE_SPEC_SQL = text(
    """
SELECT to_jsonb(sp) AS spec
FROM site_spec sp
WHERE slug = :slug
"""
)


class SiteIn(BaseModel):
    name: str


class SiteOut(BaseModel):
    id: int
    name: str
    slug: str

    class Config:
        from_attributes = True


class PageOut(PydanticBaseModel):
    id: int
    site_id: int
    path: str
    title: str | None = None
    body: str | None = None


def get_db():
    with get_session() as s:
        yield s


@router.get("", response_model=list[SiteOut])
def list_sites(db: Session = Depends(get_db)):
    rows = db.execute(select(Site).order_by(Site.id.desc())).scalars().all()
    return rows


@router.post("", response_model=SiteOut, status_code=201)
def create_site(payload: SiteIn, db: Session = Depends(get_db)):
    # compute a slug similar to DB regexp_replace used elsewhere
    import re

    slug = re.sub(r"[^a-zA-Z0-9]+", "-", payload.name).strip("-").lower()
    obj = Site(name=payload.name, slug=slug)
    db.add(obj)
    try:
        db.flush()
        db.refresh(obj)
        return obj
    except IntegrityError:
        # slug already exists: return existing row
        db.rollback()
        existing = db.execute(select(Site).where(Site.slug == slug)).scalars().first()
        if existing:
            return existing
        raise


@router.get("/{site_id}", response_model=SiteOut)
def get_site_by_id(site_id: int, db: Session = Depends(get_db)):
    row = db.execute(select(Site).where(Site.id == site_id)).scalars().first()
    if not row:
        raise HTTPException(status_code=404, detail="Site not found")
    return row


@router.get("/{slug}/spec")
def get_site_spec(slug: str):
    with get_session() as s:
        row = s.execute(SITE_SPEC_SQL, {"slug": slug}).fetchone()
        if not row or not row.spec:
            raise HTTPException(status_code=404, detail="Site not found")
        return row.spec


@router.get("/{site_id}/pages", response_model=List[PageOut])
def list_site_pages(site_id: int = Path(...)):
    engine = get_engine()
    with engine.begin() as conn:
        rows = (
            conn.execute(
                text(
                    """
            SELECT id, site_id, path, title, body
            FROM page
            WHERE site_id = :sid
            ORDER BY path ASC
        """
                ),
                {"sid": site_id},
            )
            .mappings()
            .all()
        )
        return [dict(r) for r in rows]
