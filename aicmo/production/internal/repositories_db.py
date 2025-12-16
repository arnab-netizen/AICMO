"""
Production module database repository.

Implements production persistence using SQLAlchemy ORM.
Follows same session lifecycle pattern as onboarding/strategy modules.

Idempotency Keys:
- ContentDraft: draft_id (unique constraint)
- DraftBundle: bundle_id (unique constraint)
- BundleAsset: asset_id (unique constraint)
"""

from datetime import datetime, timezone
from typing import Optional, Protocol, List
from sqlalchemy.exc import IntegrityError

from aicmo.production.api.dtos import (
    ContentDraftDTO,
    DraftBundleDTO,
    AssetDTO,
)
from aicmo.shared.ids import DraftId, StrategyId, AssetId


class ProductionRepository(Protocol):
    """Repository interface for production persistence."""
    
    def save_draft(self, draft: ContentDraftDTO) -> None:
        """Save a content draft."""
        ...
    
    def get_draft(self, draft_id: DraftId) -> Optional[ContentDraftDTO]:
        """Retrieve a draft by ID."""
        ...
    
    def save_bundle(self, bundle: DraftBundleDTO) -> None:
        """Save a draft bundle with assets."""
        ...
    
    def get_bundle(self, bundle_id: str) -> Optional[DraftBundleDTO]:
        """Retrieve a bundle by ID."""
        ...


class DatabaseProductionRepo:
    """
    Database storage for production entities using SQLAlchemy.
    
    Session Lifecycle: Uses same pattern as onboarding/strategy (aicmo.core.db.get_session)
    Idempotency: draft_id, bundle_id, asset_id uniqueness enforced by DB constraints
    Read-Only Safety: get_* methods do NOT update updated_at timestamps
    """
    
    def __init__(self):
        # Import DB models and session here to avoid circular imports
        from aicmo.production.internal.models import (
            ContentDraftDB,
            DraftBundleDB,
            BundleAssetDB,
        )
        from aicmo.core.db import get_session
        
        self._ContentDraftDB = ContentDraftDB
        self._DraftBundleDB = DraftBundleDB
        self._BundleAssetDB = BundleAssetDB
        self._get_session = get_session
    
    def save_draft(self, draft: ContentDraftDTO) -> None:
        """
        Save content draft to database.
        
        Idempotency: If draft_id already exists, updates existing row.
        Uses query + update pattern instead of merge() for explicit upsert.
        Commit boundary: Explicit commit after successful insert/update.
        Rollback: Automatic on exception via context manager.
        """
        with self._get_session() as session:
            # Check if draft already exists
            existing = session.query(self._ContentDraftDB).filter_by(
                draft_id=draft.draft_id
            ).first()
            
            if existing:
                # Update existing
                existing.strategy_id = draft.strategy_id
                existing.content_type = draft.content_type
                existing.body = draft.body
                existing.meta = draft.metadata
                existing.updated_at = datetime.now(timezone.utc)
            else:
                # Insert new
                draft_db = self._ContentDraftDB(
                    draft_id=draft.draft_id,
                    strategy_id=draft.strategy_id,
                    content_type=draft.content_type,
                    body=draft.body,
                    meta=draft.metadata,
                    created_at=draft.created_at,
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(draft_db)
            
            session.commit()
    
    def get_draft(self, draft_id: DraftId) -> Optional[ContentDraftDTO]:
        """
        Retrieve a draft by draft_id.
        
        Read-Only Safety: Does NOT commit, does NOT update updated_at.
        Returns None if not found.
        """
        with self._get_session() as session:
            draft_db = session.query(self._ContentDraftDB).filter_by(
                draft_id=draft_id
            ).first()
            
            if not draft_db:
                return None
            
            return ContentDraftDTO(
                draft_id=draft_db.draft_id,
                strategy_id=draft_db.strategy_id,
                content_type=draft_db.content_type,
                body=draft_db.body,
                metadata=draft_db.meta or {},
                created_at=draft_db.created_at,
            )
    
    def save_bundle(self, bundle: DraftBundleDTO) -> None:
        """
        Save draft bundle with assets to database.
        
        Idempotency: If bundle_id already exists, updates existing row + assets.
        Uses query + update pattern for explicit upsert.
        Assets: Deletes old assets, inserts new ones (replace strategy).
        Commit boundary: Single transaction for bundle + all assets.
        Rollback: Automatic on exception via context manager.
        """
        with self._get_session() as session:
            # Check if bundle already exists
            existing_bundle = session.query(self._DraftBundleDB).filter_by(
                bundle_id=bundle.bundle_id
            ).first()
            
            if existing_bundle:
                # Update existing bundle
                existing_bundle.draft_id = bundle.draft_id
                existing_bundle.assembled_at = bundle.assembled_at
                existing_bundle.updated_at = datetime.now(timezone.utc)
                
                # Delete old assets for this bundle (replace strategy)
                session.query(self._BundleAssetDB).filter_by(
                    bundle_id=bundle.bundle_id
                ).delete()
            else:
                # Insert new bundle
                bundle_db = self._DraftBundleDB(
                    bundle_id=bundle.bundle_id,
                    draft_id=bundle.draft_id,
                    assembled_at=bundle.assembled_at,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(bundle_db)
            
            # Insert assets (fresh set)
            for asset in bundle.assets:
                asset_db = self._BundleAssetDB(
                    asset_id=asset.asset_id,
                    bundle_id=bundle.bundle_id,
                    asset_type=asset.asset_type,
                    url=asset.url,
                    meta=asset.metadata,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(asset_db)
            
            session.commit()
    
    def get_bundle(self, bundle_id: str) -> Optional[DraftBundleDTO]:
        """
        Retrieve a bundle by bundle_id with all associated assets.
        
        Read-Only Safety: Does NOT commit, does NOT update updated_at.
        Returns None if not found.
        """
        with self._get_session() as session:
            bundle_db = session.query(self._DraftBundleDB).filter_by(
                bundle_id=bundle_id
            ).first()
            
            if not bundle_db:
                return None
            
            # Fetch all assets for this bundle
            assets_db = session.query(self._BundleAssetDB).filter_by(
                bundle_id=bundle_id
            ).all()
            
            assets = [
                AssetDTO(
                    asset_id=asset_db.asset_id,
                    asset_type=asset_db.asset_type,
                    url=asset_db.url,
                    metadata=asset_db.meta or {},
                )
                for asset_db in assets_db
            ]
            
            return DraftBundleDTO(
                bundle_id=bundle_db.bundle_id,
                draft_id=bundle_db.draft_id,
                assets=assets,
                assembled_at=bundle_db.assembled_at,
            )
