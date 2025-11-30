"""
Output Validation Layer for AICMO Reports

Ensures reports meet quality standards before export:
- Pack scoping validation (correct section count per pack)
- Field validation (no empty critical fields)
- Cross-field validation (no field substitution, e.g., goal as persona)
- Industry alignment (personas/channels match industry)
- PDF parity (PDF has all sections from preview)
- Negative constraints validation (brand "don'ts" enforcement)

FIX #6: Comprehensive validation to catch errors before export
"""

import re
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

from aicmo.io.client_reports import AICMOOutputReport, ClientInputBrief
from backend.validators.pack_schemas import get_pack_schema


# ============================================================
# PACK CONTRACT VALIDATION
# ============================================================


def validate_pack_contract(pack_key: str, report: dict | AICMOOutputReport) -> None:
    """
    Validate that a generated report matches the pack contract for the specified pack.

    Validates:
    - All required sections are present
    - Required sections are non-empty
    - Section order matches schema (if enforce_order is True)

    Args:
        pack_key: Package preset key (e.g., "quick_social_basic", "strategy_campaign_standard")
        report: Generated report as dict or AICMOOutputReport instance

    Raises:
        ValueError: If validation fails (missing sections, empty sections, wrong order)
    """
    # Get schema for this pack
    schema = get_pack_schema(pack_key)
    if not schema:
        # Pack not recognized - skip validation rather than fail
        # This allows new packs to be added without breaking existing code
        return

    # Convert report to dict if it's an AICMOOutputReport instance
    if isinstance(report, AICMOOutputReport):
        report_dict = report.model_dump()
    else:
        report_dict = report

    # Extract sections from report structure
    # AICMO reports store sections in extra_sections dict
    extra_sections = report_dict.get("extra_sections", {})

    required_sections = schema.get("required_sections", [])
    enforce_order = schema.get("enforce_order", False)

    # Validation 1: Check all required sections are present
    missing_sections = []
    for section_id in required_sections:
        if section_id not in extra_sections:
            missing_sections.append(section_id)

    if missing_sections:
        raise ValueError(
            f"Pack '{pack_key}' missing required sections: {', '.join(missing_sections)}"
        )

    # Validation 2: Check required sections are non-empty
    empty_sections = []
    for section_id in required_sections:
        content = extra_sections.get(section_id, "")
        if not content or (isinstance(content, str) and not content.strip()):
            empty_sections.append(section_id)

    if empty_sections:
        raise ValueError(
            f"Pack '{pack_key}' has empty required sections: {', '.join(empty_sections)}"
        )

    # Validation 3: Check section order (if enforce_order is True)
    if enforce_order:
        # Get actual order of sections in report
        actual_order = [sid for sid in extra_sections.keys() if sid in required_sections]

        # Get expected order from schema
        expected_order = [sid for sid in required_sections if sid in extra_sections]

        if actual_order != expected_order:
            # Build helpful error message showing mismatch
            mismatches = []
            for i, (actual, expected) in enumerate(zip(actual_order, expected_order)):
                if actual != expected:
                    mismatches.append(f"Position {i}: expected '{expected}', got '{actual}'")

            raise ValueError(
                f"Pack '{pack_key}' section order incorrect. First mismatches: {'; '.join(mismatches[:3])}"
            )


# ============================================================
# NEGATIVE CONSTRAINTS VALIDATION
# ============================================================


def parse_constraints(raw: str) -> List[str]:
    """
    Parse raw constraint text into individual constraints.

    Handles multiple separators: semicolons, newlines, periods.

    Args:
        raw: Raw constraint text from operator

    Returns:
        List of individual constraint strings
    """
    if not raw:
        return []

    # Split on semicolons, newlines, or periods
    parts = re.split(r"[;\n.]+", raw)
    return [p.strip() for p in parts if p.strip()]


def validate_negative_constraints(output_text: str, negative_constraints_raw: str) -> List[str]:
    """
    Validate that output doesn't violate negative constraints.

    Simple keyword-based checking: if a constraint mentions a word,
    flag if that word appears in the output.

    Args:
        output_text: The generated output content to validate
        negative_constraints_raw: Raw constraint text from operator

    Returns:
        List of violation messages (empty if all constraints passed)
    """
    violations = []
    constraints = parse_constraints(negative_constraints_raw)
    lower_output = output_text.lower()

    for c in constraints:
        if not c:
            continue

        # Extract keywords from constraint
        # Strategy: take the last meaningful word as the keyword
        tokens = c.split()
        if not tokens:
            continue

        # Skip common words, take the last substantive word
        keyword = tokens[-1].strip("'., ").lower()

        # Very simple check: if keyword appears in output, flag it
        if keyword and keyword in lower_output:
            violations.append(f"Constraint violation: '{c}' (keyword '{keyword}' found in output).")

    return violations


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""

    ERROR = "error"  # Blocks export
    WARNING = "warning"  # Warns but allows
    INFO = "info"  # Informational only


@dataclass
class ValidationIssue:
    """Single validation issue found in report."""

    section: str
    message: str
    severity: ValidationSeverity
    field: Optional[str] = None


class OutputValidator:
    """Validates AICMO output reports before export."""

    def __init__(
        self,
        output: AICMOOutputReport,
        brief: ClientInputBrief,
        wow_package_key: Optional[str] = None,
    ):
        """
        Initialize validator with report and brief context.

        Args:
            output: The generated report to validate
            brief: The client brief (for industry/goal context)
            wow_package_key: Which WOW pack was used (for pack-specific validation)
        """
        self.output = output
        self.brief = brief
        self.wow_package_key = wow_package_key
        self.issues: List[ValidationIssue] = []

    def validate_all(self) -> List[ValidationIssue]:
        """Run all validation checks and return list of issues found."""
        self.issues = []

        # Run all validation checks
        self._validate_pack_scoping()
        self._validate_no_empty_critical_fields()
        self._validate_no_field_substitution()
        self._validate_industry_alignment()
        self._validate_pdf_parity()

        return self.issues

    def validate_all_strict(self) -> List[ValidationIssue]:
        """Run all validation checks, treating warnings as errors for export."""
        issues = self.validate_all()
        # Convert warnings to errors for strict mode
        for issue in issues:
            if issue.severity == ValidationSeverity.WARNING:
                issue.severity = ValidationSeverity.ERROR
        return issues

    def has_blocking_issues(self) -> bool:
        """Check if there are any error-level issues."""
        return any(i.severity == ValidationSeverity.ERROR for i in self.issues)

    def get_error_summary(self) -> str:
        """Get human-readable error summary."""
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        if not errors:
            return "No blocking issues found."

        summary = f"Found {len(errors)} blocking issue(s):\n"
        for issue in errors[:5]:  # Show first 5
            summary += f"  • {issue.section}: {issue.message}\n"

        if len(errors) > 5:
            summary += f"  ... and {len(errors) - 5} more\n"

        return summary

    def _validate_pack_scoping(self) -> None:
        """
        FIX #2: Validate that output has correct section count for pack.

        Basic: 10 sections
        Standard: 17 sections
        Premium: 21 sections
        """
        if not self.wow_package_key:
            return  # Only validate if WOW pack specified

        # Count sections in extra_sections (primary indicator of section count)
        section_count = len(self.output.extra_sections or {})

        # Also count structured sections that exist
        structured_sections = 0
        if self.output.marketing_plan:
            structured_sections += 1
        if self.output.campaign_blueprint:
            structured_sections += 1
        if self.output.social_calendar:
            structured_sections += 1
        if self.output.performance_review:
            structured_sections += 1
        if self.output.creatives:
            structured_sections += 1
        if self.output.persona_cards:
            structured_sections += 1
        if self.output.action_plan:
            structured_sections += 1

        # Define expected section counts
        expected_counts = {
            "quick_social_basic": 10,
            "strategy_campaign_standard": 16,
            "full_funnel_growth_suite": 23,
            "launch_gtm_pack": 13,
            "brand_turnaround_lab": 14,
            "retention_crm_booster": 14,
            "performance_audit_revamp": 16,
        }

        expected = expected_counts.get(self.wow_package_key)
        if expected is None:
            return  # Unknown package, skip check

        # Allow some variance since extra_sections is not always populated
        total_sections = section_count + structured_sections

        if total_sections < (expected * 0.8):  # More than 20% short
            self.issues.append(
                ValidationIssue(
                    section="Pack Scoping",
                    message=f"{self.wow_package_key} expected ~{expected} sections, found {total_sections}",
                    severity=ValidationSeverity.WARNING,
                )
            )

    def _validate_no_empty_critical_fields(self) -> None:
        """
        FIX #6: Ensure critical fields are not empty or 'Not specified'.
        """
        b = self.brief.brand
        g = self.brief.goal
        a = self.brief.audience

        critical_checks = [
            ("Brand Name", b.brand_name),
            ("Industry", b.industry),
            ("Primary Goal", g.primary_goal),
            ("Primary Customer", a.primary_customer),
        ]

        for field_name, value in critical_checks:
            if not value or str(value).strip().lower() in ("not specified", "none", ""):
                self.issues.append(
                    ValidationIssue(
                        section="Input Validation",
                        message=f"Critical field empty: {field_name}",
                        severity=ValidationSeverity.WARNING,
                        field=field_name,
                    )
                )

    def _validate_no_field_substitution(self) -> None:
        """
        FIX #1 Verification: Check that persona names don't match goal text.

        This would indicate goal was incorrectly substituted into persona field.
        """
        if not self.output.persona_cards:
            return

        g = self.brief.goal
        goal_text = (g.primary_goal or "").lower()

        if not goal_text:
            return

        for i, persona in enumerate(self.output.persona_cards):
            persona_name = (persona.name or "").lower()

            # Check if goal text appears in persona name (> 50% overlap)
            goal_words = set(goal_text.split())
            persona_words = set(persona_name.split())

            if goal_words and persona_words:
                overlap = len(goal_words & persona_words) / len(goal_words)
                if overlap > 0.5:
                    self.issues.append(
                        ValidationIssue(
                            section=f"Persona {i+1}",
                            message=f"Persona name '{persona.name}' appears to contain goal text '{g.primary_goal}'",
                            severity=ValidationSeverity.ERROR,
                        )
                    )

    def _validate_industry_alignment(self) -> None:
        """
        FIX #4: Check that personas and channels are aligned with industry.

        F&B café → Instagram/TikTok primary (not LinkedIn)
        SaaS → LinkedIn/Email primary
        Retail → Instagram/Pinterest primary
        """
        industry = (self.brief.brand.industry or "").lower()

        # Define industry categories and appropriate channels
        industry_channels = {
            "food_beverage": {"instagram", "tiktok", "facebook"},
            "café": {"instagram", "tiktok", "facebook"},
            "restaurant": {"instagram", "facebook"},
            "saas": {"linkedin", "email"},
            "b2b": {"linkedin", "email"},
            "retail": {"instagram", "pinterest", "facebook"},
            "ecommerce": {"instagram", "pinterest", "email"},
            "fitness": {"instagram", "tiktok", "youtube"},
            "wellness": {"instagram", "youtube"},
        }

        # Find matching industry category
        matched_channels = None
        for industry_key, channels in industry_channels.items():
            if industry_key in industry:
                matched_channels = channels
                break

        if matched_channels is None:
            return  # Industry not recognized, skip check

        # Check if channel_plan in output matches industry
        # This is a soft check since we can't easily parse the channel_plan markdown
        if hasattr(self.output, "marketing_plan") and self.output.marketing_plan:
            mp_str = str(self.output.marketing_plan).lower()

            # Check for channel mentions
            found_channels = []
            for channel in matched_channels:
                if channel in mp_str:
                    found_channels.append(channel)

            if not found_channels:
                self.issues.append(
                    ValidationIssue(
                        section="Channel Alignment",
                        message=f"No channels from {matched_channels} found in marketing plan for {industry}",
                        severity=ValidationSeverity.INFO,  # Info level since output might still work
                    )
                )

    def _validate_pdf_parity(self) -> None:
        """
        FIX #3: Ensure PDF output has same sections as preview.

        Basic check: if WOW markdown exists, it should have similar content.
        """
        if not self.output.wow_markdown:
            return  # No WOW markdown to compare

        wow_markdown = self.output.wow_markdown.lower()

        # Count section headers in markdown (## indicates section start)
        section_count = wow_markdown.count("\n## ")

        expected_counts = {
            "quick_social_basic": 10,
            "strategy_campaign_standard": 17,
            "full_funnel_growth_suite": 21,
        }

        expected = expected_counts.get(self.wow_package_key, 0)
        if expected == 0:
            return  # Unknown package

        if section_count < (expected * 0.7):  # Less than 70% of sections present
            self.issues.append(
                ValidationIssue(
                    section="PDF Parity",
                    message=f"WOW markdown has {section_count} sections, expected ~{expected}",
                    severity=ValidationSeverity.WARNING,
                )
            )


def validate_output_report(
    output: AICMOOutputReport,
    brief: ClientInputBrief,
    wow_package_key: Optional[str] = None,
    strict: bool = False,
) -> tuple[bool, List[ValidationIssue]]:
    """
    Convenience function to validate a report and return (is_valid, issues) tuple.

    Args:
        output: Report to validate
        brief: Client brief
        wow_package_key: WOW package used (optional)
        strict: If True, treat warnings as errors

    Returns:
        Tuple of (is_valid, issues_list)
        is_valid is True if no blocking issues found.
    """
    validator = OutputValidator(output, brief, wow_package_key)

    if strict:
        issues = validator.validate_all_strict()
    else:
        issues = validator.validate_all()

    is_valid = not validator.has_blocking_issues()
    return is_valid, issues
