"""Framework fusion layer for agency-grade report enhancement.

This module provides inject_frameworks() which prepends structured strategy,
premium language, and creative context before the base draft.

Used in the main generation pipeline to layer strategy frameworks, thinking
sequences, reasoning patterns, and structure rules before the LLM output.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def structure_learning_context(raw_context: str) -> Dict[str, str]:
    """
    Parse raw learning context string and structure it into framework keys.

    This is a helper that maps retrieved blocks into the framework dict
    expected by inject_frameworks().

    Args:
        raw_context: Raw formatted text from memory.retrieve_relevant_context()

    Returns:
        Dict with keys: core_frameworks, thinking_sequences, reasoning_patterns,
                        structure_rules, premium_expressions, creative_hooks
    """
    # Placeholder: in production, you might parse sections or use LLM to categorize
    # For now, treat all context as frameworks
    if not raw_context:
        return {
            "core_frameworks": "",
            "thinking_sequences": "",
            "reasoning_patterns": "",
            "structure_rules": "",
            "premium_expressions": "",
            "creative_hooks": "",
        }

    return {
        "core_frameworks": raw_context,
        "thinking_sequences": "",
        "reasoning_patterns": "",
        "structure_rules": "",
        "premium_expressions": "",
        "creative_hooks": "",
    }


def inject_frameworks(
    brief: Dict[str, Any],
    base_draft: str,
    learning_context: Dict[str, str],
) -> str:
    """
    Prepend structured strategy + language + creative context before base draft.

    This is the main integration point for framework fusion. It constructs a
    header block from learning context and inserts it before the generated draft.

    Args:
        brief: Client brief dict (for context, may be used in future enhancements)
        base_draft: The base-generated report text
        learning_context: Dict with keys like 'core_frameworks', 'premium_expressions',
                         'creative_hooks', 'thinking_sequences', 'reasoning_patterns',
                         'structure_rules'

    Returns:
        Draft with injected framework headers prepended, or original if no context
    """
    if not learning_context:
        return base_draft

    core_frameworks = learning_context.get("core_frameworks", "").strip()
    thinking_sequences = learning_context.get("thinking_sequences", "").strip()
    reasoning_patterns = learning_context.get("reasoning_patterns", "").strip()
    structure_rules = learning_context.get("structure_rules", "").strip()
    premium_expressions = learning_context.get("premium_expressions", "").strip()
    creative_hooks = learning_context.get("creative_hooks", "").strip()

    header_blocks = []

    if core_frameworks or thinking_sequences or reasoning_patterns or structure_rules:
        framework_section = "\n\n".join(
            [
                core_frameworks,
                thinking_sequences,
                reasoning_patterns,
                structure_rules,
            ]
        )
        framework_section = "\n".join(
            [line for line in framework_section.split("\n") if line.strip()]
        )
        if framework_section:
            header_blocks.append(
                "### STRATEGY FOUNDATION (AUTO-INJECTED FROM LEARNING)\n\n" + framework_section
            )

    if premium_expressions:
        header_blocks.append(
            "### PREMIUM LANGUAGE PACK (AUTO-INJECTED FROM LEARNING)\n\n" + premium_expressions
        )

    if creative_hooks:
        header_blocks.append(
            "### CREATIVE LIBRARY (AUTO-INJECTED FROM LEARNING)\n\n" + creative_hooks
        )

    header = "\n\n---\n\n".join([b for b in header_blocks if b.strip()])
    if not header:
        logger.debug("No frameworks to inject, returning base draft")
        return base_draft

    logger.info(f"Injected {len(header_blocks)} framework sections before base draft")
    return f"{header}\n\n---\n\n{base_draft}"


def build_wow_fields(
    brief_data: Dict[str, Any],
    learning_context: str,
) -> Dict[str, str]:
    """
    Build strategic foundation fields for WOW template placeholders.

    Given a brief and learning context, construct values for:
    - {{strategic_foundation}}
    - {{brand_narrative}}
    - {{messaging_pillars}}
    - {{creative_territories}}
    - {{positioning_model}}
    - {{framework_applied}}

    Args:
        brief_data: Client brief as dict
        learning_context: Raw learning context string

    Returns:
        Dict with string values for each WOW placeholder
    """
    brand_name = brief_data.get("brand", {}).get("brand_name", "Your Brand")

    return {
        "strategic_foundation": (
            "Strategic approach informed by best-in-class agency practices "
            "and learned from past successful campaigns."
        ),
        "brand_narrative": f"{brand_name}'s unique market position and messaging foundation.",
        "messaging_pillars": "Three core messages that resonate with your ideal customer.",
        "creative_territories": "Visual and tonal directions that differentiate your brand.",
        "positioning_model": f"{brand_name}'s competitive positioning and value proposition.",
        "framework_applied": (
            "Agency-grade strategic frameworks applied to ensure professional, "
            "results-driven marketing approach."
        ),
    }
