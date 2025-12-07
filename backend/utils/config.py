"""
Configuration utilities for AICMO runtime behavior.
"""

from __future__ import annotations

import os


def is_stub_mode() -> bool:
    """
    Return True if AICMO should generate deterministic stub content
    instead of calling the LLM.

    Rules:
    - If AICMO_STUB_MODE=1 → always stub.
    - Else, if OPENAI_API_KEY is missing/empty → stub.
    - Else → normal LLM mode.

    This allows tests and CI to run without API keys while still
    enforcing benchmark compliance on generated content.
    """
    if os.getenv("AICMO_STUB_MODE") == "1":
        return True
    api_key = os.getenv("OPENAI_API_KEY") or ""
    return not bool(api_key.strip())


def allow_stubs_in_production() -> bool:
    """
    Return True if stub content is allowed when LLM is unavailable.

    Rules:
    - If production LLM keys exist (OpenAI, Anthropic, or Perplexity) → stubs NOT allowed (default)
    - If AICMO_ALLOW_STUBS explicitly set to "true" → stubs allowed (override)
    - If AICMO_ALLOW_STUBS explicitly set to "false" → stubs NOT allowed
    - If no production keys and AICMO_ALLOW_STUBS not set → stubs allowed (dev/local default)

    When stubs are not allowed and LLM is unavailable:
    - API should return structured error instead of generating stub content
    - This prevents silent stub usage in production client work
    """
    allow_stubs_env = os.getenv("AICMO_ALLOW_STUBS", "").lower()

    # Explicit override: user explicitly set the value
    if allow_stubs_env == "true":
        return True
    if allow_stubs_env == "false":
        return False

    # Auto-detect: if production LLM keys exist, stubs NOT allowed by default
    if is_production_llm_ready():
        return False

    # Default for dev/local without LLM keys: allow stubs
    return True


def allow_stubs_in_current_env() -> bool:
    """
    Alias for allow_stubs_in_production() for semantic clarity.

    Returns True if stub content generation is permitted in the current environment.
    Returns False in production environments where LLM keys are configured.
    """
    return allow_stubs_in_production()


def has_llm_configured() -> bool:
    """
    Return True if at least one LLM provider API key is configured.

    Checks for:
    - OPENAI_API_KEY
    - ANTHROPIC_API_KEY
    """
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    return bool(openai_key or anthropic_key)


def is_production_llm_ready() -> bool:
    """
    Return True if ANY real LLM key is present in environment variables.

    Checks for production-ready LLM providers:
    - OPENAI_API_KEY (and optional OPENAI_API_BASE)
    - ANTHROPIC_API_KEY
    - PERPLEXITY_API_KEY

    This is used to determine if production should NEVER use stub content.
    When any of these keys exist, the system has real LLM capability available.
    """
    openai_key = os.getenv("OPENAI_API_KEY", "").strip()
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
    perplexity_key = os.getenv("PERPLEXITY_API_KEY", "").strip()

    return bool(openai_key or anthropic_key or perplexity_key)
