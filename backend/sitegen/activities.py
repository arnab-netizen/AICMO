from __future__ import annotations
from typing import Any
from sqlalchemy import text
from backend.db import get_engine


async def ensure_home_page(site_id: int) -> dict[str, Any]:
    """
    Minimal 'generate' step: ensure a home page row exists.
    """
    engine = get_engine()
    with engine.begin() as conn:
        row = (
            conn.execute(
                text(
                    """
            INSERT INTO page (site_id, path, title, body)
            VALUES (:site_id, '/', 'Home', 'Hello from SiteGen!')
            ON CONFLICT (site_id, path) DO UPDATE SET title=excluded.title
            RETURNING id, site_id, path, title
        """
                ),
                {"site_id": site_id},
            )
            .mappings()
            .first()
        )
        return dict(row) if row else {}


async def record_deployment(site_id: int, status: str, message: str | None = None) -> int:
    engine = get_engine()
    with engine.begin() as conn:
        row = conn.execute(
            text(
                """
            INSERT INTO deployment (site_id, status, message)
            VALUES (:site_id, :status, :message)
            RETURNING id
        """
            ),
            {"site_id": site_id, "status": status, "message": message},
        ).scalar_one()
        return int(row)
