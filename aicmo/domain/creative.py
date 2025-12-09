"""Creative domain models with database persistence mapping.

Stage 2: CreativeAsset wraps CreativeAssetDB for database persistence
while maintaining domain logic separation.
"""

from typing import Optional, Dict, Any
from datetime import datetime

from .base import AicmoBaseModel
from aicmo.domain.execution import CreativeVariant


class CreativeAsset(AicmoBaseModel):
    """
    Domain model for a persisted creative asset.
    
    Stage 2: Extends CreativeVariant with persistence fields:
    - Database ID
    - Campaign linkage
    - Publish status tracking
    - Scheduling information
    """
    
    id: Optional[int] = None
    campaign_id: Optional[int] = None
    
    # Creative content (from CreativeVariant)
    platform: str
    format: str
    hook: str
    caption: Optional[str] = None
    cta: Optional[str] = None
    tone: Optional[str] = None
    
    # Publishing tracking
    publish_status: str = "DRAFT"  # DRAFT, APPROVED, SCHEDULED, PUBLISHED
    scheduled_date: Optional[str] = None
    published_at: Optional[datetime] = None
    
    # Metadata
    meta: Optional[Dict[str, Any]] = None
    
    @classmethod
    def from_variant(
        cls,
        variant: CreativeVariant,
        campaign_id: Optional[int] = None
    ) -> "CreativeAsset":
        """
        Create CreativeAsset from CreativeVariant.
        
        Args:
            variant: Source CreativeVariant
            campaign_id: Optional campaign to link to
            
        Returns:
            CreativeAsset ready for persistence
        """
        return cls(
            campaign_id=campaign_id,
            platform=variant.platform,
            format=variant.format,
            hook=variant.hook,
            caption=variant.caption,
            cta=variant.cta,
            tone=variant.tone,
            publish_status="DRAFT"
        )
    
    @classmethod
    def from_db(cls, db_asset) -> "CreativeAsset":
        """
        Create CreativeAsset from CreativeAssetDB.
        
        Args:
            db_asset: CreativeAssetDB instance
            
        Returns:
            CreativeAsset domain model
        """
        return cls(
            id=db_asset.id,
            campaign_id=db_asset.campaign_id,
            platform=db_asset.platform,
            format=db_asset.format,
            hook=db_asset.hook,
            caption=db_asset.caption,
            cta=db_asset.cta,
            tone=db_asset.tone,
            publish_status=db_asset.publish_status,
            scheduled_date=db_asset.scheduled_date,
            published_at=db_asset.published_at,
            meta=db_asset.meta
        )
    
    def apply_to_db(self, db_asset) -> None:
        """
        Apply CreativeAsset state to CreativeAssetDB instance.
        
        Args:
            db_asset: CreativeAssetDB instance to update
        """
        db_asset.campaign_id = self.campaign_id
        db_asset.platform = self.platform
        db_asset.format = self.format
        db_asset.hook = self.hook
        db_asset.caption = self.caption
        db_asset.cta = self.cta
        db_asset.tone = self.tone
        db_asset.publish_status = self.publish_status
        db_asset.scheduled_date = self.scheduled_date
        db_asset.published_at = self.published_at
        db_asset.meta = self.meta
    
    def to_variant(self) -> CreativeVariant:
        """
        Convert CreativeAsset back to CreativeVariant.
        
        Returns:
            CreativeVariant for use in non-persistent contexts
        """
        return CreativeVariant(
            platform=self.platform,
            format=self.format,
            hook=self.hook,
            caption=self.caption,
            cta=self.cta,
            tone=self.tone
        )
