# Quick Social Pack - Developer Quick Reference

## Quick Social Scope (8 Sections)

```python
QUICK_SOCIAL_CORE = [
    "overview",                    # Brand & Objectives
    "messaging_framework",         # Strategy Lite
    "detailed_30_day_calendar",    # Hero: 30-day posting plan
    "content_buckets",             # Hooks + captions
    "hashtag_strategy",            # Normalized hashtags
    "kpi_plan_light",              # Light KPIs (industry-aware)
    "execution_roadmap",           # 7-day action plan
    "final_summary",               # Cleaned summary
]
```

## Key Utilities

### Hashtag Normalization
```python
from backend.utils.text_cleanup import normalize_hashtag

# Usage
normalize_hashtag("Coffeehouse / Beverage Retail")  # → "#coffeehousebeverageretail"
normalize_hashtag("#Coffee Shop")                   # → "#coffeeshop"
```

### Text Cleanup
```python
from backend.utils.text_cleanup import clean_quick_social_text

# Automatically removes:
# - "ideal customers" (replaced with persona)
# - "over the next period"
# - "Key considerations include..."
# - Double periods (..)
# - Excessive repetition
```

### Industry Profiles
```python
from backend.industry_config import get_industry_profile

profile = get_industry_profile("Coffeehouse / Beverage Retail")
if profile:
    # Use profile.vocab for industry-specific language
    # Use profile.kpi_overrides for retail-focused KPIs
```

## 30-Day Calendar Generator

### Content Buckets
- **Education** - Tips, how-tos, industry insights
- **Proof** - Testimonials, reviews, case studies
- **Promo** - Offers, new items, bundles
- **Community** - UGC, staff features, customer stories
- **Experience** - In-store moments, atmosphere

### Day-of-Week Mapping
```python
{
    0: "Education",   # Monday: learn
    1: "Proof",       # Tuesday: testimonials
    2: "Community",   # Wednesday: engagement
    3: "Education",   # Thursday: tips
    4: "Promo",       # Friday: treat yourself
    5: "Experience",  # Saturday: in-store
    6: "Community",   # Sunday: chill
}
```

### Hook Templates (Examples)

**Instagram + Experience:**
```
"Step into {brand_name}: your community's third place."
```

**LinkedIn + Education:**
```
"3 ways {brand_name} is rethinking {industry_vocab} for busy professionals."
```

**Twitter + Proof:**
```
"What customers actually say about {brand_name}."
```

## Testing

### Run Hygiene Tests
```bash
pytest backend/tests/test_quick_social_hygiene.py -v -W ignore::DeprecationWarning
```

### Test Individual Functions
```python
# Test calendar generator
from backend.main import _gen_quick_social_30_day_calendar

# Test hashtag normalizer
from backend.utils.text_cleanup import normalize_hashtag

# Test text cleanup
from backend.utils.text_cleanup import clean_quick_social_text

# Test industry profile
from backend.industry_config import get_industry_profile
```

## Banned Phrases (Removed by Cleanup)

- "ideal customers"
- "over the next period"
- "within the near term timeframe"
- "Key considerations include the audience's core pain points"
- "in today's digital age"
- "content is king"

## Industry-Specific Behavior

**When:** Quick Social + Coffeehouse/Cafe industry

**Then:**
- KPIs focus on retail metrics (foot traffic, transaction value, repeat visits)
- Vocabulary uses "third place", "handcrafted beverages", "neighbourhood store"
- Hooks reference coffee culture and community gathering

## File Locations

```
aicmo/presets/package_presets.py          # Pack definition
backend/main.py                            # Generators + whitelist
backend/utils/text_cleanup.py             # Normalization + cleanup
backend/industry_config.py                 # Industry profiles
backend/tests/test_quick_social_hygiene.py # Hygiene tests
```

## Common Patterns

### Detect Quick Social Pack
```python
pack_key = kwargs.get("pack_key", "") or req.wow_package_key or ""
if "quick_social" in pack_key.lower():
    # Use Quick Social-specific logic
```

### Use Industry Profile
```python
from backend.industry_config import get_industry_profile

profile = get_industry_profile(req.brief.brand.industry)
use_industry_kpis = profile and "quick_social" in pack_key.lower()

if use_industry_kpis:
    kpis = profile.kpi_overrides
else:
    kpis = DEFAULT_KPIS
```

### Apply Cleanup
```python
# Cleanup runs automatically in generate_sections() for Quick Social
# But can be called manually:
from backend.utils.text_cleanup import clean_quick_social_text

if "quick_social" in pack_key.lower():
    text = clean_quick_social_text(text, req)
```

## Adding New Industry Profiles

1. Edit `backend/industry_config.py`
2. Add new `IndustryProfile` to `INDUSTRY_PROFILES` list
3. Include keywords, vocab, kpi_overrides

```python
IndustryProfile(
    keywords=["Restaurant", "Food Service", "Dining"],
    vocab=[
        "culinary experience",
        "farm-to-table",
        "signature dishes",
        # ...
    ],
    kpi_overrides=[
        "table turnover rate",
        "average check size",
        "reservation conversion",
        # ...
    ],
)
```

## Troubleshooting

### Invalid Hashtags Still Appearing?
Check that `_gen_hashtag_strategy()` is calling `normalize_hashtag()`.

### Template Leaks Not Removed?
Verify cleanup pass is running in `generate_sections()` for Quick Social packs.

### Calendar Hooks All Identical?
Check that `_make_quick_social_hook()` is receiving platform, bucket, and angle parameters.

### Wrong KPIs for Industry?
Verify `get_industry_profile()` is matching the industry string correctly.

---

**Last Updated:** November 30, 2025
