# AICMO Provider Audit - Quick Reference

**Status**: ✅ Complete | **Evidence-Based**: ✅ Yes | **Recommendations**: ✅ Included

---

## Wiring Status by Category

### ✅ Fully Wired
- **Persistence (Database)** - DATABASE_URL (30+ usages), AICMO_MEMORY_DB (82+ usages), full fallback working

### ⚠️ Wired But Issues
- **LLM Generation** - ProviderChain present + used in generators, BUT CreativeService bypasses it with direct OpenAI SDK
- **Lead Enrichment** - ProviderChain chain set up, Apollo (3 usages) + Dropcontact (3 usages) working, but missing Hunter + PeopleDataLabs
- **Backend Routing** - HTTP pattern defined but not configured (BACKEND_URL/AICMO_BACKEND_URL not set at runtime)

### ❌ Missing/Incomplete
- **Web Search** - Only Perplexity present; SERPAPI (0 usages), Jina (0 usages) not found
- **Image Generation** - Only OpenAI adapter; REPLICATE (1 usage), STABILITY (0), FAL (0), HUGGINGFACE (0)
- **Email & Outreach** - Infrastructure (SMTP, Make) present but SendGrid (0 usages), Twilio (0 usages), Mailso (0 usages) missing

---

## Evidence Summary

| Metric | Count | Status |
|--------|-------|--------|
| ProviderChain instantiation points | 7 | ✅ Present in factory.py |
| LLM adapters present | 6 | Mistral, Cohere, DeepSeek, Llama, Perplexity, Grok |
| LLM generators using ProviderChain | 5 | Creative, Messaging, Persona, Social, SWOT |
| Environment variables tracked | 127 | Total across codebase |
| Environment variables configured (runtime) | 0 | Running in stub mode only |
| Lead enrichment providers implemented | 2/4 | Apollo, Dropcontact (missing Hunter, PeopleDataLabs) |
| Backend routing configured (runtime) | ❌ Not | BACKEND_URL not set |
| Persistence backends | 2/2 | Database + Memory (both working) |

---

## Key Files Referenced

**Architecture**:
- [aicmo/gateways/provider_chain.py](aicmo/gateways/provider_chain.py) - Core provider chain (531 lines)
- [aicmo/gateways/factory.py](aicmo/gateways/factory.py) - Gateway chain factory (590 lines)

**LLM Layer**:
- [aicmo/llm/router.py](aicmo/llm/router.py) - LLM client router (creates ProviderChain correctly)
- [aicmo/llm/client.py](aicmo/llm/client.py) - Direct SDK entry point (NOT ProviderChain)
- [backend/services/creative_service.py](backend/services/creative_service.py) - Polishing service (uses direct OpenAI, not ProviderChain)

**Generators**:
- [aicmo/creative/directions_engine.py](aicmo/creative/directions_engine.py) - Creative direction generation (uses ProviderChain ✅)
- [aicmo/generators/messaging_pillars_generator.py](aicmo/generators/messaging_pillars_generator.py)
- [aicmo/generators/persona_generator.py](aicmo/generators/persona_generator.py)
- [aicmo/generators/social_calendar_generator.py](aicmo/generators/social_calendar_generator.py)
- [aicmo/generators/swot_generator.py](aicmo/generators/swot_generator.py)

**Backends**:
- [backend/routers/cam.py](backend/routers/cam.py) - Campaign Autonomous Manager router
- [aicmo/cam/worker/cam_worker.py](aicmo/cam/worker/cam_worker.py) - CAM execution worker

---

## Critical Issues Found

### 🔴 Issue 1: CreativeService Bypasses ProviderChain
- **Location**: [backend/services/creative_service.py](backend/services/creative_service.py#L130-L150)
- **Problem**: Direct OpenAI SDK instead of using LLM ProviderChain
- **Impact**: Cannot fallback to other LLM providers; single point of failure on OpenAI
- **Fix**: Route through get_llm_client() → ProviderChain instead

### 🔴 Issue 2: Major Search Providers Missing
- **Missing**: SERPAPI, Jina
- **Present**: Only Perplexity (4 usages)
- **Impact**: Limited search capability; no web research integration
- **Fix**: Add SerpAPI and Jina adapters; integrate research service into generation pipeline

### 🔴 Issue 3: Image Generation Largely Missing
- **Present**: Only OpenAI adapter
- **Missing**: Replicate, Stability AI, FAL, Hugging Face
- **Usage**: REPLICATE_API_KEY (1 reference only)
- **Impact**: No multi-provider image generation; no fallback
- **Fix**: Implement multi-provider image chain with Replicate, Stability AI fallbacks

### 🟡 Issue 4: Email Providers Incomplete
- **Missing**: SendGrid (0 usages), Twilio (0 usages), Mailso (0 usages)
- **Present**: SMTP, Make webhook
- **Impact**: Limited email outreach options; cannot use commercial email platforms
- **Fix**: Add SendGrid, Twilio adapters to email ProviderChain

### 🟡 Issue 5: Backend Routing Not Configured
- **Pattern Defined**: [operator_v2.py](operator_v2.py#L760-L913)
- **Environment Variables**: BACKEND_URL, AICMO_BACKEND_URL (not set)
- **Current Behavior**: Runners return mock results
- **Fix**: Configure backend URLs; remove mock returns

---

## Recommended Implementation Order

1. **[CRITICAL]** Fix CreativeService
   - Route polish_section() through ProviderChain instead of direct SDK
   - This unlocks multi-provider LLM fallback for all generators
   - Estimated effort: 2 hours

2. **[HIGH]** Add Search Providers
   - Implement SerpAPI and Jina adapters
   - Create search_provider_chain in factory.py
   - Integrate into research service
   - Estimated effort: 4 hours

3. **[HIGH]** Add Image Generation Chain
   - Implement Replicate, Stability AI, FAL adapters
   - Create image_provider_chain in factory.py
   - Integrate into media service
   - Estimated effort: 6 hours

4. **[HIGH]** Complete Email Providers
   - Implement SendGrid and Twilio adapters
   - Add to email ProviderChain
   - Estimated effort: 4 hours

5. **[MEDIUM]** Add Missing Lead Enrichers
   - Hunter and PeopleDataLabs adapters
   - Add to lead enrichment chain
   - Estimated effort: 3 hours

6. **[MEDIUM]** Activate Backend Routing
   - Configure BACKEND_URL environment variable
   - Remove mock returns from runners
   - Test HTTP routing
   - Estimated effort: 2 hours

---

## Verification Commands

**Check Provider Configuration**:
```bash
python3 tools/smoke_provider_calls.py
```

**Trace LLM Usage**:
```bash
grep -rn "get_llm_client\|\.invoke(" aicmo/ backend/ --include="*.py" | grep -i llm
```

**Find ProviderChain Instantiations**:
```bash
grep -rn "ProviderChain(" aicmo/ backend/ --include="*.py" | grep -v "import\|class"
```

**Count Environment Variables**:
```bash
python3 tools/audit_env_keys.py
```

---

## Audit Artifacts

**Generated Files**:
1. **[AUDIT_MULTIPROVIDER_WIRING.md](AUDIT_MULTIPROVIDER_WIRING.md)** - Full audit report with evidence
2. **[tools/smoke_provider_calls.py](tools/smoke_provider_calls.py)** - Runtime provider check script
3. **[tools/audit_env_keys.py](tools/audit_env_keys.py)** - Environment variable audit script
4. **[tools/audit_provider_wiring.py](tools/audit_provider_wiring.py)** - Provider wiring quick scan

**Output Artifacts**:
1. `/tmp/smoke_provider_calls.txt` - Provider configuration status
2. `/tmp/audit_env_keys.txt` - 127 env vars, 541 usages
3. `/tmp/audit_provider_wiring_quick.txt` - Quick provider scan results

---

**Audit Status**: ✅ COMPLETE  
**Next Steps**: Review critical issues and prioritize implementation  
**Estimated Total Implementation Time**: 20-25 hours
