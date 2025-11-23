"""
Social Calendar hooks generator: brief-driven, LLM-capable, with safe stub fallback.

Replaces "Hook idea for day X" with dynamic, channel-aware hooks based on brief context.
"""

import json
import logging
import os
from datetime import date, timedelta
from typing import List, Optional

from aicmo.io.client_reports import ClientInputBrief, CalendarPostView

logger = logging.getLogger(__name__)


def generate_social_calendar(
    brief: ClientInputBrief,
    start_date: Optional[date] = None,
    days: int = 7,
    max_platforms_per_day: int = 1,
) -> List[CalendarPostView]:
    """
    Generate brief-specific Social Calendar posts with hooks and CTAs.

    Automatically selects stub or LLM mode based on AICMO_USE_LLM.
    Always returns a non-empty list of CalendarPostView (graceful degradation).

    Args:
        brief: ClientInputBrief with brand, audience, goals, platforms, etc.
        start_date: Start date for calendar (defaults to today)
        days: Number of days to generate (default 7)
        max_platforms_per_day: Max platforms per day (default 1)

    Returns:
        List[CalendarPostView] with post data (never empty, never throws)
    """
    try:
        if start_date is None:
            from datetime import datetime

            start_date = datetime.now().date()

        use_llm = os.environ.get("AICMO_USE_LLM", "0").lower() in ["1", "true", "yes"]

        # Get base themes and platforms
        themes = _get_themes(days)
        platforms = _get_platforms(brief)

        if use_llm:
            llm_posts = _generate_social_calendar_with_llm(
                brief, start_date, days, themes, platforms
            )
            if llm_posts:
                return llm_posts

        # Fall back to stub if LLM disabled or errored
        return _stub_social_calendar(brief, start_date, days, themes, platforms)

    except Exception:
        # Ultimate fallback: return stub even if something goes wrong
        if start_date is None:
            from datetime import datetime

            start_date = datetime.now().date()
        themes = _get_themes(days)
        platforms = _get_platforms(brief)
        return _stub_social_calendar(brief, start_date, days, themes, platforms)


def _generate_social_calendar_with_llm(
    brief: ClientInputBrief,
    start_date: date,
    days: int,
    themes: List[str],
    platforms: List[str],
) -> Optional[List[CalendarPostView]]:
    """
    Generate Social Calendar posts using LLM (Claude/OpenAI).

    Returns:
        List of CalendarPostView, or None if LLM call fails
    """
    try:
        # Lazy import to avoid hard dependency
        from aicmo.llm.client import _get_llm_provider, _get_claude_client, _get_openai_client

        brand_name = brief.brand.brand_name
        category = brief.brand.industry or "their category"
        audience = brief.audience.primary_customer or "their audience"
        goals = brief.goal.primary_goal or "achieve business growth"
        pain_points = (
            ", ".join(brief.audience.pain_points[:2])
            if brief.audience.pain_points
            else "their pain points"
        )

        # Extract USP if available
        usp = ""
        if brief.product_service and brief.product_service.items:
            first_item = brief.product_service.items[0]
            if first_item.usp:
                usp = first_item.usp

        # Build prompt
        platform_str = ", ".join(platforms) if platforms else "Instagram, LinkedIn, Twitter"

        prompt = f"""Generate exactly {days} compelling social media post hooks for a 7-day calendar.

Brand: {brand_name}
Category: {category}
Target Audience: {audience}
Primary Goal: {goals}
Audience Pain Points: {pain_points}
USP: {usp if usp else "Not specified"}
Platforms to use: {platform_str}
Content Themes: {', '.join(themes[:days])}

For each day (1-{days}), generate a hook (1-2 sentences) that:
1. Is specific to the brand and audience, not generic
2. Mentions or addresses the audience's pain point or goal
3. Is suitable for the assigned platform
4. Includes a compelling call-to-action (CTA) in 2-4 words

Return ONLY valid JSON in this exact format:
{{
  "posts": [
    {{
      "day": 1,
      "platform": "Instagram",
      "theme": "Brand Story",
      "hook": "Show [Brand] solving [problem] in one powerful visual that resonates with [audience].",
      "cta": "See the story"
    }},
    {{
      "day": 2,
      "platform": "LinkedIn",
      "theme": "Educational",
      "hook": "Share a quick tip on how [Brand] helps [audience] save time on [pain point].",
      "cta": "Learn the trick"
    }},
    ...
  ]
}}

Requirements:
- Each hook must be unique and specific to the day's theme and platform
- Hooks should not be generic ("Learn more", "Click here", etc.)
- CTAs must be action-oriented and varied (not all "Learn more")
- Avoid placeholder phrases like "will be customized", "TBD", "placeholder"
- Return ONLY the JSON, no explanation"""

        # Get LLM provider and call appropriate client
        provider = _get_llm_provider()

        if provider == "claude":
            client = _get_claude_client()
            model = os.getenv("AICMO_CLAUDE_MODEL", "claude-3-5-sonnet-20241022")
            response = client.messages.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text
        else:
            client = _get_openai_client()
            model = os.getenv("AICMO_OPENAI_MODEL", "gpt-4o-mini")
            response = client.chat.completions.create(
                model=model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content

        if not result or not result.strip():
            return None

        # Parse JSON response
        result = result.strip()
        # Remove markdown code fence if present
        if result.startswith("```"):
            result = result[result.find("{") : result.rfind("}") + 1]

        data = json.loads(result)
        if not isinstance(data, dict) or "posts" not in data:
            return None

        posts_data = data.get("posts", [])
        if not isinstance(posts_data, list):
            return None

        posts = []
        for item in posts_data:
            if not isinstance(item, dict):
                continue

            day_num = item.get("day", 0)
            if day_num < 1 or day_num > days:
                continue

            hook = item.get("hook", "").strip()
            cta = item.get("cta", "").strip()
            platform = item.get("platform", "Instagram").strip()
            theme = item.get(
                "theme", themes[day_num - 1] if day_num <= len(themes) else "Content"
            ).strip()

            if not hook or not cta:
                continue

            post = CalendarPostView(
                date=start_date + timedelta(days=day_num - 1),
                platform=platform,
                theme=theme,
                hook=hook,
                cta=cta,
                asset_type="reel" if day_num % 2 == 1 else "static_post",
                status="planned",
            )
            posts.append(post)

        return posts if len(posts) == days else None

    except Exception:
        return None


def _stub_social_calendar(
    brief: ClientInputBrief,
    start_date: date,
    days: int,
    themes: List[str],
    platforms: List[str],
) -> List[CalendarPostView]:
    """
    Fallback: Generate honest, brief-based Social Calendar posts.

    No placeholder phrases, no fake claims.
    Just simple, actionable hooks grounded in the brief.

    Args:
        brief: ClientInputBrief
        start_date: Start date for calendar
        days: Number of days to generate
        themes: List of themes for each day
        platforms: Available platforms

    Returns:
        Non-empty list of CalendarPostView
    """
    brand_name = brief.brand.brand_name
    audience = brief.audience.primary_customer or "your audience"
    category = brief.brand.industry or "your industry"

    # Get first pain point if available
    pain_point = ""
    if brief.audience.pain_points:
        pain_point = brief.audience.pain_points[0]

    # Get USP if available
    usp = ""
    if brief.product_service and brief.product_service.items:
        first_item = brief.product_service.items[0]
        if first_item.usp:
            usp = first_item.usp

    # CTA rotation to vary the messages
    cta_options = [
        "See how",
        "Learn more",
        "Read the full story",
        "Try it out",
        "Watch this",
        "Discover why",
        "Share this",
    ]

    posts = []
    for i in range(days):
        day_num = i + 1
        d = start_date + timedelta(days=i)
        platform = platforms[i % len(platforms)] if platforms else "Instagram"
        theme = themes[i] if i < len(themes) else "Content"

        # Generate hook based on brief context
        if i == 0:
            # Day 1: Introduce the brand
            hook = f"Meet {brand_name}: helping {audience} with {category}."
        elif i == 1:
            # Day 2: Pain point focus
            if pain_point:
                hook = f"Struggling with {pain_point}? {brand_name} has a better way."
            else:
                hook = f"{brand_name} makes {category} simpler for {audience}."
        elif i == 2:
            # Day 3: USP focus
            if usp:
                hook = f"How {brand_name}'s {usp} saves {audience} time and effort."
            else:
                hook = f"Discover what makes {brand_name} different in {category}."
        elif i == 3:
            # Day 4: Value proposition
            hook = f"Why {audience} are choosing {brand_name} for {category} solutions."
        elif i == 4:
            # Day 5: Social proof angle
            hook = f"Real {audience} getting real results with {brand_name}."
        elif i == 5:
            # Day 6: Action-oriented
            hook = f"Ready to experience {brand_name}? Here's how {audience} get started."
        else:
            # Day 7: Reinforce value
            hook = f"{brand_name}: trusted by {audience} for {category} excellence."

        # Pick CTA
        cta = cta_options[i % len(cta_options)]

        post = CalendarPostView(
            date=d,
            platform=platform,
            theme=theme,
            hook=hook,
            cta=cta,
            asset_type="reel" if day_num % 2 == 1 else "static_post",
            status="planned",
        )
        posts.append(post)

    return posts


def _get_themes(days: int) -> List[str]:
    """Get default themes for calendar days."""
    themes = [
        "Brand Story",
        "Educational",
        "Social Proof",
        "Behind-the-Scenes",
        "Value Proposition",
        "Action & Call-to-Action",
        "Community & Engagement",
    ]
    return themes[:days]


def _get_platforms(brief: ClientInputBrief) -> List[str]:
    """Extract available platforms from brief."""
    if brief.assets_constraints and brief.assets_constraints.focus_platforms:
        return brief.assets_constraints.focus_platforms
    # Default platforms
    return ["Instagram", "LinkedIn", "Twitter"]
