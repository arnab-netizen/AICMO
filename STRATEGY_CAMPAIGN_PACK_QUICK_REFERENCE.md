# Strategy + Campaign Pack - Quick Reference

## ⚡ Quick Update Checklist

### 🔴 HIGH PRIORITY - SaaS-Specific Terms Found

#### execution_roadmap() - 3 instances to fix
**File:** `backend/main.py`  
**Function:** `_gen_execution_roadmap()`  
**Lines:** 2020-2043

| Line | Current Text | Issue | Fix |
|------|--------------|-------|-----|
| 2027 | `"Create waitlist via LinkedIn ads, partnerships, Product Hunt Ship page"` | ProductHunt reference | Remove "Product Hunt Ship page", replace with "industry directories" |
| 2030 | `"Finalize Product Hunt launch page with clear value prop and demo video"` | ProductHunt reference | Replace entire line with generic "Finalize launch page" |
| 2033 | `"Deploy across Product Hunt, TechCrunch, major tech media"` | ProductHunt + TechCrunch | Replace with "Deploy across industry directories, relevant media outlets" |
| 2043 | `"**Success Metrics:** 100+ customers Month 1, 4.5+ G2 rating, $50K MRR by Month 3"` | G2 + MRR (SaaS metrics) | Replace with generic "X+ customers Month 1, 4.5+ customer satisfaction score, [$revenue] MRR" |

### 🟠 MEDIUM PRIORITY - Length Issues

#### campaign_objective() - Exceeds 250-word maximum
**File:** `backend/main.py`  
**Function:** `_gen_campaign_objective()`  
**Lines:** 746-800  
**Current Length:** ~350 words  
**Max Allowed:** 250 words  
**Recommendation:** Condense secondary objectives and success metrics sections

### 🟢 LOW PRIORITY - Verification

- [x] overview() - ✅ No SaaS terms, within 150-400 word range
- [x] core_campaign_idea() - ✅ No SaaS terms
- [x] messaging_framework() - ✅ No SaaS terms, production-verified
- [x] kpi_and_budget_plan() - ✅ No SaaS terms, generic metrics
- [x] brand_positioning() - ✅ No SaaS terms (Enterprise only)
- [x] strategic_recommendations() - ✅ No SaaS terms (Enterprise only)
- [x] cxo_summary() - ✅ No SaaS terms (Enterprise only)

---

## Section Locations Map

### Strategy + Campaign Standard Pack (17 sections)

| # | Section | Type | File | Function | Lines | Status |
|---|---------|------|------|----------|-------|--------|
| 1 | **overview** | Intro | main.py | _gen_overview | 683-745 | ✅ OK |
| 2 | **campaign_objective** | Strategy | main.py | _gen_campaign_objective | 746-850 | ⚠️ LONG |
| 3 | **core_campaign_idea** | Strategy | main.py | _gen_core_campaign_idea | 851-869 | ✅ OK |
| 4 | **messaging_framework** | Strategy | main.py | _gen_messaging_framework | 871+ | ✅ OK |
| 5 | **channel_plan** | Tactics | main.py | _gen_channel_plan | TBD | ? |
| 6 | **audience_segments** | Research | main.py | _gen_audience_segments | TBD | ? |
| 7 | **persona_cards** | Research | main.py | _gen_persona_cards | TBD | ? |
| 8 | **creative_direction** | Creative | main.py | _gen_creative_direction | TBD | ? |
| 9 | **influencer_strategy** | Tactics | main.py | _gen_influencer_strategy | TBD | ? |
| 10 | **promotions_and_offers** | Tactics | main.py | _gen_promotions_and_offers | TBD | ? |
| 11 | **detailed_30_day_calendar** | Execution | main.py | _gen_detailed_30_day_calendar | TBD | ? |
| 12 | **email_and_crm_flows** | Tactics | main.py | _gen_email_and_crm_flows | TBD | ? |
| 13 | **ad_concepts** | Creative | main.py | _gen_ad_concepts | TBD | ? |
| 14 | **kpi_and_budget_plan** | Planning | main.py | _gen_kpi_and_budget_plan | 1897-1950 | ✅ OK |
| 15 | **execution_roadmap** | Execution | main.py | _gen_execution_roadmap | 1950-2100 | ❌ SaaS TERMS |
| 16 | **post_campaign_analysis** | Review | main.py | _gen_post_campaign_analysis | TBD | ? |
| 17 | **final_summary** | Summary | main.py | _gen_final_summary | TBD | ? |

---

## Fix Templates

### Fix #1: execution_roadmap() - Line 2027 (Remove ProductHunt)

**OLD:**
```python
f"- Create waitlist via LinkedIn ads, partnerships, Product Hunt Ship page\n"
```

**NEW:**
```python
f"- Create waitlist via LinkedIn ads, partnerships, and industry directories\n"
```

---

### Fix #2: execution_roadmap() - Line 2030 (Remove ProductHunt)

**OLD:**
```python
f"- Finalize Product Hunt launch page with clear value prop and demo video\n\n"
```

**NEW:**
```python
f"- Finalize launch page with clear value prop and demo video\n\n"
```

---

### Fix #3: execution_roadmap() - Line 2033 (Remove ProductHunt + TechCrunch)

**OLD:**
```python
f"- Deploy across Product Hunt, TechCrunch, major tech media\n"
```

**NEW:**
```python
f"- Deploy across relevant industry directories and media outlets\n"
```

---

### Fix #4: execution_roadmap() - Line 2043 (Replace G2 + MRR)

**OLD:**
```python
f"**Success Metrics:** 100+ customers Month 1, 4.5+ G2 rating, $50K MRR by Month 3\n"
```

**NEW:**
```python
f"**Success Metrics:** 100+ customers Month 1, 4.5+ customer satisfaction score, [$revenue_target] monthly revenue by Month 3\n"
```

---

## SaaS Detection Logic

**File:** `backend/main.py` | **Function:** `infer_is_saas()` | **Lines:** 659-672

```python
def infer_is_saas(brief: Any) -> bool:
    """Detect if the brief describes a SaaS/software product."""
    saas_keywords = ["saas", "software", "platform", "app", "subscription", "b2b saas", "cloud", "api"]
    return any(k in text for k in saas_keywords)
```

**Current Behavior:**
- ✅ Correctly detects SaaS products from keywords
- ✅ Triggers SaaS-specific branch at line 2022 in execution_roadmap()
- ⚠️ But SaaS branch still contains ProductHunt, G2, MRR references meant only for tech startups

**Recommendation:** Update SaaS branch to use more generic terms that work for all SaaS products (not just tech startups)

---

## Length Constraints Reference

**From:** `backend/layers/layer3_soft_validators.py` | **Function:** `_check_length_bounds()` | **Lines:** 155-175

```python
expected_ranges = {
    "overview": (150, 400),
    "campaign_objective": (100, 250),  # ⚠️ Current exceeds this
    "creatives_headline": (50, 150),
    "strategy": (200, 500),
    "social_calendar": (500, 2000),
    "media_plan": (100, 300),
}
```

**Sections Checked:** Only these 6 sections have explicit constraints  
**Other Sections:** No length validation (rely on quality assessment)

---

## Related Files

- **Generator Registration:** `backend/main.py` lines 6761-6850 (SECTION_GENERATORS dict)
- **Pack Definitions:** `aicmo/presets/package_presets.py` (sections per pack tier)
- **Validation Rules:** `backend/layers/layer3_soft_validators.py` (quality checks)
- **Brand Strategy Generator:** `backend/generators/brand_strategy_generator.py` (brand_positioning logic)
- **Creative Service:** `backend/services/creative_service.py` (optional LLM polish)

