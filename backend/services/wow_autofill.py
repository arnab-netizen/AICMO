"""
WOW Auto-Fill Service

Auto-generates captions, reels, hashtags, calendars, competitor insights,
email sequences, landing pages and directly pipes them into WOW placeholders.

This service bridges the gap between generators and WOW template placeholders,
allowing seamless integration of real generated content into the template system.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import os

from aicmo.llm.client import _get_llm_provider, _get_claude_client, _get_openai_client


def _run_llm(prompt: str, max_tokens: int = 1000) -> str:
    """
    Run an LLM prompt using the configured provider (Claude or OpenAI).

    Args:
        prompt: The prompt to send to the LLM
        max_tokens: Maximum tokens in response

    Returns:
        The LLM response text
    """
    provider = _get_llm_provider()

    try:
        if provider == "claude":
            client = _get_claude_client()
            model = os.getenv("AICMO_CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text.strip()
        else:
            client = _get_openai_client()
            model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=0.7,
            )
            return response.choices[0].message.content.strip()
    except Exception as e:
        # Graceful fallback if LLM fails
        return f"[Auto-fill failed: {str(e)}]"


def generate_captions(brief: Dict[str, Any], count: int = 10) -> str:
    """
    Generate engaging social media captions.

    Args:
        brief: Client brief with business details
        count: Number of captions to generate

    Returns:
        Captions separated by newlines
    """
    prompt = f"""
Generate {count} engaging social media captions for a brand:

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Audience: {brief.get('target_audience', 'N/A')}
Tone: {brief.get('brand_tone', 'professional')}

Return each caption on a new line, without numbering.
Captions should be 50-100 characters each.
Mix emotional, educational, and promotional angles.
""".strip()

    return _run_llm(prompt, max_tokens=600)


def generate_reels(brief: Dict[str, Any], count: int = 5) -> str:
    """
    Generate Instagram Reel content ideas with hook + script + shotlist.

    Args:
        brief: Client brief with business details
        count: Number of reel ideas to generate

    Returns:
        Reel concepts with scripts
    """
    prompt = f"""
Generate {count} Instagram Reel content ideas with hook, script, and shotlist.

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Audience: {brief.get('target_audience', 'N/A')}
Tone: {brief.get('brand_tone', 'professional')}

Format each reel as:
**Reel [N]: [Concept Title]**
Hook: [Opening 3-5 seconds]
Script: [Full reel script]
Shots: [Key visual moments]
---
""".strip()

    return _run_llm(prompt, max_tokens=1500)


def generate_hashtag_bank(brief: Dict[str, Any], count: int = 40) -> Dict[str, str]:
    """
    Generate relevant hashtags grouped into categories.

    Args:
        brief: Client brief with business details
        count: Total number of hashtags to generate

    Returns:
        Dictionary with hashtag groups
    """
    prompt = f"""
Generate {count} relevant hashtags grouped into these categories:
- Location ({count//4} hashtags)
- Audience & Lifestyle ({count//4} hashtags)
- Product / Service ({count//4} hashtags)
- Trending / Occasion ({count//4} hashtags)

Business: {brief.get('brand_name', 'N/A')}
Location: {brief.get('city', 'N/A')}
Category: {brief.get('category', 'N/A')}

Return as:

**Location Hashtags**
#hashtag1 #hashtag2 ...

**Audience Hashtags**
#hashtag1 #hashtag2 ...

**Product Hashtags**
#hashtag1 #hashtag2 ...

**Trending Hashtags**
#hashtag1 #hashtag2 ...
""".strip()

    result = _run_llm(prompt, max_tokens=800)

    # Parse result into groups (simple approach)
    groups = result.split("**")
    parsed = {
        "hashtags_location": "",
        "hashtags_audience": "",
        "hashtags_product": "",
        "hashtags_trend": "",
    }

    # Best-effort parsing
    if len(groups) > 2:
        parsed["hashtags_location"] = groups[2].replace("Location Hashtags", "").strip()
    if len(groups) > 4:
        parsed["hashtags_audience"] = groups[4].replace("Audience Hashtags", "").strip()
    if len(groups) > 6:
        parsed["hashtags_product"] = groups[6].replace("Product Hashtags", "").strip()
    if len(groups) > 8:
        parsed["hashtags_trend"] = groups[8].replace("Trending Hashtags", "").strip()

    return parsed


def generate_14_day_calendar(brief: Dict[str, Any]) -> str:
    """
    Generate a 14-day content calendar as markdown table.

    Args:
        brief: Client brief with business details

    Returns:
        Markdown table with content calendar
    """
    prompt = f"""
Generate a 14-day content calendar (markdown table) with these columns:
- Day (1-14)
- Post Type (Carousel, Reel, Story, Single Image)
- Idea
- CTA (Call-to-Action)
- Hashtag Focus

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Primary Channel: {brief.get('primary_channel', 'Instagram')}

Output ONLY the markdown table, no other text.
""".strip()

    return _run_llm(prompt, max_tokens=1200)


def generate_30_day_calendar(brief: Dict[str, Any]) -> str:
    """
    Generate a 30-day content calendar as markdown table.

    Args:
        brief: Client brief with business details

    Returns:
        Markdown table with content calendar
    """
    prompt = f"""
Generate a 30-day content calendar (markdown table) with these columns:
- Day (1-30)
- Content Format (Carousel, Reel, Story, Single, Highlight)
- Purpose (Awareness, Engagement, Conversion, Community)
- Caption Hook (5-10 words)
- CTA

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Primary Channel: {brief.get('primary_channel', 'Instagram')}

Output ONLY the markdown table, no other text.
""".strip()

    return _run_llm(prompt, max_tokens=2000)


def generate_competitor_block(brief: Dict[str, Any], count: int = 3) -> str:
    """
    Analyze competitors and generate comparison block.

    Args:
        brief: Client brief with business details
        count: Number of competitors to analyze

    Returns:
        Markdown comparison table
    """
    prompt = f"""
Analyze {count} competitor businesses and create a markdown comparison table.

Category: {brief.get('category', 'N/A')}
Location: {brief.get('city', 'N/A')}
Target Market: {brief.get('target_audience', 'N/A')}

Create a table with these columns:
- Competitor Name
- Strengths
- Weaknesses
- Content Style
- Opportunities for Client

Output ONLY the markdown table, no other text.
Focus on actionable, specific insights.
""".strip()

    return _run_llm(prompt, max_tokens=1200)


def generate_email_sequence(brief: Dict[str, Any], seq_type: str = "Welcome") -> str:
    """
    Generate email sequence (3-5 emails).

    Args:
        brief: Client brief with business details
        seq_type: Type of sequence (Welcome, Conversion, Winback, etc.)

    Returns:
        Email sequence with subject lines and body copy
    """
    prompt = f"""
Generate a {seq_type} email sequence with 3-5 emails.

For each email provide:
**Email [N]: [Subject Line]**
[Body copy - 2-3 paragraphs]
[CTA Button]

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Target Audience: {brief.get('target_audience', 'N/A')}
Tone: {brief.get('brand_tone', 'professional')}

Sequence Type: {seq_type}
Spacing: 2-3 days between emails
""".strip()

    return _run_llm(prompt, max_tokens=1500)


def generate_landing_page_wireframe(brief: Dict[str, Any]) -> str:
    """
    Create a landing page wireframe using markdown sections.

    Args:
        brief: Client brief with business details

    Returns:
        Markdown wireframe with sections
    """
    prompt = f"""
Create a landing page wireframe in markdown with these sections:
- Hero (headline + subheadline + CTA)
- Value Proposition (3 key benefits)
- Social Proof (testimonials / stats)
- Features / Benefits (3-5 points)
- Offer Breakdown (what they get)
- Pricing (if applicable)
- Final CTA

Business: {brief.get('brand_name', 'N/A')}
Category: {brief.get('category', 'N/A')}
Target Audience: {brief.get('target_audience', 'N/A')}
Primary Offer: {brief.get('offer_name', 'Service/Product')}

Output as markdown with clear section headings.
Include estimated copy length for each section.
""".strip()

    return _run_llm(prompt, max_tokens=1500)


def auto_fill_wow_blocks(
    brief: Dict[str, Any],
    wow_rules: Dict[str, Any],
    base_blocks: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generate all required blocks according to WOW rules.
    Only generates what is missing.

    Args:
        brief: Client brief with business details
        wow_rules: WOW package rules (min_captions, min_reels, etc.)
        base_blocks: Pre-generated blocks (optional, fills gaps)

    Returns:
        Dictionary of generated blocks ready for WOW template
    """
    base_blocks = base_blocks or {}
    blocks: Dict[str, Any] = {}

    # Generate captions if not present
    if "sample_captions_block" not in base_blocks:
        min_captions = wow_rules.get("min_captions", 10)
        blocks["sample_captions_block"] = generate_captions(brief, min_captions)
    else:
        blocks["sample_captions_block"] = base_blocks["sample_captions_block"]

    # Generate reel ideas if not present
    if "reel_ideas_block" not in base_blocks:
        min_reels = wow_rules.get("min_reel_ideas", 5)
        blocks["reel_ideas_block"] = generate_reels(brief, min_reels)
    else:
        blocks["reel_ideas_block"] = base_blocks["reel_ideas_block"]

    # Generate hashtag bank if not present
    if all(
        k not in base_blocks
        for k in [
            "hashtags_location",
            "hashtags_audience",
            "hashtags_product",
            "hashtags_trend",
        ]
    ):
        hashtag_groups = generate_hashtag_bank(brief, 40)
        blocks.update(hashtag_groups)
    else:
        for key in [
            "hashtags_location",
            "hashtags_audience",
            "hashtags_product",
            "hashtags_trend",
        ]:
            if key in base_blocks:
                blocks[key] = base_blocks[key]

    # Generate content calendar if not present
    calendar_key = (
        "calendar_14_day_table"
        if wow_rules.get("min_days_in_calendar", 14) == 14
        else "calendar_30_day_table"
    )
    if calendar_key not in base_blocks:
        if wow_rules.get("min_days_in_calendar", 14) == 14:
            blocks["calendar_14_day_table"] = generate_14_day_calendar(brief)
        else:
            blocks["calendar_30_day_table"] = generate_30_day_calendar(brief)
    else:
        blocks[calendar_key] = base_blocks[calendar_key]

    # Generate competitor benchmark if required
    if wow_rules.get("require_competitor_benchmark"):
        if "competitor_benchmark_block" not in base_blocks:
            blocks["competitor_benchmark_block"] = generate_competitor_block(brief)
        else:
            blocks["competitor_benchmark_block"] = base_blocks["competitor_benchmark_block"]

    # Generate email sequences if required
    if wow_rules.get("min_email_sequences"):
        email_sequences = [
            ("welcome_sequence_block", "Welcome"),
            ("conversion_sequence_block", "Conversion"),
            ("winback_sequence_block", "Winback"),
        ]
        for key, seq_type in email_sequences:
            if key not in base_blocks:
                blocks[key] = generate_email_sequence(brief, seq_type)
            else:
                blocks[key] = base_blocks[key]

    # Generate landing page wireframe if required
    if wow_rules.get("require_landing_wireframe"):
        if "landing_page_wireframe_block" not in base_blocks:
            blocks["landing_page_wireframe_block"] = generate_landing_page_wireframe(brief)
        else:
            blocks["landing_page_wireframe_block"] = base_blocks["landing_page_wireframe_block"]

    return blocks
