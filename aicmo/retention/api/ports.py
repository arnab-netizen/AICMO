"""Retention - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.retention.api.dtos import RenewalRiskDTO, UpsellOpportunityDTO, LifecycleStateDTO
from aicmo.shared.ids import ClientId

class RenewalAssessPort(ABC):
    @abstractmethod
    def assess_renewal_risk(self, client_id: ClientId) -> RenewalRiskDTO:
        pass

class UpsellDetectPort(ABC):
    @abstractmethod
    def detect_upsell_opportunities(self, client_id: ClientId) -> list[UpsellOpportunityDTO]:
        pass

class RetentionQueryPort(ABC):
    @abstractmethod
    def get_lifecycle_state(self, client_id: ClientId) -> LifecycleStateDTO:
        pass

__all__ = ["RenewalAssessPort", "UpsellDetectPort", "RetentionQueryPort"]
