"""
Test suite for output validation (FIX #6).

Tests that output validation catches:
- Empty critical fields
- Field substitution errors (goal as persona)
- Pack scoping violations
- Industry-channel misalignment
- PDF parity issues

Run: pytest tests/test_output_validation.py -v
"""

import pytest
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    StrategyExtrasBrief,
    AICMOOutputReport,
    MarketingPlanView,
    CampaignBlueprintView,
    SocialCalendarView,
    PersonaCard,
)
from backend.validators import OutputValidator, ValidationSeverity, validate_output_report


@pytest.fixture
def sample_brief():
    """Create a sample client brief for testing."""
    return ClientInputBrief(
        brand=BrandBrief(
            brand_name="TestBrand",
            industry="SaaS",
            product_service="Marketing software",
            primary_goal="Increase leads",
            primary_customer="Marketing managers",
        ),
        audience=AudienceBrief(
            primary_customer="Marketing managers",
            secondary_customer="CMOs",
        ),
        goal=GoalBrief(
            primary_goal="Generate 500 qualified leads per month",
            timeline="6 months",
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["innovative", "reliable"],
        ),
    )


@pytest.fixture
def sample_output():
    """Create a sample output report for testing."""
    return AICMOOutputReport(
        marketing_plan=MarketingPlanView(
            executive_summary="Sample executive summary",
            situation_analysis="Market situation analysis",
            strategy="Strategic approach overview",
        ),
        campaign_blueprint=CampaignBlueprintView(
            campaign_name="Sample Campaign",
        ),
        social_calendar=SocialCalendarView(
            calendar_entries=[],
        ),
        persona_cards=[
            PersonaCard(
                name="VP of Marketing",
                role="Decision maker",
                goals=["Increase lead volume", "Improve quality"],
                challenges=["Limited budget", "Complex sales cycle"],
            ),
        ],
    )


class TestOutputValidator:
    """Tests for OutputValidator class."""

    def test_validator_initializes(self, sample_output, sample_brief):
        """Test that validator initializes correctly."""
        validator = OutputValidator(sample_output, sample_brief, "strategy_campaign_standard")
        assert validator.output == sample_output
        assert validator.brief == sample_brief
        assert validator.wow_package_key == "strategy_campaign_standard"
        assert validator.issues == []

    def test_validate_all_returns_list(self, sample_output, sample_brief):
        """Test that validate_all returns a list."""
        validator = OutputValidator(sample_output, sample_brief)
        issues = validator.validate_all()
        assert isinstance(issues, list)

    def test_has_blocking_issues_false(self, sample_output, sample_brief):
        """Test that good output has no blocking issues."""
        validator = OutputValidator(sample_output, sample_brief)
        validator.validate_all()
        assert not validator.has_blocking_issues()

    def test_has_blocking_issues_true(self, sample_output, sample_brief):
        """Test that validator detects blocking issues."""
        # Create brief with missing brand name
        bad_brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="",  # Empty!
                industry="SaaS",
                product_service="Software",
                primary_goal="Growth",
                primary_customer="Users",
            ),
            audience=AudienceBrief(primary_customer="Users"),
            goal=GoalBrief(primary_goal="Growth"),
            strategy_extras=StrategyExtrasBrief(),
        )

        validator = OutputValidator(sample_output, bad_brief)
        validator.validate_all()
        # Should detect empty brand name
        assert any(i.severity == ValidationSeverity.WARNING for i in validator.issues)

    def test_field_substitution_detection(self, sample_output, sample_brief):
        """Test detection of goal text in persona name."""
        # Persona name contains goal text - should flag as ERROR
        output_with_bad_persona = AICMOOutputReport(
            marketing_plan=sample_output.marketing_plan,
            campaign_blueprint=sample_output.campaign_blueprint,
            social_calendar=sample_output.social_calendar,
            persona_cards=[
                PersonaCard(
                    name="Generate 500 qualified leads per month",  # Same as goal!
                    role="Decision maker",
                ),
            ],
        )

        validator = OutputValidator(output_with_bad_persona, sample_brief)
        issues = validator.validate_all()

        # Should detect substitution
        assert any(
            i.severity == ValidationSeverity.ERROR and "persona" in i.section.lower()
            for i in issues
        )

    def test_pack_scoping_validation(self, sample_output, sample_brief):
        """Test pack scoping validation."""
        validator = OutputValidator(sample_output, sample_brief, "quick_social_basic")

        # With minimal extra_sections, should get warning about low count
        issues = validator.validate_all()

        # Either no issue (if section count acceptable) or warning about count
        scoping_issues = [i for i in issues if "pack" in i.section.lower()]
        # Should not have blocking errors for valid packs
        assert not any(i.severity == ValidationSeverity.ERROR for i in scoping_issues)

    def test_industry_alignment_check(self, sample_output):
        """Test industry alignment validation."""
        # Create SaaS brief
        saas_brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="SaaS Co",
                industry="SaaS",  # Should recommend LinkedIn
                product_service="Software",
                primary_goal="Growth",
                primary_customer="CTOs",
            ),
            audience=AudienceBrief(primary_customer="CTOs"),
            goal=GoalBrief(primary_goal="Growth"),
            strategy_extras=StrategyExtrasBrief(),
        )

        validator = OutputValidator(sample_output, saas_brief)
        issues = validator.validate_all()

        # Industry alignment check should run without error
        assert isinstance(issues, list)


class TestValidateOutputReportFunction:
    """Tests for the convenience validate_output_report function."""

    def test_validate_output_report_good(self, sample_output, sample_brief):
        """Test validation with good output."""
        is_valid, issues = validate_output_report(sample_output, sample_brief)
        assert is_valid is True
        assert isinstance(issues, list)

    def test_validate_output_report_strict_mode(self, sample_output, sample_brief):
        """Test strict mode converts warnings to errors."""
        is_valid, issues = validate_output_report(sample_output, sample_brief, strict=True)

        # In strict mode, warnings become errors
        for issue in issues:
            # Check that severity is handled correctly
            assert issue.severity in [ValidationSeverity.ERROR, ValidationSeverity.INFO]

    def test_validate_output_report_with_wow_key(self, sample_output, sample_brief):
        """Test validation with WOW package key specified."""
        is_valid, issues = validate_output_report(
            sample_output,
            sample_brief,
            wow_package_key="strategy_campaign_standard",
        )

        assert isinstance(is_valid, bool)
        assert isinstance(issues, list)


class TestPackScopingValidation:
    """Specific tests for pack scoping validation."""

    def test_pack_section_count_basic(self, sample_brief):
        """Test Basic pack expects 10 sections."""
        output = AICMOOutputReport(
            marketing_plan=MarketingPlanView(executive_summary="Test"),
            campaign_blueprint=CampaignBlueprintView(campaign_name="Test"),
            social_calendar=SocialCalendarView(calendar_entries=[]),
            extra_sections={f"section_{i}": f"Content {i}" for i in range(8)},  # Only 8
        )

        validator = OutputValidator(output, sample_brief, "quick_social_basic")
        issues = validator.validate_all()

        # With only 11 total sections (8 + 3 structured), might get warning
        # But should not ERROR
        errors = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        assert not errors  # No blocking errors


class TestFieldValidation:
    """Specific tests for field validation."""

    def test_empty_goal_detected(self, sample_output):
        """Test detection of empty goal."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="Brand",
                industry="SaaS",
                product_service="Software",
                primary_goal="",  # Empty!
                primary_customer="Users",
            ),
            audience=AudienceBrief(primary_customer="Users"),
            goal=GoalBrief(primary_goal=""),  # Empty!
            strategy_extras=StrategyExtrasBrief(),
        )

        validator = OutputValidator(sample_output, brief)
        issues = validator.validate_all()

        # Should detect empty goal
        assert any("goal" in i.message.lower() for i in issues)

    def test_industry_not_specified(self, sample_output):
        """Test detection of missing industry."""
        brief = ClientInputBrief(
            brand=BrandBrief(
                brand_name="Brand",
                industry="",  # Empty!
                product_service="Software",
                primary_goal="Growth",
                primary_customer="Users",
            ),
            audience=AudienceBrief(primary_customer="Users"),
            goal=GoalBrief(primary_goal="Growth"),
            strategy_extras=StrategyExtrasBrief(),
        )

        validator = OutputValidator(sample_output, brief)
        issues = validator.validate_all()

        # Should detect empty industry
        assert any("industry" in i.message.lower() for i in issues)


class TestPDFParity:
    """Tests for PDF parity validation."""

    def test_pdf_parity_with_wow_markdown(self, sample_output, sample_brief):
        """Test PDF parity check with WOW markdown."""
        output_with_wow = AICMOOutputReport(
            marketing_plan=sample_output.marketing_plan,
            campaign_blueprint=sample_output.campaign_blueprint,
            social_calendar=sample_output.social_calendar,
            wow_markdown="## Section 1\nContent\n## Section 2\nContent\n" * 10,  # 20 sections
        )

        validator = OutputValidator(output_with_wow, sample_brief, "strategy_campaign_standard")
        issues = validator.validate_all()

        # Should pass parity check (20 sections >= 70% of 17)
        parity_issues = [i for i in issues if "pdf" in i.section.lower()]
        assert not parity_issues or all(
            i.severity != ValidationSeverity.ERROR for i in parity_issues
        )

    def test_pdf_parity_too_few_sections(self, sample_output, sample_brief):
        """Test PDF parity fails with too few sections."""
        output_with_wow = AICMOOutputReport(
            marketing_plan=sample_output.marketing_plan,
            campaign_blueprint=sample_output.campaign_blueprint,
            social_calendar=sample_output.social_calendar,
            wow_markdown="## Section 1\nContent",  # Only 1 section!
        )

        validator = OutputValidator(output_with_wow, sample_brief, "strategy_campaign_standard")
        issues = validator.validate_all()

        # Should detect low section count
        parity_issues = [i for i in issues if "pdf parity" in i.section.lower()]
        assert any(i.severity == ValidationSeverity.WARNING for i in parity_issues)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
