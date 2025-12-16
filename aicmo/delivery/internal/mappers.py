"""Delivery Module - DTO <-> DB Mappers."""
from typing import List, Tuple
from datetime import datetime
from aicmo.delivery.api.dtos import DeliveryPackageDTO, DeliveryArtifactDTO
from aicmo.delivery.internal.models import DeliveryPackageDB, DeliveryArtifactDB
from aicmo.shared.ids import DeliveryPackageId, DraftId


def dto_to_db_package(dto: DeliveryPackageDTO) -> Tuple[DeliveryPackageDB, List[DeliveryArtifactDB]]:
    """
    Convert DeliveryPackageDTO to database models.
    
    Returns:
        Tuple of (DeliveryPackageDB, List[DeliveryArtifactDB])
        
    Note: Artifacts include position field for deterministic ordering.
    """
    package_db = DeliveryPackageDB(
        package_id=str(dto.package_id),
        draft_id=str(dto.draft_id),
        created_at=dto.created_at,
        updated_at=datetime.utcnow(),
    )
    
    artifacts_db = [
        DeliveryArtifactDB(
            package_id=str(dto.package_id),
            name=artifact.name,
            url=artifact.url,
            format=artifact.format,
            position=idx,  # Preserve list order
            created_at=datetime.utcnow(),
        )
        for idx, artifact in enumerate(dto.artifacts)
    ]
    
    return package_db, artifacts_db


def db_to_dto_package(
    package_db: DeliveryPackageDB,
    artifacts_db: List[DeliveryArtifactDB]
) -> DeliveryPackageDTO:
    """
    Convert database models to DeliveryPackageDTO.
    
    Args:
        package_db: DeliveryPackageDB instance
        artifacts_db: List of DeliveryArtifactDB instances (pre-sorted by position)
        
    Returns:
        DeliveryPackageDTO with artifacts in position order
    """
    artifacts_dto = [
        DeliveryArtifactDTO(
            name=artifact.name,
            url=artifact.url,
            format=artifact.format,
        )
        for artifact in sorted(artifacts_db, key=lambda a: a.position)
    ]
    
    return DeliveryPackageDTO(
        package_id=DeliveryPackageId(package_db.package_id),
        draft_id=DraftId(package_db.draft_id),
        artifacts=artifacts_dto,
        created_at=package_db.created_at,
    )
