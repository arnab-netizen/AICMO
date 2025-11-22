"""Test SECTION_MAPPING validation for Phase L learning system."""

import pytest
from aicmo.io.client_reports import AICMOOutputReport
from backend.services.learning import SECTION_MAPPING


def test_section_mapping_fields_exist_on_model():
    """
    Verify all SECTION_MAPPING field names exist on AICMOOutputReport.

    This test validates that every field referenced in SECTION_MAPPING is actually
    a field on the AICMOOutputReport Pydantic model. If a field is missing, it indicates
    a configuration mismatch that would break learn_from_report().
    """

    # Get all field names defined in AICMOOutputReport model
    report_fields = set(AICMOOutputReport.model_fields.keys())

    # Get all field names referenced in SECTION_MAPPING
    mapped_fields = {field_name for _, field_name in SECTION_MAPPING}

    # Verify each SECTION_MAPPING field exists on the report model
    missing_fields = mapped_fields - report_fields
    assert not missing_fields, (
        f"SECTION_MAPPING references non-existent fields: {missing_fields}. "
        f"Available fields: {sorted(report_fields)}"
    )

    # Verify no duplicate mappings
    assert len(SECTION_MAPPING) == len(mapped_fields), (
        f"SECTION_MAPPING has duplicate field names. " f"Mapping: {SECTION_MAPPING}"
    )

    # Verify all expected fields are present
    expected_fields = {
        "marketing_plan",
        "campaign_blueprint",
        "social_calendar",
        "performance_review",
        "creatives",
        "persona_cards",
        "action_plan",
    }
    assert expected_fields == mapped_fields, (
        f"SECTION_MAPPING fields don't match expected set. "
        f"Expected: {expected_fields}, Got: {mapped_fields}"
    )


def test_section_mapping_structure():
    """Verify SECTION_MAPPING has correct structure (tuples of display_name, field_name)."""

    # Each item in SECTION_MAPPING should be a 2-tuple
    for i, item in enumerate(SECTION_MAPPING):
        assert isinstance(item, tuple), f"Item {i} is not a tuple: {item}"
        assert len(item) == 2, f"Item {i} tuple has wrong length: {item}"

        display_name, field_name = item
        assert isinstance(display_name, str), f"Item {i} display_name is not str: {display_name}"
        assert isinstance(field_name, str), f"Item {i} field_name is not str: {field_name}"

        # Field names should be lowercase snake_case (simple check)
        assert field_name.islower() or "_" in field_name, (
            f"Item {i} field_name looks wrong: {field_name} " "(should be lowercase/snake_case)"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
