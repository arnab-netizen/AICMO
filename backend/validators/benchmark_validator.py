"""
Section-level benchmark validation for AICMO reports.

Validates individual sections against quality benchmarks including:
- Word count ranges
- Structural requirements (bullets, headings)
- Required and forbidden content
- Repetition detection
- Sentence length analysis
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

from backend.utils.benchmark_loader import (
    get_section_benchmark,
    is_strict_pack,
    BenchmarkNotFoundError,
)


# Sections where we want softer, format-only validation instead of strict snapshot match,
# because they are highly dynamic and have been refactored.
QUICK_SOCIAL_SOFT_VALIDATION_SECTIONS: Dict[str, Set[str]] = {
    "quick_social_basic": {
        "detailed_30_day_calendar",
        "kpi_plan_light",
        "execution_roadmap",
    }
}


@dataclass
class SectionValidationIssue:
    """Single validation issue found in a section."""

    code: str
    message: str
    severity: str = "error"  # "error" | "warning"


@dataclass
class SectionValidationResult:
    """Result of validating one section against its benchmark."""

    section_id: str
    status: str  # "PASS" | "PASS_WITH_WARNINGS" | "FAIL"
    issues: List[SectionValidationIssue] = field(default_factory=list)

    def is_ok(self) -> bool:
        """Check if validation passed (with or without warnings)."""
        return self.status in ("PASS", "PASS_WITH_WARNINGS")

    def has_errors(self) -> bool:
        """Check if there are any error-level issues."""
        return any(i.severity == "error" for i in self.issues)


def _split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using simple heuristic.

    Good enough for guard-rails without requiring NLP libraries.
    """
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p]


def _count_words(text: str) -> int:
    """Count words in text."""
    return len([t for t in re.split(r"\s+", text.strip()) if t])


def _analyse_structure(text: str) -> Tuple[int, int, int]:
    """
    Analyse markdown structure of text.

    Returns:
        Tuple of (bullet_count, heading_count, total_lines)

    Bullets: lines starting with -, *, •
    Headings: lines starting with #
    """
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    bullet_count = sum(1 for line in lines if line.lstrip().startswith(("-", "*", "•")))
    heading_count = sum(1 for line in lines if line.lstrip().startswith("#"))
    return bullet_count, heading_count, len(lines)


def _repetition_ratio(text: str) -> float:
    """
    Calculate ratio of repeated lines.

    Returns value between 0.0 (all unique) and 1.0 (all duplicates).
    """
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return 0.0
    unique = set(lines)
    return 1.0 - (len(unique) / len(lines))


def _is_quick_social_soft_section(pack_key: str, section_id: str) -> bool:
    """
    Check if a section should use soft validation instead of strict benchmark matching.

    Args:
        pack_key: Pack identifier
        section_id: Section identifier

    Returns:
        True if this section should use format-only validation
    """
    return (
        pack_key in QUICK_SOCIAL_SOFT_VALIDATION_SECTIONS
        and section_id in QUICK_SOCIAL_SOFT_VALIDATION_SECTIONS[pack_key]
    )


def _validate_soft_section(section_id: str, content: str) -> SectionValidationResult:
    """
    Perform soft/structural validation for Quick Social dynamic sections.

    Instead of comparing against a strict benchmark, we validate that the content
    meets basic structural requirements specific to each section type.

    Args:
        section_id: Section identifier
        content: Section content

    Returns:
        SectionValidationResult with validation outcome
    """
    result = SectionValidationResult(section_id=section_id, status="PASS", issues=[])
    normalized = content.strip()

    # Must not be empty
    if not normalized:
        result.status = "FAIL"
        result.issues.append(
            SectionValidationIssue(
                code="EMPTY",
                message="Section content is empty.",
                severity="error",
            )
        )
        return result

    # Section-specific structural rules
    if section_id == "detailed_30_day_calendar":
        # Require markdown table with expected columns
        has_pipe = "|" in normalized
        has_day = "Day" in normalized or "Date" in normalized
        has_platform = "Platform" in normalized

        if not (has_pipe and has_day and has_platform):
            result.status = "FAIL"
            result.issues.append(
                SectionValidationIssue(
                    code="MISSING_TABLE_STRUCTURE",
                    message="Calendar must include a markdown table with Day/Date and Platform columns.",
                    severity="error",
                )
            )

        # Check for reasonable number of rows (should have ~30 days)
        table_rows = [line for line in normalized.split("\n") if line.strip().startswith("|")]
        if len(table_rows) < 20:  # Allow some flexibility but ensure it's substantial
            result.issues.append(
                SectionValidationIssue(
                    code="TOO_FEW_CALENDAR_ROWS",
                    message=f"Calendar has only {len(table_rows)} table rows, expected at least 20.",
                    severity="warning",
                )
            )

    elif section_id == "kpi_plan_light":
        # Require KPI-related terminology
        kpi_tokens = [
            "reach",
            "engagement",
            "conversion",
            "clicks",
            "traffic",
            "impressions",
            "followers",
            "ctr",
            "roi",
        ]
        has_kpi_content = any(tok.lower() in normalized.lower() for tok in kpi_tokens)

        if not has_kpi_content:
            result.status = "FAIL"
            result.issues.append(
                SectionValidationIssue(
                    code="MISSING_KPI_CONTENT",
                    message="KPI section must include relevant metrics (reach, engagement, conversion, etc.).",
                    severity="error",
                )
            )

        # Should have some structure (bullets or numbers)
        has_structure = any(c in normalized for c in ["-", "*", "•", "1.", "2.", "3."])
        if not has_structure:
            result.issues.append(
                SectionValidationIssue(
                    code="UNSTRUCTURED_CONTENT",
                    message="KPI section should have bullets or numbered lists.",
                    severity="warning",
                )
            )

    elif section_id == "execution_roadmap":
        # Require timeline/phases
        timeline_keywords = [
            "Day 1",
            "Day 2",
            "Day 3",
            "Week 1",
            "Week 2",
            "Next 7 days",
            "Next 30 days",
            "Phase",
            "Timeline",
        ]
        has_timeline = any(keyword in normalized for keyword in timeline_keywords)

        if not has_timeline:
            result.status = "FAIL"
            result.issues.append(
                SectionValidationIssue(
                    code="MISSING_TIMELINE",
                    message="Execution roadmap must include timeline markers (Day 1, Week 1, phases, etc.).",
                    severity="error",
                )
            )

        # Should have action-oriented content
        action_keywords = [
            "setup",
            "launch",
            "create",
            "post",
            "publish",
            "monitor",
            "optimize",
            "review",
        ]
        has_actions = any(keyword.lower() in normalized.lower() for keyword in action_keywords)
        if not has_actions:
            result.issues.append(
                SectionValidationIssue(
                    code="LACKS_ACTION_ITEMS",
                    message="Execution roadmap should include action verbs (setup, launch, create, etc.).",
                    severity="warning",
                )
            )

    # Determine final status based on issues
    if any(i.severity == "error" for i in result.issues):
        result.status = "FAIL"
    elif result.issues:
        result.status = "PASS_WITH_WARNINGS"
    else:
        result.status = "PASS"

    return result


def validate_section_against_benchmark(
    *, pack_key: str, section_id: str, content: str
) -> SectionValidationResult:
    """
    Validate one section against its benchmark criteria.

    This function is safe to call from anywhere in the pipeline.

    Args:
        pack_key: Pack identifier (e.g., "quick_social_basic")
        section_id: Section identifier (e.g., "overview")
        content: Rendered markdown/text content of the section

    Returns:
        SectionValidationResult with status and any issues found
    """
    # Check for Quick Social soft validation sections first
    if _is_quick_social_soft_section(pack_key, section_id):
        return _validate_soft_section(section_id, content)

    result = SectionValidationResult(section_id=section_id, status="PASS", issues=[])

    # Check for empty content
    if not content or not content.strip():
        result.status = "FAIL"
        result.issues.append(
            SectionValidationIssue(
                code="EMPTY",
                message="Section content is empty.",
                severity="error",
            )
        )
        return result

    # Load benchmark
    try:
        benchmark = get_section_benchmark(pack_key, section_id)
    except BenchmarkNotFoundError as exc:
        # If strict pack: fail; otherwise allow.
        if is_strict_pack(pack_key):
            result.status = "FAIL"
            result.issues.append(
                SectionValidationIssue(
                    code="NO_BENCHMARK",
                    message=f"No benchmark defined for section={section_id}: {exc}",
                    severity="error",
                )
            )
        else:
            result.status = "PASS_WITH_WARNINGS"
            result.issues.append(
                SectionValidationIssue(
                    code="NO_BENCHMARK",
                    message=f"No benchmark defined for section={section_id}, skipping checks.",
                    severity="warning",
                )
            )
        return result

    if not benchmark:
        # Same behaviour as above: strict packs treat this as error.
        if is_strict_pack(pack_key):
            result.status = "FAIL"
            result.issues.append(
                SectionValidationIssue(
                    code="NO_SECTION_CONFIG",
                    message=f"Benchmark file does not contain section={section_id}.",
                    severity="error",
                )
            )
        else:
            result.status = "PASS_WITH_WARNINGS"
            result.issues.append(
                SectionValidationIssue(
                    code="NO_SECTION_CONFIG",
                    message=f"Benchmark file does not contain section={section_id}, skipping checks.",
                    severity="warning",
                )
            )
        return result

    # Calculate metrics
    word_count = _count_words(content)
    bullets, headings, _ = _analyse_structure(content)
    sentences = _split_sentences(content)
    avg_sentence_len = (
        (sum(_count_words(s) for s in sentences) / len(sentences)) if sentences else 0.0
    )
    rep_ratio = _repetition_ratio(content)

    # Extract benchmark criteria
    min_words = int(benchmark.get("min_words", 0))
    max_words = int(benchmark.get("max_words", 10_000))
    min_bullets = int(benchmark.get("min_bullets", 0))
    max_bullets = int(benchmark.get("max_bullets", 10_000))
    min_headings = int(benchmark.get("min_headings", 0))
    max_headings = int(benchmark.get("max_headings", 10_000))
    max_rep_ratio = float(benchmark.get("max_repeated_line_ratio", 0.7))
    max_avg_sent = float(benchmark.get("max_avg_sentence_length", 999))

    required_headings = benchmark.get("required_headings") or []
    required_substrings = benchmark.get("required_substrings") or []
    forbidden_substrings = benchmark.get("forbidden_substrings") or []
    forbidden_regex = benchmark.get("forbidden_regex") or []
    fmt = benchmark.get("format", "markdown_block")

    # Validate word count
    if word_count < min_words:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_SHORT",
                message=f"Section has {word_count} words, minimum is {min_words}.",
                severity="error",
            )
        )
    if word_count > max_words:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_LONG",
                message=f"Section has {word_count} words, maximum is {max_words}.",
                severity="error",
            )
        )

    # Validate structure
    if bullets < min_bullets:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_FEW_BULLETS",
                message=f"Section has {bullets} bullets, minimum is {min_bullets}.",
                severity="error",
            )
        )
    if bullets > max_bullets:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_MANY_BULLETS",
                message=f"Section has {bullets} bullets, maximum is {max_bullets}.",
                severity="warning",
            )
        )
    if headings < min_headings:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_FEW_HEADINGS",
                message=f"Section has {headings} headings, minimum is {min_headings}.",
                severity="error",
            )
        )
    if headings > max_headings:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_MANY_HEADINGS",
                message=f"Section has {headings} headings, maximum is {max_headings}.",
                severity="warning",
            )
        )

    # Validate required content
    for h in required_headings:
        if h not in content:
            result.issues.append(
                SectionValidationIssue(
                    code="MISSING_HEADING",
                    message=f"Required heading '{h}' not found in section.",
                    severity="error",
                )
            )

    for s in required_substrings:
        if s not in content:
            result.issues.append(
                SectionValidationIssue(
                    code="MISSING_PHRASE",
                    message=f"Required phrase '{s}' not found in section.",
                    severity="error",
                )
            )

    # Validate forbidden content
    lowered = content.lower()
    for s in forbidden_substrings:
        if s.lower() in lowered:
            result.issues.append(
                SectionValidationIssue(
                    code="FORBIDDEN_PHRASE",
                    message=f"Forbidden phrase '{s}' present in section.",
                    severity="error",
                )
            )

    for pattern in forbidden_regex:
        if re.search(pattern, content):
            result.issues.append(
                SectionValidationIssue(
                    code="FORBIDDEN_PATTERN",
                    message=f"Content matches forbidden pattern: {pattern}",
                    severity="error",
                )
            )

    # Validate quality metrics
    if rep_ratio > max_rep_ratio:
        result.issues.append(
            SectionValidationIssue(
                code="TOO_REPETITIVE",
                message=f"Repeated lines ratio {rep_ratio:.2f} exceeds max {max_rep_ratio:.2f}.",
                severity="error",
            )
        )

    if avg_sentence_len > max_avg_sent and max_avg_sent > 0:
        result.issues.append(
            SectionValidationIssue(
                code="SENTENCES_TOO_LONG",
                message=f"Average sentence length {avg_sentence_len:.1f} exceeds {max_avg_sent}.",
                severity="warning",
            )
        )

    # Validate format-specific requirements
    if fmt == "markdown_table":
        if "|" not in content:
            result.issues.append(
                SectionValidationIssue(
                    code="EXPECTED_TABLE",
                    message="Section is expected to be a markdown table but contains no '|' characters.",
                    severity="error",
                )
            )

    # Determine final status
    if any(i.severity == "error" for i in result.issues):
        result.status = "FAIL"
    elif result.issues:
        result.status = "PASS_WITH_WARNINGS"
    else:
        result.status = "PASS"

    return result
