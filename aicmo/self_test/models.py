"""
Self-Test Engine Models

Data structures for test results, status tracking, and reporting.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from aicmo.self_test.layout_checkers import (
        HtmlLayoutCheckResult,
        PptxLayoutCheckResult,
        PdfLayoutCheckResult,
    )
    from aicmo.self_test.semantic_checkers import SemanticAlignmentResult
    from aicmo.self_test.security_checkers import SecurityScanResult


class TestStatus(Enum):
    """Overall test status."""
    PASS = "pass"
    FAIL = "fail"
    SKIP = "skip"
    PARTIAL = "partial"


class FeatureCategory(Enum):
    """Categories of features to test."""
    GENERATOR = "generator"
    PACKAGER = "packager"
    GATEWAY = "gateway"
    VALIDATOR = "validator"
    CAM = "cam"
    WORKFLOW = "workflow"


# ============================================================================
# CRITICAL FEATURES DEFINITION
# ============================================================================
# These features must pass for CI/CD; if any fail, exit code is 1
# Optional/non-critical features can fail without breaking CI

CRITICAL_FEATURES: Set[str] = {
    # Core generators that are essential
    "persona_generator",
    "social_calendar_generator",
    "situation_analysis_generator",
    "messaging_pillars_generator",
    "swot_generator",
    # Critical packagers
    "generate_full_deck_pptx",
    "generate_html_summary",
}


# ============================================================================
# SELF-TEST ENGINE 2.0: Coverage and Quality Models (defined before FeatureStatus)
# ============================================================================


@dataclass
class BenchmarkCoverageStatus:
    """Benchmark coverage for a feature."""
    feature_name: str
    benchmarks_mapped: List[str] = field(default_factory=list)
    benchmarks_enforced: List[str] = field(default_factory=list)
    benchmarks_unenforced: List[str] = field(default_factory=list)


@dataclass
class LayoutCheckResults:
    """Layout validation results for client-facing outputs."""
    html_valid: Optional[bool] = None
    html_details: Dict[str, Any] = field(default_factory=dict)
    pptx_valid: Optional[bool] = None
    pptx_slide_count: int = 0
    pptx_details: Dict[str, Any] = field(default_factory=dict)
    pdf_valid: Optional[bool] = None
    pdf_page_count: int = 0
    pdf_details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormatCheckResults:
    """Format and word-count validation results."""
    is_valid: bool
    too_short_fields: List[str] = field(default_factory=list)
    too_long_fields: List[str] = field(default_factory=list)
    metrics: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class QualityCheckResults:
    """Content quality validation results."""
    genericity_score: float = 0.0
    repeated_phrases: List[str] = field(default_factory=list)
    placeholders_found: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    overall_quality_assessment: str = "unknown"  # excellent, good, fair, poor


@dataclass
class CoverageInfo:
    """Coverage information for self-test."""
    total_benchmarks: int = 0
    mapped_benchmarks: int = 0
    enforced_benchmarks: int = 0
    unmapped_benchmarks: int = 0
    html_layout_checked: bool = False
    pptx_layout_checked: bool = False
    pdf_layout_checked: bool = False
    quality_checks_enabled: bool = True
    format_checks_enabled: bool = True
    notes: List[str] = field(default_factory=list)


# ============================================================================
# V1 MODELS (now can reference 2.0 models)
# ============================================================================


@dataclass
class FeatureStatus:
    """Status of a single feature."""
    name: str
    category: FeatureCategory
    status: TestStatus
    critical: bool = False  # True if this feature must pass for CI/CD
    description: Optional[str] = None
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    scenarios_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    # 2.0 Fields
    benchmark_coverage: Optional[BenchmarkCoverageStatus] = None
    layout_checks: Optional[LayoutCheckResults] = None
    format_checks: Optional[FormatCheckResults] = None
    quality_checks: Optional[QualityCheckResults] = None
    semantic_alignment: Optional["SemanticAlignmentResult"] = None
    # Performance tracking (3.0)
    runtime_seconds: Optional[float] = None
    # Security & Privacy scanning (5.0)
    security_scan_result: Optional["SecurityScanResult"] = None

    @property
    def total_scenarios(self) -> int:
        return self.scenarios_passed + self.scenarios_failed + self.scenarios_skipped

    def add_error(self, error: str) -> None:
        self.errors.append(error)
        if self.status == TestStatus.PASS:
            self.status = TestStatus.FAIL

    def add_warning(self, warning: str) -> None:
        self.warnings.append(warning)


@dataclass
class GeneratorStatus:
    """Status of a generator."""
    name: str
    module_path: str
    status: TestStatus
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    scenarios_skipped: int = 0
    errors: List[str] = field(default_factory=list)
    snapshot_diffs: Dict[str, str] = field(default_factory=dict)
    output_samples: Dict[str, str] = field(default_factory=dict)

    @property
    def total_scenarios(self) -> int:
        return self.scenarios_passed + self.scenarios_failed + self.scenarios_skipped


@dataclass
class GatewayStatus:
    """Status of a gateway or adapter."""
    name: str
    provider: str
    is_configured: bool
    status: TestStatus
    details: str = ""
    error_message: Optional[str] = None


@dataclass
class PackagerStatus:
    """Status of a packaging function."""
    name: str
    module_path: str
    status: TestStatus
    output_file: Optional[str] = None
    file_size: Optional[int] = None
    error_message: Optional[str] = None
    # 2.0 Fields: Layout validation results
    html_layout_result: Optional["HtmlLayoutCheckResult"] = None
    pptx_layout_result: Optional["PptxLayoutCheckResult"] = None
    pdf_layout_result: Optional["PdfLayoutCheckResult"] = None


@dataclass
class ExternalServiceStatus:
    """Status of an external integration/service."""
    name: str
    configured: bool
    reachable: Optional[bool] = None  # None means we didn't check (safe mode), True/False means we did check
    critical: bool = False
    details: Dict[str, Any] = field(default_factory=dict)  # Extra info: env_vars_present, error_message, etc.

    @property
    def status_display(self) -> str:
        """Human-readable status for reports."""
        if not self.configured:
            return "NOT CONFIGURED"
        if self.reachable is None:
            return "UNCHECKED"
        if self.reachable:
            return "✅ REACHABLE"
        return "❌ UNREACHABLE"

    @property
    def criticality_display(self) -> str:
        """Display criticality."""
        return "CRITICAL" if self.critical else "OPTIONAL"


@dataclass
class SelfTestResult:
    """Complete self-test results."""
    timestamp: datetime
    features: List[FeatureStatus] = field(default_factory=list)
    generators: List[GeneratorStatus] = field(default_factory=list)
    gateways: List[GatewayStatus] = field(default_factory=list)
    packagers: List[PackagerStatus] = field(default_factory=list)
    critical_failures: List[str] = field(default_factory=list)
    # 2.0 Fields
    coverage_info: Optional[CoverageInfo] = None
    project_rehearsals: List["ProjectRehearsalResult"] = field(default_factory=list)
    # 3.0 Performance & Flakiness Fields
    deterministic_mode: bool = False
    flakiness_check_results: Dict[str, List[str]] = field(default_factory=dict)  # feature_name -> list of flaky runs
    # 4.0 External Integrations Health Fields
    external_services: List[ExternalServiceStatus] = field(default_factory=list)  # Health status of external integrations

    @property
    def total_features(self) -> int:
        return len(self.features)

    @property
    def passed_features(self) -> int:
        return sum(1 for f in self.features if f.status == TestStatus.PASS)

    @property
    def failed_features(self) -> int:
        return sum(1 for f in self.features if f.status == TestStatus.FAIL)

    @property
    def skipped_features(self) -> int:
        return sum(1 for f in self.features if f.status == TestStatus.SKIP)

    @property
    def has_critical_failures(self) -> bool:
        return len(self.critical_failures) > 0

    @property
    def summary_line(self) -> str:
        return (
            f"Features: {self.passed_features} PASS, "
            f"{self.failed_features} FAIL, {self.skipped_features} SKIP"
        )


@dataclass
class SnapshotDiffResult:
    """Result of comparing with a snapshot."""
    has_diff: bool
    severity: str  # "none", "minor", "moderate", "severe"
    added_keys: List[str] = field(default_factory=list)
    removed_keys: List[str] = field(default_factory=list)
    changed_keys: List[str] = field(default_factory=list)
    length_diffs: Dict[str, tuple] = field(default_factory=dict)  # key -> (old_len, new_len)


# ============================================================================
# FULL PROJECT REHEARSAL (2.0 - E2E FLOW TESTING)
# ============================================================================


@dataclass
class RehearsalStepResult:
    """Result of a single step in the project rehearsal."""
    name: str
    status: TestStatus  # PASS, FAIL, SKIP
    duration_ms: float = 0.0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)  # e.g., word_count, slide_count


@dataclass
class ProjectRehearsalResult:
    """Complete result of running a full project rehearsal (brief → artifacts)."""
    project_name: str
    brief_name: str
    passed: bool
    total_steps: int = 0
    passed_steps: int = 0
    failed_steps: int = 0
    skipped_steps: int = 0
    steps: List[RehearsalStepResult] = field(default_factory=list)
    overall_duration_ms: float = 0.0
    artifacts_generated: List[str] = field(default_factory=list)
    critical_errors: List[str] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_steps == 0:
            return 0.0
        return (self.passed_steps / self.total_steps) * 100

    message: str = ""
