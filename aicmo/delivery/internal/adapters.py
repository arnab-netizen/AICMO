"""Delivery module - Internal adapters (MVP)."""
from datetime import datetime
from typing import Optional
from aicmo.delivery.api.ports import DeliveryPackagePort, PublishExecutePort, DeliveryQueryPort
from aicmo.delivery.api.dtos import DeliveryPackageDTO, DeliveryArtifactDTO, PublishResultDTO
from aicmo.shared.ids import DraftId, DeliveryPackageId


class DeliveryPackageAdapter(DeliveryPackagePort):
    """Minimal delivery package creation adapter."""
    
    def __init__(self, repo):
        """
        Initialize adapter with repository.
        
        Args:
            repo: Repository instance (InMemoryDeliveryRepo or DatabaseDeliveryRepo)
        """
        self._repo = repo
    
    def create_package(self, draft_id: DraftId) -> DeliveryPackageDTO:
        """
        Create delivery package from draft.
        
        MVP: Generates deterministic pack output artifacts.
        """
        package_id = DeliveryPackageId(f"pkg_{draft_id}_{int(datetime.utcnow().timestamp())}")
        
        # Create pack artifacts
        artifacts = [
            DeliveryArtifactDTO(
                name="content_pack.zip",
                url=f"https://delivery.aicmo.com/{package_id}/pack.zip",
                format="zip",
            ),
            DeliveryArtifactDTO(
                name="strategy_doc.pdf",
                url=f"https://delivery.aicmo.com/{package_id}/strategy.pdf",
                format="pdf",
            ),
            DeliveryArtifactDTO(
                name="assets_bundle.zip",
                url=f"https://delivery.aicmo.com/{package_id}/assets.zip",
                format="zip",
            ),
        ]
        
        package = DeliveryPackageDTO(
            package_id=package_id,
            draft_id=draft_id,
            artifacts=artifacts,
            created_at=datetime.utcnow(),
        )
        
        self._repo.save_package(package)
        return package


class PublishExecuteAdapter(PublishExecutePort):
    """Minimal publish execution adapter."""
    
    def __init__(self, repo):
        """
        Initialize adapter with repository.
        
        Args:
            repo: Repository instance (InMemoryDeliveryRepo or DatabaseDeliveryRepo)
        """
        self._repo = repo
    
    def publish(self, package_id: DeliveryPackageId) -> PublishResultDTO:
        """Publish package to destination (MVP: simulated)."""
        package = self._repo.get_package(package_id)
        if not package:
            raise ValueError(f"Package {package_id} not found")
        
        # Simulate successful publish
        published_urls = [artifact.url for artifact in package.artifacts]
        
        return PublishResultDTO(
            job_id=f"pub_{package_id}",
            success=True,
            published_urls=published_urls,
            published_at=datetime.utcnow(),
        )


class DeliveryQueryAdapter(DeliveryQueryPort):
    """Minimal query adapter."""
    
    def __init__(self, repo):
        """
        Initialize adapter with repository.
        
        Args:
            repo: Repository instance (InMemoryDeliveryRepo or DatabaseDeliveryRepo)
        """
        self._repo = repo
    
    def get_package(self, package_id: DeliveryPackageId) -> DeliveryPackageDTO:
        package = self._repo.get_package(package_id)
        if not package:
            raise ValueError(f"Package {package_id} not found")
        return package
