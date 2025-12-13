"""Observability - Events."""
from aicmo.shared.events import DomainEvent

class LogEmitted(DomainEvent):
    level: str
    message: str

class MetricRecorded(DomainEvent):
    metric_name: str
    value: float

__all__ = ["LogEmitted", "MetricRecorded"]
