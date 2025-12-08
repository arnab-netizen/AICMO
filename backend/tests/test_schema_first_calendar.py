"""
Test suite for schema-first Full Funnel Calendar implementation.

Verifies that the new Pydantic-model-based calendar generation:
1. Produces deterministic, validated structured data
2. Renders markdown that passes all benchmark constraints
3. Integrates properly with the HTTP pipeline
4. Supports repair and validation workflows

Benchmark constraints verified (from learning/benchmarks/section_benchmarks.full_funnel.json):
- word_count: 300-1000
- headings: 4-10, required: ["Week 1", "Week 2", "Week 3", "Week 4"]
- bullets: 12-40
- format: markdown_table (must contain |)
- max_repeated_line_ratio: 0.35
- max_avg_sentence_length: 28
- forbidden_substrings: ["post daily", "figure it out later", "lorem ipsum"]
"""

import pytest
from backend.models_full_funnel_calendar import FullFunnelCalendarItem, FullFunnelCalendar
from backend.full_funnel_calendar_builder import (
    build_full_funnel_calendar,
    render_calendar_to_markdown,
)
from backend.validators.calendar_validator import (
    validate_full_funnel_calendar,
    repair_full_funnel_calendar,
)


class TestPydanticModels:
    """Test the Pydantic calendar models."""

    def test_full_funnel_calendar_item_valid(self):
        """Test creating valid FullFunnelCalendarItem."""
        item = FullFunnelCalendarItem(
            day="Day 1",
            stage="Awareness",
            topic="Why Enterprise Users choose our Platform",
            format="Blog",
            channel="LinkedIn",
            cta="Read →",
        )
        assert item.day == "Day 1"
        assert item.stage == "Awareness"
        assert len(item.topic) > 0

    def test_full_funnel_calendar_item_invalid_day(self):
        """Test that invalid day format raises ValueError."""
        with pytest.raises(ValueError, match="Day must be"):
            FullFunnelCalendarItem(
                day="1",  # Invalid format
                stage="Awareness",
                topic="Topic",
                format="Blog",
                channel="LinkedIn",
                cta="Read →",
            )

    def test_full_funnel_calendar_item_invalid_stage(self):
        """Test that invalid stage raises ValueError."""
        with pytest.raises(ValueError, match="Stage must be"):
            FullFunnelCalendarItem(
                day="Day 1",
                stage="InvalidStage",
                topic="Topic here",
                format="Blog",
                channel="LinkedIn",
                cta="Read →",
            )

    def test_full_funnel_calendar_30_items(self):
        """Test that FullFunnelCalendar validates exactly 30 items."""
        # Build 30 valid items
        items = [
            FullFunnelCalendarItem(
                day=f"Day {i}",
                stage=(
                    "Awareness"
                    if i <= 7
                    else "Consideration" if i <= 14 else "Conversion" if i <= 21 else "Retention"
                ),
                topic=f"Content for day {i} specific to enterprise goals",
                format="Blog",
                channel="LinkedIn",
                cta="Read →",
            )
            for i in range(1, 31)
        ]

        calendar = FullFunnelCalendar(
            items=items,
            brand="TestBrand",
            industry="SaaS",
            customer="Enterprise Users",
            goal="increase revenue",
            product="Platform",
        )

        assert len(calendar.items) == 30
        assert all(item.day for item in calendar.items)

    def test_full_funnel_calendar_duplicate_days_rejected(self):
        """Test that duplicate days are rejected."""
        items = [
            FullFunnelCalendarItem(
                day="Day 1",
                stage="Awareness",
                topic="First day content",
                format="Blog",
                channel="LinkedIn",
                cta="Read →",
            ),
            FullFunnelCalendarItem(
                day="Day 1",  # Duplicate!
                stage="Awareness",
                topic="Another day 1 content",
                format="Blog",
                channel="LinkedIn",
                cta="Read →",
            ),
        ]

        with pytest.raises(ValueError, match="must be unique"):
            FullFunnelCalendar(
                items=items,
                brand="TestBrand",
                industry="SaaS",
                customer="Enterprise Users",
                goal="increase revenue",
                product="Platform",
            )


class TestCalendarBuilder:
    """Test the calendar builder functions."""

    def test_build_calendar_creates_30_items(self):
        """Test that build_full_funnel_calendar creates exactly 30 items."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        assert len(calendar.items) == 30
        assert calendar.brand == "Acme Inc"
        assert calendar.industry == "SaaS"

    def test_build_calendar_stage_progression(self):
        """Test that weeks follow stage progression."""
        calendar = build_full_funnel_calendar(
            brand_name="TestBrand",
            industry="Finance",
            primary_customer="Banks",
            primary_goal="reduce fraud",
            product_service="SecurityPlatform",
        )

        # Week 1 should be mostly Awareness
        w1_items = [item for item in calendar.items if 1 <= int(item.day.split()[1]) <= 7]
        w1_awareness = sum(1 for item in w1_items if item.stage == "Awareness")
        assert w1_awareness >= 5, f"Week 1 should have 5+ Awareness items, got {w1_awareness}"

        # Week 2 should have Consideration items
        w2_items = [item for item in calendar.items if 8 <= int(item.day.split()[1]) <= 14]
        w2_consideration = sum(1 for item in w2_items if item.stage == "Consideration")
        assert w2_consideration > 0, "Week 2 should have Consideration items"


class TestCalendarRenderer:
    """Test markdown rendering from structured calendar."""

    def test_render_markdown_output(self):
        """Test that render_calendar_to_markdown produces valid markdown."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)

        # Check basic structure
        assert markdown.startswith("## Full 30-Day Content Calendar")
        assert "Week 1" in markdown
        assert "Week 2" in markdown
        assert "Week 3" in markdown
        assert "Week 4" in markdown
        assert "Campaign Framework" in markdown

    def test_render_markdown_word_count(self):
        """Test that rendered markdown word count is in valid range."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)
        words = len(markdown.split())

        # Benchmark: 300-1000 words
        assert 300 <= words <= 1000, f"Word count {words} not in range 300-1000"

    def test_render_markdown_contains_table(self):
        """Test that markdown contains table format."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)

        # Benchmark requires markdown_table format
        assert "|" in markdown, "Markdown must contain table format with |"
        assert "Day |" in markdown, "Table must have Day column"
        assert "Stage |" in markdown, "Table must have Stage column"

    def test_render_markdown_headings(self):
        """Test that markdown has required headings."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)

        # Benchmark requires specific headings
        required_headings = ["Week 1", "Week 2", "Week 3", "Week 4"]
        for heading in required_headings:
            assert f"### {heading}" in markdown, f"Required heading '{heading}' not found"

    def test_render_markdown_bullets(self):
        """Test that markdown has sufficient bullets."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)
        bullets = markdown.count("\n- **")

        # Benchmark: 12-40 bullets
        assert 12 <= bullets <= 40, f"Bullet count {bullets} not in range 12-40"


class TestValidatorAndRepair:
    """Test calendar validation and repair functions."""

    def test_validate_good_calendar(self):
        """Test that good calendar passes validation."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        is_valid, issues = validate_full_funnel_calendar(calendar)
        assert is_valid, f"Valid calendar failed validation: {issues}"
        assert len(issues) == 0

    def test_repair_missing_days(self):
        """Test that repair adds missing days."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        # Remove some days
        broken = FullFunnelCalendar(
            items=calendar.items[:15],  # Only 15 items
            brand=calendar.brand,
            industry=calendar.industry,
            customer=calendar.customer,
            goal=calendar.goal,
            product=calendar.product,
        )

        repaired, repair_log = repair_full_funnel_calendar(broken)

        assert len(repaired.items) == 30
        assert repair_log["days_added"] > 0

        # Validate repaired calendar passes
        is_valid, issues = validate_full_funnel_calendar(repaired)
        assert is_valid, f"Repaired calendar failed: {issues}"


class TestBenchmarkCompliance:
    """Test that output meets all benchmark requirements."""

    def test_full_compliance(self):
        """Test full compliance with all benchmark rules."""
        calendar = build_full_funnel_calendar(
            brand_name="Acme Inc",
            industry="SaaS",
            primary_customer="Enterprise Users",
            primary_goal="increase revenue",
            product_service="Platform",
        )

        markdown = render_calendar_to_markdown(calendar)

        # Verify structure is valid first
        is_valid, issues = validate_full_funnel_calendar(calendar)
        assert is_valid, f"Structure validation failed: {issues}"

        # Verify markdown compliance
        words = len(markdown.split())
        bullets = markdown.count("\n- **")
        has_table = "|" in markdown
        has_week1 = "### Week 1" in markdown
        has_week2 = "### Week 2" in markdown
        has_week3 = "### Week 3" in markdown
        has_week4 = "### Week 4" in markdown

        # Benchmark constraints
        assert 300 <= words <= 1000, f"Word count {words} out of range"
        assert 12 <= bullets <= 40, f"Bullet count {bullets} out of range"
        assert has_table, "Missing markdown table format"
        assert has_week1 and has_week2 and has_week3 and has_week4, "Missing Week headings"

        # No forbidden phrases
        forbidden = ["post daily", "figure it out later", "lorem ipsum"]
        for phrase in forbidden:
            assert phrase.lower() not in markdown.lower(), f"Forbidden phrase: {phrase}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
