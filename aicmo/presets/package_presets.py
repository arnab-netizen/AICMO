"""
Package Presets for AICMO Report Generation

Defines all available report packages with their section configurations.
Each package specifies which sections to include, research requirements, and complexity level.
"""

from __future__ import annotations

from typing import List, TypedDict


class PackageConfig(TypedDict):
    sections: List[str]
    requires_research: bool
    complexity: str
    label: str


PACKAGE_PRESETS: dict[str, PackageConfig] = {
    # IMPORTANT: Keys are SLUGS (e.g., "quick_social_basic"), not display names
    # The label field provides the display name
    # -------------------------------------------------------------
    # 1. Quick Social Pack (Basic)
    # -------------------------------------------------------------
    "quick_social_basic": {
        "label": "Quick Social Pack (Basic)",
        # All fields are required
        "sections": [
            "overview",
            "audience_segments",
            "messaging_framework",
            "content_buckets",
            "weekly_social_calendar",
            "creative_direction_light",
            "hashtag_strategy",
            "platform_guidelines",
            "kpi_plan_light",
            "final_summary",
        ],
        "requires_research": False,
        "complexity": "low",
    },
    # -------------------------------------------------------------
    # 2. Strategy + Campaign Pack (Standard)
    # -------------------------------------------------------------
    "strategy_campaign_standard": {
        "label": "Strategy + Campaign Pack (Standard)",
        "sections": [
            "overview",
            "campaign_objective",
            "core_campaign_idea",
            "messaging_framework",
            "channel_plan",
            "audience_segments",
            "persona_cards",
            "creative_direction",
            "influencer_strategy",
            "promotions_and_offers",
            "detailed_30_day_calendar",
            "email_and_crm_flows",
            "ad_concepts",
            "kpi_and_budget_plan",
            "execution_roadmap",
            "post_campaign_analysis",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "medium",
    },
    # -------------------------------------------------------------
    # 3. Full-Funnel Growth Suite (Premium)
    # -------------------------------------------------------------
    "full_funnel_growth_suite": {
        "label": "Full-Funnel Growth Suite (Premium)",
        "sections": [
            "overview",
            "market_landscape",
            "competitor_analysis",
            "funnel_breakdown",
            "audience_segments",
            "persona_cards",
            "value_proposition_map",
            "messaging_framework",
            "awareness_strategy",
            "consideration_strategy",
            "conversion_strategy",
            "retention_strategy",
            "email_automation_flows",
            "remarketing_strategy",
            "ad_concepts_multi_platform",
            "creative_direction",
            "full_30_day_calendar",
            "kpi_and_budget_plan",
            "execution_roadmap",
            "optimization_opportunities",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "high",
    },
    # -------------------------------------------------------------
    # 4. Launch & GTM Pack
    # -------------------------------------------------------------
    "launch_gtm_pack": {
        "label": "Launch & GTM Pack",
        "sections": [
            "overview",
            "market_landscape",
            "product_positioning",
            "messaging_framework",
            "launch_phases",
            "channel_plan",
            "audience_segments",
            "persona_cards",
            "creative_direction",
            "influencer_strategy",
            "launch_campaign_ideas",
            "email_and_crm_flows",
            "content_calendar_launch",
            "ad_concepts",
            "kpi_and_budget_plan",
            "execution_roadmap",
            "risk_analysis",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "medium-high",
    },
    # -------------------------------------------------------------
    # 5. Brand Turnaround Lab
    # -------------------------------------------------------------
    "brand_turnaround_lab": {
        "label": "Brand Turnaround Lab",
        "sections": [
            "overview",
            "brand_audit",
            "customer_insights",
            "competitor_analysis",
            "problem_diagnosis",
            "new_positioning",
            "messaging_framework",
            "creative_direction",
            "channel_reset_strategy",
            "reputation_recovery_plan",
            "promotions_and_offers",
            "email_and_crm_flows",
            "30_day_recovery_calendar",
            "ad_concepts",
            "kpi_and_budget_plan",
            "execution_roadmap",
            "turnaround_milestones",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "high",
    },
    # -------------------------------------------------------------
    # 6. Retention & CRM Booster
    # -------------------------------------------------------------
    "retention_crm_booster": {
        "label": "Retention & CRM Booster",
        "sections": [
            "overview",
            "customer_segments",
            "persona_cards",
            "customer_journey_map",
            "retention_drivers",
            "email_automation_flows",
            "sms_and_whatsapp_flows",
            "loyalty_program_concepts",
            "winback_sequence",
            "post_purchase_experience",
            "ugc_and_community_plan",
            "kpi_plan_retention",
            "execution_roadmap",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "medium",
    },
    # -------------------------------------------------------------
    # 7. Performance Audit & Revamp
    # -------------------------------------------------------------
    "performance_audit_revamp": {
        "label": "Performance Audit & Revamp",
        "sections": [
            "overview",
            "account_audit",
            "campaign_level_findings",
            "creative_performance_analysis",
            "audience_analysis",
            "funnel_breakdown",
            "competitor_benchmark",
            "problem_diagnosis",
            "revamp_strategy",
            "new_ad_concepts",
            "creative_direction",
            "remarketing_strategy",
            "kpi_reset_plan",
            "execution_roadmap",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "medium-high",
    },
}
