"""Reporting - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.reporting.api.dtos import MetricsSnapshotDTO, ReportDTO
from aicmo.shared.ids import ReportId, ProjectId

class MetricsCollectPort(ABC):
    @abstractmethod
    def collect_metrics(self, project_id: ProjectId) -> MetricsSnapshotDTO:
        pass

class ReportGeneratePort(ABC):
    @abstractmethod
    def generate_report(self, project_id: ProjectId) -> ReportDTO:
        pass

class ReportingQueryPort(ABC):
    @abstractmethod
    def get_report(self, report_id: ReportId) -> ReportDTO:
        pass

__all__ = ["MetricsCollectPort", "ReportGeneratePort", "ReportingQueryPort"]
