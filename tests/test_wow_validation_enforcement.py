"""
End-to-end test proving validation enforcement in the real WOW flow.

This test verifies that _apply_wow_to_output (the actual production function)
raises ValueError when validation fails, proving the fix is complete.
"""

import pytest
from unittest.mock import Mock

from backend.main import _apply_wow_to_output, GenerateRequest


def test_real_wow_flow_blocks_poor_quality():
    """
    CRITICAL TEST: Verify the REAL _apply_wow_to_output function blocks poor quality.

    This is the actual production code path, not a test helper.
    """
    # Poor quality markdown with multiple quality issues
    poor_quality_markdown = """## Overview

In today's digital age, {{brand_name}} leverages content marketing to drive results.
We create tangible impact through proven methodologies and industry-leading best practices.
Content is king and we'll move the needle with our cutting-edge approach.

**Brand**: Starbucks
**Industry**: Food & Beverage  
**Primary Goal**: [INSERT GOAL]

## Messaging Framework

We leverage synergy to create a game-changer in the market.
Our state-of-the-art solutions deliver best practices.
Think outside the box with our proven methodologies.
"""

    # Create mock output object with markdown content
    output = Mock()
    output.wow_markdown = poor_quality_markdown
    output.report_markdown = None
    output.extra_sections = {}
    output.wow_package_key = None

    req = Mock(spec=GenerateRequest)
    req.wow_enabled = True
    req.wow_package_key = "quick_social_basic"
    req.brief = Mock()
    req.brief.brand_name = "Starbucks"
    req.brief.industry_key = "food_beverage"
    req.brief.industry = "Food & Beverage"

    # The REAL production function should raise ValueError for poor quality
    with pytest.raises(ValueError) as exc_info:
        _apply_wow_to_output(output, req)

    # Verify it's specifically a quality validation failure
    assert "Quality validation FAILED" in str(exc_info.value) or "WOW validation FAILED" in str(
        exc_info.value
    )

    # Verify the error message includes details
    error_msg = str(exc_info.value)
    assert "quick_social_basic" in error_msg or "quality" in error_msg.lower()


def test_real_wow_flow_accepts_good_quality():
    """
    Verify the REAL _apply_wow_to_output function accepts good quality content.
    """
    # Good quality markdown
    good_quality_markdown = """## Overview

Brand: Starbucks
Industry: Food & Beverage
Primary Goal: Increase mobile app engagement by 25% through personalized rewards

Starbucks operates 15,000 retail locations across North America. They serve 100 million customers each week.
The mobile app processes 23% of all transactions. The Rewards program has 28 million active members.
Pike Place blend is their top seller. Sales reach 3.2 million pounds monthly.

The strategy focuses on mobile order-ahead. This feature handles 18% of morning rush orders.
Data shows 67% higher visit frequency. Rewards members visit stores more often than non-members.
Mobile payments grew 45% year-over-year. The app ranks third in the food category.

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
"""

    # Create mock output object with markdown content
    output = Mock()
    output.wow_markdown = good_quality_markdown
    output.report_markdown = None
    output.extra_sections = {}
    output.wow_package_key = None

    req = Mock(spec=GenerateRequest)
    req.wow_enabled = True
    req.wow_package_key = "quick_social_basic"
    req.brief = Mock()
    req.brief.brand_name = "Starbucks"
    req.brief.industry_key = "food_beverage"
    req.brief.industry = "Food & Beverage"

    # Should NOT raise - good quality passes
    result = _apply_wow_to_output(output, req)

    assert result is not None
    assert result == output


def test_validation_failure_propagates_not_swallowed():
    """
    Prove that ValueError from validation is NOT caught by outer exception handlers.

    This verifies the fix to the exception handling hierarchy.
    """
    # Poor quality markdown that will fail validation
    poor_markdown = """## Overview

In today's digital age, Starbucks drives results.
"""

    output = Mock()
    output.wow_markdown = poor_markdown
    output.report_markdown = None
    output.extra_sections = {}
    output.wow_package_key = None

    req = Mock(spec=GenerateRequest)
    req.wow_enabled = True
    req.wow_package_key = "quick_social_basic"
    req.brief = Mock()
    req.brief.brand_name = "Test"
    req.brief.industry_key = None
    req.brief.industry = None

    # Must raise, NOT be caught and logged
    with pytest.raises(ValueError, match="WOW validation FAILED|Quality validation FAILED"):
        _apply_wow_to_output(output, req)
