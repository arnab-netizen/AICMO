"""Observability - DTOs."""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from aicmo.shared.ids import TraceId, SpanId

class LogEventDTO(BaseModel):
    level: str  # "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"
    message: str
    context: Dict[str, Any] = {}
    timestamp: datetime

class MetricDTO(BaseModel):
    name: str
    value: float
    tags: Dict[str, str] = {}
    timestamp: datetime

class TraceSpanDTO(BaseModel):
    span_id: Optional[SpanId] = None
    trace_id: TraceId
    operation_name: str
    parent_span_id: Optional[SpanId] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    tags: Dict[str, Any] = {}

__all__ = ["LogEventDTO", "MetricDTO", "TraceSpanDTO"]
