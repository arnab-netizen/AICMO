"""Production module - Internal adapters (MVP)."""
from datetime import datetime
from typing import Protocol, Optional
from aicmo.production.api.ports import DraftGeneratePort, AssetAssemblePort, ProductionQueryPort
from aicmo.production.api.dtos import ContentDraftDTO, AssetDTO, DraftBundleDTO
from aicmo.shared.ids import StrategyId, DraftId, AssetId


class ProductionRepository(Protocol):
    """
    Repository protocol for production persistence.
    
    Implemented by:
    - DatabaseProductionRepo (aicmo.production.internal.repositories_db)
    - InMemoryProductionRepo (aicmo.production.internal.repositories_mem)
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


class DraftGenerateAdapter(DraftGeneratePort):
    """Minimal draft generation adapter."""
    
    def __init__(self, repo: ProductionRepository):
        self._repo = repo
    
    def generate_draft(self, strategy_id: StrategyId) -> ContentDraftDTO:
        """
        Generate content draft from strategy.
        
        MVP: Returns deterministic sample content.
        """
        draft_id = DraftId(f"draft_{strategy_id}_{int(datetime.utcnow().timestamp())}")
        
        draft = ContentDraftDTO(
            draft_id=draft_id,
            strategy_id=strategy_id,
            content_type="blog_post",
            body="# B2B Marketing Trends 2024\n\nThis is a sample blog post draft for your content strategy...",
            metadata={
                "word_count": 1500,
                "target_keywords": ["B2B marketing", "digital transformation"],
                "tone": "professional",
            },
            created_at=datetime.utcnow(),
        )
        
        self._repo.save_draft(draft)
        return draft


class AssetAssembleAdapter(AssetAssemblePort):
    """Minimal asset assembly adapter."""
    
    def __init__(self, repo: ProductionRepository):
        self._repo = repo
    
    def assemble_bundle(self, draft_id: DraftId) -> DraftBundleDTO:
        """Assemble draft with assets into bundle."""
        bundle_id = f"bundle_{draft_id}_{int(datetime.utcnow().timestamp())}"
        
        # MVP: Include sample assets
        assets = [
            AssetDTO(
                asset_id=AssetId(f"asset_img_{bundle_id}"),
                asset_type="image",
                url="https://example.com/hero-image.jpg",
                metadata={"width": 1200, "height": 630},
            ),
            AssetDTO(
                asset_id=AssetId(f"asset_pdf_{bundle_id}"),
                asset_type="pdf",
                url="https://example.com/draft.pdf",
                metadata={"pages": 5},
            ),
        ]
        
        bundle = DraftBundleDTO(
            bundle_id=bundle_id,
            draft_id=draft_id,
            assets=assets,
            assembled_at=datetime.utcnow(),
        )
        
        self._repo.save_bundle(bundle)
        return bundle


class ProductionQueryAdapter(ProductionQueryPort):
    """Minimal query adapter."""
    
    def __init__(self, repo: ProductionRepository):
        self._repo = repo
    
    def get_draft(self, draft_id: DraftId) -> ContentDraftDTO:
        draft = self._repo.get_draft(draft_id)
        if not draft:
            raise ValueError(f"Draft {draft_id} not found")
        return draft
