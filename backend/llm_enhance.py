"""Unified LLM enhancement layer for AICMO.

Enhances generated content with:
1. Industry preset context (if provided)
2. Reference deck learning examples (always)
3. Structured master prompt with all context
4. Optional: LLM-based enhancement (returns stub for now)
"""

import json
from typing import Any, Dict, Optional, TYPE_CHECKING

from backend.learning_store import get_relevant_examples
from aicmo.presets.industry_presets import get_industry_preset

if TYPE_CHECKING:
    from backend.schemas import ClientIntakeForm


def enhance_with_llm(
    brief: "ClientIntakeForm",  # From backend.schemas
    stub_output: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Enhance stub output with industry context + learning examples.

    This is the single entry point for LLM enhancement. It:
    1. Fetches industry preset (if provided via options["industry_key"])
    2. Fetches learning examples: strategy_deck, campaign_blueprint, full_report
    3. Builds a master prompt with 4 sections
    4. TODO: Call actual LLM (for now returns stub unchanged)
    5. Returns enhanced output

    All operations are wrapped in try-except to ensure this never breaks the endpoint.

    Args:
        brief: ClientIntakeForm from the request
        stub_output: Base/stub output dict from generation
        options: Dict with optional keys like "industry_key", "use_claude", etc.

    Returns:
        Enhanced output dict (or stub if any operation fails)
    """
    try:
        options = options or {}

        # 1) Fetch industry preset (if provided)
        industry_preset = None
        industry_key = options.get("industry_key")
        if industry_key:
            try:
                industry_preset = get_industry_preset(industry_key)
            except Exception as e:
                print(f"[LLM Enhance] Warning: Could not load industry preset: {e}")

        # 2) Fetch learning examples
        learning_examples = {
            "strategy_deck": [],
            "campaign_blueprint": [],
            "full_report": [],
        }
        try:
            # Extract industry from brief (for relevance scoring)
            brief_industry = (
                getattr(brief.brand, "industry", None) if hasattr(brief, "brand") else None
            )
            brief_goal = (
                getattr(brief.goals, "primary_goal", None) if hasattr(brief, "goals") else None
            )

            for learning_type in learning_examples.keys():
                examples = get_relevant_examples(
                    learning_type=learning_type,
                    industry=brief_industry,
                    goal=brief_goal,
                    max_examples=3,
                )
                learning_examples[learning_type] = [
                    {
                        "source": ex.source_name,
                        "notes": ex.notes,
                        "text": ex.raw_text[:500],  # Truncate for prompt size
                    }
                    for ex in examples
                ]
        except Exception as e:
            print(f"[LLM Enhance] Warning: Could not load learning examples: {e}")

        # 3) Build master prompt (for future LLM calls)
        master_prompt_sections = []

        # [INDUSTRY PRESET CONTEXT]
        if industry_preset:
            preset_section = f"""[INDUSTRY PRESET CONTEXT]
Industry: {industry_preset.name}
Description: {industry_preset.description}

Strategy Notes:
{chr(10).join(f"- {note}" for note in industry_preset.strategy_notes)}

Priority Channels:
{', '.join(industry_preset.priority_channels)}

Key KPIs:
{', '.join(industry_preset.sample_kpis)}

Creative Angles:
{chr(10).join(f"- {angle}" for angle in industry_preset.creative_angles)}

Common Objections:
{chr(10).join(f"- {obj}" for obj in industry_preset.common_objections)}

Default Tone: {industry_preset.default_tone}
"""
            master_prompt_sections.append(preset_section)

        # [REFERENCE DECK EXAMPLES]
        if any(learning_examples.values()):
            examples_section = "[REFERENCE DECK EXAMPLES]\n\n"
            for learning_type, examples in learning_examples.items():
                if examples:
                    examples_section += f"### {learning_type.replace('_', ' ').title()}\n"
                    for i, ex in enumerate(examples, 1):
                        examples_section += f"\n**Example {i}** (Source: {ex['source']})\n"
                        if ex.get("notes"):
                            examples_section += f"Notes: {ex['notes']}\n"
                        examples_section += f"Content: {ex['text']}\n"
                    examples_section += "\n"
            master_prompt_sections.append(examples_section)

        # [CLIENT BRIEF]
        brief_section = "[CLIENT BRIEF]\n"
        brief_section += f"Brand: {getattr(brief.brand, 'name', 'Unknown')}\n"
        if hasattr(brief.brand, "industry"):
            brief_section += f"Industry: {brief.brand.industry}\n"
        if hasattr(brief, "goals"):
            brief_section += f"Primary Goal: {getattr(brief.goals, 'primary_goal', 'Unknown')}\n"
        if hasattr(brief, "target_audience"):
            brief_section += (
                f"Target Audience: {getattr(brief.target_audience, 'name', 'Unknown')}\n"
            )
        master_prompt_sections.append(brief_section)

        # [BASE/STUB OUTPUT]
        stub_section = "[BASE/STUB OUTPUT]\n"
        stub_section += json.dumps(stub_output, indent=2)
        master_prompt_sections.append(stub_section)

        # Store master prompt for debugging (optional)
        master_prompt = "\n\n".join(master_prompt_sections)
        print(f"[LLM Enhance] Master prompt built ({len(master_prompt)} chars)")

        # 4) TODO: Call actual LLM with master_prompt
        # For now, return stub unchanged while learning infrastructure is tested
        enhanced_output = stub_output.copy()

        return enhanced_output

    except Exception as e:
        # If anything goes wrong, log and return stub unchanged
        print(f"[LLM Enhance] Error during enhancement: {e}")
        return stub_output
