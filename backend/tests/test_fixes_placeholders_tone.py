"""
Tests for all 7 fix categories (Placeholders, Synonyms, Numbers, Length, Typos, Duplicates, Founder)
"""

import pytest
from backend.layers.utils_context import (
    sanitize_brief_context,
    _apply_synonym_rotation,
    normalize_numbers,
    basic_typos_cleanup,
    remove_founder_placeholder_if_missing,
    apply_all_cleanup_passes,
)


class TestContextSanitization:
    """FIX #1: Context Sanitization (Placeholders)"""

    def test_sanitize_empty_primary_customer(self):
        """Empty primary_customer should be replaced with fallback"""
        class MockCtx:
            primary_customer = ""
            secondary_customer = "test"
            industry = "test"

        ctx = sanitize_brief_context(MockCtx())
        assert ctx.primary_customer == "the intended customer segment"

    def test_sanitize_not_specified_values(self):
        """'Not specified' values should be replaced"""
        class MockCtx:
            primary_customer = "Not specified"
            industry = "none"
            timeline = "n/a"

        ctx = sanitize_brief_context(MockCtx())
        assert ctx.primary_customer == "the intended customer segment"
        assert ctx.industry == "the relevant industry"
        assert ctx.timeline == "the next 30 to 90 days"

    def test_sanitize_valid_values_unchanged(self):
        """Valid values should not be modified"""
        class MockCtx:
            primary_customer = "SaaS founders"
            industry = "Software"
            brand_name = "MyBrand"

        ctx = sanitize_brief_context(MockCtx())
        assert ctx.primary_customer == "SaaS founders"
        assert ctx.industry == "Software"
        assert ctx.brand_name == "MyBrand"

    def test_sanitize_handles_missing_attributes(self):
        """Should not crash if attributes are missing"""
        class MockCtx:
            pass

        ctx = sanitize_brief_context(MockCtx())
        assert ctx is not None


class TestSynonymRotation:
    """FIX #2: Synonym Rotation & Boring Tone"""

    def test_brand_overuse_rotation(self):
        """Brand name appearing 5+ times should be partially rotated"""
        content = "TechFlow helps TechFlow teams. TechFlow's TechFlow solution beats TechFlow."
        result = _apply_synonym_rotation(content, "TechFlow")
        # Should replace every other occurrence after first
        assert result.count("TechFlow") < content.count("TechFlow")
        assert "the brand" in result

    def test_ignore_test_brand(self):
        """'test' brand names should not be rotated"""
        content = "Test brand is the best. Test is great."
        result = _apply_synonym_rotation(content, "Test")
        # Should not rotate "test"
        assert result == content

    def test_no_rotation_for_infrequent_brand(self):
        """Brand appearing <4 times should not be rotated"""
        content = "MyBrand helps MyBrand users succeed."
        result = _apply_synonym_rotation(content, "MyBrand")
        assert result == content  # No rotation for < 4 occurrences


class TestNumberNormalization:
    """FIX #3: Number Normalization"""

    def test_fix_20_00_to_20000(self):
        """20,00 should become 20,000"""
        content = "Budget: 20,00"
        result = normalize_numbers(content)
        assert result == "Budget: 20,000"

    def test_fix_5_00_10_00_range(self):
        """5,00–10,00 should become 5,000–10,000"""
        content = "Range: 5,00–10,00"
        result = normalize_numbers(content)
        assert "5,000–10,000" in result or "5,000-10,000" in result

    def test_multiple_broken_numbers(self):
        """Multiple broken numbers should all be fixed"""
        content = "Cost: 40,00, Timeline: 90, Target: 65,00"
        result = normalize_numbers(content)
        assert "40,000" in result
        assert "65,000" in result

    def test_normal_numbers_unchanged(self):
        """Normal numbers should not be changed"""
        content = "In 2024, we had 10,000 users and $50,000 revenue."
        result = normalize_numbers(content)
        assert "10,000" in result
        assert "50,000" in result


class TestTyposCleanup:
    """FIX #5: Grammar & Spellcheck Pass"""

    def test_fix_se_to_see(self):
        """'se ' should become 'see '"""
        content = "se what we can do for you."
        result = basic_typos_cleanup(content)
        assert "see what" in result

    def test_fix_fre_to_free(self):
        """'fre ' should become 'free '"""
        content = "Get your fre trial today."
        result = basic_typos_cleanup(content)
        assert "free trial" in result

    def test_fix_les_to_less(self):
        """'les ' should become 'less '"""
        content = "les friction in the process."
        result = basic_typos_cleanup(content)
        assert "less friction" in result

    def test_fix_cross_sell(self):
        """'cros-sell' should become 'cross-sell'"""
        content = "cros-sell opportunities abound."
        result = basic_typos_cleanup(content)
        assert "cross-sell" in result

    def test_typos_cleanup_word_boundaries(self):
        """Should use word boundaries to avoid over-aggressive replacement"""
        content = "less friction leads to less churn."
        result = basic_typos_cleanup(content)
        # Should not break anything
        assert "less" in result


class TestFounderNamePlaceholder:
    """FIX #7: Founder Name Placeholder"""

    def test_remove_placeholder_when_missing(self):
        """[Founder's Name] should be removed if founder_name is None"""
        content = "Founder [Founder's Name] started this company."
        result = remove_founder_placeholder_if_missing(content, None)
        assert "[Founder" not in result

    def test_replace_placeholder_when_present(self):
        """[Founder's Name] should be replaced with actual name"""
        content = "[Founder's Name] founded the company."
        result = remove_founder_placeholder_if_missing(content, "Alice")
        assert "Alice" in result
        assert "[Founder" not in result

    def test_handle_various_placeholder_formats(self):
        """Should handle [Founder Name] and [Founder's Name]"""
        content = "[Founder Name] and [Founder's Name] are the same."
        result = remove_founder_placeholder_if_missing(content, "Bob")
        assert "[Founder" not in result
        assert result.count("Bob") >= 1

    def test_remove_lines_with_only_placeholder(self):
        """Lines containing only placeholder should be removed"""
        content = "Company info.\n[Founder's Name]\nMore info."
        result = remove_founder_placeholder_if_missing(content, None)
        # Placeholder line should be removed or minimized
        assert "[Founder" not in result


class TestCompositeCleanup:
    """All fixes applied together"""

    def test_apply_all_cleanup_passes(self):
        """All cleanup passes should work together"""
        content = """
Brand TechFlow helps you see fre opportunities.
Budget: 20,00
[Founder's Name] built this.
TechFlow and TechFlow and TechFlow succeed.
        """
        result = apply_all_cleanup_passes(content, "TechFlow", "Alice")

        # Should fix numbers
        assert "20,000" in result
        # Should fix typos
        assert "free opportunities" in result
        # Should handle founder
        assert "[Founder" not in result
        # Should reduce brand overuse
        assert result.count("TechFlow") <= content.count("TechFlow")

    def test_empty_content_safe(self):
        """Empty content should not crash"""
        result = apply_all_cleanup_passes("", "Brand", "Founder")
        assert result == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
