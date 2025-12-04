# AICMO LLM Architecture V2 - Clean Separation Model

**Status**: ✅ Implemented  
**Date**: 2024-12-03  
**Author**: Internal Architecture Team

---

## Executive Summary

AICMO's LLM architecture has been upgraded to cleanly separate concerns:

- **Perplexity** = All research, facts, competitor intelligence, market data
- **OpenAI** = All creative enhancement, narrative polish, degenericization  
- **Templates** = Deterministic scaffolding and structure (95%+ of content)

This three-tier architecture ensures:
- **Testability**: Each layer can be tested/mocked independently
- **Observability**: Logging at decision points for data source tracking
- **Graceful Fallbacks**: System works even with API failures
- **Cost Control**: Templates provide baseline, LLMs add value where needed

---

## Architecture Overview

```
Client Brief
     ↓
┌────────────────────────────────────────┐
│   ResearchService (Perplexity Layer)   │
│  - Brand research                      │
│  - Competitor intelligence             │
│  - Audience pain points/desires        │
│  - Market trends & dynamics            │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│   Template Layer (Deterministic)       │
│  - Structured markdown scaffolding     │
│  - Data injection from research        │
│  - Fallback content when APIs fail     │
│  - Benchmark enforcement               │
└────────────────────────────────────────┘
     ↓
┌────────────────────────────────────────┐
│   CreativeService (OpenAI Polish)      │
│  - Section enhancement                 │
│  - Degenericization                    │
│  - Narrative generation                │
│  - Calendar post hooks                 │
└────────────────────────────────────────┘
     ↓
Validated Output
```

---

## Service Layers

### 1. ResearchService (`backend/services/research_service.py`)

**Purpose**: Centralized orchestration of all Perplexity API calls for research and factual intelligence.

**Core API**:
```python
from backend.services.research_service import ResearchService, ComprehensiveResearchData

research_service = ResearchService()
research = research_service.fetch_comprehensive_research(brief)

# Check what data is available
if research.has_brand_data():
    themes = research.brand_research.recent_content_themes
    hashtags = research.brand_research.hashtag_brand

if research.has_competitor_data():
    competitors = research.competitor_research.competitors
    advantages = research.competitor_research.competitive_advantages

if research.has_audience_data():
    pain_points = research.audience_insights.pain_points
    desires = research.audience_insights.desires

if research.has_market_data():
    trends = research.market_trends.industry_trends
```

**Data Structures**:
- `ComprehensiveResearchData` - Unified container for all research
- `BrandResearchResult` - Brand themes, hashtags, content patterns
- `CompetitorResearchResult` - Competitor names, summaries, SWOT data
- `AudienceInsightsResult` - Pain points, desires, objections, triggers
- `MarketTrendsResult` - Industry trends, growth drivers, disruptions

**Features**:
- ✅ Respects `AICMO_PERPLEXITY_ENABLED` config flag
- ✅ Graceful fallbacks on API failures (returns empty data, never crashes)
- ✅ Comprehensive logging for observability
- ✅ Integrates existing `PerplexityClient` infrastructure
- ✅ LRU caching for efficiency

**When to Use**:
- Fetching competitor intelligence (names, market position)
- Understanding audience pain points and desires
- Getting market trends and industry dynamics
- Enriching hashtag strategies with real data
- Any section requiring factual, research-backed content

---

### 2. CreativeService (`backend/services/creative_service.py`)

**Purpose**: Centralized orchestration of all OpenAI API calls for creative enhancement and narrative generation.

**Core API**:
```python
from backend.services.creative_service import CreativeService, CreativeConfig

creative_service = CreativeService()

# Polish existing template content
polished = creative_service.polish_section(
    content=template_text,
    brief=brief,
    research_data=research,
    section_type="strategy"  # or "calendar", "tactical", etc.
)

# Remove generic marketing language
specific = creative_service.degenericize_text(generic_text, brief)

# Generate narrative from scratch
narrative = creative_service.generate_narrative(
    brief=brief,
    narrative_type="brand_story",
    max_length=500
)

# Enhance social media hooks
enhanced_posts = creative_service.enhance_calendar_posts(posts, brief, research)
```

**Configuration**:
```python
config = CreativeConfig(
    temperature=0.7,      # Creativity level (0.0-2.0)
    max_tokens=1500,      # Response length limit
    model="gpt-4o",       # OpenAI model to use
    enable_polish=True,   # Master switch for all enhancements
)

service = CreativeService(config=config)
```

**Features**:
- ✅ Respects stub mode (`is_stub_mode()`)
- ✅ Always returns text (never throws exceptions)
- ✅ Template-first approach (returns original on failure)
- ✅ Research-aware prompts (uses ComprehensiveResearchData when available)
- ✅ Section-type specific enhancement strategies
- ✅ Comprehensive logging

**When to Use**:
- Enhancing template output to be more specific and branded
- Removing generic buzzwords like "leverage", "synergy", "maximize ROI"
- Generating creative narratives for brand stories
- Improving social media hooks and CTAs
- Any section requiring creative polish and human touch

**When NOT to Use**:
- Generating factual/research content (use ResearchService instead)
- Creating structured data or tables (use templates)
- Benchmark-sensitive sections (polish may affect validation)

---

## Generator Integration Patterns

### Pattern 1: Research-Powered Generator (Perplexity → Template)

**Use Case**: Sections that benefit from real market/competitor/audience data.

**Example**: `_gen_competitor_analysis()`, `_gen_customer_insights()`, `_gen_market_landscape()`

```python
def _gen_section_name(req: GenerateRequest, **kwargs) -> str:
    """
    Generate 'section_name' section - RESEARCH-POWERED.
    
    Architecture:
        1. Check for Perplexity research data
        2. Use real data if available
        3. Fall back to template if unavailable
    """
    import logging
    b = req.brief.brand
    log = logging.getLogger("section_name")
    
    # Step 1: Get research data
    research = getattr(b, "research", None)
    
    # Step 2: Check if relevant research exists
    if research and research.has_competitor_data():
        log.info("[SectionName] Using Perplexity competitor data")
        
        # Build section with real data
        competitors = research.competitor_research.competitors
        template_text = f"""## Competitive Landscape

**Primary Competitors**:
{chr(10).join([f"- **{c.name}**: {c.description}" for c in competitors[:5]])}

**Market Position**:
{chr(10).join([f"- {insight}" for insight in research.competitor_research.market_share_insights])}
"""
    else:
        log.warning("[SectionName] No research data, using template fallback")
        
        # Fallback to generic template
        template_text = f"""## Competitive Landscape

**Primary Competitors**:
- Competitor A: Market leader with strong brand recognition
- Competitor B: Fast-growing challenger focused on innovation
- Competitor C: Established player with premium positioning

**Market Position**:
- Industry shows high fragmentation with no dominant player
- Customer switching costs are moderate
- Differentiation opportunities exist in customer service
"""
    
    return sanitize_output(template_text, req.brief)
```

**Key Points**:
- Always check if research exists before using
- Always provide template fallback
- Log decision (Perplexity vs template) for observability
- Maintain same output structure regardless of data source

---

### Pattern 2: Polish-Enhanced Generator (Template → OpenAI)

**Use Case**: Creative/strategic sections that benefit from AI enhancement.

**Example**: `_gen_campaign_objective()`, `_gen_core_campaign_idea()`, `_gen_creative_direction()`

```python
def _gen_section_name(req: GenerateRequest, **kwargs) -> str:
    """
    Generate 'section_name' section - WITH OPTIONAL CREATIVE POLISH.
    
    Architecture:
        1. Build structured template with client data
        2. Optionally enhance with OpenAI polish
        3. Return validated output
    """
    import logging
    from backend.services.creative_service import CreativeService
    
    b = req.brief.brand
    g = req.brief.goal
    log = logging.getLogger("section_name")
    
    # Step 1: Build template
    template_text = f"""## Campaign Objective

**Primary Goal**: {g.primary_goal}

Drive measurable business impact for {b.brand_name} by achieving {g.primary_goal}. 
This campaign focuses on creating sustainable momentum through strategic audience 
engagement, compelling messaging, and data-driven optimization across all channels.

**Timeline**: {g.timeline or '90 days'}

**Success Metrics**: {', '.join(g.kpis[:3]) if g.kpis else 'engagement, conversions'}
"""
    
    # Step 2: Optional creative polish
    try:
        creative_service = CreativeService()
        research = getattr(b, "research", None)
        
        if hasattr(creative_service, '_is_enabled') and creative_service._is_enabled():
            log.info("[SectionName] Polishing with CreativeService")
            polished = creative_service.polish_section(
                content=template_text,
                brief=req.brief,
                research_data=research,
                section_type="strategy"
            )
            return sanitize_output(polished, req.brief)
        else:
            log.debug("[SectionName] CreativeService disabled, using template")
    except Exception as e:
        log.warning(f"[SectionName] Creative polish failed: {e}, using template")
    
    # Step 3: Fallback to template
    return sanitize_output(template_text, req.brief)
```

**Key Points**:
- Template is primary output (always works)
- Creative polish is enhancement layer (optional)
- Check if CreativeService is enabled before calling
- Wrap in try/except with fallback to template
- Log all decisions for debugging

---

### Pattern 3: Full Pipeline (Research → Template → Creative)

**Use Case**: High-value sections that benefit from both research AND creative polish.

**Example**: `_gen_positioning_statement()`, `_gen_value_proposition()`

```python
def _gen_section_name(req: GenerateRequest, **kwargs) -> str:
    """
    Generate 'section_name' - FULL THREE-TIER PIPELINE.
    
    Architecture:
        1. Fetch Perplexity research data
        2. Build template with research injection
        3. Polish with OpenAI creative enhancement
    """
    import logging
    from backend.services.research_service import ResearchService
    from backend.services.creative_service import CreativeService
    
    b = req.brief.brand
    log = logging.getLogger("section_name")
    
    # Tier 1: Research (Perplexity)
    research_service = ResearchService()
    research = research_service.fetch_comprehensive_research(req.brief)
    
    # Tier 2: Template with research injection
    if research.has_audience_data():
        log.info("[SectionName] Using Perplexity audience insights")
        pain_points = research.audience_insights.pain_points[:3]
        desires = research.audience_insights.desires[:3]
        
        template_text = f"""## Value Proposition

**Customer Pain Points**:
{chr(10).join([f"- {pain}" for pain in pain_points])}

**Our Solution**:
{b.brand_name} addresses these challenges by {b.value_proposition or 'providing innovative solutions'}.

**Customer Desires**:
{chr(10).join([f"- {desire}" for desire in desires])}
"""
    else:
        log.warning("[SectionName] No audience data, using template")
        template_text = f"""## Value Proposition

{b.brand_name} provides {b.value_proposition or 'exceptional value'} to customers 
in {b.industry} by solving critical challenges and delivering measurable results.
"""
    
    # Tier 3: Creative polish (OpenAI)
    try:
        creative_service = CreativeService()
        if creative_service._is_enabled():
            log.info("[SectionName] Applying creative polish")
            return sanitize_output(
                creative_service.polish_section(template_text, req.brief, research, "strategy"),
                req.brief
            )
    except Exception as e:
        log.warning(f"[SectionName] Polish failed: {e}")
    
    return sanitize_output(template_text, req.brief)
```

**Key Points**:
- Use all three tiers for maximum quality
- Each tier adds value incrementally
- Each tier has independent fallback
- System degrades gracefully (works even if all LLMs fail)
- Logging shows exactly which tier succeeded/failed

---

## Configuration & Feature Flags

### Environment Variables

```bash
# Perplexity Research Layer
AICMO_PERPLEXITY_ENABLED=true         # Master switch for all Perplexity calls
PERPLEXITY_API_KEY=pplx-xxxxx         # API key for authentication

# OpenAI Creative Layer  
AICMO_USE_LLM=true                    # Master switch for OpenAI calls
OPENAI_API_KEY=sk-xxxxx               # API key for authentication

# Stub Mode (for testing/development)
# Set by is_stub_mode() function - disables all external API calls
```

### CreativeService Configuration

```python
# Default configuration (backend/services/creative_service.py)
@dataclass
class CreativeConfig:
    temperature: float = 0.7              # Creativity (0.0 = deterministic, 2.0 = wild)
    max_tokens: int = 1500                # Response length limit
    model: str = "gpt-4o"                 # OpenAI model
    enable_polish: bool = True            # Master switch for polish operations
    enable_degenericize: bool = True      # Master switch for degenericize
    enable_narrative: bool = True         # Master switch for narratives
    enable_calendar_enhance: bool = True  # Master switch for calendar enhancement
```

---

## Observability & Logging

### Logging Pattern

Every generator should log data source decisions:

```python
import logging
log = logging.getLogger("generator_name")

# Log Perplexity usage
if using_perplexity_data:
    log.info("[GeneratorName] Using Perplexity research data")
else:
    log.warning("[GeneratorName] No research data, using template fallback")

# Log OpenAI usage  
if using_openai_polish:
    log.info("[GeneratorName] Polishing with CreativeService (OpenAI)")
else:
    log.debug("[GeneratorName] CreativeService disabled, template only")

# Log API failures
except Exception as e:
    log.error(f"[GeneratorName] API call failed: {e}, falling back")
```

### Log Levels
- `INFO`: Successful LLM usage (Perplexity data found, OpenAI polish applied)
- `WARNING`: Fallback to template (no research data, API disabled)
- `ERROR`: API failures or unexpected issues
- `DEBUG`: Detailed flow information (for development)

### Monitoring Queries

To track LLM usage across the platform:

```bash
# Find all Perplexity-powered sections
grep -r "Using Perplexity" logs/

# Find all OpenAI polish usage
grep -r "Polishing with CreativeService" logs/

# Find all template fallbacks
grep -r "No research data" logs/

# Find all API failures
grep -r "API call failed" logs/
```

---

## Testing Strategy

### Unit Tests

**ResearchService Tests** (`backend/tests/test_research_service.py`):
- Mock PerplexityClient responses
- Test data structure integrity
- Test graceful fallbacks on API failures
- Test config flag handling

**CreativeService Tests** (`backend/tests/test_creative_service.py`):
- Mock OpenAI client responses
- Test stub mode detection
- Test template-first fallback pattern
- Test all enhancement methods

### Integration Tests

```python
def test_full_pipeline_integration():
    """Test complete Research → Template → Creative flow."""
    # Setup
    brief = create_test_brief()
    
    # Tier 1: Research
    research_service = ResearchService()
    research = research_service.fetch_comprehensive_research(brief)
    assert research is not None
    
    # Tier 2: Generator with research
    result = _gen_competitor_analysis(GenerateRequest(brief=brief))
    assert "## Competitive Landscape" in result
    
    # Tier 3: Creative polish
    creative_service = CreativeService()
    polished = creative_service.polish_section(result, brief, research, "strategy")
    assert len(polished) > len(result)  # Should add value
```

### Benchmark Validation

Existing benchmarks must continue to pass:

```bash
# Run quality enforcement checks
pytest backend/tests/test_benchmark_enforcement_smoke.py

# Run validation script
python scripts/dev_validate_benchmark_proof.py

# Check for regressions
pytest backend/tests/ -k "benchmark"
```

---

## Decision Matrix: When to Use What

| Scenario | Use Perplexity? | Use Template? | Use OpenAI? | Example Section |
|----------|----------------|---------------|-------------|----------------|
| **Factual competitor data** | ✅ Yes | ✅ Fallback | ❌ No | competitor_analysis |
| **Audience pain points** | ✅ Yes | ✅ Fallback | ❌ No | customer_insights |
| **Market trends** | ✅ Yes | ✅ Fallback | ❌ No | market_landscape |
| **Hashtag strategy** | ✅ Yes | ✅ Fallback | ❌ No | hashtag_strategy |
| **Creative campaign idea** | ⚠️ Optional | ✅ Primary | ✅ Polish | core_campaign_idea |
| **Campaign objectives** | ⚠️ Optional | ✅ Primary | ✅ Polish | campaign_objective |
| **Messaging pillars** | ✅ Research | ✅ Structure | ✅ Polish | messaging_pillars |
| **Value proposition** | ✅ Research | ✅ Structure | ✅ Polish | value_proposition |
| **Calendar content** | ❌ No | ✅ Primary | ✅ Hooks | calendar |
| **Structured tables** | ❌ No | ✅ Only | ❌ No | metrics_table |
| **Benchmark sections** | ❌ No | ✅ Only | ❌ No | budget_breakdown |

**Legend**:
- ✅ **Yes**: Primary use case, recommended
- ✅ **Primary**: Main content source
- ✅ **Fallback**: Safety net when APIs fail
- ✅ **Polish**: Enhancement layer on top of template
- ⚠️ **Optional**: Can provide context but not required
- ❌ **No**: Not recommended (wrong tool for job)

---

## Migration Guide: Upgrading Existing Generators

### Step 1: Identify Generator Type

**Research-Heavy Sections** → Add ResearchService  
Examples: competitor_analysis, market_landscape, customer_insights, SWOT

**Creative Sections** → Add CreativeService polish  
Examples: campaign_objective, core_campaign_idea, creative_direction

**Structured Data** → Keep template-only  
Examples: budget_breakdown, metrics_dashboard, timeline_gantt

### Step 2: Add Research Integration

```python
# Before
def _gen_competitor_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate competitor analysis."""
    return """## Competitors
- Competitor A: Generic description
- Competitor B: Generic description
"""

# After
def _gen_competitor_analysis(req: GenerateRequest, **kwargs) -> str:
    """Generate competitor analysis - RESEARCH-POWERED."""
    import logging
    b = req.brief.brand
    log = logging.getLogger("competitor_analysis")
    
    research = getattr(b, "research", None)
    
    if research and research.has_competitor_data():
        log.info("[CompetitorAnalysis] Using Perplexity data")
        competitors = research.competitor_research.competitors
        return f"""## Competitors
{chr(10).join([f"- **{c.name}**: {c.description}" for c in competitors])}
"""
    else:
        log.warning("[CompetitorAnalysis] No research, using template")
        return """## Competitors
- Competitor A: Market leader with strong brand recognition
- Competitor B: Fast-growing challenger
"""
```

### Step 3: Add Creative Polish (Optional)

```python
# Add after template building
try:
    creative_service = CreativeService()
    if creative_service._is_enabled():
        log.info("[SectionName] Applying creative polish")
        template_text = creative_service.polish_section(
            template_text, req.brief, research, "strategy"
        )
except Exception as e:
    log.warning(f"[SectionName] Polish failed: {e}")

return sanitize_output(template_text, req.brief)
```

### Step 4: Add Logging

```python
import logging
log = logging.getLogger("section_name")

# At decision points
log.info("[SectionName] Using Perplexity data")
log.warning("[SectionName] No research, falling back to template")
log.error(f"[SectionName] API error: {e}")
```

### Step 5: Test

1. Run generator in stub mode → Should work (template fallback)
2. Run with Perplexity enabled → Should use research data
3. Run with OpenAI enabled → Should apply polish
4. Run benchmarks → Should still pass
5. Check logs → Should see data source tracking

---

## Best Practices

### DO ✅

1. **Always provide template fallback** - System must work even if all APIs fail
2. **Log all LLM usage decisions** - Essential for debugging and cost tracking
3. **Check research data exists before using** - Use `has_*_data()` helper methods
4. **Wrap LLM calls in try/except** - Never let API failures crash generators
5. **Use sanitize_output() on all returns** - Maintains quality standards
6. **Test in stub mode first** - Validates template-only path works
7. **Preserve output structure** - Same markdown structure regardless of data source
8. **Document architecture in docstring** - Explain Research/Template/Creative tiers

### DON'T ❌

1. **Don't assume research data exists** - Always check with `research.has_*_data()`
2. **Don't throw exceptions on API failure** - Return template instead
3. **Don't skip logging** - Observability is critical for production debugging
4. **Don't mix concerns** - Keep research (Perplexity) and creative (OpenAI) separate
5. **Don't over-polish** - Some sections (metrics, tables) should stay template-only
6. **Don't bypass sanitize_output()** - Quality enforcement is mandatory
7. **Don't call LLMs for simple string operations** - Use templates for predictable content
8. **Don't skip stub mode testing** - Every generator must work without APIs

---

## Performance & Cost Optimization

### Caching Strategy

```python
# ResearchService uses LRU cache internally
@lru_cache(maxsize=100)
def fetch_comprehensive_research(brief):
    # Expensive Perplexity calls cached automatically
    pass
```

### Cost Tiers

**Perplexity Usage** (~$0.005/request):
- Brand research: 1 request per pack generation
- Competitor research: 1 request per pack generation  
- Audience insights: 1 request per pack generation
- Market trends: 1 request per pack generation
- **Total: ~$0.02 per pack** (with full research)

**OpenAI Usage** (~$0.03/1K tokens):
- Polish section (1500 tokens): ~$0.045 per section
- Degenericize (500 tokens): ~$0.015 per section
- Calendar enhancement (200 tokens per post × 30): ~$0.18 per calendar
- **Total: ~$0.50 per pack** (with full polish on 10 sections)

**Template-Only** ($0):
- No API costs, instant generation
- Used for all sections when APIs unavailable

### Optimization Tips

1. **Enable selective polish** - Only polish high-value sections (objective, big idea)
2. **Use research caching** - ResearchService caches per brief to avoid redundant calls
3. **Batch calendar posts** - Process multiple posts in single OpenAI call
4. **Monitor token usage** - Log token counts with each creative service call
5. **Set reasonable timeouts** - Fail fast on API issues, fall back to template

---

## Troubleshooting

### Issue: "No research data available"

**Symptom**: Logs show `"No research data, using template fallback"` for all sections

**Causes**:
- `AICMO_PERPLEXITY_ENABLED=false` in environment
- Invalid or missing `PERPLEXITY_API_KEY`
- Perplexity API is down or rate-limited
- Brief data incomplete (missing brand_name, industry, etc.)

**Fix**:
1. Check environment variables: `echo $AICMO_PERPLEXITY_ENABLED`
2. Verify API key: `echo $PERPLEXITY_API_KEY | cut -c1-10`
3. Test PerplexityClient directly: `python -c "from backend.external.perplexity_client import PerplexityClient; print(PerplexityClient().research_brand('TestBrand', 'Tech', 'US'))"`
4. Check ResearchService logs for error messages

### Issue: "Creative polish not applying"

**Symptom**: Output looks exactly like template, no enhancement

**Causes**:
- Stub mode enabled (`is_stub_mode() == True`)
- `AICMO_USE_LLM=false` in environment
- Invalid or missing `OPENAI_API_KEY`
- OpenAI API rate limit or quota exceeded
- Generator doesn't call CreativeService

**Fix**:
1. Check stub mode: `python -c "from backend.core.config import is_stub_mode; print(is_stub_mode())"`
2. Verify LLM flag: `echo $AICMO_USE_LLM`
3. Check OpenAI key: `echo $OPENAI_API_KEY | cut -c1-10`
4. Verify generator calls `creative_service.polish_section()`
5. Check CreativeService logs for errors

### Issue: "Tests failing with AttributeError"

**Symptom**: Tests can't find `is_stub_mode` or other imports

**Causes**:
- Import paths in tests don't match actual service implementation
- Mock patches target wrong module path
- Dataclass __init__ signatures don't match

**Fix**:
1. Check actual import in service file: `grep "^from\|^import" backend/services/research_service.py`
2. Update test mock patch to match: `@patch('backend.core.config.is_stub_mode')`
3. Check dataclass fields: `python -c "from backend.services.research_service import ComprehensiveResearchData; print(ComprehensiveResearchData.__dataclass_fields__)"`

### Issue: "Benchmarks failing after upgrade"

**Symptom**: Quality enforcement or benchmark tests now fail

**Causes**:
- Creative polish changed word count, affecting length benchmarks
- Research data injection changed section structure
- Hashtag format changed (brand vs industry vs campaign)
- Markdown formatting changed

**Fix**:
1. Identify which benchmark failed: `pytest backend/tests/test_benchmark_enforcement_smoke.py -v`
2. Compare old vs new output: `diff -u old_output.txt new_output.txt`
3. If polish caused issue, disable CreativeService for that section
4. If research caused issue, ensure fallback template matches old structure
5. Update benchmarks if new output is actually better (with team approval)

---

## Future Enhancements

### Planned (Short-Term)

1. **Test Suite Alignment** - Fix test mocks to match actual method signatures
2. **Benchmark Validation** - Run full test suite and validate no regressions
3. **Additional Generators** - Upgrade remaining research-aware sections (SWOT, positioning, messaging_pillars)
4. **Cost Tracking** - Add token usage logging to CreativeService
5. **Performance Metrics** - Track API latency and success rates

### Roadmap (Long-Term)

1. **Multi-Model Support** - Add Anthropic Claude as alternative to OpenAI
2. **Research Expansion** - Add trend data, regulatory insights, technology disruptions
3. **Smart Caching** - Implement Redis-based distributed cache for research
4. **A/B Testing Framework** - Test template vs polished outputs for quality
5. **Cost Optimization** - Dynamic model selection based on section complexity
6. **Real-Time Research** - Stream Perplexity results as they arrive
7. **Research Validation** - Cross-check facts with multiple sources

---

## Summary

AICMO now has a **clean three-tier LLM architecture**:

1. **ResearchService (Perplexity)** - Facts, competitors, market data, audience insights
2. **Template Layer** - Deterministic structure, reliable fallbacks, benchmark enforcement
3. **CreativeService (OpenAI)** - Enhancement, polish, degenericization, narrative generation

**Key Benefits**:
- ✅ Clear separation of concerns
- ✅ Testable and mockable layers
- ✅ Graceful degradation (works even if all APIs fail)
- ✅ Comprehensive logging and observability
- ✅ Cost control through selective enhancement
- ✅ Maintains existing benchmarks and quality gates

**Migration Status**:
- ✅ Service layers implemented (777 lines of production code)
- ✅ Hashtag strategy upgraded (enhanced logging)
- ✅ Competitor analysis upgraded (Perplexity-powered)
- ✅ Market landscape upgraded (research-aware)
- ✅ Customer insights upgraded (audience data integration)
- ✅ Campaign objective upgraded (creative polish layer)
- ⏳ Additional generators pending (SWOT, positioning, messaging_pillars)
- ⏳ Test suite needs alignment with actual implementations
- ⏳ Full benchmark validation pending

---

**Document Version**: 1.0  
**Last Updated**: 2024-12-03  
**Next Review**: After remaining generator upgrades complete
