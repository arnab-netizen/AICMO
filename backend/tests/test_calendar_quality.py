"""
Calendar Quality Test Suite

Tests 30-day content calendar generation for:
1. No duplicate hooks across 30 days
2. No empty hooks or CTAs
3. No truncated/broken text
4. Proper field population (date, platform, theme, etc.)
5. Valid asset types and status

These tests are BRAND-AGNOSTIC - they verify quality patterns,
not brand-specific content.
"""

import pytest
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


def create_test_request(brand_name="TestBrand", industry="Coffeehouse / Beverage Retail"):
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
    )
    return req


# ============================================================================
# TEST 1: No Duplicate Hooks
# ============================================================================


def test_no_duplicate_hooks_in_30_day_calendar():
    """
    CRITICAL: 30-day calendar must have unique hooks for each day.

    This test is brand-agnostic - it works for any brand/industry.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    # Extract hooks from markdown table
    hooks = []
    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            # Parse: | Date | Day | Platform | Theme | Hook | CTA | Asset Type | Status |
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:  # Has all columns
                hook = parts[5]  # Hook is 5th column (0-indexed after leading |)
                if hook and hook != "Hook":  # Skip header row
                    hooks.append(hook)

    # Assert: All hooks should be unique
    assert len(hooks) == 30, f"Expected 30 hooks, got {len(hooks)}"

    duplicates = [hook for hook in set(hooks) if hooks.count(hook) > 1]
    assert len(duplicates) == 0, f"Found {len(duplicates)} duplicate hooks: {duplicates[:3]}"


# ============================================================================
# TEST 2: No Empty Hooks
# ============================================================================


def test_no_empty_hooks():
    """
    All hooks must be non-empty and substantial (>= 10 characters).

    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    hooks = []
    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                hook = parts[5]
                if hook and hook != "Hook":
                    hooks.append(hook)

    # Assert: No empty hooks
    empty_hooks = [h for h in hooks if not h or len(h) < 10]
    assert len(empty_hooks) == 0, f"Found {len(empty_hooks)} empty/too-short hooks: {empty_hooks}"


# ============================================================================
# TEST 3: No Empty CTAs
# ============================================================================


def test_no_empty_ctas():
    """
    All CTAs must be non-empty and substantial.

    CTAs like "", ".", "-" are invalid.
    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    ctas = []
    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                cta = parts[6]  # CTA is 6th column
                if cta and cta != "CTA":
                    ctas.append(cta)

    # Assert: No empty CTAs
    invalid_ctas = [c for c in ctas if not c or c in ["", ".", "-"] or len(c) < 5]
    assert len(invalid_ctas) == 0, f"Found {len(invalid_ctas)} invalid CTAs: {invalid_ctas}"


# ============================================================================
# TEST 4: No Truncated Text
# ============================================================================


def test_no_truncated_hooks_or_ctas():
    """
    Hooks and CTAs must not have truncation markers like trailing dashes.

    Examples of truncation:
    - "Limited time—" (ends with em-dash)
    - "Flash: limited-" (ends with hyphen mid-word)

    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    hooks = []
    ctas = []
    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                hook = parts[5]
                cta = parts[6]
                if hook and hook != "Hook":
                    hooks.append(hook)
                if cta and cta != "CTA":
                    ctas.append(cta)

    # Check for truncation markers
    truncated_hooks = [h for h in hooks if h.endswith("—") or h.endswith("-")]
    truncated_ctas = [c for c in ctas if c.endswith("—") or c.endswith("-")]

    assert (
        len(truncated_hooks) == 0
    ), f"Found {len(truncated_hooks)} truncated hooks: {truncated_hooks}"
    assert len(truncated_ctas) == 0, f"Found {len(truncated_ctas)} truncated CTAs: {truncated_ctas}"


# ============================================================================
# TEST 5: Proper Field Population
# ============================================================================


def test_all_calendar_fields_populated():
    """
    Every row must have all required fields:
    - Date (formatted)
    - Day number
    - Platform (Instagram/LinkedIn/Twitter)
    - Theme
    - Hook
    - CTA
    - Asset Type
    - Status

    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    rows_with_missing_fields = []
    row_count = 0

    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            # Skip header row (contains "Day" as column header, not "Day 1", "Day 2", etc.)
            if "Platform" in line and "Hook" in line and "CTA" in line:
                continue  # This is the header row

            parts = [p.strip() for p in line.split("|")]
            row_count += 1

            # Should have 9 parts: ['', 'Date', 'Day', 'Platform', 'Theme', 'Hook', 'CTA', 'Asset', 'Status', '']
            # (Leading and trailing | create empty strings)
            if len(parts) < 9:
                rows_with_missing_fields.append(line)
                continue

            # Check each required field is non-empty
            date_val = parts[1]
            day_val = parts[2]
            platform = parts[3]
            theme = parts[4]
            hook = parts[5]
            cta = parts[6]
            asset = parts[7]
            status = parts[8]

            if not all([date_val, day_val, platform, theme, hook, cta, asset, status]):
                rows_with_missing_fields.append(line)

    assert row_count == 30, f"Expected 30 rows, got {row_count}"
    assert len(rows_with_missing_fields) == 0, (
        f"Found {len(rows_with_missing_fields)} rows with missing fields: "
        f"{rows_with_missing_fields[:2]}"
    )


# ============================================================================
# TEST 6: Valid Platforms
# ============================================================================


def test_valid_platforms():
    """
    All platforms must be valid: Instagram, LinkedIn, or Twitter.

    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    valid_platforms = {"Instagram", "LinkedIn", "Twitter"}
    platforms = []

    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 7:
                platform = parts[3]
                if platform and platform != "Platform":
                    platforms.append(platform)

    invalid_platforms = [p for p in platforms if p not in valid_platforms]
    assert len(invalid_platforms) == 0, f"Found invalid platforms: {set(invalid_platforms)}"


# ============================================================================
# TEST 7: Valid Asset Types
# ============================================================================


def test_valid_asset_types():
    """
    All asset types must be valid for their platform.

    Instagram: reel, static_post, carousel
    LinkedIn: static_post, document, carousel
    Twitter: short_post, thread

    This test is brand-agnostic.
    """
    req = create_test_request()
    calendar_md = _gen_quick_social_30_day_calendar(req)

    valid_asset_types = {
        "Instagram": {"reel", "static_post", "carousel"},
        "LinkedIn": {"static_post", "document", "carousel"},
        "Twitter": {"short_post", "thread"},
    }

    invalid_combinations = []

    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 8:
                platform = parts[3]
                asset_type = parts[7]

                if (
                    platform
                    and asset_type
                    and platform != "Platform"
                    and asset_type != "Asset Type"
                ):
                    if platform in valid_asset_types:
                        if asset_type not in valid_asset_types[platform]:
                            invalid_combinations.append((platform, asset_type))

    assert len(invalid_combinations) == 0, (
        f"Found {len(invalid_combinations)} invalid platform/asset combinations: "
        f"{invalid_combinations[:3]}"
    )


# ============================================================================
# TEST 8: Brand-Agnostic Test - Works for Multiple Industries
# ============================================================================


@pytest.mark.parametrize(
    "brand_name,industry",
    [
        ("CoffeeShop", "Coffeehouse / Beverage Retail"),
        ("FitGym", "Fitness / Wellness"),
        ("TechSaaS", "SaaS / Technology"),
        ("FashionBrand", "Fashion / Apparel"),
    ],
)
def test_calendar_works_for_any_industry(brand_name, industry):
    """
    Calendar generation must work for ANY brand/industry combination.

    This proves the system is generic, not hardcoded to specific brands.
    """
    req = create_test_request(brand_name=brand_name, industry=industry)
    calendar_md = _gen_quick_social_30_day_calendar(req)

    # Basic sanity checks
    assert len(calendar_md) > 1000, f"Calendar too short for {brand_name}"
    assert brand_name in calendar_md, "Brand name not found in calendar"

    # Count rows (excluding header)
    row_count = 0
    for line in calendar_md.split("\n"):
        if line.startswith("|") and "Day " in line:
            # Skip header row
            if "Platform" in line and "Hook" in line:
                continue
            row_count += 1

    assert row_count == 30, f"Expected 30 rows for {brand_name}, got {row_count}"

    # Check no obvious errors
    assert "ERROR" not in calendar_md.upper()
    assert "NONE" not in calendar_md.upper()
    assert "EXCEPTION" not in calendar_md.upper()


if __name__ == "__main__":
    # Allow running directly for quick testing
    import sys

    pytest.main([__file__, "-v"] + sys.argv[1:])
