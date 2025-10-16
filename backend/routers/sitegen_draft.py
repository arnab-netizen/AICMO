from fastapi import APIRouter

router = APIRouter(prefix="/sitegen", tags=["sitegen"])


@router.post("/draft")
def draft(brief: dict):  # type: ignore
    from sitegen.agents.site_architect import draft_site_spec

    return draft_site_spec(brief)
