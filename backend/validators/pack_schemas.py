"""
Per-Pack Output Contract Schemas for AICMO

Defines the expected structure (required sections, optional sections, ordering rules)
for each AICMO package preset. These schemas are used to validate that generated
reports contain all necessary sections before being exported to clients.

IMPORTANT: Section IDs in these schemas MUST match the keys in SECTION_GENERATORS
(backend/main.py) and the section lists in PACKAGE_PRESETS (aicmo/presets/package_presets.py).

Schema Structure:
    - required_sections: List of section IDs that MUST be present and non-empty
    - optional_sections: List of section IDs that MAY appear
    - enforce_order: Whether sections must appear in the specified order
"""

from typing import Dict, List, Any

# Type alias for pack schema structure
PackSchema = Dict[str, Any]

PACK_OUTPUT_SCHEMAS: Dict[str, PackSchema] = {
    # ============================================================
    # 1. Quick Social Pack (Basic) - 10 sections
    # ============================================================
    "quick_social_basic": {
        "required_sections": [
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
        "optional_sections": [],
        "enforce_order": True,
        "description": "Quick, focused social media strategy for fast execution",
        "expected_section_count": 10,
    },
    # ============================================================
    # 2. Strategy + Campaign Pack (Standard) - 17 sections
    # ============================================================
    "strategy_campaign_standard": {
        "required_sections": [
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
        "optional_sections": [],
        "enforce_order": True,
        "description": "Comprehensive, professional strategy for mid-market campaigns",
        "expected_section_count": 17,
    },
    # ============================================================
    # 3. Strategy + Campaign Pack (Basic) - 6 sections
    # ============================================================
    "strategy_campaign_basic": {
        "required_sections": [
            "overview",
            "core_campaign_idea",
            "messaging_framework",
            "audience_segments",
            "detailed_30_day_calendar",
            "final_summary",
        ],
        "optional_sections": [],
        "enforce_order": True,
        "description": "Quick, focused strategy for fast execution",
        "expected_section_count": 6,
    },
    # ============================================================
    # 4. Full-Funnel Growth Suite (Premium) - 23 sections
    # ============================================================
    "full_funnel_growth_suite": {
        "required_sections": [
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
            "landing_page_blueprint",
            "email_automation_flows",
            "remarketing_strategy",
            "ad_concepts_multi_platform",
            "creative_direction",
            "full_30_day_calendar",
            "kpi_and_budget_plan",
            "measurement_framework",
            "execution_roadmap",
            "optimization_opportunities",
            "final_summary",
        ],
        "optional_sections": [],
        "enforce_order": True,
        "description": "Full-service, multi-channel, detailed strategy",
        "expected_section_count": 23,
    },
    # ============================================================
    # 5. Launch & GTM Pack - 13 sections
    # ============================================================
    "launch_gtm_pack": {
        "required_sections": [
            "overview",
            "market_landscape",
            "product_positioning",
            "messaging_framework",
            "launch_phases",
            "channel_plan",
            "audience_segments",
            "creative_direction",
            "launch_campaign_ideas",
            "content_calendar_launch",
            "ad_concepts",
            "execution_roadmap",
            "final_summary",
        ],
        "optional_sections": [],
        "enforce_order": True,
        "description": "Product launch and go-to-market strategy",
        "expected_section_count": 13,
    },
    # ============================================================
    # 6. Brand Turnaround Lab - 14 sections
    # ============================================================
    "brand_turnaround_lab": {
        "required_sections": [
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
            "30_day_recovery_calendar",
            "execution_roadmap",
            "final_summary",
        ],
        "optional_sections": [],
        "enforce_order": True,
        "description": "Brand recovery and repositioning strategy",
        "expected_section_count": 14,
    },
    # ============================================================
    # 7. Retention & CRM Booster - 14 sections
    # ============================================================
    "retention_crm_booster": {
        "required_sections": [
            "overview",
            "customer_segments",
            "persona_cards",
            "customer_journey_map",
            "churn_diagnosis",
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
        "optional_sections": [],
        "enforce_order": True,
        "description": "Customer retention and lifecycle marketing strategy",
        "expected_section_count": 14,
    },
    # ============================================================
    # 8. Performance Audit & Revamp - 16 sections
    # ============================================================
    "performance_audit_revamp": {
        "required_sections": [
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
            "conversion_audit",
            "remarketing_strategy",
            "kpi_reset_plan",
            "execution_roadmap",
            "final_summary",
        ],
        "optional_sections": [],
        "enforce_order": True,
        "description": "Marketing performance audit and optimization strategy",
        "expected_section_count": 16,
    },
    # ============================================================
    # 9. Strategy + Campaign Pack (Premium) - 28 sections
    # ============================================================
    "strategy_campaign_premium": {
        "required_sections": [
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
        "optional_sections": [],
        "enforce_order": True,
        "description": "Comprehensive, multi-channel strategy with advanced creative frameworks",
        "expected_section_count": 28,
    },
    # ============================================================
    # 10. Strategy + Campaign Pack (Enterprise) - 39 sections
    # ============================================================
    "strategy_campaign_enterprise": {
        "required_sections": [
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
        "optional_sections": [],
        "enforce_order": True,
        "description": "Consulting-grade strategy with industry analysis and C-suite summaries",
        "expected_section_count": 39,
    },
}


def get_pack_schema(pack_key: str) -> PackSchema | None:
    """
    Retrieve the output schema for a given pack key.

    Args:
        pack_key: Package preset key (e.g., "quick_social_basic", "strategy_campaign_standard")

    Returns:
        Pack schema dict or None if pack_key not found
    """
    return PACK_OUTPUT_SCHEMAS.get(pack_key)


def get_all_pack_keys() -> List[str]:
    """
    Get list of all registered pack keys.

    Returns:
        List of pack keys that have defined schemas
    """
    return list(PACK_OUTPUT_SCHEMAS.keys())


def validate_schema_completeness() -> List[str]:
    """
    Validate that all schemas are properly defined.

    Checks:
    - All required_sections are non-empty lists
    - expected_section_count matches len(required_sections)
    - No duplicate section IDs within a schema

    Returns:
        List of validation error messages (empty if all valid)
    """
    errors = []

    for pack_key, schema in PACK_OUTPUT_SCHEMAS.items():
        # Check required_sections exists and is non-empty
        required = schema.get("required_sections", [])
        if not required:
            errors.append(f"{pack_key}: required_sections is empty or missing")
            continue

        # Check expected_section_count matches
        expected_count = schema.get("expected_section_count", 0)
        actual_count = len(required)
        if expected_count != actual_count:
            errors.append(
                f"{pack_key}: expected_section_count={expected_count} but found {actual_count} required sections"
            )

        # Check for duplicates
        if len(required) != len(set(required)):
            duplicates = [s for s in required if required.count(s) > 1]
            errors.append(f"{pack_key}: duplicate section IDs: {set(duplicates)}")

    return errors
