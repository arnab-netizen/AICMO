from __future__ import annotations

from typing import Dict

# WOW templates for each service pack.
# These are markdown-based, PDF-friendly layouts with placeholders using
# double-curly syntax (e.g {{brand_name}}) so they can be filled by any
# simple replace/format layer without extra dependencies.

WOW_TEMPLATES: Dict[str, str] = {
    # ============================================================
    # 1. Quick Social Pack (Basic)
    # ============================================================
    "quick_social_basic": r"""# {{brand_name}} – Quick Social Playbook
### Social Media Content Engine for {{primary_channel}} – {{city}}

---

## 1. Brand & Context Snapshot

{{overview}}

---

## 2. Audience Snapshot

{{audience_segments}}

---

## 3. Messaging Framework

{{messaging_framework}}

---

## 4. Content Buckets & Themes

{{content_buckets}}

---

## 5. Weekly Social Calendar

{{weekly_social_calendar}}

---

## 6. Lightweight Creative Direction

{{creative_direction_light}}

---

## 7. Hashtag Strategy

{{hashtag_strategy}}

---

## 8. Platform-by-Platform Guidelines

{{platform_guidelines}}

---

## 9. KPIs & Lightweight Measurement Plan

{{kpi_plan_light}}

---

## 10. Final Summary & Next Steps

{{final_summary}}
""",
    # ============================================================
    # 2. Strategy + Campaign Pack (Standard)
    # ============================================================
    "strategy_campaign_standard": r"""# {{brand_name}} – Strategy + Campaign Pack (Standard)
### Integrated Social & Campaign Strategy – {{campaign_name}}

---

## 1. Campaign Overview

{{overview}}

---

## 2. Campaign Objectives

{{campaign_objective}}

---

## 3. Core Campaign Idea

{{core_campaign_idea}}

---

## 4. Messaging Framework

{{messaging_framework}}

---

## 5. Channel Plan

{{channel_plan}}

---

## 6. Audience Segments

{{audience_segments}}

---

## 7. Persona Cards

{{persona_cards}}

---

## 8. Creative Direction

{{creative_direction}}

---

## 9. Influencer Strategy

{{influencer_strategy}}

---

## 10. Promotions & Offers

{{promotions_and_offers}}

---

## 11. Detailed 30-Day Calendar

{{detailed_30_day_calendar}}

---

## 12. Email & CRM Flows

{{email_and_crm_flows}}

---

## 13. Ad Concepts

{{ad_concepts}}

---

## 14. KPI & Budget Plan

{{kpi_and_budget_plan}}

---

## 15. Execution Roadmap

{{execution_roadmap}}

---

## 16. Post-Campaign Analysis

{{post_campaign_analysis}}

---

## 17. Final Summary

{{final_summary}}

---

*This Strategy + Campaign Pack gives {{brand_name}} a comprehensive, executable roadmap that aligns objectives, messaging, channels, creative, and measurement around {{campaign_name}}.*
""",
    "full_funnel_growth_suite": r"""# {{brand_name}} – Full-Funnel Growth Suite (Premium)
### Awareness → Consideration → Conversion → Retention

---

## 1. Brand & Offer Architecture

- **Brand:** {{brand_name}}
- **Core Offer(s):** {{core_offers}}
- **Price Points:** {{price_points}}
- **Ideal Customer Profile (ICP):** {{icp}}
- **Primary Objections:** {{primary_objections}}
- **Unique Proof & Authority:** {{proof_points}}

---

## 2. Funnel Overview

```
Traffic Sources → Lead Magnet → Nurture → Offer → Post-Purchase → Referral
```

**Traffic Sources:** {{traffic_sources}}

**Lead Magnets:** {{lead_magnets}}

**Primary Offers:** {{primary_offers}}

**Nurture Mechanisms:** {{nurture_mechanisms}}

**LTV Growth Levers:** {{ltv_levers}}

---

## 3. Funnel Stage Breakdown

### A. Awareness

**Channels:** {{awareness_channels}}

**Content types:** {{awareness_content_types}}

**Key hooks & angles:** {{awareness_hooks}}

### B. Consideration

**Channels:** {{consideration_channels}}

**Nurture content:** {{consideration_content}}

**Social proof assets:** {{social_proof_assets}}

### C. Conversion

**Sales pages / landing pages:** {{conversion_pages}}

**Core offer positioning:** {{conversion_positioning}}

**Guarantees & urgency:** {{conversion_guarantees}}

### D. Retention & Expansion

**Onboarding experience:** {{onboarding_experience}}

**Upsell / cross-sell mechanics:** {{upsell_cross_sell}}

**Community & loyalty:** {{community_loyalty}}

---

## 4. Landing Page Wireframe (Hero Page)

{{landing_page_wireframe_block}}

---

## 5. Email Sequences

### Welcome / Indoctrination (3–5 Emails)

{{welcome_sequence_block}}

### Conversion / Offer Push (3–5 Emails)

{{conversion_sequence_block}}

### Win-back / Re-activation (3–5 Emails)

{{winback_sequence_block}}

---

## 6. 30-Day Full-Funnel Content Calendar

{{calendar_full_funnel_30_day_table}}

---

## 7. Ad & Reel Script Bank (15 Concepts)

{{ad_reel_scripts_block}}

---

## 8. CTA Library

{{cta_library_block}}

---

## 9. Hashtag Bank (120 Tags)

{{hashtags_full_funnel_block}}

---

## 10. KPI Dashboard & Optimization Plan

**Acquisition KPIs:** {{acquisition_kpis}}

**Conversion KPIs:** {{conversion_kpis}}

**Retention KPIs:** {{retention_kpis}}

**Weekly Optimization Ritual:** {{optimization_ritual}}

---

*This Full-Funnel Growth Suite maps {{brand_name}}'s entire path from traffic to repeat purchase, with creative, messaging, and automations aligned at every stage.*
""",
    "launch_gtm_pack": r"""# {{brand_name}} – Launch & GTM Pack
### Go-To-Market Strategy for {{product_name}}

---

## 1. GTM Snapshot

- **Product:** {{product_name}}
- **Category:** {{category}}
- **Launch Region(s):** {{regions}}
- **Ideal Customer:** {{ideal_customer}}
- **Launch Timing:** {{launch_timing}}
- **Key Objectives:** {{launch_objectives}}

---

## 2. Positioning & Story

**Positioning Statement:** {{positioning_statement}}

**Benefit Ladder:** {{benefit_ladder}}

**Core Brand Story:** {{brand_story}}

---

## 3. Market & Competitor Landscape

{{launch_competitor_block}}

---

## 4. GTM Framework

**Who:** {{gtm_who}}

**What:** {{gtm_what}}

**Where:** {{gtm_where}}

**Why Now:** {{gtm_why_now}}

**How (Channels & Tactics):** {{gtm_how}}

---

## 5. Launch Campaign

**Campaign name:** {{campaign_name}}

**Core idea:** {{campaign_core_idea}}

**Main message:** {{campaign_main_message}}

**Supporting angles:** {{campaign_supporting_angles}}

---

## 6. Influencer & Partnership Strategy

{{influencer_strategy_block}}

---

## 7. 30-Day Launch Calendar (Pre, During, Post)

{{launch_calendar_30_day_table}}

---

## 8. Launch Assets

**Landing page:** {{launch_landing_page}}

**Email sequences:** {{launch_emails_summary}}

**Social creatives & captions:** {{launch_social_assets}}

**PR / announcement angles:** {{launch_pr_angles}}

---

## 9. KPIs & Milestones

{{launch_kpis_milestones_block}}

---

*This Launch & GTM Pack ensures {{product_name}} enters the market with clarity, momentum, and a repeatable framework for future launches.*
""",
    "brand_turnaround_lab": r"""# {{brand_name}} – Brand Turnaround Lab
### From Decline to Relevance

---

## 1. Current Brand Diagnosis

- **Perception Today:** {{perception_today}}
- **Key Complaints / Issues:** {{brand_issues}}
- **Internal Constraints:** {{internal_constraints}}
- **Strengths to Protect:** {{brand_strengths}}

---

## 2. Competitor & Market Reality

{{turnaround_competitor_block}}

---

## 3. Root Cause Analysis

**Category problems:** {{category_problems}}

**Brand-specific issues:** {{brand_specific_issues}}

**Experience gaps:** {{experience_gaps}}

---

## 4. New Positioning & Promise

**Repositioning Statement:** {{repositioning_statement}}

**New Brand Promise:** {{new_brand_promise}}

**Proof Points:** {{new_proof_points}}

---

## 5. Voice, Tone & Visual Reset

### Voice & Tone:

- **Old:** {{old_tone}}
- **New:** {{new_tone}}

### Visual Direction:

- **Colors:** {{new_colors}}
- **Fonts:** {{new_fonts}}
- **Imagery:** {{new_imagery}}

---

## 6. Reputation Repair & Response Templates

{{reputation_templates_block}}

---

## 7. 30-Day Brand Repair Plan

{{turnaround_30_day_plan_table}}

---

## 8. Social Content Examples (New Tone)

{{turnaround_captions_block}}

---

## 9. Hashtag & Community Plan

{{turnaround_hashtags_block}}

---

## 10. Monitoring & Guardrails

**What to track weekly:** {{monitoring_metrics}}

**Do / Don't list for the team:** {{do_dont_list}}

---

*This Brand Turnaround Lab gives {{brand_name}} a practical path from damaged perception to renewed trust and relevance.*
""",
    "retention_crm_booster": r"""# {{brand_name}} – Retention & CRM Booster
### Turning Buyers into Lifelong Customers

---

## 1. Customer Snapshot

- **Segments:** {{customer_segments}}
- **Purchase Patterns:** {{purchase_patterns}}
- **Churn Risks:** {{churn_risks}}
- **Highest LTV Group:** {{highest_ltv_group}}

---

## 2. Customer Journey Mapping

{{customer_journey_block}}

---

## 3. Email Automation Flows

### A. Onboarding / Welcome

{{crm_welcome_flow_block}}

### B. Post-Purchase

{{crm_post_purchase_flow_block}}

### C. Win-Back / Re-activation

{{crm_winback_flow_block}}

---

## 4. SMS & WhatsApp Templates

{{crm_sms_templates_block}}

---

## 5. Loyalty & Referral Concepts

{{loyalty_referral_block}}

---

## 6. 30-Day Customer Love Calendar

{{crm_30_day_calendar_table}}

---

## 7. Offer & Promotion Strategy

{{offer_strategy_block}}

---

## 8. KPI Dashboard

- **Repeat rate:** {{kpi_repeat_rate}}
- **Average order value:** {{kpi_aov}}
- **LTV:** {{kpi_ltv}}
- **Churn:** {{kpi_churn}}

---

*This Retention & CRM Booster is designed to make every new buyer more profitable over time for {{brand_name}}.*
""",
    "performance_audit_revamp": r"""# {{brand_name}} – Performance Audit & Revamp
### What's Working, What's Wasted, What to Fix First

---

## 1. Account & Funnel Snapshot

- **Platforms audited:** {{platforms_audited}}
- **Period analysed:** {{period_analysed}}
- **Monthly ad spend:** {{monthly_spend}}
- **Main objectives:** {{audit_objectives}}

---

## 2. High-Level Findings

**Top strengths:** {{top_strengths}}

**Key issues:** {{key_issues}}

**Biggest quick wins:** {{quick_wins}}

---

## 3. Channel-by-Channel Audit

{{channel_audit_block}}

---

## 4. Creative Performance Review

{{creative_review_block}}

---

## 5. Funnel & Landing Page Review

{{funnel_review_block}}

---

## 6. Priority Fix List (Top 15)

{{priority_fix_list_block}}

---

## 7. 30-Day Revamp Plan

{{revamp_30_day_plan_table}}

---

## 8. New Creative & Messaging Directions

{{revamp_creative_block}}

---

## 9. KPI Targets & Reporting

{{revamp_kpi_block}}

---

*This Performance Audit & Revamp equips {{brand_name}} with a clear, prioritized roadmap to stop waste and scale what works.*
""",
    # ============================================================
    # STRATEGY + CAMPAIGN PACK TEMPLATES (Tier System)
    # (Basic, Standard, Premium, Enterprise)
    # Each pack has a dedicated template matching its section count & complexity
    # ============================================================
    "strategy_campaign_basic": r"""# {{brand_name}} – Strategy + Campaign Plan (Quick)
### Fast-Track Campaign Strategy – {{campaign_name}}

---

## 1. Overview

{{overview}}

---

## 2. Core Campaign Idea

{{core_campaign_idea}}

---

## 3. Messaging Framework

{{messaging_framework}}

---

## 4. Audience & Segments

{{audience_segments}}

---

## 5. 30-Day Action Plan

{{detailed_30_day_calendar}}

---

## Final Summary

{{final_summary}}

---

*This quick-turnaround strategy gives {{brand_name}} a clear, executable plan for {{campaign_name}} launch and execution.*
""",
    "strategy_campaign_premium": r"""# {{brand_name}} – Strategy + Campaign Plan (Premium)
### Comprehensive Multi-Channel Campaign Strategy – {{campaign_name}}

---

## 1. Campaign Overview

{{overview}}

---

## 2. Campaign Objective & Success Criteria

{{campaign_objective}}

---

## 3. Core Campaign Idea

{{core_campaign_idea}}

---

## 4. Value Proposition & Positioning

{{value_proposition_map}}

---

## 5. Messaging Framework

{{messaging_framework}}

---

## 6. Channel Plan & Platform Strategy

{{channel_plan}}

---

## 7. Audience Segments & Targeting

{{audience_segments}}

---

## 8. Buyer Personas

{{persona_cards}}

---

## 9. Creative Direction

{{creative_direction}}

---

## 10. Creative Territories & Variations

{{creative_territories}}

---

## 11. Copy Variants & Key Messages

{{copy_variants}}

---

## 12. Influencer & Partnership Strategy

{{influencer_strategy}}

---

## 13. UGC & Community Building

{{ugc_and_community_plan}}

---

## 14. Promotions & Special Offers

{{promotions_and_offers}}

---

## 15. Funnel Breakdown (Awareness → Conversion)

{{funnel_breakdown}}

---

## 16. Awareness Stage Strategy

{{awareness_strategy}}

---

## 17. Consideration Stage Strategy

{{consideration_strategy}}

---

## 18. Conversion Stage Strategy

{{conversion_strategy}}

---

## 19. Detailed 30-Day Content Calendar

{{detailed_30_day_calendar}}

---

## 20. Email & CRM Automation Flows

{{email_and_crm_flows}}

---

## 21. SMS & WhatsApp Strategy

{{sms_and_whatsapp_strategy}}

---

## 22. Paid Advertising Concepts

{{ad_concepts}}

---

## 23. Remarketing & Conversion Strategy

{{remarketing_strategy}}

---

## 24. KPI & Budget Allocation Plan

{{kpi_and_budget_plan}}

---

## 25. Execution Roadmap & Timeline

{{execution_roadmap}}

---

## 26. Post-Campaign Analysis Framework

{{post_campaign_analysis}}

---

## 27. Optimization Opportunities

{{optimization_opportunities}}

---

## 28. Final Summary & Recommended Next Steps

{{final_summary}}

---

*This comprehensive Premium strategy positions {{brand_name}} for significant growth through integrated, multi-channel execution and continuous optimization.*
""",
    "strategy_campaign_enterprise": r"""# {{brand_name}} – Strategy + Campaign Plan (Enterprise)
### Consulting-Grade Strategic Campaign Framework – {{campaign_name}}

---

## 1. Executive Summary

{{overview}}

---

## 2. Industry & Market Landscape

{{industry_landscape}}

---

## 3. Market Analysis & Trends

{{market_analysis}}

---

## 4. Competitive Intelligence & Positioning

{{competitor_analysis}}

---

## 5. Customer Insights & Pain Points

{{customer_insights}}

---

## 6. Campaign Objectives & Success Criteria

{{campaign_objective}}

---

## 7. Core Campaign Idea & Strategic Narrative

{{core_campaign_idea}}

---

## 8. Value Proposition & Brand Promise Mapping

{{value_proposition_map}}

---

## 9. Brand Positioning & Differentiation

{{brand_positioning}}

---

## 10. Messaging Architecture & Framework

{{messaging_framework}}

---

## 11. Integrated Channel Plan

{{channel_plan}}

---

## 12. Audience Segmentation & Targeting Strategy

{{audience_segments}}

---

## 13. Detailed Buyer Personas & Decision Journeys

{{persona_cards}}

---

## 14. Customer Journey Mapping

{{customer_journey_map}}

---

## 15. Creative Direction & Brand Expression

{{creative_direction}}

---

## 16. Creative Territories & Strategic Variations

{{creative_territories}}

---

## 17. Copy Architecture & Message Variants

{{copy_variants}}

---

## 18. Influencer & Strategic Partnership Framework

{{influencer_strategy}}

---

## 19. User-Generated Content & Community Strategy

{{ugc_and_community_plan}}

---

## 20. Promotional & Offer Architecture

{{promotions_and_offers}}

---

## 21. Multi-Stage Funnel Breakdown

{{funnel_breakdown}}

---

## 22. Awareness Stage Strategy & Tactics

{{awareness_strategy}}

---

## 23. Consideration Stage Strategy & Tactics

{{consideration_strategy}}

---

## 24. Conversion Stage Strategy & Tactics

{{conversion_strategy}}

---

## 25. Retention & Expansion Strategy

{{retention_strategy}}

---

## 26. Detailed 30-Day Integrated Calendar

{{detailed_30_day_calendar}}

---

## 27. Email & CRM Automation Architecture

{{email_and_crm_flows}}

---

## 28. SMS & WhatsApp Engagement Strategy

{{sms_and_whatsapp_strategy}}

---

## 29. Paid Media & Advertising Strategy

{{ad_concepts}}

---

## 30. Remarketing & Conversion Optimization

{{remarketing_strategy}}

---

## 31. Measurement Framework & KPI Dashboard

{{measurement_framework}}

---

## 32. Budget Allocation & Financial Planning

{{kpi_and_budget_plan}}

---

## 33. Risk Assessment & Mitigation Strategies

{{risk_assessment}}

---

## 34. Implementation Roadmap & Timeline

{{execution_roadmap}}

---

## 35. Post-Campaign Analysis & Learning Framework

{{post_campaign_analysis}}

---

## 36. Optimization Opportunities & Scale Levers

{{optimization_opportunities}}

---

## 37. Strategic Recommendations & Future Roadmap

{{strategic_recommendations}}

---

## 38. C-Suite Summary & Business Impact

{{cxo_summary}}

---

## 39. Final Summary & Commitment to Execution

{{final_summary}}

---

*This Enterprise-grade strategic campaign plan provides {{brand_name}} with a comprehensive, integrated framework designed for executive decision-making, multi-team coordination, and measurable business impact. Built on industry best practices, customer insights, and competitive intelligence, this strategy ensures alignment across all functions and channels.*
""",
    # ============================================================
    # 9. PR & Reputation Pack
    # ============================================================
    "pr_reputation_pack": r"""# {{brand_name}} – PR & Reputation Strategy

---

## 1. Brand Overview

{{overview}}

---

## 2. Current Reputation Assessment

{{reputation_assessment}}

---

## 3. Key Messages & Narrative

{{key_messages}}

---

## 4. Media Strategy & Outreach

{{media_strategy}}

---

## 5. Crisis Communication Playbook

{{crisis_playbook}}

---

## 6. Social Listening & Monitoring

{{social_listening}}

---

## 7. Influencer & Advocate Program

{{influencer_strategy}}

---

## 8. Content Calendar (PR & Comms)

{{pr_content_calendar}}

---

## 9. Measurement & KPIs

{{pr_kpis}}

---

## 10. Executive Summary

{{pr_summary}}

---

*This PR and Reputation Strategy provides {{brand_name}} with a comprehensive framework to build positive brand perception, manage stakeholder relationships, and protect reputation in an always-on media environment.*
""",
    # ============================================================
    # 10. Always-On Content Engine
    # ============================================================
    "always_on_content_engine": r"""# {{brand_name}} – Always-On Content Engine

---

## 1. Brand & Audience Foundation

{{overview}}

---

## 2. Content Strategy & Pillars

{{content_pillars}}

---

## 3. Editorial Calendar (30-Day Rolling)

{{editorial_calendar}}

---

## 4. Content Production Playbook

{{production_playbook}}

---

## 5. Social Media Distribution Strategy

{{distribution_strategy}}

---

## 6. Engagement & Community Management

{{engagement_framework}}

---

## 7. Content Performance Benchmarks

{{performance_benchmarks}}

---

## 8. Optimization & Iteration Process

{{optimization_process}}

---

## 9. Resource & Team Requirements

{{resource_requirements}}

---

## 10. Strategic Summary

{{content_engine_summary}}

---

*This Always-On Content Engine equips {{brand_name}} with a sustainable, scalable framework for consistent, high-quality content production that builds audience loyalty and drives continuous business results.*
""",
}


def get_wow_template(package_key: str) -> str:
    """
    Safely fetch a WOW template by key.

    Returns a sensible default message if the key is unknown, so callers
    never explode with a KeyError.
    """
    if package_key in WOW_TEMPLATES:
        return WOW_TEMPLATES[package_key]

    return (
        "# WOW Template Not Found\n\n"
        f"No WOW template is defined for package key: `{package_key}`.\n"
        "Please configure it in aicmo/presets/wow_templates.py."
    )
