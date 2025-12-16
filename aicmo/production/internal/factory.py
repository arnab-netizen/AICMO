"""
Production module repository factory.

Selects production repository implementation based on persistence mode.
Uses same config mechanism as onboarding/strategy modules.
"""

from typing import Protocol, Optional
from aicmo.shared.config import is_db_mode
from aicmo.production.api.dtos import ContentDraftDTO, DraftBundleDTO
from aicmo.shared.ids import DraftId


class ProductionRepository(Protocol):
    """
    Repository protocol for production persistence.
    
    Both DatabaseProductionRepo and InMemoryProductionRepo implement this interface.
    """
    
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


def create_production_repository() -> ProductionRepository:
    """
    Factory function to create production repository based on persistence mode.
    
    Uses aicmo.shared.config.is_db_mode() to determine mode:
    - db: Returns DatabaseProductionRepo
    - inmemory: Returns InMemoryProductionRepo (default)
    
    Same pattern as onboarding/strategy factories.
    """
    if is_db_mode():
        from aicmo.production.internal.repositories_db import DatabaseProductionRepo
        return DatabaseProductionRepo()
    else:
        from aicmo.production.internal.repositories_mem import InMemoryProductionRepo
        return InMemoryProductionRepo()
