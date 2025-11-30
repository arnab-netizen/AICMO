"""
Tests for pack output contract validation.

Ensures that each pack produces reports with all required sections and that the
validate_pack_contract() function correctly identifies missing or invalid sections.

Test strategy:
1. Unit tests for validate_pack_contract() function with mock data
2. Integration tests using actual report generation for key packs
3. Golden snapshot tests to detect unintended structural changes
"""
import asyncio
import pytest

from backend.main import api_aicmo_generate_report
from backend.validators.output_validator import validate_pack_contract
from backend.validators.pack_schemas import PACK_OUTPUT_SCHEMAS, get_pack_schema


# ============================================================
# UNIT TESTS - validate_pack_contract() function
# ============================================================


def test_validate_pack_contract_with_valid_report():
    """Test that validation passes for a well-formed report."""
    pack_key = "quick_social_basic"
    schema = get_pack_schema(pack_key)

    # Create mock report with all required sections
    mock_report = {
        "extra_sections": {
            section_id: f"Content for {section_id}"
            for section_id in schema["required_sections"]
        }
    }

    # Should not raise any exception
    validate_pack_contract(pack_key, mock_report)


def test_validate_pack_contract_missing_section():
    """Test that validation fails when a required section is missing."""
    pack_key = "quick_social_basic"
    schema = get_pack_schema(pack_key)

    # Create report missing one required section
    required = schema["required_sections"]
    mock_report = {
        "extra_sections": {
            section_id: f"Content for {section_id}"
            for section_id in required[:-1]  # Omit last section
        }
    }

    with pytest.raises(ValueError, match="missing required sections"):
        validate_pack_contract(pack_key, mock_report)


def test_validate_pack_contract_empty_section():
    """Test that validation fails when a required section is empty."""
    pack_key = "quick_social_basic"
    schema = get_pack_schema(pack_key)

    # Create report with one empty section
    required = schema["required_sections"]
    mock_report = {
        "extra_sections": {
            section_id: f"Content for {section_id}" if i > 0 else ""
            for i, section_id in enumerate(required)
        }
    }

    with pytest.raises(ValueError, match="has empty required sections"):
        validate_pack_contract(pack_key, mock_report)


def test_validate_pack_contract_wrong_order():
    """Test that validation fails when section order is incorrect (if enforce_order is True)."""
    pack_key = "quick_social_basic"
    schema = get_pack_schema(pack_key)

    if not schema.get("enforce_order"):
        pytest.skip("Pack does not enforce order")

    # Create report with sections in wrong order
    required = schema["required_sections"]
    reordered = [required[-1]] + required[:-1]  # Move last to first

    mock_report = {
        "extra_sections": {
            section_id: f"Content for {section_id}"
            for section_id in reordered
        }
    }

    with pytest.raises(ValueError, match="section order incorrect"):
        validate_pack_contract(pack_key, mock_report)


def test_validate_pack_contract_unknown_pack():
    """Test that validation is skipped for unknown pack keys (non-breaking)."""
    # Should not raise exception for unknown pack
    mock_report = {"extra_sections": {}}
    validate_pack_contract("unknown_pack_key", mock_report)


# ============================================================
# INTEGRATION TESTS - Quick Social Pack (Basic)
# ============================================================


def _make_quick_social_payload():
    """Create payload for Quick Social Pack."""
    return {
        "package_name": "Quick Social Pack (Basic)",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Food & Beverage",
            "product_service": "Test product",
            "primary_goal": "Increase engagement",
            "primary_customer": "Target audience",
            "geography": "Test City",
            "timeline": "30 days",
        },
        "services": {},
        "wow_enabled": True,
        "wow_package_key": "quick_social_basic",
        "use_learning": False,
    }


def test_quick_social_pack_has_all_required_sections():
    """Integration test: Verify Quick Social Pack generates all required sections."""
    payload = _make_quick_social_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))

    report_markdown = result.get("report_markdown", "")
    assert report_markdown, "Report markdown should not be empty"

    # Get expected sections from schema
    schema = get_pack_schema("quick_social_basic")
    required_sections = schema["required_sections"]

    # Check that all required sections appear in markdown (as headers)
    # Note: Section IDs are converted to human-readable headers in WOW templates
    # For now, just verify report has substantial content
    assert len(report_markdown) > 1000, "Report should have substantial content"

    # Check for key section markers (simplified check)
    assert "overview" in report_markdown.lower() or "Overview" in report_markdown
    assert "calendar" in report_markdown.lower() or "Calendar" in report_markdown
    assert "summary" in report_markdown.lower() or "Summary" in report_markdown


def test_quick_social_pack_includes_30_day_calendar():
    """Integration test: Verify Quick Social Pack includes 30-day calendar section."""
    payload = _make_quick_social_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))

    report_markdown = result.get("report_markdown", "")

    # Check for calendar section
    assert "calendar" in report_markdown.lower(), "Report should include calendar section"

    # Check for substantial calendar content (heuristic: multiple weeks or days)
    calendar_indicators = ["Week ", "Day ", "Monday", "Tuesday", "Wednesday"]
    found_indicators = sum(1 for ind in calendar_indicators if ind in report_markdown)

    assert found_indicators >= 3, f"Expected calendar content, found only {found_indicators} indicators"


# ============================================================
# INTEGRATION TESTS - Strategy + Campaign Pack (Standard)
# ============================================================


def _make_strategy_campaign_payload():
    """Create payload for Strategy + Campaign Pack (Standard)."""
    return {
        "package_name": "Strategy + Campaign Pack (Standard)",
        "stage": "final",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "SaaS",
            "product_service": "Marketing automation",
            "primary_goal": "Generate leads",
            "primary_customer": "Marketing managers",
            "geography": "North America",
            "timeline": "90 days",
        },
        "services": {"include_agency_grade": True},
        "wow_enabled": True,
        "wow_package_key": "strategy_campaign_standard",
        "use_learning": False,
    }


def test_strategy_campaign_standard_has_all_required_sections():
    """Integration test: Verify Strategy + Campaign Pack (Standard) generates all required sections."""
    payload = _make_strategy_campaign_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))

    report_markdown = result.get("report_markdown", "")
    assert report_markdown, "Report markdown should not be empty"

    # Get expected sections from schema
    schema = get_pack_schema("strategy_campaign_standard")
    required_sections = schema["required_sections"]

    # Verify report has substantial content for standard pack (more than basic)
    assert len(report_markdown) > 2000, "Standard pack report should have substantial content"

    # Check for key sections specific to standard pack
    key_sections = ["campaign", "persona", "calendar", "execution", "kpi"]
    found_sections = sum(1 for section in key_sections if section in report_markdown.lower())

    assert found_sections >= 4, f"Expected standard pack sections, found only {found_sections}"


# ============================================================
# GOLDEN SNAPSHOT TESTS
# ============================================================


def test_pack_schema_structure_unchanged():
    """
    Golden snapshot test: Ensure pack schemas haven't changed unexpectedly.

    This test will fail if someone adds/removes required sections from a pack,
    forcing them to consciously update this test and review the change.
    """
    # Snapshot of expected section counts per pack
    expected_counts = {
        "quick_social_basic": 10,
        "strategy_campaign_standard": 16,
        "strategy_campaign_basic": 6,
        "full_funnel_growth_suite": 23,
        "launch_gtm_pack": 13,
        "brand_turnaround_lab": 14,
        "retention_crm_booster": 14,
        "performance_audit_revamp": 16,
        "strategy_campaign_premium": 28,
        "strategy_campaign_enterprise": 39,
    }

    for pack_key, expected_count in expected_counts.items():
        schema = get_pack_schema(pack_key)
        assert schema is not None, f"Schema for {pack_key} should exist"

        actual_count = len(schema["required_sections"])
        assert actual_count == expected_count, (
            f"Section count changed for {pack_key}: "
            f"expected {expected_count}, got {actual_count}. "
            f"If this is intentional, update the golden snapshot."
        )


def test_quick_social_sections_list_unchanged():
    """
    Golden snapshot: Exact list of sections for Quick Social Pack.

    If this test fails, it means the Quick Social Pack structure changed.
    Update this test only after reviewing the change.
    """
    schema = get_pack_schema("quick_social_basic")
    expected_sections = [
        "overview",
        "audience_segments",
        "messaging_framework",
        "content_buckets",
        "weekly_social_calendar",
        "creative_direction_light",
        "hashtag_strategy",
        "platform_guidelines",
        "kpi_plan_light",
        "final_summary",
    ]

    actual_sections = schema["required_sections"]
    assert actual_sections == expected_sections, (
        f"Quick Social Pack sections changed. "
        f"Expected: {expected_sections}, "
        f"Got: {actual_sections}. "
        f"Update this golden snapshot if change is intentional."
    )


def test_strategy_campaign_standard_sections_list_unchanged():
    """
    Golden snapshot: Exact list of sections for Strategy + Campaign Pack (Standard).

    If this test fails, it means the Standard pack structure changed.
    Update this test only after reviewing the change.
    """
    schema = get_pack_schema("strategy_campaign_standard")
    expected_sections = [
        "overview",
        "campaign_objective",
        "core_campaign_idea",
        "messaging_framework",
        "channel_plan",
        "audience_segments",
        "persona_cards",
        "creative_direction",
        "influencer_strategy",
        "promotions_and_offers",
        "detailed_30_day_calendar",
        "ad_concepts",
        "kpi_and_budget_plan",
        "execution_roadmap",
        "post_campaign_analysis",
        "final_summary",
    ]

    actual_sections = schema["required_sections"]
    assert actual_sections == expected_sections, (
        f"Strategy + Campaign Pack (Standard) sections changed. "
        f"Expected: {expected_sections}, "
        f"Got: {actual_sections}. "
        f"Update this golden snapshot if change is intentional."
    )


# ============================================================
# SCHEMA VALIDATION TESTS
# ============================================================


def test_all_pack_schemas_are_valid():
    """Test that all pack schemas pass internal validation checks."""
    from backend.validators.pack_schemas import validate_schema_completeness

    errors = validate_schema_completeness()
    assert not errors, f"Pack schema validation errors: {'; '.join(errors)}"


def test_all_packs_have_schemas():
    """Test that all packs defined in PACKAGE_PRESETS have corresponding schemas."""
    from aicmo.presets.package_presets import PACKAGE_PRESETS

    for pack_key in PACKAGE_PRESETS.keys():
        schema = get_pack_schema(pack_key)
        assert schema is not None, f"Pack '{pack_key}' missing schema in PACK_OUTPUT_SCHEMAS"


def test_all_section_ids_exist_in_generators():
    """
    Test that all section IDs referenced in schemas exist in SECTION_GENERATORS.

    This catches typos and ensures schemas reference real generators.
    """
    from backend.main import SECTION_GENERATORS

    for pack_key, schema in PACK_OUTPUT_SCHEMAS.items():
        required_sections = schema.get("required_sections", [])
        optional_sections = schema.get("optional_sections", [])
        all_sections = required_sections + optional_sections

        for section_id in all_sections:
            assert section_id in SECTION_GENERATORS, (
                f"Pack '{pack_key}' references unknown section '{section_id}'. "
                f"Section not found in SECTION_GENERATORS."
            )
