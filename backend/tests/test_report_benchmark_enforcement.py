"""
Unit tests for backend.validators.report_enforcer.

These tests focus on the control flow of enforce_benchmarks_with_regen:
- Passing scenario (no regeneration).
- Single-regeneration success scenario.
- Failure after max attempts raises BenchmarkEnforcementError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

import pytest

from backend.validators import report_enforcer


@dataclass
class DummyIssue:
    code: str
    message: str
    severity: str = "error"
    details: Any = None


@dataclass
class DummySectionResult:
    section_id: str
    issues: list


class DummyValidationResult:
    def __init__(self, status: str, failing: list):
        self.status = status
        self._failing = failing

    def failing_sections(self) -> list:
        return list(self._failing)


def test_enforcer_passes_when_all_sections_ok(monkeypatch):
    """If validation passes and no failing sections, enforcer should return immediately."""

    def fake_validate(pack_key: str, sections: list):
        # Simulate a successful validation with no failures.
        return DummyValidationResult(status="PASS", failing=[])

    monkeypatch.setattr(report_enforcer, "validate_report_sections", fake_validate)

    sections = [
        {"id": "overview", "content": "Valid content with enough depth."},
        {"id": "audience_segments", "content": "Another valid section."},
    ]

    outcome = report_enforcer.enforce_benchmarks_with_regen(
        pack_key="quick_social_basic",
        sections=sections,
        regenerate_failed_sections=None,  # not needed when everything passes
    )

    assert outcome.status == "PASS"
    assert outcome.sections == sections
    assert isinstance(outcome.validation, DummyValidationResult)


def test_enforcer_regenerates_and_then_passes(monkeypatch):
    """
    If the first validation fails, but regeneration fixes it, the enforcer
    should return a passing outcome without raising.
    """

    calls = {"validate_calls": 0}

    def fake_validate(pack_key: str, sections: list):
        calls["validate_calls"] += 1
        # First call: fail on 'overview'
        if calls["validate_calls"] == 1:
            failing = [
                DummySectionResult(
                    section_id="overview",
                    issues=[DummyIssue(code="TOO_SHORT", message="Too few words.")],
                )
            ]
            return DummyValidationResult(status="FAIL", failing=failing)
        # Second call: pass
        return DummyValidationResult(status="PASS", failing=[])

    monkeypatch.setattr(report_enforcer, "validate_report_sections", fake_validate)

    original_sections = [
        {"id": "overview", "content": "Short."},
        {"id": "audience_segments", "content": "Valid content."},
    ]

    def fake_regen(failing_ids: List[str], failing_issues: List[dict]):
        # Ensure we are regenerating the expected section.
        assert failing_ids == ["overview"]
        assert len(failing_issues) == 1
        assert failing_issues[0]["section_id"] == "overview"

        # Return a new, improved overview section.
        return [
            {
                "id": "overview",
                "content": "This is now a detailed overview with enough words.",
            }
        ]

    outcome = report_enforcer.enforce_benchmarks_with_regen(
        pack_key="quick_social_basic",
        sections=list(original_sections),
        regenerate_failed_sections=fake_regen,
        max_attempts=2,
    )

    assert calls["validate_calls"] == 2
    assert outcome.status == "PASS"
    # The overview content should be the regenerated one.
    overview = {s["id"]: s for s in outcome.sections}["overview"]
    assert "detailed overview" in overview["content"]


def test_enforcer_raises_after_max_attempts(monkeypatch):
    """
    If validation keeps failing even after max_attempts, the enforcer
    must raise BenchmarkEnforcementError with the failing section IDs.
    """

    def fake_validate(pack_key: str, sections: list):
        failing = [
            DummySectionResult(
                section_id="overview",
                issues=[DummyIssue(code="TOO_SHORT", message="Too few words.")],
            )
        ]
        return DummyValidationResult(status="FAIL", failing=failing)

    monkeypatch.setattr(report_enforcer, "validate_report_sections", fake_validate)

    sections = [
        {"id": "overview", "content": "Still short."},
    ]

    def fake_regen(failing_ids, failing_issues):
        # Pretend regeneration does nothing useful.
        return [
            {"id": "overview", "content": "Still not good enough."},
        ]

    with pytest.raises(report_enforcer.BenchmarkEnforcementError) as excinfo:
        report_enforcer.enforce_benchmarks_with_regen(
            pack_key="quick_social_basic",
            sections=sections,
            regenerate_failed_sections=fake_regen,
            max_attempts=2,
        )

    msg = str(excinfo.value)
    assert "quick_social_basic" in msg
    assert "overview" in msg
