"""
Tests to ensure Quick Social pack stays lightweight and doesn't misuse goal text
as persona/audience labels. Uses the Streamlit-compatible wrapper `api_aicmo_generate_report`.
"""
import asyncio
import re

import pytest

from backend.main import api_aicmo_generate_report


def _make_payload():
    return {
        "package_name": "Quick Social Pack (Basic)",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Driftwood Coffee Co.",
            "industry": "Food & Beverage",
            "product_service": "Seasonal coffees and light bites",
            "primary_goal": "Grow weekday footfall and increase Instagram engagement",
            "primary_customer": "",  # simulate missing persona
            "geography": "Seattle, WA",
            "timeline": "Next 30 days",
        },
        "services": {},
        "wow_enabled": False,
        "use_learning": False,
    }


def test_quick_social_does_not_use_goal_as_persona():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    assert "Grow weekday footfall and increase Instagram engagement" in report

    # It must NOT appear as a persona phrase
    assert (
        "Grow weekday footfall and increase Instagram engagement who is actively looking"
        not in report
    )
    assert (
        "trusted by Grow weekday footfall and increase Instagram engagement" not in report
    )


def test_quick_social_calendar_has_minimum_30_days():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    # Heuristic: count lines that include an expected platform name
    calendar_rows = [
        line for line in report.splitlines() if any(p in line for p in ("Instagram", "Facebook", "LinkedIn"))
    ]

    assert len(calendar_rows) >= 30, f"Expected at least 30 calendar rows, got {len(calendar_rows)}"


def test_no_empty_persona_fields_in_quick_social():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    # Ensure we don't have empty 'Demographics:' or similar lines
    assert "Demographics:\n" not in report
    assert "Psychographics:\n" not in report
    assert "Tone preference:\n" not in report


def test_quick_social_excludes_premium_sections():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")
"""
Tests to ensure Quick Social pack stays lightweight and doesn't misuse goal text
as persona/audience labels. Uses the Streamlit-compatible wrapper `api_aicmo_generate_report`.
"""
import asyncio
import re

import pytest

from backend.main import api_aicmo_generate_report


def _make_payload():
    return {
        "package_name": "Quick Social Pack (Basic)",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Driftwood Coffee Co.",
            "industry": "Food & Beverage",
            "product_service": "Seasonal coffees and light bites",
            "primary_goal": "Grow weekday footfall and increase Instagram engagement",
            "primary_customer": "",  # simulate missing persona
            "geography": "Seattle, WA",
            "timeline": "Next 30 days",
        },
        "services": {},
        "wow_enabled": False,
        "use_learning": False,
    }


def test_quick_social_does_not_use_goal_as_persona():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    assert "Grow weekday footfall and increase Instagram engagement" in report

    # It must NOT appear as a persona phrase
    assert (
        "Grow weekday footfall and increase Instagram engagement who is actively looking"
        not in report
    )
    assert (
        "trusted by Grow weekday footfall and increase Instagram engagement" not in report
    )


def test_quick_social_calendar_has_minimum_30_days():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    # Heuristic: count lines that include an expected platform name
    calendar_rows = [
        line for line in report.splitlines() if any(p in line for p in ("Instagram", "Facebook", "LinkedIn"))
    ]

    assert len(calendar_rows) >= 30, f"Expected at least 30 calendar rows, got {len(calendar_rows)}"


def test_no_empty_persona_fields_in_quick_social():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    # Ensure we don't have empty 'Demographics:' or similar lines
    assert "Demographics:\n" not in report
    assert "Psychographics:\n" not in report
    assert "Tone preference:\n" not in report


def test_quick_social_excludes_premium_sections():
    payload = _make_payload()
    result = asyncio.get_event_loop().run_until_complete(api_aicmo_generate_report(payload))
    report = result.get("report_markdown", "")

    forbidden_headings = [
        "Outcome Forecast – 90 Days",
        "Offer Strategy & Funnel Design",
        "Customer Journey Map for Driftwood Coffee Co.",
        "Competitive Positioning Matrix",
        "Budget & Media Plan (Indicative)",
        "Hero Framework",
        "Category Tension & Entry Points",
        "Multi-Channel Funnel Blueprint",
    ]

    for heading in forbidden_headings:
        assert heading not in report