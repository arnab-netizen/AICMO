from __future__ import annotations
from typing import Dict, List

_DB: Dict[str, Dict[str, dict]] = {"sites": {}, "pages": {}}


def upsert_site(slug: str, name: str) -> dict:
    _DB["sites"][slug] = {"slug": slug, "name": name}
    return _DB["sites"][slug]


def upsert_page(site_slug: str, slug: str, data: dict) -> dict:
    key = f"{site_slug}:{slug}"
    _DB["pages"][key] = {"site": site_slug, "slug": slug, "data": data}
    return _DB["pages"][key]


def list_pages(site_slug: str) -> List[dict]:
    return [p for p in _DB["pages"].values() if p["site"] == site_slug]
