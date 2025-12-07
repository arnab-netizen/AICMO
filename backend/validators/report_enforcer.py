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
    fallback_to_original: Optional[Dict[str, str]] = None,
    draft_mode: bool = False,
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
        -> NEW: If fallback_to_original is provided for failing section IDs, use those
           original templates instead of raising an error.
        -> Otherwise, raise BenchmarkEnforcementError with details.

    Args:
        pack_key: The pack being generated (e.g. "quick_social_basic").
        sections: List of section dicts. Each must include "id" and "content".
        regenerate_failed_sections: Callback that accepts:
            - failing_ids: List[str]
            - failing_issues: List[Dict[str, Any]] (per-section issue summaries)
          and returns a NEW list of sections (matching those ids) with improved content.
        max_attempts: Maximum number of validation attempts (including the first one).
        fallback_to_original: Optional dict mapping section_id -> original template content.
          If provided, failing sections after max_attempts will transparently fall back
          to these safe template versions instead of raising errors.
        draft_mode: If True, skip strict benchmark validation and return sections as-is
          with warnings in the validation result. Useful for internal/debug iteration
          where spec compliance is not yet required. Default is False (strict mode).

    Returns:
        EnforcementOutcome with the final validated sections and validation result.

    Raises:
        BenchmarkEnforcementError: If content still fails after regeneration attempts
          AND no fallback is available AND draft_mode is False.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be >= 1")

    # Draft mode: skip strict validation and return sections as-is
    if draft_mode:
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"[DRAFT MODE] Skipping strict benchmark validation for pack '{pack_key}'")

        # Still run validation to collect metrics/warnings but don't fail
        validation = validate_report_sections(
            pack_key=pack_key,
            sections=sections,
        )

        # Return with draft status (not strictly enforced)
        return EnforcementOutcome(
            status="PASS_WITH_WARNINGS",  # Report draft status
            sections=list(sections),
            validation=validation,
        )

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

        # If we have no callback or we've reached max attempts, check for fallback.
        if regenerate_failed_sections is None or attempt >= max_attempts:
            failing_ids = [getattr(fr, "section_id", "UNKNOWN") for fr in failing]

            # DEBUG: Log detailed validation errors before raising
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"\n{'='*80}\nDETAILED VALIDATION FAILURES FOR {pack_key}:\n{'='*80}")
            for fr in failing:
                sid = getattr(fr, "section_id", "UNKNOWN")
                issues = getattr(fr, "issues", [])
                logger.error(f"\n📋 Section: {sid}")
                logger.error(f"   Total issues: {len(issues)}")
                for issue in issues[:10]:  # First 10 issues
                    code = getattr(issue, "code", "?")
                    msg = getattr(issue, "message", "?")
                    sev = getattr(issue, "severity", "?")
                    logger.error(f"   [{sev.upper()}] {code}: {msg}")
                if len(issues) > 10:
                    logger.error(f"   ... and {len(issues) - 10} more issues")
            logger.error(f"{'='*80}\n")

            # NEW: Try fallback to original template for sections that have it
            if fallback_to_original:
                fallback_applied = False
                indexed = _index_sections_by_id(current_sections)

                for sid in failing_ids:
                    if sid in fallback_to_original:
                        logger.warning(
                            f"[BENCHMARK FALLBACK] Section '{sid}' failed after {attempt} "
                            f"attempt(s). Falling back to safe template version."
                        )
                        indexed[sid] = {
                            "id": sid,
                            "content": fallback_to_original[sid],
                        }
                        fallback_applied = True

                if fallback_applied:
                    # Re-merge and validate one more time with fallback content
                    current_sections = list(indexed.values())
                    final_validation = validate_report_sections(
                        pack_key=pack_key,
                        sections=current_sections,
                    )
                    final_status = getattr(final_validation, "status", "PASS")
                    final_failing = list(final_validation.failing_sections())

                    if not final_failing:
                        logger.info(
                            f"[BENCHMARK FALLBACK] Successfully recovered with template "
                            f"fallback for {len([s for s in failing_ids if s in fallback_to_original])} section(s)"
                        )
                        return EnforcementOutcome(
                            status=final_status,
                            sections=current_sections,
                            validation=final_validation,
                        )
                    else:
                        # Even fallback failed (shouldn't happen if template is known-good)
                        logger.error(
                            "[BENCHMARK FALLBACK] Fallback templates still failed validation! "
                            "This indicates a bug in the fallback mechanism."
                        )

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
