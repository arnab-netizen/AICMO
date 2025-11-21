"""Dependency injection for FastAPI backend."""

import os

from backend.services.llm_client import LLMClient


def get_llm() -> LLMClient:
    """Get LLM client instance with configured API key and model."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    model = os.getenv("AICMO_MODEL_MAIN", "gpt-4o-mini")
    return LLMClient(api_key=api_key, model=model)
