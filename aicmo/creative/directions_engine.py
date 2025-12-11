"""Creative directions generation using OpenAI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, List, Optional

from openai import OpenAI


@dataclass
class CreativeDirection:
    """A single creative direction (territory) for a campaign."""

    name: str
    tagline: str
    description: str
    visual_style: str
    color_directions: str
    tone_voice: str
    messaging_pillars: List[str]
    example_hooks: List[str]
    example_post_ideas: List[str]


def generate_creative_directions(
    *,
    brief: Any,
    report: Any,
    competitor_stats: Optional[List[dict]] = None,
    model: str = "gpt-4o-mini",
) -> List[CreativeDirection]:
    """
    Generate 3 creative directions using OpenAI.

    Args:
        brief: ClientInputBrief object or dict with campaign info
        report: AICMOOutputReport or dict with generated report
        competitor_stats: Optional list of competitor analysis dicts
        model: OpenAI model to use (gpt-4o-mini, gpt-4.1, gpt-4.1-mini)

    Returns:
        List of 3 CreativeDirection objects
    """
    # Import LLM router (Phase 8.4)
    from aicmo.llm.router import get_llm_client, LLMUseCase
    import asyncio

    # Extract key info from brief
    brief_text = ""
    if hasattr(brief, "goal"):
        brief_text += f"Primary goal: {brief.goal.primary_goal}\n"
    if hasattr(brief, "brand"):
        brief_text += f"Brand: {brief.brand.brand_name}\n"
        if hasattr(brief.brand, "brand_adjectives"):
            brief_text += f"Brand adjectives: {', '.join(brief.brand.brand_adjectives)}\n"
    if hasattr(brief, "audience"):
        brief_text += f"Primary audience: {brief.audience.primary_customer}\n"

    # Add competitor context if available
    competitor_context = ""
    if competitor_stats:
        competitor_context = "\n\nCompetitor insights:\n"
        for comp in competitor_stats:
            name = comp.get("competitor", "Unknown")
            style = comp.get("style_note", "")
            competitor_context += f"- {name}: {style}\n"

    prompt = f"""Generate 3 distinct creative territories for this marketing campaign:

{brief_text}{competitor_context}

For each direction, provide a JSON object with these exact fields:
- name: string (e.g., "Bold & Disruptive")
- tagline: string (short phrase, e.g., "Break conventions, grab attention")
- description: string (2-3 sentences about this direction)
- visual_style: string (design approach, colors, imagery style)
- color_directions: string (recommended color palette)
- tone_voice: string (how the brand speaks)
- messaging_pillars: array of 3-4 key messages
- example_hooks: array of 3-4 content hooks/angles
- example_post_ideas: array of 3-4 specific post concepts

Return a JSON array with exactly 3 direction objects. Example format:
[
  {{
    "name": "Direction 1",
    "tagline": "...",
    "description": "...",
    "visual_style": "...",
    "color_directions": "...",
    "tone_voice": "...",
    "messaging_pillars": ["...", "...", "..."],
    "example_hooks": ["...", "...", "..."],
    "example_post_ideas": ["...", "...", "..."]
  }},
  ...
]

Generate ONLY the JSON array, no other text."""

    try:
        # Get LLM client for CREATIVE_SPEC use-case
        chain = get_llm_client(
            use_case=LLMUseCase.CREATIVE_SPEC,
            profile_override=None,
            deep_research=False,
            multimodal=False
        )

        # Call the chain via ProviderChain.invoke
        success, result, provider_name = asyncio.run(
            chain.invoke(
                "generate",
                prompt=prompt
            )
        )

        if not success or not result:
            raise Exception(f"LLM returned failure via {provider_name}")

        # Extract response text
        text = result if isinstance(result, str) else result.get("content", "")
        text = text.strip()

        # Parse JSON response
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0].strip()
            elif "```" in text:
                text = text.split("```")[1].split("```")[0].strip()
            data = json.loads(text)

        # Convert to CreativeDirection objects
        directions = []
        for item in data:
            try:
                direction = CreativeDirection(
                    name=item.get("name", "Untitled"),
                    tagline=item.get("tagline", ""),
                    description=item.get("description", ""),
                    visual_style=item.get("visual_style", ""),
                    color_directions=item.get("color_directions", ""),
                    tone_voice=item.get("tone_voice", ""),
                    messaging_pillars=item.get("messaging_pillars", []),
                    example_hooks=item.get("example_hooks", []),
                    example_post_ideas=item.get("example_post_ideas", []),
                )
                directions.append(direction)
            except Exception:
                # Skip malformed items
                continue

        # Ensure we have exactly 3
        while len(directions) < 3:
            directions.append(
                CreativeDirection(
                    name=f"Direction {len(directions) + 1}",
                    tagline="",
                    description="",
                    visual_style="",
                    color_directions="",
                    tone_voice="",
                    messaging_pillars=[],
                    example_hooks=[],
                    example_post_ideas=[],
                )
            )

        return directions[:3]

    except Exception as e:
        raise ValueError(f"Failed to generate creative directions: {e}")
