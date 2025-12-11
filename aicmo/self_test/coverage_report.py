"""
Coverage Report

Generates coverage summary for benchmarks, layout checks, and quality checks.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FeatureCoverageInfo:
    """Coverage information for a single feature."""

    feature_name: str
    benchmarks_mapped: List[str] = field(default_factory=list)
    benchmarks_enforced: List[str] = field(default_factory=list)
    benchmarks_unenforced: List[str] = field(default_factory=list)
    has_html_check: bool = False
    has_pptx_check: bool = False
    has_pdf_check: bool = False
    has_format_check: bool = False
    has_quality_check: bool = False
    notes: List[str] = field(default_factory=list)


@dataclass
class CoverageSummary:
    """Summary of all coverage across the self-test system."""

    total_benchmarks: int = 0
    mapped_benchmarks: int = 0
    enforced_benchmarks: int = 0
    unenforced_benchmarks: int = 0
    unmapped_benchmarks: int = 0

    html_layout_checked: bool = False
    pptx_layout_checked: bool = False
    pdf_layout_checked: bool = False

    quality_checks_enabled: bool = True
    format_checks_enabled: bool = True

    feature_coverage: Dict[str, FeatureCoverageInfo] = field(default_factory=dict)
    """Detailed coverage per feature"""

    uncovered_features: List[str] = field(default_factory=list)
    """Features with no benchmarks or checks"""

    notes: List[str] = field(default_factory=list)
    """General notes about coverage gaps"""

    @property
    def benchmark_coverage_percent(self) -> float:
        """Percentage of mapped benchmarks that are enforced."""
        if self.mapped_benchmarks == 0:
            return 0.0
        return round((self.enforced_benchmarks / self.mapped_benchmarks) * 100, 1)

    @property
    def total_coverage_score(self) -> float:
        """Overall coverage score (0-1.0)."""
        # Components: benchmarks (40%), layout checks (30%), quality checks (30%)
        benchmark_score = self.benchmark_coverage_percent / 100.0 if self.mapped_benchmarks > 0 else 0.5
        layout_score = 1.0 if (self.html_layout_checked or self.pptx_layout_checked or self.pdf_layout_checked) else 0.0
        quality_score = 1.0 if self.quality_checks_enabled else 0.0

        overall = (
            benchmark_score * 0.4 +
            layout_score * 0.3 +
            quality_score * 0.3
        )
        return round(overall, 2)

    def summary_text(self) -> str:
        """Generate a summary text of coverage."""
        lines = []

        lines.append(f"**Benchmarks:** {self.enforced_benchmarks}/{self.mapped_benchmarks} mapped benchmarks enforced")
        if self.unmapped_benchmarks > 0:
            lines.append(f"  - {self.unmapped_benchmarks} benchmarks unmapped")

        layout_checks = sum([
            self.html_layout_checked,
            self.pptx_layout_checked,
            self.pdf_layout_checked,
        ])
        lines.append(f"**Layout Checks:** {layout_checks}/3 modalities checked")
        if not self.html_layout_checked:
            lines.append("  - HTML layout: not checked")
        if not self.pptx_layout_checked:
            lines.append("  - PPTX layout: not checked")
        if not self.pdf_layout_checked:
            lines.append("  - PDF layout: not checked")

        lines.append(f"**Quality Checks:** {'enabled' if self.quality_checks_enabled else 'disabled'}")
        lines.append(f"**Format Checks:** {'enabled' if self.format_checks_enabled else 'disabled'}")

        if self.uncovered_features:
            lines.append(f"**Uncovered Features:** {len(self.uncovered_features)}")
            for feat in self.uncovered_features[:5]:
                lines.append(f"  - {feat}")
            if len(self.uncovered_features) > 5:
                lines.append(f"  - ... and {len(self.uncovered_features) - 5} more")

        if self.notes:
            lines.append("**Notes:**")
            for note in self.notes:
                lines.append(f"  - {note}")

        return "\n".join(lines)


def build_coverage_summary(
    total_benchmarks: int = 0,
    mapped_benchmarks: int = 0,
    enforced_benchmarks: int = 0,
    html_checked: bool = False,
    pptx_checked: bool = False,
    pdf_checked: bool = False,
    quality_enabled: bool = True,
    format_enabled: bool = True,
    feature_coverage: Optional[Dict[str, FeatureCoverageInfo]] = None,
    uncovered_features: Optional[List[str]] = None,
) -> CoverageSummary:
    """
    Build a coverage summary from components.

    Args:
        total_benchmarks: Total benchmarks discovered
        mapped_benchmarks: Benchmarks that map to features
        enforced_benchmarks: Benchmarks actually enforced
        html_checked: Whether HTML layout was checked
        pptx_checked: Whether PPTX layout was checked
        pdf_checked: Whether PDF layout was checked
        quality_enabled: Whether quality checks are enabled
        format_enabled: Whether format checks are enabled
        feature_coverage: Optional detailed coverage per feature
        uncovered_features: List of features with no coverage

    Returns:
        CoverageSummary object
    """
    unmapped = total_benchmarks - mapped_benchmarks
    unenforced = mapped_benchmarks - enforced_benchmarks

    summary = CoverageSummary(
        total_benchmarks=total_benchmarks,
        mapped_benchmarks=mapped_benchmarks,
        enforced_benchmarks=enforced_benchmarks,
        unenforced_benchmarks=unenforced,
        unmapped_benchmarks=unmapped,
        html_layout_checked=html_checked,
        pptx_layout_checked=pptx_checked,
        pdf_layout_checked=pdf_checked,
        quality_checks_enabled=quality_enabled,
        format_checks_enabled=format_enabled,
        feature_coverage=feature_coverage or {},
        uncovered_features=uncovered_features or [],
    )

    # Add notes about coverage gaps
    if unmapped > 0:
        summary.notes.append(f"{unmapped} benchmarks could not be mapped to features")
    if unenforced > 0:
        summary.notes.append(f"{unenforced} benchmarks are not enforced by validators")
    if not pdf_checked:
        summary.notes.append("PDF layout checks not implemented (no PDF parser)")
    if not quality_enabled:
        summary.notes.append("Quality checks disabled (set AICMO_SELF_TEST_ENABLE_QUALITY=true to enable)")

    return summary


def calculate_feature_coverage(
    feature_name: str,
    benchmarks_mapped: Optional[List[str]] = None,
    benchmarks_enforced: Optional[List[str]] = None,
    has_html_check: bool = False,
    has_pptx_check: bool = False,
    has_pdf_check: bool = False,
    has_format_check: bool = False,
    has_quality_check: bool = False,
) -> FeatureCoverageInfo:
    """
    Calculate coverage for a single feature.

    Args:
        feature_name: Name of feature
        benchmarks_mapped: List of benchmark names mapped to this feature
        benchmarks_enforced: List of benchmark names enforced for this feature
        has_html_check: Whether HTML layout is checked
        has_pptx_check: Whether PPTX layout is checked
        has_pdf_check: Whether PDF layout is checked
        has_format_check: Whether format checks are run
        has_quality_check: Whether quality checks are run

    Returns:
        FeatureCoverageInfo for this feature
    """
    benchmarks_mapped = benchmarks_mapped or []
    benchmarks_enforced = benchmarks_enforced or []

    unenforced = [b for b in benchmarks_mapped if b not in benchmarks_enforced]

    return FeatureCoverageInfo(
        feature_name=feature_name,
        benchmarks_mapped=benchmarks_mapped,
        benchmarks_enforced=benchmarks_enforced,
        benchmarks_unenforced=unenforced,
        has_html_check=has_html_check,
        has_pptx_check=has_pptx_check,
        has_pdf_check=has_pdf_check,
        has_format_check=has_format_check,
        has_quality_check=has_quality_check,
    )


def coverage_assessment(summary: CoverageSummary) -> Dict[str, Any]:
    """
    Generate assessment and recommendations based on coverage.

    Args:
        summary: CoverageSummary object

    Returns:
        Dictionary with assessment and recommendations
    """
    assessment = {
        "coverage_score": summary.total_coverage_score,
        "assessment": "",
        "recommendations": [],
        "critical_gaps": [],
    }

    score = summary.total_coverage_score

    if score >= 0.8:
        assessment["assessment"] = "Excellent coverage"
    elif score >= 0.6:
        assessment["assessment"] = "Good coverage"
    elif score >= 0.4:
        assessment["assessment"] = "Moderate coverage"
    else:
        assessment["assessment"] = "Poor coverage"

    # Recommendations
    if summary.unmapped_benchmarks > 0:
        assessment["critical_gaps"].append(
            f"Unmapped benchmarks ({summary.unmapped_benchmarks}) - map to features"
        )
        assessment["recommendations"].append(
            "Add metadata to benchmark JSON files (target_feature field)"
        )

    if summary.unenforced_benchmarks > 0:
        assessment["critical_gaps"].append(
            f"Unenforced benchmarks ({summary.unenforced_benchmarks}) - add validators"
        )
        assessment["recommendations"].append(
            "Add validators for mapped benchmarks to quality/validators.py"
        )

    if not summary.html_layout_checked:
        assessment["recommendations"].append(
            "Enable HTML layout checks for summary/report outputs"
        )

    if not summary.pptx_layout_checked:
        assessment["recommendations"].append(
            "Enable PPTX layout checks for deck generation"
        )

    if not summary.quality_checks_enabled:
        assessment["recommendations"].append(
            "Enable quality checks (AICMO_SELF_TEST_ENABLE_QUALITY=true)"
        )

    if summary.uncovered_features:
        assessment["recommendations"].append(
            f"Add benchmarks or checks for {len(summary.uncovered_features)} features"
        )

    return assessment
