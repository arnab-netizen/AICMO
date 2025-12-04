"""
Report-level quality gate validation.

Validates all sections of a report against their benchmarks and provides
a consolidated pass/fail result. This is the final gate before export/save.
"""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.validators.benchmark_validator import (
    SectionValidationIssue,
    SectionValidationResult,
    validate_section_against_benchmark,
)

logger = logging.getLogger(__name__)


@dataclass
class ReportValidationResult:
    """Result of validating all sections in a report."""

    pack_key: str
    status: str  # "PASS" | "PASS_WITH_WARNINGS" | "FAIL"
    section_results: List[SectionValidationResult] = field(default_factory=list)

    def failing_sections(self) -> List[SectionValidationResult]:
        """Return list of sections that failed validation."""
        return [r for r in self.section_results if r.status == "FAIL"]

    def has_errors(self) -> bool:
        """Check if any section has errors."""
        return any(r.status == "FAIL" for r in self.section_results)

    def get_error_summary(self) -> str:
        """Generate human-readable summary of errors."""
        if not self.has_errors():
            return "No errors found."

        failing = self.failing_sections()
        summary = f"Report validation failed: {len(failing)} section(s) with errors.\n\n"

        for section_result in failing:
            summary += f"Section '{section_result.section_id}':\n"
            for issue in section_result.issues:
                if issue.severity == "error":
                    summary += f"  • [{issue.code}] {issue.message}\n"

        return summary


def _get_valid_section_ids_for_pack(pack_key: str) -> set:
    """
    Get the set of valid section IDs for a given pack.

    Args:
        pack_key: Pack identifier (e.g., "strategy_campaign_standard")

    Returns:
        Set of valid section IDs for this pack
    """
    # Import here to avoid circular dependency
    try:
        from backend.main import PACK_SECTION_WHITELIST

        return PACK_SECTION_WHITELIST.get(pack_key, set())
    except ImportError:
        logger.warning(
            f"Could not import PACK_SECTION_WHITELIST, unable to filter sections for {pack_key}"
        )
        return set()


def _merge_unknown_sections(pack_key: str, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge unknown subsection headings back into their parent canonical sections.

    When WOW markdown parser splits on ALL ## headings, it treats internal subsections
    (like "## Results" within post_campaign_analysis) as separate sections. This function
    merges those unknown sections back into their parent sections.

    Args:
        pack_key: Pack identifier to determine valid section IDs
        sections: List of parsed sections from WOW markdown

    Returns:
        List of sections with unknown subsections merged into their parents

    Example:
        Input sections: [
            {"id": "post_campaign_analysis", "content": "## Post Campaign Analysis\n..."},
            {"id": "results", "content": "## Results\nMetrics here..."},
            {"id": "learnings", "content": "## Learnings\nInsights here..."}
        ]
        Output: [
            {"id": "post_campaign_analysis", "content": "## Post Campaign Analysis\n...\n\n## Results\nMetrics here...\n\n## Learnings\nInsights here..."}
        ]
    """
    valid_section_ids = _get_valid_section_ids_for_pack(pack_key)

    if not valid_section_ids:
        # If we can't determine valid sections, return original list
        logger.warning(f"No valid section IDs found for pack {pack_key}, skipping merge")
        return sections

    original_count = len(sections)
    original_ids = [s.get("id") for s in sections]

    merged_sections: List[Dict[str, Any]] = []
    current_canonical_section: Dict[str, Any] | None = None
    merged_count = 0

    for section in sections:
        section_id = section.get("id", "")
        content = section.get("content", "")

        if section_id in valid_section_ids:
            # This is a valid canonical section - save previous and start new
            if current_canonical_section is not None:
                merged_sections.append(current_canonical_section)

            current_canonical_section = {"id": section_id, "content": content}
        else:
            # Unknown section - merge into current canonical section
            if current_canonical_section is not None:
                logger.info(
                    f"[WOW MERGE] Merged subsection '{section_id}' into '{current_canonical_section['id']}'"
                )
                # Append unknown section's content to canonical section with separator
                current_canonical_section["content"] += "\n\n" + content
                merged_count += 1
            else:
                # No canonical section yet (shouldn't happen but handle gracefully)
                logger.warning(
                    f"[WOW MERGE] Found unknown section '{section_id}' before any canonical section, skipping"
                )

    # Don't forget the last canonical section
    if current_canonical_section is not None:
        merged_sections.append(current_canonical_section)

    final_ids = [s["id"] for s in merged_sections]

    logger.info(
        f"[WOW MERGE] Pack '{pack_key}': Original sections: {original_count} {original_ids} → "
        f"Canonical sections: {len(merged_sections)} {final_ids} (merged {merged_count} subsections)"
    )

    return merged_sections


def validate_report_sections(
    *, pack_key: str, sections: List[Dict[str, Any]]
) -> ReportValidationResult:
    """
    Validate all sections of a report against benchmarks.

    This is the main entry point for report-level quality validation.

    Args:
        pack_key: Pack identifier (e.g., "quick_social_basic")
        sections: List of section dicts, each with:
            - "id": section_id (str)
            - "content": rendered markdown/text (str)

    Returns:
        ReportValidationResult with overall status and per-section results

    Example:
        sections = [
            {"id": "overview", "content": "Brand: Example Co..."},
            {"id": "audience_segments", "content": "Primary Audience..."},
        ]
        result = validate_report_sections(
            pack_key="quick_social_basic",
            sections=sections
        )
        if result.has_errors():
            print(result.get_error_summary())
    """
    # STEP 1: Merge unknown subsections back into their parent canonical sections
    # This prevents WOW parser artifacts (## Results, ## Learnings) from being
    # validated as separate sections
    sections = _merge_unknown_sections(pack_key, sections)

    # STEP 2: Validate each canonical section
    results: List[SectionValidationResult] = []

    for section in sections:
        section_id = section.get("id")
        content = section.get("content") or ""

        if not section_id:
            # Hard fail – misconfigured output structure.
            issue = SectionValidationIssue(
                code="MISSING_SECTION_ID",
                message="Section dict is missing 'id' field.",
                severity="error",
            )
            res = SectionValidationResult(
                section_id="unknown",
                status="FAIL",
                issues=[issue],
            )
            results.append(res)
            continue

        res = validate_section_against_benchmark(
            pack_key=pack_key,
            section_id=section_id,
            content=content,
        )
        results.append(res)

    # Determine overall status
    if any(r.status == "FAIL" for r in results):
        status = "FAIL"
    elif any(r.status == "PASS_WITH_WARNINGS" for r in results):
        status = "PASS_WITH_WARNINGS"
    else:
        status = "PASS"

    return ReportValidationResult(
        pack_key=pack_key,
        status=status,
        section_results=results,
    )
