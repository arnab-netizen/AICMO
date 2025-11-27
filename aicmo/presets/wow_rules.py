from __future__ import annotations

from typing import Any, Dict, List, TypedDict


class WowSection(TypedDict):
    key: str


class WowRule(TypedDict, total=False):
    sections: List[WowSection]


# WOW_RULES defines which underlying section keys are assembled
# into the WOW (client-facing) report for each pack.
WOW_RULES: Dict[str, WowRule] = {
    # ------------------------------------------------------------
    # 1. Quick Social Pack (Basic)
    # ------------------------------------------------------------
    "quick_social_basic": {
        "sections": [
            {"key": "overview"},
            {"key": "audience_segments"},
            {"key": "messaging_framework"},
            {"key": "content_buckets"},
            {"key": "weekly_social_calendar"},
            {"key": "creative_direction_light"},
            {"key": "hashtag_strategy"},
            {"key": "platform_guidelines"},
            {"key": "kpi_plan_light"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 2. Strategy + Campaign Pack (Standard)
    # ------------------------------------------------------------
    "strategy_campaign_standard": {
        "sections": [
            {"key": "overview"},
            {"key": "campaign_objective"},
            {"key": "core_campaign_idea"},
            {"key": "messaging_framework"},
            {"key": "channel_plan"},
            {"key": "audience_segments"},
            {"key": "persona_cards"},
            {"key": "creative_direction"},
            {"key": "influencer_strategy"},
            {"key": "promotions_and_offers"},
            {"key": "detailed_30_day_calendar"},
            {"key": "email_and_crm_flows"},
            {"key": "ad_concepts"},
            {"key": "kpi_and_budget_plan"},
            {"key": "execution_roadmap"},
            {"key": "post_campaign_analysis"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 3. Full-Funnel Growth Suite (Premium)
    # ------------------------------------------------------------
    "full_funnel_growth_suite": {
        "sections": [
            {"key": "overview"},
            {"key": "market_landscape"},
            {"key": "competitor_analysis"},
            {"key": "funnel_breakdown"},
            {"key": "audience_segments"},
            {"key": "persona_cards"},
            {"key": "value_proposition_map"},
            {"key": "messaging_framework"},
            {"key": "awareness_strategy"},
            {"key": "consideration_strategy"},
            {"key": "conversion_strategy"},
            {"key": "retention_strategy"},
            {"key": "email_automation_flows"},
            {"key": "remarketing_strategy"},
            {"key": "ad_concepts_multi_platform"},
            {"key": "creative_direction"},
            {"key": "full_30_day_calendar"},
            {"key": "video_scripts"},
            {"key": "week1_action_plan"},
            {"key": "kpi_and_budget_plan"},
            {"key": "execution_roadmap"},
            {"key": "optimization_opportunities"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 4. Launch & GTM Pack
    # ------------------------------------------------------------
    "launch_gtm_pack": {
        "sections": [
            {"key": "overview"},
            {"key": "market_landscape"},
            {"key": "product_positioning"},
            {"key": "messaging_framework"},
            {"key": "launch_phases"},
            {"key": "channel_plan"},
            {"key": "audience_segments"},
            {"key": "persona_cards"},
            {"key": "creative_direction"},
            {"key": "influencer_strategy"},
            {"key": "launch_campaign_ideas"},
            {"key": "email_and_crm_flows"},
            {"key": "content_calendar_launch"},
            {"key": "ad_concepts"},
            {"key": "video_scripts"},
            {"key": "week1_action_plan"},
            {"key": "kpi_and_budget_plan"},
            {"key": "execution_roadmap"},
            {"key": "risk_analysis"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 5. Brand Turnaround Lab
    # ------------------------------------------------------------
    "brand_turnaround_lab": {
        "sections": [
            {"key": "overview"},
            {"key": "brand_audit"},
            {"key": "customer_insights"},
            {"key": "competitor_analysis"},
            {"key": "problem_diagnosis"},
            {"key": "new_positioning"},
            {"key": "messaging_framework"},
            {"key": "creative_direction"},
            {"key": "channel_reset_strategy"},
            {"key": "reputation_recovery_plan"},
            {"key": "promotions_and_offers"},
            {"key": "email_and_crm_flows"},
            {"key": "30_day_recovery_calendar"},
            {"key": "ad_concepts"},
            {"key": "video_scripts"},
            {"key": "week1_action_plan"},
            {"key": "kpi_and_budget_plan"},
            {"key": "execution_roadmap"},
            {"key": "turnaround_milestones"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 6. Retention & CRM Booster
    # ------------------------------------------------------------
    "retention_crm_booster": {
        "sections": [
            {"key": "overview"},
            {"key": "customer_segments"},
            {"key": "persona_cards"},
            {"key": "customer_journey_map"},
            {"key": "retention_drivers"},
            {"key": "email_automation_flows"},
            {"key": "sms_and_whatsapp_flows"},
            {"key": "loyalty_program_concepts"},
            {"key": "winback_sequence"},
            {"key": "post_purchase_experience"},
            {"key": "ugc_and_community_plan"},
            {"key": "video_scripts"},
            {"key": "week1_action_plan"},
            {"key": "kpi_plan_retention"},
            {"key": "execution_roadmap"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 7. Performance Audit & Revamp
    # ------------------------------------------------------------
    "performance_audit_revamp": {
        "sections": [
            {"key": "overview"},
            {"key": "account_audit"},
            {"key": "campaign_level_findings"},
            {"key": "creative_performance_analysis"},
            {"key": "audience_analysis"},
            {"key": "funnel_breakdown"},
            {"key": "competitor_benchmark"},
            {"key": "problem_diagnosis"},
            {"key": "revamp_strategy"},
            {"key": "new_ad_concepts"},
            {"key": "creative_direction"},
            {"key": "remarketing_strategy"},
            {"key": "kpi_reset_plan"},
            {"key": "execution_roadmap"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 8. PR & Reputation Pack
    # ------------------------------------------------------------
    "pr_reputation_pack": {
        "sections": [
            {"key": "overview"},
            {"key": "market_landscape"},
            {"key": "customer_insights"},
            {"key": "competitor_benchmark"},
            {"key": "problem_diagnosis"},
            {"key": "brand_audit"},
            {"key": "product_positioning"},
            {"key": "new_positioning"},
            {"key": "messaging_framework"},
            {"key": "channel_plan"},
            {"key": "influencer_strategy"},
            {"key": "reputation_recovery_plan"},
            {"key": "content_calendar_launch"},
            {"key": "email_and_crm_flows"},
            {"key": "kpi_and_budget_plan"},
            {"key": "execution_roadmap"},
            {"key": "final_summary"},
        ]
    },
    # ------------------------------------------------------------
    # 9. Always-On Content Engine
    # ------------------------------------------------------------
    "always_on_content_engine": {
        "sections": [
            {"key": "overview"},
            {"key": "audience_segments"},
            {"key": "persona_cards"},
            {"key": "messaging_framework"},
            {"key": "content_buckets"},
            {"key": "platform_guidelines"},
            {"key": "hashtag_strategy"},
            {"key": "channel_plan"},
            {"key": "creative_direction"},
            {"key": "weekly_social_calendar"},
            {"key": "full_30_day_calendar"},
            {"key": "ugc_and_community_plan"},
            {"key": "email_and_crm_flows"},
            {"key": "kpi_plan_light"},
            {"key": "execution_roadmap"},
            {"key": "final_summary"},
        ]
    },
}


def get_wow_rule(package_key: str) -> WowRule:
    """
    Safe accessor for WOW rules. Returns an empty rule if none is defined.
    """
    return WOW_RULES.get(package_key, {"sections": []})


def get_wow_rules(package_key: str) -> Dict[str, Any]:
    """
    Backward-compatible accessor for WOW rules.

    Returns section structure for new code, empty dict for old code.
    This maintains compatibility with code that expects min_captions, etc.
    """
    rule = WOW_RULES.get(package_key)
    if rule:
        return {"sections": rule.get("sections", [])}
    return {}
