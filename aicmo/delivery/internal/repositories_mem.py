"""Delivery Module - In-Memory Repository."""
from typing import Dict, Optional
from aicmo.delivery.api.dtos import DeliveryPackageDTO, DeliveryArtifactDTO
from aicmo.shared.ids import DeliveryPackageId


class InMemoryDeliveryRepo:
    """
    In-memory storage for delivery packages (Phase 3 baseline).
    
    Extracted from adapters.py for dual-mode support.
    Idempotency: Saving same package_id replaces previous package.
    Returns copies to prevent mutation leaks.
    """
    
    def __init__(self):
        self._packages: Dict[DeliveryPackageId, DeliveryPackageDTO] = {}
    
    def save_package(self, package: DeliveryPackageDTO) -> None:
        """
        Save delivery package (idempotent).
        
        If package_id already exists, replace with new package.
        Artifacts are replaced entirely (not merged).
        """
        self._packages[package.package_id] = package
    
    def get_package(self, package_id: DeliveryPackageId) -> Optional[DeliveryPackageDTO]:
        """
        Retrieve delivery package by package_id.
        
        Returns copy to prevent mutation of stored data.
        Returns None if not found.
        """
        package = self._packages.get(package_id)
        if package is None:
            return None
        
        # Return copy to prevent mutation leaks
        return DeliveryPackageDTO(
            package_id=package.package_id,
            draft_id=package.draft_id,
            artifacts=[
                DeliveryArtifactDTO(
                    name=artifact.name,
                    url=artifact.url,
                    format=artifact.format,
                )
                for artifact in package.artifacts
            ],
            created_at=package.created_at,
        )
