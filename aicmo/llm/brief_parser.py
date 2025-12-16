"""LLM-based brief parser for converting raw text to structured ClientInputBrief."""

from __future__ import annotations

import json
import os

from aicmo.io.client_reports import ClientInputBrief

try:
    from aicmo.presets.industry_presets import INDUSTRY_PRESETS
except ImportError:
    INDUSTRY_PRESETS = {}


def build_brief_with_llm(raw_text: str, industry_key: str | None = None) -> ClientInputBrief:
    """
    Converts client raw text brief → fully structured ClientInputBrief
    using OpenAI (gpt-4o-mini or any model you choose).

    Args:
        raw_text: Raw client brief text
        industry_key: Optional industry preset key for context

    Returns:
        ClientInputBrief: Fully structured brief object
    """
    from aicmo.core.llm.runtime import require_llm
    
    # Fail early with clear message if LLM not available
    require_llm()
    
    # Only import after we've verified LLM is available
    from openai import OpenAI
    
    model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")
    api_key = os.getenv("OPENAI_API_KEY", "")

    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    client = OpenAI(api_key=api_key)

    preset = INDUSTRY_PRESETS.get(industry_key) if industry_key else None

    preset_context = ""
    if preset:
        preset_context = f"""
[Industry preset context]
Name: {preset.name}
Strategy notes: {preset.strategy_notes}
Priority channels: {preset.priority_channels}
Common objections: {preset.common_objections}
"""

    # Get the JSON schema for ClientInputBrief
    schema = ClientInputBrief.model_json_schema()
    schema_json = json.dumps(schema, indent=2)

    prompt = f"""You are an expert senior marketing strategist at Ogilvy.

Your task: Convert raw client brief text into a structured JSON that fits
the ClientInputBrief Pydantic model EXACTLY.

ONLY output valid JSON. No markdown, no explanations, no code blocks.

[RAW CLIENT BRIEF]
{raw_text}

{preset_context}

[REQUIRED JSON SCHEMA]
{schema_json}

Produce valid JSON matching this schema exactly. Return ONLY the JSON object."""

    response = client.messages.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.7,
    )

    # Extract text from response
    response_text = response.content[0].text.strip()

    # Remove markdown code blocks if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    # Parse and validate
    try:
        return ClientInputBrief.model_validate_json(response_text)
    except Exception as e:
        raise ValueError(
            f"Failed to parse LLM response as ClientInputBrief: {e}\n\nResponse: {response_text}"
        )
