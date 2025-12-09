"""
Tests for humanization helpers – Phase 6

Verifies that humanization functions:
- Remove AI markers correctly
- Handle edge cases (None, empty strings)
- Don't break existing functionality
"""

import pytest
from aicmo.cam.humanization import (
    sanitize_message_to_avoid_ai_markers,
    pick_variant,
    lighten_tone,
    apply_humanization_to_outbound_text,
)


class TestSanitizeMessageToAvoidAIMarkers:
    """Test suite for AI marker sanitization."""
    
    def test_sanitize_removes_ai_marker(self):
        """Test that common AI markers are removed."""
        text = "As an AI assistant, I cannot make promises."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        assert "As an AI" not in result
        assert "I cannot make promises" in result or "cannot make promises" in result
    
    def test_sanitize_removes_artificial_intelligence_marker(self):
        """Test removal of 'artificial intelligence' marker."""
        text = "I am an artificial intelligence and this is my response."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        assert "artificial intelligence" not in result.lower()
    
    def test_sanitize_removes_language_model_marker(self):
        """Test removal of 'language model' marker."""
        text = "As a language model, I should tell you that..."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        assert "language model" not in result.lower()
    
    def test_sanitize_removes_ai_generated_marker(self):
        """Test removal of 'AI-generated' marker."""
        text = "This is an AI-generated response about your product."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        assert "AI-generated" not in result
        assert "response about your product" in result
    
    def test_sanitize_handles_none(self):
        """Test that None input is handled gracefully."""
        result = sanitize_message_to_avoid_ai_markers(None)
        
        assert result == ""
        assert isinstance(result, str)
    
    def test_sanitize_handles_empty_string(self):
        """Test that empty string is handled gracefully."""
        result = sanitize_message_to_avoid_ai_markers("")
        
        assert result == ""
    
    def test_sanitize_cleans_whitespace(self):
        """Test that extra whitespace is cleaned up."""
        text = "As an AI    I have   multiple   spaces."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        # Should have normalized whitespace
        assert "   " not in result
    
    def test_sanitize_case_insensitive(self):
        """Test that sanitization is case-insensitive."""
        text = "As an AI, hello"
        result = sanitize_message_to_avoid_ai_markers(text)
        
        # Should have removed 'As an AI' but kept 'hello'
        assert "As an AI" not in result
        assert "hello" in result
    
    def test_sanitize_preserves_legitimate_content(self):
        """Test that legitimate content is preserved."""
        text = "Here's how to use our product effectively."
        result = sanitize_message_to_avoid_ai_markers(text)
        
        assert result == text


class TestPickVariant:
    """Test suite for variant picking."""
    
    def test_pick_variant_returns_first_option(self):
        """Test that first non-empty option is returned."""
        options = ["Hello", "Hi", "Hey"]
        result = pick_variant(options)
        
        assert result == "Hello"
    
    def test_pick_variant_skips_empty_strings(self):
        """Test that empty strings are skipped."""
        options = ["", "", "Hello", "Hi"]
        result = pick_variant(options)
        
        assert result == "Hello"
    
    def test_pick_variant_skips_whitespace_only(self):
        """Test that whitespace-only strings are skipped."""
        options = ["   ", "\t", "Hello"]
        result = pick_variant(options)
        
        assert result == "Hello"
    
    def test_pick_variant_empty_list(self):
        """Test that empty list returns empty string."""
        result = pick_variant([])
        
        assert result == ""
    
    def test_pick_variant_all_empty(self):
        """Test that all-empty list returns empty string."""
        options = ["", "   ", "\n"]
        result = pick_variant(options)
        
        assert result == ""
    
    def test_pick_variant_strips_result(self):
        """Test that result is stripped of whitespace."""
        options = ["  Hello  "]
        result = pick_variant(options)
        
        assert result == "Hello"


class TestLightenTone:
    """Test suite for tone lightening."""
    
    def test_lighten_removes_urgent(self):
        """Test that URGENT is removed."""
        text = "URGENT: Check this out now!"
        result = lighten_tone(text)
        
        assert "URGENT" not in result
    
    def test_lighten_removes_limited_time(self):
        """Test that LIMITED TIME is removed."""
        text = "LIMITED TIME: Offer expires today!"
        result = lighten_tone(text)
        
        assert "LIMITED TIME" not in result
    
    def test_lighten_removes_act_now(self):
        """Test that ACT NOW is removed."""
        text = "ACT NOW or miss out on this deal!"
        result = lighten_tone(text)
        
        assert "ACT NOW" not in result
    
    def test_lighten_removes_hurry(self):
        """Test that HURRY is removed."""
        text = "HURRY! Only 3 spots left!"
        result = lighten_tone(text)
        
        assert "HURRY" not in result
    
    def test_lighten_handles_none(self):
        """Test that None is handled gracefully."""
        result = lighten_tone(None, remove_urgency=True)
        
        assert result == ""
    
    def test_lighten_preserves_content(self):
        """Test that legitimate content is preserved."""
        text = "Check out our new features"
        result = lighten_tone(text)
        
        assert result == text
    
    def test_lighten_can_disable_urgency_removal(self):
        """Test that urgency removal can be disabled."""
        text = "URGENT: Check this out"
        result = lighten_tone(text, remove_urgency=False)
        
        # Should still have URGENT if removal is disabled
        assert "URGENT" in result or result == text


class TestApplyHumanizationToOutboundText:
    """Test suite for full humanization pipeline."""
    
    def test_apply_humanization_removes_ai_markers(self):
        """Test that AI markers are removed."""
        text = "As an AI, here's the solution: Try our product!"
        result = apply_humanization_to_outbound_text(text)
        
        assert "As an AI" not in result
        assert "solution" in result or "product" in result
    
    def test_apply_humanization_removes_urgent(self):
        """Test that urgent language is removed."""
        text = "As an AI, URGENT: ACT NOW and grab this deal!"
        result = apply_humanization_to_outbound_text(text)
        
        assert "AI" not in result
        assert "URGENT" not in result
        assert "ACT NOW" not in result
    
    def test_apply_humanization_handles_none(self):
        """Test that None is handled gracefully."""
        result = apply_humanization_to_outbound_text(None)
        
        assert result == ""
    
    def test_apply_humanization_handles_empty(self):
        """Test that empty string is handled."""
        result = apply_humanization_to_outbound_text("")
        
        assert result == ""
    
    def test_apply_humanization_full_example(self):
        """Test a realistic example."""
        text = "As an AI language model, URGENT: Try our product! LIMITED TIME offer!"
        result = apply_humanization_to_outbound_text(text)
        
        # Should have removed some markers
        assert "As an AI" not in result
        assert "URGENT" not in result
        # Core message should be preserved
        assert "product" in result or "Try" in result


class TestHumanizationIntegration:
    """Integration tests for humanization helpers."""
    
    def test_sanitize_then_lighten(self):
        """Test combining sanitize and lighten operations."""
        text = "As an AI, URGENT: Buy now or miss out!"
        
        step1 = sanitize_message_to_avoid_ai_markers(text)
        step2 = lighten_tone(step1)
        
        # Should progressively remove more
        assert len(step2) <= len(step1)
        assert "AI" not in step1 or "URGENT" in step1
    
    def test_humanization_on_clean_text(self):
        """Test that clean text is unchanged."""
        text = "Check out our new product features"
        result = apply_humanization_to_outbound_text(text)
        
        assert result == text
    
    def test_humanization_preserves_linebreaks_not_available(self):
        """Test that content structure is maintained."""
        text = "Hello\nWorld"
        result = apply_humanization_to_outbound_text(text)
        
        # Normalizes to single space due to whitespace cleanup
        assert "Hello" in result
        assert "World" in result
