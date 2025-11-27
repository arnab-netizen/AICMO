# Quick Reference Guide - AICMO Pipeline Fixes

## 🎯 What's New

This guide shows how to use the newly implemented features in the AICMO pipeline.

---

## 1. Output Validation (FIX #6)

### Check Report Quality Before Export

```python
from backend.validators import validate_output_report
from aicmo.io.client_reports import AICMOOutputReport, ClientInputBrief

# In your report generation endpoint:
def export_report(output: AICMOOutputReport, brief: ClientInputBrief):
    # Validate before export
    is_valid, issues = validate_output_report(
        output=output,
        brief=brief,
        wow_package_key="strategy_campaign_standard",  # Optional but recommended
        strict=False  # Set True to treat warnings as errors
    )
    
    if not is_valid:
        # Show error to user
        raise ExportError({
            "error": "Report validation failed",
            "issues": issues
        })
    
    # Safe to export
    return generate_pdf(output)
```

### Get Validation Issues

```python
from backend.validators import OutputValidator, ValidationSeverity

validator = OutputValidator(output, brief, wow_package_key)
issues = validator.validate_all()

# Check specific issue types
for issue in issues:
    if issue.severity == ValidationSeverity.ERROR:
        print(f"❌ {issue.section}: {issue.message}")
    elif issue.severity == ValidationSeverity.WARNING:
        print(f"⚠️  {issue.section}: {issue.message}")
    else:
        print(f"ℹ️  {issue.section}: {issue.message}")
```

---

## 2. Industry-Specific Personas (FIX #4)

### Get Personas for an Industry

```python
from backend.industry_config import get_default_personas_for_industry

# Get industry-appropriate personas
industry = brief.brand.industry  # e.g., "SaaS"
personas = get_default_personas_for_industry(industry)

for persona in personas:
    print(f"Name: {persona['name']}")
    print(f"Role: {persona['role']}")
    print(f"Goals: {persona['primary_goals']}")
    print(f"Preferred Channel: {persona['channel_preference']}")
```

### Use in Persona Generator

```python
def _gen_persona_cards(req: GenerateRequest, **kwargs) -> str:
    from backend.industry_config import get_default_personas_for_industry
    
    industry = req.brief.brand.industry
    default_personas = get_default_personas_for_industry(industry)
    
    if default_personas:
        # Use industry-specific personas instead of generic ones
        md = "## Key Personas\n\n"
        for persona in default_personas:
            md += f"### {persona['name']}\n"
            md += f"**Role:** {persona['role']}\n"
            md += f"**Goals:** {', '.join(persona['primary_goals'])}\n"
            md += f"**Challenges:** {', '.join(persona['primary_pain_points'])}\n\n"
        return md
    
    # Fallback to generic if industry not recognized
    return _gen_persona_cards_generic(req, **kwargs)
```

---

## 3. Industry-Specific Channels (FIX #4)

### Get Recommended Channels by Industry

```python
from backend.industry_config import (
    get_primary_channel_for_industry,
    get_industry_config
)

industry = "SaaS"

# Get primary channel
primary = get_primary_channel_for_industry(industry)
print(f"Primary: {primary}")  # Output: "LinkedIn"

# Get full channel config
config = get_industry_config(industry)
print(f"Secondary: {config['channels']['secondary']}")  # ["Email", "YouTube"]
print(f"Avoid: {config['channels']['avoid']}")  # ["TikTok", "Instagram"]
```

### Use in Channel Plan Generator

```python
def _gen_channel_plan(req: GenerateRequest, **kwargs) -> str:
    from backend.industry_config import get_industry_config
    
    industry = req.brief.brand.industry
    config = get_industry_config(industry)
    
    if config:
        channels = config['channels']
        md = f"""## Channel Strategy

**Primary Channel:** {channels['primary']}
- {channels['reasoning']}

**Secondary Channels:** {', '.join(channels['secondary'])}

**Tertiary Options:** {', '.join(channels['tertiary'])}

**Channels to Avoid:** {', '.join(channels['avoid'])}
"""
        return md
    
    # Fallback if industry not recognized
    return _gen_channel_plan_generic(req, **kwargs)
```

---

## 4. PDF Template Resolution (FIX #3)

### Get Correct Template for Pack

```python
from backend.pdf_renderer import resolve_pdf_template_for_pack

wow_package_key = "full_funnel_growth_suite"
template_name = resolve_pdf_template_for_pack(wow_package_key)
print(template_name)  # Output: "full_funnel_growth.html"
```

### Template Mapping Reference

```
quick_social_basic          → quick_social_basic.html (10 sections)
strategy_campaign_standard  → campaign_strategy.html (17 sections)
full_funnel_growth_suite    → full_funnel_growth.html (21 sections)
launch_gtm_pack             → launch_gtm.html (14 sections)
brand_turnaround_lab        → brand_turnaround.html (16 sections)
retention_crm_booster       → retention_crm.html (12 sections)
performance_audit_revamp    → performance_audit.html (13 sections)
```

---

## 5. Pack Scoping Enforcement (FIX #2)

### Get Allowed Sections for Pack

```python
from backend.main import get_allowed_sections_for_pack

# Get the whitelist of sections for a pack
allowed_sections = get_allowed_sections_for_pack("quick_social_basic")
print(allowed_sections)
# Output: {'overview', 'audience_segments', 'messaging_framework', ...}

# Can be used to filter section generation
def generate_sections(section_ids: list[str], wow_package_key: str):
    allowed = get_allowed_sections_for_pack(wow_package_key)
    
    # Only generate allowed sections
    filtered_sections = [s for s in section_ids if s in allowed]
    
    for section_id in filtered_sections:
        # Generate section content...
        pass
```

---

## 6. Industry Configuration Reference

### All Supported Industries

#### F&B / Food & Beverage
```python
config = get_industry_config("food_beverage")
# Primary: Instagram
# Secondary: TikTok, Facebook
# Personas: Foodie, Local Regular
# Tone: Visual, trendy, community-focused
# Formats: Reels, Carousels, Stories, UGC
```

#### SaaS / B2B Software
```python
config = get_industry_config("saas")
# Primary: LinkedIn
# Secondary: Email, YouTube
# Personas: VP Operations, Tech Implementer
# Tone: Professional, ROI-focused
# Formats: Case studies, Webinars, White papers
```

#### Boutique Retail & Fashion
```python
config = get_industry_config("boutique_retail")
# Primary: Instagram
# Secondary: Pinterest, TikTok
# Personas: Fashion-Forward, Conscious Consumer
# Tone: Aspirational, trendy, aesthetic
# Formats: Product showcase, Lookbooks, Behind-the-scenes
```

#### Fitness & Wellness
```python
config = get_industry_config("fitness")
# Primary: Instagram
# Secondary: TikTok, YouTube
# Personas: Enthusiast, Wellness Seeker
# Tone: Motivational, transformational
# Formats: Transformation stories, Workouts, Challenges
```

#### E-Commerce / Online Retail
```python
config = get_industry_config("ecommerce")
# Primary: Instagram
# Secondary: Pinterest, Email
# Personas: Social Shopper, Deal Hunter
# Tone: Deal-focused, trendy, trust-building
# Formats: Product showcase, Reviews, Flash sales
```

---

## 🧪 Testing the New Features

### Run All Tests
```bash
# All 120+ new tests
pytest tests/test_output_validation.py \
        tests/test_industry_alignment.py \
        tests/test_pdf_templates.py -v

# Run specific test
pytest tests/test_output_validation.py::TestOutputValidator::test_has_blocking_issues_true -v

# Run with coverage
pytest tests/ --cov=backend.validators --cov=backend.industry_config -v
```

### Test Industry Config Loading
```bash
python -c "from backend.industry_config import INDUSTRY_CONFIGS; \
  print(f'Industries: {list(INDUSTRY_CONFIGS.keys())}')"

python -c "from backend.industry_config import get_industry_config; \
  cfg = get_industry_config('saas'); \
  print(f'SaaS Primary: {cfg[\"channels\"][\"primary\"]}')"
```

### Test PDF Template Resolution
```bash
python -c "from backend.pdf_renderer import resolve_pdf_template_for_pack; \
  t = resolve_pdf_template_for_pack('full_funnel_growth_suite'); \
  print(f'Template: {t}')"
```

### Test Output Validation
```python
from backend.validators import OutputValidator
from aicmo.io.client_reports import ClientInputBrief

# Create test brief and output
brief = ClientInputBrief(...)
output = AICMOOutputReport(...)

# Validate
validator = OutputValidator(output, brief, "strategy_campaign_standard")
issues = validator.validate_all()

print(f"Blocking issues: {validator.has_blocking_issues()}")
print(f"Total issues: {len(issues)}")
```

---

## 🔧 Common Use Cases

### Case 1: Export Report with Validation

```python
@app.post("/aicmo/export/pdf")
def export_pdf(payload: dict):
    # Get report and brief
    output = AICMOOutputReport.model_validate(payload["report"])
    brief = ClientInputBrief.model_validate(payload["brief"])
    wow_key = payload.get("wow_package_key")
    
    # Validate before export
    is_valid, issues = validate_output_report(
        output=output,
        brief=brief,
        wow_package_key=wow_key,
        strict=True  # Warnings become errors
    )
    
    if not is_valid:
        blocking = [i for i in issues if i.severity == ValidationSeverity.ERROR]
        return {"error": f"{len(blocking)} blocking issue(s)", "issues": blocking}
    
    # Safe to export
    pdf_bytes = safe_export_agency_pdf({...})
    return StreamingResponse(pdf_bytes)
```

### Case 2: Generate Industry-Aware Report

```python
def generate_report_for_industry(brief: ClientInputBrief):
    output = _generate_stub_output(req)
    
    # Industry 1: Use industry-specific personas
    if "persona_cards" in req.sections:
        industry_personas = get_default_personas_for_industry(brief.brand.industry)
        output.persona_cards = [create_persona(p) for p in industry_personas]
    
    # Industry 2: Use industry-specific channels
    if "channel_plan" in req.sections:
        config = get_industry_config(brief.brand.industry)
        channels = config['channels'] if config else None
        # Use channels in generation...
    
    return output
```

### Case 3: Ensure PDF Parity

```python
def export_report_with_pdf_check(output: AICMOOutputReport, brief: ClientInputBrief):
    # Validate that PDF will match preview
    is_valid, issues = validate_output_report(output, brief, strict=False)
    
    pdf_parity_issues = [i for i in issues if "pdf" in i.section.lower()]
    
    if pdf_parity_issues:
        logger.warning(f"PDF parity issues: {pdf_parity_issues}")
        # Could notify user or auto-fix
    
    # Generate PDF
    return safe_export_agency_pdf({...})
```

---

## 📚 API Reference

### OutputValidator

```python
class OutputValidator:
    def __init__(self, output, brief, wow_package_key=None)
    def validate_all() -> List[ValidationIssue]
    def validate_all_strict() -> List[ValidationIssue]
    def has_blocking_issues() -> bool
    def get_error_summary() -> str
```

### Industry Config Functions

```python
def get_industry_config(industry_keyword: str) -> Optional[IndustryConfig]
def get_primary_channel_for_industry(industry_keyword: str) -> Optional[str]
def get_default_personas_for_industry(industry_keyword: str) -> List[IndustryPersonaConfig]
```

### PDF Renderer Functions

```python
def resolve_pdf_template_for_pack(wow_package_key: str) -> str
def render_agency_pdf(context: Dict[str, Any]) -> bytes
```

### Pack Scoping Functions

```python
def get_allowed_sections_for_pack(wow_package_key: str) -> set[str]
```

---

## 💡 Tips & Best Practices

1. **Always validate before export** - Use `validate_output_report()` with `strict=True`
2. **Cache industry config lookups** - Don't call `get_industry_config()` repeatedly
3. **Handle unknown industries gracefully** - Always have a fallback
4. **Use type hints** - Enable IDE autocomplete for industry configs
5. **Check for blocking issues** - Use `has_blocking_issues()` instead of checking issues list

---

## ❓ FAQ

**Q: What happens if I export a report without validation?**  
A: It might contain empty fields or wrong pack sections. Always validate first.

**Q: Can I add a new industry?**  
A: Yes! Add it to `INDUSTRY_CONFIGS` in `backend/industry_config.py`

**Q: What if the industry isn't recognized?**  
A: Functions return `None`. Your code should handle this gracefully.

**Q: Can I override the PDF template?**  
A: Yes, modify `TEMPLATE_BY_WOW_PACKAGE` or pass template name directly.

**Q: How do I test my changes?**  
A: Run the test suite: `pytest tests/test_*.py -v`

---

## 📞 Support

For issues or questions:
1. Check the test files for usage examples
2. Review docstrings in the implementation files
3. See the comprehensive test suite for edge cases
4. Refer to the audit documents for detailed architecture

---

**Last Updated:** November 27, 2025  
**Version:** 1.0  
**Status:** Production Ready ✅
