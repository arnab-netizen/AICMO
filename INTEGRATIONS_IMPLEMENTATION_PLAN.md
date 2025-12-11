# INTEGRATIONS IMPLEMENTATION PLAN

## Overview
Transform stub integrations into real working implementations while maintaining safe fallback architecture.

## Items to Implement (from EXTERNAL_INTEGRATIONS_AUDIT_FINAL.md Section C)

### TIER 1: CRITICAL PATH (Backend integrations with API calls)

#### 1.1 Apollo Lead Enrichment
**Current State**: Stub at `/aicmo/gateways/adapters/apollo_enricher.py:45` (TODO comment)
**File**: `/aicmo/gateways/adapters/apollo_enricher.py`
**Interface Used**: `LeadEnricherPort` from `/aicmo/cam/ports.py`
**Factory**: `get_lead_enricher()` in `/aicmo/gateways/factory.py:178`
**Config Var**: `APOLLO_API_KEY`

**What to Implement**:
- Real HTTP calls to Apollo API (https://api.apollo.io/v1/people/search)
- Batch enrichment endpoint
- Extract fields: email status, company, job title, LinkedIn URL, phone
- Maintain safe no-op when APOLLO_API_KEY not set

**API Reference**: Apollo REST API v1
- Endpoint: POST `/people/search`
- Auth: Header `X-Api-Key: <API_KEY>`
- Rate limit: 300 req/min (free tier)

---

#### 1.2 Dropcontact Email Verification
**Current State**: Stub at `/aicmo/gateways/adapters/dropcontact_verifier.py:45` (TODO comment)
**File**: `/aicmo/gateways/adapters/dropcontact_verifier.py`
**Interface Used**: `EmailVerifierPort` from `/aicmo/cam/ports.py`
**Factory**: `get_email_verifier()` in `/aicmo/gateways/factory.py:197`
**Config Var**: `DROPCONTACT_API_KEY`

**What to Implement**:
- Real HTTP calls to Dropcontact API (https://api.dropcontact.io/v1)
- Single email verification
- Batch verification (if available in free tier)
- Return: valid (bool), status (string), reason (string)
- Maintain safe optimistic no-op when DROPCONTACT_API_KEY not set

**API Reference**: Dropcontact REST API v1
- Endpoint: POST `/contact-verify`
- Auth: Header `X-Dropcontact-ApiKey: <API_KEY>`
- Rate limit: Free tier allows limited calls

---

### TIER 2: EXPORT/OUTPUT (File generation)

#### 2.1 PPTX Generation
**Current State**: Stub at `/aicmo/delivery/output_packager.py:365`-`384`
**File**: `/aicmo/delivery/output_packager.py::generate_full_deck_pptx()`
**Depends On**: `python-pptx` library (NOT in requirements yet)
**Config**: No env var needed (should always work once library installed)

**What to Implement**:
- Use python-pptx to create PowerPoint from project data
- Slides: Title, Strategy, Creatives (per platform), Calendar, Metrics
- Export to temp directory with standard naming
- Return path to generated .pptx file
- Gracefully return None if python-pptx not installed

**Changes**:
1. Add `python-pptx>=0.6.21` to requirements.txt
2. Implement `generate_full_deck_pptx()` function
3. Use project_data dict structure already passed

---

#### 2.2 HTML Summary Export
**Current State**: Stub at `/aicmo/delivery/output_packager.py:404`
**File**: `/aicmo/delivery/output_packager.py::generate_html_summary()`
**Depends On**: Jinja2 (already in requirements)
**Config**: No env var needed

**What to Implement**:
- Use Jinja2 to render project data to HTML
- Create simple responsive HTML template (Bootstrap or similar)
- Sections: Overview, Strategy, Content Calendar, Assets
- Export to temp directory
- Return path to generated .html file
- Handle missing template gracefully

---

### TIER 3: CRM INTEGRATION

#### 3.1 Airtable CRM Adapter
**Current State**: Factory ready but adapter not implemented
**File**: Need to create `/aicmo/gateways/adapters/airtable_crm.py`
**Interface Used**: `CRMSyncerPort` (infer from factory at `factory.py:120`)
**Factory**: `get_crm_syncer()` in `/aicmo/gateways/factory.py:95`
**Config Var**: `AIRTABLE_API_TOKEN` + `AIRTABLE_BASE_ID` + `AIRTABLE_TABLE_ID`

**What to Implement**:
- Create AirtableCRMSyncer adapter
- Methods: `sync_campaign()`, `sync_lead()`, `sync_contact_event()`
- Use Airtable REST API v0 (simple HTTP)
- Maintain safe no-op when env vars not set

**API Reference**: Airtable REST API v0
- Base URL: https://api.airtable.com/v0/{baseId}/{tableName}
- Auth: Header `Authorization: Bearer <TOKEN>`
- Free tier: 100 req/sec

---

### TIER 4: LLM PROVIDER (Configuration wiring)

#### 4.1 Anthropic Claude Integration
**Current State**: Env var exists (`ANTHROPIC_API_KEY` in `/streamlit_app.py:94`) but no usage
**Files**: 
  - Layer 2: `/backend/layers/layer2_humanizer.py:38` (already accepts Optional[Callable])
  - Layer 4: `/backend/layers/layer4_section_rewriter.py:30` (same pattern)
**Config Var**: `ANTHROPIC_API_KEY`

**What to Implement**:
- Create Anthropic client provider in `/backend/anthropic_client.py`
- Wire to factory pattern in core config
- Allow Layer 2/4 to use Claude if ANTHROPIC_API_KEY set
- Maintain OpenAI fallback if Claude not configured

---

## Architecture Overview

All implementations follow this pattern:

```
┌─ Configuration (env vars) ─┐
│                             ↓
┌─ Factory (factory.py) ─────────┐
│  ├─ if CONFIGURED: return Real  │
│  └─ else: return NoOp          │
├─ Real Adapter (adapter.py)     │
│  ├─ HTTP calls to API          │
│  ├─ Data transformation        │
│  └─ Error handling            │
└─ No-op Adapter (noop.py)      │
   └─ Safe defaults             │
```

**Key Principles**:
1. **Zero Blocking**: Missing config/API never crashes system
2. **Safe Defaults**: No-ops return sensible defaults (true, empty, etc.)
3. **Configuration Gated**: Real adapters only active with explicit env vars
4. **Testing**: Mock tests verify both real and no-op paths

---

## Implementation Checklist

- [ ] Apollo Lead Enrichment (real API implementation)
- [ ] Dropcontact Email Verification (real API implementation)
- [ ] PPTX Export (python-pptx library integration)
- [ ] HTML Export (Jinja2 template rendering)
- [ ] Airtable CRM Adapter (new file + factory wiring)
- [ ] Anthropic Claude Wiring (config provider + Layer 2/4 integration)
- [ ] Unit tests for all new adapters
- [ ] Integration tests for factory pattern
- [ ] Documentation and example .env file
- [ ] Verification that no existing tests break

---

## External Dependency Additions

**To Add to requirements.txt**:
- `python-pptx>=0.6.21` - PPTX generation
- `airtable-python-wrapper>=2.2.1` - Airtable API (or use requests directly)
- `anthropic>=0.12.0` - Anthropic Claude API (optional, only if ANTHROPIC_API_KEY set)

**Already Present**:
- `requests` - HTTP calls (Apollo, Dropcontact)
- `jinja2` - HTML template rendering
- `openai` - OpenAI Claude (already working)

---

## Implementation Order

1. **Apollo & Dropcontact** (high ROI, lead enrichment is core CAM feature)
2. **PPTX & HTML Exports** (output quality, already have test stubs)
3. **Airtable CRM** (optional but useful, clear interface)
4. **Anthropic Claude** (config wiring only, doesn't add new code)

---

## Files to Modify/Create

| File | Action | Reason |
|------|--------|--------|
| `/aicmo/gateways/adapters/apollo_enricher.py` | Implement | Replace TODO with real API |
| `/aicmo/gateways/adapters/dropcontact_verifier.py` | Implement | Replace TODO with real API |
| `/aicmo/delivery/output_packager.py` | Implement 2 functions | PPTX + HTML generation |
| `/aicmo/gateways/adapters/airtable_crm.py` | CREATE | New CRM adapter |
| `/aicmo/gateways/factory.py` | Update | Wire Airtable into get_crm_syncer() |
| `/backend/anthropic_client.py` | CREATE | Anthropic provider |
| `/requirements.txt` | Add deps | python-pptx, airtable-python-wrapper |
| `/backend/tests/test_apollo_enricher.py` | CREATE | Unit + integration tests |
| `/backend/tests/test_dropcontact_verifier.py` | CREATE | Unit + integration tests |
| `/backend/tests/test_pptx_generation.py` | CREATE | PPTX export tests |
| `/backend/tests/test_airtable_crm.py` | CREATE | CRM sync tests |

---

## Next Steps

1. Read existing test patterns from `/backend/tests/test_phase4_gateways_execution.py`
2. Implement Apollo enrichment with real API calls + mocked tests
3. Implement Dropcontact verification with real API calls + mocked tests
4. Implement PPTX/HTML exports with template handling
5. Create Airtable CRM adapter from scratch
6. Wire Anthropic Claude to Layer 2/4 (config only)
7. Run full test suite to ensure no regressions
8. Generate completion report with env var examples
