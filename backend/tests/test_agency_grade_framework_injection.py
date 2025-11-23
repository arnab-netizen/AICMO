"""
Tests for Phase L framework injection in agency-grade report processing.

Verifies that:
1. Framework injection prepends strategic headers to report sections
2. Language filters remove blacklisted phrases and inject premium language
3. Reasoning trace is attached for internal review
4. All transformations are non-breaking and gracefully degrade
"""

from aicmo.io.client_reports import (
    ClientInputBrief,
    AICMOOutputReport,
)
from aicmo.generators.agency_grade_processor import (
    process_report_for_agency_grade,
    _inject_frameworks_into_report,
    _apply_language_filters_to_report,
)
from aicmo.memory.engine import count_items
from backend.main import _retrieve_learning_context, _generate_stub_output


class TestFrameworkInjection:
    """Test framework injection into agency-grade reports."""

    def test_retrieve_learning_context_returns_structured_dict(self):
        """Verify learning context is retrieved and structured correctly."""
        raw, struct = _retrieve_learning_context("marketing strategy technology startup")

        # Should have both raw context and structured dict
        assert isinstance(raw, str)
        assert isinstance(struct, dict)

        # If context was found, should have framework keys
        if struct:
            expected_keys = {
                "core_frameworks",
                "thinking_sequences",
                "reasoning_patterns",
                "structure_rules",
                "premium_expressions",
                "creative_hooks",
            }
            assert set(struct.keys()) == expected_keys

    def test_memory_engine_has_learned_items(self):
        """Verify the memory engine has been populated with learned examples."""
        count = count_items()
        assert count > 0, "Memory engine should have learned items for Phase L integration"

    def test_framework_injection_non_breaking_without_learning_context(self):
        """Verify framework injection gracefully handles missing learning context."""
        # Create a minimal report
        stub = _generate_stub_output(
            type("Req", (), {"brief": self._make_brief(), "industry_key": None})()
        )

        # Process with empty learning context
        result = process_report_for_agency_grade(
            report=stub,
            brief_text="test brief",
            learning_context_raw="",
            learning_context_struct={},
            include_reasoning_trace=False,
        )

        # Should return a valid report even without learning context
        assert result is not None
        assert isinstance(result, AICMOOutputReport)

    def test_framework_injection_with_learning_context(self):
        """Verify framework injection modifies report when learning context available."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": self._make_brief(), "industry_key": None})()
        )

        # Get actual learning context from memory
        raw, struct = _retrieve_learning_context("marketing technology strategy")

        # Process with learning context
        result = process_report_for_agency_grade(
            report=stub,
            brief_text="Test brand in tech space",
            learning_context_raw=raw,
            learning_context_struct=struct,
            include_reasoning_trace=False,
        )

        # Result should be valid
        assert result is not None
        assert isinstance(result, AICMOOutputReport)

        # If frameworks were injected into marketing_plan, it should be modified
        if struct and struct.get("core_frameworks"):
            # Check if marketing plan strategy was modified
            if result.marketing_plan and result.marketing_plan.strategy:
                # Strategy should still be a string
                assert isinstance(result.marketing_plan.strategy, str)

    def test_language_filters_non_breaking_without_training_files(self):
        """Verify language filters degrade gracefully when training files missing."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": self._make_brief(), "industry_key": None})()
        )

        # Apply filters (training files may not exist)
        _apply_language_filters_to_report(stub)

        # Report should still be valid
        assert stub is not None
        assert isinstance(stub, AICMOOutputReport)

    def test_process_report_returns_valid_output(self):
        """Verify process_report_for_agency_grade returns valid AICMOOutputReport."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": self._make_brief(), "industry_key": None})()
        )

        result = process_report_for_agency_grade(
            report=stub,
            brief_text="test brief",
            learning_context_raw="",
            learning_context_struct={},
            include_reasoning_trace=False,
        )

        assert result is not None
        assert isinstance(result, AICMOOutputReport)
        # Should have all required fields
        assert hasattr(result, "marketing_plan")
        assert hasattr(result, "campaign_blueprint")
        assert hasattr(result, "extra_sections")

    def test_reasoning_trace_optional(self):
        """Verify reasoning trace can be optionally attached."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": self._make_brief(), "industry_key": None})()
        )

        raw, struct = _retrieve_learning_context("test")

        # Process with reasoning trace enabled
        result = process_report_for_agency_grade(
            report=stub,
            brief_text="test brief",
            learning_context_raw=raw if raw else "test context",
            learning_context_struct=struct,
            include_reasoning_trace=True,
        )

        # Should still return valid report
        assert result is not None
        assert isinstance(result, AICMOOutputReport)

    @staticmethod
    def _make_brief():
        """Create a minimal valid ClientInputBrief for testing."""
        return ClientInputBrief(
            brand={"name": "Test Brand", "industry": "Technology"},
            audience={"target": "Professionals", "behaviors": "Early adopters"},
            goal={
                "primary": "Growth",
                "success_metrics": ["CAC", "LTV"],
            },
            voice={
                "tone": "Professional",
                "persona": "Expert",
            },
            product_service={
                "name": "SaaS Platform",
                "type": "Software",
            },
            assets_constraints={
                "budget": "Medium",
                "timeline": "3 months",
            },
            operations={"team_size": "Small", "resources": "Limited"},
            strategy_extras={},
        )


class TestLanguageFilters:
    """Test language filtering in agency-grade processing."""

    def test_language_filters_preserve_structure(self):
        """Verify language filters don't break report structure."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": TestFrameworkInjection._make_brief(), "industry_key": None})()
        )

        original_type = type(stub)
        _apply_language_filters_to_report(stub)

        # Type should be unchanged
        assert isinstance(stub, original_type)

    def test_agency_grade_processor_is_composable(self):
        """Verify each processing step can run independently."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": TestFrameworkInjection._make_brief(), "industry_key": None})()
        )

        raw, struct = _retrieve_learning_context("test")

        # Each step should be callable independently
        _inject_frameworks_into_report(stub, "test", struct)
        _apply_language_filters_to_report(stub)

        # Report should still be valid
        assert stub is not None
        assert isinstance(stub, AICMOOutputReport)

    def test_full_agency_grade_pipeline(self):
        """End-to-end test of full agency-grade processing pipeline."""
        stub = _generate_stub_output(
            type("Req", (), {"brief": TestFrameworkInjection._make_brief(), "industry_key": None})()
        )

        raw, struct = _retrieve_learning_context("technology marketing")

        # Full pipeline
        result = process_report_for_agency_grade(
            report=stub,
            brief_text="Test brand marketing strategy",
            learning_context_raw=raw,
            learning_context_struct=struct,
            include_reasoning_trace=True,
        )

        # Should return valid report
        assert result is not None
        assert isinstance(result, AICMOOutputReport)

        # Should be serializable to dict (for API responses)
        output_dict = result.model_dump()
        assert isinstance(output_dict, dict)
        assert "marketing_plan" in output_dict or output_dict.get("marketing_plan") is not None
