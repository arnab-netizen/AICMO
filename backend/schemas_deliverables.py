"""
Canonical deliverable envelope schema for Streamlit ↔ Backend contract.

This schema defines the required format for all generate responses.
MUST be used by all generate endpoints.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


class DeliverableKind(str, Enum):
    """Supported deliverable content types"""
    LINKEDIN_POST = "linkedin_post"
    INSTAGRAM_POST = "instagram_post"
    TWITTER_POST = "twitter_post"
    EMAIL_COPY = "email_copy"
    AD_COPY = "ad_copy"
    LANDING_PAGE = "landing_page"
    BLOG_POST = "blog_post"
    IMAGE_PROMPT = "image_prompt"
    VIDEO_SCRIPT = "video_script"
    CAROUSEL = "carousel"
    STRATEGY = "strategy"
    CAMPAIGN_BRIEF = "campaign_brief"
    CONTENT_CALENDAR = "content_calendar"
    AUDIENCE_SEGMENT = "audience_segment"
    PERSONA_CARD = "persona_card"
    UNKNOWN = "unknown"


class ResponseStatus(str, Enum):
    """Response status codes"""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    PARTIAL = "PARTIAL"  # Some deliverables succeeded


@dataclass
class DeliverableAssets:
    """Assets associated with a deliverable"""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
    file_url: Optional[str] = None
    slides: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, filtering None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class Deliverable:
    """Single deliverable item in response"""
    id: str  # Unique ID for this deliverable
    kind: str  # DeliverableKind
    title: str
    content_markdown: str  # REQUIRED: text content, never empty for SUCCESS
    platform: Optional[str] = None
    hashtags: Optional[List[str]] = field(default_factory=list)
    assets: Optional[DeliverableAssets] = None
    metadata: Optional[Dict[str, Any]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict"""
        data = asdict(self)
        if self.assets:
            data["assets"] = self.assets.to_dict()
        return data


@dataclass
class ResponseMeta:
    """Response metadata"""
    timestamp: str
    run_id: str
    provider: str  # LLM provider used
    model: Optional[str] = None
    cost_usd: Optional[float] = None
    tokens_used: Optional[int] = None
    warnings: Optional[List[str]] = field(default_factory=list)
    trace_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, filtering None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ResponseError:
    """Error information"""
    type: str  # e.g., "VALIDATION_ERROR", "RATE_LIMIT", "NETWORK_ERROR"
    message: str
    trace_id: Optional[str] = None
    code: Optional[int] = None  # HTTP code if applicable
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict, filtering None values"""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class DeliverablesEnvelope:
    """
    Canonical response envelope for generate operations.
    
    RULE: All generate endpoints MUST return this shape.
    RULE: If status=SUCCESS, deliverables must NOT be empty.
    RULE: Each deliverable MUST have content_markdown (never empty strings).
    """
    status: str  # ResponseStatus enum value
    module: str  # e.g., "campaigns", "creatives", "strategy"
    run_id: str  # Unique ID for this generate run
    meta: Dict[str, Any]  # ResponseMeta.to_dict()
    deliverables: List[Dict[str, Any]] = field(default_factory=list)
    raw: Optional[Dict[str, Any]] = None  # Optional debug payload
    error: Optional[Dict[str, Any]] = None  # ResponseError.to_dict() if error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "status": self.status,
            "module": self.module,
            "run_id": self.run_id,
            "meta": self.meta,
            "deliverables": self.deliverables,
            "raw": self.raw,
            "error": self.error,
        }


def validate_deliverables_envelope(data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Validate that response matches deliverable envelope contract.
    
    Args:
        data: Response dict to validate
        
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Required top-level fields
    if "status" not in data:
        errors.append("Missing required field: status")
    elif data["status"] not in [ResponseStatus.SUCCESS.value, ResponseStatus.FAILED.value, ResponseStatus.PARTIAL.value]:
        errors.append(f"Invalid status: {data.get('status')}. Must be SUCCESS, FAILED, or PARTIAL")
    
    if "module" not in data:
        errors.append("Missing required field: module")
    
    if "run_id" not in data:
        errors.append("Missing required field: run_id")
    elif not isinstance(data["run_id"], str) or not data["run_id"].strip():
        errors.append("run_id must be non-empty string")
    
    if "meta" not in data:
        errors.append("Missing required field: meta")
    elif not isinstance(data["meta"], dict):
        errors.append("meta must be a dict")
    else:
        meta = data["meta"]
        if "timestamp" not in meta:
            errors.append("meta missing required field: timestamp")
        if "provider" not in meta:
            errors.append("meta missing required field: provider")
    
    if "deliverables" not in data:
        errors.append("Missing required field: deliverables")
    elif not isinstance(data["deliverables"], list):
        errors.append("deliverables must be a list")
    else:
        # If SUCCESS, deliverables must not be empty
        if data.get("status") == ResponseStatus.SUCCESS.value and len(data["deliverables"]) == 0:
            errors.append("SUCCESS status requires at least one deliverable")
        
        # Each deliverable must have required fields
        for i, d in enumerate(data["deliverables"]):
            if not isinstance(d, dict):
                errors.append(f"deliverables[{i}] must be a dict")
                continue
            
            if "id" not in d:
                errors.append(f"deliverables[{i}] missing required field: id")
            if "kind" not in d:
                errors.append(f"deliverables[{i}] missing required field: kind")
            if "title" not in d:
                errors.append(f"deliverables[{i}] missing required field: title")
            if "content_markdown" not in d:
                errors.append(f"deliverables[{i}] missing required field: content_markdown")
            elif isinstance(d["content_markdown"], str) and not d["content_markdown"].strip():
                errors.append(f"deliverables[{i}].content_markdown cannot be empty string")
    
    # If FAILED, error should be present
    if data.get("status") == ResponseStatus.FAILED.value:
        if "error" not in data or not data.get("error"):
            errors.append("FAILED status should include error details")
    
    return len(errors) == 0, errors


def create_success_envelope(
    module: str,
    run_id: str,
    deliverables: List[Deliverable],
    provider: str,
    model: Optional[str] = None,
    cost_usd: Optional[float] = None,
    tokens_used: Optional[int] = None,
    trace_id: Optional[str] = None,
    warnings: Optional[List[str]] = None,
) -> DeliverablesEnvelope:
    """Create a SUCCESS envelope"""
    return DeliverablesEnvelope(
        status=ResponseStatus.SUCCESS.value,
        module=module,
        run_id=run_id,
        meta=ResponseMeta(
            timestamp=datetime.utcnow().isoformat(),
            run_id=run_id,
            provider=provider,
            model=model,
            cost_usd=cost_usd,
            tokens_used=tokens_used,
            warnings=warnings or [],
            trace_id=trace_id,
        ).to_dict(),
        deliverables=[d.to_dict() for d in deliverables],
    )


def create_failed_envelope(
    module: str,
    run_id: str,
    error_type: str,
    error_message: str,
    trace_id: Optional[str] = None,
    code: Optional[int] = None,
) -> DeliverablesEnvelope:
    """Create a FAILED envelope"""
    return DeliverablesEnvelope(
        status=ResponseStatus.FAILED.value,
        module=module,
        run_id=run_id,
        meta=ResponseMeta(
            timestamp=datetime.utcnow().isoformat(),
            run_id=run_id,
            provider="none",
            trace_id=trace_id,
        ).to_dict(),
        error=ResponseError(
            type=error_type,
            message=error_message,
            trace_id=trace_id,
            code=code,
        ).to_dict(),
    )
