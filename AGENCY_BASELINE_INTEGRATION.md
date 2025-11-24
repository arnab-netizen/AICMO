## 🔌 Agency Baseline – Integration Patterns

**How to wire the new baselines into your existing generators and APIs.**

---

## Pattern 1: Wrap Existing Generator

Most direct way: wrap your current LLM call with baseline.

### Before
```python
# backend/generators/strategy.py
def generate_strategy(brief: dict) -> str:
    system = "You are a marketing strategist..."
    user = f"Brief:\n{brief}"
    return call_llm(system, user)  # Raw, potentially messy output
```

### After
```python
# backend/generators/strategy.py
from aicmo.agency.baseline import apply_agency_baseline

def generate_strategy(brief: dict) -> str:
    system = "You are a marketing strategist..."
    user = f"Brief:\n{brief}"
    raw_draft = call_llm(system, user)
    
    # Apply agency baseline
    return apply_agency_baseline(
        brief=brief,
        raw_draft=raw_draft,
        llm=call_llm,
        pack_key="agency_strategy_default",
    )
```

**Result:** Same 2 LLM calls (1 draft, 1 per stage of baseline = 5 more), but output is guaranteed 14-section agency structure.

---

## Pattern 2: Backend API Endpoint

Expose baseline as optional parameter in your API.

### Current Endpoint
```python
# backend/main.py
@app.post("/api/aicmo/generate_report")
async def generate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    client_brief = payload.get("client_brief")
    raw_output = generate_from_llm(client_brief)
    return {"report_markdown": raw_output}
```

### Enhanced with Baseline
```python
# backend/main.py
from aicmo.agency.baseline import apply_agency_baseline, apply_quick_social_baseline

@app.post("/api/aicmo/generate_report")
async def generate_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    client_brief = payload.get("client_brief")
    service_type = payload.get("service_type")  # "strategy" | "social" | etc
    use_agency_baseline = payload.get("use_agency_baseline", True)  # default ON
    
    raw_output = generate_from_llm(client_brief)
    
    if use_agency_baseline:
        if service_type == "strategy":
            final_output = apply_agency_baseline(
                brief=client_brief,
                raw_draft=raw_output,
                llm=call_llm,
            )
        elif service_type == "social":
            final_output = apply_quick_social_baseline(
                brief=client_brief,
                raw_draft=raw_output,
                llm=call_llm,
            )
        else:
            final_output = raw_output
    else:
        final_output = raw_output
    
    return {"report_markdown": final_output}
```

**Client call:**
```python
response = requests.post(
    "http://localhost:8000/api/aicmo/generate_report",
    json={
        "client_brief": {"brand_name": "Acme", "objectives": "Growth"},
        "service_type": "strategy",
        "use_agency_baseline": True,  # ← Baseline is ON
    },
)
```

---

## Pattern 3: Streamlit Integration

Add baseline to your Streamlit workflow.

### Before
```python
# streamlit_pages/aicmo_operator.py
if st.button("Generate report"):
    report_md = call_backend_generate(stage="draft")
    st.markdown(report_md)  # May be messy
```

### After
```python
# streamlit_pages/aicmo_operator.py
from aicmo.agency.baseline import apply_agency_baseline

def get_llm_function():
    """Return LLM function for baseline."""
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def llm(system: str, user: str) -> str:
        completion = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=6000,
            temperature=0.7,
        )
        return completion.choices[0].message.content or ""
    
    return llm

if st.button("Generate report"):
    with st.spinner("Generating..."):
        report_md = call_backend_generate(stage="draft")
    
    # Apply agency baseline
    brief = st.session_state["client_brief_meta"]
    if brief.get("brand_name"):
        llm_func = get_llm_function()
        report_md = apply_agency_baseline(
            brief=brief,
            raw_draft=report_md,
            llm=llm_func,
        )
    
    st.markdown(report_md)  # Guaranteed 14 sections
```

---

## Pattern 4: Conditional Baseline by Package

Different packages = different baselines.

```python
from aicmo.agency.baseline import apply_agency_baseline, apply_quick_social_baseline

BASELINE_BY_PACKAGE = {
    "Full-Funnel Growth Suite": ("strategy", "agency_strategy_default"),
    "Launch & GTM Pack": ("strategy", "agency_strategy_default"),
    "Brand Turnaround Lab": ("strategy", "agency_strategy_default"),
    "Always-on Content Engine": ("social", "quick_social_agency_default"),
    "Quick Social Pack (Basic)": ("social", "quick_social_agency_default"),
}

def generate_with_package(brief: dict, package_name: str) -> str:
    raw_draft = call_llm_for_package(brief, package_name)
    
    baseline_type, pack_key = BASELINE_BY_PACKAGE.get(
        package_name, 
        ("strategy", "agency_strategy_default")
    )
    
    if baseline_type == "strategy":
        return apply_agency_baseline(
            brief=brief,
            raw_draft=raw_draft,
            llm=call_llm,
            pack_key=pack_key,
        )
    elif baseline_type == "social":
        return apply_quick_social_baseline(
            brief=brief,
            raw_draft=raw_draft,
            llm=call_llm,
            pack_key=pack_key,
        )
    else:
        return raw_draft
```

---

## Pattern 5: Testing & Validation

Unit test your integration.

```python
# tests/test_agency_baseline_integration.py
import pytest
from aicmo.agency.baseline import apply_agency_baseline, apply_quick_social_baseline

def mock_llm(system: str, user: str) -> str:
    """Mock LLM that returns minimal valid structure."""
    return """
## Executive Summary
- Challenge: Market saturation
- Big idea: Reposition as premium
- Impact: 30% uplift

## Brand & Market Context
- Category: Luxury goods
- Market: Growing affluent segment

[... minimal content for all 14 sections ...]
"""

def test_strategy_baseline_has_all_sections():
    brief = {
        "brand_name": "TestBrand",
        "objectives": "Growth and market expansion",
    }
    raw = "Growth... market... expand..."
    
    result = apply_agency_baseline(brief, raw, mock_llm)
    
    # Verify all 14 sections are present
    sections = [
        "Executive Summary",
        "Brand & Market Context",
        "Problem / Challenge Definition",
        "Audience & Key Insight",
        "Brand Positioning",
        "Competitive & Market Landscape",
        "Big Idea & Strategic Pillars",
        "Messaging Architecture",
        "Channel & Content Strategy",
        "Phasing & Roadmap",
        "Measurement & KPIs",
        "Budget & Investment Logic",
        "Risks, Assumptions & Dependencies",
        "Implementation Plan & Next Steps",
    ]
    
    for section in sections:
        assert section in result, f"Missing section: {section}"

def test_social_baseline_has_calendar():
    brief = {
        "brand_name": "TestBrand",
        "primary_channel": "Instagram",
    }
    raw = "Post content... Instagram... every day..."
    
    result = apply_quick_social_baseline(brief, raw, mock_llm)
    
    assert "30-Day Content Calendar" in result
    assert "Hooks" in result
    assert "Hashtag" in result
    assert "CTA" in result

def test_template_rendering():
    from aicmo.agency.baseline import _render_wow_template
    from aicmo.presets.wow_templates import WOW_TEMPLATES
    
    brief = {
        "brand_name": "Acme Corp",
        "primary_market": "North America",
        "timeframe": "Q1 2025",
    }
    
    template = WOW_TEMPLATES["agency_strategy_default"]
    rendered = _render_wow_template(template, brief, "")
    
    assert "Acme Corp" in rendered
    assert "North America" in rendered
    assert "Q1 2025" in rendered
```

---

## Pattern 6: Chaining Multiple Baselines

For multi-stage workflows.

```python
from aicmo.agency.baseline import apply_agency_baseline, apply_quick_social_baseline

def generate_full_suite(brief: dict) -> Dict[str, str]:
    """Generate strategy + social in one pass."""
    
    # Stage 1: Full strategy report
    strategy_draft = call_llm("Generate strategy...", brief)
    strategy_final = apply_agency_baseline(brief, strategy_draft, call_llm)
    
    # Stage 2: Extract key insights for social
    social_brief = {
        **brief,
        "big_idea": extract_big_idea(strategy_final),
        "audience": extract_audience(strategy_final),
    }
    
    social_draft = call_llm("Generate social plan...", social_brief)
    social_final = apply_quick_social_baseline(social_brief, social_draft, call_llm)
    
    return {
        "strategy": strategy_final,
        "social": social_final,
    }
```

---

## Pattern 7: Custom LLM Backends

Baseline is agnostic to LLM provider.

```python
# Use with Claude
from anthropic import Anthropic

anthropic = Anthropic()

def claude_llm(system: str, user: str) -> str:
    response = anthropic.messages.create(
        model="claude-3-sonnet-20240229",
        max_tokens=6000,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return response.content[0].text

result = apply_agency_baseline(brief, raw_draft, claude_llm)

# Use with local LLaMA
from ollama import Client

ollama = Client()

def llama_llm(system: str, user: str) -> str:
    response = ollama.generate(
        model="llama2",
        prompt=f"{system}\n\n{user}",
        stream=False,
    )
    return response["response"]

result = apply_agency_baseline(brief, raw_draft, llama_llm)

# Use with Azure OpenAI
from openai import AzureOpenAI

azure_client = AzureOpenAI(api_key=..., api_version="2024-02", base_url=...)

def azure_llm(system: str, user: str) -> str:
    response = azure_client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content

result = apply_agency_baseline(brief, raw_draft, azure_llm)
```

---

## Pattern 8: Monitoring & Logging

Track baseline execution for diagnostics.

```python
import logging
import time

logger = logging.getLogger(__name__)

def apply_agency_baseline_with_logging(brief, raw_draft, llm, pack_key=None):
    """Wrapper around baseline with timing & logging."""
    from aicmo.agency.baseline import apply_agency_baseline
    
    start = time.time()
    stages = []
    
    try:
        logger.info(f"Starting agency baseline for {brief.get('brand_name')}")
        
        # Internal timing (pseudo-code; integrate with actual function)
        result = apply_agency_baseline(brief, raw_draft, llm, pack_key)
        
        elapsed = time.time() - start
        logger.info(
            f"✅ Agency baseline complete in {elapsed:.1f}s | "
            f"Sections: {result.count('##')} | Template: {pack_key}"
        )
        
        return result
    except Exception as e:
        logger.error(f"❌ Agency baseline failed: {e}", exc_info=True)
        raise
```

---

## Summary

| Pattern | Use Case | Code Changes |
|---------|----------|--------------|
| Wrap Generator | Direct LLM call | Minimal – just wrap |
| Backend API | HTTP endpoint | Add parameter + conditional |
| Streamlit | UI integration | Import + call in button handler |
| Package Mapping | Different deliverables | Dict lookup + conditional |
| Testing | Validation | Mock LLM + assert sections |
| Chaining | Multi-stage workflow | Sequential calls + brief extraction |
| Custom LLM | Different providers | Pass custom llm function |
| Logging | Monitoring | Wrapper with timing & logging |

Pick the patterns that fit your architecture. All are pluggable.
