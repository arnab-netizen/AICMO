# Strategy + Campaign Pack Sections Analysis

## Overview
This document maps where Strategy + Campaign pack sections are generated in the codebase and identifies which sections contain SaaS-specific terms and length constraints.

---

## Strategy + Campaign Pack Composition

### Standard Pack (17 sections)
1. overview
2. campaign_objective
3. core_campaign_idea
4. messaging_framework
5. channel_plan
6. audience_segments
7. persona_cards
8. creative_direction
9. influencer_strategy
10. promotions_and_offers
11. detailed_30_day_calendar
12. email_and_crm_flows
13. ad_concepts
14. kpi_and_budget_plan
15. execution_roadmap
16. post_campaign_analysis
17. final_summary

### Premium Pack (28 sections) - Includes all above plus:
- value_proposition_map
- creative_territories
- copy_variants
- ugc_and_community_plan
- funnel_breakdown
- awareness_strategy
- consideration_strategy
- conversion_strategy
- sms_and_whatsapp_strategy
- remarketing_strategy
- optimization_opportunities

### Enterprise Pack (39 sections) - Includes all above plus:
- industry_landscape
- market_analysis
- competitor_analysis
- customer_insights
- brand_positioning
- customer_journey_map
- measurement_framework
- risk_assessment
- strategic_recommendations
- cxo_summary

---

## Section Generators Detailed Analysis

### 1. **overview** (Strategy section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_overview()`  
**Line Range:** 683-745  
**Pack Key:** Included in ALL packs (quick_social_basic, strategy_campaign_standard, etc.)

**Current Content:**
- Brand name, industry, primary goal
- Industry-specific description using vocabulary profiles
- Strategic approach with platform consistency, metrics tracking, customer stories, optimization

**SaaS-Specific Terms:** ✅ NONE (generic, non-SaaS focused)

**Length Constraints:** 
- Expected: 150-400 words (defined in layer3_soft_validators.py:169)
- Current actual: ~250 words

**Notes:**
- ✅ Uses industry vocabulary from profiles (e.g., "third place" for coffeehouse)
- ✅ Non-SaaS friendly
- Falls back to generic industry description if no industry profile

---

### 2. **campaign_objective** (Campaign section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_campaign_objective()`  
**Line Range:** 746-850

**Current Content:**
- Primary objective section
- Secondary objectives (lead generation, retention)
- Time horizon and timeline structure
- Success metrics (engagement rate, conversion benchmarks, CPA thresholds)

**SaaS-Specific Terms:** ✅ NONE (all generic metrics)

**Length Constraints:**
- Expected: 100-250 words (defined in layer3_soft_validators.py:169)
- Current actual: ~350 words

**Special Features:**
- Has optional CreativeService polish for "strategy" section type
- Template-based with LLM enhancement capability

**Notes:**
- ⚠️ Current output may be longer than 250-word constraint
- ✅ No SaaS-specific language
- Uses engagement rate >2%, conversion benchmarks, CPA metrics

---

### 3. **core_campaign_idea** (Strategy/Campaign section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_core_campaign_idea()`  
**Line Range:** 851-900+ (continues beyond)

**Current Content:**
- Big Idea positioning statement
- Creative Territory ("From Chaos to Clarity" transformation narrative)
- Why It Works section with proof-driven narrative focus

**SaaS-Specific Terms:** ✅ NONE (all generic)

**Length Constraints:** No explicit constraint defined

**Special Features:**
- Optional CreativeService polish for high-value narrative
- Before/after storytelling approach
- Emphasizes proof-driven messaging

---

### 4. **messaging_framework** (Strategy section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_messaging_framework()`  
**Line Range:** 871-950+

**Current Content:**
- Promise/brand positioning statement
- Key messages (brand-appropriate, industry-specific)
- Uses MarketingPlanView pyramid data

**SaaS-Specific Terms:** ✅ NONE (avoids agency language)

**Length Constraints:** No explicit constraint defined

**Special Features:**
- ✅ Production-verified for Quick Social Pack
- Uses industry-specific themes (e.g., coffeehouse vocabulary)
- Avoids agency jargon

**Notes:**
- Important: Don't modify without running specific test suite

---

### 5. **execution_roadmap** (Next Steps/Action Plan section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_execution_roadmap()`  
**Line Range:** 1950-2100+

**Current Content - Two Variants:**

**A) Performance Audit Pack:**
- 30/60/90-day sprint structure
- Week-by-week breakdown with specific actions
- Detailed tables with outcomes and metrics
- Very long (~2000+ words)

**B) SaaS Pack:**
- Phase 1: Pre-Launch Foundation (Days 1-14)
  - ❌ CONTAINS SAAS-SPECIFIC TERMS:
    - "ProductHunt" 
    - "TechCrunch"
    - "G2 rating"
    - "$50K MRR by Month 3"
    - Tech-focused influencers
    - Demo materials
    - Early access
- Success metrics: "100+ customers Month 1, 4.5+ G2 rating, $50K MRR"

**C) Non-SaaS Pack:**
- Phase 1: Pre-Launch Foundation (Days 1-14)
- ✅ Generic launch roadmap (no ProductHunt, no tech bias)
- Email waitlist via LinkedIn, partnerships, directories
- Email announcement at launch

**Length Constraints:** No explicit max constraint

**SaaS Detection:**
- Uses `infer_is_saas(req.brief)` function (line 659-672)
- Keyword detection: "saas", "software", "platform", "app", "subscription", "b2b saas", "cloud", "api"

**❌ NEEDS UPDATE:**
- Remove ProductHunt references (lines 2027, 2030, 2033)
- Remove G2 and MRR references (line 2043)
- Remove tech-specific language throughout SaaS variant

---

### 6. **kpi_and_budget_plan** (KPI/Framework section)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_kpi_and_budget_plan()`  
**Line Range:** 1897-1950

**Current Content:**
- Primary KPIs (reach, engagement, lead generation, conversion)
- Budget allocation (40% content, 35% paid, 15% email, 10% creative)
- Channel breakdown
- Testing vs Always-On split
- Performance guardrails
- Success metrics

**SaaS-Specific Terms:** ✅ NONE (all generic metrics)

**Length Constraints:** No explicit constraint defined

**Notes:**
- Generic metrics applicable to all business types
- 3.5:1 ROAS minimum mentioned but not SaaS-specific

---

### 7. **brand_positioning** (Strategy section - Enterprise only)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_brand_positioning()`  
**Line Range:** 3427-3480

**Current Content:**
- Uses structured brand strategy generator
- JSON-validated output
- Markdown conversion from strategy dict

**SaaS-Specific Terms:** ✅ NONE (generic strategy framework)

**Length Constraints:** No explicit constraint defined

**Special Features:**
- Delegates to `generate_brand_strategy_block()` (backend/generators/brand_strategy_generator.py)
- Optional CreativeService polish
- Stores structured block in `req.brand_strategy_block` for downstream rendering

---

### 8. **strategic_recommendations** (Strategy section - Enterprise only)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_strategic_recommendations()`  
**Line Range:** 3619-3750

**Current Content:**
- Strategic Priorities (8 high-impact initiatives)
- Implementation Roadmap (3 phases: Foundation, Scale, Optimize)
- Key Execution Principles
- Success Criteria (revenue, awareness, pipeline, efficiency, advocacy)

**SaaS-Specific Terms:** ✅ NONE (all generic strategy language)

**Length Constraints:** No explicit constraint defined

**Notes:**
- Generic framework applicable to all industries
- C-suite ready language

---

### 9. **kpi_plan_retention** (KPI section - Retention pack only)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_kpi_plan_retention()`  
**Line Range:** 5570-5650+

**Special Content:**
- Contains ❌ SaaS-SPECIFIC TERMS:
  - MRR (Monthly Recurring Revenue)
  - NRR (Net Revenue Retention)
  - Churn rate
  - Expansion revenue
  - LTV:CAC ratio
  - "Formula: ((Start MRR + Expansion - Downgrades - Churn) / Start MRR) × 100"
  - Beta customers
  - Waitlist

**⚠️ Not in Strategy + Campaign Pack but affects related retention strategies**

---

### 10. **cxo_summary** (Executive section - Enterprise only)
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `_gen_cxo_summary()`  
**Line Range:** 3751-3850+

**Current Content:**
- Executive Summary section
- Context and core strategy
- Expected outcomes (90-day, 6-month, 12-month projections)
- Investment and risk profile

**SaaS-Specific Terms:** ✅ NONE (generic executive language)

**Length Constraints:** No explicit constraint defined

**Notes:**
- C-suite focused
- Contains business metrics but no product-specific terms

---

## Length Constraint Summary

From `/workspaces/AICMO/backend/layers/layer3_soft_validators.py` (line 169):

| Section | Min Words | Max Words | Current | Status |
|---------|-----------|-----------|---------|--------|
| overview | 150 | 400 | ~250 | ✅ OK |
| campaign_objective | 100 | 250 | ~350 | ⚠️ EXCEEDS |
| creatives_headline | 50 | 150 | N/A | N/A |
| strategy | 200 | 500 | Varies | Check |
| social_calendar | 500 | 2000 | N/A | N/A |
| media_plan | 100 | 300 | N/A | N/A |

---

## SaaS-Specific Terms Found

| Location | Terms | Action |
|----------|-------|--------|
| **execution_roadmap()** line 2027-2043 | ProductHunt, Product Hunt, G2, $50K MRR, waitlist, beta, tech media | ❌ UPDATE NEEDED |
| **kpi_plan_retention()** line 5588, 5593, 5613, 5710 | MRR, NRR, expansion revenue, churn, LTV:CAC, beta customers | ✅ OK (Retention pack only) |
| Other sections | NONE FOUND | ✅ OK |

---

## Recommended Updates

### 1. **execution_roadmap()** - PRIORITY HIGH
**File:** `/workspaces/AICMO/backend/main.py`  
**Lines to Update:** 2020-2080

**Changes Needed:**
- [ ] Line 2027: Remove "Product Hunt Ship page" reference
- [ ] Line 2030: Remove "Product Hunt launch page" reference
- [ ] Line 2033: Remove "Product Hunt" from deployment list, replace with "industry directories"
- [ ] Line 2043: Replace "$50K MRR" with "revenue target", replace "G2 rating" with "customer satisfaction score"

**Suggested Generic Alternative:**
```python
# Instead of SaaS-specific metrics
"**Success Metrics:** First 50+ customers, 4.5+ customer satisfaction score, "
"$[revenue_target] monthly revenue by Month 3"
```

### 2. **campaign_objective()** - PRIORITY MEDIUM
**File:** `/workspaces/AICMO/backend/main.py`  
**Lines to Update:** 746-800

**Issue:** Exceeds 250-word constraint (currently ~350 words)

**Changes Needed:**
- [ ] Condense Secondary Objectives section
- [ ] Consolidate Success Metrics into fewer bullets
- [ ] Consider moving detailed budget/KPI specs to separate section

### 3. **Overall SaaS Detection** - PRIORITY MEDIUM
**File:** `/workspaces/AICMO/backend/main.py`  
**Function:** `infer_is_saas()` line 659-672

**Current Logic:**
```python
def infer_is_saas(brief: Any) -> bool:
    """Detect if the brief describes a SaaS/software product."""
    saas_keywords = ["saas", "software", "platform", "app", "subscription", "b2b saas", "cloud", "api"]
    return any(k in text for k in saas_keywords)
```

**Recommendation:** This is working as intended for SaaS-specific packs. For Strategy + Campaign pack, ensure it only applies SaaS-specific language when `"saas"` is explicitly detected in brief.

---

## Generator Registration

**File:** `/workspaces/AICMO/backend/main.py`  
**Lines:** 6761-6850

All Strategy + Campaign sections are properly registered in `SECTION_GENERATORS` dict:

```python
SECTION_GENERATORS: dict[str, callable] = {
    "overview": _gen_overview,
    "campaign_objective": _gen_campaign_objective,
    "core_campaign_idea": _gen_core_campaign_idea,
    "messaging_framework": _gen_messaging_framework,
    "channel_plan": _gen_channel_plan,
    # ... and 40+ more
    "execution_roadmap": _gen_execution_roadmap,
    "post_campaign_analysis": _gen_post_campaign_analysis,
    "final_summary": _gen_final_summary,
}
```

---

## Layer 3 Soft Validators

**File:** `/workspaces/AICMO/backend/layers/layer3_soft_validators.py`  
**Function:** `run_soft_validators()` and `_check_length_bounds()`

- Validates content length against expected_ranges
- Returns quality_score (0-100) with warnings
- Flags: "too_short", "too_long", "has_placeholders", "too_many_cliches"
- Only processes sections with explicit length definitions

---

## Summary Table

| Section | File | Function | Lines | SaaS Terms | Length Constraint | Notes |
|---------|------|----------|-------|-----------|-------------------|-------|
| **overview** | main.py | _gen_overview | 683-745 | ✅ None | 150-400 | ✅ OK, industry vocab used |
| **campaign_objective** | main.py | _gen_campaign_objective | 746-850 | ✅ None | 100-250 | ⚠️ Exceeds (350w) |
| **core_campaign_idea** | main.py | _gen_core_campaign_idea | 851-870 | ✅ None | None | ✅ OK |
| **messaging_framework** | main.py | _gen_messaging_framework | 871-950 | ✅ None | None | ✅ Production-verified |
| **channel_plan** | main.py | _gen_channel_plan | TBD | TBD | None | N/A |
| **audience_segments** | main.py | _gen_audience_segments | TBD | TBD | None | N/A |
| **persona_cards** | main.py | _gen_persona_cards | TBD | TBD | None | N/A |
| **creative_direction** | main.py | _gen_creative_direction | TBD | TBD | None | N/A |
| **influencer_strategy** | main.py | _gen_influencer_strategy | TBD | TBD | None | N/A |
| **promotions_and_offers** | main.py | _gen_promotions_and_offers | TBD | TBD | None | N/A |
| **detailed_30_day_calendar** | main.py | _gen_detailed_30_day_calendar | TBD | TBD | 500-2000 | N/A |
| **email_and_crm_flows** | main.py | _gen_email_and_crm_flows | TBD | TBD | None | N/A |
| **ad_concepts** | main.py | _gen_ad_concepts | TBD | TBD | None | N/A |
| **kpi_and_budget_plan** | main.py | _gen_kpi_and_budget_plan | 1897-1950 | ✅ None | None | ✅ OK, generic metrics |
| **execution_roadmap** | main.py | _gen_execution_roadmap | 1950-2100 | ❌ ProductHunt, G2, MRR | None | ⚠️ NEEDS UPDATE |
| **post_campaign_analysis** | main.py | _gen_post_campaign_analysis | TBD | TBD | None | N/A |
| **final_summary** | main.py | _gen_final_summary | TBD | TBD | None | N/A |
| **brand_positioning** (Ent) | main.py | _gen_brand_positioning | 3427-3480 | ✅ None | None | ✅ OK |
| **strategic_recommendations** (Ent) | main.py | _gen_strategic_recommendations | 3619-3750 | ✅ None | None | ✅ OK |
| **cxo_summary** (Ent) | main.py | _gen_cxo_summary | 3751+ | ✅ None | None | ✅ OK |

---

## Files to Update

1. **HIGH PRIORITY:**
   - `/workspaces/AICMO/backend/main.py` - lines 2020-2080 (execution_roadmap SaaS references)

2. **MEDIUM PRIORITY:**
   - `/workspaces/AICMO/backend/main.py` - lines 746-800 (campaign_objective length)

3. **REFERENCE:**
   - `/workspaces/AICMO/backend/layers/layer3_soft_validators.py` - length constraints
   - `/workspaces/AICMO/aicmo/presets/package_presets.py` - pack definitions
   - `/workspaces/AICMO/backend/generators/brand_strategy_generator.py` - brand positioning logic

