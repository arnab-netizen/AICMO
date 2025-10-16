def write_page_copy(page: dict, brand: dict) -> dict:
    return {**page, "copy": {"h1": brand.get("tagline", "Welcome"), "body": "Coming soon."}}
