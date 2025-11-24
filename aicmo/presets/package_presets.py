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
    # ----- 2. Strategy + Campaign Pack (Standard - 17 sections) -----
    "strategy_campaign_standard": {
        "label": "Strategy + Campaign Pack (Standard)",
        "description": "Comprehensive, professional strategy for mid-market campaigns. Agency-ready output.",
        "tier": "standard",
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
    # ============================================================
    # STRATEGY + CAMPAIGN PACK TIER SYSTEM
    # (3-layer architecture: Basic → Standard → Premium → Enterprise)
    # ============================================================
    # All strategy packs use same core sections but vary in depth & scope
    # Basic: Concise, quick-turnaround, perfect for small teams
    # Standard: Comprehensive, professional, agency-ready (17 sections)
    # Premium: Full-service, multi-channel, detailed (25 sections)
    # Enterprise: Consulting-grade, strategic frameworks, C-suite ready (30 sections)
    # ============================================================
    # ----- 3a. Strategy + Campaign Pack (Basic - 4-5 sections) -----
    "strategy_campaign_basic": {
        "label": "Strategy + Campaign Pack (Basic)",
        "description": "Quick, focused strategy for fast execution. Perfect for teams on tight deadlines.",
        "tier": "basic",
        "sections": [
            "overview",
            "core_campaign_idea",
            "messaging_framework",
            "audience_segments",
            "detailed_30_day_calendar",
            "final_summary",
        ],
        "requires_research": False,
        "complexity": "low",
    },
    # Note: strategy_campaign_standard stays at 17 sections (moved below)
    # ============================================================
    # 3. Full-Funnel Growth Suite (Premium)
    # ============================================================
    # (Renamed from full_funnel_growth_suite for consistency in naming)
    # Note: This is currently 21 sections. Will be enhanced to 25 for true Premium tier.
    # ============================================================
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
    # ============================================================
    # 8. Strategy + Campaign Pack (Premium - 25 sections)
    # ============================================================
    "strategy_campaign_premium": {
        "label": "Strategy + Campaign Pack (Premium)",
        "description": "Comprehensive, multi-channel strategy with advanced creative, UGC, and funnel frameworks.",
        "tier": "premium",
        "sections": [
            "overview",
            "campaign_objective",
            "core_campaign_idea",
            "messaging_framework",
            "value_proposition_map",
            "channel_plan",
            "audience_segments",
            "persona_cards",
            "creative_direction",
            "creative_territories",
            "copy_variants",
            "influencer_strategy",
            "ugc_and_community_plan",
            "promotions_and_offers",
            "funnel_breakdown",
            "awareness_strategy",
            "consideration_strategy",
            "conversion_strategy",
            "detailed_30_day_calendar",
            "email_and_crm_flows",
            "sms_and_whatsapp_strategy",
            "ad_concepts",
            "remarketing_strategy",
            "kpi_and_budget_plan",
            "execution_roadmap",
            "post_campaign_analysis",
            "optimization_opportunities",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "high",
    },
    # ============================================================
    # 9. Strategy + Campaign Pack (Enterprise - 30 sections)
    # ============================================================
    "strategy_campaign_enterprise": {
        "label": "Strategy + Campaign Pack (Enterprise)",
        "description": "Consulting-grade strategy with industry analysis, competitive frameworks, risk assessment, and C-suite summaries.",
        "tier": "enterprise",
        "sections": [
            "overview",
            "industry_landscape",
            "market_analysis",
            "competitor_analysis",
            "customer_insights",
            "campaign_objective",
            "core_campaign_idea",
            "value_proposition_map",
            "messaging_framework",
            "brand_positioning",
            "channel_plan",
            "audience_segments",
            "persona_cards",
            "customer_journey_map",
            "creative_direction",
            "creative_territories",
            "copy_variants",
            "influencer_strategy",
            "ugc_and_community_plan",
            "promotions_and_offers",
            "funnel_breakdown",
            "awareness_strategy",
            "consideration_strategy",
            "conversion_strategy",
            "retention_strategy",
            "detailed_30_day_calendar",
            "email_and_crm_flows",
            "sms_and_whatsapp_strategy",
            "ad_concepts",
            "remarketing_strategy",
            "measurement_framework",
            "kpi_and_budget_plan",
            "risk_assessment",
            "execution_roadmap",
            "post_campaign_analysis",
            "optimization_opportunities",
            "strategic_recommendations",
            "cxo_summary",
            "final_summary",
        ],
        "requires_research": True,
        "complexity": "very-high",
    },
}
