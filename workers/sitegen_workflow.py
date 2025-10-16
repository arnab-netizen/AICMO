def run_sitegen(spec: dict) -> dict:
    return {"status": "planned", "pages": [p.get("slug") for p in spec.get("pages", [])]}
