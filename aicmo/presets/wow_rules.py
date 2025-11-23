from __future__ import annotations

from typing import Dict, Any


"""
Standardized "WOW rules" for all packs.

These rules define the *minimum content expectations* AICMO should meet
when generating a deliverable, so every client feels they received more
than expected.

The idea: the generator can check these numbers and ensure it produces
at least this amount of content per section.
"""


WOW_RULES: Dict[str, Dict[str, Any]] = {
    "quick_social_basic": {
        "min_days_in_calendar": 14,
        "min_captions": 10,
        "min_reel_ideas": 5,
        "min_hashtags": 40,
        "include_weekly_checklist": True,
        "include_visual_direction": "mini",
    },
    "strategy_campaign_standard": {
        "min_days_in_calendar": 30,
        "min_captions": 20,
        "min_reel_ideas": 10,
        "min_hashtags": 90,
        "require_competitor_benchmark": True,
        "require_kpi_plan": True,
        "include_visual_direction": "full",
    },
    "full_funnel_premium": {
        "min_days_in_calendar": 30,
        "min_captions": 25,
        "min_reel_ideas": 15,
        "min_hashtags": 120,
        "min_email_sequences": 3,
        "require_landing_wireframe": True,
        "require_kpi_dashboard": True,
        "require_cta_library": True,
    },
    "launch_gtm": {
        "min_days_in_calendar": 30,
        "min_captions": 20,
        "min_reel_ideas": 10,
        "min_hashtags": 80,
        "require_competitor_benchmark": True,
        "require_influencer_strategy": True,
    },
    "brand_turnaround": {
        "min_days_in_calendar": 30,
        "min_captions": 10,
        "min_hashtags": 60,
        "require_brand_diagnosis": True,
        "require_reputation_templates": True,
    },
    "retention_crm": {
        "min_days_in_calendar": 30,
        "min_email_sequences": 3,
        "min_sms_templates": 10,
        "require_journey_map": True,
        "require_loyalty_concepts": True,
    },
    "performance_audit": {
        "min_days_in_calendar": 30,
        "min_priority_fixes": 15,
        "require_channel_audit": True,
        "require_creative_review": True,
        "require_kpi_targets": True,
    },
}


def get_wow_rules(package_key: str) -> Dict[str, Any]:
    """
    Safely return WOW rules for a given package key.

    Returns an empty dict if not configured, so callers can handle
    gracefully without crashing.
    """
    return WOW_RULES.get(package_key, {})
