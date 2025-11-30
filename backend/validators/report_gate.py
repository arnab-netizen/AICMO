"""
Report-level quality gate validation.

Validates all sections of a report against their benchmarks and provides
a consolidated pass/fail result. This is the final gate before export/save.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List

from backend.validators.benchmark_validator import (
    SectionValidationIssue,
    SectionValidationResult,
    validate_section_against_benchmark,
)


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
