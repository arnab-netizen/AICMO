"""Creative generation service.

Phase 3: Wraps existing backend creative generation and provides
asset library management for organizing content variants.
"""

from typing import List, Optional
from datetime import date, datetime
import uuid

from aicmo.domain.strategy import StrategyDoc
from aicmo.domain.execution import CreativeVariant, ContentItem
from aicmo.domain.intake import ClientIntake
from aicmo.learning.kaizen_service import KaizenContext
from aicmo.memory.engine import log_event
from aicmo.learning.event_types import EventType


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
    platforms: Optional[List[str]] = None,
    campaign_id: Optional[int] = None,
    session = None,
    kaizen: Optional[KaizenContext] = None
) -> CreativeLibrary:
    """
    Generate creative variants from strategy.
    
    Phase 3 Implementation:
    - Creates platform-specific creative variants
    - Uses strategy pillars to inform messaging
    - Generates hooks, captions, CTAs for each platform
    - Returns organized CreativeLibrary
    
    Stage K2: Uses Kaizen to avoid rejected patterns and favor successful hooks
    Action 4: Accepts kaizen_context to inform creative generation with past learnings
    
    Args:
        intake: Client intake data
        strategy: Approved strategy document
        platforms: Optional list of platforms (defaults to Instagram, LinkedIn, Twitter)
        campaign_id: Optional campaign ID for persistence
        session: Optional SQLAlchemy session for persistence
        kaizen_context: Optional Kaizen learnings to influence creative generation
        
    Returns:
        CreativeLibrary with organized variants
        
    Kaizen Usage:
        If kaizen_context provided:
        - Uses preferred_platforms to prioritize platform selection
        - Uses recommended_tones to influence tone choices
        - Uses high_performing_hooks to inspire hook generation
        - Avoids risky_patterns and banned_phrases
    """
    # Stage K2: Apply Kaizen insights to platform selection
    if platforms is None:
        if kaizen and kaizen.best_channels:
            # Prioritize channels/platforms that have performed well
            platforms = [ch for ch in kaizen.best_channels[:3] if ch in ["instagram", "linkedin", "twitter", "facebook", "youtube"]]
            if not platforms:
                platforms = ["instagram", "linkedin", "twitter"]
        else:
            platforms = ["instagram", "linkedin", "twitter"]
    
    library = CreativeLibrary()
    
    # Stage K2: Check for rejected patterns to avoid
    avoided_hooks = []
    if kaizen and kaizen.rejected_patterns:
        avoided_hooks = [p.get("pattern", "") for p in kaizen.rejected_patterns[:3]]
        logger.info(f"Kaizen: Avoiding {len(avoided_hooks)} rejected patterns")
    
    # Use successful hooks if available
    successful_hooks = []
    if kaizen and kaizen.successful_hooks:
        successful_hooks = kaizen.successful_hooks[:3]
        logger.info(f"Kaizen: Applying {len(successful_hooks)} successful hooks")
    
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
            
            # Stage K2: Use successful hooks or create new ones avoiding rejected patterns
            if successful_hooks and i < len(successful_hooks):
                hook = f"{successful_hooks[i]}: {pillar.description[:60]}..."
            else:
                hook = f"{pillar.name}: {pillar.description[:80]}..."
            
            # Ensure we're not using a rejected pattern
            for avoided in avoided_hooks:
                if avoided.lower() in hook.lower():
                    hook = f"Innovative approach: {pillar.description[:70]}..."
                    break
            
            caption = f"Focused on {strategy.primary_goal or 'growth'}. {pillar.kpi_impact}"
            cta = "Learn more" if i == 0 else ("Get started" if i == 1 else "See how it works")
            
            # Stage K2: Apply effective tones from Kaizen
            if kaizen and kaizen.effective_tones:
                tone = kaizen.effective_tones[i % len(kaizen.effective_tones)]
            else:
                tone = "professional" if i == 0 else ("friendly" if i == 1 else "bold")
            
            variant = CreativeVariant(
                platform=platform,
                format=format_type,
                hook=hook,
                caption=caption,
                cta=cta,
                tone=tone
            )
            library.add_variant(variant)
            
            # Stage 2: Persist to database if campaign_id and session provided
            if campaign_id is not None and session is not None:
                from aicmo.cam.db_models import CreativeAssetDB
                from aicmo.domain.creative import CreativeAsset
                
                asset = CreativeAsset.from_variant(variant, campaign_id=campaign_id)
                db_asset = CreativeAssetDB()
                asset.apply_to_db(db_asset)
                session.add(db_asset)
    
    # Validate creatives before returning (G1: contracts layer)
    from aicmo.core.contracts import validate_creative_assets
    validate_creative_assets(library.variants)
    
    # Stage K2: Log creatives generation event with Kaizen usage
    from aicmo.memory.engine import log_event
    log_event(
        "CREATIVES_GENERATED",
        project_id=f"campaign_{campaign_id}" if campaign_id else intake.brand_name,
        details={
            "variants_count": len(library.variants),
            "platforms": platforms,
            "persisted": campaign_id is not None and session is not None,
            "kaizen_influenced": kaizen is not None,
            "avoided_patterns": len(avoided_hooks) if kaizen else 0,
            "used_successful_hooks": len(successful_hooks) if kaizen else 0
        },
        tags=["creatives", "success"]
    )
    
    return library


# ═══════════════════════════════════════════════════════════════════════
# Stage C: Advanced Creative Production Functions
# ═══════════════════════════════════════════════════════════════════════

import logging

from aicmo.creatives.domain import (
    VideoSpec,
    MotionGraphicsSpec,
    Moodboard,
    MoodboardItem,
    Storyboard,
    CreativeProject,
    VideoStyle,
    AspectRatio,
)

logger = logging.getLogger(__name__)


def generate_video_storyboard(
    intake: ClientIntake,
    video_purpose: str,
    duration_seconds: int = 30,
    aspect_ratio: AspectRatio = AspectRatio.HORIZONTAL
) -> Storyboard:
    """
    Generate a video storyboard from client intake.
    
    Stage C: Skeleton with basic scene structure.
    Future: Use LLM to generate compelling narrative arcs.
    
    Args:
        intake: Client intake data
        video_purpose: Purpose of the video
        duration_seconds: Target duration
        aspect_ratio: Video aspect ratio
        
    Returns:
        Storyboard with scene breakdown
    """
    logger.info(f"Generating video storyboard for {intake.brand_name}")
    
    # Stage C: Basic 3-scene structure
    scenes = _generate_basic_scenes(intake, duration_seconds)
    
    storyboard = Storyboard(
        title=f"{intake.brand_name} - {video_purpose}",
        brand_name=intake.brand_name,
        video_purpose=video_purpose,
        total_duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        scenes=scenes,
        creative_notes=f"Storyboard for {intake.industry or 'general'} industry",
        created_at=datetime.now()
    )
    
    # Learning: Log storyboard creation
    log_event(
        EventType.ADV_CREATIVE_STORYBOARD_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "video_purpose": video_purpose,
            "duration_seconds": duration_seconds,
            "num_scenes": len(scenes)
        },
        tags=["creative", "video", "storyboard"]
    )
    
    logger.info(f"Generated storyboard with {len(scenes)} scenes")
    return storyboard


def generate_moodboard(
    intake: ClientIntake,
    purpose: str = "Brand identity",
    aesthetic: str = "modern"
) -> Moodboard:
    """
    Generate a creative moodboard for brand/campaign inspiration.
    
    Stage C: Skeleton with placeholder items.
    Future: Integrate with image generation/search APIs.
    
    Args:
        intake: Client intake data
        purpose: Moodboard purpose
        aesthetic: Overall aesthetic direction
        
    Returns:
        Moodboard with inspiration items
    """
    logger.info(f"Generating moodboard for {intake.brand_name}")
    
    # Stage C: Generate placeholder moodboard items
    items = _generate_moodboard_items(intake, aesthetic)
    
    moodboard = Moodboard(
        title=f"{intake.brand_name} - {purpose}",
        brand_name=intake.brand_name,
        purpose=purpose,
        items=items,
        overall_aesthetic=aesthetic,
        color_palette=_derive_color_palette(intake, aesthetic),
        keywords=_derive_moodboard_keywords(intake),
        created_at=datetime.now()
    )
    
    # Learning: Log moodboard creation
    log_event(
        EventType.ADV_CREATIVE_MOODBOARD_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "purpose": purpose,
            "aesthetic": aesthetic,
            "num_items": len(items)
        },
        tags=["creative", "moodboard", "design"]
    )
    
    logger.info(f"Generated moodboard with {len(items)} items")
    return moodboard


def generate_motion_graphics_spec(
    intake: ClientIntake,
    key_messages: List[str],
    duration_seconds: int = 15,
    aspect_ratio: AspectRatio = AspectRatio.SQUARE
) -> MotionGraphicsSpec:
    """
    Generate motion graphics specifications.
    
    Stage C: Skeleton with basic specs.
    Future: AI-driven animation style selection.
    
    Args:
        intake: Client intake data
        key_messages: Key messages to animate
        duration_seconds: Target duration
        aspect_ratio: Aspect ratio for output
        
    Returns:
        MotionGraphicsSpec with animation parameters
    """
    logger.info(f"Generating motion graphics spec for {intake.brand_name}")
    
    spec = MotionGraphicsSpec(
        duration_seconds=duration_seconds,
        aspect_ratio=aspect_ratio,
        key_messages=key_messages,
        color_palette=_derive_color_palette(intake, "modern"),
        animation_style=_select_animation_style(intake),
        typography_style="modern"
    )
    
    # Learning: Log motion graphics spec
    log_event(
        EventType.ADV_CREATIVE_MOTION_GENERATED.value,
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "duration_seconds": duration_seconds,
            "num_messages": len(key_messages)
        },
        tags=["creative", "motion", "animation"]
    )
    
    logger.info(f"Generated motion graphics spec with {len(key_messages)} messages")
    return spec


def create_creative_project(
    intake: ClientIntake,
    project_name: str,
    deliverables: List[str]
) -> CreativeProject:
    """
    Create a creative production project.
    
    Stage C: Skeleton for project management.
    Future: Integrate with project tracking tools.
    
    Args:
        intake: Client intake data
        project_name: Name of the project
        deliverables: List of required deliverables
        
    Returns:
        CreativeProject with initial setup
    """
    logger.info(f"Creating creative project for {intake.brand_name}")
    
    project = CreativeProject(
        project_id=str(uuid.uuid4()),
        brand_name=intake.brand_name,
        project_name=project_name,
        deliverables=deliverables,
        created_at=datetime.now(),
        status="planning"
    )
    
    # Learning: Log project creation
    log_event(
        EventType.ADV_CREATIVE_STORYBOARD_GENERATED.value,  # Placeholder for project event
        project_id=intake.brand_name,
        details={
            "brand_name": intake.brand_name,
            "project_name": project_name,
            "num_deliverables": len(deliverables)
        },
        tags=["creative", "project", "production"]
    )
    
    logger.info(f"Created creative project with {len(deliverables)} deliverables")
    return project


# ═══════════════════════════════════════════════════════════════════════
# Stage C: Helper Functions
# ═══════════════════════════════════════════════════════════════════════


def _generate_basic_scenes(intake: ClientIntake, duration: int) -> List[dict]:
    """Generate basic 3-act scene structure."""
    scene_duration = duration // 3
    
    return [
        {
            "scene_number": 1,
            "duration_seconds": scene_duration,
            "description": f"Opening: Introduce {intake.brand_name} and problem",
            "visuals": "Brand logo, problem visualization",
            "audio": "Upbeat music, voiceover intro"
        },
        {
            "scene_number": 2,
            "duration_seconds": scene_duration,
            "description": f"Solution: Show {intake.product_service or 'solution'}",
            "visuals": "Product/service in action, benefits",
            "audio": "Engaging explanation, demo"
        },
        {
            "scene_number": 3,
            "duration_seconds": scene_duration,
            "description": "Call to action and brand reinforcement",
            "visuals": "Clear CTA, contact info, logo",
            "audio": "Strong CTA, memorable tagline"
        }
    ]


def _generate_moodboard_items(intake: ClientIntake, aesthetic: str) -> List[MoodboardItem]:
    """Generate placeholder moodboard items."""
    items = []
    
    items.append(MoodboardItem(
        image_description=f"{aesthetic.title()} color palette for {intake.industry or 'brand'}",
        category="color",
        notes="Primary and secondary colors"
    ))
    
    items.append(MoodboardItem(
        image_description=f"{aesthetic.title()} typography examples",
        category="typography",
        notes="Headline and body font pairings"
    ))
    
    items.append(MoodboardItem(
        image_description=f"{intake.industry or 'Industry'}-specific imagery style",
        category="imagery",
        notes="Photography direction and style"
    ))
    
    items.append(MoodboardItem(
        image_description=f"{aesthetic.title()} layout composition",
        category="layout",
        notes="Grid systems and spacing"
    ))
    
    return items


def _derive_color_palette(intake: ClientIntake, aesthetic: str) -> List[str]:
    """Derive color palette based on aesthetic."""
    palettes = {
        "modern": ["#2563EB", "#10B981", "#F59E0B", "#EF4444"],
        "minimal": ["#1F2937", "#9CA3AF", "#F3F4F6", "#FFFFFF"],
        "energetic": ["#EC4899", "#8B5CF6", "#F97316", "#FBBF24"],
        "professional": ["#1E40AF", "#059669", "#DC2626", "#6B7280"]
    }
    return palettes.get(aesthetic, palettes["modern"])


def _derive_moodboard_keywords(intake: ClientIntake) -> List[str]:
    """Derive moodboard search keywords from intake."""
    keywords = []
    
    if intake.industry:
        keywords.append(intake.industry.lower())
    
    if intake.product_service:
        keywords.append(intake.product_service.lower())
    
    keywords.extend(["professional", "modern", "clean"])
    
    return keywords[:6]


def _select_animation_style(intake: ClientIntake) -> str:
    """Select animation style based on brand context."""
    if intake.industry and "tech" in intake.industry.lower():
        return "energetic"
    elif intake.industry and "finance" in intake.industry.lower():
        return "smooth"
    else:
        return "smooth"

