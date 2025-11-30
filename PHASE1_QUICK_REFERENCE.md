# PHASE 1 Quick Reference Guide

## For Developers

### Adding a New Pack

1. **Define sections in `aicmo/presets/package_presets.py`**
   ```python
   "new_pack_key": {
       "label": "New Pack Name",
       "sections": ["overview", "section1", "section2", ...],
       "requires_research": True,
       "complexity": "medium",
   }
   ```

2. **Create schema in `backend/validators/pack_schemas.py`**
   ```python
   "new_pack_key": {
       "required_sections": ["overview", "section1", ...],
       "optional_sections": [],
       "enforce_order": True,
       "description": "Pack description",
       "expected_section_count": N,
   }
   ```

3. **Update golden snapshot test**
   - Add to `test_pack_schema_structure_unchanged()` in `test_pack_output_contracts.py`

4. **Validate**
   ```bash
   python3 -c "from backend.validators.pack_schemas import validate_schema_completeness; print(validate_schema_completeness())"
   ```

### Adding a New Section

1. **Create generator in `backend/main.py`**
   ```python
   def _gen_new_section(req: GenerateRequest, **kwargs) -> str:
       """Generate 'new_section' content."""
       return sanitize_output("Section content here", req.brief)
   ```

2. **Register in SECTION_GENERATORS**
   ```python
   SECTION_GENERATORS = {
       # ... existing sections
       "new_section": _gen_new_section,
   }
   ```

3. **Add to relevant pack schemas**
   - Update `required_sections` or `optional_sections` in pack schemas

## For QA/Testing

### Running Tests

```bash
# All contract tests
pytest backend/tests/test_pack_output_contracts.py -v

# Quick validation
python3 -c "from backend.validators.pack_schemas import validate_schema_completeness; print(validate_schema_completeness())"

# Test specific pack
pytest backend/tests/test_pack_output_contracts.py::test_quick_social_pack_has_all_required_sections -v
```

### Checking Report Validation

When testing reports in Streamlit, check logs for:
```
✅ Pack contract validation passed for {pack_key}
```

Or warnings:
```
⚠️  Pack contract validation failed for {pack_key}: {error}
```

## For Product/Operations

### Understanding Pack Contracts

Each pack has a **guaranteed structure** defined in schemas:

- **Required sections**: Must appear in every report of this pack type
- **Section order**: Sections appear in consistent order for better UX
- **Content validation**: Required sections must have content (not empty)

### Pack Size Reference

| Tier | Sections | Example Packs |
|------|----------|---------------|
| Basic | 6-10 | Quick Social, Strategy (Basic) |
| Standard | 13-16 | Strategy (Standard), Audit & Revamp |
| Premium | 23-28 | Full-Funnel, Strategy (Premium) |
| Enterprise | 39 | Strategy (Enterprise) |

### Quick Social 30-Day Calendar

Quick Social Pack **always includes** a 30-day content calendar:
- Generated automatically in `social_calendar` field
- Includes daily post recommendations
- Platform-specific content guidance
- Test verifies minimum 30 calendar entries

## Troubleshooting

### "Missing required sections" Error

**Cause:** Pack schema expects sections that aren't being generated.

**Fix:**
1. Check if section generator exists in `SECTION_GENERATORS`
2. Verify section is included in pack preset
3. Check WOW rule includes the section

### "Section order incorrect" Error

**Cause:** Report sections don't match schema order.

**Fix:**
1. Check pack preset section order matches schema
2. Verify WOW rule section order
3. Consider setting `enforce_order: False` if order doesn't matter

### Schema Validation Fails

**Cause:** Schema definition has issues (duplicate sections, wrong count, etc.)

**Fix:**
1. Run `validate_schema_completeness()` to see specific errors
2. Check `expected_section_count` matches actual count
3. Look for duplicate section IDs

## Monitoring

### Key Metrics to Track

1. **Validation Pass Rate**: Should be >95%
   - Log filter: `Pack contract validation passed`

2. **Most Common Failures**: Identify patterns
   - Log filter: `Pack contract validation failed`

3. **Pack Usage**: Which packs are used most
   - Track by `wow_package_key`

### Health Checks

Run weekly to ensure schemas stay consistent:
```bash
python3 -c "
from backend.validators.pack_schemas import validate_schema_completeness
errors = validate_schema_completeness()
print('Schema health:', 'OK' if not errors else f'ISSUES: {errors}')
"
```

## Support Contacts

- **Schema Changes**: Backend team
- **Test Failures**: QA team
- **Pack Definition Changes**: Product team
- **Validation Logic**: Backend team
