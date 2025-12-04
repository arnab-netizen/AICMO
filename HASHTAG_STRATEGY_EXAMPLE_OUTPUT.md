# Perplexity-Powered Hashtag Strategy - Example Output

## Deterministic, Benchmark-Compliant Markdown Rendering

### Input (Perplexity Research Data):
```json
{
  "keyword_hashtags": [
    "#Starbucks",
    "#StarbucksLove", 
    "#StarbucksCoffee",
    "#StarbucksRewards"
  ],
  "industry_hashtags": [
    "#Coffee",
    "#CoffeeLover",
    "#CoffeeTime",
    "#Barista",
    "#Espresso"
  ],
  "campaign_hashtags": [
    "#FallFavorites",
    "#PumpkinSpice",
    "#HolidayDrinks",
    "#NewMenu"
  ]
}
```

### Generated Output:

---

## Brand Hashtags

Proprietary hashtags that build Starbucks brand equity and community. Use consistently across all posts to create searchable brand content:

- #Starbucks
- #StarbucksLove
- #StarbucksCoffee
- #StarbucksRewards

## Industry Hashtags

Target relevant industry tags to maximize discoverability in the Coffee & Cafes space:

- #Coffee
- #CoffeeLover
- #CoffeeTime
- #Barista
- #Espresso

## Campaign Hashtags

Create unique hashtags for specific campaigns, launches, or seasonal initiatives. Track performance to measure campaign reach and engagement:

- #FallFavorites
- #PumpkinSpice
- #HolidayDrinks
- #NewMenu

## Best Practices

- Use 8-12 hashtags per post for optimal reach
- Mix brand + industry tags to maximize discoverability
- Avoid banned or spammy tags that limit post visibility
- Keep campaign tags time-bound and tracked separately for ROI measurement

---

### Validation Result:

```
✅ PASS - 0 errors, 0 warnings

Validation Checks:
✅ All hashtags start with #
✅ All hashtags >= 4 characters
✅ No banned generic hashtags
✅ Brand Hashtags: 4 hashtags (minimum: 3) ✓
✅ Industry Hashtags: 5 hashtags (minimum: 3) ✓
✅ Campaign Hashtags: 4 hashtags (minimum: 3) ✓
✅ Required sections present:
   - Brand Hashtags ✓
   - Industry Hashtags ✓
   - Campaign Hashtags ✓
   - Best Practices ✓
```

---

### Fallback Behavior (When Perplexity Returns No Data):

```markdown
## Brand Hashtags

Proprietary hashtags that build Starbucks brand equity and community...

- #Starbucks
- #starbucksCommunity
- #starbucksInsider

## Industry Hashtags

Target relevant industry tags to maximize discoverability...

- #Coffee&Cafes
- #Coffee&CafesLife
- #Coffee&CafesLovers

## Campaign Hashtags

Create unique hashtags for specific campaigns...

- #LaunchWeek
- #SeasonalOffer
- #LimitedTime

## Best Practices

- Use 8-12 hashtags per post for optimal reach
...
```

**Validation Result**: ✅ **PASS** (fallbacks ensure minimum requirements met)

---

## Comparison: Before vs After

### Before (Static Generation):
- All hashtags hardcoded/generated from brand name
- No industry intelligence
- Generic campaign tags
- Limited to 3-5 tags per category

### After (Perplexity-Powered):
- **Keyword hashtags**: Intelligent brand-specific tags from Perplexity
- **Industry hashtags**: Trending tags from industry research
- **Campaign hashtags**: Seasonal/promotional tags based on market trends
- Expandable to 10 tags per category
- Real-time data from Perplexity API
- Smart fallbacks ensure reliability

---

## Error Handling Examples

### Scenario 1: Missing # Prefix
**Input**: `["Starbucks", "Coffee"]`  
**After Validation**: `["#Starbucks", "#Coffee"]` ✅

### Scenario 2: Too Short
**Input**: `["#A", "#BB", "#CCC"]`  
**Result**: All rejected (< 4 chars) ❌  
**Action**: Fallback tags added to meet minimum

### Scenario 3: Duplicate (Case-Insensitive)
**Input**: `["#Coffee", "#coffee", "#COFFEE"]`  
**After Deduplication**: `["#Coffee"]` ✅

### Scenario 4: Banned Generic
**Input**: `["#fun", "#love", "#happy"]`  
**Result**: All rejected (banned list) ❌  
**Action**: Replaced with brand-specific tags

---

**This output demonstrates**: 
✅ Deterministic structure
✅ Benchmark compliance  
✅ Perplexity integration
✅ Fallback safety
✅ Validation enforcement
