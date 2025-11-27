# tests/test_humanizer.py
from backend.humanizer import (
    humanize_report_text,
    HumanizerConfig,
    extract_headings,
    extract_numbers,
    token_change_ratio,
)


class DummyBrief:
    def __init__(self):
        self.industry = "boutique_retail"
        self.location = "Kolkata – Gariahat"
        self.brand_name = "Test Boutique"
        self.primary_goal = "Increase festive sales"


def test_humanizer_preserves_headings_and_numbers():
    original = (
        "# Campaign Overview\n"
        "This Diwali campaign runs for 30 days and targets 3 primary segments.\n\n"
        "## Budget & Targets\n"
        "Total budget is 150000 INR. Target ROI is 3.5 times better.\n"
    )
    brief = DummyBrief()
    cfg = HumanizerConfig(level="medium", max_change_ratio=0.5)
    industry_profile = {
        "word_substitutions": {
            "customers": "shoppers",
        }
    }

    humanized = humanize_report_text(
        original,
        brief=brief,
        pack_key="strategy_campaign",
        industry_key="boutique_retail",
        config=cfg,
        industry_profile=industry_profile,
    )

    # Headings should still be there
    orig_headings = extract_headings(original)
    new_headings = extract_headings(humanized)
    for h in orig_headings.keys():
        assert h in new_headings, f"Heading missing after humanization: {h}"

    # Numbers should still be present
    orig_numbers = extract_numbers(original)
    new_numbers = extract_numbers(humanized)
    for n in orig_numbers.keys():
        assert n in new_numbers, f"Number missing after humanization: {n}"

    # Change ratio should not be extreme
    ratio = token_change_ratio(original, humanized)
    assert ratio < 0.6, f"Change ratio too high: {ratio}"


def test_humanizer_noop_when_off():
    original = "Simple line with 3 numbers: 10, 20 and 30."
    brief = DummyBrief()
    cfg = HumanizerConfig(level="off")
    humanized = humanize_report_text(
        original,
        brief=brief,
        pack_key="quick_social",
        industry_key="boutique_retail",
        config=cfg,
        industry_profile=None,
    )
    assert humanized == original


def test_extract_headings():
    text = """
# Main Heading
Some content here.

## Sub Heading
More content.

### Another level
And more.

## Another heading:
    """
    headings = extract_headings(text)
    assert "# Main Heading" in headings
    assert "## Sub Heading" in headings
    assert "### Another level" in headings
    assert "## Another heading:" in headings


def test_extract_numbers():
    text = "Budget: 150000. Target: 3.5x. Days: 30."
    numbers = extract_numbers(text)
    assert "150000" in numbers
    assert "3" in numbers  # 3.5 is extracted as "3" and "5" separately by the regex
    assert "30" in numbers


def test_token_change_ratio():
    original = "The quick brown fox jumps over the lazy dog."
    identical = "The quick brown fox jumps over the lazy dog."
    ratio1 = token_change_ratio(original, identical)
    assert ratio1 == 0.0, f"Identical text should have ratio 0, got {ratio1}"

    different = "The fast brown cat jumps over the sleeping canine."
    ratio2 = token_change_ratio(original, different)
    assert 0 < ratio2 < 1.0, f"Different text should have ratio between 0 and 1, got {ratio2}"


def test_humanizer_applies_phrase_replacements():
    original = "In today's digital age, we use a holistic approach to cut through the clutter."
    brief = DummyBrief()
    cfg = HumanizerConfig(level="medium")

    humanized = humanize_report_text(
        original,
        brief=brief,
        pack_key="strategy_campaign",
        industry_key="boutique_retail",
        config=cfg,
        industry_profile=None,
    )

    # Check that at least some replacements were applied
    assert "holistic" not in humanized.lower() or "joined-up" in humanized.lower()
    # The result should be different
    assert humanized != original


def test_humanizer_min_section_length():
    """Test that very short text is not humanized."""
    short_text = "Hi"
    brief = DummyBrief()
    cfg = HumanizerConfig(level="medium", min_section_length_to_edit=100)

    humanized = humanize_report_text(
        short_text,
        brief=brief,
        pack_key="strategy_campaign",
        industry_key="boutique_retail",
        config=cfg,
        industry_profile=None,
    )

    assert humanized == short_text
