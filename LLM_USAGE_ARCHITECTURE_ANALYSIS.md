# AICMO LLM Usage Architecture Analysis

**Generated:** 2025-12-03  
**Purpose:** Map all Perplexity and OpenAI usage across the AICMO codebase  
**Scope:** Backend services, generators, section functions, and API integration points

---

## Executive Summary

AICMO uses a **hybrid LLM architecture** with clear separation of concerns:

- **Perplexity (Sonar)**: Real-time brand research and competitive intelligence
- **OpenAI (GPT-4o-mini)**: Content generation, copywriting, and strategy text
- **Template-based**: Most section generators use deterministic f-string templates (no LLM)

**Key Finding:** The majority of AICMO's 70+ section generators are **template-based** (no LLM), with LLM usage reserved for specific high-value tasks (research, enhancement, and optional polish layers).

---

## 1. Perplexity Usage Map

### 1.1 Core Integration

**File:** `backend/external/perplexity_client.py`  
**Model:** `sonar` (Perplexity's search-augmented model)  
**API Base:** `https://api.perplexity.ai`

#### Functions:

| Function | Purpose | Pack/Section | Input | Output |
|----------|---------|--------------|-------|--------|
| `PerplexityClient.research_brand()` | Fetch brand research data | All packs (when enabled) | brand_name, industry, location | `BrandResearchResult` (JSON) |
| `PerplexityClient.fetch_hashtag_research()` | Fetch hashtag strategy data | Quick Social Pack | brand_name, industry, audience | Hashtag lists (keyword, industry, campaign) |
| `PerplexityClient._validate_hashtag_data()` | Validate hashtag format/length | Internal | hashtag_data dict | Cleaned hashtag lists |

**Configuration:**
```python
# backend/core/config.py
PERPLEXITY_API_KEY: str | None = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_BASE: str = os.getenv("PERPLEXITY_API_BASE", "https://api.perplexity.ai")
AICMO_PERPLEXITY_ENABLED: bool = os.getenv("AICMO_PERPLEXITY_ENABLED", "").lower() in ("true", "1", "yes")
```

### 1.2 Service Layer Integration

**File:** `backend/services/brand_research.py`  
**Function:** `get_brand_research(brand_name, industry, location)`

**Purpose:** Unified entry point for Perplexity research with caching, fallbacks, and validation.

**Usage Pattern:**
```python
from backend.services.brand_research import get_brand_research

research = get_brand_research("Starbucks", "Coffee & Cafes", "Seattle, WA")
# Returns: BrandResearchResult with fields:
#   - brand_summary: str
#   - current_positioning: str | None
#   - local_competitors: List[CompetitorInfo]
#   - hashtag_hints: List[str] (legacy)
#   - keyword_hashtags: List[str] (new v1)
#   - industry_hashtags: List[str] (new v1)
#   - campaign_hashtags: List[str] (new v1)
```

**Integration Points:**
- Called in `backend/main.py` at line 7546 during WOW pack generation
- Attached to `ClientInputBrief.brand.research` field
- Consumed by section generators via `getattr(b, "research", None)` pattern

### 1.3 Section Generators Using Perplexity Data

| Section ID | Generator Function | Usage | Data Fields |
|------------|-------------------|-------|-------------|
| `messaging_framework` | `_gen_messaging_framework()` | Injects positioning and competitor data into messaging | `research.current_positioning`, `research.local_competitors` |
| `hashtag_strategy` | `_gen_hashtag_strategy()` | **Primary v1 feature** - uses Perplexity hashtags with fallbacks | `research.keyword_hashtags`, `research.industry_hashtags`, `research.campaign_hashtags` |

**Code Example (hashtag_strategy generator):**
```python
# backend/main.py:3523-3594
def _gen_hashtag_strategy(req: GenerateRequest, **kwargs) -> str:
    research = getattr(b, "research", None)
    
    # Use Perplexity data if available
    if research and research.keyword_hashtags and len(research.keyword_hashtags) > 0:
        brand_tags = research.keyword_hashtags[:10]  # Perplexity-powered
    else:
        brand_tags = [normalize_hashtag(b.brand_name), ...]  # Fallback
    
    # Same pattern for industry_hashtags and campaign_hashtags
    # Output: 4-section markdown with Brand, Industry, Campaign, Best Practices
```

### 1.4 Research Data Model

**File:** `backend/research_models.py`

```python
class BrandResearchResult(BaseModel):
    brand_summary: str
    current_positioning: str | None = None
    local_competitors: List[CompetitorInfo] = []
    hashtag_hints: List[str] = []  # Legacy field (pre-v1)
    
    # Perplexity Hashtag Strategy v1 (new fields)
    keyword_hashtags: Optional[List[str]] = None
    industry_hashtags: Optional[List[str]] = None
    campaign_hashtags: Optional[List[str]] = None
    
    def apply_fallbacks(self, brand_name: str, industry: str) -> "BrandResearchResult":
        """Generate fallback hashtags if Perplexity data missing."""
        # Case-insensitive deduplication, # prefix enforcement, validation
```

---

## 2. OpenAI Usage Map

### 2.1 Core Client

**File:** `backend/services/llm_client.py`  
**Class:** `LLMClient`  
**Model:** `gpt-4o-mini` (default, configurable)

**Purpose:** Lightweight async wrapper around OpenAI API with retry logic, timeout protection, and error handling.

**Capabilities:**
- 3 retry attempts with exponential backoff
- 25-second timeout per attempt
- 7 specific exception handlers (auth, rate limit, API status, connection, timeout)
- All errors converted to HTTPException for consistent API responses

**Usage Pattern:**
```python
from backend.dependencies import get_llm

llm = get_llm()  # Returns LLMClient instance
response = await llm.generate(prompt, temperature=0.7, max_tokens=2000)
```

### 2.2 OpenAI Usage by Feature Area

#### A. **LLM Enhancement Layer (Optional)**

**Files:**
- `aicmo/llm/client.py` - Core enhancement functions
- `backend/llm_enhance.py` - Backend wrapper for pack enhancement

**Purpose:** Polish deterministic stub output with LLM-generated text (optional upgrade layer).

**Supported Models:**
- **Primary:** Claude Sonnet 4 (`claude-3-5-sonnet-20241022`) via `ANTHROPIC_API_KEY`
- **Fallback:** OpenAI GPT-4o-mini via `OPENAI_API_KEY`

**Function:** `enhance_with_llm(brief, stub_output, options)`

**What it enhances:**
- Marketing Plan executive summaries
- Campaign Blueprint core ideas
- Social Calendar strategy narratives
- Section-level text polishing (preserves structure, upgrades prose)

**Control:**
```python
# Set environment variable to enable
AICMO_USE_LLM=1  # Enables LLM enhancement
```

#### B. **Generator-Level LLM Usage**

Specific generators that **optionally** use LLM (fallback to template if disabled):

| Generator | File | LLM Function | Purpose | Fallback |
|-----------|------|--------------|---------|----------|
| `generate_persona()` | `aicmo/generators/persona_generator.py` | `_generate_persona_with_llm()` | Generate detailed B2B/B2C personas | Template persona from brief |
| `generate_swot()` | `aicmo/generators/swot_generator.py` | `_generate_swot_with_llm()` | Generate SWOT analysis | Generic SWOT template |
| `generate_messaging_pillars()` | `aicmo/generators/messaging_pillars_generator.py` | `_generate_messaging_pillars_with_llm()` | Generate 3-5 messaging pillars | Template pillars from brief |
| `generate_situation_analysis()` | `aicmo/generators/situation_analysis_generator.py` | `_generate_situation_analysis_with_llm()` | Generate 2-3 paragraph market analysis | Template analysis from industry preset |

**Control Pattern (all generators):**
```python
use_llm = os.environ.get("AICMO_USE_LLM", "0").lower() in ["1", "true", "yes"]

if use_llm:
    return _generate_with_llm(brief)  # OpenAI/Claude call
else:
    return _generate_stub(brief)  # Template-based fallback
```

#### C. **Brief Parser (Text → Structured Data)**

**File:** `aicmo/llm/brief_parser.py`  
**Function:** `build_brief_with_llm(raw_text, industry_key)`

**Purpose:** Convert unstructured client brief text into `ClientInputBrief` Pydantic model.

**Model:** `gpt-4o-mini` (or `AICMO_OPENAI_MODEL` env var)

**Input:** Raw client text (e.g., email, document)  
**Output:** Fully structured `ClientInputBrief` with all nested fields populated

**Usage:**
```python
raw_text = "We're a coffee shop in Seattle targeting young professionals..."
brief = build_brief_with_llm(raw_text, industry_key="food_beverage")
# Returns: ClientInputBrief with brand, audience, goal, voice, etc.
```

#### D. **Humanization Layer (Text Quality Enhancement)**

**File:** `backend/humanizer.py`, `backend/humanization_wrapper.py`

**Purpose:** Post-process generated text to fix:
- Template artifacts (`{brand_name}`, `INSERT_X`, `TBD`)
- Broken punctuation (`& .`, `..`, trailing commas)
- Awkward phrasing
- Placeholder text

**Model:** `gpt-4o-mini` (or `AICMO_HUMANIZER_MODEL` env var)

**Control:**
```python
# Enabled via environment variable
OPENAI_API_KEY=sk-...  # If set, humanization uses LLM
# If not set, falls back to heuristic regex cleanup
```

**Usage:**
```python
from backend.humanizer import humanize_report_text, HumanizerConfig

cleaned_text = humanize_report_text(
    raw_text,
    brief=brief,
    config=HumanizerConfig(fix_templates=True, fix_punctuation=True)
)
```

#### E. **Agency Grade Enhancement (Premium Polish)**

**File:** `backend/agency_grade_enhancers.py`

**Purpose:** Apply "agency-grade" polish to sections for premium packs.

**Model:** `gpt-4o-mini` (or `AICMO_OPENAI_MODEL` env var)

**Functions:**
- `apply_agency_grade_enhancements(report, brief)` - Main entry point
- `_call_llm_for_section(client, system_prompt, user_prompt)` - LLM wrapper

**Enhancement Types:**
- Expand bullet points into narrative prose
- Add strategic depth and specific examples
- Improve tone and professionalism
- Inject industry-specific insights

**Integration:** Called in pack generation pipeline for Standard/Premium/Enterprise packs.

#### F. **WOW Autofill (Client Brief Auto-Completion)**

**File:** `backend/services/wow_autofill.py`

**Purpose:** Auto-fill missing client brief fields using LLM inference.

**Model:** Claude Sonnet 4 (primary) or OpenAI GPT-4o-mini (fallback)

**Function:** `autofill_brief_fields(brief, section_id)`

**Use Cases:**
- Infer target audience from brand name + industry
- Generate pain points from business type
- Suggest KPIs from primary goal
- Complete incomplete brief inputs

---

## 3. Template-Based Sections (No LLM)

The **majority of AICMO section generators** use **deterministic f-string templates** with no LLM dependency.

### 3.1 All 70+ Section Generators

**File:** `backend/main.py` (lines 5900-5980)  
**Dictionary:** `SECTION_GENERATORS` - Maps section_id → generator function

**Pattern:**
```python
def _gen_section_name(req: GenerateRequest, **kwargs) -> str:
    b = req.brief.brand
    g = req.brief.goal
    a = req.brief.audience
    
    raw = f"""## Section Title
    
    {b.brand_name} serves {a.primary_customer} in the {b.industry} market...
    
    **Key Points:**
    - Point 1 based on {g.primary_goal}
    - Point 2 with industry context
    - Point 3 with strategic guidance
    
    ## Next Steps
    - Action 1
    - Action 2
    """
    
    return sanitize_output(raw, req.brief)
```

### 3.2 Major Template-Based Sections

| Section ID | Generator Function | Lines | Pack Usage | Complexity |
|------------|-------------------|-------|------------|------------|
| `overview` | `_gen_overview()` | 530-582 | All packs | Medium - injects brief fields |
| `campaign_objective` | `_gen_campaign_objective()` | 584-617 | Strategy/Campaign packs | Low - template with goals |
| `core_campaign_idea` | `_gen_core_campaign_idea()` | 619-654 | Strategy/Campaign packs | Low - brand hook template |
| `channel_plan` | `_gen_channel_plan()` | 756-809 | All packs | Medium - platform rotation logic |
| `audience_segments` | `_gen_audience_segments()` | 811-844 | Strategy/Full-Funnel packs | Low - demographic templates |
| `creative_direction` | `_gen_creative_direction()` | 901-950 | All packs | Medium - visual guidelines |
| `influencer_strategy` | `_gen_influencer_strategy()` | 952-1003 | Strategy/Full-Funnel packs | Medium - tiered influencer strategy |
| `promotions_and_offers` | `_gen_promotions_and_offers()` | 1005-1050 | Strategy/Campaign packs | Medium - offer templates |
| `detailed_30_day_calendar` | `_gen_detailed_30_day_calendar()` | 1106-1156 | Strategy/Campaign packs | High - weekly table format |
| `quick_social_30_day_calendar` | `_gen_quick_social_30_day_calendar()` | 1158-1520 | Quick Social pack | **Very High** - algorithmic calendar with duplicate prevention |
| `kpi_and_budget_plan` | `_gen_kpi_and_budget_plan()` | 1619-1663 | Standard/Premium packs | Medium - KPI table templates |
| `execution_roadmap` | `_gen_execution_roadmap()` | 1665-1774 | All packs | High - phased action plan |
| `post_campaign_analysis` | `_gen_post_campaign_analysis()` | 1776-1859 | Strategy/Campaign packs | Medium - retrospective template |
| `final_summary` | `_gen_final_summary()` | 1861-1932 | All packs | Low - recap template |
| `content_buckets` | `_gen_content_buckets()` | 3430-3512 | Quick Social pack | Medium - content type rotation |
| `hashtag_strategy` | `_gen_hashtag_strategy()` | 3514-3594 | Quick Social pack | **High** - Perplexity integration + fallbacks |
| `market_landscape` | `_gen_market_landscape()` | 5088-5179 | Full-Funnel/Launch packs | Medium - market sizing template |
| `competitor_analysis` | `_gen_competitor_analysis()` | 2706-2753 | Full-Funnel/Turnaround packs | Medium - competitive landscape |

**Note:** All template-based generators use `sanitize_output(raw, req.brief)` to clean placeholders before returning.

### 3.3 Quick Social 30-Day Calendar (No LLM)

**Special Case:** The most complex template-based generator in AICMO.

**File:** `backend/main.py:1158-1520`  
**Function:** `_gen_quick_social_30_day_calendar()`

**Complexity Features:**
- **No LLM calls** - entirely algorithmic
- Generates 30 unique daily posts with:
  - Rotating content buckets (Education, Proof, Promo, Community, Experience)
  - Rotating angles (Product spotlight, Store experience, Offer, UGC, BTS)
  - Platform rotation (Instagram, LinkedIn, Twitter)
  - Day-of-week mapping (e.g., Friday = Promo)
- **Duplicate prevention:** Tracks seen hooks in `seen_hooks` set
- **Industry-aware hooks:** Uses `backend/industry_config.py` vocabulary
- **Creative territories:** Calls `get_creative_territories_for_brief()` for brand alignment
- **Visual concepts:** Calls `generate_visual_concept()` for each post
- **Genericity detection:** Uses `is_too_generic()` scoring to retry weak hooks
- **Anti-duplicate retries:** Up to 5 attempts to generate unique hooks

**Output:** 30-row markdown table with columns:
- Date | Day | Platform | Theme | Hook | CTA | Asset Type | Status

**Example Row:**
```
| Nov 15 | Day 3 | Instagram | Education: Product spotlight | Discover the 3 ingredients that make our coffee stand out from the rest | Save this for later. | carousel | Planned |
```

---

## 4. High-Level Architecture Summary

### 4.1 Three-Tier Content Generation

```
┌─────────────────────────────────────────────────────────────┐
│                    CLIENT INPUT BRIEF                        │
│  (Structured data: brand, audience, goals, constraints)      │
└──────────────────────┬──────────────────────────────────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
       ▼               ▼               ▼
┌────────────┐  ┌────────────┐  ┌────────────┐
│ PERPLEXITY │  │  TEMPLATE  │  │   OPENAI   │
│  (Research)│  │ (70+ gens) │  │ (Optional) │
└─────┬──────┘  └─────┬──────┘  └─────┬──────┘
      │               │               │
      │               │               │
      ▼               ▼               ▼
┌─────────────────────────────────────────────────────────────┐
│              SECTION GENERATORS (backend/main.py)            │
│  - 70+ functions mapping section_id → markdown content       │
│  - Most use templates (f-strings)                            │
│  - Some inject Perplexity data (research.*)                  │
│  - None call OpenAI directly (templates only)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              POST-PROCESSING LAYERS (Optional)               │
│  - Humanization (fix templates, punctuation)                 │
│  - LLM Enhancement (polish prose, add depth)                 │
│  - Agency Grade (premium narrative expansion)                │
│  - Benchmark Validation (quality enforcement)                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              FINAL AICMO REPORT (Markdown/PDF)               │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Division of Work

| **Task Type** | **Provider** | **When Used** | **Cost Impact** |
|---------------|-------------|---------------|-----------------|
| **Brand Research** | Perplexity Sonar | Every pack generation (if enabled) | Low - 1-2 calls per pack |
| **Hashtag Research** | Perplexity Sonar | Quick Social pack only | Low - 1 call per pack |
| **Section Generation** | Templates (no LLM) | 95%+ of section content | Free |
| **Brief Parsing** | OpenAI GPT-4o-mini | When converting raw text to structured brief | Medium - 1 call per brief |
| **Content Enhancement** | OpenAI/Claude | Optional polish layer (if enabled) | High - 1 call per section enhanced |
| **Humanization** | OpenAI GPT-4o-mini | Optional cleanup layer (if enabled) | Medium - 1 call per section cleaned |
| **Agency Grade** | OpenAI GPT-4o-mini | Premium packs only (if enabled) | High - Multiple calls per pack |

### 4.3 Current Provider Usage

**What AICMO uses Perplexity for:**
1. ✅ **Brand research** - Competitive landscape, positioning, local competitors
2. ✅ **Hashtag strategy** - Keyword, industry, and campaign hashtags (v1 feature)
3. ❌ **NOT used for** - Content generation, copywriting, strategy text

**What AICMO uses OpenAI for:**
1. ✅ **Brief parsing** - Converting raw text to structured ClientInputBrief
2. ✅ **Optional enhancement** - Polishing template-generated text with LLM
3. ✅ **Humanization** - Fixing template artifacts and broken text
4. ✅ **Agency grade** - Premium narrative expansion
5. ✅ **Specific generators** - Persona, SWOT, Messaging Pillars (optional, with template fallback)
6. ❌ **NOT used for** - Research, hashtag discovery, competitive intelligence

---

## 5. Sections with No LLM (Template Only)

Based on `SECTION_GENERATORS` mapping and codebase analysis:

### 5.1 Purely Template-Based Sections

All of these sections use **deterministic f-string templates** with **no external API calls**:

<details>
<summary><strong>Click to expand: 60+ Template-Only Sections</strong></summary>

| Section ID | Pack Usage | Implementation |
|------------|------------|----------------|
| `account_audit` | Performance Audit pack | Rule-based metrics template |
| `ad_concepts` | Strategy/Campaign packs | Creative format templates |
| `ad_concepts_multi_platform` | Full-Funnel pack | Platform-specific ad templates |
| `audience_analysis` | Full-Funnel pack | Demographic template |
| `audience_segments` | Strategy/Full-Funnel packs | Segment templates (HVM, Switchers, etc.) |
| `awareness_strategy` | Full-Funnel pack | Top-of-funnel tactics template |
| `brand_audit` | Turnaround pack | Brand health template |
| `brand_positioning` | Turnaround pack | Positioning statement template |
| `campaign_level_findings` | Performance Audit pack | Campaign metrics template |
| `campaign_objective` | Strategy/Campaign packs | Goal-based template |
| `channel_plan` | All packs | Platform rotation template |
| `channel_reset_strategy` | Turnaround pack | Channel optimization template |
| `churn_diagnosis` | Retention/CRM pack | Churn analysis template |
| `competitor_analysis` | Full-Funnel/Turnaround packs | Competitive tier template |
| `competitor_benchmark` | Performance Audit pack | Competitor metrics template |
| `consideration_strategy` | Full-Funnel pack | Mid-funnel tactics template |
| `content_buckets` | Quick Social pack | Content type rotation logic |
| `content_calendar_launch` | Launch/GTM pack | Launch timeline template |
| `conversion_audit` | Performance Audit pack | Conversion funnel template |
| `conversion_strategy` | Full-Funnel pack | Bottom-funnel tactics template |
| `copy_variants` | Performance Audit pack | A/B test copy templates |
| `core_campaign_idea` | Strategy/Campaign packs | Brand hook template |
| `creative_direction` | All packs | Visual guidelines template |
| `creative_direction_light` | Quick Social pack | Simplified visual guide |
| `creative_performance_analysis` | Performance Audit pack | Creative metrics template |
| `creative_territories` | Full-Funnel/Premium packs | Creative theme templates |
| `customer_insights` | Full-Funnel/Turnaround packs | Pain points template |
| `customer_journey_map` | Retention/CRM pack | Journey stage table template |
| `customer_segments` | Retention/CRM pack | Lifecycle segment templates |
| `cxo_summary` | Enterprise/Premium packs | Executive summary template |
| `detailed_30_day_calendar` | Strategy/Campaign packs | Weekly content table |
| `email_and_crm_flows` | Strategy/Campaign packs | Email automation templates |
| `email_automation_flows` | Full-Funnel/Retention packs | Complex flow tables |
| `execution_roadmap` | All packs | Phased action plan template |
| `final_summary` | All packs | Recap template |
| `full_30_day_calendar` | Full-Funnel pack | Detailed weekly tables |
| `funnel_breakdown` | Full-Funnel pack | Funnel stage template |
| `hashtag_strategy` | Quick Social pack | **Perplexity-powered** (w/ fallbacks) |
| `industry_landscape` | Launch/GTM pack | Industry trends template |
| `influencer_strategy` | Strategy/Full-Funnel packs | Influencer tier template |
| `kpi_and_budget_plan` | Standard/Premium packs | KPI table template |
| `kpi_plan_light` | Quick Social pack | Light KPI template |
| `kpi_plan_retention` | Retention/CRM pack | Retention metrics template |
| `kpi_reset_plan` | Turnaround pack | New KPI framework template |
| `landing_page_blueprint` | Full-Funnel pack | Landing page wireframe |
| `launch_campaign_ideas` | Launch/GTM pack | Launch campaign templates |
| `launch_phases` | Launch/GTM pack | Phased launch plan |
| `loyalty_program_concepts` | Retention/CRM pack | Loyalty program templates |
| `market_analysis` | Full-Funnel pack | Market sizing template |
| `market_landscape` | Full-Funnel/Launch packs | Market dynamics template |
| `measurement_framework` | Performance Audit pack | Analytics setup template |
| `messaging_framework` | All packs | **Injects Perplexity data** (positioning, competitors) |
| `new_ad_concepts` | Performance Audit pack | Refresh ad creative templates |
| `new_positioning` | Turnaround pack | Repositioning template |
| `optimization_opportunities` | Performance Audit pack | Optimization checklist |
| `persona_cards` | Strategy/Full-Funnel packs | Persona template (or LLM-generated) |
| `platform_guidelines` | Quick Social pack | Platform best practices |
| `post_campaign_analysis` | Strategy/Campaign packs | Retrospective template |
| `post_purchase_experience` | Retention/CRM pack | Onboarding template |
| `problem_diagnosis` | Turnaround pack | Issue identification template |

(Continued...)

</details>

### 5.2 Missing/Stubbed Sections

Based on pack definitions and SECTION_GENERATORS mapping:

| Section ID | Status | Pack Assignment | Notes |
|------------|--------|-----------------|-------|
| `review_responder` | ✅ **Implemented** but not wired to any pack | None | Function exists (`_gen_review_responder()`), intentionally excluded from pack presets |
| `video_scripts` | ✅ **Implemented** with generator | Quick Social pack | Uses `backend/generators/social/video_script_generator.py` |
| `week1_action_plan` | ✅ **Implemented** with generator | Quick Social pack | Uses `backend/generators/action/week1_action_plan.py` |

**Note:** All sections in `SECTION_GENERATORS` dictionary have implementations. No missing/stubbed sections found.

---

## 6. Candidates for Migration

### 6.1 Sections That Could Move to Perplexity

**Current State:** Template-based  
**Opportunity:** Real-time research-backed content

| Section | Current Implementation | Perplexity Benefit | Priority |
|---------|----------------------|-------------------|----------|
| `competitor_analysis` | Generic competitor tier template | **Real competitor names, market share, positioning** from web search | 🔥 **High** |
| `market_landscape` | Static market sizing template | **Actual market data, trends, growth rates** from recent sources | 🔥 **High** |
| `industry_landscape` | Generic industry trends template | **Current industry news, regulations, disruptions** | Medium |
| `customer_insights` | Generic pain points template | **Real customer reviews, forums, social sentiment** | Medium |
| `influencer_strategy` | Generic influencer tier template | **Actual influencer names, follower counts, engagement rates** | Low |

### 6.2 Sections That Should Stay with OpenAI

**Rationale:** Creative/strategic tasks requiring generative capabilities

| Section | Current Implementation | Why OpenAI/Claude | Alternative |
|---------|----------------------|-------------------|-------------|
| `creative_direction` | Template with brand guidelines | **Creative storytelling, tone examples, visual concepts** | Keep template for speed |
| `core_campaign_idea` | Template with brand hook | **Original campaign concepts, taglines, angles** | Keep template for consistency |
| `messaging_framework` | Template + Perplexity positioning | **Crafting persuasive messaging, emotional appeals** | Current hybrid is optimal |
| `copy_variants` | Template with A/B test examples | **Original ad copy, subject lines, headlines** | Could enhance with GPT-4 |

### 6.3 Sections That Should Remain Template-Based

**Rationale:** Speed, cost, determinism, or structural requirements

| Section | Why Template-Based | LLM Would Not Improve |
|---------|-------------------|----------------------|
| `quick_social_30_day_calendar` | Complex algorithmic generation with duplicate prevention | LLM too slow/expensive for 30 posts |
| `kpi_and_budget_plan` | Structured table format with calculations | LLM unreliable for numeric precision |
| `execution_roadmap` | Phased checklist with dependencies | Template clarity beats LLM verbosity |
| `email_automation_flows` | Complex multi-flow tables | LLM struggles with nested table structures |
| `platform_guidelines` | Platform-specific best practices | Static guidelines more reliable than LLM |

---

## 7. Recommended Next Steps

### 7.1 Short-Term (High ROI, Low Effort)

1. **Expand Perplexity Integration to `competitor_analysis`**
   - Add `fetch_competitor_data()` to `perplexity_client.py`
   - Return: competitor names, market positions, recent news
   - Integrate into `_gen_competitor_analysis()` with fallback
   - **Impact:** Real competitive intelligence vs generic templates

2. **Expand Perplexity Integration to `market_landscape`**
   - Add `fetch_market_data()` to `perplexity_client.py`
   - Return: market size, growth rates, trends, forecasts
   - Integrate into `_gen_market_landscape()` with fallback
   - **Impact:** Actual market data vs placeholder numbers

3. **Add Perplexity Caching Layer**
   - Cache research results per (brand, industry, location) tuple
   - TTL: 7 days for brand research, 30 days for market data
   - **Impact:** Reduce API costs by 80%+ for repeat generations

### 7.2 Medium-Term (High Value, Medium Effort)

4. **Create Hybrid Generator Pattern**
   - Perplexity for research/data → Template for structure → Optional OpenAI polish
   - Example: `competitor_analysis` = Perplexity data + structured table template + GPT-4 narrative polish
   - **Impact:** Best of all worlds (accuracy + structure + prose quality)

5. **Add Perplexity to `customer_insights`**
   - Scrape customer reviews, Reddit threads, forum discussions
   - Extract pain points, feature requests, satisfaction scores
   - **Impact:** Real customer voice vs assumed pain points

6. **Implement Smart LLM Routing**
   - Use OpenAI for creative tasks (copy, ideas, hooks)
   - Use Perplexity for research tasks (data, facts, trends)
   - Use Templates for structural tasks (tables, roadmaps, checklists)
   - **Impact:** Cost optimization + quality improvement

### 7.3 Long-Term (Strategic)

7. **Build Multi-LLM Orchestration Layer**
   - Route tasks to optimal provider based on task type
   - Example: Perplexity → research → pass to GPT-4 → pass to Claude → final polish
   - **Impact:** Best-in-class output quality across all sections

8. **Implement Agentic Workflow for Research**
   - Perplexity fetches raw data → Agent validates → Agent fills gaps → Agent formats
   - Example: Competitor analysis = multi-step research + validation + synthesis
   - **Impact:** Production-grade research quality

9. **Add User-Configurable LLM Preferences**
   - Allow clients to choose: Speed (templates) vs Quality (LLM) vs Balance (hybrid)
   - Per-section toggles in UI: "Use AI enhancement for this section?"
   - **Impact:** User control + cost transparency

---

## 8. Configuration Reference

### 8.1 Environment Variables

```bash
# === PERPLEXITY ===
PERPLEXITY_API_KEY=pplx-xxxxx...        # Required for Perplexity features
PERPLEXITY_API_BASE=https://api.perplexity.ai  # Optional override
AICMO_PERPLEXITY_ENABLED=true           # Enable/disable Perplexity integration

# === OPENAI ===
OPENAI_API_KEY=sk-xxxxx...              # Required for LLM features
AICMO_OPENAI_MODEL=gpt-4o-mini          # Default model for OpenAI
AICMO_HUMANIZER_MODEL=gpt-4o-mini       # Model for humanization layer

# === CLAUDE (Alternative to OpenAI) ===
ANTHROPIC_API_KEY=sk-ant-xxxxx...       # Required for Claude features
AICMO_CLAUDE_MODEL=claude-3-5-sonnet-20241022  # Default Claude model

# === LLM CONTROL ===
AICMO_USE_LLM=1                         # Enable optional LLM enhancement (0=off, 1=on)
AICMO_STUB_MODE=1                       # Force stub/template mode (no API calls)
```

### 8.2 Stub Mode Logic

**File:** `backend/utils/config.py`

```python
def is_stub_mode() -> bool:
    """Return True if AICMO should use templates instead of LLM."""
    if os.getenv("AICMO_STUB_MODE") == "1":
        return True
    api_key = os.getenv("OPENAI_API_KEY") or ""
    return not bool(api_key.strip())  # Stub mode if no API key
```

**Behavior:**
- `AICMO_STUB_MODE=1` → Always use templates (override)
- `OPENAI_API_KEY` missing → Use templates (auto-fallback)
- `OPENAI_API_KEY` set → Use LLM (if enabled via `AICMO_USE_LLM=1`)

---

## 9. Testing & Validation

### 9.1 Test Coverage by Provider

| Provider | Test File | Coverage |
|----------|-----------|----------|
| **Perplexity** | `backend/tests/test_brand_research_integration.py` | ✅ Full coverage (4 tests) |
| **Perplexity** | `backend/tests/test_hashtag_strategy_perplexity.py` | ✅ Full coverage (20 tests) |
| **OpenAI** | `backend/tests/test_fullstack_simulation.py` | ✅ Integration tests |
| **Templates** | `backend/tests/test_benchmark_enforcement_smoke.py` | ✅ Quality validation tests |
| **Humanization** | `test_humanization.py` | ✅ Unit tests for cleanup |

### 9.2 Quality Assurance

**Validation Script:** `scripts/dev_validate_benchmark_proof.py`

**Purpose:** Proof that validation system works for both template and LLM-generated content.

**Tests:**
1. ✅ Markdown parser works
2. ✅ Quality checks work
3. ✅ Poor quality content rejected
4. ✅ Good quality content accepted
5. ✅ Poor hashtag strategy rejected (Perplexity v1)
6. ✅ Good hashtag strategy accepted (Perplexity v1)

**Result:** 6/6 tests passing ✅

---

## 10. Appendix: Complete Section Generator Map

<details>
<summary><strong>Click to expand: All 70+ Section Generators</strong></summary>

```python
# backend/main.py:5900-5980
SECTION_GENERATORS = {
    "account_audit": _gen_account_audit,
    "ad_concepts": _gen_ad_concepts,
    "ad_concepts_multi_platform": _gen_ad_concepts_multi_platform,
    "audience_analysis": _gen_audience_analysis,
    "audience_segments": _gen_audience_segments,
    "awareness_strategy": _gen_awareness_strategy,
    "brand_audit": _gen_brand_audit,
    "brand_positioning": _gen_brand_positioning,
    "campaign_level_findings": _gen_campaign_level_findings,
    "campaign_objective": _gen_campaign_objective,
    "channel_plan": _gen_channel_plan,
    "channel_reset_strategy": _gen_channel_reset_strategy,
    "churn_diagnosis": _gen_churn_diagnosis,
    "competitor_analysis": _gen_competitor_analysis,
    "competitor_benchmark": _gen_competitor_benchmark,
    "consideration_strategy": _gen_consideration_strategy,
    "content_buckets": _gen_content_buckets,
    "content_calendar_launch": _gen_content_calendar_launch,
    "conversion_audit": _gen_conversion_audit,
    "conversion_strategy": _gen_conversion_strategy,
    "copy_variants": _gen_copy_variants,
    "core_campaign_idea": _gen_core_campaign_idea,
    "creative_direction": _gen_creative_direction,
    "creative_direction_light": _gen_creative_direction_light,
    "creative_performance_analysis": _gen_creative_performance_analysis,
    "creative_territories": _gen_creative_territories,
    "customer_insights": _gen_customer_insights,
    "customer_journey_map": _gen_customer_journey_map,
    "customer_segments": _gen_customer_segments,
    "cxo_summary": _gen_cxo_summary,
    "detailed_30_day_calendar": _gen_detailed_30_day_calendar,
    "email_and_crm_flows": _gen_email_and_crm_flows,
    "email_automation_flows": _gen_email_automation_flows,
    "execution_roadmap": _gen_execution_roadmap,
    "final_summary": _gen_final_summary,
    "full_30_day_calendar": _gen_full_30_day_calendar,
    "funnel_breakdown": _gen_funnel_breakdown,
    "hashtag_strategy": _gen_hashtag_strategy,           # ← PERPLEXITY-POWERED (v1)
    "industry_landscape": _gen_industry_landscape,
    "influencer_strategy": _gen_influencer_strategy,
    "kpi_and_budget_plan": _gen_kpi_and_budget_plan,
    "kpi_plan_light": _gen_kpi_plan_light,
    "kpi_plan_retention": _gen_kpi_plan_retention,
    "kpi_reset_plan": _gen_kpi_reset_plan,
    "landing_page_blueprint": _gen_landing_page_blueprint,
    "launch_campaign_ideas": _gen_launch_campaign_ideas,
    "launch_phases": _gen_launch_phases,
    "loyalty_program_concepts": _gen_loyalty_program_concepts,
    "market_analysis": _gen_market_analysis,
    "market_landscape": _gen_market_landscape,
    "measurement_framework": _gen_measurement_framework,
    "messaging_framework": _gen_messaging_framework,     # ← PERPLEXITY-ENHANCED
    "new_ad_concepts": _gen_new_ad_concepts,
    "new_positioning": _gen_new_positioning,
    "optimization_opportunities": _gen_optimization_opportunities,
    "persona_cards": _gen_persona_cards,                 # ← OPTIONAL LLM
    "platform_guidelines": _gen_platform_guidelines,
    "post_campaign_analysis": _gen_post_campaign_analysis,
    "post_purchase_experience": _gen_post_purchase_experience,
    "problem_diagnosis": _gen_problem_diagnosis,
    "product_positioning": _gen_product_positioning,
    "promotions_and_offers": _gen_promotions_and_offers,
    "remarketing_strategy": _gen_remarketing_strategy,
    "reputation_recovery_plan": _gen_reputation_recovery_plan,
    "retention_drivers": _gen_retention_drivers,
    "retention_strategy": _gen_retention_strategy,
    "revamp_strategy": _gen_revamp_strategy,
    "review_responder": _gen_review_responder,          # ← NOT WIRED TO PACKS
    "risk_analysis": _gen_risk_analysis,
    "risk_assessment": _gen_risk_assessment,
    "sms_and_whatsapp_flows": _gen_sms_and_whatsapp_flows,
    "sms_and_whatsapp_strategy": _gen_sms_and_whatsapp_strategy,
    "strategic_recommendations": _gen_strategic_recommendations,
    "turnaround_milestones": _gen_turnaround_milestones,
    "ugc_and_community_plan": _gen_ugc_and_community_plan,
    "value_proposition_map": _gen_value_proposition_map,
    "video_scripts": _gen_video_scripts,
    "week1_action_plan": _gen_week1_action_plan,
    "weekly_social_calendar": _gen_weekly_social_calendar,
    "winback_sequence": _gen_winback_sequence,
}
```

</details>

---

**End of Analysis**  
**Total Generators Analyzed:** 70+  
**Perplexity Integrations:** 2 (brand research, hashtag strategy)  
**OpenAI Integrations:** 5 (brief parsing, enhancement, humanization, agency grade, optional generators)  
**Template-Only Generators:** 95%+ of section content
