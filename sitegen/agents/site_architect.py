def draft_site_spec(brief: dict) -> dict:
    return {"site": {"name": brief.get("name", "demo")}, "pages": [{"slug": "home"}]}
