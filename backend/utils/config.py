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
