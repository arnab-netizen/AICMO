# SWOT Generator - Quick Reference

## Usage

### In Code
```python
from aicmo.generators import generate_swot
from aicmo.io.client_reports import ClientInputBrief

brief: ClientInputBrief = ...  # Your brief

# Automatic mode selection based on AICMO_USE_LLM environment variable
swot = generate_swot(brief)

# Returns:
# {
#   "strengths": ["...", "..."],
#   "weaknesses": ["...", "..."],
#   "opportunities": ["...", "..."],
#   "threats": ["...", "..."]
# }
```

### In Backend
Already integrated into `backend/main.py`:
```python
# In _generate_stub_output():
swot_dict = generate_swot(req.brief)
swot = SWOTBlock(
    strengths=swot_dict.get("strengths", []),
    weaknesses=swot_dict.get("weaknesses", []),
    opportunities=swot_dict.get("opportunities", []),
    threats=swot_dict.get("threats", []),
)
```

## Environment Variables

```bash
# Stub mode (offline, no LLM)
export AICMO_USE_LLM=0

# LLM mode (uses Claude by default)
export AICMO_USE_LLM=1
export ANTHROPIC_API_KEY=sk-ant-...

# Or use OpenAI
export AICMO_USE_LLM=1
export AICMO_LLM_PROVIDER=openai
export OPENAI_API_KEY=sk-...
```

## API

### `generate_swot(brief, industry_preset=None, memory_snippets=None, max_items=5)`

**Args:**
- `brief: ClientInputBrief` - The client brief (required)
- `industry_preset: Optional[IndustryPreset]` - Industry context (future use)
- `memory_snippets: Optional[List[str]]` - Phase L memory (future use)
- `max_items: int` - Max items per quadrant (default: 5)

**Returns:**
- `Dict[str, List[str]]` with keys: strengths, weaknesses, opportunities, threats

**Behavior:**
- **Stub mode** (AICMO_USE_LLM=0): Returns minimal, neutral SWOT
- **LLM mode** (AICMO_USE_LLM=1): Generates brief-specific SWOT via Claude/OpenAI
- **On error**: Falls back to stub SWOT (never throws)

## Testing

Run SWOT generator tests:
```bash
python -m pytest backend/tests/test_swot_generation.py -v
```

Run all tests:
```bash
python -m pytest backend/tests -q
```

## Example Output

### Stub Mode
```json
{
  "strengths": [
    "TestBrand has clear objectives for growth.",
    "There is structured planning around brand positioning."
  ],
  "weaknesses": [
    "Past marketing efforts may have lacked consistency.",
    "Channel presence could be more coordinated."
  ],
  "opportunities": [
    "Build a recognizable brand narrative across channels.",
    "Establish a repeatable content system that compounds over time."
  ],
  "threats": [
    "Competitors with more frequent marketing activity.",
    "Market and platform algorithm changes."
  ]
}
```

### LLM Mode (Example)
```json
{
  "strengths": [
    "Strong focus on data-driven decision making",
    "Established relationships in target market"
  ],
  "weaknesses": [
    "Limited brand awareness outside core industry",
    "Small marketing team relative to competitors"
  ],
  "opportunities": [
    "Expand into adjacent market segments",
    "Leverage social proof from existing customers"
  ],
  "threats": [
    "New entrants with larger marketing budgets",
    "Changing regulatory environment"
  ]
}
```

## No Placeholder Phrases

SWOT content will NEVER contain:
- ❌ "will be refined"
- ❌ "[PLACEHOLDER]"
- ❌ "TBD"
- ❌ "Hook idea for"
- ❌ "Performance review will be populated"

This applies to both stub mode and LLM mode.

## Validation

All SWOT content passes:
- ✅ Placeholder detection (aicmo/quality/validators.py)
- ✅ Export validation (safe_export_pdf/pptx/zip)
- ✅ Report validation before client delivery

## Integration Points

1. **Main generation**: `backend/main.py:_generate_stub_output()`
2. **Marketing plan**: `aicmo/io/client_reports.py:MarketingPlanView`
3. **Exports**: Safe to export SWOT in all formats (PDF/PPTX/ZIP)
4. **Validation**: No placeholder issues in SWOT

## Performance

- Stub mode: ~1ms (instant)
- LLM mode: ~2-5 seconds (API call to Claude/OpenAI)
- Fallback: Automatic if LLM fails

## Future Enhancements

1. **Phase L memory**: Use learned examples to improve SWOT
2. **Industry presets**: Use industry context in prompt
3. **Custom max_items**: Allow configuration per brief
4. **SWOT refinement**: Let users refine generated SWOT in UI
