from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from backend.db import get_session

router = APIRouter()


@router.post("/sites")
def create_site(payload: dict):
    name = payload.get("name") if isinstance(payload, dict) else None
    with get_session() as s:
        row = s.execute(
            text("INSERT INTO site (name, slug, title) VALUES (:n, :slug, :t) RETURNING id"),
            {"n": name or "", "slug": (name or "").lower().replace(" ", "-"), "t": name or ""},
        ).fetchone()
        # Ensure the transaction is committed so other sessions (GET /sites) can see it.
        try:
            s.commit()
        except Exception:
            # If commit fails, let the exception propagate; tests will surface the problem.
            raise
        return {"id": row[0], "slug": (name or "").lower().replace(" ", "-")}


@router.get("/sites")
def list_sites():
    with get_session() as s:
        rows = s.execute(text("SELECT id, slug, name FROM site ORDER BY id")).fetchall()
        return [{"id": r[0], "slug": r[1], "name": r[2]} for r in rows]


@router.get("/sites/{site_id}")
def get_site(site_id: int):
    with get_session() as s:
        row = s.execute(
            text("SELECT id, slug, name FROM site WHERE id = :id"), {"id": site_id}
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Not found")
        return {"id": row[0], "slug": row[1], "name": row[2]}
