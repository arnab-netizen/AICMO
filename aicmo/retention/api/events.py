"""Retention - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import ClientId

class RenewalDue(DomainEvent):
    client_id: ClientId
    days_until_renewal: int

class ChurnRiskDetected(DomainEvent):
    client_id: ClientId
    risk_score: float
    factors: list[str]

class UpsellSuggested(DomainEvent):
    client_id: ClientId
    opportunity_type: str
    estimated_value: float

__all__ = ["RenewalDue", "ChurnRiskDetected", "UpsellSuggested"]
