from __future__ import annotations

import os
import requests
from typing import Dict, List, Optional, Tuple

OSM_URL = "https://nominatim.openstreetmap.org/search"

GOOGLE_GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
GOOGLE_PLACES_TEXT_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
GOOGLE_PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"
GOOGLE_PLACES_PHOTO_URL = "https://maps.googleapis.com/maps/api/place/photo"


# -------------------------------------------------
# PUBLIC: main entrypoint for AICMO
# -------------------------------------------------


def find_competitors_for_brief(
    *,
    business_category: str,
    location: str,
    pincode: Optional[str] = None,
    limit: int = 10,
) -> List[Dict]:
    """
    High-level wrapper used by AICMO.

    1) If GOOGLE_MAPS_API_KEY is set -> use Google Places (rich data)
    2) Else -> use free OSM fallback (names + lat/lon only)
    """
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")

    if api_key:
        try:
            return find_competitors_google(
                category=business_category,
                location=location,
                pincode=pincode,
                api_key=api_key,
                limit=limit,
            )
        except Exception:
            # Fail soft and fall back to OSM
            pass

    # Fallback: OSM only
    query_str = f"{business_category} in {location}"
    if pincode:
        query_str += f" {pincode}"

    osm_results = find_competitors_osm(query=query_str, limit=limit)
    # Normalize to same shape
    normalized: List[Dict] = []
    for r in osm_results:
        normalized.append(
            {
                "name": r.get("name"),
                "address": r.get("raw", {}).get("display_name"),
                "website": None,
                "maps_url": None,
                "photo_url": None,
                "lat": r.get("lat"),
                "lon": r.get("lon"),
                "source": "osm",
                "place_id": None,
            }
        )
    return normalized


# -------------------------------------------------
# GOOGLE PLACES IMPLEMENTATION
# -------------------------------------------------


def find_competitors_google(
    *,
    category: str,
    location: str,
    pincode: Optional[str],
    api_key: str,
    limit: int = 10,
) -> List[Dict]:
    """
    Uses Google Geocoding + Places Text Search + Place Details to fetch
    competitors with rich information.
    """
    lat, lon = _geocode_location(location=location, pincode=pincode, api_key=api_key)

    if lat is None or lon is None:
        # Fallback: text-only search
        query = f"{category} in {location}"
        if pincode:
            query += f" {pincode}"
        return _places_text_search(query=query, api_key=api_key, limit=limit)

    # Prefer geocoded search around the client
    query = category
    return _places_text_search(
        query=query,
        api_key=api_key,
        limit=limit,
        location=(lat, lon),
        radius=3000,  # 3km radius, adjust as needed
    )


def _geocode_location(
    *,
    location: str,
    pincode: Optional[str],
    api_key: str,
) -> Tuple[Optional[float], Optional[float]]:
    q = location
    if pincode:
        q = f"{location} {pincode}"

    params = {"address": q, "key": api_key}
    r = requests.get(GOOGLE_GEOCODE_URL, params=params, timeout=8)
    if r.status_code != 200:
        return None, None

    data = r.json()
    if not data.get("results"):
        return None, None

    loc = data["results"][0]["geometry"]["location"]
    return loc.get("lat"), loc.get("lng")


def _places_text_search(
    *,
    query: str,
    api_key: str,
    limit: int,
    location: Optional[Tuple[float, float]] = None,
    radius: Optional[int] = None,
) -> List[Dict]:
    params = {
        "query": query,
        "key": api_key,
    }
    if location and radius:
        params["location"] = f"{location[0]},{location[1]}"
        params["radius"] = str(radius)

    r = requests.get(GOOGLE_PLACES_TEXT_URL, params=params, timeout=8)
    if r.status_code != 200:
        return []

    data = r.json()
    results = data.get("results", [])[:limit]

    enriched: List[Dict] = []
    for place in results:
        place_id = place.get("place_id")
        details = _fetch_place_details(place_id=place_id, api_key=api_key) if place_id else {}

        photo_url = None
        photos = place.get("photos") or details.get("photos")
        if photos:
            photo_ref = photos[0].get("photo_reference")
            if photo_ref:
                photo_url = _build_photo_url(photo_ref, api_key)

        enriched.append(
            {
                "name": place.get("name"),
                "address": details.get("formatted_address") or place.get("formatted_address"),
                "website": details.get("website"),
                "maps_url": details.get("url"),
                "photo_url": photo_url,
                "lat": place.get("geometry", {}).get("location", {}).get("lat"),
                "lon": place.get("geometry", {}).get("location", {}).get("lng"),
                "place_id": place_id,
                "source": "google_places",
                "rating": details.get("rating") or place.get("rating"),
                "user_ratings_total": details.get("user_ratings_total")
                or place.get("user_ratings_total"),
            }
        )

    return enriched


def _fetch_place_details(*, place_id: str, api_key: str) -> Dict:
    params = {
        "place_id": place_id,
        "key": api_key,
        "fields": "name,formatted_address,website,url,photo,rating,user_ratings_total",
    }
    r = requests.get(GOOGLE_PLACES_DETAILS_URL, params=params, timeout=8)
    if r.status_code != 200:
        return {}
    return r.json().get("result", {}) or {}


def _build_photo_url(photo_reference: str, api_key: str, maxwidth: int = 400) -> str:
    return (
        f"{GOOGLE_PLACES_PHOTO_URL}?maxwidth={maxwidth}"
        f"&photoreference={photo_reference}&key={api_key}"
    )


# -------------------------------------------------
# OSM FALLBACK (your original function)
# -------------------------------------------------


def find_competitors_osm(
    query: str,
    limit: int = 10,
) -> List[Dict]:
    """
    Lightweight competitor finder using OpenStreetMap (free, no key).
    """
    params = {
        "format": "json",
        "q": query,
        "addressdetails": 1,
        "limit": limit,
    }

    r = requests.get(OSM_URL, params=params, headers={"User-Agent": "AICMO"}, timeout=8)
    if r.status_code != 200:
        return []

    out: List[Dict] = []
    for item in r.json():
        name = item.get("display_name", "")
        out.append(
            {
                "name": name.split(",")[0],
                "lat": item.get("lat"),
                "lon": item.get("lon"),
                "raw": item,
            }
        )
    return out
