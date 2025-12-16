"""Delivery Module - Database Repository."""
from typing import Optional
from sqlalchemy.exc import IntegrityError
from aicmo.delivery.api.dtos import DeliveryPackageDTO
from aicmo.shared.ids import DeliveryPackageId


class DatabaseDeliveryRepo:
    """
    Database persistence for delivery packages.
    
    Idempotency: Saving same package_id replaces package + artifacts.
    Ordering: Artifacts retrieved in deterministic position order.
    """
    
    def __init__(self):
        # Lazy imports to avoid circular dependencies
        from aicmo.delivery.internal.models import DeliveryPackageDB, DeliveryArtifactDB
        from aicmo.core.db import get_session
        self._DeliveryPackageDB = DeliveryPackageDB
        self._DeliveryArtifactDB = DeliveryArtifactDB
        self._get_session = get_session
    
    def save_package(self, package: DeliveryPackageDTO) -> None:
        """
        Save delivery package with idempotent behavior.
        
        If package_id already exists, delete old package + artifacts
        and insert new package + artifacts (cascade delete ensures cleanup).
        """
        from aicmo.delivery.internal.mappers import dto_to_db_package
        
        with self._get_session() as session:
            try:
                # Delete existing package (cascade deletes artifacts)
                existing = session.query(self._DeliveryPackageDB).filter_by(
                    package_id=str(package.package_id)
                ).first()
                
                if existing:
                    session.delete(existing)
                    session.flush()
                
                # Insert new package + artifacts
                package_db, artifacts_db = dto_to_db_package(package)
                session.add(package_db)
                session.flush()  # Get package ID
                
                # Add artifacts with package_id reference
                for artifact_db in artifacts_db:
                    artifact_db.package_id = package_db.package_id
                    session.add(artifact_db)
                
                session.commit()
            
            except IntegrityError as e:
                session.rollback()
                raise ValueError(f"Failed to save package {package.package_id}: {e}")
    
    def get_package(self, package_id: DeliveryPackageId) -> Optional[DeliveryPackageDTO]:
        """
        Retrieve delivery package by package_id.
        
        Returns None if not found.
        Artifacts are returned in deterministic position order.
        """
        from aicmo.delivery.internal.mappers import db_to_dto_package
        
        with self._get_session() as session:
            package_db = session.query(self._DeliveryPackageDB).filter_by(
                package_id=str(package_id)
            ).first()
            
            if not package_db:
                return None
            
            # Fetch artifacts in deterministic order
            artifacts_db = session.query(self._DeliveryArtifactDB).filter_by(
                package_id=str(package_id)
            ).order_by(self._DeliveryArtifactDB.position.asc()).all()
            
            return db_to_dto_package(package_db, artifacts_db)
