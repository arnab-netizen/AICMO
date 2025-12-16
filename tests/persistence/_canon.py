"""
Canonicalization helpers for persistence test parity verification.

Purpose: Normalize DTOs for comparison to prove mem/db parity.
- Normalize timestamps to isoformat strings (deterministic comparison)
- Sort lists by stable keys (IDs)
- Remove fields not in DTO contracts (if any appear in implementation)

NOT for business logic - test-only utility.
"""

from datetime import datetime
from typing import Any, Dict, List


def normalize_datetime(dt: datetime) -> str:
    """Convert datetime to ISO format string for comparison."""
    if dt is None:
        return None
    return dt.isoformat()


def canonicalize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively canonicalize dictionary for comparison.
    
    - Converts datetime objects to ISO strings
    - Sorts lists by 'id' or first string field
    - Returns copy (doesn't mutate input)
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, datetime):
            result[key] = normalize_datetime(value)
        elif isinstance(value, dict):
            result[key] = canonicalize_dict(value)
        elif isinstance(value, list):
            result[key] = canonicalize_list(value)
        else:
            result[key] = value
    return result


def canonicalize_list(items: List[Any]) -> List[Any]:
    """
    Canonicalize list by sorting and normalizing items.
    
    - If items are dicts, sort by 'id' field (or first field)
    - If items are primitives, sort directly
    - Recursively canonicalize nested structures
    """
    if not items:
        return items
    
    # Handle list of dicts
    if isinstance(items[0], dict):
        normalized = [canonicalize_dict(item) for item in items]
        # Try to sort by 'id' field, fall back to first field
        try:
            if 'id' in items[0]:
                return sorted(normalized, key=lambda x: str(x.get('id', '')))
            else:
                first_key = next(iter(items[0].keys()))
                return sorted(normalized, key=lambda x: str(x.get(first_key, '')))
        except (TypeError, StopIteration):
            return normalized
    
    # Handle list of primitives
    if isinstance(items[0], (str, int, float)):
        return sorted(items)
    
    # Handle list of datetime
    if isinstance(items[0], datetime):
        return [normalize_datetime(dt) for dt in items]
    
    return items


def dto_to_comparable(dto: Any) -> Dict[str, Any]:
    """
    Convert DTO to comparable dict for parity tests.
    
    Uses model_dump() if Pydantic model, otherwise dict().
    """
    if hasattr(dto, 'model_dump'):
        return canonicalize_dict(dto.model_dump())
    elif hasattr(dto, 'dict'):
        return canonicalize_dict(dto.dict())
    else:
        return canonicalize_dict(dict(dto))


def canonicalize_delivery_package(pkg_dto) -> Dict[str, Any]:
    """
    Canonicalize DeliveryPackageDTO for mem vs db comparison.
    
    - Normalizes timestamps
    - Preserves artifact order (position field ensures determinism)
    - Converts IDs to strings for comparison
    """
    from aicmo.delivery.api.dtos import DeliveryPackageDTO
    
    if not isinstance(pkg_dto, DeliveryPackageDTO):
        raise TypeError(f"Expected DeliveryPackageDTO, got {type(pkg_dto)}")
    
    return {
        "package_id": str(pkg_dto.package_id),
        "draft_id": str(pkg_dto.draft_id),
        "artifacts": [
            {
                "name": artifact.name,
                "url": artifact.url,
                "format": artifact.format,
            }
            for artifact in pkg_dto.artifacts
        ],  # Preserve order (both mem and db maintain list order)
        "created_at": normalize_datetime(pkg_dto.created_at),
    }

