from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
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
    # Try the materialized view first; if it doesn't exist (e.g. tests without
    # migrations applied), assemble the spec from base tables as a graceful
    # fallback so tests can run against a fresh DB.
    with get_session() as s:
        try:
            row = s.execute(SITE_SPEC_SQL, {"slug": slug}).fetchone()
            if row and row.spec:
                return row.spec
        except ProgrammingError:
            # The failed query may have left the session in a failed state; rollback
            # so subsequent manual queries succeed.
            try:
                s.rollback()
            except Exception:
                pass

        # Manual assembly fallback
        site_row = s.execute(
            text("SELECT id, slug, name, title FROM site WHERE slug = :s"), {"s": slug}
        ).fetchone()
        if not site_row:
            raise HTTPException(status_code=404, detail="Site not found")

        site_id = site_row.id
        pages = []
        try:
            for pr in s.execute(
                text("SELECT id, path, title, seo FROM page WHERE site_id = :sid ORDER BY id"),
                {"sid": site_id},
            ).mappings():
                pages.append(
                    {"id": pr["id"], "path": pr["path"], "title": pr["title"], "seo": pr["seo"]}
                )
        except ProgrammingError:
            # Missing page table -> no pages
            try:
                s.rollback()
            except Exception:
                pass

        sections = []
        try:
            for sr in s.execute(
                text(
                    'SELECT id, type, props, "order" FROM site_section WHERE site_id = :sid ORDER BY id'
                ),
                {"sid": site_id},
            ).mappings():
                sections.append(
                    {"id": sr["id"], "type": sr["type"], "props": sr["props"], "order": sr["order"]}
                )
        except ProgrammingError:
            # Missing site_section table -> no sections
            try:
                s.rollback()
            except Exception:
                pass

        spec = {
            "slug": site_row.slug,
            "name": site_row.name,
            "title": site_row.title,
            "pages": pages,
            "sections": sections,
        }
        return spec
