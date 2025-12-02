"""
Language Quality Test Suite

Tests generated pack content for:
1. No template placeholders ({brand_name}, INSERT, TBD, <<...>>)
2. No broken punctuation (& ., .., ,,)
3. No template artifacts (repeated letters, "Se " instead of "See ")
4. No generic filler phrases
5. Proper capitalization and formatting

These tests are BRAND-AGNOSTIC - they check for unacceptable patterns,
not specific content.
"""

import pytest
import re
from backend.main import GenerateRequest, _gen_quick_social_30_day_calendar
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


def create_test_request(
    brand_name="TestBrand", industry="Coffeehouse / Beverage Retail", section_key="brand_snapshot"
):
    """Create minimal GenerateRequest for testing"""
    brief = ClientInputBrief(
        brand=BrandBrief(
            brand_name=brand_name,
            industry=industry,
            primary_goal="increase engagement",
            primary_customer="busy professionals",
            product_service="premium coffee",
            location="Seattle, WA",
            secondary_customer="tourists",
            brand_tone="friendly, welcoming",
            timeline="30 days",
        ),
        audience=AudienceBrief(
            primary_customer="busy professionals",
            secondary_customer="tourists",
            pain_points=["finding quality service", "limited time"],
            online_hangouts=["Instagram", "LinkedIn"],
        ),
        goal=GoalBrief(
            primary_goal="increase engagement",
            timeline="30 days",
            kpis=["engagement rate", "followers"],
        ),
        voice=VoiceBrief(
            tone_of_voice=["friendly", "professional"],
        ),
        product_service=ProductServiceBrief(
            current_offers="premium coffee and pastries",
            testimonials_or_proof="4.8/5 stars from customers",
        ),
        assets_constraints=AssetsConstraintsBrief(
            focus_platforms=["Instagram", "LinkedIn"],
        ),
        operations=OperationsBrief(
            needs_calendar=True,
        ),
        strategy_extras=StrategyExtrasBrief(
            brand_adjectives=["friendly", "welcoming", "quality"],
            success_30_days="20% increase in social engagement",
            tagline="Your daily coffee ritual",
        ),
    )

    req = GenerateRequest(
        brief=brief,
        package_preset="quick_social_basic",
        section_keys=[section_key],
    )
    return req


# ============================================================================
# TEST 1: No Template Placeholders
# ============================================================================


PLACEHOLDER_PATTERNS = [
    r"\{brand_name\}",
    r"\{industry\}",
    r"\{product_service\}",
    r"\{primary_customer\}",
    r"\{location\}",
    r"<<.*?>>",  # Template markers
    r"\[INSERT.*?\]",
    r"\[TBD.*?\]",
    r"\[PLACEHOLDER.*?\]",
    r"\[YOUR.*?\]",
    r"{{.*?}}",  # Jinja-style templates
    r"%\(.*?\)s",  # Python string format
]


def test_no_template_placeholders_in_output():
    """
    Generated content must not contain unresolved template placeholders.

    Examples of INVALID output:
    - "Welcome to {brand_name}"
    - "[INSERT DESCRIPTION HERE]"
    - "<<CAMPAIGN OBJECTIVE>>"

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    # Check for placeholder patterns
    found_placeholders = []
    for pattern in PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        if matches:
            found_placeholders.extend(matches)

    assert len(found_placeholders) == 0, (
        f"Found {len(found_placeholders)} template placeholders in output: "
        f"{found_placeholders[:5]}"
    )


# ============================================================================
# TEST 2: No Broken Punctuation
# ============================================================================


BROKEN_PUNCTUATION_PATTERNS = [
    (r" & \.", "Space-ampersand-space-period"),
    (r"\.\.\.", "Triple periods (not ellipsis)"),
    (r",,", "Double commas"),
    (r" ,$", "Space-comma at end of line"),
]


def test_no_broken_punctuation():
    """
    Generated content must not contain broken punctuation patterns.

    Examples of INVALID output:
    - "Great service & ."
    - "We offer coffee.. and tea"
    - "Visit us today ,,"

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    found_issues = []
    for pattern, description in BROKEN_PUNCTUATION_PATTERNS:
        if re.search(pattern, content):
            found_issues.append(description)

    assert len(found_issues) == 0, f"Found broken punctuation patterns: {found_issues}"


# ============================================================================
# TEST 3: No Template Artifacts
# ============================================================================


TEMPLATE_ARTIFACTS = [
    (r"customersss\b", "Repeated letters (customersss)"),
    (r"coffeee\b", "Repeated letters (coffeee)"),
    (r"\bSe\s", "Corrupted 'See' → 'Se'"),
    (r"\bscros\b", "Corrupted 'across' → 'scros'"),
    (r"\bsucces\b(?!s)", "Corrupted 'success' → 'succes'"),
    (r"\bawarenes\b(?!s)", "Corrupted 'awareness' → 'awarenes'"),
    (r"\.\s+And\b", "Broken sentence join (. And)"),
    (r"\.\s+Or\b", "Broken sentence join (. Or)"),
    (r"\.\s+But\b", "Broken sentence join (. But)"),
]


def test_no_template_artifacts():
    """
    Generated content must not contain template artifacts or corruption.

    Examples of INVALID output:
    - "We target customersss in the area"
    - "Se our latest offers"
    - "Great coffee. And amazing service."

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    found_artifacts = []
    for pattern, description in TEMPLATE_ARTIFACTS:
        if re.search(pattern, content, re.IGNORECASE):
            found_artifacts.append(description)

    assert len(found_artifacts) == 0, f"Found template artifacts: {found_artifacts}"


# ============================================================================
# TEST 4: No Generic Filler Phrases
# ============================================================================


GENERIC_FILLER_PHRASES = [
    "in today's digital age",
    "content is king",
    "cutting-edge solutions",
    "world-class service",
    "state-of-the-art",
    "best in class",
    "industry-leading",
    "unparalleled",
    "revolutionary",
    "game-changing",
    "next-generation",
    "innovative solutions",  # Too vague
    "leverage synergies",  # Corporate jargon
]


def test_no_generic_filler_phrases():
    """
    Generated content should avoid generic marketing clichés.

    Examples of INVALID output:
    - "In today's digital age, content is king"
    - "Our cutting-edge solutions leverage synergies"

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    found_filler = []
    for phrase in GENERIC_FILLER_PHRASES:
        if phrase.lower() in content.lower():
            found_filler.append(phrase)

    # Allow 1-2 occurrences but not excessive
    assert len(found_filler) <= 2, (
        f"Found {len(found_filler)} generic filler phrases: " f"{found_filler[:3]}"
    )


# ============================================================================
# TEST 5: Proper Formatting
# ============================================================================


def test_proper_section_structure():
    """
    Content should have proper markdown structure:
    - Section header (## Title)
    - Multiple lines (not empty)
    - Reasonable length

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    # Should have header
    assert "##" in content, "Content should have ## header"

    # Should have multiple lines
    lines = content.split("\n")
    assert len(lines) >= 10, f"Content too short: {len(lines)} lines"

    # Should not be excessively long (calendar should be reasonable size)
    assert len(content) < 10000, f"Content too long: {len(content)} chars"


# ============================================================================
# TEST 6: No Excessive Whitespace
# ============================================================================


def test_no_excessive_whitespace():
    """
    Content should not have excessive whitespace.

    - No triple+ newlines
    - No excessive double spaces in non-table content

    This test is brand-agnostic.
    """
    req = create_test_request()
    content = _gen_quick_social_30_day_calendar(req)

    # Check for triple newlines
    assert "\n\n\n" not in content, "Found triple newlines"

    # Check for double spaces in non-table lines
    lines_with_double_spaces = []
    for line in content.split("\n"):
        # Ignore markdown table rows (they naturally have double spaces)
        if not line.strip().startswith("|"):
            if "  " in line:
                lines_with_double_spaces.append(line[:50])

    # Tables are OK, but non-table content shouldn't have many double spaces
    assert len(lines_with_double_spaces) <= 3, (
        f"Found {len(lines_with_double_spaces)} non-table lines with double spaces: "
        f"{lines_with_double_spaces[:2]}"
    )


# ============================================================================
# TEST 7: Brand Name Consistency
# ============================================================================


def test_brand_name_appears_correctly():
    """
    Brand name should appear in the content and be properly formatted.

    This test verifies the brand name is actually used, not replaced
    with generic terms.

    This test IS brand-specific by design - it verifies personalization works.
    """
    brand_name = "StarbucksTest"
    req = create_test_request(brand_name=brand_name)
    content = _gen_quick_social_30_day_calendar(req)

    # Brand name should appear at least once
    assert brand_name in content, f"Brand name '{brand_name}' not found in output"

    # Should not be over-replaced with generic terms
    generic_replacements = [
        "your brand",
        "the brand",
        "your business",
        "the business",
        "your company",
    ]
    for generic in generic_replacements:
        count = content.lower().count(generic.lower())
        # Calendar is shorter, allow fewer generic terms
        assert (
            count <= 3
        ), f"Generic term '{generic}' appears {count} times - use brand name instead"


# ============================================================================
# TEST 8: Cross-Industry Test
# ============================================================================


@pytest.mark.parametrize(
    "industry",
    [
        "Coffeehouse / Beverage Retail",
        "SaaS / Technology",
        "Fashion / Apparel",
        "Fitness / Wellness",
    ],
)
def test_language_quality_works_for_any_industry(industry):
    """
    Language quality must be maintained across different industries.

    This proves the cleanup system is truly generic.
    """
    req = create_test_request(industry=industry)
    content = _gen_quick_social_30_day_calendar(req)

    # Basic quality checks
    assert len(content) > 500, f"Output too short for {industry}"
    assert not re.search(r"\{.*?\}", content), f"Placeholders found for {industry}"
    assert " & ." not in content, f"Broken punctuation for {industry}"
    # Industry should appear (case-insensitive since it gets lowercased in hooks)
    assert industry.lower() in content.lower(), f"Industry not mentioned for {industry}"


if __name__ == "__main__":
    # Allow running directly for quick testing
    import sys

    pytest.main([__file__, "-v"] + sys.argv[1:])
