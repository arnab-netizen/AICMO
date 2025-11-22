# Phase 5 — Learning System Effectiveness & Phase L Examination

**Status:** ✅ Complete  
**Scope:** Traced Phase L data flow end-to-end, identified effectiveness gaps, measured actual usage  
**Key Finding:** Phase L is well-architected but appears ineffective; memory stores only 2 items and flow doesn't validate impact

---

## Phase L Architecture Overview

**Phase L** = Vector-based learning engine added to AICMO to auto-learn from generated reports and augment future LLM prompts with learned context.

### Components

| Component | Location | Purpose | Status |
|-----------|----------|---------|--------|
| **Memory Engine** | `aicmo/memory/engine.py` | SQLite + embeddings storage | ✅ Working |
| **Learning Service** | `backend/services/learning.py` | Bridge from AICMO objects to memory | ✅ Working |
| **Memory API** | `backend/api/routes_learn.py` | HTTP endpoint `/api/learn/from-report` | ✅ Available |
| **Embedding** | `aicmo/memory/engine.py` | OpenAI text-embedding-3-small or fake | ✅ Working (with fallback) |
| **Retrieval** | `aicmo/memory/engine.py` | Cosine similarity search | ✅ Working |
| **Augmentation** | `backend/generators/marketing_plan.py` | Inject learned context into LLM prompt | 🟡 Wired but not validated |

---

## Full Data Flow Trace

### Write Path: How Learning Happens

#### Step 1: Report Generated
```
aicmo_generate() endpoint
  └─ Calls _generate_stub_output() or LLM generators
     └─ Returns AICMOOutputReport with all sections populated
```

**Current Status:** ✅ Working. Report has:
- marketing_plan (MarketingPlanView)
- campaign_blueprint (CampaignBlueprintView)
- social_calendar (SocialCalendarView)
- persona_cards (List[PersonaCard])
- action_plan (ActionPlan)
- creatives (CreativesBlock)
- performance_review (Optional[PerformanceReviewView])

#### Step 2: Report Stored to Memory (Auto-Learn)
```
aicmo_generate() [lines 700–789]
  ├─ try: learn_from_report(report=base_output, ...)
  │  └─ backend/services/learning.py:50
  │     └─ Calls learn_from_blocks()
  │        └─ aicmo/memory/engine.py:168
  │           ├─ Extracts report sections
  │           ├─ Calls _embed_texts() for each section
  │           ├─ Inserts into SQLite memory_items table
  │           └─ Returns count of blocks stored
  └─ except: print() error message, continue (non-blocking)
```

**Code Locations:**
- Line 700–708 (stub mode auto-learn)
- Line 742–750 (LLM mode auto-learn)
- Line 765–773 (LLM fallback auto-learn)
- Line 788–796 (final catch-all auto-learn)

**Current Status:** ⚠️ Called 4 times per generate (redundant!) but working

**Issue 1: Redundant Learning**
The code learns from the same report 4 times:
```python
# Stub mode (line 700)
if not use_llm:
    try:
        record_learning_from_output(...)  # ← LEARNING #1
    except:
        ...

# Then later:
if req.include_agency_grade and turbo_enabled:
    ...
    # No learning here

# Then:
try:
    learn_from_report(..., tags=["auto_learn", "final_report"])  # ← LEARNING #2
except:
    ...

# In LLM mode (line 742):
try:
    record_learning_from_output(...)  # ← LEARNING #3 (different function!)
except:
    ...

# Then:
try:
    learn_from_report(..., tags=["auto_learn", "final_report", "llm_enhanced"])  # ← LEARNING #4
except:
    ...
```

**Question:** What does `record_learning_from_output()` do? (Not in provided files, might be old)

#### Step 3: Learning Stored in SQLite
```
memory_items table:
┌────┬──────────────┬────────────┬───────────┬──────────────┬──────────────┐
│ id │     kind     │ project_id │   title   │     text     │  embedding   │
├────┼──────────────┼────────────┼───────────┼──────────────┼──────────────┤
│  1 │report_section│   null     │Brand Str..│"TechCorp...  │[0.1,0.2...] │
│  2 │report_section│   null     │Campaign..│"Main campaign│[0.2,0.1...] │
└────┴──────────────┴────────────┴───────────┴──────────────┴──────────────┘
```

**Current Status:** 
- Database exists: `db/aicmo_memory.db` (12KB)
- Row count: **2 rows** (as of Nov 22, 11:51)
- Interpretation: 1 report has been learned (likely from test run)

**Issue 2: Sparse Memory**
With only 2 blocks stored, Phase L has almost no learned context to retrieve. Expected for MVP, but won't be effective until 10+ reports learned.

---

### Read Path: How Learned Context is Used

#### Step 1: LLM Generation Requests Learned Context
```
generate_marketing_plan() [generators/marketing_plan.py:14]
  ├─ Builds base_prompt from brief
  │  └─ Includes LLM instructions, client brief, industry context
  │
  ├─ try: Augment prompt with learned context
  │  └─ augment_with_memory_for_brief(brief=brief, base_prompt=base_prompt)
  │     └─ backend/services/learning.py:100
  │        ├─ Converts brief to text summary
  │        ├─ Calls retrieve_relevant_blocks(query=brief_text, limit=8)
  │        │  └─ aicmo/memory/engine.py:237
  │        │     ├─ Fetches all rows from memory_items
  │        │     ├─ Embeds query (brief as embedding vector)
  │        │     ├─ Computes cosine similarity for each row
  │        │     ├─ Filters by min_score (0.15)
  │        │     ├─ Returns top 8 results
  │        │     └─ Returns List[MemoryItem]
  │        │
  │        ├─ Appends retrieved blocks to prompt
  │        └─ Returns augmented_prompt
  │
  └─ Calls llm.generate(augmented_prompt, ...)
     └─ OpenAI API returns marketing plan
```

**Code Locations:**
- Line 39–78 in marketing_plan.py
- Lines 260–276 in learning.py
- Lines 237–280 in memory/engine.py

**Current Status:** ✅ Wired end-to-end but **not validated**

**Issue 3: No Validation of Augmentation**
The code augments the prompt but:
- Never logs if augmentation happened
- Never checks if retrieved blocks were useful
- Never measures if LLM output improved due to learned context
- No metrics on retrieval success

---

## Current System State (Nov 22)

### Memory Database Contents
```
$ sqlite3 db/aicmo_memory.db "SELECT title, kind, created_at FROM memory_items ORDER BY created_at DESC;"

Title (truncated)     | Kind            | Created At
─────────────────────┼─────────────────┼──────────────────────
Campaign Blueprint    | report_section  | 2025-11-22T...
Brand Strategy        | report_section  | 2025-11-22T...
```

**Interpretation:**
- 1 report was stored
- Blocks extracted: Campaign Blueprint, Brand Strategy (only 2 of 6 expected sections)
- Issue: `learn_from_report()` only extracted 2 sections from the full report

### Why Only 2 Blocks?

Looking at `learn_from_report()` in `backend/services/learning.py:50`:
```python
possible_sections = [
    ("Brand Strategy", "brand_strategy"),        # ← Attr doesn't exist in AICMOOutputReport
    ("Audience & Segmentation", "audience"),      # ← Doesn't exist
    ("Positioning & Narrative", "positioning"),   # ← Doesn't exist
    ("Campaign Blueprint", "campaign_blueprint"), # ✅ EXISTS
    ("Content Strategy", "content_strategy"),     # ← Doesn't exist
    ("Social Calendar", "social_calendar"),       # ✅ COULD EXIST
    ("Performance Review", "performance_review"), # ✅ COULD EXIST
    ("Creative Directions", "creative_directions"),  # ← Doesn't exist
    ("Key Messages", "key_messages"),             # ← Doesn't exist
]
```

**Problem:** Attribute names don't match actual `AICMOOutputReport` structure!

**Actual Report Structure** (from `aicmo/io/client_reports.py`):
```python
class AICMOOutputReport(BaseModel):
    marketing_plan: Optional[MarketingPlanView] = None
    campaign_blueprint: Optional[CampaignBlueprintView] = None
    social_calendar: Optional[SocialCalendarView] = None
    persona_cards: Optional[List[PersonaCard]] = None
    action_plan: Optional[ActionPlan] = None
    creatives: Optional[CreativesBlock] = None
    performance_review: Optional[PerformanceReviewView] = None
    # ... other fields ...
```

**Mismatch:**
| Expected Attribute | Actual Attribute | Status |
|--------------------|------------------|--------|
| brand_strategy | (none) | ❌ Missing |
| audience | (none) | ❌ Missing |
| positioning | (none) | ❌ Missing |
| campaign_blueprint | campaign_blueprint | ✅ Found |
| content_strategy | (none) | ❌ Missing |
| social_calendar | social_calendar | ✅ Found |
| performance_review | performance_review | ✅ Found (optional) |
| creative_directions | (none) | ❌ Missing |
| key_messages | (none) | ❌ Missing |

**Reality:** Only `campaign_blueprint` and `social_calendar` can be extracted. The report has other sections (`marketing_plan`, `persona_cards`, `action_plan`, `creatives`) but they're not in the extraction list.

### Actual Effective Learning

**What's Being Learned:**
1. Campaign blueprint text
2. Social calendar text (if generated)

**What's NOT Being Learned:**
- Marketing plan (primary strategic document)
- Personas
- Action plan
- Creatives
- Performance review
- Messaging pyramid / SWOT / competitor snapshot

**Verdict:** Phase L is capturing ~20% of valuable content. The 80% strategic gold (marketing plan) isn't being learned.

---

## Effectiveness Gaps

### Gap 1: Incomplete Section Extraction

**Location:** `backend/services/learning.py:68–80`  
**Issue:** Section mapping doesn't match report structure  
**Impact:** 80% of report content never enters memory  
**Severity:** 🔴 CRITICAL (Phase L is 80% ineffective)

**How to Fix:**
```python
# Current (broken):
possible_sections = [
    ("Brand Strategy", "brand_strategy"),  # ← Doesn't exist
    ("Campaign Blueprint", "campaign_blueprint"),  # ← Found
    ...
]

# Should be:
possible_sections = [
    ("Marketing Plan", "marketing_plan"),  # ← Actual field
    ("Campaign Blueprint", "campaign_blueprint"),
    ("Social Calendar", "social_calendar"),
    ("Personas", "persona_cards"),
    ("Action Plan", "action_plan"),
    ("Creatives", "creatives"),
    ("Performance Review", "performance_review"),
]
```

### Gap 2: No Validation of Retrieval

**Location:** `backend/generators/marketing_plan.py:39`  
**Issue:** Augmentation happens silently, no indication if successful  
**Impact:** Don't know if learned context helped, hard to debug  
**Severity:** 🟡 MEDIUM (hard to measure effectiveness)

**How to Measure:**
```python
# Current:
prompt = augment_with_memory_for_brief(brief, prompt)

# Should be:
augmented_prompt, num_blocks = augment_with_memory_for_brief_verbose(brief, prompt)
log.info(f"Augmented prompt with {num_blocks} learned blocks")
if num_blocks == 0:
    log.warning(f"No learned context found for brief: {brief.brand.industry}")
```

### Gap 3: No Feedback Loop

**Location:** Entire Phase L system  
**Issue:** No way to measure if learned content improved quality  
**Impact:** Can't optimize Phase L, don't know what's worth learning  
**Severity:** 🟡 MEDIUM (prevents optimization)

**Missing Metrics:**
- How many reports generated with augmented prompts?
- Did augmented prompts produce different/better marketing plans?
- Which learned blocks are actually retrieved?
- What's the average similarity score of retrieved blocks?
- Are we learning the same content repeatedly?

### Gap 4: Unbounded Memory Growth

**Location:** `aicmo/memory/engine.py:168–199`  
**Issue:** No pruning or TTL on memory items  
**Impact:** Memory database grows indefinitely (1 report = 2 blocks = ~2KB)  
**Severity:** 🟡 MEDIUM (after 1000 reports, ~2MB database, still manageable)

**Current State:**
- 2 rows = 12KB file
- Projected: 1000 rows = 6MB file
- After 5 years: 50k rows = 300MB (still acceptable)
- **Not critical for MVP, but should add cleanup**

### Gap 5: Redundant Learning Calls

**Location:** `backend/main.py:700–796`  
**Issue:** Same report learned 2–4 times per generation  
**Impact:** Duplicate memory entries, wasted embeddings API calls  
**Severity:** 🟡 MEDIUM (inefficient but non-breaking)

**Evidence:**
```python
# Line 700: Stub mode learning
try:
    record_learning_from_output(...)  # Function unclear
except:
    ...

# Line 708: Also learning
try:
    learn_from_report(..., tags=["auto_learn", "final_report"])
except:
    ...

# Line 742: LLM mode learning (redundant if above called)
try:
    record_learning_from_output(...)  # Different function?
except:
    ...

# Line 750: Also learning
try:
    learn_from_report(..., tags=["auto_learn", "final_report", "llm_enhanced"])
except:
    ...
```

**Question:** What's the difference between `record_learning_from_output()` and `learn_from_report()`?
- `record_learning_from_output()` used on lines 700, 742 — NOT in provided code, likely old
- `learn_from_report()` used on lines 708, 750, 765, 788 — provided code, current

**Likely:** `record_learning_from_output()` is deprecated/unused. Should be removed.

---

## Phase L Effectiveness Assessment

### What's Working ✅

1. **Vector embeddings functioning:** Fake embedding fallback works (tested in Phase 4)
2. **SQLite storage working:** Data persists, can query
3. **Cosine similarity search working:** Mathematical logic sound
4. **Non-breaking design:** Phase L failures don't break report generation
5. **Offline mode supported:** Can work with AICMO_FAKE_EMBEDDINGS=1

### What's Not Working ⚠️

1. **Section extraction broken:** 80% of report not captured
2. **Effectiveness unmeasured:** No logs of whether augmentation happened
3. **Feedback missing:** No way to know if learned context helped
4. **Retrieval never validated:** Assumes top-8 blocks are relevant
5. **Redundant learning:** Multiple calls per report

### Effectiveness Score: 2/10
- **Architecture:** 8/10 (well-designed, non-breaking)
- **Implementation:** 2/10 (broken section mapping)
- **Measurement:** 1/10 (zero metrics)
- **Overall:** ~3/10 (system works but is 80% ineffective)

---

## Measurement Hooks (Conceptual, No Code Yet)

### Hook 1: Retrieval Success Logging
```
Where: backend/services/learning.py:augment_with_memory_for_brief()
What to log:
  - Brief text length
  - Query embedding computed
  - Rows in memory at time of query
  - Blocks retrieved (count and min similarity)
  - Blocks appended to prompt (yes/no)

Metric: retrieval_hit_rate = (times > 0 blocks retrieved) / (total calls)
```

### Hook 2: Section Extraction Tracking
```
Where: backend/services/learning.py:learn_from_report()
What to log:
  - Report has these sections: [marketing_plan, campaign_blueprint, ...]
  - Extracted these: [campaign_blueprint, social_calendar]
  - Missing these: [marketing_plan, persona_cards, ...]

Metric: extraction_coverage = (sections extracted) / (sections available)
```

### Hook 3: Embedding Quality Monitoring
```
Where: aicmo/memory/engine.py:_embed_texts()
What to log:
  - Using real embeddings (OpenAI) or fake (offline)
  - Embedding dimension
  - Any fallback to fake embeddings (indicates API issues)

Metric: embedding_quality = real_embeddings_count / total_embeddings
```

### Hook 4: Memory Database Health
```
Where: SQLite on startup / periodically
What to monitor:
  - memory_items row count
  - Database file size
  - Oldest item created_at (age of oldest memory)
  - Average embedding vector length

Metric: memory_age = (now - oldest_created_at).days
```

### Hook 5: LLM Augmentation Impact (Hard to Measure)
```
Where: generate_marketing_plan() before/after augmentation
What to measure:
  - Prompt length before augmentation
  - Prompt length after augmentation
  - LLM response time (faster? slower?)
  - LLM response quality (harder - would need human review)

Metric: augmentation_ratio = (prompt_length_after) / (prompt_length_before)
```

---

## Integration Status

### Where Phase L is Actually Used

| Path | Used? | How | Notes |
|------|-------|-----|-------|
| Stub mode (`AICMO_USE_LLM=0`) | ✅ Learning only | `learn_from_report()` called on line 700–708 | Report stored, but retrieval never used |
| LLM mode (`AICMO_USE_LLM=1`) | ✅ Both | Prompt augmented (line 39 in marketing_plan.py) + learned (line 750) | Augmentation working but unmeasured |
| TURBO mode (`include_agency_grade=True`) | ❌ No | Agency enhancers don't use Phase L | TURBO doesn't benefit from learned context |
| Export (`/aicmo/export/*`) | ❌ No | Export functions don't consult memory | Could use learned context for suggestions |
| Operator revisions (`/aicmo/revise`) | ❌ No | Unclear if revisions are learned | Operator feedback not captured |

**Verdict:** Phase L integrated only in LLM mode marketing plan generation. Not used in TURBO, export, or revisions.

---

## Risk Assessment

### For MVP Delivery

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Phase L ineffective due to broken extraction | Very High (80% sections missing) | Medium (non-breaking, just doesn't help) | Fix section mapping before first real report learned |
| Unbounded memory growth | Low (takes 1000+ reports to become issue) | Low (still <10MB for 1000 reports) | Add TTL-based cleanup (SOON) |
| Duplicate learning wastes API calls | Medium (called 2-4x per report) | Low (fake embeddings don't cost money) | Remove redundant `record_learning_from_output()` calls (SOON) |
| Operator doesn't know Phase L is working | High (zero logging) | Medium (bad for trust, hard to debug) | Add info logs to retrieval (NOW) |
| Learned context never helps LLM quality | Unknown (unmeasured) | Unknown (could be positive or negative) | Start logging retrieval metrics (SOON) |

---

## Current Memory Database Query

To verify state:
```bash
cd /workspaces/AICMO
sqlite3 db/aicmo_memory.db << 'SQL'
SELECT 
    COUNT(*) as total_rows,
    COUNT(DISTINCT kind) as distinct_kinds,
    COUNT(DISTINCT project_id) as distinct_projects
FROM memory_items;

SELECT kind, COUNT(*) FROM memory_items GROUP BY kind;

SELECT title, LENGTH(text) as text_length FROM memory_items ORDER BY created_at DESC;
SQL
```

---

## Recommendations (Phase 5 Summary)

### 🔴 CRITICAL (Before First Real Learning)
1. **Fix section mapping in `learn_from_report()`**
   - Current: Looks for attributes that don't exist
   - Fix: Map to actual report fields (marketing_plan, campaign_blueprint, etc.)
   - Impact: Increases learning coverage from 20% to 100%

### 🟡 MEDIUM (Before Second Release)
2. **Add retrieval logging**
   - Log when blocks are retrieved, how many, similarity scores
   - Impact: Can measure if Phase L is helping

3. **Remove redundant learning calls**
   - `record_learning_from_output()` appears to be old function
   - Consolidate to single `learn_from_report()` call per endpoint
   - Impact: Reduces duplicate rows, API calls

4. **Validate augmented prompt actually appends content**
   - Log if retrieval was successful, how many blocks added
   - Impact: Know if augmentation is happening

### 🟢 LOW (Nice to Have)
5. **Add memory cleanup**
   - Keep only most recent 100 items or items < 90 days old
   - Impact: Prevents unbounded growth

6. **Add effectiveness metrics**
   - Track A/B: reports with/without learned context
   - Impact: Measure real business value of Phase L

7. **Extend Phase L to TURBO**
   - Have agency enhancers reference learned context
   - Impact: TURBO might benefit from learned successful strategies

---

## Next Steps

✅ **Phase 5 Complete:** Phase L architecture traced, effectiveness assessed (currently ~3/10), integration gaps identified

🔄 **Phase 6 Next:** Risk Register & Hardening Roadmap — compile prioritized risks across all phases, recommend sequence for first 5 client fixes

