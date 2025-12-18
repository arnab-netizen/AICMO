from __future__ import annotations

from typing import Any

class IncompatibleSchemaError(Exception):
    def to_error_response(self):
        try:
            from aicmo.api.schemas import ErrorResponse
        except Exception:
            return {"error_code": "SCHEMA_INCOMPATIBLE", "message": "Schema incompatible", "details": None, "trace_id": ""}
        return ErrorResponse(error_code="SCHEMA_INCOMPATIBLE", message="Schema incompatible", details=None, trace_id="")


def _major_version(schema_version: str) -> int:
    parts = str(schema_version).split(".")
    try:
        return int(parts[0])
    except Exception:
        return 0


def validate_compat(artifact: Any) -> bool:
    """Validate artifact schema compatibility.

    Rules:
    - Unknown MAJOR schema_version -> reject
    - Missing required fields -> reject
    - Additive fields allowed
    """
    # Supported major versions
    SUPPORTED_MAJOR = {1}

    sv = getattr(artifact, "schema_version", None) or artifact.get("schema_version") if isinstance(artifact, dict) else None
    if not sv:
        raise IncompatibleSchemaError()

    major = _major_version(sv)
    if major not in SUPPORTED_MAJOR:
        raise IncompatibleSchemaError()

    # Basic required fields check (minimal enforcement)
    required = ["id", "tenant_id", "project_id", "type", "schema_version", "version", "checksum"]
    for f in required:
        if isinstance(artifact, dict):
            if f not in artifact:
                raise IncompatibleSchemaError()
        else:
            if not hasattr(artifact, f):
                raise IncompatibleSchemaError()

    return True
