# 📝 Exact Code Changes Required

## Copy-Paste Ready Fixes

Each section below shows the exact before/after for each file.

---

## Fix #1: Add Output Validator to /aicmo/generate

**File:** `backend/main.py`  
**Location:** Line ~1967 (after `base_output = _apply_wow_to_output(base_output, req)`)  
**Changes:** Add 15 lines

```python
# ════════════════════════════════════════════════════════════════════
# BEFORE (current code at line 1965-1970):
# ════════════════════════════════════════════════════════════════════
        # Phase L: Auto-learn from this final report (gated by AICMO_ENABLE_HTTP_LEARNING)
        # Import quality gate check
        from backend.quality_gates import is_report_learnable

        if AICMO_ENABLE_HTTP_LEARNING:
            try:

# ════════════════════════════════════════════════════════════════════
# AFTER (insert between lines 1967 and 1968):
# ════════════════════════════════════════════════════════════════════
        # Phase L: Auto-learn from this final report (gated by AICMO_ENABLE_HTTP_LEARNING)
        # Import quality gate check
        from backend.quality_gates import is_report_learnable

        # 🔥 FIX #6: Validate output before export
        try:
            from backend.validators import OutputValidator
            
            validator = OutputValidator(
                output=base_output,
                brief=req.brief,
                wow_package_key=req.wow_package_key if req.wow_enabled else None
            )
            issues = validator.validate_all()
            
            error_count = sum(1 for i in issues if i.severity == "error")
            if error_count > 0 and req.wow_enabled:
                logger.warning(f"Output validation: {error_count} blocking issues detected")
                logger.debug(validator.get_error_summary())
        except Exception as e:
            logger.debug(f"Output validation failed (non-critical): {e}")

        if AICMO_ENABLE_HTTP_LEARNING:
            try:
```

---

## Fix #2A: Wire Industry Config - Personas

**File:** `backend/main.py`  
**Location:** In `_generate_stub_output()` function, around line 1450  
**Changes:** Replace generic persona generation with industry-aware version

```python
# ════════════════════════════════════════════════════════════════════
# BEFORE (current code around line 1450):
# ════════════════════════════════════════════════════════════════════
    # Personas
    if req.generate_personas:
        persona_cards = [
            PersonaCard(
                name=f"{a.primary_customer} 1",
                role=f"{a.primary_customer}",
                # ... generic persona fields
            ),
            PersonaCard(
                name=f"{a.secondary_customer} 1" if a.secondary_customer else "Decision Influencer",
                role=a.secondary_customer or "Other stakeholder",
                # ... generic fields
            ),
        ]
    else:
        persona_cards = None

# ════════════════════════════════════════════════════════════════════
# AFTER (replace with):
# ════════════════════════════════════════════════════════════════════
    # Personas
    persona_cards: Optional[List[PersonaCard]] = None
    if req.generate_personas:
        # 🔥 FIX #4: Try industry-specific personas first
        from backend.industry_config import get_default_personas_for_industry
        
        industry = req.brief.brand.industry
        industry_personas = get_default_personas_for_industry(industry) if industry else None
        
        if industry_personas:
            logger.info(f"Using {len(industry_personas)} industry-specific personas for {industry}")
            persona_cards = [
                PersonaCard(
                    name=p.get("name", "Unknown Persona"),
                    role=p.get("role", "Stakeholder"),
                    description=f"Age: {p.get('age_range', 'N/A')}",
                    primary_goals=", ".join(p.get("primary_goals", [])),
                    pain_points=", ".join(p.get("primary_pain_points", [])),
                    decision_factors=", ".join(p.get("decision_factors", [])),
                    channel_preference=p.get("channel_preference", "Multi-channel"),
                )
                for p in industry_personas
            ]
        else:
            # Fallback to generic personas
            logger.debug(f"No industry config for {industry}, using generic personas")
            persona_cards = [
                PersonaCard(
                    name=f"{a.primary_customer} 1",
                    role=f"{a.primary_customer}",
                    description="Primary customer segment",
                    primary_goals=g.primary_goal or "Unspecified",
                    pain_points="Inconsistent results from marketing efforts",
                ),
                PersonaCard(
                    name=f"{a.secondary_customer} 1" if a.secondary_customer else "Decision Influencer",
                    role=a.secondary_customer or "Other stakeholder",
                    description="Secondary influencer",
                    primary_goals="Support primary buyer",
                    pain_points="Lack of clarity on ROI",
                ),
            ]
```

---

## Fix #2B: Wire Industry Config - Channels

**File:** `backend/main.py`  
**Location:** In `_generate_stub_output()`, around line 1520 (in strategy section)  
**Changes:** Add industry-aware channel logic

```python
# ════════════════════════════════════════════════════════════════════
# BEFORE (current code):
# ════════════════════════════════════════════════════════════════════
    s = Strategy(
        channel_focus=c.primary_channel or "Instagram, LinkedIn, Email",
        # ... rest of strategy
    )

# ════════════════════════════════════════════════════════════════════
# AFTER (replace with):
# ════════════════════════════════════════════════════════════════════
    # 🔥 FIX #4: Load industry-specific channels
    from backend.industry_config import get_industry_config
    
    industry = req.brief.brand.industry
    industry_config = get_industry_config(industry) if industry else None
    
    if industry_config:
        channels = industry_config.get("channels", {})
        primary_channel = channels.get("primary", "Instagram")
        secondary_channels = ", ".join(channels.get("secondary", []))
        channel_focus = f"{primary_channel}, {secondary_channels}"
        logger.info(f"Using industry channels for {industry}: {channel_focus}")
    else:
        channel_focus = c.primary_channel or "Instagram, LinkedIn, Email"
        logger.debug(f"Using generic channels (no industry config for {industry})")
    
    s = Strategy(
        channel_focus=channel_focus,
        # ... rest of strategy
    )
```

---

## Fix #3: Apply Pack Scoping Whitelist

**File:** `backend/main.py`  
**Location:** In `_generate_stub_output()`, around line 1755  
**Changes:** Filter sections by pack before generation

```python
# ════════════════════════════════════════════════════════════════════
# BEFORE (current code):
# ════════════════════════════════════════════════════════════════════
    # Build extra_sections for package-specific presets
    extra_sections: Dict[str, str] = {}

    if req.package_preset:
        # 🔥 Convert display name to preset key if needed
        preset_key = PACKAGE_NAME_TO_KEY.get(req.package_preset, req.package_preset)
        preset = PACKAGE_PRESETS.get(preset_key)
        if preset:
            # Get the section_ids list from the preset
            section_ids = preset.get("sections", [])

            # Use the generalized generate_sections() function
            # This is pack-agnostic and works for any preset (Basic, Standard, Premium, Enterprise)
            extra_sections = generate_sections(
                section_ids=section_ids,
                req=req,
                mp=mp,
                cb=cb,
                cal=cal,
                pr=pr,
                creatives=creatives,
                action_plan=action_plan,
            )

# ════════════════════════════════════════════════════════════════════
# AFTER (replace with):
# ════════════════════════════════════════════════════════════════════
    # Build extra_sections for package-specific presets
    extra_sections: Dict[str, str] = {}

    if req.package_preset:
        # 🔥 Convert display name to preset key if needed
        preset_key = PACKAGE_NAME_TO_KEY.get(req.package_preset, req.package_preset)
        preset = PACKAGE_PRESETS.get(preset_key)
        if preset:
            # Get the section_ids list from the preset
            section_ids = preset.get("sections", [])
            
            # 🔥 FIX #2: Apply pack-scoping whitelist
            if req.wow_enabled and req.wow_package_key:
                allowed_sections = get_allowed_sections_for_pack(req.wow_package_key)
                if allowed_sections:
                    original_count = len(section_ids)
                    section_ids = [s for s in section_ids if s in allowed_sections]
                    
                    logger.info(
                        f"Pack scoping applied for {req.wow_package_key}: "
                        f"{original_count} sections → {len(section_ids)} allowed sections"
                    )
                    
                    if len(section_ids) != original_count:
                        filtered_out = set(preset.get("sections", [])) - set(section_ids)
                        logger.debug(f"Filtered out sections: {filtered_out}")

            # Use the generalized generate_sections() function
            extra_sections = generate_sections(
                section_ids=section_ids,
                req=req,
                mp=mp,
                cb=cb,
                cal=cal,
                pr=pr,
                creatives=creatives,
                action_plan=action_plan,
            )
```

---

## Fix #4: Update pytest.ini

**File:** `pytest.ini`  
**Location:** Line 2  
**Changes:** Add tests directory to search path

```ini
# ════════════════════════════════════════════════════════════════════
# BEFORE:
# ════════════════════════════════════════════════════════════════════
[pytest]
testpaths = backend/tests
addopts = -v

# ════════════════════════════════════════════════════════════════════
# AFTER:
# ════════════════════════════════════════════════════════════════════
[pytest]
testpaths = tests backend/tests
addopts = -v --tb=short
```

---

## Verification Commands

After making all changes, run these to verify:

```bash
# 1. Check syntax
python -m py_compile backend/main.py

# 2. Check imports
python -c "from backend.validators import OutputValidator; print('✅ Validators OK')"
python -c "from backend.industry_config import get_industry_config; print('✅ Industry config OK')"

# 3. Run test discovery
pytest tests/ --collect-only -q

# 4. Run all new tests
pytest tests/test_output_validation.py tests/test_industry_alignment.py tests/test_pdf_templates.py -v

# 5. Test a generation locally (if backend running)
curl -X POST http://localhost:8000/aicmo/generate \
  -H "Content-Type: application/json" \
  -d '{
    "brief": {
      "brand": {"brand_name": "Test", "industry": "saas", "product_service": "Software", "primary_goal": "Growth"},
      "goal": {"primary_goal": "100 leads/month"},
      "audience": {"primary_customer": "CTOs"}
    },
    "wow_enabled": true,
    "wow_package_key": "quick_social_basic"
  }'
```

---

## Summary

**Files to modify:** 2 (backend/main.py, pytest.ini)  
**Total lines added:** ~90  
**Total time:** ~60 minutes  
**Risk:** 🟢 LOW (isolated changes, no API modifications)

All changes are additive and maintain backward compatibility.

