"""Creative generation service.

Phase 3: Wraps existing backend creative generation and provides
asset library management for organizing content variants.
"""

from typing import List, Optional
from datetime import date

from aicmo.domain.strategy import StrategyDoc
from aicmo.domain.execution import CreativeVariant, ContentItem
from aicmo.domain.intake import ClientIntake


class CreativeLibrary:
    """
    Manages a library of creative variants for a project.
    
    Phase 3: Provides organization and retrieval of creative assets
    by platform, format, and tone.
    """
    
    def __init__(self):
        self.variants: List[CreativeVariant] = []
    
    def add_variant(self, variant: CreativeVariant) -> None:
        """Add a creative variant to the library."""
        self.variants.append(variant)
    
    def get_by_platform(self, platform: str) -> List[CreativeVariant]:
        """Get all variants for a specific platform."""
        return [v for v in self.variants if v.platform.lower() == platform.lower()]
    
    def get_by_format(self, format: str) -> List[CreativeVariant]:
        """Get all variants of a specific format."""
        return [v for v in self.variants if v.format.lower() == format.lower()]
    
    def get_by_tone(self, tone: str) -> List[CreativeVariant]:
        """Get all variants with a specific tone."""
        return [v for v in self.variants if v.tone and v.tone.lower() == tone.lower()]
    
    def to_content_items(
        self,
        project_id: Optional[int] = None,
        scheduled_date: Optional[str] = None
    ) -> List[ContentItem]:
        """
        Convert creative variants to executable content items.
        
        Args:
            project_id: Optional project ID to associate
            scheduled_date: Optional date for scheduling
            
        Returns:
            List of ContentItem ready for execution
        """
        items = []
        for variant in self.variants:
            body = variant.caption or variant.hook
            if variant.cta:
                body += f"\n\n{variant.cta}"
            
            item = ContentItem(
                project_id=project_id,
                platform=variant.platform,
                title=variant.hook[:100] if len(variant.hook) > 100 else variant.hook,
                body_text=body,
                hook=variant.hook,
                caption=variant.caption,
                cta=variant.cta,
                asset_type=variant.format,
                scheduled_date=scheduled_date,
            )
            items.append(item)
        
        return items


async def generate_creatives(
    intake: ClientIntake,
    strategy: StrategyDoc,
    platforms: Optional[List[str]] = None
) -> CreativeLibrary:
    """
    Generate creative variants from strategy.
    
    Phase 3 Implementation:
    - Creates platform-specific creative variants
    - Uses strategy pillars to inform messaging
    - Generates hooks, captions, CTAs for each platform
    - Returns organized CreativeLibrary
    
    Args:
        intake: Client intake data
        strategy: Approved strategy document
        platforms: Optional list of platforms (defaults to Instagram, LinkedIn, Twitter)
        
    Returns:
        CreativeLibrary with organized variants
    """
    if platforms is None:
        platforms = ["instagram", "linkedin", "twitter"]
    
    library = CreativeLibrary()
    
    # Phase 3: Generate creative variants based on strategy pillars
    # For now, create stub variants to demonstrate structure
    # Phase 3.1 will integrate with backend creative generators
    
    for platform in platforms:
        # For each strategy pillar, create a content variant
        for i, pillar in enumerate(strategy.pillars[:3]):  # Top 3 pillars
            # Determine format based on platform
            if platform.lower() == "instagram":
                format_type = "reel" if i == 0 else "static_post"
            elif platform.lower() == "linkedin":
                format_type = "post"
            elif platform.lower() == "twitter":
                format_type = "thread"
            else:
                format_type = "post"
            
            # Create hook based on pillar
            hook = f"{pillar.name}: {pillar.description[:80]}..."
            caption = f"Focused on {strategy.primary_goal or 'growth'}. {pillar.kpi_impact}"
            cta = "Learn more" if i == 0 else ("Get started" if i == 1 else "See how it works")
            
            variant = CreativeVariant(
                platform=platform,
                format=format_type,
                hook=hook,
                caption=caption,
                cta=cta,
                tone="professional" if i == 0 else ("friendly" if i == 1 else "bold")
            )
            library.add_variant(variant)
    
    return library
