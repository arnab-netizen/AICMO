from __future__ import annotations

from typing import Optional, Dict, Any
from pydantic import BaseModel


class BaseSchema(BaseModel):
    # Backwards-compatible `.dict()` for tests and older codepaths which still
    # call `.dict()`; delegate to `model_dump()` under Pydantic v2 to avoid
    # deprecation warnings being treated as errors.
    def dict(self, *args, **kwargs):
        return self.model_dump(*args, **kwargs)


class ErrorResponse(BaseSchema):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    trace_id: str = ""


class GenerateRequest(BaseSchema):
    tenant_id: str
    project_id: str
    artifact_type: str
    idempotency_key: Optional[str] = None
    trace_id: Optional[str] = None
    requested_schema_version: Optional[str] = None


class GenerateResponse(BaseSchema):
    artifact_id: str
    status: str
    trace_id: str
    schema_version: str


class ExportRequest(BaseSchema):
    tenant_id: str
    project_id: str
    idempotency_key: str
    trace_id: str
    bundle_schema_version: str


class ExportResponse(BaseSchema):
    delivery_artifact_id: str
    trace_id: str
    bundle_schema_version: str
