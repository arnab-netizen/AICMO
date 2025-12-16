"""DEPRECATED_BACKEND_ENTRYPOINT

This file is an orphaned/duplicate FastAPI app from early development.

**Production deployment must use: backend/app.py**

Rationale:
- app/main.py appears to be a historical artifact or alternative implementation
- backend/app.py (120 lines) is the canonical production backend
- RUNBOOK_RENDER_STREAMLIT.md:25 specifies: uvicorn backend.app:app

If imported or run directly, raises RuntimeError to prevent accidental deployment.
"""

import sys

raise RuntimeError(
    "DEPRECATED_BACKEND_ENTRYPOINT: app/main.py is legacy code. "
    "Use 'backend.app:app' for Render deployment. "
    "See RUNBOOK_RENDER_STREAMLIT.md:25 for details."
)

sys.exit(1)


@app.get("/health/db")
async def health_db():
    ok = await db_healthcheck()
    return {"postgres_ok": ok}


# List all sites
@app.get("/sites")
async def list_sites(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Site))
    sites = result.scalars().all()
    return [{"id": s.id, "slug": s.slug, "name": s.name} for s in sites]


# Example endpoint for frontend integration
@app.get("/sitegen/spec")
async def sitegen_spec(path: str = "/", session: AsyncSession = Depends(get_session)):
    # Query SiteSection for the given path (site_id or slug can be used for more advanced logic)
    result = await session.execute(select(SiteSection).order_by(SiteSection.order))
    sections = result.scalars().all()
    # Convert DB rows to API format
    return {"sections": [{"type": s.type, "props": json.loads(s.props)} for s in sections]}


# Get site by ID
@app.get("/sites/{site_id}")
async def get_site(site_id: int, session: AsyncSession = Depends(get_session)):
    site = await session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return {"id": site.id, "slug": site.slug, "name": site.name}


# Update site
@app.put("/sites/{site_id}")
async def update_site(
    site_id: int, slug: str = None, name: str = None, session: AsyncSession = Depends(get_session)
):
    site = await session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    if slug:
        site.slug = slug
    if name:
        site.name = name
    await session.commit()
    return {"id": site.id, "slug": site.slug, "name": site.name}


# Delete site
@app.delete("/sites/{site_id}")
async def delete_site(site_id: int, session: AsyncSession = Depends(get_session)):
    site = await session.get(Site, site_id)
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await session.delete(site)
    await session.commit()
    return {"ok": True}
