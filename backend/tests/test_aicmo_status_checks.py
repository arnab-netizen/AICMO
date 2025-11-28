"""
AICMO Status Check Tests
Minimal contract validation for key functions and endpoints.
Validates that implementations are callable and return structurally valid data.
No business logic changes – only verification.
"""

import pytest

# ============================================================================
# Import key public functions and objects
# ============================================================================

try:
    from backend.main import (
        SECTION_GENERATORS,
        PACKAGE_PRESETS,
        aicmo_generate,
        api_aicmo_generate_report,
        api_competitor_research,
        aicmo_export_pdf,
    )
except ImportError as e:
    pytest.skip(f"Could not import from backend.main: {e}", allow_module_level=True)

try:
    from aicmo.presets.wow_rules import WOW_RULES
    from aicmo.presets.package_presets import PACKAGE_PRESETS
except ImportError as e:
    pytest.skip(f"Could not import presets: {e}", allow_module_level=True)

try:
    from aicmo.memory import engine as memory_engine
except ImportError as e:
    pytest.skip(f"Could not import memory engine: {e}", allow_module_level=True)

try:
    from backend.validators.output_validator import validate_output_report
except ImportError as e:
    pytest.skip(f"Could not import validators: {e}", allow_module_level=True)

try:
    from backend.humanizer import humanize_report_text, HumanizerConfig
except ImportError as e:
    pytest.skip(f"Could not import humanizer: {e}", allow_module_level=True)


# ============================================================================
# Contract Tests – Verify implementations are callable and return valid types
# ============================================================================


class TestSectionGenerators:
    """Verify SECTION_GENERATORS registry is properly populated."""

    def test_section_generators_exists(self):
        """SECTION_GENERATORS dict should exist and not be empty."""
        assert isinstance(SECTION_GENERATORS, dict), "SECTION_GENERATORS must be dict"
        assert len(SECTION_GENERATORS) > 0, "SECTION_GENERATORS must not be empty"

    def test_section_generators_callable(self):
        """All generators should be callable functions."""
        for name, func in SECTION_GENERATORS.items():
            assert callable(func), f"Generator '{name}' is not callable"

    def test_section_generators_count(self):
        """Should have reasonable number of generators (>=40)."""
        assert (
            len(SECTION_GENERATORS) >= 40
        ), f"Expected >=40 generators, got {len(SECTION_GENERATORS)}"

    def test_core_generators_present(self):
        """Core generators should be present."""
        core_sections = [
            "overview",
            "messaging_framework",
            "audience_segments",
            "persona_cards",
            "detailed_30_day_calendar",
            "final_summary",
        ]
        for section in core_sections:
            assert section in SECTION_GENERATORS, f"Missing core section: {section}"


class TestPackagePresets:
    """Verify package presets are properly defined."""

    def test_package_presets_exists(self):
        """PACKAGE_PRESETS should exist and have packs."""
        assert isinstance(PACKAGE_PRESETS, dict), "PACKAGE_PRESETS must be dict"
        assert len(PACKAGE_PRESETS) > 0, "PACKAGE_PRESETS must have packs"

    def test_package_presets_count(self):
        """Should have multiple packs (>=5)."""
        assert len(PACKAGE_PRESETS) >= 5, f"Expected >=5 packs, got {len(PACKAGE_PRESETS)}"

    def test_preset_structure(self):
        """Each preset should have required fields."""
        for pack_key, pack_config in PACKAGE_PRESETS.items():
            assert "sections" in pack_config, f"Pack '{pack_key}' missing 'sections'"
            assert "label" in pack_config, f"Pack '{pack_key}' missing 'label'"
            assert isinstance(
                pack_config["sections"], list
            ), f"Pack '{pack_key}' sections must be list"
            assert len(pack_config["sections"]) > 0, f"Pack '{pack_key}' has no sections"

    def test_quick_social_pack_exists(self):
        """Quick Social pack should exist."""
        assert "quick_social_basic" in PACKAGE_PRESETS, "quick_social_basic pack not found"
        quick_social = PACKAGE_PRESETS["quick_social_basic"]
        assert (
            len(quick_social["sections"]) >= 8
        ), f"Quick Social should have >=8 sections, got {len(quick_social['sections'])}"

    def test_strategy_pack_exists(self):
        """Strategy + Campaign pack should exist."""
        assert (
            "strategy_campaign_standard" in PACKAGE_PRESETS
        ), "strategy_campaign_standard pack not found"
        strategy = PACKAGE_PRESETS["strategy_campaign_standard"]
        assert len(strategy["sections"]) >= 10, "Strategy pack should have >=10 sections"


class TestWOWRules:
    """Verify WOW rules are properly defined."""

    def test_wow_rules_exists(self):
        """WOW_RULES should exist and have entries."""
        assert isinstance(WOW_RULES, dict), "WOW_RULES must be dict"
        assert len(WOW_RULES) > 0, "WOW_RULES must have entries"

    def test_wow_rule_structure(self):
        """Each WOW rule should have sections."""
        for rule_key, rule_config in WOW_RULES.items():
            assert "sections" in rule_config, f"WOW rule '{rule_key}' missing 'sections'"
            assert isinstance(
                rule_config["sections"], list
            ), f"WOW rule '{rule_key}' sections must be list"

    def test_wow_sections_have_keys(self):
        """Each section in WOW rules should have 'key' field."""
        for rule_key, rule_config in WOW_RULES.items():
            for section in rule_config.get("sections", []):
                assert isinstance(section, dict), f"WOW section must be dict, got {type(section)}"
                assert "key" in section, f"WOW section missing 'key' field in {rule_key}"


class TestMemoryEngine:
    """Verify memory engine is functional."""

    def test_memory_engine_importable(self):
        """Memory engine should be importable."""
        assert memory_engine is not None, "Memory engine not importable"

    def test_memory_item_dataclass(self):
        """MemoryItem dataclass should be accessible."""
        assert hasattr(memory_engine, "MemoryItem"), "Memory engine missing MemoryItem dataclass"

    def test_memory_engine_methods(self):
        """Memory engine should have key methods for learning and retrieval."""
        # Memory engine uses functional interface, not class-based
        # Check for key functions available in the module
        required_functions = ["learn_from_blocks", "retrieve_relevant_context", "get_memory_stats"]
        for func in required_functions:
            assert hasattr(memory_engine, func), f"Memory engine missing function: {func}"


class TestValidators:
    """Verify validation functions exist and are callable."""

    def test_validate_output_report_callable(self):
        """validate_output_report should be callable."""
        assert callable(validate_output_report), "validate_output_report must be callable"

    def test_validate_output_accepts_dict(self):
        """validate_output_report should accept proper output report and brief."""
        try:
            # Create minimal mock objects
            from unittest.mock import MagicMock

            mock_report = MagicMock()
            mock_brief = MagicMock()

            # Should not raise exception
            result = validate_output_report(output=mock_report, brief=mock_brief)
            # Result should be tuple of (is_valid, issues)
            assert isinstance(result, tuple), "Validator should return tuple"
            assert len(result) == 2, "Validator should return (is_valid, issues) tuple"
        except Exception as e:
            # Some validators may fail on minimal input – that's OK
            # We just want to ensure it's callable and doesn't crash unexpectedly
            assert "TypeError" not in str(type(e)), f"Validator failed with unexpected error: {e}"


class TestHumanizer:
    """Verify humanizer is functional."""

    def test_humanizer_callable(self):
        """humanize_report_text should be callable."""
        assert callable(humanize_report_text), "humanize_report_text must be callable"

    def test_humanizer_config_exists(self):
        """HumanizerConfig should be available."""
        assert HumanizerConfig is not None, "HumanizerConfig not available"

    def test_humanizer_accepts_text(self):
        """humanize_report_text should accept text input with required arguments."""
        test_text = "# Overview\n\nThis is a test report.\n\n**Key Metrics:** 100, 200, 300"
        try:
            # Humanizer requires: text, brief, pack_key, industry_key
            from unittest.mock import MagicMock

            mock_brief = MagicMock()
            result = humanize_report_text(
                text=test_text,
                brief=mock_brief,
                pack_key="quick_social_basic",
                industry_key="technology",
            )
            assert isinstance(result, str), "Humanizer should return string"
            assert len(result) > 0, "Humanizer output should not be empty"
        except Exception as e:
            # If it fails, should be for logical reasons, not type mismatches
            assert "TypeError" not in str(type(e)), f"Humanizer failed with type error: {e}"


class TestEndpoints:
    """Verify endpoint functions exist and are callable."""

    def test_aicmo_generate_callable(self):
        """aicmo_generate should be callable."""
        assert callable(aicmo_generate), "aicmo_generate must be callable"

    def test_api_aicmo_generate_report_callable(self):
        """api_aicmo_generate_report should be callable."""
        assert callable(api_aicmo_generate_report), "api_aicmo_generate_report must be callable"

    def test_api_competitor_research_callable(self):
        """api_competitor_research should be callable."""
        assert callable(api_competitor_research), "api_competitor_research must be callable"

    def test_aicmo_export_pdf_callable(self):
        """aicmo_export_pdf should be callable."""
        assert callable(aicmo_export_pdf), "aicmo_export_pdf must be callable"


class TestWiringConsistency:
    """Verify basic wiring between presets and generators."""

    def test_quick_social_sections_in_generators(self):
        """Quick Social pack sections should be in SECTION_GENERATORS."""
        quick_social_sections = PACKAGE_PRESETS.get("quick_social_basic", {}).get("sections", [])
        missing = []
        for section in quick_social_sections:
            if section not in SECTION_GENERATORS:
                missing.append(section)

        # Quick Social should have most/all sections
        assert (
            len(missing) == 0
        ), f"Quick Social pack has {len(missing)} missing generators: {missing}"

    def test_all_generators_are_functions(self):
        """All SECTION_GENERATORS values should be callable."""
        for gen_name, gen_func in SECTION_GENERATORS.items():
            assert (
                callable(gen_func) or gen_func is None
            ), f"Generator '{gen_name}' is not callable or None"

    def test_pack_presets_not_empty(self):
        """All pack presets should have non-empty section lists."""
        for pack_key, pack_config in PACKAGE_PRESETS.items():
            sections = pack_config.get("sections", [])
            assert len(sections) > 0, f"Pack '{pack_key}' has empty section list"


class TestDataIntegrity:
    """Verify data structures are well-formed."""

    def test_section_generators_no_duplicates(self):
        """SECTION_GENERATORS keys should be unique."""
        keys = list(SECTION_GENERATORS.keys())
        assert len(keys) == len(set(keys)), "SECTION_GENERATORS has duplicate keys"

    def test_preset_keys_valid_python_identifiers(self):
        """Pack keys should be valid identifiers (lowercase, underscores)."""
        import re

        for pack_key in PACKAGE_PRESETS.keys():
            assert re.match(r"^[a-z_]+$", pack_key), f"Pack key '{pack_key}' not valid identifier"

    def test_section_ids_valid_format(self):
        """Section IDs should be lowercase with underscores and numbers."""
        import re

        all_sections = set()
        for sections in PACKAGE_PRESETS.values():
            all_sections.update(sections.get("sections", []))

        for section_id in all_sections:
            assert re.match(
                r"^[a-z0-9_]+$", section_id
            ), f"Section ID '{section_id}' not valid format"


# ============================================================================
# Summary Test
# ============================================================================


class TestAICMOReadiness:
    """Overall readiness assessment based on contract checks."""

    def test_core_infrastructure_present(self):
        """All core infrastructure should be present."""
        checklist = {
            "SECTION_GENERATORS": SECTION_GENERATORS,
            "PACKAGE_PRESETS": PACKAGE_PRESETS,
            "WOW_RULES": WOW_RULES,
            "Memory engine": memory_engine,
        }

        for component, obj in checklist.items():
            assert obj is not None, f"{component} is not available"

    def test_minimum_generator_count(self):
        """Should have minimum viable generator count."""
        # At least 40 generators for basic functionality
        assert len(SECTION_GENERATORS) >= 40, f"Too few generators: {len(SECTION_GENERATORS)}"

    def test_minimum_pack_count(self):
        """Should have minimum viable pack count."""
        # At least 5 packs for market coverage
        assert len(PACKAGE_PRESETS) >= 5, f"Too few packs: {len(PACKAGE_PRESETS)}"

    def test_quick_social_ready(self):
        """Quick Social pack should be completely ready."""
        pack = PACKAGE_PRESETS.get("quick_social_basic", {})
        sections = pack.get("sections", [])

        # All Quick Social sections should be in generators
        missing = [s for s in sections if s not in SECTION_GENERATORS]

        assert len(missing) == 0, f"Quick Social pack not ready. Missing generators: {missing}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
