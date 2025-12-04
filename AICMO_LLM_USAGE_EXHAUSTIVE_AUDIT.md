# AICMO LLM Usage - Exhaustive Architecture Audit

**Date**: 2024-12-04  
**Status**: Complete Code Analysis  
**Scope**: All packs, all sections, all LLM integration points

---

## EXECUTIVE SUMMARY

This audit maps **every pack, section, and LLM usage** in the AICMO codebase based on actual code inspection.

### Quick Stats

- **Total Packs**: 9 (including 3 Strategy+Campaign tiers)
- **Total Unique Sections**: 83 generators registered in `SECTION_GENERATORS`
- **Perplexity Usage**: 1 central call location (`get_brand_research()` in `/aicmo/generate` endpoint)
- **OpenAI Usage**: 5 distinct integration points (CreativeService, agency_grade, humanizer, creative_territories, brief parsing)
- **Template-Only Sections**: ~95% of sections (Perplexity data available but not used directly)

### Architecture Model

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT BRIEF INPUT                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  RESEARCH LAYER (Perplexity - ONE CENTRAL CALL)             │
│  - File: backend/main.py:7834 (api_aicmo_generate_report)   │
│  - Function: get_brand_research()                            │
│  - Stores result in: brief.brand.research                    │
│  - Called: Once per pack generation                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  GENERATOR LAYER (Template-First)                           │
│  - 83 section generators in backend/main.py                  │
│  - Access research via: research = getattr(b, "research")    │
│  - Usage: 2 sections use research directly                   │
│  - Fallback: All have template-only fallback                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  ENHANCEMENT LAYER (OpenAI - 5 integration points)          │
│  1. CreativeService.polish_section() - Optional polish       │
│  2. agency_grade_enhancers - Turbo mode frameworks          │
│  3. humanizer - Generic phrase replacement                   │
│  4. creative_territories - Brand-specific angles             │
│  5. Brief parsing - WOW autofill                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FINAL REPORT OUTPUT                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 1. PACK INVENTORY

Source: `aicmo/presets/package_presets.py`

### All Registered Packs

| # | Pack Key | Display Name | Sections | Research? | Complexity | Tier |
|---|----------|--------------|----------|-----------|------------|------|
| 1 | `quick_social_basic` | Quick Social Pack (Basic) | 8 | No | low | basic |
| 2 | `strategy_campaign_standard` | Strategy + Campaign Pack (Standard) | 17 | Yes | medium | standard |
| 3 | `strategy_campaign_basic` | Strategy + Campaign Pack (Basic) | 6 | No | low | basic |
| 4 | `full_funnel_growth_suite` | Full-Funnel Growth Suite (Premium) | 23 | Yes | high | premium |
| 5 | `launch_gtm_pack` | Launch & GTM Pack | 13 | Yes | medium-high | - |
| 6 | `brand_turnaround_lab` | Brand Turnaround Lab | 14 | Yes | high | - |
| 7 | `retention_crm_booster` | Retention & CRM Booster | 14 | Yes | medium | - |
| 8 | `performance_audit_revamp` | Performance Audit & Revamp | 16 | Yes | medium-high | - |
| 9 | `strategy_campaign_premium` | Strategy + Campaign Pack (Premium) | 28 | Yes | high | premium |
| 10 | `strategy_campaign_enterprise` | Strategy + Campaign Pack (Enterprise) | 38 | Yes | very-high | enterprise |

**Note**: Packs 2, 3, 9, 10 are the 4-tier Strategy+Campaign system.

---

## 2. PERPLEXITY USAGE MAPPING

### 2.1 Central Research Infrastructure

**Research Call Location**: `backend/main.py` line 7834

```python
from backend.services.brand_research import get_brand_research

brand_research = get_brand_research(
    brand_name=client_brief_dict.get("brand_name", "").strip() or "",
    industry=client_brief_dict.get("industry", "").strip() or "",
    location=client_brief_dict.get("geography", "").strip() or "",
)
```

**Storage**: Result attached to `brief.brand.research` (BrandResearchResult object)

**Frequency**: Called **once** per pack generation, regardless of pack size

**Data Structure** (`backend/research_models.py`):
```python
@dataclass
class BrandResearchResult:
    recent_content_themes: List[str]       # Perplexity-sourced
    local_competitors: List[Competitor]    # Perplexity-sourced
    hashtag_brand: List[str]               # Perplexity-sourced (keyword_hashtags)
    hashtag_hints: List[str]               # Perplexity-sourced (industry_hashtags)
    hashtag_campaign: List[str]            # Perplexity-sourced (campaign_hashtags)
    audience_pain_points: List[str]        # Placeholder (not yet implemented)
    audience_desires: List[str]            # Placeholder (not yet implemented)
```

### 2.2 Perplexity Client API

**File**: `backend/external/perplexity_client.py`

**Methods**:
| Method | Purpose | Input | Output | Used By |
|--------|---------|-------|--------|---------|
| `research_brand()` | Fetch brand research | brand_name, industry, location | JSON response | `get_brand_research()` |
| `fetch_hashtag_research()` | Fetch hashtag strategy | brand_name, industry, audience | Hashtag lists | `get_brand_research()` |

**API Model**: Perplexity Sonar (claude-3.5-sonnet via Perplexity)

**Environment Config**:
- `AICMO_PERPLEXITY_ENABLED` - Master switch (default: true)
- `PERPLEXITY_API_KEY` - API authentication

### 2.3 Sections Using Perplexity Data

Based on code inspection (`grep research\\.` in backend/main.py):

| Section ID | Pack(s) | Perplexity Data Used | Fallback Behavior | File Location |
|------------|---------|----------------------|-------------------|---------------|
| `hashtag_strategy` | quick_social_basic | `research.keyword_hashtags`<br>`research.industry_hashtags`<br>`research.campaign_hashtags` | Rule-based generation from brand name + industry | backend/main.py:3658 |
| `competitor_analysis` | full_funnel_growth_suite<br>brand_turnaround_lab<br>performance_audit_revamp | `research.local_competitors` | Generic template with Tier 1/2/3 structure | backend/main.py:2701 |
| `customer_insights` | brand_turnaround_lab<br>strategy_campaign_enterprise | `research.audience_pain_points`<br>`research.audience_desires` | Template with generic pain points | backend/main.py:2809 |
| `market_landscape` | full_funnel_growth_suite<br>launch_gtm_pack | `research.recent_content_themes` (mentioned in comment) | Template with generic market analysis | backend/main.py:5376 |

**Critical Finding**: Only **4 out of 83 sections** (4.8%) actually consume Perplexity data, despite research being fetched for all packs marked `requires_research: True`.

### 2.4 Research Service Layer (Not Yet Used)

**File**: `backend/services/research_service.py`

**Status**: ✅ Implemented but **NOT INTEGRATED** into main generation flow

**Classes**:
```python
class ResearchService:
    def fetch_comprehensive_research(brief) -> ComprehensiveResearchData
    
@dataclass
class ComprehensiveResearchData:
    brand_research: Optional[BrandResearchResult]
    competitor_research: Optional[CompetitorResearchResult]  # NEW
    audience_insights: Optional[AudienceInsightsResult]      # NEW
    market_trends: Optional[MarketTrendsResult]              # NEW
```

**Purpose**: Architectural layer for future expansion (competitor intelligence, audience insights, market trends)

**Integration Status**: Zero usages in backend/main.py generator functions

---

## 3. OPENAI USAGE MAPPING

### 3.1 Integration Point #1: CreativeService (Polish Layer)

**File**: `backend/services/creative_service.py`

**Class**: `CreativeService`

**Purpose**: Optional section polish and enhancement

**Methods**:
| Method | Purpose | Input | Output | Used By |
|--------|---------|-------|--------|---------|
| `polish_section()` | Enhance template with creative polish | template_text, brief, research_data, section_type | Polished markdown | `_gen_campaign_objective` only |
| `degenericize_text()` | Remove generic marketing language | text, brief | Cleaned text | Not used |
| `generate_narrative()` | Generate brand story from scratch | brief, narrative_type, max_length | Narrative text | Not used |
| `enhance_calendar_posts()` | Improve social media hooks | posts, brief, research | Enhanced posts | Not used |

**Configuration**:
```python
@dataclass
class CreativeConfig:
    temperature: float = 0.7
    max_tokens: int = 2000
    model: str = "gpt-4o-mini"
    enable_polish: bool = True
```

**Integration Status**: 
- ✅ Implemented (425 lines)
- ⚠️ **Only 1 section uses it**: `_gen_campaign_objective` (line 593)
- ❌ Not used by other 82 sections

**Example Usage** (backend/main.py:641):
```python
creative_service = CreativeService()
if creative_service.is_enabled():
    polished_text = creative_service.polish_section(
        content=template_text,
        brief=req.brief,
        research_data=research,
        section_type="strategy"
    )
```

**Environment Config**:
- `AICMO_USE_LLM` - Master switch for OpenAI
- `OPENAI_API_KEY` - API authentication
- Stub mode disables all OpenAI calls

### 3.2 Integration Point #2: Agency Grade Enhancers (Turbo Mode)

**File**: `backend/agency_grade_enhancers.py`

**Purpose**: Add strategic frameworks and consulting-grade depth to reports

**Functions**:
| Function | Purpose | OpenAI Usage | Integration Point |
|----------|---------|--------------|-------------------|
| `apply_agency_grade_enhancements()` | Add frameworks (AIDA, SOSTAC, etc.) | Yes (gpt-4o-mini) | Called in `api_aicmo_generate_report()` when `include_agency_grade=True` |
| `_get_openai_client()` | Safe client initialization | N/A | Internal helper |
| `_call_llm_for_section()` | Generic OpenAI wrapper | Yes | Internal helper |
| `_augment_with_phase_l()` | Add Phase L memory context | Yes (if enabled) | Internal helper |

**Trigger**: `req.include_agency_grade = True` in GenerateRequest

**Model**: `gpt-4o-mini` (configurable via `AICMO_MODEL_MAIN`)

**Usage Pattern**:
```python
if req.include_agency_grade and turbo_enabled:
    apply_agency_grade_enhancements(req.brief, base_output)
```

**Integration Points** (backend/main.py):
- Line 7433: After marketing plan generation
- Line 7540: After campaign blueprint generation
- Line 7599: After social calendar generation
- Line 7634: After performance review generation

**Affected Packs**: ALL packs when `include_agency_grade=True` (frontend toggle)

### 3.3 Integration Point #3: Humanizer (Generic Phrase Removal)

**File**: `backend/humanizer.py`

**Purpose**: Remove AI-ish generic language, add industry-specific flavor

**Mode**: Primarily **deterministic** (regex replacements), optional LLM mode (disabled by default)

**Functions**:
| Function | Uses LLM? | Purpose |
|----------|-----------|---------|
| `humanize_report_text()` | Optional (default: OFF) | Main entry point |
| `apply_phrase_replacements()` | No | Deterministic regex (e.g., "leverage" → "use") |
| `inject_industry_flavor()` | No | Word substitution from config |
| `normalize_sentence_lengths()` | No | Heuristic sentence splitting |

**Configuration**:
```python
@dataclass
class HumanizerConfig:
    level: HumanizeLevel = "medium"  # "off" | "light" | "medium"
    enable_llm: bool = False         # KEEP FALSE BY DEFAULT
```

**Replacements** (deterministic):
```python
GENERIC_PHRASES = {
    "in today's digital age" → "right now in your market",
    "holistic" → "joined-up",
    "robust" → "reliable",
    "by leveraging" → "by using",
}
```

**Integration Point**: `backend/main.py` line 7176

```python
if req.wow_enabled and req.wow_package_key:
    humanizer_config = HumanizerConfig(level=pack_humanize_level)
    wow_markdown = humanize_report_text(
        text=wow_markdown,
        brief_data=brief_dict,
        config=humanizer_config,
    )
```

**Pack-Specific Levels**:
- `quick_social_basic`: "light"
- All other packs: "medium"

**LLM Usage**: ❌ Disabled by default (`enable_llm=False`)

### 3.4 Integration Point #4: Creative Territories

**File**: `backend/creative_territories.py`

**Purpose**: Generate brand-specific content angles and themes

**Class**: `CreativeTerritory` (dataclass)

**Function**: `get_creative_territories_for_brief(brief: Dict) -> List[CreativeTerritory]`

**Logic**:
- Hardcoded territories for Starbucks (example implementation)
- Generic territories for other brands
- ❌ **No LLM calls** in current implementation

**Structure**:
```python
@dataclass
class CreativeTerritory:
    id: str
    label: str
    summary: str
    example_angles: List[str]
```

**Used By**: `_gen_detailed_30_day_calendar` (line 1195) - assigns territory to each calendar post

**OpenAI Usage**: **NONE** - purely template-based currently

### 3.5 Integration Point #5: Brief Parsing & WOW Autofill

**File**: `backend/services/wow_autofill.py`

**Purpose**: Parse unstructured brief text into structured ClientInputBrief

**Function**: `autofill_brief_from_text(raw_text: str) -> Dict`

**OpenAI Model**: `gpt-4o` (via `_get_openai_client()`)

**Trigger**: When user submits raw text brief instead of structured form

**Usage Location**: `/aicmo/generate` endpoint when `raw_brief_text` is provided

**Prompt Pattern**:
```python
system_prompt = """Extract structured brief data from unstructured text.
Return JSON with: brand_name, industry, product_service, primary_goal, etc."""

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": raw_text}
    ]
)
```

**Affected Fields**: All ClientInputBrief fields (brand, audience, goal, voice, etc.)

---

## 4. SECTION-BY-SECTION LLM CLASSIFICATION

### 4.1 Complete Section Registry

Source: `backend/main.py` SECTION_GENERATORS (line 6193)

Total: **83 registered sections**

### 4.2 Classification Matrix

| Section ID | Perplexity | OpenAI | Template | Packs Using | Notes |
|------------|------------|--------|----------|-------------|-------|
| **CORE SECTIONS** |
| `overview` | No | No | ✅ | All (10/10) | Pure template |
| `messaging_framework` | No | No | ✅ | 9/10 | Pure template |
| `final_summary` | No | No | ✅ | All (10/10) | Pure template |
| `execution_roadmap` | No | No | ✅ | All (10/10) | Pure template |
| **STRATEGY SECTIONS** |
| `campaign_objective` | No | ✅ Optional | ✅ | 4/10 | **ONLY section using CreativeService.polish_section()** |
| `core_campaign_idea` | No | No | ✅ | 5/10 | Pure template (CreativeService mentioned in docstring but not called) |
| `value_proposition_map` | No | No | ✅ | 3/10 | Pure template |
| `brand_positioning` | No | No | ✅ | 1/10 | Pure template |
| **RESEARCH SECTIONS** |
| `hashtag_strategy` | ✅ Direct | No | ✅ | 1/10 (quick_social_basic) | Uses research.keyword_hashtags, research.industry_hashtags, research.campaign_hashtags |
| `competitor_analysis` | ✅ Direct | No | ✅ | 3/10 | Uses research.local_competitors |
| `customer_insights` | ✅ Direct | No | ✅ | 2/10 | Uses research.audience_pain_points (mostly empty) |
| `market_landscape` | ⚠️ Indirect | No | ✅ | 2/10 | Comment mentions research but doesn't use it |
| `market_analysis` | No | No | ✅ | 1/10 | Pure template |
| `industry_landscape` | No | No | ✅ | 1/10 | Pure template |
| **AUDIENCE SECTIONS** |
| `audience_segments` | No | No | ✅ | 7/10 | Pure template |
| `persona_cards` | No | No | ✅ | 5/10 | Pure template |
| `customer_journey_map` | No | No | ✅ | 2/10 | Pure template |
| `customer_segments` | No | No | ✅ | 1/10 | Pure template |
| **CREATIVE SECTIONS** |
| `creative_direction` | No | No | ✅ | 7/10 | Pure template |
| `creative_territories` | No | ❌ Planned | ✅ | 2/10 | Pure template (OpenAI integration planned but not implemented) |
| `copy_variants` | No | No | ✅ | 2/10 | Pure template |
| `ad_concepts` | No | No | ✅ | 3/10 | Pure template |
| `ad_concepts_multi_platform` | No | No | ✅ | 1/10 | Pure template |
| `new_ad_concepts` | No | No | ✅ | 1/10 | Pure template |
| **CALENDAR SECTIONS** |
| `detailed_30_day_calendar` | No | No | ✅ | 6/10 | Pure template (uses creative_territories but no LLM) |
| `full_30_day_calendar` | No | No | ✅ | 1/10 | Pure template |
| `content_calendar_launch` | No | No | ✅ | 1/10 | Pure template |
| `30_day_recovery_calendar` | No | No | ✅ | 1/10 | Pure template |
| `content_buckets` | No | No | ✅ | 1/10 | Pure template |
| **CHANNEL SECTIONS** |
| `channel_plan` | No | No | ✅ | 4/10 | Pure template |
| `channel_reset_strategy` | No | No | ✅ | 1/10 | Pure template |
| `email_and_crm_flows` | No | No | ✅ | 2/10 | Pure template |
| `email_automation_flows` | No | No | ✅ | 2/10 | Pure template |
| `sms_and_whatsapp_flows` | No | No | ✅ | 1/10 | Pure template |
| `sms_and_whatsapp_strategy` | No | No | ✅ | 2/10 | Pure template |
| **FUNNEL SECTIONS** |
| `funnel_breakdown` | No | No | ✅ | 3/10 | Pure template |
| `awareness_strategy` | No | No | ✅ | 3/10 | Pure template |
| `consideration_strategy` | No | No | ✅ | 3/10 | Pure template |
| `conversion_strategy` | No | No | ✅ | 3/10 | Pure template |
| `retention_strategy` | No | No | ✅ | 2/10 | Pure template |
| `remarketing_strategy` | No | No | ✅ | 3/10 | Pure template |
| **TACTICAL SECTIONS** |
| `influencer_strategy` | No | No | ✅ | 4/10 | Pure template |
| `promotions_and_offers` | No | No | ✅ | 4/10 | Pure template |
| `ugc_and_community_plan` | No | No | ✅ | 3/10 | Pure template |
| `landing_page_blueprint` | No | No | ✅ | 1/10 | Pure template |
| **KPI SECTIONS** |
| `kpi_and_budget_plan` | No | No | ✅ | 4/10 | Pure template |
| `kpi_plan_light` | No | No | ✅ | 1/10 | Pure template |
| `kpi_plan_retention` | No | No | ✅ | 1/10 | Pure template |
| `kpi_reset_plan` | No | No | ✅ | 1/10 | Pure template |
| `measurement_framework` | No | No | ✅ | 2/10 | Pure template |
| **ANALYSIS SECTIONS** |
| `post_campaign_analysis` | No | No | ✅ | 3/10 | Pure template |
| `optimization_opportunities` | No | No | ✅ | 2/10 | Pure template |
| **AUDIT SECTIONS** (Performance Audit & Revamp pack) |
| `account_audit` | No | No | ✅ | 1/10 | Pure template |
| `campaign_level_findings` | No | No | ✅ | 1/10 | Pure template |
| `creative_performance_analysis` | No | No | ✅ | 1/10 | Pure template |
| `audience_analysis` | No | No | ✅ | 1/10 | Pure template |
| `competitor_benchmark` | No | No | ✅ | 1/10 | Pure template |
| `conversion_audit` | No | No | ✅ | 1/10 | Pure template |
| **TURNAROUND SECTIONS** (Brand Turnaround Lab pack) |
| `brand_audit` | No | No | ✅ | 1/10 | Pure template |
| `problem_diagnosis` | No | No | ✅ | 2/10 | Pure template |
| `new_positioning` | No | No | ✅ | 1/10 | Pure template |
| `reputation_recovery_plan` | No | No | ✅ | 1/10 | Pure template |
| **RETENTION SECTIONS** (Retention & CRM Booster pack) |
| `churn_diagnosis` | No | No | ✅ | 1/10 | Pure template |
| `loyalty_program_concepts` | No | No | ✅ | 1/10 | Pure template |
| `winback_sequence` | No | No | ✅ | 1/10 | Pure template |
| `post_purchase_experience` | No | No | ✅ | 1/10 | Pure template |
| `retention_drivers` | No | No | ✅ | 0/10 | Pure template (not wired to any pack) |
| **LAUNCH SECTIONS** (Launch & GTM Pack) |
| `product_positioning` | No | No | ✅ | 1/10 | Pure template |
| `launch_phases` | No | No | ✅ | 1/10 | Pure template |
| `launch_campaign_ideas` | No | No | ✅ | 1/10 | Pure template |
| **REVAMP SECTIONS** |
| `revamp_strategy` | No | No | ✅ | 1/10 | Pure template |
| **ENTERPRISE SECTIONS** (Strategy+Campaign Enterprise only) |
| `risk_assessment` | No | No | ✅ | 1/10 | Pure template |
| `strategic_recommendations` | No | No | ✅ | 1/10 | Pure template |
| `cxo_summary` | No | No | ✅ | 1/10 | Pure template |
| `risk_analysis` | No | No | ✅ | 0/10 | Pure template (not wired) |
| **OTHER SECTIONS** |
| `platform_guidelines` | No | No | ✅ | 0/10 | Pure template (not wired) |
| `video_scripts` | No | No | ✅ | 0/10 | Pure template (not wired) |
| `week1_action_plan` | No | No | ✅ | 0/10 | Pure template (not wired) |
| `review_responder` | No | No | ✅ | 0/10 | Pure template (implemented but not wired) |
| `turnaround_milestones` | No | No | ✅ | 0/10 | Pure template (not wired) |
| `weekly_social_calendar` | No | No | ✅ | 0/10 | Pure template (not wired) |
| `creative_direction_light` | No | No | ✅ | 0/10 | Pure template (not wired) |

### 4.3 Summary Statistics

| Category | Count | Percentage |
|----------|-------|------------|
| **Total Sections Registered** | 83 | 100% |
| **Sections Using Perplexity Directly** | 3 | 3.6% |
| **Sections Using OpenAI Directly** | 1 | 1.2% |
| **Pure Template Sections** | 79 | 95.2% |
| **Sections Wired to Packs** | 73 | 88.0% |
| **Sections Not Wired** | 10 | 12.0% |

---

## 5. PACK-BY-PACK LLM USAGE

### Pack 1: Quick Social Pack (Basic)

**Sections**: 8  
**File**: `aicmo/presets/package_presets.py` line 25

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| messaging_framework | No | No | Template |
| detailed_30_day_calendar | No | No | Template (uses creative_territories, no LLM) |
| content_buckets | No | No | Template |
| hashtag_strategy | ✅ Yes | No | **ONLY section in this pack using Perplexity** |
| kpi_plan_light | No | No | Template |
| execution_roadmap | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 1/8 sections (12.5%)  
**OpenAI Coverage**: 0/8 sections (0%)  
**Notes**: Lightest pack, minimal LLM usage. Hashtags are Perplexity-powered with rule-based fallback.

---

### Pack 2: Strategy + Campaign Pack (Standard)

**Sections**: 17  
**File**: `aicmo/presets/package_presets.py` line 43

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| campaign_objective | No | ✅ Yes (optional) | **ONLY section using CreativeService.polish_section()** |
| core_campaign_idea | No | No | Template |
| messaging_framework | No | No | Template |
| channel_plan | No | No | Template |
| audience_segments | No | No | Template |
| persona_cards | No | No | Template |
| creative_direction | No | No | Template |
| influencer_strategy | No | No | Template |
| promotions_and_offers | No | No | Template |
| detailed_30_day_calendar | No | No | Template |
| email_and_crm_flows | No | No | Template |
| ad_concepts | No | No | Template |
| kpi_and_budget_plan | No | No | Template |
| execution_roadmap | No | No | Template |
| post_campaign_analysis | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 0/17 sections (0%)  
**OpenAI Coverage**: 1/17 sections (5.9%)  
**Notes**: Most popular mid-tier pack. Only `campaign_objective` gets optional OpenAI polish.

---

### Pack 3: Strategy + Campaign Pack (Basic)

**Sections**: 6  
**File**: `aicmo/presets/package_presets.py` line 85

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| core_campaign_idea | No | No | Template |
| messaging_framework | No | No | Template |
| audience_segments | No | No | Template |
| detailed_30_day_calendar | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 0/6 sections (0%)  
**OpenAI Coverage**: 0/6 sections (0%)  
**Notes**: Minimal tier, pure template.

---

### Pack 4: Full-Funnel Growth Suite (Premium)

**Sections**: 23  
**File**: `aicmo/presets/package_presets.py` line 105

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| market_landscape | ⚠️ Indirect | No | Research mentioned but not used |
| competitor_analysis | ✅ Yes | No | Uses research.local_competitors |
| funnel_breakdown | No | No | Template |
| audience_segments | No | No | Template |
| persona_cards | No | No | Template |
| value_proposition_map | No | No | Template |
| messaging_framework | No | No | Template |
| awareness_strategy | No | No | Template |
| consideration_strategy | No | No | Template |
| conversion_strategy | No | No | Template |
| retention_strategy | No | No | Template |
| landing_page_blueprint | No | No | Template |
| email_automation_flows | No | No | Template |
| remarketing_strategy | No | No | Template |
| ad_concepts_multi_platform | No | No | Template |
| creative_direction | No | No | Template |
| full_30_day_calendar | No | No | Template |
| kpi_and_budget_plan | No | No | Template |
| measurement_framework | No | No | Template |
| execution_roadmap | No | No | Template |
| optimization_opportunities | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 1/23 sections (4.3%)  
**OpenAI Coverage**: 0/23 sections (0%)  
**Notes**: Despite being "Premium" tier, minimal LLM usage. Heavy on templates.

---

### Pack 5: Launch & GTM Pack

**Sections**: 13  
**File**: `aicmo/presets/package_presets.py` line 141

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| market_landscape | ⚠️ Indirect | No | Research mentioned but not used |
| product_positioning | No | No | Template |
| messaging_framework | No | No | Template |
| launch_phases | No | No | Template |
| channel_plan | No | No | Template |
| audience_segments | No | No | Template |
| creative_direction | No | No | Template |
| launch_campaign_ideas | No | No | Template |
| content_calendar_launch | No | No | Template |
| ad_concepts | No | No | Template |
| execution_roadmap | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 0/13 sections (0%)  
**OpenAI Coverage**: 0/13 sections (0%)  
**Notes**: Pure template pack, no direct LLM usage.

---

### Pack 6: Brand Turnaround Lab

**Sections**: 14  
**File**: `aicmo/presets/package_presets.py` line 161

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| brand_audit | No | No | Template |
| customer_insights | ✅ Yes | No | Uses research.audience_pain_points (often empty) |
| competitor_analysis | ✅ Yes | No | Uses research.local_competitors |
| problem_diagnosis | No | No | Template |
| new_positioning | No | No | Template |
| messaging_framework | No | No | Template |
| creative_direction | No | No | Template |
| channel_reset_strategy | No | No | Template |
| reputation_recovery_plan | No | No | Template |
| promotions_and_offers | No | No | Template |
| 30_day_recovery_calendar | No | No | Template |
| execution_roadmap | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 2/14 sections (14.3%)  
**OpenAI Coverage**: 0/14 sections (0%)  
**Notes**: Highest Perplexity usage among all packs. Uses competitor and customer data.

---

### Pack 7: Retention & CRM Booster

**Sections**: 14  
**File**: `aicmo/presets/package_presets.py` line 182

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| customer_segments | No | No | Template |
| persona_cards | No | No | Template |
| customer_journey_map | No | No | Template |
| churn_diagnosis | No | No | Template |
| email_automation_flows | No | No | Template |
| sms_and_whatsapp_flows | No | No | Template |
| loyalty_program_concepts | No | No | Template |
| winback_sequence | No | No | Template |
| post_purchase_experience | No | No | Template |
| ugc_and_community_plan | No | No | Template |
| kpi_plan_retention | No | No | Template |
| execution_roadmap | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 0/14 sections (0%)  
**OpenAI Coverage**: 0/14 sections (0%)  
**Notes**: Pure template pack focused on CRM/lifecycle. No LLM usage.

---

### Pack 8: Performance Audit & Revamp

**Sections**: 16  
**File**: `aicmo/presets/package_presets.py` line 203

| Section | Perplexity | OpenAI | Notes |
|---------|------------|--------|-------|
| overview | No | No | Template |
| account_audit | No | No | Template |
| campaign_level_findings | No | No | Template |
| creative_performance_analysis | No | No | Template |
| audience_analysis | No | No | Template |
| funnel_breakdown | No | No | Template |
| competitor_benchmark | No | No | Template |
| problem_diagnosis | No | No | Template |
| revamp_strategy | No | No | Template |
| new_ad_concepts | No | No | Template |
| creative_direction | No | No | Template |
| conversion_audit | No | No | Template |
| remarketing_strategy | No | No | Template |
| kpi_reset_plan | No | No | Template |
| execution_roadmap | No | No | Template |
| final_summary | No | No | Template |

**Perplexity Coverage**: 0/16 sections (0%)  
**OpenAI Coverage**: 0/16 sections (0%)  
**Notes**: Pure template pack. No LLM usage despite being audit-focused.

---

### Pack 9: Strategy + Campaign Pack (Premium)

**Sections**: 28  
**File**: `aicmo/presets/package_presets.py` line 228

Inherits sections from Standard + adds:
- creative_territories
- copy_variants
- ugc_and_community_plan
- sms_and_whatsapp_strategy
- remarketing_strategy
- optimization_opportunities

**Perplexity Coverage**: 0/28 sections (0%)  
**OpenAI Coverage**: 1/28 sections (3.6%) - same `campaign_objective` polish  
**Notes**: Largest Standard+ tier. Minimal LLM usage despite premium positioning.

---

### Pack 10: Strategy + Campaign Pack (Enterprise)

**Sections**: 38  
**File**: `aicmo/presets/package_presets.py` line 263

Inherits from Premium + adds:
- industry_landscape
- market_analysis
- customer_insights (uses research.audience_pain_points)
- brand_positioning
- customer_journey_map
- risk_assessment
- strategic_recommendations
- cxo_summary

**Perplexity Coverage**: 1/38 sections (2.6%) - customer_insights  
**OpenAI Coverage**: 1/38 sections (2.6%) - campaign_objective polish  
**Notes**: Largest pack. Only 2 sections use LLM despite "Enterprise" tier.

---

## 6. CROSS-CUTTING CONCERNS

### 6.1 Agency Grade Enhancement (OpenAI)

**Applies To**: ALL packs when `include_agency_grade=True`

**Trigger**: Frontend toggle in Streamlit or API parameter

**Enhancements**:
1. **Framework Injection**: AIDA, SOSTAC, Golden Circle, Jobs-to-be-Done
2. **Consulting Language**: C-suite terminology, strategic frameworks
3. **Phase L Memory**: Learning from past reports (if enabled)

**Applied After**: Marketing plan, campaign blueprint, social calendar, performance review generation

**Cost**: ~$0.03-0.05 per pack (gpt-4o-mini)

### 6.2 Humanization Layer (Mostly Deterministic)

**Applies To**: ALL packs when `wow_enabled=True`

**Trigger**: Automatic for WOW packs

**Operations**:
- **Deterministic** (95%): Regex replacements for generic phrases
- **Optional LLM** (disabled): OpenAI rephrasing (not used in production)

**Pack-Specific Levels**:
```python
quick_social_basic: "light"   # Minimal replacements
all_others:         "medium"  # Full replacement set
```

**Impact**: Removes AI-ish language ("leverage", "holistic", "robust") without LLM calls

### 6.3 Brief Parsing (OpenAI)

**Applies To**: ALL packs when `raw_brief_text` is provided

**Model**: gpt-4o

**Purpose**: Convert unstructured text into structured ClientInputBrief

**Frequency**: Once per generation if needed

**Cost**: ~$0.01 per brief

---

## 7. GAPS & OPPORTUNITIES

### 7.1 Current Underutilization

**Problem**: Perplexity research is fetched for all packs (7/10 marked `requires_research: True`) but only 3 sections use it.

**Wasted Data**:
- `research.recent_content_themes` - fetched but unused
- `research.audience_pain_points` - fetched but empty
- `research.audience_desires` - fetched but empty

**Cost Impact**: ~$0.02 per pack for unused research

### 7.2 Sections That Should Use Research

Based on semantic analysis:

| Section | Current State | Should Use | Data Source |
|---------|---------------|------------|-------------|
| `market_landscape` | Template | ✅ | research.recent_content_themes |
| `market_analysis` | Template | ✅ | research.recent_content_themes |
| `industry_landscape` | Template | ✅ | research.industry_trends (NEW) |
| `customer_insights` | Partial | ✅ | research.audience_pain_points (needs data) |
| `audience_analysis` | Template | ✅ | research.audience_desires (NEW) |
| `competitor_benchmark` | Template | ✅ | research.local_competitors |

### 7.3 Sections That Should Use OpenAI

Based on creative requirements:

| Section | Current State | Should Use | Method |
|---------|---------------|------------|--------|
| `core_campaign_idea` | Template | ✅ | CreativeService.polish_section() |
| `creative_territories` | Template | ✅ | OpenAI generation from brief |
| `copy_variants` | Template | ✅ | CreativeService.generate_variants() |
| `messaging_framework` | Template | ⚠️ Maybe | CreativeService.polish_section() |
| `value_proposition_map` | Template | ⚠️ Maybe | CreativeService.polish_section() |

### 7.4 ResearchService Integration Gap

**Status**: Fully implemented (451 lines) but **zero usage** in generators

**Classes Available**:
- `CompetitorResearchResult` - structured competitor intelligence
- `AudienceInsightsResult` - pain points, desires, objections
- `MarketTrendsResult` - industry trends, growth drivers

**Integration Path**: Replace direct `research.field` access with `research_service.fetch_comprehensive_research()`

**Benefit**: Unified research API, better error handling, comprehensive fallbacks

### 7.5 CreativeService Integration Gap

**Status**: Fully implemented (425 lines) but only 1 section uses it

**Methods Available**:
- `polish_section()` - used by 1 section
- `degenericize_text()` - unused
- `generate_narrative()` - unused
- `enhance_calendar_posts()` - unused

**Potential Users**: 15-20 sections could benefit from polish (strategy, creative, messaging sections)

**Cost**: ~$0.01-0.02 per section polish (gpt-4o-mini)

---

## 8. ARCHITECTURAL SUMMARY

### 8.1 Current Architecture (As-Is)

```
Perplexity (Research):
  - Single call location: api_aicmo_generate_report()
  - Data storage: brief.brand.research
  - Usage: 3 sections read directly (hashtag_strategy, competitor_analysis, customer_insights)
  - Coverage: 3.6% of sections

OpenAI (Creative):
  - 5 integration points (CreativeService, agency_grade, humanizer, creative_territories, brief parsing)
  - Direct usage: 1 section (campaign_objective with optional polish)
  - Coverage: 1.2% of sections
  - Agency Grade: Opt-in for all packs
  - Humanizer: Auto-enabled for WOW packs (deterministic mode)

Templates:
  - Coverage: 95.2% of sections
  - All sections have template fallback
  - Templates are primary content source
```

### 8.2 Architectural Principles (Observed)

1. **Template-First**: All generators have complete template fallbacks
2. **Research Optional**: LLM data enhances but never replaces templates
3. **Fail-Safe**: System works even if all LLM APIs are down
4. **Cost-Conscious**: Minimal LLM calls by default, opt-in for premium features
5. **Centralized Fetch**: Single Perplexity call per pack (not per-section)

### 8.3 LLM Usage by Pack Tier

| Tier | Packs | Perplexity Avg | OpenAI Avg | Template Avg |
|------|-------|----------------|------------|--------------|
| **Basic** | 2 | 6.3% | 0% | 93.7% |
| **Standard** | 1 | 0% | 5.9% | 94.1% |
| **Premium** | 2 | 2.2% | 1.8% | 96.0% |
| **Enterprise** | 1 | 2.6% | 2.6% | 94.8% |
| **Specialized** | 4 | 3.6% | 0% | 96.4% |

**Key Finding**: Premium/Enterprise tiers do **NOT** have significantly higher LLM usage.

---

## 9. COST ANALYSIS

### 9.1 Per-Pack LLM Costs (Estimated)

| Pack | Perplexity | OpenAI (Base) | OpenAI (Agency Grade) | Total (Base) | Total (Premium) |
|------|------------|---------------|----------------------|--------------|-----------------|
| quick_social_basic | $0.005 | $0 | $0.03 | $0.005 | $0.035 |
| strategy_campaign_standard | $0.02 | $0.01 | $0.05 | $0.03 | $0.08 |
| full_funnel_growth_suite | $0.02 | $0 | $0.05 | $0.02 | $0.07 |
| launch_gtm_pack | $0.02 | $0 | $0.03 | $0.02 | $0.05 |
| brand_turnaround_lab | $0.02 | $0 | $0.03 | $0.02 | $0.05 |
| retention_crm_booster | $0.02 | $0 | $0.03 | $0.02 | $0.05 |
| performance_audit_revamp | $0.02 | $0 | $0.03 | $0.02 | $0.05 |
| strategy_campaign_premium | $0.02 | $0.01 | $0.05 | $0.03 | $0.08 |
| strategy_campaign_enterprise | $0.02 | $0.01 | $0.05 | $0.03 | $0.08 |

**Notes**:
- Base = Default configuration (no agency_grade)
- Premium = With agency_grade enhancement
- OpenAI costs assume gpt-4o-mini at $0.15/1M input, $0.60/1M output
- Perplexity costs at ~$0.005 per request (4 requests per pack)

### 9.2 Cost Distribution

**Average Pack** (without agency_grade):
- Perplexity: 67% ($0.02)
- OpenAI: 33% ($0.01)
- **Total**: $0.03

**Average Pack** (with agency_grade):
- Perplexity: 29% ($0.02)
- OpenAI: 71% ($0.05)
- **Total**: $0.07

**Key Finding**: Agency Grade enhancement increases cost by ~133% but is opt-in.

---

## 10. RECOMMENDATIONS

### 10.1 Quick Wins (Low Effort, High Value)

1. **Wire CreativeService to core strategy sections** (4-6 hours)
   - Target: core_campaign_idea, messaging_framework, value_proposition_map
   - Impact: 17% of sections get creative polish
   - Cost: +$0.03 per pack

2. **Use existing competitor data in competitor_benchmark** (1 hour)
   - Target: performance_audit_revamp pack
   - Impact: Research data already fetched, just wire it
   - Cost: $0 (already fetching)

3. **Integrate ResearchService into market sections** (6-8 hours)
   - Target: market_landscape, market_analysis, industry_landscape
   - Impact: 3 sections get real market data
   - Cost: $0 (data already available)

### 10.2 High-Value Enhancements (Medium Effort)

1. **Implement audience_pain_points fetching in Perplexity** (16 hours)
   - Current: Field exists but empty
   - Target: customer_insights, audience_analysis sections
   - Impact: 2 sections get real audience data
   - Cost: +$0.005 per pack

2. **Add creative_territories OpenAI generation** (12 hours)
   - Current: Hardcoded Starbucks example
   - Target: All packs with calendars
   - Impact: More brand-specific content angles
   - Cost: +$0.01 per pack

3. **Wire CreativeService.enhance_calendar_posts()** (8 hours)
   - Target: detailed_30_day_calendar, full_30_day_calendar
   - Impact: Better hooks and CTAs in calendars
   - Cost: +$0.02 per pack

### 10.3 Strategic Initiatives (High Effort)

1. **Migrate all research access to ResearchService** (40 hours)
   - Benefit: Unified API, better error handling, observability
   - Impact: All 83 sections use consistent research interface
   - Cost: $0 (refactor only)

2. **Implement selective polish strategy** (32 hours)
   - Logic: Polish high-value sections only (objectives, big ideas, messaging)
   - Benefit: 10-15 sections get creative enhancement
   - Cost: +$0.10-0.15 per pack

3. **Add market trends research to Perplexity** (24 hours)
   - Target: industry_landscape, market_analysis
   - Data: Industry trends, growth drivers, regulatory changes
   - Cost: +$0.005 per pack

### 10.4 Do NOT Do

1. ❌ **Add OpenAI to tactical/data sections** (kpi_plan, execution_roadmap, etc.)
   - Reason: Templates are better for structured data
   - Risk: Hallucinations in metrics/dates

2. ❌ **Enable humanizer LLM mode by default**
   - Reason: Deterministic mode works fine, costs $0
   - Risk: +$0.05 per pack for minimal benefit

3. ❌ **Polish all 83 sections with OpenAI**
   - Reason: Diminishing returns, high cost
   - Risk: +$0.50-1.00 per pack

---

## 11. FILE REFERENCE INDEX

### Core Files

| File | Lines | Purpose | LLM Usage |
|------|-------|---------|-----------|
| `backend/main.py` | 8331 | Main generation logic | Perplexity fetch (line 7834), CreativeService usage (line 641) |
| `aicmo/presets/package_presets.py` | 352 | Pack definitions | None (config only) |
| `backend/services/research_service.py` | 463 | Research orchestration | Not yet integrated |
| `backend/services/creative_service.py` | 425 | Creative enhancement | Used by 1 section |
| `backend/agency_grade_enhancers.py` | 652 | Turbo mode frameworks | OpenAI gpt-4o-mini |
| `backend/humanizer.py` | 299 | Generic phrase removal | Deterministic (no LLM) |
| `backend/creative_territories.py` | 181 | Brand content angles | Template-based (no LLM) |
| `backend/services/brand_research.py` | ~200 | Brand research wrapper | Perplexity integration |
| `backend/external/perplexity_client.py` | ~300 | Perplexity API client | Direct API calls |

### Generator Files (Sections)

All section generators located in `backend/main.py`:

- Lines 531-6192: Individual section generator functions (_gen_*)
- Line 6193: SECTION_GENERATORS registry (83 sections)
- Lines 6320-6420: generate_sections() orchestration function

### Test Files

- `backend/tests/test_research_service.py` - ResearchService tests
- `backend/tests/test_creative_service.py` - CreativeService tests
- `backend/tests/test_hashtag_strategy_perplexity.py` - Perplexity hashtag tests
- `backend/tests/test_brand_research_integration.py` - Brand research tests

---

## 12. CONCLUSIONS

### What Actually Uses LLMs?

**Perplexity (Research)**:
- Fetched once per pack in `/aicmo/generate` endpoint
- Used directly by 3 sections (3.6%)
- Available to all generators but mostly ignored

**OpenAI (Creative)**:
- Used by 1 section for polish (1.2%)
- Used by agency_grade enhancement (opt-in for all packs)
- Used by humanizer (disabled by default)
- Used by brief parsing (when needed)

**Templates**:
- Primary content source for 95.2% of sections
- All sections have complete fallbacks
- High quality, benchmarked, production-tested

### Architectural Strengths

1. ✅ **Reliability**: System works even if all LLMs fail
2. ✅ **Cost Control**: Minimal LLM usage by default
3. ✅ **Quality**: Templates are well-crafted and validated
4. ✅ **Fallbacks**: Every integration has safe degradation
5. ✅ **Flexibility**: LLM features are opt-in enhancements

### Architectural Gaps

1. ⚠️ **Underutilization**: ResearchService built but not integrated
2. ⚠️ **Underutilization**: CreativeService built but barely used
3. ⚠️ **Wasted Data**: Perplexity research fetched but ignored by 95% of sections
4. ⚠️ **Tier Confusion**: Premium/Enterprise tiers don't have more LLM usage
5. ⚠️ **Documentation Gap**: LLM architecture not clearly explained to users

### Strategic Direction

AICMO follows a **"Template-First with Optional Enhancement"** model:

- Templates provide reliable, fast, cost-effective baseline
- Perplexity adds factual research data when available
- OpenAI adds creative polish when needed
- All enhancements are optional and fail-safe

This is a **defensible architecture** for production systems that prioritize reliability and cost control over bleeding-edge AI usage.

---

**End of Audit**

**Next Actions**: Review findings with team, prioritize recommendations from Section 10, update LLM_ARCHITECTURE_V2.md to reflect actual implementation.
