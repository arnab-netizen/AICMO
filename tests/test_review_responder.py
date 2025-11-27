"""Tests for review responder module."""

import pytest


def test_parse_raw_reviews_single_review():
    """Test parsing a single review."""
    from backend.generators.reviews.review_responder import parse_raw_reviews

    raw = "The coffee was cold."
    result = parse_raw_reviews(raw)

    assert len(result) == 1
    assert result[0] == "The coffee was cold."


def test_parse_raw_reviews_multiline():
    """Test parsing multiple reviews with newlines."""
    from backend.generators.reviews.review_responder import parse_raw_reviews

    raw = "The coffee was cold.\nService was slow.\nWaited 30 minutes."
    result = parse_raw_reviews(raw)

    assert len(result) == 3
    assert "The coffee was cold." in result
    assert "Service was slow." in result
    assert "Waited 30 minutes." in result


def test_parse_raw_reviews_blank_lines():
    """Test parsing reviews with blank lines."""
    from backend.generators.reviews.review_responder import parse_raw_reviews

    raw = """The coffee was cold.

Service was slow.

Staff was rude."""
    result = parse_raw_reviews(raw)

    assert len(result) == 3
    assert all(review for review in result)  # No empty strings


def test_parse_raw_reviews_duplicates():
    """Test that duplicates are removed."""
    from backend.generators.reviews.review_responder import parse_raw_reviews

    raw = "Bad service.\nBad service.\nNo coffee."
    result = parse_raw_reviews(raw)

    assert len(result) == 2
    assert result.count("Bad service.") == 1


def test_parse_raw_reviews_empty():
    """Test parsing empty input."""
    from backend.generators.reviews.review_responder import parse_raw_reviews

    result = parse_raw_reviews("")
    assert result == []


def test_generate_review_responses_schema():
    """Test that review responder creates proper schema."""
    from backend.generators.reviews.review_responder import generate_review_responses

    brand = "Test Cafe"
    raw = "The coffee was cold.\nService was slow."

    result = generate_review_responses(brand, raw)

    assert "review_responses" in result
    responses = result["review_responses"]
    assert len(responses) == 2

    # Check schema of each response
    for resp in responses:
        assert "review" in resp
        assert "response" in resp
        assert isinstance(resp["review"], str)
        assert isinstance(resp["response"], str)


def test_generate_review_responses_empty():
    """Test review responder with no reviews."""
    from backend.generators.reviews.review_responder import generate_review_responses

    result = generate_review_responses("Test Brand", "")

    assert "review_responses" in result
    assert result["review_responses"] == []


def test_generate_review_responses_review_field():
    """Test that each review is correctly extracted."""
    from backend.generators.reviews.review_responder import generate_review_responses

    raw = "Coffee was cold.\nWait time too long."
    result = generate_review_responses("Cafe", raw)

    reviews = [r["review"] for r in result["review_responses"]]
    assert "Coffee was cold." in reviews
    assert "Wait time too long." in reviews


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
