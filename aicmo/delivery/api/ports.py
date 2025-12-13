"""Delivery - Port Interfaces."""
from abc import ABC, abstractmethod
from aicmo.delivery.api.dtos import DeliveryPackageDTO, PublishJobDTO, PublishResultDTO
from aicmo.shared.ids import DraftId, DeliveryPackageId

class DeliveryPackagePort(ABC):
    @abstractmethod
    def create_package(self, draft_id: DraftId) -> DeliveryPackageDTO:
        pass

class PublishExecutePort(ABC):
    @abstractmethod
    def publish(self, package_id: DeliveryPackageId) -> PublishResultDTO:
        pass

class DeliveryQueryPort(ABC):
    @abstractmethod
    def get_package(self, package_id: DeliveryPackageId) -> DeliveryPackageDTO:
        pass

__all__ = ["DeliveryPackagePort", "PublishExecutePort", "DeliveryQueryPort"]
