"""
Base event classes for AICMO domain events.

All module-specific events should inherit from DomainEvent.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from aicmo.shared.ids import EventId, CorrelationId


class DomainEvent(BaseModel):
    """
    Base class for all domain events in AICMO.
    
    Required fields:
    - event_id: Unique identifier for this event
    - occurred_at: When the event occurred (UTC)
    - correlation_id: For tracing related events across modules
    
    Events are immutable once created.
    """
    
    model_config = ConfigDict(frozen=True)
    
    event_id: EventId = Field(default_factory=lambda: EventId(str(__import__("uuid").uuid4())))
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(__import__("datetime").timezone.utc))
    correlation_id: Optional[CorrelationId] = None


__all__ = ["DomainEvent"]
