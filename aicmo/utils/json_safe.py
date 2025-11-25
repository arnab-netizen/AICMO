"""JSON-safe serialization for dates, datetimes, Decimals, and other non-standard types."""

from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any


def _json_default(obj: Any) -> Any:
    """Safe JSON default for dates, datetimes, Decimals, etc."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    # Last-resort: string representation
    return str(obj)


def json_safe_dumps(obj: Any, **kwargs: Any) -> str:
    """
    Wrapper around json.dumps that can handle date/datetime/Decimal.
    Use this instead of json.dumps for logs / LLM payloads.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments to pass to json.dumps

    Returns:
        JSON string with safe serialization of non-standard types
    """
    kwargs.setdefault("default", _json_default)
    kwargs.setdefault("ensure_ascii", False)
    return json.dumps(obj, **kwargs)
