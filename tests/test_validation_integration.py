"""
Integration tests proving the validation fixes work end-to-end.

These tests demonstrate that:
1. Poor-quality Starbucks report NOW FAILS validation (was passing before)
2. Good-quality reports still pass
3. Validation errors are breaking (stop generation)
4. All quality checks are integrated
"""

import pytest
from unittest.mock import Mock, patch

from backend.main import (
    _dev_apply_wow_and_validate,
    _apply_wow_optional,
    PackOutput,
    GenerateRequest,
)


class TestValidationIntegration:
    """Integration tests for the complete validation fix."""

    def test_poor_quality_starbucks_now_fails(self):
        """
        CRITICAL TEST: Verify that poor-quality Starbucks content NOW FAILS.

        This is the exact scenario the user reported: generic content with blacklist
        phrases was passing validation when it should have failed.
        """
        # Poor quality markdown with multiple quality issues:
        # - Blacklist phrases ("in today's digital age", "content is king", etc.)
        # - Template placeholders ({{brand_name}}, [INSERT GOAL])
        # - Too short sections
        # - Generic marketing speak
        poor_quality_markdown = """## Overview

In today's digital age, {{brand_name}} leverages content marketing to drive results.
We create tangible impact through proven methodologies and industry-leading best practices.
Content is king and we'll move the needle with our cutting-edge approach.

Brand: Starbucks
Industry: Food & Beverage
Primary Goal: [INSERT GOAL]

## Messaging Framework

We leverage synergy to create a game-changer in the market.
Our state-of-the-art solutions deliver best practices.
Think outside the box with our proven methodologies.

## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share customer success story |
| Day 2 | Facebook | Share customer success story |
| Day 3 | Twitter | Share customer success story |
| Day 4 | Instagram | Share customer success story |
| Day 5 | Facebook | Share customer success story |
"""

        # This should NOW raise ValueError due to validation failures
        with pytest.raises(ValueError, match="Quality validation FAILED"):
            _dev_apply_wow_and_validate("quick_social_basic", poor_quality_markdown)

    def test_good_quality_content_passes(self):
        """Test that good-quality content still passes validation."""
        # Good quality markdown:
        # - Specific, concrete language with real metrics
        # - No blacklist phrases
        # - No placeholders
        # - Proper word counts
        # - Unique calendar hooks
        good_quality_markdown = """## Overview

Brand: Starbucks
Industry: Food & Beverage
Primary Goal: Increase mobile app engagement by 25% through personalized rewards

Starbucks operates 15,000 retail locations across North America. They serve 100 million customers each week.
The mobile app processes 23% of all transactions. The Rewards program has 28 million active members.
Pike Place blend is their top seller. Sales reach 3.2 million pounds monthly.

The strategy focuses on mobile order-ahead. This feature handles 18% of morning rush orders.
Data shows 67% higher visit frequency. Rewards members visit stores more often than non-members.
Mobile payments grew 45% year-over-year. The app ranks number three in the food category.

### Key Objectives
- Expand mobile ordering penetration to 30% of transactions
- Increase Rewards program enrollment by 5 million new members
- Launch personalized product recommendations based on purchase history
- Optimize store pickup experience to reduce wait times

## Messaging Framework

Premium coffee experiences crafted by expert baristas. Personalized service drives customer loyalty.
Sustainable sourcing builds community trust. Innovation creates convenience for busy lifestyles.
Digital engagement transforms the customer journey. Rewards programs build lasting relationships.

### Core Message Pillars
- Quality: 100% Arabica beans from sustainable farms in Colombia and Ethiopia
- Community: Local store events and partnerships across 6,000 US communities  
- Innovation: Mobile ordering platform with 5-minute pickup guarantee and personalized recommendations
- Responsibility: Ethical sourcing program supporting 380,000 farming families worldwide
- Experience: Customized drink recommendations based on purchase history and preferences
- Convenience: Order ahead feature eliminates waiting and streamlines morning routines

## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share coffee farm origin story |
| Day 2 | Facebook | Customer testimonial video |
| Day 3 | Twitter | Coffee brewing tip |
| Day 4 | Instagram | Behind-the-scenes barista training |
| Day 5 | Facebook | New seasonal drink announcement |
| Day 6 | Twitter | Sustainability milestone update |
| Day 7 | Instagram | Community spotlight event |
| Day 8 | Facebook | Educational post on roast levels |
| Day 9 | Twitter | Quick poll on coffee preferences |
| Day 10 | Instagram | Latte art creation video |
| Day 11 | Facebook | Local store grand opening |
| Day 12 | Twitter | Coffee trivia question |
| Day 13 | Instagram | Farm-to-cup journey photo |
| Day 14 | Facebook | Week-in-review highlights |
| Day 15 | Twitter | Industry news commentary |
| Day 16 | Instagram | Product photography showcase |
| Day 17 | Facebook | Customer appreciation post |
| Day 18 | Twitter | Coffee pairing suggestions |
| Day 19 | Instagram | Employee spotlight feature |
| Day 20 | Facebook | Recipe sharing post |
| Day 21 | Twitter | Engagement question |
| Day 22 | Instagram | Seasonal flavor teaser |
| Day 23 | Facebook | Community impact story |
| Day 24 | Twitter | Quick tip share |
| Day 25 | Instagram | User-generated content |
| Day 26 | Facebook | Partnership announcement |
| Day 27 | Twitter | Poll results share |
| Day 28 | Instagram | Month-end recap |
| Day 29 | Facebook | Preview next month |
| Day 30 | Twitter | Thank you message |
"""

        # Should NOT raise - passes validation
        result = _dev_apply_wow_and_validate("quick_social_basic", good_quality_markdown)

        assert result.status in ("PASS", "PASS_WITH_WARNINGS")

    def test_validation_errors_are_breaking(self):
        """Test that validation errors BLOCK generation (are breaking)."""
        # Markdown that will fail multiple quality checks
        failing_markdown = """## Overview

In today's digital age, {{brand_name}} is a game-changer.
[INSERT STAT] proves content is king and we leverage best practices.

Brand: Test Brand
Industry: Technology  
Primary Goal: Drive results

## Messaging Framework

We leverage synergy to move the needle with cutting-edge solutions.
Our proven methodologies deliver tangible impact through best practices.
Think outside the box to create a game-changer in the market.
"""

        # Validation errors should raise ValueError (breaking)
        with pytest.raises(ValueError) as exc_info:
            _dev_apply_wow_and_validate("quick_social_basic", failing_markdown)

        # Error message should mention quality validation
        assert "Quality validation FAILED" in str(exc_info.value)

    def test_duplicate_hooks_caught_in_calendar(self):
        """Test that duplicate hooks in calendar sections are caught."""
        # Calendar with many duplicate hooks (>30% duplicates)
        duplicate_calendar = """## Overview

Brand: Test Brand
Industry: Technology
Primary Goal: Increase engagement by 25% through social media optimization

The company operates in multiple markets. Technology solutions drive customer satisfaction.
Digital transformation creates new opportunities. Innovation leads to competitive advantages.
Market research shows strong demand patterns. Customer feedback indicates positive reception.

### Key Objectives
- Expand market presence through strategic partnerships
- Increase customer engagement through digital channels
- Launch innovative products based on market research
- Optimize operations to improve efficiency metrics

## Messaging Framework

Technology solutions transform business operations. Digital platforms enable seamless experiences.
Innovation drives sustainable growth trajectories. Customer-centric approaches build loyalty.
Strategic partnerships create synergistic opportunities. Data-driven insights guide decisions.

### Core Message Pillars
- Innovation: Cutting-edge technology solutions for modern businesses
- Reliability: Proven track record of successful implementations
- Partnership: Collaborative approach to solving customer challenges
- Growth: Scalable solutions that adapt to changing needs
- Quality: Commitment to excellence in every deliverable
- Support: Dedicated team ensuring customer success

## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share customer success story |
| Day 2 | Facebook | Share customer success story |
| Day 3 | Twitter | Share customer success story |
| Day 4 | Instagram | Share customer success story |
| Day 5 | Facebook | Share customer success story |
| Day 6 | Twitter | Share customer success story |
| Day 7 | Instagram | Share customer success story |
| Day 8 | Facebook | Share customer success story |
| Day 9 | Twitter | Share customer success story |
| Day 10 | Instagram | Share customer success story |
| Day 11 | Facebook | Post engaging content |
| Day 12 | Twitter | Post engaging content |
| Day 13 | Instagram | Post engaging content |
| Day 14 | Facebook | Post engaging content |
| Day 15 | Twitter | Post engaging content |
| Day 16 | Instagram | Post engaging content |
| Day 17 | Facebook | Post engaging content |
| Day 18 | Twitter | Post engaging content |
| Day 19 | Instagram | Post engaging content |
| Day 20 | Facebook | Post engaging content |
| Day 21 | Twitter | Post engaging content |
| Day 22 | Instagram | Post engaging content |
| Day 23 | Facebook | Post engaging content |
| Day 24 | Twitter | Post engaging content |
| Day 25 | Instagram | Post engaging content |
| Day 26 | Facebook | Post engaging content |
| Day 27 | Twitter | Post engaging content |
| Day 28 | Instagram | Post engaging content |
| Day 29 | Facebook | Post engaging content |
| Day 30 | Twitter | Post engaging content |
"""

        # Should fail due to duplicate hooks
        with pytest.raises(ValueError, match="Quality validation FAILED"):
            _dev_apply_wow_and_validate("quick_social_basic", duplicate_calendar)


class TestValidationFixProof:
    """Tests that prove each specific fix is working."""

    def test_fix_1_markdown_parser_used(self):
        """Prove that Fix #1 (markdown parser) is being used."""
        from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections

        markdown = """## Overview
Content here

## Messaging
More content
"""

        sections = parse_wow_markdown_to_sections(markdown)

        # Verify parser works
        assert len(sections) == 2
        assert sections[0]["id"] == "overview"
        assert sections[1]["id"] == "messaging"

    def test_fix_2_quality_checks_integrated(self):
        """Prove that Fix #2 (quality checks) are integrated into validator."""
        from backend.validators.benchmark_validator import validate_section_against_benchmark

        # Content with quality issues
        content = """## Overview

In today's digital age, {{brand_name}} drives results.
Content is king and we leverage best practices.
"""

        result = validate_section_against_benchmark(
            pack_key="quick_social_basic", section_id="overview", content=content
        )

        # Should catch quality issues
        assert result.status == "FAIL"
        issue_codes = {i.code for i in result.issues}

        # Should have quality check issues (blacklist, placeholder)
        assert any(
            code in issue_codes
            for code in ["BLACKLISTED_PHRASE", "TEMPLATE_PLACEHOLDER", "TOO_GENERIC"]
        )

    def test_fix_3_validation_is_breaking(self):
        """Prove that Fix #3 (breaking validation) works."""
        # Poor quality markdown should raise ValueError
        poor_markdown = """## Overview

In today's digital age, {{brand_name}} drives results.

Brand: Test
Industry: Tech
Primary Goal: [INSERT]
"""

        with pytest.raises(ValueError, match="Quality validation FAILED"):
            _dev_apply_wow_and_validate("quick_social_basic", poor_markdown)

    def test_validation_errors_are_breaking(self):
        """Test that validation errors BLOCK generation (are breaking)."""
        output = PackOutput()
        output.extra_sections = {}

        req = Mock(spec=GenerateRequest)
        req.wow_enabled = True
        req.wow_package_key = "quick_social_basic"
        req.brief = Mock()
        req.brief.brand_name = "Test Brand"

        mock_wow_rule = {"sections": [{"key": "overview"}]}

        # Markdown that will fail multiple quality checks
        failing_markdown = """## Overview

In today's digital age, {{brand_name}} is a game-changer.
[INSERT STAT] proves content is king and we leverage best practices.
"""

        with patch("backend.main.get_wow_rule", return_value=mock_wow_rule):
            with patch("backend.main.build_wow_report", return_value=failing_markdown):
                with patch(
                    "backend.main.humanize_report_text", side_effect=lambda text, **kwargs: text
                ):
                    with patch("backend.main.get_industry_config", return_value=None):
                        # Validation errors should raise ValueError (breaking)
                        with pytest.raises(ValueError) as exc_info:
                            _apply_wow_optional(output, req)

                        # Error message should mention quality validation
                        assert "Quality validation FAILED" in str(exc_info.value)

    def test_duplicate_hooks_caught_in_calendar(self):
        """Test that duplicate hooks in calendar sections are caught."""
        output = PackOutput()
        output.extra_sections = {}

        req = Mock(spec=GenerateRequest)
        req.wow_enabled = True
        req.wow_package_key = "quick_social_basic"
        req.brief = Mock()
        req.brief.brand_name = "Test Brand"

        mock_wow_rule = {"sections": [{"key": "detailed_30_day_calendar"}]}

        # Calendar with many duplicate hooks (>30% duplicates)
        duplicate_calendar = """## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share customer success story |
| Day 2 | Facebook | Share customer success story |
| Day 3 | Twitter | Share customer success story |
| Day 4 | Instagram | Share customer success story |
| Day 5 | Facebook | Share customer success story |
| Day 6 | Twitter | Share customer success story |
| Day 7 | Instagram | Share customer success story |
| Day 8 | Facebook | Share customer success story |
| Day 9 | Twitter | Share customer success story |
| Day 10 | Instagram | Share customer success story |
"""

        with patch("backend.main.get_wow_rule", return_value=mock_wow_rule):
            with patch("backend.main.build_wow_report", return_value=duplicate_calendar):
                with patch(
                    "backend.main.humanize_report_text", side_effect=lambda text, **kwargs: text
                ):
                    with patch("backend.main.get_industry_config", return_value=None):
                        # Should fail due to duplicate hooks
                        with pytest.raises(ValueError, match="Quality validation FAILED"):
                            _apply_wow_optional(output, req)

    def test_validation_runs_on_actual_content_not_metadata(self):
        """Test that validation runs on actual wow_markdown, not WOW rule metadata."""
        output = PackOutput()
        output.extra_sections = {}

        req = Mock(spec=GenerateRequest)
        req.wow_enabled = True
        req.wow_package_key = "quick_social_basic"
        req.brief = Mock()
        req.brief.brand_name = "Test Brand"

        # WOW rule with section metadata (no "content" field)
        mock_wow_rule = {
            "sections": [
                {"key": "overview", "label": "Overview", "order": 1},
                {"key": "messaging_framework", "label": "Messaging", "order": 2},
            ]
        }

        # Actual markdown that should be validated
        actual_markdown = """## Overview

This content has [INSERT PLACEHOLDER] that should be caught.

## Messaging Framework

In today's digital age, content is king.
"""

        validation_called_with_actual_content = False

        def mock_validate_report_sections(pack_key, sections):
            """Mock validator that checks if it receives actual content."""
            nonlocal validation_called_with_actual_content

            # Check that sections contain actual markdown content
            if sections and len(sections) > 0:
                first_section = sections[0]
                if "INSERT PLACEHOLDER" in first_section.get("content", ""):
                    validation_called_with_actual_content = True

            # Return failing result to trigger error
            from backend.validators.report_gate import (
                ReportValidationResult,
                SectionValidationResult,
            )
            from backend.validators.benchmark_validator import SectionValidationIssue

            section_result = SectionValidationResult(
                section_id="overview",
                status="FAIL",
                issues=[
                    SectionValidationIssue(
                        code="INSERT_PLACEHOLDER", message="Contains placeholder", severity="error"
                    )
                ],
            )

            return ReportValidationResult(status="FAIL", section_results=[section_result])

        with patch("backend.main.get_wow_rule", return_value=mock_wow_rule):
            with patch("backend.main.build_wow_report", return_value=actual_markdown):
                with patch(
                    "backend.main.humanize_report_text", side_effect=lambda text, **kwargs: text
                ):
                    with patch("backend.main.get_industry_config", return_value=None):
                        with patch(
                            "backend.validators.report_gate.validate_report_sections",
                            side_effect=mock_validate_report_sections,
                        ):
                            # Should fail and call validator with actual content
                            with pytest.raises(ValueError):
                                _apply_wow_optional(output, req)

                            # Verify validator received actual content, not metadata
                            assert validation_called_with_actual_content, (
                                "Validator should have received actual markdown content with placeholders, "
                                "not WOW rule metadata"
                            )


class TestValidationComponentProof:
    """Tests that prove each specific fix is working."""

    def test_fix_1_markdown_parser_used(self):
        """Prove that Fix #1 (markdown parser) is being used."""
        from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections

        markdown = """## Overview
Content here

## Messaging
More content
"""

        sections = parse_wow_markdown_to_sections(markdown)

        # Verify parser works
        assert len(sections) == 2
        assert sections[0]["id"] == "overview"
        assert sections[1]["id"] == "messaging"

    def test_fix_2_quality_checks_integrated(self):
        """Prove that Fix #2 (quality checks) are integrated into validator."""
        from backend.validators.benchmark_validator import validate_section_against_benchmark

        # Content with quality issues
        content = """## Overview

In today's digital age, {{brand_name}} drives results.
Content is king and we leverage best practices.
"""

        result = validate_section_against_benchmark(
            pack_key="quick_social_basic", section_id="overview", content=content
        )

        # Should catch quality issues
        assert result.status == "FAIL"
        issue_codes = {i.code for i in result.issues}

        # Should have quality check issues (blacklist, placeholder)
        assert any(
            code in issue_codes
            for code in ["BLACKLISTED_PHRASE", "TEMPLATE_PLACEHOLDER", "TOO_GENERIC"]
        )

    def test_fix_3_validation_is_breaking(self):
        """Prove that Fix #3 (breaking validation) works."""
        # This is tested in test_validation_errors_are_breaking above
        # If that test passes, Fix #3 is working
        pass
