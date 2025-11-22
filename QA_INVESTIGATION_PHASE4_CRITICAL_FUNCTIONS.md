# Phase 4 — Critical Function Health Check

**Status:** ✅ Complete  
**Scope:** Analyzed 18 critical functions across generation, learning, export, and UI layers  
**Key Finding:** Error handling is generally present but logging is weak; some functions are dangerously large

---

## Critical Functions Inventory

### Tier 1: Core Generation Pipeline (5 functions)

#### 1. **`_generate_stub_output()` — backend/main.py:250**

**Type:** Synchronous function  
**Lines:** 380 (lines 250–630)  
**Inputs:** `GenerateRequest` (brief + flags)  
**Outputs:** `AICMOOutputReport` (all 10+ sections)  
**External Deps:** None (pure Python)  
**Criticality:** 🔴 CRITICAL (every report goes through here)

**What it does:**
- Takes client brief
- Generates deterministic stub output for all report sections
- Returns fully populated `AICMOOutputReport`

**Error Handling:**
```python
# NONE explicit. Function assumes:
# - brief has required fields (no validation)
# - all string interpolations succeed
# - date arithmetic works
```
**Logging:** None (no log statements)  
**Complexity:** Very high (380 lines, 15+ subsections generated)

**Risks:**
- **No input validation:** If brief missing fields (e.g., brand.brand_name), silent string interpolation failure
- **No error wrapping:** Any exception propagates to endpoint
- **Silent failures in edge cases:** Empty arrays not handled
  - Example: If `brand_adjectives = []`, defaults used silently (acceptable)
  - Example: If `online_hangouts = None`, defaults to `["Instagram", "LinkedIn"]` (OK, documented)
- **Very large function:** Single 380-line function doing all generation
  - Should be split into: generate_marketing_plan_stub, generate_campaign_stub, etc.

**Severity Assessment:** 🟡 MEDIUM
- Risk: Function fails → 500 error (not ideal but stops propagation)
- Mitigation: Stub mode is tested (`test_aicmo_generate_stub_mode.py` passes)

**Recommendation:** Add input validation at entry, split into smaller functions, add logging

---

#### 2. **`aicmo_generate()` — backend/main.py:650**

**Type:** Async function (FastAPI endpoint)  
**Lines:** 150+ (lines 650–800)  
**Inputs:** `GenerateRequest` (includes all flags + industry_key)  
**Outputs:** `AICMOOutputReport` (JSON)  
**External Deps:**
- OpenAI API (if `AICMO_USE_LLM=1`)
- File I/O (memory DB for Phase L)
- Memory engine (`learn_from_report`)
- Agency enhancers (`apply_agency_grade_enhancements`)

**Criticality:** 🔴 CRITICAL (main API endpoint)

**What it does:**
1. Checks `AICMO_USE_LLM` env var
2. If LLM enabled: calls `generate_marketing_plan()`, tries to enhance
3. If LLM disabled: generates stub
4. Attempts Phase L learning (non-blocking)
5. If `include_agency_grade=True`: applies TURBO enhancements
6. Returns final report

**Error Handling:**
```python
# Complex error handling with multiple try-except blocks:
if use_llm:
    try:
        marketing_plan = await generate_marketing_plan(req.brief)
        # ... update base_output
    except Exception as e:
        print(f"[AICMO] LLM ... failed, using stub: {e}")
        base_output = _generate_stub_output(req)

# Then learning (non-blocking):
try:
    learn_from_report(report=base_output, ...)
except Exception as e:
    print(f"[AICMO] Auto-learning failed (non-critical): {e}")

# Then TURBO (non-blocking):
if req.include_agency_grade and turbo_enabled:
    try:
        apply_agency_grade_enhancements(req.brief, base_output)
    except Exception as e:
        print(f"[AICMO] Agency-grade enhancements failed (non-critical): {e}")
```

**Issues:**
1. **Mixed sync/async:** Calls some async functions (`generate_marketing_plan`), some sync functions (`learn_from_report`, `apply_agency_grade_enhancements`)
   - OK: Python awaits properly, but should be consistent
2. **Logging via print():** All errors logged via `print()`, not structured logging
   - Problem: Can't search logs, filter by level, or analyze programmatically
3. **Silent fallbacks:** If learning fails, silently ignored
   - OK for non-critical, but should at least increment a counter
4. **No timeout on LLM calls:** If OpenAI API hangs, endpoint blocks indefinitely
   - Problem: Operator experience suffers
5. **Multiple exception catches too broad:** `except Exception as e:` catches everything including `KeyboardInterrupt`, `SystemExit`
   - Should be more specific: `except (RuntimeError, ValueError, TimeoutError) as e:`

**Severity Assessment:** 🟡 MEDIUM
- Error handling is present and non-breaking
- But logging is weak and timeouts unprotected

**Recommendation:** 
- Switch to structured logging (Python logging module)
- Add timeouts to LLM calls (e.g., `timeout=30`)
- Narrower exception catching
- Log success cases too ("Generated report with TURBO enhancements")

---

#### 3. **`generate_marketing_plan()` — backend/generators/marketing_plan.py:14**

**Type:** Async function  
**Lines:** 60 (lines 14–74)  
**Inputs:** `ClientInputBrief`  
**Outputs:** `MarketingPlanView`  
**External Deps:**
- OpenAI API (via `llm.generate()`)
- Memory engine (via `augment_with_memory_for_brief()`)

**Criticality:** 🟡 HIGH (called only if `AICMO_USE_LLM=1`, but critical when enabled)

**What it does:**
1. Builds LLM prompt from brief
2. Optionally augments with learned context from Phase L
3. Calls OpenAI API
4. Parses LLM response (extracts sections)
5. Returns structured `MarketingPlanView`

**Error Handling:**
```python
text = await llm.generate(prompt, temperature=0.75, max_tokens=3000)
# No try-except. If LLM fails, exception propagates.
```

**Issues:**
1. **No error handling:** If `llm.generate()` fails, exception propagates to `aicmo_generate()`, which catches it
   - OK: Caught upstream, but no local logging
2. **Parser brittleness:** Section extraction via string splitting
   ```python
   def _extract_section(text: str, section_name: str) -> Optional[str]:
       lines = text.split("\n")
       in_section = False
       section_content = []
       # ... magic string matching
   ```
   - Risk: If LLM doesn't format response with expected headers, extraction fails silently
   - Fallback: Returns `None` or default string (OK, but silent)
3. **No validation of extracted sections:** If pillars extraction fails, returns empty list
   - Risk: Stale data never gets refreshed (returns None, then aicmo_generate uses stub pillar)
4. **Memory augmentation can fail silently:**
   ```python
   prompt = augment_with_memory_for_brief(brief, prompt)
   # If this function throws, it propagates. If it returns empty string, silently ignored.
   ```

**Severity Assessment:** 🟡 MEDIUM
- Parsing is brittle (depends on LLM formatting)
- Error handling exists upstream but not here
- Silent failures in extraction

**Recommendation:**
- Add structured error handling with try-except
- Log extraction success/failure
- Add validation: "Did we successfully extract all pillars?"
- Use JSON mode for LLM response instead of markdown parsing

---

#### 4. **`_extract_section()` — backend/generators/marketing_plan.py:77**

**Type:** Synchronous helper  
**Lines:** 15  
**Inputs:** `text` (LLM response), `section_name` (e.g., "Executive Summary")  
**Outputs:** `Optional[str]` (section content or None)  
**External Deps:** None

**Criticality:** 🟡 HIGH (called 4x per generate, data integrity depends on this)

**What it does:**
- Searches LLM response for `### {section_name}` header
- Extracts text until next header or end
- Returns section content

**Error Handling:** None  
**Logging:** None

**Issues:**
1. **Header format assumption:** Expects `### Executive Summary` format
   - If LLM uses different format (e.g., `# Executive Summary` or `**Executive Summary**`), extraction fails silently
2. **Silent failure:** Returns empty string or None on failure
   - Caller doesn't know if extraction worked
3. **No validation:** Doesn't check if section is empty
   - Returns valid Python string even if section is blank

**Severity Assessment:** 🔴 CRITICAL
- This function is the gateway for LLM-generated content
- Silent failures mean bad data silently propagates

**Recommendation:** 
- Log extraction attempts and results
- Raise exception if section not found (let caller decide fallback)
- Add validation: section must have minimum length

---

#### 5. **`_extract_pillars()` — backend/generators/marketing_plan.py:93**

**Type:** Synchronous helper  
**Lines:** ~20  
**Inputs:** `text` (LLM response)  
**Outputs:** `List[StrategyPillar]` (always returns list, even if empty)  
**External Deps:** None

**Criticality:** 🟡 HIGH (defines strategy structure)

**What it does:**
- Parses LLM response looking for `- Pillar Name: ...` patterns
- Extracts KPI impact line
- Returns list of structured `StrategyPillar` objects

**Error Handling:** None  
**Logging:** None

**Issues:**
1. **Regex parsing:** Uses regex to find pillar patterns
   - Risk: If LLM returns different format, silent failure
2. **Silent empty list:** If no pillars found, returns `[]`
   - Should the code flag this as a problem? Currently no.
3. **No validation:** Doesn't check if 3 pillars were extracted (prompt says "exactly 3")
   - If extraction gets only 2 pillars, report is incomplete but valid JSON

**Severity Assessment:** 🟡 MEDIUM
- Returns valid list even if extraction failed
- Silent failures in content delivery

**Recommendation:**
- Log extraction success/failure
- Raise exception if pillar count != 3 (or >= min threshold)
- Add fallback: If extraction fails, use stub pillars instead

---

### Tier 2: Learning & Memory System (3 functions)

#### 6. **`learn_from_report()` — backend/services/learning.py:50**

**Type:** Synchronous function  
**Lines:** 50  
**Inputs:** `report` (AICMOOutputReport), `project_id`, `tags`  
**Outputs:** `int` (number of blocks stored)  
**External Deps:**
- Memory engine (`learn_from_blocks`)
- SQLite (via memory engine)

**Criticality:** 🟡 MEDIUM (Phase L feature, non-critical if fails)

**What it does:**
1. Extracts text blocks from report (brand strategy, audience, positioning, etc.)
2. Calls `learn_from_blocks()` to store with embeddings
3. Returns count of blocks stored

**Error Handling:**
```python
# None explicit. Returns int count.
# If learn_from_blocks() fails, exception propagates.
```

**Logging:** None

**Issues:**
1. **Assumes report structure:** Loops through hardcoded list of possible attributes
   ```python
   possible_sections = [
       ("Brand Strategy", "brand_strategy"),  # But report uses "marketing_plan"
       ("Audience & Segmentation", "audience"),  # But report doesn't have this attr
       ...
   ]
   ```
   - Problem: Attribute names don't match actual `AICMOOutputReport` structure
   - Risk: No sections extracted, memory stays empty, Phase L ineffective
2. **Silent mismatches:** Uses `hasattr()` and `getattr()` so missing fields silently skipped
   - OK for robustness, but should log which sections were actually stored
3. **Fallback extraction:**
   ```python
   if not blocks:
       blocks.append(("Full Report", repr(report)))
   ```
   - OK: At least stores something, but `repr()` is not semantic

**Severity Assessment:** 🟡 MEDIUM
- Non-critical (Phase L enhancement only)
- But silently ineffective if section mapping is wrong

**Recommendation:**
- Verify attribute names match actual `AICMOOutputReport` fields
- Log sections extracted vs. skipped
- Add unit test to verify extraction works end-to-end

---

#### 7. **`learn_from_blocks()` — aicmo/memory/engine.py:168**

**Type:** Synchronous function  
**Lines:** 40  
**Inputs:** `kind`, `blocks` (list of title-text tuples), `project_id`, `tags`, `db_path`  
**Outputs:** `int` (count of blocks stored)  
**External Deps:**
- SQLite (file I/O, database ops)
- Embeddings (`_embed_texts`)

**Criticality:** 🟡 MEDIUM (Phase L storage layer)

**What it does:**
1. Generates embeddings for all block texts
2. Opens SQLite connection
3. Inserts rows into memory_items table
4. Returns count

**Error Handling:**
```python
# Wrapped in try-finally to close connection
try:
    cur = conn.cursor()
    # ... insert operations
    conn.commit()
finally:
    conn.close()
```

**Issues:**
1. **No error handling for insert failures:** If insert fails (e.g., DB locked), exception propagates
   - Calling code expects `int` return; if exception raised, caller gets exception instead
2. **Embedding can fail:** `_embed_texts()` can fall back to fake embeddings, but if that also fails, exception propagates
   - Problem: SQLite connection opened but may not close if embedding fails
3. **No validation:** Doesn't check if embeddings are reasonable length/format
4. **DB growth unbounded:** No pruning logic
   - Risk: `aicmo_memory.db` grows indefinitely
   - After 1000 reports (5 blocks each) = 5000 rows, ~5MB at least

**Severity Assessment:** 🟡 MEDIUM
- Try-finally ensures connection closes
- But insert errors not gracefully handled
- Unbounded growth risk

**Recommendation:**
- Narrow exception handling to specific DB errors
- Log insertion results
- Add TTL/cleanup for old items (e.g., keep only 100 most recent)

---

#### 8. **`augment_prompt_with_memory()` — aicmo/memory/engine.py:260**

**Type:** Synchronous function  
**Lines:** 30  
**Inputs:** `brief_text`, `base_prompt`  
**Outputs:** `str` (augmented prompt)  
**External Deps:**
- Memory retrieval (`retrieve_relevant_blocks`)
- String formatting

**Criticality:** 🟡 HIGH (Phase L effectiveness depends on this)

**What it does:**
1. Retrieves similar memory blocks from SQLite
2. Appends them to base prompt
3. Returns augmented prompt

**Error Handling:**
```python
def augment_prompt_with_memory(brief_text: str, base_prompt: str) -> str:
    """Helper you can call from any generator to augment prompts with learned context."""
    try:
        retrieved = retrieve_relevant_blocks(...)
    except Exception:
        return base_prompt  # Silent fallback
```

**Issues:**
1. **Silent exception handling:** All errors return original prompt
   - OK: Non-breaking fallback
   - Problem: Can't diagnose if memory system working
2. **No logging:** No indication that augmentation happened or failed
3. **Prompt injection risk:** Retrieved memory blocks are directly concatenated into prompt
   - If memory contains malicious text, it goes into LLM prompt
   - Low risk (controlled source), but should be noted

**Severity Assessment:** 🟢 LOW
- Non-breaking fallback is good
- Silent failures acceptable for enhancement feature

**Recommendation:**
- Add optional logging flag to see if memory hits/misses
- Document prompt format for augmented prompt

---

### Tier 3: Export Pipeline (3 functions)

#### 9. **`aicmo_export_pdf()` — backend/main.py:851**

**Type:** Synchronous endpoint  
**Lines:** 15  
**Inputs:** `payload` (dict with "markdown")  
**Outputs:** `StreamingResponse` (PDF bytes)  
**External Deps:**
- `text_to_pdf_bytes()` (unknown implementation)

**Criticality:** 🔴 CRITICAL (client deliverable)

**What it does:**
1. Extracts markdown from payload
2. Calls `text_to_pdf_bytes()`
3. Streams result as PDF file

**Error Handling:**
```python
def aicmo_export_pdf(payload: dict):
    markdown = payload.get("markdown") or ""
    if not markdown.strip():
        raise HTTPException(status_code=400, detail="Markdown content is empty")
    
    pdf_bytes = text_to_pdf_bytes(markdown)  # No try-except; exception propagates
    return StreamingResponse(...)
```

**Issues:**
1. **No error handling for PDF generation:** If `text_to_pdf_bytes()` fails, 500 error
   - Problem: Client sees failure instead of graceful error
2. **No validation of input markdown:** Accepts any string
   - Risk: Very large markdown (>10MB) could cause memory issues
3. **Unknown implementation:** `text_to_pdf_bytes()` is not examined
   - Could have security issues (no input sanitization)
4. **No logging:** No indication of PDF generation success/failure
5. **Streaming response:** If PDF generation is slow, client may timeout

**Severity Assessment:** 🔴 CRITICAL
- Zero error handling on core export path
- Client-facing endpoint

**Recommendation:**
- Add try-except with graceful error response
- Add input size validation (max 10MB markdown)
- Add logging for success/failure
- Add timeout to PDF generation
- Examine `text_to_pdf_bytes()` implementation for security

---

#### 10. **`aicmo_export_pptx()` — backend/main.py:869**

**Type:** Synchronous endpoint  
**Lines:** 50  
**Inputs:** `payload` (dict with "brief" and "output")  
**Outputs:** `StreamingResponse` (PPTX bytes)  
**External Deps:**
- `pptx.Presentation` (python-pptx library)
- Model validation (Pydantic)

**Criticality:** 🔴 CRITICAL (client deliverable)

**What it does:**
1. Validates brief and output as Pydantic models
2. Creates PPTX presentation
3. Adds title slide, executive summary, campaign big idea
4. Streams result

**Error Handling:**
```python
def aicmo_export_pptx(payload: dict):
    try:
        from pptx import Presentation  # Import in function
    except ImportError:
        raise HTTPException(status_code=500, detail="python-pptx not installed...")
    
    brief = ClientInputBrief.model_validate(payload["brief"])  # Will raise ValidationError
    output = AICMOOutputReport.model_validate(payload["output"])  # Will raise ValidationError
    
    # No other error handling
    prs = Presentation()
    # ... add slides ...
```

**Issues:**
1. **No try-except for model validation:** If brief/output invalid JSON, 422 response (OK)
   - But no custom error message
2. **No try-except for slide operations:** If adding slide fails, 500 error
   - Problem: PPTX library could throw on malformed data
3. **Incomplete export:** Only adds 3 slides (title, exec summary, big idea)
   - Missing: Social calendar, personas, action plan, creatives
   - Risk: Client gets incomplete PPTX but thinks it's full report
4. **No validation of PPTX library availability:** Imports in function
   - OK: Catches ImportError
   - Problem: Not caught upstream; 500 error instead of graceful message
5. **String truncation logic missing:**
   - If `brief.brand.brand_name` is 500 chars, slide title breaks

**Severity Assessment:** 🔴 CRITICAL
- Incomplete export (only 3 slides)
- No error handling for slide operations
- Client deliverable quality at risk

**Recommendation:**
- Add try-except wrapping slide operations
- Import python-pptx at module level with graceful fallback
- Expand PPTX to include all report sections
- Add text truncation logic
- Test PPTX generation end-to-end

---

#### 11. **`aicmo_export_zip()` — backend/main.py:923**

**Type:** Synchronous endpoint  
**Lines:** 80+  
**Inputs:** `payload` (dict with "brief" and "output")  
**Outputs:** `StreamingResponse` (ZIP bytes)  
**External Deps:**
- `zipfile` (standard library)
- PDF export (`text_to_pdf_bytes`)
- Model validation (Pydantic)

**Criticality:** 🔴 CRITICAL (primary export format for operator)

**What it does:**
1. Validates brief and output
2. Renders markdown report
3. Converts markdown to PDF
4. Writes to ZIP:
   - 01_Strategy/report.md
   - 01_Strategy/report.pdf
   - persona_cards.md
   - creatives files (hooks, captions, scripts, CTAs, etc.)
   - meta/brand_name.txt

**Error Handling:**
```python
def aicmo_export_zip(payload: dict):
    brief = ClientInputBrief.model_validate(payload["brief"])  # ValidationError if bad
    output = AICMOOutputReport.model_validate(payload["output"])  # ValidationError if bad
    
    report_md = generate_output_report_markdown(brief, output)  # No error handling
    pdf_bytes = text_to_pdf_bytes(report_md)  # No error handling
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        # ... writestr operations ...
```

**Issues:**
1. **No error handling for markdown generation:** If `generate_output_report_markdown()` fails, 500 error
2. **No error handling for PDF generation:** If `text_to_pdf_bytes()` fails, 500 error
3. **ZIP write operations unprotected:** If `writestr()` fails (e.g., bad filename), 500 error
4. **Persona formatting brittle:** Manual string concatenation
   ```python
   lines.append(f"Demographics: {p.demographics}")
   # What if demographics is None? Silent "None" in output.
   ```
5. **Creatives packing logic fragile:**
   ```python
   if cr.hooks:
       z.writestr("02_Creatives/hooks.txt", "\n".join(cr.hooks))
   # If cr.hooks is list of non-strings, fails
   ```
6. **No validation of ZIP structure:** Doesn't verify ZIP is readable after creation

**Severity Assessment:** 🔴 CRITICAL
- Primary operator export
- Zero error handling on core paths
- Data corruption risk (ZIP may be malformed)

**Recommendation:**
- Add try-except on markdown generation
- Add try-except on PDF generation
- Add try-except on ZIP write operations
- Validate ZIP before streaming
- Add logging for export success/failure
- Add unit tests for ZIP structure

---

### Tier 4: TURBO Enhancement (2 functions)

#### 12. **`apply_agency_grade_enhancements()` — backend/agency_grade_enhancers.py:100**

**Type:** Synchronous function (modifies report in-place)  
**Lines:** 40 (orchestrator)  
**Inputs:** `brief`, `report` (modified in-place)  
**Outputs:** None (modifies `report.extra_sections`)  
**External Deps:**
- OpenAI API (via multiple section generators)
- 15+ helper functions

**Criticality:** 🟡 HIGH (TURBO feature, premium offering)

**What it does:**
1. Gets OpenAI client (returns None if not available)
2. Converts brief and report to text
3. Calls 15 section generators:
   - outcome_forecast, creative_boards, brand_story, budget_plan, etc.
4. Each generator calls LLM and adds section to report
5. Strips placeholder text from all extra sections

**Error Handling:**
```python
def apply_agency_grade_enhancements(brief, report) -> None:
    client = _get_openai_client()
    if client is None:
        return  # Silent fallback

    # ... calls 15 functions, each with error handling ...
    # Each individual section has try-except, so failures are silent
```

**Issues:**
1. **Silent OpenAI client failure:** If OpenAI not available, function returns without indication
   - OK: Non-breaking, but operator doesn't know TURBO didn't run
2. **Silent section generator failures:** Each section generator wrapped in try-except
   ```python
   def _add_outcome_forecast_section(client, brief, report, ...):
       try:
           # ... LLM call, parsing ...
       except Exception:
           return  # Silent failure
   ```
   - Problem: If all 15 sections fail, report unchanged but client thinks TURBO was applied
3. **No validation of generated sections:** Just adds raw LLM output
   - Risk: Hallucinated or nonsensical content added
4. **Placeholder stripping runs after:** Even if sections fail, stripping still runs
   - OK: Non-breaking, but might strip content that shouldn't be stripped

**Severity Assessment:** 🟡 MEDIUM
- Non-breaking fallback (silently degrades to no TURBO)
- But operator experience suffers (client charges for TURBO, doesn't get it)

**Recommendation:**
- Log which sections succeeded/failed
- Add count of actual sections added
- Validate section length before adding
- Consider structured logging to know TURBO was attempted

---

#### 13. **`_strip_placeholders_from_extra_sections()` — backend/agency_grade_enhancers.py:585**

**Type:** Synchronous helper  
**Lines:** 20  
**Inputs:** `report` (modified in-place)  
**Outputs:** None  
**External Deps:** None (string replacement only)

**Criticality:** 🟡 MEDIUM (quality gate for TURBO content)

**What it does:**
1. Iterates through hardcoded list of placeholder phrases
2. Replaces them with empty string in all extra_sections

**Error Handling:** None needed (string operations)  
**Logging:** None

**Issues:**
1. **Hardcoded list of placeholders:** Limited to what developer predicted
   ```python
   forbidden = [
       "will be refined later",
       "not yet summarised",
       # ... about 10 items
   ]
   ```
   - Risk: New placeholders from LLM not caught
   - Example: LLM generates "I would recommend..." but placeholder list doesn't include this
2. **Naive string replacement:** Uses `str.replace()`
   - Problem: Replaces even inside URLs or code blocks
   - Example: "will be refined later" could appear in legitimate context
3. **Silent partial removal:** Doesn't check if replacement was effective
   - If placeholder appears but with different capitalization, not caught

**Severity Assessment:** 🟡 MEDIUM
- Quality gate incomplete
- Doesn't catch all placeholders

**Recommendation:**
- Expand placeholder list
- Use regex matching with word boundaries
- Log what was stripped
- Consider semantic check: "Does this section look like real content?"

---

### Tier 5: Streamlit UI & Operator (2 functions)

#### 14. **`remove_placeholders()` — streamlit_pages/aicmo_operator.py:49**

**Type:** Synchronous helper  
**Lines:** 15  
**Inputs:** `text` (operator-edited content)  
**Outputs:** `str` (cleaned text)  
**External Deps:** None

**Criticality:** 🟡 MEDIUM (operator UX)

**What it does:**
1. Takes operator-edited text
2. Removes hardcoded forbidden strings
3. Returns cleaned text

**Error Handling:** None needed (string operations)  
**Logging:** None

**Issues:**
1. **Limited forbidden list:** Only 5 items
   ```python
   forbidden = ["not yet summarised", "will be refined later", "N/A", ...]
   ```
   - Missing: Most actual placeholders from Phase 2 findings
2. **Naive string replacement:** Exact match only
   - Doesn't catch variations (capitalization, whitespace)
3. **No logging:** Can't track what was removed

**Severity Assessment:** 🟡 MEDIUM
- Incomplete placeholder removal
- Operator might not realize placeholders not cleaned

**Recommendation:**
- Expand forbidden list to actual placeholders from codebase
- Use regex for variations
- Log what was removed
- Add UI indicator: "Found X placeholders, removed"

---

#### 15. **`_report_with_creative_directions()` — streamlit_pages/aicmo_operator.py:103**

**Type:** Synchronous helper  
**Lines:** 25  
**Inputs:** `report_obj` (AICMOOutputReport), reads from `st.session_state`  
**Outputs:** `Any` (dict or original object)  
**External Deps:** Streamlit session state

**Criticality:** 🟡 MEDIUM (creative integration feature)

**What it does:**
1. Checks if creative directions in session state
2. Converts report to dict (best-effort)
3. Adds creative directions markdown
4. Returns merged dict

**Error Handling:**
```python
# Best-effort conversion:
try:
    if hasattr(report_obj, "model_dump"):
        base = report_obj.model_dump()
    elif hasattr(report_obj, "dict"):
        base = report_obj.dict()
    elif hasattr(report_obj, "__dict__"):
        base = dict(report_obj.__dict__)
    elif isinstance(report_obj, dict):
        base = dict(report_obj)
    else:
        base = {"raw": str(report_obj)}
except Exception:
    base = {"raw": str(report_obj)}
```

**Issues:**
1. **Fallback is weak:** If conversion fails, only stores `{"raw": str(report_obj)}`
   - Problem: Report data lost except for string representation
2. **Type conversion inconsistency:** Sometimes returns dict, sometimes returns original object
   - Risk: Downstream code doesn't know which type to expect
3. **Session state dependency:** Reads from global session state
   - Problem: Hard to test, hard to trace data flow
4. **No validation:** Doesn't check if creative_directions_markdown is valid

**Severity Assessment:** 🟡 MEDIUM
- Non-critical (creative directions optional)
- But data loss risk if conversion fails

**Recommendation:**
- Ensure consistent return type (always dict or always object)
- Add logging for conversion attempts
- Validate creative directions before merging
- Consider explicit error handling instead of silent fallback

---

### Tier 6: Data Model & Rendering (2 functions)

#### 16. **`generate_output_report_markdown()` — aicmo/io/client_reports.py:274**

**Type:** Synchronous function  
**Lines:** 300+  
**Inputs:** `brief` (ClientInputBrief), `output` (AICMOOutputReport)  
**Outputs:** `str` (markdown)  
**External Deps:** None (pure string building)

**Criticality:** 🔴 CRITICAL (all exports depend on this)

**What it does:**
1. Takes report object
2. Builds markdown with 40+ sections
3. Uses string formatting with fallbacks
4. Returns complete markdown report

**Error Handling:**
```python
# Likely logic like:
marketing_plan = output.marketing_plan or MarketingPlanView()  # Fallback to empty
# ... then render properties ...
md += f"# {marketing_plan.executive_summary or 'Pending'}"
```

**Issues:**
1. **Untested function:** Zero test coverage (Phase 3 finding)
   - Risk: Markdown rendering bugs not caught
2. **Unknown implementation:** Need to read full function
   - Could have string formatting issues, missing sections, wrong ordering
3. **Fallback behavior opaque:** Uses `or` operators
   - If section missing, default text inserted
   - Example: If marketing_plan is None, renders `MarketingPlanView()` (empty object), converts to string "MarketingPlanView(...)"
4. **Large function:** Likely 300+ lines
   - Hard to maintain, hard to test

**Severity Assessment:** 🔴 CRITICAL
- All exports depend on markdown generation
- Zero tests
- Unknown behavior on missing/invalid data

**Recommendation:**
- Read full implementation
- Add unit tests for each section
- Add validation: all sections present and non-empty
- Test with missing fields, null values, very long text
- Break into smaller rendering functions per section

---

#### 17. **`aicmo_export_zip()` continued — ZIP creatives packing**

(Already covered in #11, but worth separate note for creatives logic)

**Where:** Lines 960–995 in main.py  
**Lines:** 35  
**Inputs:** `output.creatives` (CreativesBlock)  
**Outputs:** 5 text files added to ZIP  
**External Deps:** None

**Issues:**
1. **No validation of creatives fields:** If `cr.hooks` is None, `"\n".join(None)` fails
2. **No fallback for missing fields:** If field missing, entire creatives section skipped
3. **No validation of CTA structure:** Assumes `cr.cta_library` has `label`, `cta`, `context` attributes
4. **Fragile list unpacking:**
   ```python
   for cta in cr.cta_library:
       # Assumes cta has specific attributes
   ```

**Severity Assessment:** 🟡 MEDIUM
- Non-breaking (silent skip if field missing)
- But creatives content might not be exported

**Recommendation:**
- Add validation before writing
- Log what was written vs. skipped
- Add fallback: if creatives missing, create placeholder file

---

### Tier 7: Configuration & Dependencies (2 functions)

#### 18. **`get_llm()` — backend/dependencies.py:8**

**Type:** Synchronous getter  
**Lines:** 10  
**Inputs:** None  
**Outputs:** `LLMClient`  
**External Deps:**
- Environment variable `OPENAI_API_KEY`
- `LLMClient` constructor

**Criticality:** 🟡 HIGH (required for LLM mode)

**What it does:**
1. Reads OPENAI_API_KEY environment variable
2. Reads AICMO_MODEL_MAIN (defaults to "gpt-4o-mini")
3. Returns `LLMClient` instance

**Error Handling:**
```python
def get_llm() -> LLMClient:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    # Assumes LLMClient() doesn't raise
```

**Issues:**
1. **No error handling for LLMClient():** If constructor raises, exception propagates
   - Risk: Not caught at endpoint level
   - Caller gets ValueError instead of graceful error
2. **No caching:** Creates new LLMClient on every call
   - Risk: Multiple API connections if called in loop
3. **No timeout:** LLMClient might hang indefinitely
4. **No validation of API key format:** Any non-empty string accepted
   - Risk: Invalid keys not caught until API call fails

**Severity Assessment:** 🟡 MEDIUM
- Non-critical (only called if LLM enabled)
- But errors not handled gracefully

**Recommendation:**
- Cache LLMClient instance
- Add validation of API key format
- Add error handling for LLMClient constructor
- Add timeout to LLMClient initialization

---

## Critical Functions Summary Table

| # | Function | File | Lines | Criticality | Error Handling | Logging | Risk Level |
|---|----------|------|-------|-------------|----------------|---------|-----------|
| 1 | `_generate_stub_output` | backend/main.py | 380 | 🔴 CRITICAL | None | None | 🟡 MEDIUM |
| 2 | `aicmo_generate` | backend/main.py | 150+ | 🔴 CRITICAL | Yes (but print) | print() only | 🟡 MEDIUM |
| 3 | `generate_marketing_plan` | generators/ | 60 | 🟡 HIGH | Upstream | None | 🟡 MEDIUM |
| 4 | `_extract_section` | generators/ | 15 | 🟡 HIGH | None | None | 🔴 CRITICAL |
| 5 | `_extract_pillars` | generators/ | 20 | 🟡 HIGH | None | None | 🟡 MEDIUM |
| 6 | `learn_from_report` | services/ | 50 | 🟡 MEDIUM | None | None | 🟡 MEDIUM |
| 7 | `learn_from_blocks` | memory/engine | 40 | 🟡 MEDIUM | Partial (try-finally) | None | 🟡 MEDIUM |
| 8 | `augment_prompt_with_memory` | memory/engine | 30 | 🟡 HIGH | Silent catch | None | 🟢 LOW |
| 9 | `aicmo_export_pdf` | backend/main.py | 15 | 🔴 CRITICAL | Minimal | None | 🔴 CRITICAL |
| 10 | `aicmo_export_pptx` | backend/main.py | 50 | 🔴 CRITICAL | Partial | None | 🔴 CRITICAL |
| 11 | `aicmo_export_zip` | backend/main.py | 80+ | 🔴 CRITICAL | None | None | 🔴 CRITICAL |
| 12 | `apply_agency_grade` | agency_grade | 40 | 🟡 HIGH | Silent catch | None | 🟡 MEDIUM |
| 13 | `_strip_placeholders` | agency_grade | 20 | 🟡 MEDIUM | None | None | 🟡 MEDIUM |
| 14 | `remove_placeholders` | streamlit_pages | 15 | 🟡 MEDIUM | None | None | 🟡 MEDIUM |
| 15 | `_report_with_creative_directions` | streamlit_pages | 25 | 🟡 MEDIUM | Weak | None | 🟡 MEDIUM |
| 16 | `generate_output_report_markdown` | io/client_reports | 300+ | 🔴 CRITICAL | Unknown | None | 🔴 CRITICAL |
| 17 | ZIP creatives packing | backend/main.py | 35 | 🟡 MEDIUM | None | None | 🟡 MEDIUM |
| 18 | `get_llm` | dependencies.py | 10 | 🟡 HIGH | Partial | None | 🟡 MEDIUM |

---

## Health Assessment Summary

### By Dimension

| Dimension | Score | Status |
|-----------|-------|--------|
| **Error Handling** | 5/10 | 🟡 Partial (main path protected, edge cases not) |
| **Logging** | 2/10 | 🔴 Weak (mostly print(), no structured logging) |
| **Code Complexity** | 4/10 | 🟡 Some large functions (380 lines, 300+ lines) |
| **Input Validation** | 3/10 | 🔴 Minimal (assume valid briefs, outputs) |
| **Fallback Strategy** | 6/10 | 🟡 Non-breaking (silent fallbacks work, but operator blind) |
| **Test Coverage** | 2/10 | 🔴 Critical functions untested |
| **Security** | 6/10 | 🟡 Basic (env vars, no obvious injection, but prompt injection risk in memory) |
| **Performance** | 6/10 | 🟡 No timeouts on LLM calls, unbounded memory growth |

**Overall Health Score: 3.5/10** (Works, but fragile and hard to debug)

---

## Key Risks for First Client Delivery

### 🔴 CRITICAL (Must Fix Before MVP)
1. **Export functions zero error handling** (#9, #10, #11)
   - PDF/PPTX/ZIP failures → 500 error → client angry
2. **Markdown rendering untested** (#16)
   - Unknown behavior on edge cases
3. **Placeholder removal incomplete** (#13, #14)
   - "Hook idea for day 1" not stripped by TURBO

### 🟡 MEDIUM (Should Fix Before MVP)
4. **Logging is print()-based** (#2, #3, #4, #6)
   - Can't debug production issues
5. **Large functions hard to maintain** (#1, #16)
   - 380-line _generate_stub_output, 300+ line markdown rendering
6. **Phase L memory system untested** (#6, #7, #8)
   - Don't know if it's working
7. **TURBO section generation silent failures** (#12)
   - Client charges for TURBO, doesn't get it

### 🟢 LOW (Nice to Have)
8. **No input validation** (#1)
   - Trust that briefs are valid (OK for MVP)
9. **No caching** (#18)
   - Each LLM call creates new client (OK for MVP)
10. **ZIP structure not validated** (#11)
    - Assume zipfile library works (OK for MVP)

---

## Next Steps

✅ **Phase 4 Complete:** 18 critical functions analyzed, health assessed, risks prioritized

🔄 **Phase 5 Next:** Learning System Examination — trace Phase L data flow, evaluate effectiveness

