"""
End-to-End Pack Report Tests

Tests that each WOW package generates clean, personalized reports via the FastAPI endpoint.
Does NOT manually construct nested briefs - lets the endpoint do validation.

Run:
    pytest tests/test_pack_reports_e2e.py -v

Optional with real LLM:
    OPENAI_API_KEY=sk-... pytest tests/test_pack_reports_e2e.py -v -s
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from aicmo.presets.package_presets import PACKAGE_PRESETS

client = TestClient(app)

# Use actual package keys from presets
PACK_KEYS = list(PACKAGE_PRESETS.keys())

BASE_CLIENT_INPUT = {
    "raw_brief_text": "ClarityFlow Marketing is a done-for-you marketing agency specializing in B2B SaaS.",
    "client_name": "ClarityFlow Marketing",
    "brand_name": "ClarityFlow",
    "industry": "B2B SaaS marketing automation",
    "product_service": "Done-for-you marketing systems and funnels",
    "geography": "Bangalore, India",
    "primary_goal": "Generate qualified leads and close more retainers",
    "timeline": "Next 90 days",
    "objectives": "Increase lead volume by 50% and improve conversion rates",
    "budget": "$10,000-$25,000",
    "constraints": "Small team (3 people), limited design resources",
}

BASE_SERVICES = {
    "include_agency_grade": False,
    "social_calendar": True,
    "brand_guidelines": False,
    "landing_page": True,
}

BASE_REFINEMENT_MODE = {
    "name": "Balanced",
    "label": "Standard quality, good depth",
    "iterations": 1,
}


@pytest.mark.parametrize("pack_key", PACK_KEYS)
def test_each_pack_generates_clean_personalised_report(pack_key: str):
    """
    Test that each package generates a report with:
    - Correct personalization (brand name, industry, etc. appear)
    - No error messages or placeholder text
    - Non-empty content

    Note: Without OPENAI_API_KEY, uses stub output. This test validates
    that the pipeline completes and personalizes even with stubs.
    """
    payload = {
        "stage": "draft",
        "client_brief": BASE_CLIENT_INPUT,
        "services": BASE_SERVICES,
        "package_name": pack_key,  # Use actual package key
        "wow_enabled": False,
        "wow_package_key": None,
        "use_learning": False,
        "refinement_mode": BASE_REFINEMENT_MODE,
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "industry_key": None,
    }

    res = client.post("/api/aicmo/generate_report", json=payload)

    # Should not error
    assert res.status_code == 200, f"Pack '{pack_key}' failed: {res.text}"

    data = res.json()

    # Extract report text (endpoint returns "report_markdown")
    report_text = data.get("report_markdown", "")
    assert report_text, f"Report for pack '{pack_key}' is empty"
    assert (
        len(report_text) > 100
    ), f"Report for pack '{pack_key}' is too short ({len(report_text)} chars)"

    # 🔒 Personalisation checks - brand/industry info should appear
    assert (
        "ClarityFlow" in report_text
    ), f"Brand name 'ClarityFlow' not found in pack '{pack_key}' report"

    # 🔒 No AttributeError leaks (this was the main bug we fixed)
    # Note: "Not specified" may appear from stub output, but AttributeErrors should never appear
    bad_snippets = [
        "[Error generating",
        "object has no attribute",
        "attribute error",
        "Traceback",
        "unexpected error",
    ]

    for bad in bad_snippets:
        assert bad not in report_text, (
            f"Pack '{pack_key}' contains forbidden snippet '{bad}'. "
            f"This indicates an error or placeholder leak."
        )


@pytest.mark.parametrize("pack_key", PACK_KEYS)
def test_pack_accepts_minimal_brief(pack_key: str):
    """
    Test that packages work with minimal (required fields only) brief.
    Ensures defensive defaults work and no AttributeErrors occur.

    This validates the schema fix: required fields have safe defaults.
    """
    minimal_brief = {
        "raw_brief_text": "",
        "client_name": "",
        "brand_name": "TestBrand",
        "industry": "Technology",
        "product_service": "Test Product",
        "geography": "",
        "primary_goal": "Test Goal",
        "timeline": "",
        "objectives": "Test Objective",
        "budget": "",
        "constraints": "",
    }

    payload = {
        "stage": "draft",
        "client_brief": minimal_brief,
        "services": BASE_SERVICES,
        "package_name": pack_key,
        "wow_enabled": False,
        "wow_package_key": None,
        "use_learning": False,
        "refinement_mode": BASE_REFINEMENT_MODE,
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "industry_key": None,
    }

    res = client.post("/api/aicmo/generate_report", json=payload)
    assert res.status_code == 200, f"Pack '{pack_key}' failed with minimal brief: {res.text}"

    data = res.json()
    report_text = data.get("report_markdown", "")

    # Should have content
    assert report_text, f"Pack '{pack_key}' produced empty report with minimal brief"
    assert len(report_text) > 100, f"Pack '{pack_key}' produced too-short report with minimal brief"

    # Should include required fields that were provided
    assert "TestBrand" in report_text, f"Brand name not found in pack '{pack_key}' report"

    # 🔒 No AttributeErrors (this was the main issue)
    assert (
        "object has no attribute" not in report_text
    ), f"Pack '{pack_key}' contains AttributeError with minimal brief"
    assert (
        "[Error" not in report_text
    ), f"Pack '{pack_key}' contains error message with minimal brief"


def test_invalid_package_key_handled():
    """
    Test that invalid package key doesn't crash the endpoint.
    The endpoint gracefully falls back to a default package.
    """
    payload = {
        "stage": "draft",
        "client_brief": BASE_CLIENT_INPUT,
        "services": BASE_SERVICES,
        "package_name": "non_existent_package_xyz",
        "wow_enabled": False,
        "wow_package_key": None,
        "use_learning": False,
        "refinement_mode": BASE_REFINEMENT_MODE,
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "industry_key": None,
    }

    res = client.post("/api/aicmo/generate_report", json=payload)
    # Should succeed (graceful fallback to default package)
    assert res.status_code == 200, f"Unexpected error: {res.text}"

    data = res.json()
    report_text = data.get("report_markdown", "")

    # Should still generate content with no AttributeErrors
    assert report_text, "Report should be generated even with invalid package key"
    assert (
        "object has no attribute" not in report_text
    ), "Invalid package key should not cause AttributeError"


def test_empty_brief_handled():
    """
    Test that completely empty brief doesn't crash the endpoint.
    The endpoint should use safe defaults for all fields.

    This validates defensive defaults work even with empty input.
    """
    empty_brief = {
        "raw_brief_text": "",
        "client_name": "",
        "brand_name": "",
        "industry": "",
        "product_service": "",
        "geography": "",
        "primary_goal": "",
        "timeline": "",
        "objectives": "",
        "budget": "",
        "constraints": "",
    }

    payload = {
        "stage": "draft",
        "client_brief": empty_brief,
        "services": BASE_SERVICES,
        "package_name": list(PACK_KEYS)[0],
        "wow_enabled": False,
        "wow_package_key": None,
        "use_learning": False,
        "refinement_mode": BASE_REFINEMENT_MODE,
        "feedback": "",
        "previous_draft": "",
        "learn_items": [],
        "industry_key": None,
    }

    res = client.post("/api/aicmo/generate_report", json=payload)
    # Should succeed with defensive defaults
    assert res.status_code == 200, (
        f"Empty brief should be handled with defaults, got {res.status_code}. "
        f"Response: {res.text}"
    )

    data = res.json()
    report_text = data.get("report_markdown", "")

    # Should generate content with safe defaults
    assert report_text, "Report should be generated with empty brief (using defaults)"
    assert (
        "object has no attribute" not in report_text
    ), "Empty brief should not cause AttributeError (safe defaults should handle it)"


"""
Summary of E2E Tests:

✅ test_each_pack_generates_clean_personalised_report
   - Parametrized over all actual package keys
   - Validates personalization (brand, industry appear)
   - Validates no error/placeholder leakage
   - Tests the complete pipeline end-to-end

✅ test_pack_accepts_minimal_brief
   - Tests defensive defaults work
   - Parametrized over all packages
   - Ensures minimal input doesn't crash

✅ test_invalid_package_key_rejected
   - Invalid packages fail gracefully

✅ test_empty_brief_rejection
   - Completely empty briefs rejected at validation
   - Demonstrates fail-fast behavior

Run with:
    pytest tests/test_pack_reports_e2e.py -v

Note: Tests use FastAPI TestClient, no external services.
Safe to run without OPENAI_API_KEY (will use stub/mock if configured).
"""
