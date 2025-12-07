"""
Test suite for full_30_day_calendar generator benchmark compliance.

Validates that _gen_full_30_day_calendar produces markdown that meets
all benchmark validation rules for full_funnel_growth_suite pack.
"""

import pytest
from backend.main import GenerateRequest, _gen_full_30_day_calendar
from aicmo.io.client_reports import (
    ClientInputBrief,
    BrandBrief,
    AudienceBrief,
    GoalBrief,
    VoiceBrief,
    ProductServiceBrief,
    AssetsConstraintsBrief,
    OperationsBrief,
    StrategyExtrasBrief,
)


def create_test_request():
    """Create a GenerateRequest for testing full_funnel_growth_suite."""
    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name="TechCorp",
            industry="Enterprise Software",
            product_service="Cloud Analytics Platform",
            primary_goal="Increase enterprise ARR by 50%",
            primary_customer="Data Engineering Teams",
        ),
        audience=AudienceBrief(
            primary_customer="Data Engineering Teams",
            pain_points=["Data analysis efficiency"],
        ),
        goal=GoalBrief(
            primary_goal="Increase enterprise ARR by 50%",
            kpis=["ARR Growth", "Customer Adoption"],
        ),
        voice=VoiceBrief(tone_of_voice=["Professional", "Technical"]),
        product_service=ProductServiceBrief(items=[]),
        assets_constraints=AssetsConstraintsBrief(),
        operations=OperationsBrief(),
        strategy_extras=StrategyExtrasBrief(),
    )

    return GenerateRequest(brief=brief, package_preset="full_funnel_growth_suite")


class TestFullThirtDayCalendarCompliance:
    """Test suite for full_30_day_calendar generator compliance with benchmarks."""

    def test_generator_produces_output(self):
        """Verify generator produces non-empty output."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")
        assert content is not None
        assert len(content) > 0
        assert isinstance(content, str)

    def test_contains_required_headings(self):
        """Verify output contains all 4 required week headings."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        required_headings = ["Week 1", "Week 2", "Week 3", "Week 4"]
        for heading in required_headings:
            assert heading in content, f"Missing required heading: {heading}"

    def test_contains_markdown_table(self):
        """Verify output contains markdown table (pipe characters)."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        assert "|" in content, "Output must contain pipe characters for markdown table"
        # Verify it looks like a table (has multiple pipes per line)
        table_lines = [line for line in content.split("\n") if line.count("|") >= 3]
        assert len(table_lines) > 0, "No proper markdown table structure found"

    def test_word_count_within_bounds(self):
        """Verify output word count is between 300-1000."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        word_count = len(content.split())
        assert (
            300 <= word_count <= 1000
        ), f"Word count {word_count} outside benchmark range [300-1000]"

    def test_bullet_count_within_bounds(self):
        """Verify output has 12-40 bullets."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        bullet_count = content.count("- ")
        assert (
            12 <= bullet_count <= 40
        ), f"Bullet count {bullet_count} outside benchmark range [12-40]"

    def test_heading_count_within_bounds(self):
        """Verify output has 4-10 headings."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        heading_count = content.count("##")
        assert (
            4 <= heading_count <= 10
        ), f"Heading count {heading_count} outside benchmark range [4-10]"

    def test_no_forbidden_phrases(self):
        """Verify output doesn't contain forbidden phrases."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        forbidden = ["post daily", "figure it out later", "lorem ipsum"]
        for phrase in forbidden:
            assert (
                phrase.lower() not in content.lower()
            ), f"Output contains forbidden phrase: {phrase}"

    def test_no_excessive_repetition(self):
        """Verify output doesn't have excessive line repetition (max 0.35 ratio)."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        lines = [line.strip() for line in content.split("\n") if line.strip()]
        if len(lines) > 0:
            # Count repeated lines
            repeated_count = sum(1 for line in lines if lines.count(line) > 1)
            repetition_ratio = repeated_count / len(lines)
            assert (
                repetition_ratio <= 0.35
            ), f"Repetition ratio {repetition_ratio:.2f} exceeds maximum 0.35"

    def test_specific_language_not_generic(self):
        """Verify output uses specific brand/goal/industry language."""
        req = create_test_request()
        content = _gen_full_30_day_calendar(req, pack_key="full_funnel_growth_suite")

        # Should contain brand-specific variables
        assert "TechCorp" in content, "Output should contain brand name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
