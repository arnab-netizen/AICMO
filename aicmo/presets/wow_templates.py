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

## 1. Brand & Audience Snapshot

- **Brand:** {{brand_name}}
- **Category:** {{category}}
- **Location / Markets:** {{markets}}
- **Primary Audience:** {{primary_audience}}
- **Secondary Audience:** {{secondary_audience}}
- **Current Positioning:** {{current_positioning}}
- **Desired Positioning:** {{desired_positioning}}
- **Key Business Objective:** {{business_objective}}

---

## 2. Insight & Core Challenge

> What problem are we really solving?

- **Audience Insight:** {{audience_insight}}
- **Market Insight:** {{market_insight}}
- **Primary Challenge:** {{primary_challenge}}
- **Success Looks Like:** {{definition_of_success}}

---

## 3. Creative & Visual Direction

**Tone & Personality:** {{tone_personality}}

**Visual Direction:**
- Colors: {{colors_summary}}
- Fonts: {{fonts_summary}}
- Photography style: {{photo_style}}
- References / Mood: {{visual_references}}

---

## 4. Competitor Benchmark (3 Key Competitors)

{{competitor_benchmark_block}}

> Key white space opportunity: **{{whitespace_opportunity}}**

---

## 5. Campaign Strategy Framework (e.g., AIDA)

**Attention:** {{strategy_attention}}  
**Interest:** {{strategy_interest}}  
**Desire:** {{strategy_desire}}  
**Action:** {{strategy_action}}

Core Campaign Idea:  
> **{{big_idea_tagline}}**

Supporting Angles:
- {{angle_1}}
- {{angle_2}}
- {{angle_3}}

---

## 6. Channel & Content System

**Primary Channels:** {{primary_channels}}  
**Support Channels:** {{support_channels}}

**Content Pillars:**
{{content_pillars_block}}

---

## 7. 30-Day Campaign Calendar

{{calendar_30_day_table}}

---

## 8. Sample Captions & Hooks

**Hero Posts (5):**  
{{hero_captions_block}}

**Supporting Posts (10):**  
{{supporting_captions_block}}

**Carousel / Long-form Captions (5):**  
{{carousel_captions_block}}

---

## 9. Reels & Video Concepts (10)

{{reel_concepts_block}}

---

## 10. Hashtag Bank (90 Tags)

- **Brand & Category:** {{hashtags_brand_category}}
- **Occasion / Campaign:** {{hashtags_occasion}}
- **Audience & Community:** {{hashtags_audience}}
- **Tiered mix:** {{hashtags_tier_mix}}

---

## 11. KPIs & Measurement Plan

- **Primary KPI(s):** {{primary_kpis}}
- **Secondary KPI(s):** {{secondary_kpis}}
- **Checkpoints:** {{checkpoints}}
- **Reporting Cadence:** {{reporting_cadence}}

---

*This Strategy + Campaign Pack gives {{brand_name}} a clear, executable roadmap that aligns creative, channels, and KPIs around {{campaign_name}}.*
""",
    "full_funnel_premium": r"""# {{brand_name}} – Full-Funnel Growth Suite (Premium)
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
    "launch_gtm": r"""# {{brand_name}} – Launch & GTM Pack
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
    "brand_turnaround": r"""# {{brand_name}} – Brand Turnaround Lab
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
    "retention_crm": r"""# {{brand_name}} – Retention & CRM Booster
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
    "performance_audit": r"""# {{brand_name}} – Performance Audit & Revamp
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
