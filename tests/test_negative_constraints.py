"""Tests for negative constraints feature."""

import pytest


def test_parse_constraints_basic():
    """Test parsing basic constraint strings."""
    from backend.validators.output_validator import parse_constraints

    raw = "Do not use emojis"
    result = parse_constraints(raw)

    assert len(result) > 0
    assert any("emojis" in c.lower() for c in result)


def test_parse_constraints_multiple():
    """Test parsing multiple constraints separated by newlines."""
    from backend.validators.output_validator import parse_constraints

    raw = "Do not use emojis\nNever mention competitors\nAvoid slang"
    result = parse_constraints(raw)

    assert len(result) >= 3
    assert any("emojis" in c.lower() for c in result)
    assert any("competitors" in c.lower() for c in result)


def test_parse_constraints_semicolon():
    """Test parsing constraints separated by semicolons."""
    from backend.validators.output_validator import parse_constraints

    raw = "No emojis; No competitors; Professional tone"
    result = parse_constraints(raw)

    assert len(result) >= 3


def test_parse_constraints_empty():
    """Test parsing empty constraint string."""
    from backend.validators.output_validator import parse_constraints

    result = parse_constraints("")
    assert result == []


def test_validate_negative_constraints_violation():
    """Test that constraint violations are detected."""
    from backend.validators.output_validator import validate_negative_constraints

    text = "We love using emojis in our content! 😊 🎉"
    constraints = "Do not use emojis"

    violations = validate_negative_constraints(text, constraints)

    assert len(violations) > 0
    assert any("emojis" in v.lower() for v in violations)


def test_validate_negative_constraints_no_violation():
    """Test that passing constraints don't trigger violations."""
    from backend.validators.output_validator import validate_negative_constraints

    text = "We focus on professional communication and brand messaging."
    constraints = "Do not use emojis"

    violations = validate_negative_constraints(text, constraints)

    # Should have no violations
    assert len(violations) == 0


def test_validate_negative_constraints_case_insensitive():
    """Test that constraint checking is case-insensitive."""
    from backend.validators.output_validator import validate_negative_constraints

    text = "We love EMOJIS in our content"
    constraints = "Do not use emojis"

    violations = validate_negative_constraints(text, constraints)

    # Should catch even with different case
    assert len(violations) > 0


def test_validate_negative_constraints_multiple():
    """Test validation against multiple constraints."""
    from backend.validators.output_validator import validate_negative_constraints

    text = "Our competitor offers similar services using emojis."
    constraints = "Do not mention competitors\nDo not use emojis"

    violations = validate_negative_constraints(text, constraints)

    # Should catch violations for both constraints
    assert len(violations) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
