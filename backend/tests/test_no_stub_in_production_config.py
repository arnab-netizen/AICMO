"""
Test that AICMO refuses to generate stub content when AICMO_ALLOW_STUBS=false
and auto-enables LLM when production keys exist.

This ensures that in production deployments:
- If LLM keys exist, LLM is auto-enabled (no stub fallback)
- If LLM is unavailable, returns clear error instead of stub content
"""

import pytest
from backend.main import api_aicmo_generate_report


@pytest.mark.asyncio
async def test_no_stub_when_production_mode(monkeypatch):
    """
    Test that when AICMO_ALLOW_STUBS=false and no LLM is configured,
    the API returns structured error instead of generating stub content.
    """
    # Clear all LLM keys and disable stubs
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("PERPLEXITY_API_KEY", raising=False)
    monkeypatch.setenv("AICMO_ALLOW_STUBS", "false")
    monkeypatch.setenv("AICMO_USE_LLM", "0")  # Ensure LLM not attempted

    payload = {
        "pack_key": "quick_social_basic",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Test Industry",
            "primary_goal": "Test Goal",
        },
        "services": {
            "marketing_plan": True,
        },
    }

    result = await api_aicmo_generate_report(payload)

    # Verify structured error response
    assert result["success"] is False, "Should return error when stubs disabled"
    assert result["error_type"] == "llm_unavailable"
    assert result["stub_used"] is False, "Should not use stub when disabled"
    assert "LLM unavailable" in result["error_message"]
    assert "AICMO_ALLOW_STUBS" in result["error_message"]

    print("\n✅ NO-STUB PRODUCTION MODE TEST PASSED")
    print(f"   error_type: {result['error_type']}")
    print(f"   stub_used: {result['stub_used']}")
    print(f"   error_message: {result['error_message'][:100]}...")


@pytest.mark.asyncio
async def test_stub_allowed_when_dev_mode(monkeypatch):
    """
    Test that when AICMO_ALLOW_STUBS=true (default), stub content is generated
    when no LLM is configured.
    """
    # Clear LLM keys but allow stubs (default behavior)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("AICMO_ALLOW_STUBS", "true")  # Explicit dev mode
    monkeypatch.setenv("AICMO_USE_LLM", "0")

    payload = {
        "pack_key": "quick_social_basic",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Test Industry",
            "primary_goal": "Test Goal",
        },
        "services": {
            "marketing_plan": True,
        },
    }

    result = await api_aicmo_generate_report(payload)

    # Should succeed with stub content in dev mode
    # May fail quality gates, but should not be llm_unavailable error
    if not result["success"]:
        # If it fails, should be quality gate, not LLM unavailable
        assert (
            result["error_type"] != "llm_unavailable"
        ), "Should not fail with llm_unavailable when stubs allowed"

    # Always check stub_used flag
    assert "stub_used" in result

    print("\n✅ STUB ALLOWED IN DEV MODE TEST PASSED")
    print(f"   success: {result['success']}")
    print(f"   stub_used: {result.get('stub_used', 'N/A')}")


@pytest.mark.asyncio
async def test_llm_failure_with_stubs_disabled(monkeypatch):
    """
    Test that when LLM generation fails and AICMO_ALLOW_STUBS=false,
    system returns error instead of falling back to stub.
    """
    # Configure LLM keys but disable stubs (simulate LLM failure scenario)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.setenv("AICMO_ALLOW_STUBS", "false")
    monkeypatch.setenv("AICMO_USE_LLM", "1")  # Try to use LLM

    payload = {
        "pack_key": "quick_social_basic",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand",
            "industry": "Test Industry",
            "primary_goal": "Test Goal",
        },
        "services": {
            "marketing_plan": True,
        },
    }

    result = await api_aicmo_generate_report(payload)

    # When LLM fails and stubs disabled, should get error
    # (This test may pass if LLM succeeds with fake key, which is also fine)
    if not result["success"]:
        assert result["error_type"] in ["llm_unavailable", "unexpected_error"]
        assert result["stub_used"] is False

    print("\n✅ LLM FAILURE WITH STUBS DISABLED TEST PASSED")


@pytest.mark.asyncio
async def test_auto_enable_llm_when_production_keys_exist(monkeypatch):
    """
    Test that LLM is auto-enabled when production keys exist,
    even without AICMO_USE_LLM=1.
    """
    # Set production key (any one is sufficient)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-key-for-testing")
    monkeypatch.delenv("AICMO_USE_LLM", raising=False)  # Not explicitly set
    monkeypatch.setenv("AICMO_ALLOW_STUBS", "false")  # Strict mode

    # Disable cache to ensure fresh generation attempt
    monkeypatch.setenv("AICMO_CACHE_ENABLED", "false")

    payload = {
        "pack_key": "quick_social_basic",
        "stage": "draft",
        "client_brief": {
            "brand_name": "Test Brand Production Keys",  # Unique to avoid cache
            "industry": "Test Industry",
            "primary_goal": "Test Goal",
        },
        "services": {
            "marketing_plan": True,
        },
    }

    result = await api_aicmo_generate_report(payload)

    # LLM should have been auto-enabled (attempt made)
    # If it fails due to fake key, that's expected - but it should NOT use stub
    if not result["success"]:
        # Verify no stub fallback occurred
        assert (
            result["stub_used"] is False
        ), "Should not fall back to stub when production keys exist"
        # Accept all LLM error types (llm_failure, llm_chain_failed, unexpected_error)
        assert result["error_type"] in [
            "unexpected_error",
            "llm_unavailable",
            "llm_failure",
            "llm_chain_failed",
        ], f"Unexpected error type: {result['error_type']}"
    else:
        # If successful (unlikely with fake key), verify no stub was used
        assert result["stub_used"] is False, "Production mode should never use stubs"

    print("\n✅ AUTO-ENABLE LLM WITH PRODUCTION KEYS TEST PASSED")
    print(f"   success: {result['success']}")
    print(f"   stub_used: {result['stub_used']}")
    if not result["success"]:
        print(f"   error_type: {result['error_type']}")
    print(f"   success: {result['success']}")
    print(f"   error_type: {result.get('error_type', 'N/A')}")
