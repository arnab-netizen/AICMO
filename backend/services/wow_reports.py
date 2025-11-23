"""
WOW Report Building Service

This module encapsulates all WOW template logic, keeping main.py clean.
Provides safe, defensive placeholder replacement and rule access.

Key functions:
- build_default_placeholders: Create a generic placeholder map from brief + blocks
- apply_wow_template: Replace {{placeholders}} with values, strip unfilled ones
- get_wow_rules_for_package: Wrapper around get_wow_rules() for locality
"""

from __future__ import annotations

import re
from typing import Any, Dict, Mapping, Optional

from aicmo.presets.wow_templates import get_wow_template
from aicmo.presets.wow_rules import get_wow_rules

# Matches {{placeholder_name}} patterns
_PLACEHOLDER_PATTERN = re.compile(r"{{\s*([a-zA-Z0-9_]+)\s*}}")


def build_default_placeholders(
    brief: Optional[Mapping[str, Any]] = None,
    base_blocks: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a generic placeholder map for WOW templates from:
    - the client brief (business details, goals, etc.)
    - any blocks your generator already produced (tables, captions, etc.)

    This is intentionally defensive:
    - Missing keys just become empty strings
    - You can extend this mapping over time without breaking anything

    Args:
        brief: Client brief dict with business details, goals, audience, etc.
        base_blocks: Pre-generated blocks (tables, captions, hashtags, etc.)

    Returns:
        Dictionary mapping placeholder names to values (or empty strings if missing)
    """
    brief = dict(brief or {})
    base_blocks = dict(base_blocks or {})

    # Try to resolve commonly used fields; fall back gracefully if missing.
    brand_name = (
        brief.get("brand_name")
        or brief.get("business_name")
        or brief.get("client_name")
        or brief.get("name")
        or ""
    )
    category = brief.get("category") or brief.get("business_type") or ""
    city = brief.get("city") or brief.get("location") or ""
    region = brief.get("region") or brief.get("country") or ""
    target_audience = brief.get("target_audience") or brief.get("audience") or ""
    brand_tone = brief.get("brand_tone") or brief.get("tone_of_voice") or ""
    primary_channel = brief.get("primary_channel") or "Instagram"
    key_opportunity = brief.get("key_opportunity") or brief.get("main_goal") or ""

    placeholders: Dict[str, Any] = {
        # Generic / brand-level placeholders used across templates
        "brand_name": brand_name,
        "category": category,
        "city": city,
        "region": region,
        "target_audience": target_audience,
        "brand_tone": brand_tone,
        "primary_channel": primary_channel,
        "key_opportunity": key_opportunity,
        # Smart defaults for branding elements
        "brand_colors": brief.get("brand_colors", "#FFFFFF, #000000"),
        "brand_fonts": brief.get("brand_fonts", "Inter, Roboto"),
        "ideal_customer_profile": brief.get("ideal_customer_profile", ""),
        "pricing": brief.get("pricing", ""),
        "offer_name": brief.get("offer_name", ""),
    }

    # Pick up any known blocks the generator already produced
    # (calendar tables, captions, reels, hashtags, etc.).
    # This is safe even if some are missing.
    for key in (
        "calendar_14_day_table",
        "calendar_30_day_table",
        "calendar_full_funnel_30_day_table",
        "launch_calendar_30_day_table",
        "turnaround_30_day_plan_table",
        "revamp_30_day_plan_table",
        "crm_30_day_calendar_table",
        "sample_captions_block",
        "hero_captions_block",
        "supporting_captions_block",
        "carousel_captions_block",
        "reel_ideas_block",
        "reel_concepts_block",
        "ad_reel_scripts_block",
        "hashtags_location",
        "hashtags_audience",
        "hashtags_product",
        "hashtags_trend",
        "hashtags_brand_category",
        "hashtags_occasion",
        "hashtags_tier_mix",
        "hashtags_full_funnel_block",
        "turnaround_hashtags_block",
        "cta_library_block",
        "competitor_benchmark_block",
        "launch_competitor_block",
        "turnaround_competitor_block",
        "reputation_templates_block",
        "landing_page_wireframe_block",
        "welcome_sequence_block",
        "conversion_sequence_block",
        "winback_sequence_block",
        "customer_journey_block",
        "crm_welcome_flow_block",
        "crm_post_purchase_flow_block",
        "crm_winback_flow_block",
        "crm_sms_templates_block",
        "loyalty_referral_block",
        "offer_strategy_block",
        "channel_audit_block",
        "creative_review_block",
        "funnel_review_block",
        "priority_fix_list_block",
        "revamp_creative_block",
        "revamp_kpi_block",
        "launch_kpis_milestones_block",
    ):
        if key in base_blocks and base_blocks.get(key) is not None:
            placeholders[key] = base_blocks[key]

    # Some sensible numeric / checklist defaults if not provided upstream
    placeholders.setdefault("posting_frequency", "1 post per day")
    placeholders.setdefault("weekly_posts_target", 5)
    placeholders.setdefault("weekly_reels_target", 2)
    placeholders.setdefault("weekly_engagement_target", 20)

    return placeholders


def apply_wow_template(
    package_key: str,
    placeholder_values: Mapping[str, Any],
    strip_unfilled: bool = True,
) -> str:
    """
    Apply a WOW template for the given package key using placeholder_values.

    - Uses get_wow_template() so unknown package_key returns a safe fallback.
    - Replaces {{placeholder}} with the provided values.
    - Optionally strips any unreplaced {{...}} placeholders to avoid leaking
      template artifacts to the client.
    - If brief is incomplete (missing >3 key fields), uses fallback_basic template.

    Args:
        package_key: One of the WOW package keys (e.g., "quick_social_basic")
        placeholder_values: Mapping of placeholder names to their values
        strip_unfilled: If True, remove any unfilled {{placeholder}} patterns

    Returns:
        Markdown string with placeholders replaced
    """
    # Check if brief is too incomplete; if so, use fallback template
    # Count non-empty required fields
    required_fields = ["brand_name", "category", "target_audience", "city"]
    provided_fields = sum(
        1
        for field in required_fields
        if placeholder_values.get(field) and str(placeholder_values.get(field)).strip()
    )

    # If less than 2 required fields are filled, use fallback_basic
    if provided_fields < 2:
        package_key = "fallback_basic"

    template = get_wow_template(package_key)
    result = template

    # First pass: direct substitution for all known placeholder values.
    for key, value in dict(placeholder_values).items():
        # Always coerce to string, but avoid 'None'
        safe_value = "" if value is None else str(value)
        result = result.replace(f"{{{{{key}}}}}", safe_value)

    if strip_unfilled:
        # Remove any leftover {{placeholder}} patterns
        result = _PLACEHOLDER_PATTERN.sub("", result)

    return result


def get_wow_rules_for_package(package_key: str) -> Dict[str, Any]:
    """
    Thin wrapper around get_wow_rules() so main.py doesn't need to import it
    directly if you want to keep dependencies localized.

    Args:
        package_key: WOW package key

    Returns:
        Dictionary of rules for this package (e.g., min_captions, min_hashtags)
        Empty dict if package_key is not found.
    """
    return get_wow_rules(package_key)


# Mapping from UI dropdown labels to internal wow_package_key values
PACKAGE_KEY_BY_LABEL = {
    "Quick Social Pack (Basic)": "quick_social_basic",
    "Strategy + Campaign Pack (Standard)": "strategy_campaign_standard",
    "Full-Funnel Growth Suite (Premium)": "full_funnel_premium",
    "Launch & GTM Pack": "launch_gtm",
    "Brand Turnaround Lab": "brand_turnaround",
    "Retention & CRM Booster": "retention_crm",
    "Performance Audit & Revamp": "performance_audit",
}


def resolve_wow_package_key(service_pack_label: Optional[str]) -> Optional[str]:
    """
    Convert a service pack dropdown label to the internal wow_package_key.

    Args:
        service_pack_label: Label from the UI dropdown

    Returns:
        The internal package key (e.g., "quick_social_basic"), or None if not found
    """
    if not service_pack_label:
        return None
    return PACKAGE_KEY_BY_LABEL.get(service_pack_label)
