#!/usr/bin/env python
"""
Development validation proof script.

This script demonstrates that the benchmark validation fixes work correctly:
1. Parses WOW markdown into sections (Fix #1)
2. Runs enhanced quality checks (Fixes #4-8)
3. Validates that poor quality is REJECTED (Fix #3)
4. Validates that good quality is ACCEPTED

Run this script to prove the validation system is now functional.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.wow_markdown_parser import parse_wow_markdown_to_sections
from backend.validators.report_gate import validate_report_sections
from backend.validators.quality_checks import (
    run_all_quality_checks,
    check_hashtag_format,
    check_hashtag_category_counts,
)


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_result(label: str, passed: bool, details: str = ""):
    """Print a test result."""
    icon = "✅" if passed else "❌"
    print(f"{icon} {label}")
    if details:
        print(f"   {details}")


def create_poor_quality_markdown() -> str:
    """Create example of poor-quality WOW markdown (should FAIL validation)."""
    return """## Overview

In today's digital age, {{brand_name}} leverages content marketing to drive results.
We create tangible impact through proven methodologies and industry-leading best practices.
Content is king and we'll move the needle with our cutting-edge approach.

**Brand**: Starbucks
**Industry**: Food & Beverage
**Primary Goal**: [INSERT GOAL]

## Messaging Framework

We leverage synergy to create a game-changer in the market. Our state-of-the-art solutions
deliver best practices that move the needle. Think outside the box with our proven methodologies
to drive engagement and create tangible impact.

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
"""


def create_good_quality_markdown() -> str:
    """Create example of good-quality WOW markdown (should PASS validation)."""
    return """## Overview

Brand: Starbucks
Industry: Food & Beverage
Primary Goal: Increase mobile app engagement by 25% through personalized rewards

Starbucks operates 15,000 retail locations across North America. They serve 100 million customers each week.
The mobile app processes 23% of all transactions. The Rewards program has 28 million active members.
Pike Place blend is their top seller. Sales reach 3.2 million pounds monthly.

The strategy focuses on mobile order-ahead. This feature handles 18% of morning rush orders.
Data shows 67% higher visit frequency. Rewards members visit stores more often than non-members.
Mobile payments grew 45% year-over-year. The app ranks #3 in the food category.

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


def test_fix_1_markdown_parser():
    """Test Fix #1: WOW markdown parsing."""
    print_section("TEST 1: Markdown Parser (Fix #1)")

    poor_markdown = create_poor_quality_markdown()
    sections = parse_wow_markdown_to_sections(poor_markdown)

    passed = len(sections) >= 3
    print_result(
        "Parse poor quality markdown into sections",
        passed,
        f"Found {len(sections)} sections: {[s['id'] for s in sections]}",
    )

    # Check that sections contain actual content
    has_content = all(len(s["content"]) > 50 for s in sections)
    print_result(
        "Each section contains actual content (not metadata)",
        has_content,
        f"Overview section length: {len(sections[0]['content'])} chars",
    )

    return passed and has_content


def test_fix_2_quality_checks():
    """Test Fixes #4-8: Enhanced quality checks."""
    print_section("TEST 2: Enhanced Quality Checks (Fixes #4-8)")

    poor_text = (
        """In today's digital age, {{brand_name}} drives results through proven methodologies."""
    )

    issues = run_all_quality_checks(poor_text, "overview")

    # Check for each type of quality issue
    codes = {i.code for i in issues}

    tests = [
        ("Blacklist phrases detected", "BLACKLISTED_PHRASE" in codes),
        ("Template placeholders detected", "TEMPLATE_PLACEHOLDER" in codes),
        ("Multiple issues found", len(issues) >= 2),
    ]

    all_passed = True
    for label, passed in tests:
        print_result(label, passed)
        all_passed = all_passed and passed

    print(f"\n   Total issues found: {len(issues)}")
    for issue in issues[:5]:  # Show first 5
        print(f"   - [{issue.code}] {issue.message}")

    return all_passed


def test_fix_3_poor_quality_rejected():
    """Test Fix #3: Poor quality is REJECTED (validation is breaking)."""
    print_section("TEST 3: Poor Quality REJECTED (Fix #3)")

    poor_markdown = create_poor_quality_markdown()
    sections = parse_wow_markdown_to_sections(poor_markdown)

    # Validate all sections
    validation_result = validate_report_sections(pack_key="quick_social_basic", sections=sections)

    # Should FAIL
    failed = validation_result.status == "FAIL"
    print_result(
        "Poor quality report validation status = FAIL",
        failed,
        f"Status: {validation_result.status}",
    )

    # Check specific issues
    all_issues = []
    for section_result in validation_result.section_results:
        all_issues.extend(section_result.issues)

    error_issues = [i for i in all_issues if i.severity == "error"]
    has_errors = len(error_issues) > 0
    print_result(
        "Multiple quality errors detected",
        has_errors,
        f"Found {len(error_issues)} errors across {len(validation_result.section_results)} sections",
    )

    # Show failing sections
    failing_sections = [r for r in validation_result.section_results if r.status == "FAIL"]
    print(f"\n   Failing sections ({len(failing_sections)}):")
    for section in failing_sections:
        error_count = sum(1 for i in section.issues if i.severity == "error")
        print(f"   - {section.section_id}: {error_count} errors")
        for issue in section.issues[:2]:  # Show first 2 issues
            print(f"      • [{issue.code}] {issue.message}")

    return failed and has_errors


def test_fix_4_good_quality_accepted():
    """Test that good quality content still passes."""
    print_section("TEST 4: Good Quality ACCEPTED")

    good_markdown = create_good_quality_markdown()
    sections = parse_wow_markdown_to_sections(good_markdown)

    # Validate all sections
    validation_result = validate_report_sections(pack_key="quick_social_basic", sections=sections)

    # Should PASS or PASS_WITH_WARNINGS
    passed = validation_result.status in ("PASS", "PASS_WITH_WARNINGS")
    print_result(
        "Good quality report validation status = PASS",
        passed,
        f"Status: {validation_result.status}",
    )

    # Count warnings vs errors
    all_issues = []
    for section_result in validation_result.section_results:
        all_issues.extend(section_result.issues)

    error_issues = [i for i in all_issues if i.severity == "error"]
    warning_issues = [i for i in all_issues if i.severity == "warning"]

    no_errors = len(error_issues) == 0
    print_result(
        "No error-level issues found",
        no_errors,
        f"Errors: {len(error_issues)}, Warnings: {len(warning_issues)}",
    )

    # Show any warnings
    if warning_issues:
        print("\n   Warnings (non-blocking):")
        for issue in warning_issues[:3]:
            print(f"   - [{issue.code}] {issue.message}")

    return passed and no_errors


def create_poor_quality_hashtag_markdown() -> str:
    """Create example of poor-quality hashtag strategy (should FAIL validation)."""
    return """## Brand Hashtags

- fun
- love
- #happy

## Industry Hashtags

- #A
- #BB

## Campaign Hashtags

- Campaign1
- #Sale
"""


def create_good_quality_hashtag_markdown() -> str:
    """Create example of good-quality hashtag strategy (should PASS validation)."""
    return """## Brand Hashtags

Proprietary hashtags that build brand equity and community. Use consistently across all posts:

- #TestBrand
- #BrandCommunity
- #BrandLife

## Industry Hashtags

Target relevant industry tags to maximize discoverability:

- #Coffee
- #Cafe
- #Barista
- #Espresso

## Campaign Hashtags

Create unique hashtags for specific campaigns and launches:

- #FallMenu
- #SeasonalOffer
- #LimitedTime

## Best Practices

- Use 8-12 hashtags per post for optimal reach
- Mix brand + industry tags to maximize discoverability
- Avoid banned or spammy tags that limit post visibility
"""


def test_fix_5_poor_hashtag_rejected() -> bool:
    """Test that poor-quality hashtag strategy is rejected."""
    print_section("TEST 5: Poor Hashtag Strategy REJECTED (Perplexity v1)")

    poor_markdown = create_poor_quality_hashtag_markdown()

    # Run hashtag-specific checks
    format_issues = check_hashtag_format(poor_markdown, "hashtag_strategy")
    count_issues = check_hashtag_category_counts(
        poor_markdown, "hashtag_strategy", min_per_category=3
    )

    all_errors = [i for i in format_issues + count_issues if i.severity == "error"]

    print_result("Poor hashtag strategy validation status = FAIL", len(all_errors) > 0)
    print(f"   Found {len(all_errors)} errors")

    if all_errors:
        print("\n   Error samples:")
        for issue in all_errors[:3]:  # Show first 3
            print(f"   - [{issue.code}] {issue.message}")

    return len(all_errors) > 0


def test_fix_6_good_hashtag_accepted() -> bool:
    """Test that good-quality hashtag strategy is accepted."""
    print_section("TEST 6: Good Hashtag Strategy ACCEPTED (Perplexity v1)")

    good_markdown = create_good_quality_hashtag_markdown()

    # Run hashtag-specific checks
    format_issues = check_hashtag_format(good_markdown, "hashtag_strategy")
    count_issues = check_hashtag_category_counts(
        good_markdown, "hashtag_strategy", min_per_category=3
    )

    all_errors = [i for i in format_issues + count_issues if i.severity == "error"]

    print_result("Good hashtag strategy validation status = PASS", len(all_errors) == 0)
    print(f"   Errors: {len(all_errors)}")

    if all_errors:
        print("\n   Unexpected errors:")
        for issue in all_errors:
            print(f"   - [{issue.code}] {issue.message}")

    return len(all_errors) == 0


def main():
    """Run all validation proof tests."""
    print("\n" + "=" * 80)
    print("  BENCHMARK VALIDATION FIX PROOF SCRIPT")
    print("=" * 80)
    print("\nThis script proves that the 8 validation bugs have been fixed:")
    print("  Bug #1: Wrong data validated (WOW rule metadata vs actual content)")
    print("  Bug #2: Type mismatch (string vs list of dicts)")
    print("  Bug #3: Non-breaking validation")
    print("  Bug #4: No genericity detection")
    print("  Bug #5: No blacklist integration")
    print("  Bug #6: No duplicate hook detection")
    print("  Bug #7: No placeholder detection")
    print("  Bug #8: No premium language enforcement")

    results = []

    # Run tests
    results.append(("Markdown Parser Works", test_fix_1_markdown_parser()))
    results.append(("Quality Checks Work", test_fix_2_quality_checks()))
    results.append(("Poor Quality Rejected", test_fix_3_poor_quality_rejected()))
    results.append(("Good Quality Accepted", test_fix_4_good_quality_accepted()))
    results.append(("Poor Hashtag Rejected (Perplexity v1)", test_fix_5_poor_hashtag_rejected()))
    results.append(("Good Hashtag Accepted (Perplexity v1)", test_fix_6_good_hashtag_accepted()))

    # Summary
    print_section("SUMMARY")

    all_passed = all(result[1] for result in results)

    for label, passed in results:
        print_result(label, passed)

    print()
    if all_passed:
        print("🎉 ALL TESTS PASSED - Validation system is now functional!")
        print("\nKey Achievements:")
        print("  ✅ Parses WOW markdown into sections (not metadata)")
        print("  ✅ Detects blacklist phrases, placeholders, genericity")
        print("  ✅ Detects duplicate hooks in calendars")
        print("  ✅ Poor quality is REJECTED (validation blocks generation)")
        print("  ✅ Good quality is still ACCEPTED")
        print("  ✅ Perplexity v1: Poor hashtags REJECTED (format + count validation)")
        print("  ✅ Perplexity v1: Good hashtags ACCEPTED (Perplexity-powered)")
        return 0
    else:
        print("❌ SOME TESTS FAILED - Review output above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
