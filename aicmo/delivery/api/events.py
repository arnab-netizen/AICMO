"""Delivery - Events."""
from aicmo.shared.events import DomainEvent
from aicmo.shared.ids import DeliveryPackageId

class Delivered(DomainEvent):
    package_id: DeliveryPackageId
    artifact_count: int

class PublishStarted(DomainEvent):
    job_id: str
    package_id: DeliveryPackageId

class PublishCompleted(DomainEvent):
    job_id: str
    published_urls: list[str]

class PublishFailed(DomainEvent):
    job_id: str
    error_message: str

__all__ = ["Delivered", "PublishStarted", "PublishCompleted", "PublishFailed"]
