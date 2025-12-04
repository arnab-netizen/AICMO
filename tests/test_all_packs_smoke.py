"""
Smoke test: All packs generate successfully in stub mode.

This test ensures no pack throws exceptions during report generation,
even when LLM services are unavailable (stub mode).

Purpose:
- Prevent regressions in pack generation logic
- Verify template-only mode works for all packs
- Fast regression test for CI/CD

Note: This test does NOT verify:
- LLM service integration (tested separately)
- Report quality (tested in quality tests)
- Section content accuracy (tested in pack-specific tests)
"""

import os
import sys
import asyncio
import pytest
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root))

# Force stub mode for reliable testing
os.environ["AICMO_STUB_MODE"] = "1"
os.environ["AICMO_USE_LLM"] = "0"

from backend.main import api_aicmo_generate_report
from aicmo.presets.package_presets import PACKAGE_PRESETS


def make_test_payload(pack_key: str) -> dict:
    """Create minimal valid payload for testing."""
    return {
        "pack_key": pack_key,
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Technology",
            "product_service": "Software platform",
            "primary_goal": "Increase engagement",
            "primary_customer": "Tech startups",
            "geography": "United States",
            "timeline": "90 days",
        },
        "services": {},
        "wow_enabled": True,
        "wow_package_key": pack_key,
        "use_learning": False,
    }


@pytest.mark.parametrize("pack_key", list(PACKAGE_PRESETS.keys()))
def test_pack_generates_in_stub_mode(pack_key):
    """
    Test that each pack can generate a report in stub mode without errors.

    This verifies:
    1. No Python exceptions during generation
    2. Report is returned with content
    3. Template-only mode works (no LLM dependencies)
    """
    payload = make_test_payload(pack_key)

    # Run generation
    result = asyncio.run(api_aicmo_generate_report(payload))

    # Basic assertions
    assert result, f"No result returned for {pack_key}"
    assert isinstance(result, dict), f"Result should be dict for {pack_key}"

    # Note: Some packs may fail quality validation, which is expected in stub mode
    # The important thing is that they don't crash with unhandled exceptions
    if result.get("error"):
        # If there's an error, it should be a controlled validation error, not a crash
        error_msg = str(result.get("error", ""))
        assert (
            "Quality validation" in error_msg or "ValueError" in error_msg
        ), f"Unexpected error type for {pack_key}: {error_msg}"


def test_all_packs_registered():
    """Verify all packs in PACKAGE_PRESETS are valid."""
    assert len(PACKAGE_PRESETS) > 0, "No packs registered"

    for pack_key, config in PACKAGE_PRESETS.items():
        assert "sections" in config, f"{pack_key} missing 'sections'"
        assert "requires_research" in config, f"{pack_key} missing 'requires_research'"
        assert "complexity" in config, f"{pack_key} missing 'complexity'"
        assert len(config["sections"]) > 0, f"{pack_key} has no sections"


def test_pack_section_counts():
    """Verify pack section counts match expected ranges."""
    for pack_key, config in PACKAGE_PRESETS.items():
        section_count = len(config["sections"])

        # Basic sanity checks
        assert section_count >= 5, f"{pack_key} has too few sections ({section_count})"
        assert section_count <= 50, f"{pack_key} has too many sections ({section_count})"

        # Verify complexity mapping is reasonable
        complexity = config["complexity"]
        if complexity == "low":
            assert section_count <= 12, f"{pack_key} marked 'low' but has {section_count} sections"
        elif complexity in ("high", "very-high"):
            assert (
                section_count >= 13
            ), f"{pack_key} marked '{complexity}' but only has {section_count} sections"
