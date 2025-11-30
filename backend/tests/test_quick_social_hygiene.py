"""
Quick Social Hygiene Tests

Validates Quick Social pack output quality:
- No banned phrases or template leaks
- Valid hashtags (no slashes/spaces)
- Calendar hook uniqueness
- Reasonable sentence length (avoid AI soup)
"""

import re
import pytest
from fastapi.testclient import TestClient
from backend.main import app


client = TestClient(app)


def _make_quick_social_request(test_id: str = "test1") -> dict:
    """Create minimal Quick Social request payload for /api/aicmo/generate_report endpoint.

    Args:
        test_id: Unique identifier to prevent cache hits across tests
    """
    import time

    # Add timestamp to ensure cache miss
    unique_suffix = f"{test_id}_{int(time.time() * 1000)}"
    return {
        "pack_key": "quick_social_basic",
        "client_brief": {
            "brand_name": f"The Daily Grind {unique_suffix}",
            "industry": "Coffeehouse / Beverage Retail",
            "product_service": "Artisan coffee and pastries",
            "primary_customer": "Busy professionals aged 25-45",
            "primary_goal": "increase in-store foot traffic",
            "timeline": "30 days",
        },
        "stage": "draft",
        "wow_enabled": True,
        "wow_package_key": "quick_social_basic",
    }


def test_no_banned_phrases_in_quick_social(monkeypatch):
    """Ensure Quick Social output doesn't contain template leaks."""
    # Enable stub mode for deterministic content
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="no_banned_phrases")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    assert "report_markdown" in data, "Missing 'report_markdown' in response"

    full_text = data["report_markdown"]

    # Banned phrases that should never appear
    BANNED_PHRASES = [
        "ideal customers",
        "over the next period",
        "within the near term timeframe",
        "Key considerations include the audience's core pain points",
    ]

    for phrase in BANNED_PHRASES:
        assert phrase not in full_text, f"Banned phrase found: '{phrase}'"


def test_valid_hashtags_no_slashes_or_spaces(monkeypatch):
    """Ensure all hashtags are valid (no slashes or spaces)."""
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="valid_hashtags")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    markdown = data.get("report_markdown", "")

    # Find hashtag_strategy section by looking for the heading
    # Extract section between "## Hashtag Strategy" and next "##"
    hashtag_match = re.search(
        r"## .*[Hh]ashtag.*?Strategy.*?\n(.*?)(?=\n## |$)", markdown, re.DOTALL
    )

    hashtag_content = hashtag_match.group(1) if hashtag_match else markdown

    # Extract all hashtags via regex
    hashtags = re.findall(r"#\w+", hashtag_content)

    # Validate each hashtag
    for tag in hashtags:
        # Should not contain slashes
        assert "/" not in tag, f"Invalid hashtag with slash: {tag}"
        # Should not contain spaces (regex already ensures this, but explicit check)
        assert " " not in tag, f"Invalid hashtag with space: {tag}"
        # Should only contain letters, digits, underscores after #
        assert re.match(r"^#[a-z0-9_]+$", tag, re.IGNORECASE), f"Invalid hashtag format: {tag}"


def test_calendar_hook_uniqueness(monkeypatch):
    """Ensure 30-day calendar has unique hooks (not repetitive)."""
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="calendar_hook_uniqueness")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    markdown = data.get("report_markdown", "")

    # Find 30-day calendar section - use exact heading format
    calendar_match = re.search(
        r"## \d+\.\s+30-Day Content Calendar\s*\n(.*?)(?=\n## |\Z)", markdown, re.DOTALL
    )

    calendar_content = calendar_match.group(1) if calendar_match else ""

    # Extract hooks from table - actual format: | Day | Platform | Hook | Bucket | CTA |
    lines = calendar_content.split("\n")
    hooks = []

    for line in lines:
        if (
            line.startswith("|") and line.count("|") >= 5
        ):  # At least 5 pipes for 6 columns (including edges)
            # Parse table row
            columns = [col.strip() for col in line.split("|")]
            # Hook is in column 3 (index 3), skip header and separator rows
            if (
                len(columns) > 3
                and columns[3]
                and "Hook" not in columns[3]
                and "---" not in columns[3]
            ):
                hooks.append(columns[3])

    # Validate uniqueness
    unique_hooks = set(hooks)
    uniqueness_ratio = len(unique_hooks) / len(hooks) if hooks else 0

    # At least 50% unique hooks (15+ out of 30)
    assert len(hooks) >= 20, f"Calendar should have at least 20 hooks, found {len(hooks)}"
    assert (
        uniqueness_ratio >= 0.5
    ), f"Calendar hooks too repetitive: {len(unique_hooks)}/{len(hooks)} unique ({uniqueness_ratio:.1%})"

    # At least 10 distinct hooks
    assert len(unique_hooks) >= 10, f"Only {len(unique_hooks)} unique hooks (expected 10+)"


def test_reasonable_sentence_length(monkeypatch):
    """Ensure no AI soup - sentences should be reasonable length."""
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="reasonable_sentence_length")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    markdown = data.get("report_markdown", "")

    # Check overview and final_summary sections (most prone to long sentences)
    sections_to_check = [
        (r"## .*[Oo]verview.*?\n(.*?)(?=\n## |$)", "Overview"),
        (r"## .*[Ff]inal.*[Ss]ummary.*?\n(.*?)(?=\n## |$)", "Final Summary"),
    ]

    for pattern, section_name in sections_to_check:
        match = re.search(pattern, markdown, re.DOTALL)
        if not match:
            continue

        section_content = match.group(1)

        # Split into sentences (simple approach: split on period + space)
        sentences = [s.strip() for s in re.split(r"\.\s+", section_content) if s.strip()]

        for sentence in sentences:
            word_count = len(sentence.split())
            # No sentence should exceed 80 words (slightly relaxed from 50)
            assert word_count <= 80, (
                f"Section '{section_name}' has sentence with {word_count} words (limit 80): "
                f"{sentence[:100]}..."
            )


def test_hashtag_normalization_function():
    """Test normalize_hashtag() function directly."""
    from backend.utils.text_cleanup import normalize_hashtag

    # Test cases
    test_cases = [
        ("Coffeehouse / Beverage Retail", "#coffeehousebeverageretail"),
        ("#Coffee Shop", "#coffeeshop"),
        ("coffee-lover", "#coffeelover"),
        ("SPECIALTY COFFEE", "#specialtycoffee"),
        ("", ""),
        ("   spaces   ", "#spaces"),
    ]

    for input_tag, expected in test_cases:
        result = normalize_hashtag(input_tag)
        assert (
            result == expected
        ), f"normalize_hashtag('{input_tag}') = '{result}', expected '{expected}'"


def test_content_buckets_in_calendar(monkeypatch):
    """Ensure calendar uses all content buckets (Education, Proof, Promo, Community)."""
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="content_buckets")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    markdown = data.get("report_markdown", "")

    # Find 30-day calendar section - use exact heading format
    calendar_match = re.search(
        r"## \d+\.\s+30-Day Content Calendar\s*\n(.*?)(?=\n## |\Z)", markdown, re.DOTALL
    )

    calendar_content = calendar_match.group(1) if calendar_match else ""

    # Check that all buckets appear in the calendar
    expected_buckets = ["Education", "Proof", "Promo", "Community"]

    for bucket in expected_buckets:
        assert bucket in calendar_content, f"Content bucket '{bucket}' not found in calendar"


def test_quick_social_section_count(monkeypatch):
    """Ensure Quick Social pack has correct number of core sections."""
    monkeypatch.setenv("AICMO_STUB_MODE", "1")

    payload = _make_quick_social_request(test_id="section_count")

    # Generate Quick Social report via HTTP endpoint
    response = client.post("/api/aicmo/generate_report", json=payload)
    assert response.status_code == 200, f"HTTP {response.status_code}: {response.text}"

    data = response.json()
    markdown = data.get("report_markdown", "")

    # Count ## numbered sections (main sections only, ignore sub-headings)
    section_headings = re.findall(r"^## \d+\. (.+)$", markdown, re.MULTILINE)

    # Verify we have exactly 8 main sections
    assert (
        len(section_headings) == 8
    ), f"Expected 8 numbered sections, found {len(section_headings)}: {section_headings}"

    # Verify key sections are present (fuzzy matching)
    found_sections = [h.lower() for h in section_headings]
    missing = []

    # Check for key Quick Social sections (use actual template naming)
    for expected in ["brand", "calendar", "hashtag", "summary"]:
        if not any(expected in found for found in found_sections):
            missing.append(expected)

    assert not missing, f"Missing expected sections: {missing}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-W", "ignore::DeprecationWarning"])
