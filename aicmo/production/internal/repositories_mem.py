"""
Production module in-memory repository.

Simulates database behavior for testing and inmemory persistence mode.
Maintains parity with DatabaseProductionRepo for deterministic testing.

Idempotency enforced via dict key checks (draft_id, bundle_id, asset_id).
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Tuple, List

from aicmo.production.api.dtos import (
    ContentDraftDTO,
    DraftBundleDTO,
    AssetDTO,
)
from aicmo.shared.ids import DraftId, StrategyId, AssetId


class InMemoryProductionRepo:
    """
    In-memory storage for production entities.
    
    Simulates database constraints:
    - Unique draft_id (idempotency)
    - Unique bundle_id (idempotency)
    - Unique asset_id (idempotency)
    
    Maintains same behavior as DatabaseProductionRepo for parity testing.
    """
    
    def __init__(self):
        self._drafts: Dict[str, ContentDraftDTO] = {}
        self._bundles: Dict[str, DraftBundleDTO] = {}
        self._assets: Dict[str, AssetDTO] = {}  # asset_id -> AssetDTO
        self._bundle_assets: Dict[str, List[str]] = {}  # bundle_id -> [asset_ids]
    
    def save_draft(self, draft: ContentDraftDTO) -> None:
        """
        Save content draft to memory.
        
        Idempotency: If draft_id exists, overwrites (same as merge() in DB repo).
        """
        self._drafts[draft.draft_id] = draft
    
    def get_draft(self, draft_id: DraftId) -> Optional[ContentDraftDTO]:
        """
        Retrieve a draft by draft_id.
        
        Read-Only: Returns stored DTO, does not mutate state.
        Returns None if not found.
        """
        return self._drafts.get(draft_id)
    
    def save_bundle(self, bundle: DraftBundleDTO) -> None:
        """
        Save draft bundle with assets to memory.
        
        Idempotency: If bundle_id exists, overwrites (same as merge() in DB repo).
        Assets: Stores each asset separately with bundle_id reference.
        """
        self._bundles[bundle.bundle_id] = bundle
        
        # Store assets separately for retrieval
        asset_ids = []
        for asset in bundle.assets:
            self._assets[asset.asset_id] = asset
            asset_ids.append(asset.asset_id)
        
        self._bundle_assets[bundle.bundle_id] = asset_ids
    
    def get_bundle(self, bundle_id: str) -> Optional[DraftBundleDTO]:
        """
        Retrieve a bundle by bundle_id with all associated assets.
        
        Read-Only: Returns stored DTO with assets, does not mutate state.
        Returns None if not found.
        """
        bundle = self._bundles.get(bundle_id)
        if not bundle:
            return None
        
        # Reconstruct bundle with current assets (in case assets were updated separately)
        asset_ids = self._bundle_assets.get(bundle_id, [])
        assets = [self._assets[aid] for aid in asset_ids if aid in self._assets]
        
        # Return bundle with current assets
        return DraftBundleDTO(
            bundle_id=bundle.bundle_id,
            draft_id=bundle.draft_id,
            assets=assets,
            assembled_at=bundle.assembled_at,
        )
    
    def clear(self) -> None:
        """Clear all stored data (useful for test cleanup)."""
        self._drafts.clear()
        self._bundles.clear()
        self._assets.clear()
        self._bundle_assets.clear()
