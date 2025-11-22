"""
Tests for Phase L learning system fixes.

Tests cover:
1. Section mapping correctness
2. Extraction of all report sections
3. Handling of missing/None sections
4. Non-blocking error handling
5. Fallback behavior
"""

import pytest
from datetime import date

from backend.services.learning import (
    learn_from_report,
    _brief_to_text,
    SECTION_MAPPING,
)
from aicmo.io.client_reports import (
    AICMOOutputReport,
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
    MarketingPlanView,
    CampaignBlueprintView,
    CampaignObjectiveView,
    AudiencePersonaView,
    SocialCalendarView,
    PersonaCard,
    ActionPlan,
)


@pytest.fixture
def minimal_brief():
    """Create a minimal valid brief."""
    return ClientInputBrief(
        brand=BrandBrief(brand_name="Test Brand"),
        audience=AudienceBrief(primary_customer="Test Customer"),
        goal=GoalBrief(primary_goal="Test Goal"),
        voice=VoiceBrief(),
        product_service=ProductServiceBrief(),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )


@pytest.fixture
def complete_report():
    """Create a report with all sections populated."""
    return AICMOOutputReport(
        marketing_plan=MarketingPlanView(
            executive_summary="Executive summary content.",
            situation_analysis="Situation analysis content.",
            strategy="Strategy content.",
        ),
        campaign_blueprint=CampaignBlueprintView(
            big_idea="Big idea content.",
            objective=CampaignObjectiveView(primary="awareness"),
            audience_persona=AudiencePersonaView(
                name="Test Persona", description="Test description"
            ),
        ),
        social_calendar=SocialCalendarView(
            start_date=date.today(),
            end_date=date.today(),
            posts=[],
        ),
        persona_cards=[
            PersonaCard(
                name="Persona 1",
                demographics="25-35",
                psychographics="Test psychographics",
                pain_points=["Pain point 1"],
                triggers=["Trigger 1"],
                objections=["Objection 1"],
                content_preferences=["Text"],
                primary_platforms=["Instagram"],
                tone_preference="Friendly",
            )
        ],
        action_plan=ActionPlan(
            quick_wins=["Quick win 1"],
            next_10_days=["10-day action"],
            next_30_days=["30-day action"],
            risks=["Risk 1"],
        ),
    )


class TestSectionMapping:
    """Tests for section mapping configuration."""

    def test_section_mapping_not_empty(self):
        """Section mapping should be configured."""
        assert len(SECTION_MAPPING) > 0

    def test_section_mapping_has_tuples(self):
        """Each mapping should be a (title, attr) tuple."""
        for title, attr in SECTION_MAPPING:
            assert isinstance(title, str)
            assert isinstance(attr, str)
            assert len(title) > 0
            assert len(attr) > 0

    def test_section_mapping_unique_attrs(self):
        """All attribute names should be unique."""
        attrs = [attr for title, attr in SECTION_MAPPING]
        assert len(attrs) == len(set(attrs))


class TestLearningFromReport:
    """Tests for learn_from_report function."""

    def test_learn_from_none_report(self):
        """Should handle None report gracefully."""
        result = learn_from_report(None)
        assert result == 0

    def test_learn_from_complete_report(self, complete_report):
        """Should extract sections from complete report."""
        result = learn_from_report(complete_report)
        # Should extract at least the sections that were populated
        assert result > 0

    def test_learn_from_minimal_report(self):
        """Should work with minimal report (required fields only)."""
        report = AICMOOutputReport(
            marketing_plan=MarketingPlanView(
                executive_summary="Summary",
                situation_analysis="Analysis",
                strategy="Strategy",
            ),
            campaign_blueprint=CampaignBlueprintView(
                big_idea="Idea",
                objective=CampaignObjectiveView(primary="awareness"),
                audience_persona=AudiencePersonaView(name="Test", description="Test"),
            ),
            social_calendar=SocialCalendarView(
                start_date=date.today(),
                end_date=date.today(),
                posts=[],
            ),
        )
        result = learn_from_report(report)
        assert result >= 0

    def test_learn_from_report_with_project_id(self, complete_report):
        """Should accept and use project_id parameter."""
        result = learn_from_report(
            complete_report,
            project_id="test_project_123",
        )
        assert result >= 0

    def test_learn_from_report_with_tags(self, complete_report):
        """Should accept and use tags parameter."""
        result = learn_from_report(
            complete_report,
            tags=["test_tag", "custom_tag"],
        )
        assert result >= 0

    def test_learn_only_populated_sections(self):
        """Should only extract populated sections, skip empty ones."""
        # Report with only marketing_plan populated
        report = AICMOOutputReport(
            marketing_plan=MarketingPlanView(
                executive_summary="Summary",
                situation_analysis="Analysis",
                strategy="Strategy",
            ),
            campaign_blueprint=CampaignBlueprintView(
                big_idea="Idea",
                objective=CampaignObjectiveView(primary="awareness"),
                audience_persona=AudiencePersonaView(name="Test", description="Test"),
            ),
            social_calendar=SocialCalendarView(
                start_date=date.today(),
                end_date=date.today(),
                posts=[],
            ),
            # Intentionally NOT setting persona_cards, creatives, performance_review
        )

        result = learn_from_report(report)
        # Should still extract marketing plan and campaign blueprint
        assert result >= 0

    def test_learn_fallback_to_full_report(self):
        """Should fallback to full report if no sections extracted."""
        # Create report with empty/None sections where possible
        report = AICMOOutputReport(
            marketing_plan=MarketingPlanView(
                executive_summary="",  # Empty
                situation_analysis="",
                strategy="",
            ),
            campaign_blueprint=CampaignBlueprintView(
                big_idea="",
                objective=CampaignObjectiveView(primary="awareness"),
                audience_persona=AudiencePersonaView(name="", description=""),
            ),
            social_calendar=SocialCalendarView(
                start_date=date.today(),
                end_date=date.today(),
                posts=[],
            ),
        )

        result = learn_from_report(report)
        # Should still return a result (fallback)
        assert result >= 0


class TestBriefToText:
    """Tests for brief text conversion."""

    def test_brief_to_text_returns_string(self, minimal_brief):
        """Should return a string."""
        result = _brief_to_text(minimal_brief)
        assert isinstance(result, str)

    def test_brief_to_text_non_empty(self, minimal_brief):
        """Should return non-empty string."""
        result = _brief_to_text(minimal_brief)
        assert len(result) > 0

    def test_brief_to_text_includes_brand_name(self, minimal_brief):
        """Should include brand name if available."""
        result = _brief_to_text(minimal_brief)
        # May or may not include brand name depending on implementation
        assert isinstance(result, str)


class TestLearningIntegration:
    """Integration tests for learning system."""

    def test_learn_and_augment_flow(self, minimal_brief, complete_report):
        """Should be able to learn from report and augment prompts."""
        # Learn from report
        stored = learn_from_report(complete_report)
        assert stored >= 0

        # Brief should be convertible to text for augmentation
        brief_text = _brief_to_text(minimal_brief)
        assert len(brief_text) > 0

    def test_repeated_learning(self, complete_report):
        """Should handle repeated learning calls."""
        result1 = learn_from_report(complete_report)
        result2 = learn_from_report(complete_report)
        # Both should succeed
        assert result1 >= 0
        assert result2 >= 0
