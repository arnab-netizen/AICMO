# PDF Pack Mappings Overview

**Date**: 2024-12-04  
**Purpose**: Document all WOW pack → PDF template mappings and section-to-field relationships

---

## Pack → PDF Template Mapping

| Pack Key | PDF Template | Status |
|----------|--------------|--------|
| `quick_social_basic` | `quick_social_basic.html` | ✅ **VERIFIED (30.9 KB, 8 pages)** |
| `strategy_campaign_standard` | `campaign_strategy.html` | ✅ **VERIFIED (38.1 KB, 12 pages)** |
| `strategy_campaign_basic` | `campaign_strategy.html` | ✅ **VERIFIED (26.0 KB, 7 pages)** |
| `strategy_campaign_premium` | `campaign_strategy.html` | ✅ **VERIFIED (38.1 KB, 12 pages)** |
| `strategy_campaign_enterprise` | `campaign_strategy.html` | ✅ **VERIFIED (38.2 KB, 12 pages)** |
| `full_funnel_growth_suite` | `full_funnel_growth.html` | ✅ **VERIFIED (58.2 KB, 19 pages)** |
| `launch_gtm_pack` | `launch_gtm.html` | ✅ **VERIFIED (39.7 KB, 10 pages)** |
| `brand_turnaround_lab` | `brand_turnaround.html` | ✅ **VERIFIED (33.0 KB, 7 pages)** |
| `retention_crm_booster` | `retention_crm.html` | ✅ **VERIFIED (24.5 KB, 3 pages)** |
| `performance_audit_revamp` | `performance_audit.html` | ✅ **VERIFIED (22.0 KB, 2 pages)** |

---

## Section ID → Template Field Mappings

### Quick Social Basic (8 sections) ✅

**Pack Sections** (from `package_presets.py`):
- overview
- messaging_framework
- detailed_30_day_calendar
- content_buckets
- hashtag_strategy
- kpi_plan_light
- execution_roadmap
- final_summary

**PDF Template Fields** (`quick_social_basic.html`):
- `overview_html`
- `audience_segments_html` (not in pack - expected empty)
- `messaging_framework_html`
- `content_buckets_html`
- `calendar_html`
- `creative_direction_html` (not in pack - expected empty)
- `hashtags_html`
- `platform_guidelines_html` (not in pack - expected empty)
- `kpi_plan_html` (combines kpi_plan_light + execution_roadmap)
- `final_summary_html`

**Mapping**:
```python
QUICK_SOCIAL_SECTION_MAP = {
    "overview": "overview_html",
    "messaging_framework": "messaging_framework_html",
    "detailed_30_day_calendar": "calendar_html",
    "content_buckets": "content_buckets_html",
    "hashtag_strategy": "hashtags_html",
    "kpi_plan_light": "kpi_plan_html",
    "execution_roadmap": "kpi_plan_html",  # Merged with kpi_plan_light
    "final_summary": "final_summary_html",
}
```

---

### Strategy + Campaign Standard (17 sections) 🔄

**Pack Sections** (from `package_presets.py`):
- overview
- campaign_objective
- core_campaign_idea
- messaging_framework
- channel_plan
- audience_segments
- persona_cards
- creative_direction
- influencer_strategy
- promotions_and_offers
- detailed_30_day_calendar
- email_and_crm_flows
- ad_concepts
- kpi_and_budget_plan
- execution_roadmap
- post_campaign_analysis
- final_summary

**PDF Template Fields** (`campaign_strategy.html`):
- `brand_name`, `campaign_title`, `campaign_duration` (metadata)
- `objectives_html`
- `core_campaign_idea_html`
- `competitor_snapshot` (structured data - may skip in section-based approach)
- `channel_plan_html`
- `audience_segments_html`
- `personas` (structured data - array)
- `roi_model` (structured data - may skip)
- `creative_direction_html`
- `brand_identity` (structured data - color swatches, may skip)
- `calendar_html`
- `ad_concepts_html`
- `kpi_budget_html`
- `execution_html`
- `post_campaign_html`
- `final_summary_html`

**Mapping Strategy**:
```python
STRATEGY_CAMPAIGN_SECTION_MAP = {
    "overview": "objectives_html",  # Or create separate overview_html?
    "campaign_objective": "objectives_html",
    "core_campaign_idea": "core_campaign_idea_html",
    "messaging_framework": "objectives_html",  # May need to merge or create messaging_html
    "channel_plan": "channel_plan_html",
    "audience_segments": "audience_segments_html",
    "persona_cards": "personas",  # Structured - needs special handling
    "creative_direction": "creative_direction_html",
    "influencer_strategy": "channel_plan_html",  # Merge into channel
    "promotions_and_offers": "core_campaign_idea_html",  # Merge into big idea
    "detailed_30_day_calendar": "calendar_html",
    "email_and_crm_flows": "channel_plan_html",  # Merge into channel
    "ad_concepts": "ad_concepts_html",
    "kpi_and_budget_plan": "kpi_budget_html",
    "execution_roadmap": "execution_html",
    "post_campaign_analysis": "post_campaign_html",
    "final_summary": "final_summary_html",
}
```

**Notes**:
- Several sections may merge into same template fields (influencer→channel, promotions→big_idea)
- Persona_cards needs structured data handling (not just markdown→HTML)
- Template has fewer fields than pack has sections - intelligent merging required

---

### Full-Funnel Growth Suite (23 sections) 🔄

**Pack Sections**:
- overview, market_landscape, competitor_analysis, funnel_breakdown
- audience_segments, persona_cards, value_proposition_map, messaging_framework
- awareness_strategy, consideration_strategy, conversion_strategy, retention_strategy
- landing_page_blueprint, email_automation_flows, remarketing_strategy
- ad_concepts_multi_platform, creative_direction, full_30_day_calendar
- kpi_and_budget_plan, measurement_framework, execution_roadmap
- optimization_opportunities, final_summary

**PDF Template Fields** (`full_funnel_growth.html`):
- `market_landscape_html`
- `competitor_analysis_html`
- `funnel_breakdown_html`
- `audience_segments_html`
- `personas` (structured)
- `value_proposition_html`
- `messaging_framework_html`
- `awareness_strategy_html`, `consideration_strategy_html`, `conversion_strategy_html`, `retention_strategy_html`
- `landing_page_html`
- `email_flows_html`
- `remarketing_html`
- `ad_concepts_html`
- `creative_direction_html`
- `calendar_html`
- `kpi_budget_html`
- `measurement_html`
- `execution_html`
- `optimization_html`
- `final_summary_html`

**Good news**: Template fields closely match section IDs for this pack!

---

### Launch & GTM Pack (13 sections) 🔄

**Pack Sections**:
- overview, market_landscape, product_positioning, messaging_framework
- launch_phases, channel_plan, audience_segments, creative_direction
- launch_campaign_ideas, content_calendar_launch, ad_concepts
- execution_roadmap, final_summary

**PDF Template Fields** (`launch_gtm.html`):
- `market_landscape_html`
- `positioning_html`
- `messaging_framework_html`
- `launch_phases_html`
- `channel_plan_html`
- `audience_segments_html`
- `personas` (structured)
- `creative_direction_html`
- `campaign_ideas_html`
- `calendar_html`
- `ad_concepts_html`
- `execution_html`
- `final_summary_html`

---

### Brand Turnaround Lab (14 sections) 🔄

**Pack Sections**:
- overview, brand_audit, customer_insights, competitor_analysis
- problem_diagnosis, new_positioning, messaging_framework, creative_direction
- channel_reset_strategy, reputation_recovery_plan, promotions_and_offers
- 30_day_recovery_calendar, execution_roadmap, final_summary

**PDF Template**: `brand_turnaround.html` (need to inspect)

---

### Retention & CRM Booster (14 sections) 🔄

**Pack Sections**:
- overview, customer_segments, persona_cards, customer_journey_map
- churn_diagnosis, email_automation_flows, sms_and_whatsapp_flows
- loyalty_program_concepts, winback_sequence, post_purchase_experience
- ugc_and_community_plan, kpi_plan_retention, execution_roadmap, final_summary

**PDF Template**: `retention_crm.html` (need to inspect)

---

### Performance Audit & Revamp (16 sections) 🔄

**Pack Sections**:
- overview, account_audit, campaign_level_findings, creative_performance_analysis
- audience_analysis, funnel_breakdown, competitor_benchmark, problem_diagnosis
- revamp_strategy, new_ad_concepts, creative_direction, conversion_audit
- remarketing_strategy, kpi_reset_plan, execution_roadmap, final_summary

**PDF Template**: `performance_audit.html` (need to inspect)

---

## Implementation Strategy

### Phase 1: Core Infrastructure (STEP 1)
- Extend `PACK_SECTION_MAPS` dict with all pack mappings
- Refactor `build_pdf_context_for_wow_package()` to use central map
- Keep Quick Social logic backward compatible

### Phase 2: Generic Dev Script (STEP 2)
- Create `scripts/dev_compare_pdf_for_pack.py`
- Accepts `--pack` argument
- Generates sections directly from stubs/generators
- Outputs pack-specific PDF: `tmp_demo_{pack_key}.pdf`

### Phase 3: Per-Pack Verification (STEP 3)
- For each pack with PDF template:
  - Verify stub coverage for all sections
  - Run dev script
  - Inspect PDF (size, pages, text extraction)
- Fix any missing stubs or mappings

### Phase 4: Cleanup & Documentation (STEP 4)
- Remove debug logging
- Document verified packs in this file
- Create final status report

---

## Stub Coverage Status

Will be updated as we verify each pack's stub implementations.

**Quick Social**: ✅ All 8 sections have stubs  
**Strategy Campaign Standard**: 🔄 To verify  
**Strategy Campaign Premium**: 🔄 To verify  
**Strategy Campaign Enterprise**: 🔄 To verify  
**Full-Funnel Growth**: 🔄 To verify  
**Launch GTM**: 🔄 To verify  
**Brand Turnaround**: 🔄 To verify  
**Retention CRM**: 🔄 To verify  
**Performance Audit**: 🔄 To verify

---

## PDF Generation Verification

Will track PDF output metrics for each pack.

| Pack | PDF Size | Pages | Sections Visible | Status |
|------|----------|-------|------------------|--------|
| quick_social_basic | 31.8 KB | 8 | 8/8 (100%) | ✅ |
| strategy_campaign_standard | TBD | TBD | TBD | 🔄 |
| strategy_campaign_premium | TBD | TBD | TBD | 🔄 |
| full_funnel_growth_suite | TBD | TBD | TBD | 🔄 |
| launch_gtm_pack | TBD | TBD | TBD | 🔄 |
| brand_turnaround_lab | TBD | TBD | TBD | 🔄 |
| retention_crm_booster | TBD | TBD | TBD | 🔄 |
| performance_audit_revamp | TBD | TBD | TBD | 🔄 |

---

**Last Updated**: 2024-12-04  
**Next Review**: After STEP 3 completion
