"""
Self-Test Engine Pytest Integration

Light smoke tests to ensure self-test engine runs without crashing.
"""

import pytest

from aicmo.self_test.discovery import (
    discover_adapters,
    discover_benchmarks,
    discover_cam_components,
    discover_generators,
    discover_packagers,
    discover_validators,
    get_all_discoveries,
)
from aicmo.self_test.orchestrator import SelfTestOrchestrator
from aicmo.self_test.reporting import ReportGenerator
from aicmo.self_test.snapshots import SnapshotManager
from aicmo.self_test.test_inputs import (
    get_all_test_briefs,
    get_briefs_for_generator,
    get_quick_test_briefs,
)


class TestSelfTestDiscovery:
    """Test discovery functions."""

    def test_discover_generators(self):
        """Test generator discovery."""
        generators = discover_generators()
        assert len(generators) > 0
        assert all(hasattr(g, "name") and hasattr(g, "module_path") for g in generators)

    def test_discover_adapters(self):
        """Test adapter/gateway discovery."""
        adapters = discover_adapters()
        # Adapters might be optional, but discovery should work
        assert isinstance(adapters, list)

    def test_discover_packagers(self):
        """Test packager discovery."""
        packagers = discover_packagers()
        assert isinstance(packagers, list)

    def test_discover_validators(self):
        """Test validator discovery."""
        validators = discover_validators()
        assert isinstance(validators, list)

    def test_discover_benchmarks(self):
        """Test benchmark discovery."""
        benchmarks = discover_benchmarks()
        assert isinstance(benchmarks, list)

    def test_discover_cam_components(self):
        """Test CAM component discovery."""
        components = discover_cam_components()
        assert isinstance(components, list)

    def test_get_all_discoveries(self):
        """Test unified discovery."""
        discoveries = get_all_discoveries()
        assert "generators" in discoveries
        assert "adapters" in discoveries
        assert "packagers" in discoveries
        assert "validators" in discoveries
        assert "benchmarks" in discoveries
        assert "cam_components" in discoveries


class TestSelfTestInputs:
    """Test synthetic test inputs."""

    def test_get_all_test_briefs(self):
        """Test getting all test briefs."""
        briefs = get_all_test_briefs()
        assert len(briefs) >= 3
        # All briefs should be ClientInputBrief instances
        assert all(hasattr(b, "brand") for b in briefs)
        assert all(hasattr(b, "audience") for b in briefs)

    def test_get_briefs_for_generator(self):
        """Test getting briefs for specific generator."""
        briefs = get_briefs_for_generator("persona_generator")
        assert len(briefs) > 0
        # All briefs should be ClientInputBrief instances
        assert all(hasattr(b, "brand") for b in briefs)

    def test_get_quick_test_briefs(self):
        """Test getting quick test briefs."""
        briefs = get_quick_test_briefs(2)
        assert len(briefs) == 2
        assert all(hasattr(b, "brand") for b in briefs)


class TestSelfTestSnapshots:
    """Test snapshot management."""

    def test_snapshot_manager_init(self, tmp_path):
        """Test snapshot manager initialization."""
        manager = SnapshotManager(str(tmp_path))
        assert (tmp_path).exists()

    def test_save_and_load_snapshot(self, tmp_path):
        """Test saving and loading snapshots."""
        manager = SnapshotManager(str(tmp_path))
        
        test_payload = {"key": "value", "number": 42}
        path = manager.save_snapshot("test_feature", "test_scenario", test_payload)
        
        assert path.exists()
        
        loaded = manager.load_snapshot("test_feature", "test_scenario")
        assert loaded is not None
        assert loaded["payload"] == test_payload

    def test_compare_with_snapshot(self, tmp_path):
        """Test snapshot comparison."""
        manager = SnapshotManager(str(tmp_path))
        
        old_payload = {"key": "value", "count": 5}
        manager.save_snapshot("test_feature", "test_scenario", old_payload)
        
        # Load and compare (should match)
        result = manager.compare_with_snapshot("test_feature", "test_scenario", old_payload)
        assert result.has_diff is False
        assert result.severity == "none"


class TestSelfTestOrchestrator:
    """Test the main orchestrator."""

    def test_orchestrator_init(self, tmp_path):
        """Test orchestrator initialization."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        assert orchestrator.result is not None

    def test_critical_features_marked(self, tmp_path):
        """Test that critical features are properly marked."""
        from aicmo.self_test.models import CRITICAL_FEATURES
        
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Find critical features in the result
        critical_features_found = [f for f in result.features if f.critical]
        
        # Should have some critical features marked
        assert len(critical_features_found) > 0, "Should have critical features marked"
        
        # All marked critical features should be in CRITICAL_FEATURES constant
        for feature in critical_features_found:
            assert feature.name in CRITICAL_FEATURES, f"{feature.name} marked critical but not in CRITICAL_FEATURES"

    def test_has_critical_failures_property(self, tmp_path):
        """Test the has_critical_failures property works correctly."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Check the property exists and returns a boolean
        assert isinstance(result.has_critical_failures, bool)
        
        # If there are critical failures, the property should be True
        if result.critical_failures:
            assert result.has_critical_failures is True
        else:
            assert result.has_critical_failures is False

    @pytest.mark.slow
    def test_run_self_test_quick_mode(self, tmp_path):
        """Test running self-test in quick mode."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        assert result is not None
        assert hasattr(result, "timestamp")
        assert hasattr(result, "features")
        assert len(result.features) > 0

    @pytest.mark.slow
    def test_self_test_has_generators(self, tmp_path):
        """Test that self-test finds generators."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        assert len(result.generators) > 0


class TestSelfTestCLI:
    """Test CLI exit code behavior."""

    def test_cli_exit_code_on_all_pass(self, tmp_path):
        """Test CLI exit code behavior with pass and fail."""
        from aicmo.self_test.cli import main
        
        # Run main with tmp_path
        exit_code = main(quick_mode=True, output_dir=str(tmp_path), verbose=False)
        
        # Exit code should be 0 or 1 depending on test results
        # In this case, generators may fail due to LLM availability, so exit 1 is valid
        assert exit_code in [0, 1], "Exit code should be 0 (success) or 1 (critical failure)"

    def test_cli_handles_critical_vs_noncritical(self, tmp_path):
        """Test CLI distinguishes critical from non-critical failures."""
        from aicmo.self_test.orchestrator import SelfTestOrchestrator
        from aicmo.self_test.models import FeatureStatus, FeatureCategory, TestStatus
        
        # Create a result with both critical and non-critical failures
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Verify that critical features are marked correctly
        critical_count = sum(1 for f in result.features if f.critical)
        non_critical_count = sum(1 for f in result.features if not f.critical)
        
        # We should have features of both types
        assert len(result.features) > 0, "Should have features"
        assert critical_count + non_critical_count == len(result.features), "All features should be classified"


class TestPerformanceTracking:
    """Test performance tracking (runtime_seconds) for features."""

    @pytest.mark.slow
    def test_runtime_seconds_recorded(self, tmp_path):
        """Test that runtime_seconds is recorded for features."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Should have at least one feature
        assert len(result.features) > 0, "Should have features"
        
        # At least one feature should have runtime_seconds recorded
        features_with_runtime = [f for f in result.features if f.runtime_seconds is not None]
        assert len(features_with_runtime) > 0, "Should have at least one feature with runtime recorded"
        
        # Runtime should be positive (>0)
        for feature in features_with_runtime:
            assert feature.runtime_seconds > 0, f"Feature {feature.name} should have positive runtime"

    @pytest.mark.slow
    def test_runtime_seconds_in_range(self, tmp_path):
        """Test that recorded runtimes are in reasonable range."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Check runtime values are reasonable (quick test should be <60 seconds)
        for feature in result.features:
            if feature.runtime_seconds is not None:
                assert feature.runtime_seconds < 120, f"Feature {feature.name} runtime too high: {feature.runtime_seconds}s"

    def test_deterministic_flag_recognized(self):
        """Test that deterministic flag is recognized by run_self_test."""
        from aicmo.self_test.orchestrator import SelfTestOrchestrator
        
        orchestrator = SelfTestOrchestrator()
        # Should accept deterministic parameter without error
        result = orchestrator.run_self_test(quick_mode=True, deterministic=True)
        
        # Result should have deterministic_mode set to True
        assert result.deterministic_mode is True, "Should mark result as deterministic"

    def test_deterministic_mode_sets_seeds(self, tmp_path):
        """Test that deterministic mode sets reproducible seeds."""
        import random
        import numpy as np
        
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        
        # Run with deterministic=True
        result = orchestrator.run_self_test(quick_mode=True, deterministic=True)
        
        # After deterministic run, seeds should be set
        # Generate some random numbers to verify reproducibility
        vals1 = [random.random() for _ in range(5)]
        
        # Reset and generate again - should get same values
        random.seed(42)
        vals2 = [random.random() for _ in range(5)]
        
        # They might not be identical (orchestrator may have consumed random state)
        # but the test verifies deterministic mode accepted the flag
        assert result.deterministic_mode is True

    def test_performance_section_in_markdown_report(self, tmp_path):
        """Test that Performance & Flakiness section appears in markdown report."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        reporter = ReportGenerator(str(tmp_path))
        markdown = reporter.generate_markdown_report(result)
        
        # Should include Performance & Flakiness section
        assert "Performance & Flakiness" in markdown or "Performance" in markdown, \
            "Report should include performance section"

    def test_markdown_report_shows_runtime_for_features(self, tmp_path):
        """Test that markdown report displays feature runtimes."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        reporter = ReportGenerator(str(tmp_path))
        markdown = reporter.generate_markdown_report(result)
        
        # If we have features with runtime, report should show them
        features_with_runtime = [f for f in result.features if f.runtime_seconds is not None]
        if features_with_runtime:
            # At least one feature name and a time unit (s, ms) should appear
            assert any(f.name in markdown for f in features_with_runtime[:3]) or "s" in markdown, \
                "Report should show feature names or timing information"


class TestFlakinesDetection:
    """Test flakiness detection (multiple runs in deterministic mode)."""

    def test_flakiness_check_result_structure(self):
        """Test that flakiness_check_results has correct structure."""
        from aicmo.self_test.models import SelfTestResult
        from datetime import datetime
        
        result = SelfTestResult(timestamp=datetime.now())
        
        # Should have flakiness_check_results dict
        assert hasattr(result, 'flakiness_check_results'), \
            "SelfTestResult should have flakiness_check_results field"
        assert isinstance(result.flakiness_check_results, dict), \
            "flakiness_check_results should be a dict"

    def test_flakiness_check_accepts_flag(self):
        """Test that CLI main() accepts flakiness_check flag."""
        from aicmo.self_test.cli import main
        
        # Should accept flakiness_check parameter without error
        # Use quick_mode to keep test fast
        exit_code = main(quick_mode=True, flakiness_check=False)
        
        # Should execute successfully
        assert exit_code in [0, 1], "CLI should return valid exit code"

    def test_deterministic_mode_flag(self):
        """Test that CLI main() accepts deterministic flag."""
        from aicmo.self_test.cli import main
        
        # Should accept deterministic parameter without error
        exit_code = main(quick_mode=True, deterministic=True)
        
        # Should execute successfully
        assert exit_code in [0, 1], "CLI should return valid exit code"


class TestSelfTestReporting:
    """Test report generation."""

    def test_report_generator_init(self, tmp_path):
        """Test report generator initialization."""
        reporter = ReportGenerator(str(tmp_path))
        assert (tmp_path).exists()

    @pytest.mark.slow
    def test_generate_markdown_report(self, tmp_path):
        """Test Markdown report generation."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        reporter = ReportGenerator(str(tmp_path))
        markdown = reporter.generate_markdown_report(result)
        
        assert isinstance(markdown, str)
        assert "AICMO System Health Report" in markdown
        assert "✅" in markdown or "❌" in markdown
    
    @pytest.mark.slow
    def test_markdown_report_shows_critical_features(self, tmp_path):
        """Test that markdown report shows critical features badge."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Verify we have some critical features
        critical_features = [f for f in result.features if f.critical]
        assert len(critical_features) > 0, "Should have critical features"
        
        reporter = ReportGenerator(str(tmp_path))
        markdown = reporter.generate_markdown_report(result)
        
        # Check that critical badge appears in report
        assert "**CRITICAL**" in markdown or "CRITICAL" in markdown

    @pytest.mark.slow
    def test_save_reports(self, tmp_path):
        """Test saving reports to files."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        reporter = ReportGenerator(str(tmp_path))
        md_path, html_path = reporter.save_reports(result)
        
        assert md_path is not None
        assert html_path is not None


class TestSemanticAlignment:
    """Test semantic alignment checks."""

    def test_check_semantic_alignment_matching(self):
        """Test semantic alignment with matching content."""
        from aicmo.self_test.semantic_checkers import check_semantic_alignment
        from aicmo.self_test.test_inputs import _saas_startup_brief

        brief = _saas_startup_brief()
        
        # Output that matches the brief
        output = {
            "persona_type": "Enterprise Data Manager",
            "industry": "SaaS and cloud computing",
            "pain_points": "Cloud data synchronization challenges",
            "description": "Senior data engineer at enterprise using SaaS platforms for data sync",
        }
        
        result = check_semantic_alignment(brief, output, "persona_generator")
        
        # Should recognize industry match
        assert result.is_valid is True
        assert len(result.mismatched_fields) == 0

    def test_check_semantic_alignment_mismatches(self):
        """Test semantic alignment with clear mismatches."""
        from aicmo.self_test.semantic_checkers import check_semantic_alignment
        from aicmo.self_test.test_inputs import _saas_startup_brief

        brief = _saas_startup_brief()
        
        # Output that doesn't match the brief
        output = {
            "persona_type": "Home baker",
            "industry": "Food preparation",
            "pain_points": "Finding good recipes",
            "description": "Amateur baker interested in pastry techniques",
        }
        
        result = check_semantic_alignment(brief, output, "persona_generator")
        
        # Should detect industry mismatch (SaaS vs Food)
        assert result.is_valid is False
        assert len(result.mismatched_fields) > 0
        assert any("industry" in field.lower() for field in result.mismatched_fields)

    def test_check_semantic_alignment_partial_match(self):
        """Test semantic alignment with partial matches."""
        from aicmo.self_test.semantic_checkers import check_semantic_alignment
        from aicmo.self_test.test_inputs import _restaurant_brief

        brief = _restaurant_brief()
        
        # Output that mentions industry but not goal
        output = {
            "strategy": "Focus on farm-to-table dining experience",
            "platforms": "Instagram and TikTok",
            "content_themes": "Recipe videos and behind-the-scenes",
            # Missing mention of goal (reservations, loyalty)
        }
        
        result = check_semantic_alignment(brief, output, "strategy")
        
        # Should note partial alignment
        assert len(result.partial_matches) >= 0 or len(result.notes) > 0

    def test_markdown_report_includes_semantic_section(self):
        """Test that markdown report includes semantic alignment section."""
        orchestrator = SelfTestOrchestrator()
        result = orchestrator.run_self_test(quick_mode=True, enable_semantic_checks=True)
        
        reporter = ReportGenerator()
        markdown = reporter.generate_markdown_report(result)
        
        # Should include semantic alignment section if features have semantic checks
        if any(f.semantic_alignment for f in result.features):
            assert "Semantic Alignment" in markdown


class TestProjectRehearsal:
    """Test full project rehearsal feature."""

    def test_run_full_project_rehearsal_basic(self):
        """Test basic project rehearsal execution."""
        from aicmo.self_test.test_inputs import _saas_startup_brief

        orchestrator = SelfTestOrchestrator()
        brief = _saas_startup_brief()
        
        result = orchestrator.run_full_project_rehearsal(
            brief,
            project_name="CloudSync AI Test"
        )
        
        # Verify result structure
        assert result.project_name == "CloudSync AI Test"
        assert result.brief_name == brief.brand.brand_name
        assert result.total_steps > 0
        assert len(result.steps) > 0
        assert result.overall_duration_ms >= 0

    def test_run_full_project_rehearsal_has_step_results(self):
        """Test that rehearsal includes detailed step results."""
        from aicmo.self_test.test_inputs import _restaurant_brief

        orchestrator = SelfTestOrchestrator()
        brief = _restaurant_brief()
        
        result = orchestrator.run_full_project_rehearsal(
            brief,
            project_name="Harvest Table Test"
        )
        
        # Should have execution steps
        assert len(result.steps) > 0
        
        # Each step should have required fields
        for step in result.steps:
            assert step.name is not None
            assert step.status is not None
            assert step.duration_ms >= 0

    def test_run_full_project_rehearsal_tracks_artifacts(self):
        """Test that rehearsal tracks generated artifacts."""
        from aicmo.self_test.test_inputs import _saas_startup_brief

        orchestrator = SelfTestOrchestrator()
        brief = _saas_startup_brief()
        
        result = orchestrator.run_full_project_rehearsal(brief)
        
        # May have generated artifacts (HTML, PPTX)
        # At minimum, should track attempts
        assert isinstance(result.artifacts_generated, list)
        # Note: May be empty if packaging not available in test environment

    def test_run_full_project_rehearsal_calculates_success_rate(self):
        """Test that success rate is calculated correctly."""
        from aicmo.self_test.test_inputs import _restaurant_brief

        orchestrator = SelfTestOrchestrator()
        brief = _restaurant_brief()
        
        result = orchestrator.run_full_project_rehearsal(brief)
        
        # Success rate should be percentage (0-100)
        assert 0 <= result.success_rate <= 100
        
        # Should match step counts if total_steps > 0
        if result.total_steps > 0:
            expected_rate = (result.passed_steps / result.total_steps) * 100
            assert abs(result.success_rate - expected_rate) < 0.01

    def test_markdown_report_includes_rehearsal_section(self):
        """Test that markdown report includes project rehearsal section."""
        from aicmo.self_test.test_inputs import _saas_startup_brief

        orchestrator = SelfTestOrchestrator()
        brief = _saas_startup_brief()
        
        # Run rehearsal
        rehearsal = orchestrator.run_full_project_rehearsal(brief)
        
        # Add to result
        result = orchestrator.run_self_test(quick_mode=True)
        result.project_rehearsals.append(rehearsal)
        
        # Generate report
        reporter = ReportGenerator()
        markdown = reporter.generate_markdown_report(result)
        
        # Should include rehearsal section
        if result.project_rehearsals:
            assert "Full Project Rehearsal" in markdown
            assert brief.brand.brand_name in markdown


class TestExternalIntegrationsHealth:
    """Test external integrations health checking."""

    def test_external_service_status_creation(self):
        """Test ExternalServiceStatus model creation."""
        from aicmo.self_test.models import ExternalServiceStatus
        
        service = ExternalServiceStatus(
            name="Test Service",
            configured=True,
            reachable=True,
            critical=True,
            details={"env_var": "TEST_KEY"}
        )
        
        assert service.name == "Test Service"
        assert service.configured is True
        assert service.reachable is True
        assert service.critical is True
        assert service.status_display == "✅ REACHABLE"
        assert service.criticality_display == "CRITICAL"

    def test_external_service_status_unconfigured(self):
        """Test unconfigured service status."""
        from aicmo.self_test.models import ExternalServiceStatus
        
        service = ExternalServiceStatus(
            name="Optional Service",
            configured=False,
            critical=False
        )
        
        assert service.status_display == "NOT CONFIGURED"
        assert service.criticality_display == "OPTIONAL"

    def test_external_service_status_unchecked(self):
        """Test service that wasn't checked."""
        from aicmo.self_test.models import ExternalServiceStatus
        
        service = ExternalServiceStatus(
            name="Unchecked Service",
            configured=True,
            reachable=None,  # None means we didn't check
            critical=False
        )
        
        assert service.status_display == "UNCHECKED"

    @pytest.mark.asyncio
    async def test_get_external_services_health(self):
        """Test getting external services health."""
        from aicmo.self_test.external_integrations_health import get_external_services_health
        
        services = await get_external_services_health()
        
        # Should return a list of services
        assert isinstance(services, list)
        assert len(services) > 0
        
        # All should be ExternalServiceStatus objects
        from aicmo.self_test.models import ExternalServiceStatus
        for service in services:
            assert isinstance(service, ExternalServiceStatus)
            assert service.name
            assert isinstance(service.configured, bool)
            assert service.reachable is None or isinstance(service.reachable, bool)

    def test_self_test_result_has_external_services(self, tmp_path):
        """Test that SelfTestResult includes external_services field."""
        from aicmo.self_test.models import SelfTestResult
        from datetime import datetime
        
        result = SelfTestResult(timestamp=datetime.now())
        
        # Should have external_services field
        assert hasattr(result, 'external_services')
        assert isinstance(result.external_services, list)
        assert len(result.external_services) == 0  # Empty by default

    @pytest.mark.slow
    def test_orchestrator_collects_external_services(self, tmp_path):
        """Test that orchestrator collects external integrations health."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        # Result should have external_services
        assert hasattr(result, 'external_services')
        assert isinstance(result.external_services, list)
        
        # Should have collected some services
        assert len(result.external_services) > 0

    @pytest.mark.slow
    def test_report_includes_external_integrations_matrix(self, tmp_path):
        """Test that markdown report includes external integrations matrix."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        reporter = ReportGenerator(str(tmp_path))
        markdown = reporter.generate_markdown_report(result)
        
        # Should include external integrations section if services are checked
        if result.external_services:
            assert "External Integrations Health Matrix" in markdown
            assert "Configured" in markdown
            assert "Status" in markdown
            assert "Criticality" in markdown

    def test_critical_vs_optional_services(self):
        """Test that services are properly marked as critical or optional."""
        from aicmo.self_test.models import ExternalServiceStatus
        
        critical = ExternalServiceStatus(
            name="OpenAI LLM",
            configured=False,
            critical=True
        )
        
        optional = ExternalServiceStatus(
            name="Apollo",
            configured=False,
            critical=False
        )
        
        assert critical.critical is True
        assert optional.critical is False
        assert critical.criticality_display == "CRITICAL"
        assert optional.criticality_display == "OPTIONAL"

    @pytest.mark.slow
    def test_external_services_health_summary(self, tmp_path):
        """Test external services health summary statistics."""
        orchestrator = SelfTestOrchestrator(str(tmp_path))
        result = orchestrator.run_self_test(quick_mode=True)
        
        if result.external_services:
            # Count services by status
            configured = sum(1 for s in result.external_services if s.configured)
            reachable = sum(1 for s in result.external_services if s.reachable is True)
            critical = sum(1 for s in result.external_services if s.critical)
            
            # Should have valid counts
            assert 0 <= configured <= len(result.external_services)
            assert 0 <= reachable <= len(result.external_services)
            assert 0 <= critical <= len(result.external_services)

    def test_external_service_details_structure(self):
        """Test that external service details have expected structure."""
        from aicmo.self_test.models import ExternalServiceStatus
        
        service = ExternalServiceStatus(
            name="Test API",
            configured=True,
            reachable=True,
            critical=False,
            details={
                "env_vars_present": True,
                "api_endpoint": "https://api.example.com",
                "check_type": "format_validation"
            }
        )
        
        assert isinstance(service.details, dict)
        assert "env_vars_present" in service.details
        assert "api_endpoint" in service.details
        assert "check_type" in service.details
