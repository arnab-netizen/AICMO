"""Reporting - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import ReportId, ProjectId

class ReportGenerated(DomainEvent):
    report_id: ReportId
    project_id: ProjectId

class MetricsCollected(DomainEvent):
    project_id: ProjectId
    metric_count: int

__all__ = ["ReportGenerated", "MetricsCollected"]
