"""Client Review - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import ReviewPackageId, ClientId

class ClientReviewSent(DomainEvent):
    package_id: ReviewPackageId
    client_id: ClientId

class ClientFeedbackReceived(DomainEvent):
    package_id: ReviewPackageId
    approval_status: str

class RevisionRequested(DomainEvent):
    package_id: ReviewPackageId
    revision_count: int

class ClientApproved(DomainEvent):
    package_id: ReviewPackageId
    client_id: ClientId

__all__ = ["ClientReviewSent", "ClientFeedbackReceived", "RevisionRequested", "ClientApproved"]
