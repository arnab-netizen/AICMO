from fastapi import APIRouter

router = APIRouter(prefix="/sitegen", tags=["sitegen"])


@router.post("/draft")
def draft(brief: dict):  # type: ignore
    from sitegen.agents.site_architect import draft_site_spec

    return draft_site_spec(brief)


@router.post("/materialize")
def materialize(spec: dict):  # type: ignore
    """
    Input: site-spec JSON.
    Output: basic build plan (pages, assets) without writing disk yet.
    """
    pages = [p.get("slug", "home") for p in spec.get("pages", [{"slug": "home"}])]
    return {"ok": True, "pages": pages}
