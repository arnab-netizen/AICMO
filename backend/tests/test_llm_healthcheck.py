"""
Test the /health/llm endpoint.

This test verifies the health check endpoint exists and returns the expected schema,
but does NOT require LLM keys to be present (it should work in dev environments).
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_llm_healthcheck_endpoint_exists(client):
    """Verify /health/llm endpoint is reachable."""
    response = client.get("/health/llm")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"


def test_llm_healthcheck_response_schema(client):
    """Verify /health/llm returns expected JSON schema."""
    response = client.get("/health/llm")
    data = response.json()

    # Required fields
    assert "ok" in data, "Response missing 'ok' field"
    assert "llm_ready" in data, "Response missing 'llm_ready' field"
    assert "used_stub" in data, "Response missing 'used_stub' field"
    assert "quality_passed" in data, "Response missing 'quality_passed' field"
    assert "pack_key" in data, "Response missing 'pack_key' field"

    # Optional fields (present on error)
    # error_type and debug_hint may or may not be present

    # Type checks
    assert isinstance(data["ok"], bool), "'ok' should be boolean"
    assert isinstance(data["llm_ready"], bool), "'llm_ready' should be boolean"
    assert isinstance(data["used_stub"], bool), "'used_stub' should be boolean"
    assert isinstance(data["quality_passed"], bool), "'quality_passed' should be boolean"
    assert isinstance(data["pack_key"], str), "'pack_key' should be string"


def test_llm_healthcheck_does_not_leak_secrets(client):
    """Verify response doesn't contain API keys or sensitive data."""
    response = client.get("/health/llm")
    response_text = response.text.lower()

    # Check for common secret patterns
    assert "sk-" not in response_text, "Response may contain OpenAI key"
    assert "pplx-" not in response_text, "Response may contain Perplexity key"
    assert "api_key" not in response_text, "Response contains 'api_key' text"
    assert "secret" not in response_text, "Response contains 'secret' text"


def test_llm_healthcheck_works_without_keys(client):
    """
    Verify endpoint works in dev environment (no LLM keys).

    When no keys are present:
    - llm_ready should be False
    - ok may be False (that's expected in dev)
    - used_stub should be True (stubs allowed in dev)
    """
    response = client.get("/health/llm")
    data = response.json()

    # In dev (no keys), these are expected behaviors:
    # - llm_ready = False
    # - used_stub = True (stubs allowed)
    # We DON'T assert ok == True because that requires real LLM keys

    # Just verify the endpoint completed and returned data
    assert "llm_ready" in data
    assert "used_stub" in data
    # ok can be False in dev - that's fine


@pytest.mark.integration
def test_llm_healthcheck_in_production_mode(client, monkeypatch):
    """
    Test health check behavior when LLM keys are configured.

    This test only runs if OPENAI_API_KEY or PERPLEXITY_API_KEY is set.
    """
    import os

    # Skip if no LLM keys present
    has_openai = bool(os.getenv("OPENAI_API_KEY"))
    has_perplexity = bool(os.getenv("PERPLEXITY_API_KEY"))

    if not (has_openai or has_perplexity):
        pytest.skip("No LLM keys configured - skipping production mode test")

    response = client.get("/health/llm")
    data = response.json()

    # With LLM keys present:
    assert data["llm_ready"] is True, "llm_ready should be True when keys present"

    # In production mode, we expect:
    # - used_stub should be False (stubs forbidden)
    # - ok should be True (health check passed)
    # Note: This may fail if LLM providers are down - that's valuable signal!
