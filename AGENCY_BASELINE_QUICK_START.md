## 🎯 Agency Baseline Pipelines – Quick Start

**Commit:** 4bae6ff  
**Date:** November 24, 2025

---

## Overview

Two hardwired agency-grade pipelines guarantee premium structure and depth:

| Pipeline | Use Case | Sections | Template |
|----------|----------|----------|----------|
| `apply_agency_baseline()` | Full strategy decks | 14 | `agency_strategy_default` |
| `apply_quick_social_baseline()` | Social calendars | 9 | `quick_social_agency_default` |

Both ensure professional structure even if raw LLM output is messy.

---

## 1. Strategy Report Baseline

**Full 14-section agency strategy with guaranteed depth.**

### Usage

```python
from aicmo.agency.baseline import apply_agency_baseline
from aicmo.llm import call_llm

# Your existing LLM call
raw_draft = call_llm(system_prompt, brief_text)

# Wrap it with agency baseline
final_report = apply_agency_baseline(
    brief=client_brief_dict,  # e.g. {"brand_name": "Acme", "objectives": "Growth"}
    raw_draft=raw_draft,
    llm=call_llm,  # your LLM function(system, user) -> str
    pack_key="agency_strategy_default",  # optional, defaults to this
)
```

### What It Does

**5-stage pipeline:**

1. **Scaffold** → Enforces 14 exact sections, fills gaps from brief
2. **Deepen** → Ensures each section meets minimum depth (3+ audience segments, 3+ competitor archetypes, etc.)
3. **Narrate** → Ensures all sections ladder to one clear big idea + tension story
4. **Measure** → Ties objectives to KPIs without fabricating data
5. **Polish** → Removes AI tells, humanizes language, runs QA checklist

**Result:** Professional 14-section strategy deck with:
- ✅ Clear problem definition
- ✅ Named big idea + 3-5 strategic pillars
- ✅ Channel roles + tactics
- ✅ 30/60/90 roadmap
- ✅ KPI mapping
- ✅ Risk + dependencies
- ✅ Human-sounding, premium language

### WOW Template Structure

```
1. Executive Summary
2. Brand & Market Context
3. Problem / Challenge Definition
4. Audience & Key Insight
5. Brand Positioning & Strategic Platform
6. Competitive & Market Landscape
7. Big Idea & Strategic Pillars
8. Messaging Architecture
9. Channel & Content Strategy
10. Phasing & Roadmap
11. Measurement & KPIs
12. Budget & Investment Logic
13. Risks, Assumptions & Dependencies
14. Implementation Plan & Next Steps
```

### Example Brief

```python
brief = {
    "brand_name": "TechCorp",
    "client_name": "TechCorp Inc",
    "category": "B2B SaaS",
    "target_audience": "Mid-market GTM leaders",
    "business_problem": "Need to expand from SMBs into enterprise segment",
    "objectives": ["30% lead growth", "improve sales enablement", "establish thought leadership"],
    "budget": "$200k/year",
    "timeline": "12 months",
}

raw_draft = "We should do a marketing plan... [messy AI output]"

final = apply_agency_baseline(brief, raw_draft, call_llm)
print(final)  # Perfectly structured 14-section strategy deck
```

---

## 2. Quick Social Baseline

**Compact 9-section social calendar with varied content, hooks, and CTAs.**

### Usage

```python
from aicmo.agency.baseline import apply_quick_social_baseline

raw_draft = call_llm(system_prompt, brief_text)

final_plan = apply_quick_social_baseline(
    brief=social_brief_dict,
    raw_draft=raw_draft,
    llm=call_llm,
    pack_key="quick_social_agency_default",  # optional
)
```

### What It Does

**3-stage pipeline (lighter than strategy):**

1. **Scaffold** → Enforces 9 exact sections
2. **Enrich** → Adds 3-5 content pillars, 30-day calendar with variety, 8-12 hooks, hashtag strategy
3. **Polish** → Energetic but human tone, removes clichés, QA checklist

**Result:** Social content plan with:
- ✅ 3-5 content pillars + example angles
- ✅ 30-day calendar (varied formats, daily hooks)
- ✅ 8-12 sample hooks (thumb-stopping)
- ✅ Caption guidelines + hashtag clusters
- ✅ Soft vs hard CTAs
- ✅ KPIs + weekly review ritual
- ✅ Setup checklist + owner matrix

### WOW Template Structure

```
1. Snapshot & Objectives
2. Audience Snapshot
3. Content Pillars & Creative Angles
4. Posting Rhythm & Format Mix
5. 30-Day Content Calendar (Outline)
6. Hooks, Captions & Hashtag Directions
7. CTAs & Funnel Logic
8. Measurement & Quick Optimization
9. Next Steps (0–2 Weeks)
```

### Example Brief

```python
brief = {
    "brand_name": "Luna Coffee",
    "primary_channel": "Instagram",
    "target_audience": "Millennial coffee enthusiasts in NYC",
    "objectives": ["Grow followers 50%", "Drive store foot-traffic"],
    "budget": "Organic only",
    "timeline": "30 days",
}

raw_draft = "Post coffee pics... [messy AI output]"

final_plan = apply_quick_social_baseline(brief, raw_draft, call_llm)
print(final_plan)  # Structured, varied 30-day social plan with hooks & CTAs
```

---

## 3. Integration Examples

### Strategy Generator

```python
# backend/generators/strategy.py
from aicmo.llm import call_llm
from aicmo.agency.baseline import apply_agency_baseline

def generate_strategy_report(brief: dict) -> str:
    system = "You are an experienced marketing strategist..."
    user = f"Create a draft marketing & campaign plan:\n\n{brief}"
    raw_draft = call_llm(system, user)
    
    # Apply agency baseline
    return apply_agency_baseline(
        brief=brief,
        raw_draft=raw_draft,
        llm=call_llm,
        pack_key="agency_strategy_default",
    )
```

### Social Calendar Generator

```python
# backend/generators/social.py
from aicmo.llm import call_llm
from aicmo.agency.baseline import apply_quick_social_baseline

def generate_quick_social_plan(brief: dict) -> str:
    system = "You are a social media strategist for short, punchy content plans."
    user = f"Create a draft quick social plan:\n\n{brief}"
    raw_draft = call_llm(system, user)
    
    # Apply agency baseline
    return apply_quick_social_baseline(
        brief=brief,
        raw_draft=raw_draft,
        llm=call_llm,
        pack_key="quick_social_agency_default",
    )
```

### Streamlit Integration

```python
# streamlit_pages/aicmo_operator.py
from aicmo.agency.baseline import apply_agency_baseline, apply_quick_social_baseline

if service == "strategy":
    raw = call_backend_generate("draft")
    final = apply_agency_baseline(brief, raw, llm_func)
    st.markdown(final)

elif service == "quick_social":
    raw = call_backend_generate("draft")
    final = apply_quick_social_baseline(brief, raw, llm_func)
    st.markdown(final)
```

---

## 4. Depth Enforcement Details

### Strategy Baseline Minimums

- **Executive Summary:** ≥3 bullets (challenge, moves, impact)
- **Audience & Key Insight:** ≥2 segments + 1 explicit human tension
- **Competitive Landscape:** ≥3 competitor archetypes or patterns
- **Big Idea & Pillars:** 1 named big idea + 3–5 pillars
- **Channel Strategy:** Each channel has role, objectives, 2-3 example tactics
- **Measurement:** ≥1 KPI per main objective
- **Implementation:** ≥5 concrete next steps with owners/timelines

### Quick Social Enrichment Minimums

- **Content Pillars:** 3–5 distinct pillars (education, social proof, offers, BTS, culture)
- **30-Day Calendar:** Varied formats, themes, daily hooks (5-10 word angles)
- **Hooks:** 8–12 thumb-stopping hook lines
- **Hashtag Strategy:** % split + 3-4 example tag clusters
- **CTAs:** Both soft (save, share) and hard (DM, click, buy)

---

## 5. Files Created/Modified

```
✅ aicmo/agency/__init__.py (NEW - 13 lines)
✅ aicmo/agency/baseline.py (NEW - 450+ lines)
   - apply_agency_baseline()
   - apply_quick_social_baseline()
   - 5 helper functions per pipeline
   - _render_wow_template() (shared)

✅ aicmo/presets/wow_templates.py (MODIFIED - added 2 templates)
   - "agency_strategy_default" (14 sections)
   - "quick_social_agency_default" (9 sections)
```

---

## 6. Design Principles

### No Fabrication
- Never invent fake numbers, case studies, or brand names
- Qualitative KPIs ("healthy engagement rate") are fine when data unavailable
- All assertions are grounded in the brief or standard agency practice

### Modular Pipeline
- Each stage (scaffold → deepen → narrate → measure → polish) is independent
- Easy to skip stages or swap in custom versions
- LLM function is pluggable (`call_llm` pattern)

### Graceful Degradation
- If a WOW template key is missing, system returns a sensible error message
- If brief is incomplete, placeholders fill intelligently
- If raw draft is messy, each stage progressively cleans it up

### Client-Ready by Default
- All output is human-readable, no AI tells
- Language is confident but not buzzword-heavy
- Structure is immediately usable as client deck outline

---

## 7. Next Steps

1. **Wire into your LLM layer:**
   - Replace `from aicmo.llm import call_llm` with your actual LLM function
   - Ensure it matches signature: `llm(system: str, user: str) -> str`

2. **Test with real briefs:**
   ```python
   final = apply_agency_baseline(your_brief, raw_draft, your_llm)
   # Verify all 14 sections are present
   # Verify narrative cohesion (big idea mentioned 3+ times)
   # Verify KPIs are mapped to objectives
   ```

3. **Add to generators:**
   - Wrap existing LLM calls in both pipelines
   - Test with different service packages (strategy, social, campaign, audit)

4. **Customize templates (optional):**
   - Add new WOW templates to `WOW_TEMPLATES` dict
   - Pass custom `pack_key` to baseline functions

---

*Agency Baseline Module v1.0 – Production Ready*
