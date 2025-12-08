"""Phase 3 tests: Creatives and Asset Librarian.

Verifies that:
1. CreativeVariant model works correctly
2. ContentItem enhanced with creative fields
3. CreativeLibrary manages asset organization
4. generate_creatives produces platform-specific variants
5. Integration with strategy service works
6. No breaking changes to existing backend
"""

import pytest
from unittest.mock import AsyncMock, patch

from aicmo.domain.execution import CreativeVariant, ContentItem, PublishStatus
from aicmo.domain.strategy import StrategyDoc, StrategyPillar
from aicmo.domain.intake import ClientIntake
from aicmo.creatives.service import CreativeLibrary, generate_creatives


class TestPhase3CreativeModels:
    """Phase 3: Creative domain model tests."""

    def test_creative_variant_creation(self):
        """CreativeVariant can be created with required fields."""
        variant = CreativeVariant(
            platform="instagram",
            format="reel",
            hook="Compelling hook for Instagram Reel",
            caption="Full caption with engaging content",
            cta="Swipe up to learn more",
            tone="friendly"
        )
        
        assert variant.platform == "instagram"
        assert variant.format == "reel"
        assert "Compelling hook" in variant.hook
        assert variant.cta == "Swipe up to learn more"
        assert variant.tone == "friendly"

    def test_content_item_with_creative_fields(self):
        """ContentItem now has creative-specific fields."""
        item = ContentItem(
            platform="linkedin",
            body_text="Full post content",
            hook="Professional hook",
            caption="Detailed caption with insights",
            cta="Connect with us",
            asset_type="post",
            scheduled_date="2024-12-15",
            theme="Thought Leadership"
        )
        
        assert item.platform == "linkedin"
        assert item.hook == "Professional hook"
        assert item.caption == "Detailed caption with insights"
        assert item.cta == "Connect with us"
        assert item.asset_type == "post"
        assert item.scheduled_date == "2024-12-15"
        assert item.theme == "Thought Leadership"
        assert item.publish_status == PublishStatus.DRAFT


class TestPhase3CreativeLibrary:
    """Phase 3: CreativeLibrary tests."""

    def test_library_add_variant(self):
        """Library can store creative variants."""
        library = CreativeLibrary()
        
        variant1 = CreativeVariant(
            platform="instagram",
            format="reel",
            hook="Test hook 1"
        )
        variant2 = CreativeVariant(
            platform="linkedin",
            format="post",
            hook="Test hook 2"
        )
        
        library.add_variant(variant1)
        library.add_variant(variant2)
        
        assert len(library.variants) == 2

    def test_library_get_by_platform(self):
        """Library can filter variants by platform."""
        library = CreativeLibrary()
        
        library.add_variant(CreativeVariant(platform="instagram", format="reel", hook="IG 1"))
        library.add_variant(CreativeVariant(platform="instagram", format="post", hook="IG 2"))
        library.add_variant(CreativeVariant(platform="linkedin", format="post", hook="LI 1"))
        
        ig_variants = library.get_by_platform("instagram")
        assert len(ig_variants) == 2
        assert all(v.platform == "instagram" for v in ig_variants)

    def test_library_get_by_format(self):
        """Library can filter variants by format."""
        library = CreativeLibrary()
        
        library.add_variant(CreativeVariant(platform="instagram", format="reel", hook="Reel 1"))
        library.add_variant(CreativeVariant(platform="instagram", format="reel", hook="Reel 2"))
        library.add_variant(CreativeVariant(platform="linkedin", format="post", hook="Post 1"))
        
        reels = library.get_by_format("reel")
        assert len(reels) == 2
        assert all(v.format == "reel" for v in reels)

    def test_library_get_by_tone(self):
        """Library can filter variants by tone."""
        library = CreativeLibrary()
        
        library.add_variant(CreativeVariant(platform="instagram", format="post", hook="H1", tone="professional"))
        library.add_variant(CreativeVariant(platform="linkedin", format="post", hook="H2", tone="professional"))
        library.add_variant(CreativeVariant(platform="twitter", format="thread", hook="H3", tone="friendly"))
        
        professional = library.get_by_tone("professional")
        assert len(professional) == 2
        assert all(v.tone == "professional" for v in professional)

    def test_library_to_content_items(self):
        """Library can convert variants to executable content items."""
        library = CreativeLibrary()
        
        library.add_variant(CreativeVariant(
            platform="instagram",
            format="reel",
            hook="Amazing hook",
            caption="Full caption text",
            cta="Learn more"
        ))
        library.add_variant(CreativeVariant(
            platform="linkedin",
            format="post",
            hook="Professional insight",
            caption="Detailed analysis"
        ))
        
        items = library.to_content_items(project_id=123, scheduled_date="2024-12-20")
        
        assert len(items) == 2
        assert all(isinstance(item, ContentItem) for item in items)
        assert all(item.project_id == 123 for item in items)
        assert all(item.scheduled_date == "2024-12-20" for item in items)
        assert items[0].platform == "instagram"
        assert items[0].hook == "Amazing hook"
        assert "Learn more" in items[0].body_text


class TestPhase3GenerateCreatives:
    """Phase 3: Creative generation service tests."""

    @pytest.mark.asyncio
    async def test_generate_creatives_basic(self):
        """generate_creatives creates platform-specific variants."""
        intake = ClientIntake(
            brand_name="Creative Test Co",
            industry="SaaS",
            primary_goal="Brand awareness"
        )
        
        strategy = StrategyDoc(
            brand_name="Creative Test Co",
            industry="SaaS",
            executive_summary="Summary",
            situation_analysis="Analysis",
            strategy_narrative="Strategy",
            pillars=[
                StrategyPillar(name="Awareness", description="Build brand recognition", kpi_impact="Reach +50%"),
                StrategyPillar(name="Trust", description="Establish credibility", kpi_impact="Engagement +30%"),
                StrategyPillar(name="Conversion", description="Drive signups", kpi_impact="Leads +40%"),
            ]
        )
        
        library = await generate_creatives(intake, strategy)
        
        assert len(library.variants) > 0
        assert len(library.get_by_platform("instagram")) > 0
        assert len(library.get_by_platform("linkedin")) > 0
        assert len(library.get_by_platform("twitter")) > 0

    @pytest.mark.asyncio
    async def test_generate_creatives_uses_strategy_pillars(self):
        """Creatives are informed by strategy pillars."""
        intake = ClientIntake(brand_name="Test")
        
        strategy = StrategyDoc(
            brand_name="Test",
            executive_summary="S",
            situation_analysis="A",
            strategy_narrative="S",
            pillars=[
                StrategyPillar(name="Innovation", description="Lead with innovation", kpi_impact="Growth"),
            ]
        )
        
        library = await generate_creatives(intake, strategy)
        
        # At least one variant should reference the pillar
        all_hooks = [v.hook for v in library.variants]
        assert any("Innovation" in hook for hook in all_hooks)

    @pytest.mark.asyncio
    async def test_generate_creatives_custom_platforms(self):
        """generate_creatives accepts custom platform list."""
        intake = ClientIntake(brand_name="Test")
        strategy = StrategyDoc(
            brand_name="Test",
            executive_summary="S",
            situation_analysis="A",
            strategy_narrative="S",
            pillars=[StrategyPillar(name="P1", description="D1", kpi_impact="K1")]
        )
        
        library = await generate_creatives(intake, strategy, platforms=["tiktok", "youtube"])
        
        assert len(library.get_by_platform("tiktok")) > 0
        assert len(library.get_by_platform("youtube")) > 0
        assert len(library.get_by_platform("instagram")) == 0  # Not in custom list

    @pytest.mark.asyncio
    async def test_generate_creatives_different_tones(self):
        """Creatives include different tone variations."""
        intake = ClientIntake(brand_name="Test")
        strategy = StrategyDoc(
            brand_name="Test",
            executive_summary="S",
            situation_analysis="A",
            strategy_narrative="S",
            pillars=[
                StrategyPillar(name="P1", description="D1", kpi_impact="K1"),
                StrategyPillar(name="P2", description="D2", kpi_impact="K2"),
                StrategyPillar(name="P3", description="D3", kpi_impact="K3"),
            ]
        )
        
        library = await generate_creatives(intake, strategy)
        
        tones = {v.tone for v in library.variants if v.tone}
        assert "professional" in tones
        assert "friendly" in tones
        assert "bold" in tones


class TestPhase3Integration:
    """Phase 3: Integration with previous phases."""

    @pytest.mark.asyncio
    async def test_full_workflow_intake_to_creatives(self):
        """End-to-end: Intake → Strategy → Creatives."""
        # 1. Create intake
        intake = ClientIntake(
            brand_name="Full Integration Co",
            industry="FinTech",
            primary_goal="User acquisition"
        )
        
        # 2. Generate strategy (mocked)
        from aicmo.io.client_reports import MarketingPlanView, StrategyPillar as BackendPillar
        
        mock_plan = MarketingPlanView(
            executive_summary="Executive summary",
            situation_analysis="Market analysis",
            strategy="Strategic approach",
            pillars=[
                BackendPillar(name="Awareness", description="Build recognition", kpi_impact="Reach +50%"),
                BackendPillar(name="Trust", description="Build credibility", kpi_impact="Engagement +30%"),
            ]
        )
        
        with patch("backend.generators.marketing_plan.generate_marketing_plan", new=AsyncMock(return_value=mock_plan)):
            from aicmo.strategy.service import generate_strategy
            strategy = await generate_strategy(intake)
        
        # 3. Generate creatives from strategy
        library = await generate_creatives(intake, strategy)
        
        # Verify full workflow
        assert strategy.brand_name == "Full Integration Co"
        assert len(strategy.pillars) == 2
        assert len(library.variants) > 0
        
        # Creatives reference strategy
        assert any("Awareness" in v.hook for v in library.variants)
        
        # Convert to executable content
        items = library.to_content_items(project_id=1)
        assert len(items) > 0
        assert all(item.publish_status == PublishStatus.DRAFT for item in items)
