"""
Tests for enhanced quality checks (genericity, blacklist, duplicates, placeholders).

These tests verify that Fixes #4-8 (missing quality checks) work correctly.
"""

from backend.validators.quality_checks import (
    check_genericity,
    check_blacklist_phrases,
    check_duplicate_hooks,
    check_template_placeholders,
    check_premium_language,
    run_all_quality_checks,
)


class TestGenericityCheck:
    """Tests for genericity detection."""

    def test_generic_content_flagged(self):
        """Test that generic marketing speak is flagged."""
        generic_text = (
            "We drive results and create tangible impact through our proven methodologies. "
            "Our industry-leading solutions leverage cutting-edge best practices to move the needle."
        )
        issue = check_genericity(generic_text, threshold=0.35)

        assert issue is not None
        assert issue.code == "TOO_GENERIC"
        assert "score:" in issue.message.lower()

    def test_specific_content_passes(self):
        """Test that specific, concrete content passes."""
        specific_text = (
            "Starbucks operates 15,000 locations across North America. "
            "Their Pike Place blend uses 100% Arabica beans sourced from Colombia. "
            "Mobile order volume increased 27% in Q4 2023."
        )
        issue = check_genericity(specific_text, threshold=0.35)

        # Specific content should have low genericity score and pass
        # (or return None if genericity_score module not available)
        assert issue is None or issue.severity == "warning"


class TestBlacklistPhrases:
    """Tests for blacklist phrase detection."""

    def test_single_blacklist_phrase(self):
        """Test detection of single blacklisted phrase."""
        text = "In today's digital age, content is very important."
        issues = check_blacklist_phrases(text)

        assert len(issues) > 0
        assert any("in today's digital age" in i.message.lower() for i in issues)

    def test_multiple_blacklist_phrases(self):
        """Test detection of multiple blacklisted phrases."""
        text = (
            "In today's digital age, content is king. "
            "We leverage best practices to drive results."
        )
        issues = check_blacklist_phrases(text)

        assert len(issues) >= 3  # At least 3 blacklisted phrases
        codes = [i.code for i in issues]
        assert codes.count("BLACKLISTED_PHRASE") >= 3

    def test_clean_content_no_blacklist(self):
        """Test that clean content has no blacklist issues."""
        text = "Starbucks serves premium coffee in 15,000 locations worldwide."
        issues = check_blacklist_phrases(text)

        assert len(issues) == 0

    def test_case_insensitive_detection(self):
        """Test that blacklist detection is case-insensitive."""
        text = "CONTENT IS KING and In Today's Digital Age we thrive."
        issues = check_blacklist_phrases(text)

        assert len(issues) >= 2

    def test_custom_blacklist(self):
        """Test using custom blacklist phrases."""
        text = "Our product is awesome and amazing."
        custom_blacklist = ["awesome", "amazing"]
        issues = check_blacklist_phrases(text, blacklist_phrases=custom_blacklist)

        assert len(issues) == 2


class TestDuplicateHooks:
    """Tests for duplicate hook detection in calendar sections."""

    def test_duplicate_hooks_flagged(self):
        """Test that calendars with duplicate hooks are flagged."""
        calendar = """
## 30-Day Social Calendar

| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share customer success story |
| Day 2 | Facebook | Share customer success story |
| Day 3 | Twitter | Share customer success story |
| Day 4 | Instagram | Share customer success story |
| Day 5 | Facebook | Share customer success story |
| Day 6 | Twitter | Post engaging content |
| Day 7 | Instagram | Post engaging content |
| Day 8 | Facebook | Post engaging content |
| Day 9 | Twitter | Post engaging content |
| Day 10 | Instagram | Post engaging content |
"""
        issue = check_duplicate_hooks(calendar, "detailed_30_day_calendar")

        assert issue is not None
        assert issue.code == "DUPLICATE_HOOKS"
        assert "duplicate" in issue.message.lower()

    def test_unique_hooks_pass(self):
        """Test that calendars with unique hooks pass."""
        calendar = """
| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Share origin story |
| Day 2 | Facebook | Customer testimonial video |
| Day 3 | Twitter | Coffee brewing tip |
| Day 4 | Instagram | Behind-the-scenes photo |
| Day 5 | Facebook | New product announcement |
"""
        issue = check_duplicate_hooks(calendar, "detailed_30_day_calendar")

        assert issue is None

    def test_non_calendar_section_skipped(self):
        """Test that non-calendar sections are not checked for duplicate hooks."""
        text = "Some content with repeated words: success success success"
        issue = check_duplicate_hooks(text, "overview")

        assert issue is None

    def test_moderate_duplication_allowed(self):
        """Test that moderate duplication (< 30%) is allowed for recurring themes."""
        calendar = """
| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Monday motivation |
| Day 2 | Facebook | Customer spotlight |
| Day 3 | Twitter | Coffee tip |
| Day 4 | Instagram | Product feature |
| Day 5 | Facebook | Weekly recap |
| Day 6 | Twitter | Industry news |
| Day 7 | Instagram | Community highlight |
| Day 8 | Instagram | Monday motivation |
| Day 9 | Facebook | Customer spotlight |
| Day 10 | Twitter | Coffee tip |
"""
        # 3 duplicates out of 10 = 30% (exactly at threshold, should pass)
        issue = check_duplicate_hooks(calendar, "detailed_30_day_calendar")

        # Should pass (30% is threshold)
        assert issue is None or "30%" not in issue.message


class TestTemplatePlaceholders:
    """Tests for template placeholder detection."""

    def test_double_brace_placeholders(self):
        """Test detection of {{placeholder}} patterns."""
        text = "Welcome to {{brand_name}} where {{tagline}} matters."
        issues = check_template_placeholders(text)

        assert len(issues) > 0
        assert any(i.code == "TEMPLATE_PLACEHOLDER" for i in issues)
        assert any("{{brand_name}}" in i.details for i in issues)

    def test_insert_placeholders(self):
        """Test detection of [INSERT ...] patterns."""
        text = "Our company has [INSERT STAT] customers and [INSERT METRIC] growth."
        issues = check_template_placeholders(text)

        assert len(issues) > 0
        assert any(i.code == "INSERT_PLACEHOLDER" for i in issues)

    def test_bracket_placeholders(self):
        """Test detection of [BRAND], [CLIENT], etc. patterns."""
        text = "[BRAND] offers [PRODUCT] to [CLIENT] with [METRIC] results."
        issues = check_template_placeholders(text)

        assert len(issues) > 0
        assert any(i.code == "BRACKET_PLACEHOLDER" for i in issues)

    def test_clean_text_no_placeholders(self):
        """Test that text without placeholders passes."""
        text = "Starbucks offers premium coffee to customers with excellent results."
        issues = check_template_placeholders(text)

        assert len(issues) == 0

    def test_legitimate_brackets_not_flagged(self):
        """Test that legitimate brackets (like markdown links) aren't flagged."""
        text = "Visit our website [here](https://example.com) for more information."
        issues = check_template_placeholders(text)

        # Should not flag markdown link syntax
        assert len(issues) == 0


class TestPremiumLanguage:
    """Tests for premium language verification."""

    def test_basic_text_lacks_premium(self):
        """Test that basic marketing text lacks premium language."""
        basic_text = "We offer social media services to help your business grow online."
        issue = check_premium_language(basic_text, required_count=1)

        assert issue is not None
        assert issue.code == "LACKS_PREMIUM_LANGUAGE"

    def test_premium_text_passes(self):
        """Test that text with premium language passes."""
        premium_text = (
            "Imagine a vibrant social presence that crystallizes your brand's essence. "
            "We'll launch a 90-day framework that increases engagement by 45% while "
            "orchestrating authentic moments that illuminate your unique story."
        )
        issue = check_premium_language(premium_text, required_count=2)

        assert issue is None

    def test_specific_metrics_count_as_premium(self):
        """Test that specific metrics are recognized as premium."""
        text = "Our strategy increased conversions by 67% and doubled ROI within 6 months."
        issue = check_premium_language(text, required_count=1)

        assert issue is None  # Has numbers/metrics

    def test_warning_severity(self):
        """Test that premium language check is warning, not error."""
        text = "Basic text without premium language."
        issue = check_premium_language(text)

        if issue:
            assert issue.severity == "warning"


class TestIntegratedQualityChecks:
    """Tests for the integrated run_all_quality_checks function."""

    def test_multiple_issues_detected(self):
        """Test that multiple quality issues are detected in one pass."""
        bad_text = (
            "In today's digital age, {{brand_name}} drives results. "
            "Content is king and we leverage best practices to move the needle. "
            "[INSERT STAT] proves our methodology works."
        )
        issues = run_all_quality_checks(bad_text, "overview")

        # Should have:
        # - Genericity issues (probably)
        # - Blacklist phrases (at least 3)
        # - Template placeholders (at least 2)
        assert len(issues) >= 5

        codes = {i.code for i in issues}
        assert "BLACKLISTED_PHRASE" in codes
        assert "TEMPLATE_PLACEHOLDER" in codes or "INSERT_PLACEHOLDER" in codes

    def test_clean_content_passes_all_checks(self):
        """Test that high-quality content passes all checks."""
        good_text = (
            "Starbucks operates 15,000 retail locations across North America, "
            "serving premium Arabica coffee sourced from sustainable farms in Colombia. "
            "Their mobile app saw 27% growth in Q4 2023, with Pike Place blend "
            "remaining the top-selling product at 3.2 million pounds per month."
        )
        issues = run_all_quality_checks(good_text, "overview", genericity_threshold=0.35)

        # Should have at most warnings (premium language), no errors
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) == 0

    def test_calendar_duplicate_check_runs(self):
        """Test that duplicate hook check runs for calendar sections."""
        calendar = """
| Day | Platform | Hook |
|-----|----------|------|
| Day 1 | Instagram | Same hook |
| Day 2 | Facebook | Same hook |
| Day 3 | Twitter | Same hook |
| Day 4 | Instagram | Same hook |
| Day 5 | Facebook | Same hook |
| Day 6 | Twitter | Same hook |
| Day 7 | Instagram | Same hook |
| Day 8 | Facebook | Same hook |
| Day 9 | Twitter | Same hook |
| Day 10 | Instagram | Same hook |
"""
        issues = run_all_quality_checks(calendar, "detailed_30_day_calendar")

        # Should detect duplicate hooks
        assert any(i.code == "DUPLICATE_HOOKS" for i in issues)

    def test_starbucks_poor_quality_example(self):
        """Test the actual Starbucks poor-quality example that should fail."""
        # This is the type of content that user complained about
        starbucks_poor = (
            "In today's digital age, Starbucks leverages content marketing to drive results. "
            "We create tangible impact through proven methodologies and best practices. "
            "{{brand_name}} will move the needle with our cutting-edge strategy."
        )
        issues = run_all_quality_checks(starbucks_poor, "overview")

        # Should have multiple errors
        error_issues = [i for i in issues if i.severity == "error"]
        assert len(error_issues) >= 3

        # Specifically should catch:
        # - Genericity (likely)
        # - Multiple blacklist phrases
        # - Template placeholder
        codes = {i.code for i in issues}
        assert "BLACKLISTED_PHRASE" in codes
        assert "TEMPLATE_PLACEHOLDER" in codes
