from fastapi import APIRouter

router = APIRouter(prefix="/sitegen", tags=["sitegen"])


@router.post("/draft")
def draft(brief: dict):  # type: ignore
    from sitegen.agents.site_architect import draft_site_spec

    return draft_site_spec(brief)


@router.post("/materialize")
def materialize(spec: dict):  # type: ignore
    """
    Persist a minimal site-spec into an in-memory repo (for Phase 2 quick iteration).
    """
    from sitegen.builder.repo_memory import upsert_site, upsert_page, list_pages

    site = spec.get("site", {}) or {}
    pages = spec.get("pages", []) or [{"slug": "home"}]
    slug = site.get("slug") or (site.get("name", "demo").lower().replace(" ", "-"))

    upsert_site(slug=slug, name=site.get("name", slug))
    for p in pages:
        upsert_page(site_slug=slug, slug=p.get("slug", "home"), data=p)

    return {"ok": True, "site": slug, "pages": [p["slug"] for p in list_pages(slug)]}
