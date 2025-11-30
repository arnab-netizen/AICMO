"""
Benchmark enforcement layer for AICMO.

This module is responsible for:
- Running benchmark validation on generated sections.
- Optionally regenerating failing sections once.
- Failing loudly if content still does not meet the spec.

It does NOT know how sections are generated.
That logic is injected via a callback so this module stays decoupled
from backend.main / SECTION_GENERATORS, avoiding circular imports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence

from backend.validators.report_gate import validate_report_sections


class BenchmarkEnforcementError(RuntimeError):
    """Raised when content fails benchmarks even after regeneration attempts."""


@dataclass
class EnforcementOutcome:
    """
    Result of benchmark enforcement.

    Attributes:
        status: Validation status ("PASS", "PASS_WITH_WARNINGS").
        sections: Final list of sections after any regeneration.
        validation: The final validation result object from validate_report_sections().
    """

    status: str
    sections: List[Dict[str, str]]
    validation: Any  # concrete type lives in report_gate, keep this decoupled.


def _index_sections_by_id(
    sections: Sequence[Dict[str, str]],
) -> Dict[str, Dict[str, str]]:
    """
    Build a mapping from section_id -> section dict.

    Assumes each section has at least:
        - "id": str
        - "content": str (markdown/text)
    """
    indexed: Dict[str, Dict[str, str]] = {}
    for s in sections:
        sid = s.get("id") or s.get("section_id")
        if not sid:
            continue
        indexed[sid] = s
    return indexed


def enforce_benchmarks_with_regen(
    *,
    pack_key: str,
    sections: List[Dict[str, str]],
    regenerate_failed_sections: Optional[
        Callable[[List[str], List[Dict[str, Any]]], List[Dict[str, str]]]
    ] = None,
    max_attempts: int = 2,
) -> EnforcementOutcome:
    """
    Enforce benchmarks on a set of sections for a given pack.

    Behaviour:
    - Run validate_report_sections(pack_key, sections).
    - If status in {"PASS", "PASS_WITH_WARNINGS"} and no failing sections:
        -> Return EnforcementOutcome with final sections + validation.
    - If failing sections AND regenerate_failed_sections is provided AND attempts < max_attempts:
        -> Call regenerate_failed_sections(failing_ids, failing_issues) to get updated
           content for only those sections.
        -> Merge regenerated sections into the list and validate again.
    - If still failing after max_attempts:
        -> Raise BenchmarkEnforcementError with details.

    Args:
        pack_key: The pack being generated (e.g. "quick_social_basic").
        sections: List of section dicts. Each must include "id" and "content".
        regenerate_failed_sections: Callback that accepts:
            - failing_ids: List[str]
            - failing_issues: List[Dict[str, Any]] (per-section issue summaries)
          and returns a NEW list of sections (matching those ids) with improved content.
        max_attempts: Maximum number of validation attempts (including the first one).

    Returns:
        EnforcementOutcome with the final validated sections and validation result.

    Raises:
        BenchmarkEnforcementError: If content still fails after regeneration attempts.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    attempt = 1
    current_sections: List[Dict[str, str]] = list(sections)

    while True:
        validation = validate_report_sections(
            pack_key=pack_key,
            sections=current_sections,
        )

        status = getattr(validation, "status", None)
        failing = list(validation.failing_sections())

        # Fast path: all good
        if status in ("PASS", "PASS_WITH_WARNINGS") and not failing:
            return EnforcementOutcome(
                status=status or "PASS",
                sections=current_sections,
                validation=validation,
            )

        # If we have no callback or we've reached max attempts, fail loudly.
        if regenerate_failed_sections is None or attempt >= max_attempts:
            failing_ids = [getattr(fr, "section_id", "UNKNOWN") for fr in failing]
            raise BenchmarkEnforcementError(
                f"Benchmark validation failed for pack '{pack_key}' "
                f"after {attempt} attempt(s). Failing sections: {failing_ids}"
            )

        # Prepare data for regeneration callback
        failing_ids: List[str] = []
        failing_issues: List[Dict[str, Any]] = []

        for fr in failing:
            sid = getattr(fr, "section_id", None)
            if not sid:
                continue
            failing_ids.append(sid)
            issues_payload: List[Dict[str, Any]] = []
            for issue in getattr(fr, "issues", []):
                issues_payload.append(
                    {
                        "code": getattr(issue, "code", None),
                        "message": getattr(issue, "message", None),
                        "severity": getattr(issue, "severity", None),
                        "details": getattr(issue, "details", None),
                    }
                )
            failing_issues.append(
                {
                    "section_id": sid,
                    "issues": issues_payload,
                }
            )

        # Regenerate only failing sections
        regenerated_sections = regenerate_failed_sections(failing_ids, failing_issues)

        # Merge regenerated sections into current_sections
        indexed = _index_sections_by_id(current_sections)
        for rs in regenerated_sections:
            sid = rs.get("id") or rs.get("section_id")
            if not sid:
                continue
            indexed[sid] = rs

        current_sections = list(indexed.values())
        attempt += 1
