from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
REQUEST_LOG_PATH = LOG_DIR / "aicmo_requests.jsonl"


def normalise_brief(brief: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise BrandBrief-like payloads for hashing & logging.

    - Keep only fields that matter for generation.
    - Sort keys for deterministic output.
    - Avoid logging anything that looks too sensitive (e.g. emails).
    """
    allowed_keys = [
        "brand_name",
        "industry",
        "location",
        "primary_goal",
        "secondary_goal",
        "brand_tone",
        "target_audience",
        "website",
        "budget_level",
        "time_horizon",
    ]

    normalised: Dict[str, Any] = {}
    for key in allowed_keys:
        if key in brief:
            normalised[key] = brief[key]
    return normalised


def make_fingerprint(
    *,
    pack_key: str,
    brief: Dict[str, Any],
    constraints: Dict[str, Any] | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a stable fingerprint for a (pack_key, brief, constraints) combo.

    Returns:
        - fingerprint hex string
        - the normalised payload used for hashing
    """
    constraints = constraints or {}
    payload = {
        "pack_key": pack_key,
        "brief": normalise_brief(brief),
        "constraints": constraints,  # typically small
    }
    dumped = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    fp = hashlib.sha256(dumped.encode("utf-8")).hexdigest()
    return fp, payload


def log_request(
    *,
    fingerprint: str,
    payload: Dict[str, Any],
    status: str,
    duration_ms: float | None = None,
    error_detail: str | None = None,
) -> None:
    """
    Append a single JSONL record for this request.

    Fields:
        - ts: ISO timestamp (UTC)
        - fingerprint
        - status: "ok", "error", "benchmark_fail", "cache_hit", etc.
        - duration_ms: optional
        - pack_key
        - brief: normalised brief
        - constraints: as given
        - error_detail: short text, if any
    """
    record: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "fingerprint": fingerprint,
        "status": status,
        "duration_ms": duration_ms,
        "pack_key": payload.get("pack_key"),
        "brief": payload.get("brief"),
        "constraints": payload.get("constraints"),
    }
    if error_detail:
        record["error_detail"] = error_detail

    REQUEST_LOG_PATH.parent.mkdir(exist_ok=True)
    with REQUEST_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
