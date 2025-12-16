"""
Production module mappers.

Pure mapping functions between DTOs and ORM models.
No business logic, no database session calls.
"""

from datetime import datetime, timezone
from typing import List

from aicmo.production.api.dtos import (
    ContentDraftDTO,
    DraftBundleDTO,
    AssetDTO,
)
from aicmo.production.internal.models import (
    ContentDraftDB,
    DraftBundleDB,
    BundleAssetDB,
)


def draft_to_db(draft: ContentDraftDTO) -> ContentDraftDB:
    """Map ContentDraftDTO to ContentDraftDB ORM model."""
    return ContentDraftDB(
        draft_id=draft.draft_id,
        strategy_id=draft.strategy_id,
        content_type=draft.content_type,
        body=draft.body,
        meta=draft.metadata,
        created_at=draft.created_at,
        updated_at=datetime.now(timezone.utc),
    )


def draft_from_db(draft_db: ContentDraftDB) -> ContentDraftDTO:
    """Map ContentDraftDB ORM model to ContentDraftDTO."""
    return ContentDraftDTO(
        draft_id=draft_db.draft_id,
        strategy_id=draft_db.strategy_id,
        content_type=draft_db.content_type,
        body=draft_db.body,
        metadata=draft_db.meta or {},
        created_at=draft_db.created_at,
    )


def bundle_to_db(bundle: DraftBundleDTO) -> DraftBundleDB:
    """
    Map DraftBundleDTO to DraftBundleDB ORM model.
    
    Note: Does NOT include assets. Assets are mapped separately via asset_to_db().
    """
    return DraftBundleDB(
        bundle_id=bundle.bundle_id,
        draft_id=bundle.draft_id,
        assembled_at=bundle.assembled_at,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def bundle_from_db(bundle_db: DraftBundleDB, assets: List[AssetDTO]) -> DraftBundleDTO:
    """
    Map DraftBundleDB ORM model to DraftBundleDTO.
    
    Args:
        bundle_db: Bundle ORM model
        assets: List of AssetDTO (fetched separately from BundleAssetDB)
    """
    return DraftBundleDTO(
        bundle_id=bundle_db.bundle_id,
        draft_id=bundle_db.draft_id,
        assets=assets,
        assembled_at=bundle_db.assembled_at,
    )


def asset_to_db(asset: AssetDTO, bundle_id: str) -> BundleAssetDB:
    """
    Map AssetDTO to BundleAssetDB ORM model.
    
    Args:
        asset: AssetDTO to map
        bundle_id: Parent bundle_id (required for FK reference)
    """
    return BundleAssetDB(
        asset_id=asset.asset_id,
        bundle_id=bundle_id,
        asset_type=asset.asset_type,
        url=asset.url,
        meta=asset.metadata,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )


def asset_from_db(asset_db: BundleAssetDB) -> AssetDTO:
    """Map BundleAssetDB ORM model to AssetDTO."""
    return AssetDTO(
        asset_id=asset_db.asset_id,
        asset_type=asset_db.asset_type,
        url=asset_db.url,
        metadata=asset_db.meta or {},
    )
