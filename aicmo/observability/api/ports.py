"""Observability - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.observability.api.dtos import LogEventDTO, MetricDTO, TraceSpanDTO

class LoggerPort(ABC):
    @abstractmethod
    def log(self, event: LogEventDTO) -> None:
        pass

class MetricsPort(ABC):
    @abstractmethod
    def record_metric(self, metric: MetricDTO) -> None:
        pass

class TracerPort(ABC):
    @abstractmethod
    def start_span(self, span: TraceSpanDTO) -> str:
        """Returns span_id."""
        pass
    
    @abstractmethod
    def end_span(self, span_id: str) -> None:
        pass

__all__ = ["LoggerPort", "MetricsPort", "TracerPort"]
