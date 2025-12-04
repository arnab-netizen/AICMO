# AICMO Pack Hardening - Action Plan

**Status**: READY TO EXECUTE  
**Date**: 2024-12-04  
**Scope**: 5 packs, ~80 sections total

---

## Executive Summary

After successful hardening of `strategy_campaign_standard` (17 sections, 0 errors, 2 intentional warnings), we need to apply the same methodology to 5 remaining packs:

1. **launch_gtm_pack** (13 sections) - Launch and go-to-market strategies
2. **brand_turnaround_lab** (14 sections) - Brand recovery and repositioning  
3. **retention_crm_booster** (14 sections) - Customer retention and CRM optimization
4. **performance_audit_revamp** (16 sections) - Campaign audit and performance fixes
5. **full_funnel_growth_suite** (23 sections) - Comprehensive full-funnel marketing

**Total**: 80 sections to harden

---

## Proven Hardening Methodology

Based on `strategy_campaign_standard` success:

### Phase 1: Structural Alignment (Per Pack)
1. Verify `PACK_SECTION_WHITELIST` matches `pack_schemas.py`
2. Verify WOW template placeholders match whitelist
3. Add title→ID mappings in `wow_markdown_parser.py` if needed
4. Create `test_<pack_key>_structure.py`

### Phase 2: Generator Quality (Per Section)
1. Audit generator for stubby language:
   - Remove: "This section will...", "Insert...", "Here you..."
   - Add: Concrete tactics, specific platforms, real numbers
2. Fix heading structure:
   - WOW template provides `## N. Section Name`
   - Generator uses `###` for all subsections
   - Never duplicate the main `##` heading
3. Ensure data usage:
   - Use `req.brief.brand.brand_name`, `.industry`, `.geography`
   - Use `req.brief.goal.primary_goal`, `.timeline`, `.kpis`
   - Provide realistic examples when data missing
4. Always call `sanitize_output(markdown_text, req.brief)`

### Phase 3: Quality Gates (Per Section)
Common benchmark issues to fix:
- **SENTENCES_TOO_LONG**: Split compound sentences, use bullets
- **TOO_GENERIC**: Add specific channel names, frequencies, KPIs
- **LIGHT_CONTENT / TOO_SHORT**: Add meaningful detail (not fluff)
- **MISSING_HEADING**: Add `### Required Heading Name`
- **TOO_MANY_BULLETS**: Convert some bullets to prose paragraphs
- **BLACKLIST**: Replace "best practices" → "recommended approaches"

### Phase 4: Validation Proof (Per Pack)
1. Create `test_<pack_key>.py` (like `test_strategy_campaign_standard.py`)
2. Run test, fix all ERRORS (0 required)
3. Minimize WARNINGS (document intentional ones)
4. Create `scripts/dev_validate_<pack_key>.py` proof script
5. Final status: 0 errors, minimal warnings

### Phase 5: Documentation (Per Pack)
1. Create `<PACK_KEY_UPPER>_QUALITY_REPORT.md`
2. Document section matrix (all sections + status)
3. Document changes made
4. Document intentional warnings (if any)
5. Update `PACK_HARDENING_PROGRESS.md` to mark [x] complete

---

## Pack-Specific Details

### 1. launch_gtm_pack (13 sections)

**Benchmark File**: `learning/benchmarks/section_benchmarks.launch_gtm.json`

**Section List**:
1. overview (120-280 words, 3-8 bullets, headings: Brand, Industry, Primary Goal)
2. market_landscape (260-700 words, 6-20 bullets, headings: Market Size, Trends, Opportunities)
3. product_positioning (240-650 words, 5-18 bullets, headings: Positioning Statement, Target Audience)
4. messaging_framework (200-550 words, 4-15 bullets, headings: Core Message, Key Themes)
5. launch_phases (260-750 words, 8-25 bullets, headings: Pre-Launch, Launch, Post-Launch)
6. channel_plan (260-750 words, 6-22 bullets, headings: Primary Channels, Channel Strategy)
7. audience_segments (180-500 words, 4-15 bullets, headings: Primary Audience, Secondary Audience)
8. creative_direction (260-700 words, 6-20 bullets, headings: Visual Style, Tone of Voice)
9. launch_campaign_ideas (280-800 words, 8-25 bullets, headings: Campaign Concepts, Activation Ideas)
10. content_calendar_launch (280-900 words, 10-35 bullets, headings: Week 1, Week 2, must include table)
11. ad_concepts (280-800 words, 8-25 bullets, headings: Ad Concepts, Messaging)
12. execution_roadmap (260-800 words, 8-30 bullets, headings: Phase 1, Phase 2, Key Milestones, table)
13. final_summary (180-400 words, 3-10 bullets, headings: Key Takeaways)

**Existing Generators** (verified):
- ✅ _gen_market_landscape (line 5303)
- ✅ _gen_product_positioning (line 5672)
- ✅ _gen_launch_phases (line 5198)
- ✅ _gen_launch_campaign_ideas (line 5138)
- ✅ _gen_content_calendar_launch (line 4496)
- ⚠️ Others: Check for existence, quality

**Estimated Complexity**: MEDIUM (some generators exist, need quality fixes)

---

### 2. brand_turnaround_lab (14 sections)

**Benchmark File**: `learning/benchmarks/section_benchmarks.brand_turnaround.json`

**Section List**:
1. overview
2. brand_audit
3. customer_insights
4. competitor_analysis
5. problem_diagnosis
6. new_positioning
7. messaging_framework
8. creative_direction
9. channel_reset_strategy
10. reputation_recovery_plan
11. promotions_and_offers
12. 30_day_recovery_calendar
13. execution_roadmap
14. final_summary

**Existing Generators**: To be determined

**Estimated Complexity**: MEDIUM-HIGH (turnaround focus requires specific diagnostic language)

---

### 3. retention_crm_booster (14 sections)

**Benchmark File**: `learning/benchmarks/section_benchmarks.retention_crm.json`

**Section List**:
1. overview
2. customer_segments
3. persona_cards
4. customer_journey_map
5. churn_diagnosis
6. email_automation_flows
7. sms_and_whatsapp_flows
8. loyalty_program_concepts
9. winback_sequence
10. post_purchase_experience
11. ugc_and_community_plan
12. kpi_plan_retention
13. execution_roadmap
14. final_summary

**Existing Generators**: To be determined

**Estimated Complexity**: MEDIUM (CRM/retention focus, concrete flows required)

---

### 4. performance_audit_revamp (16 sections)

**Benchmark File**: `learning/benchmarks/section_benchmarks.performance_audit.json`

**Section List**:
1. overview
2. account_audit
3. campaign_level_findings
4. creative_performance_analysis
5. audience_analysis
6. funnel_breakdown
7. competitor_benchmark
8. problem_diagnosis
9. revamp_strategy
10. new_ad_concepts
11. creative_direction
12. conversion_audit
13. remarketing_strategy
14. kpi_reset_plan
15. execution_roadmap
16. final_summary

**Existing Generators**: To be determined

**Estimated Complexity**: MEDIUM-HIGH (audit focus requires analytical language and metrics)

---

### 5. full_funnel_growth_suite (23 sections)

**Benchmark File**: `learning/benchmarks/section_benchmarks.full_funnel.json`

**Section List**:
1. overview
2. market_landscape
3. competitor_analysis
4. funnel_breakdown
5. audience_segments
6. persona_cards
7. value_proposition_map
8. messaging_framework
9. awareness_strategy
10. consideration_strategy
11. conversion_strategy
12. retention_strategy
13. landing_page_blueprint
14. email_automation_flows
15. remarketing_strategy
16. ad_concepts_multi_platform
17. creative_direction
18. full_30_day_calendar
19. kpi_and_budget_plan
20. measurement_framework
21. execution_roadmap
22. optimization_opportunities
23. final_summary

**Existing Generators**: To be determined

**Estimated Complexity**: HIGH (largest pack, 23 sections, full-funnel comprehensive)

---

## Execution Strategy

### Recommended Order

Execute packs in order of ascending complexity:

1. **launch_gtm_pack** (13 sections, MEDIUM) - Start here, some generators exist
2. **retention_crm_booster** (14 sections, MEDIUM) - Clear focus area
3. **brand_turnaround_lab** (14 sections, MEDIUM-HIGH) - Diagnostic angle
4. **performance_audit_revamp** (16 sections, MEDIUM-HIGH) - Analytical focus
5. **full_funnel_growth_suite** (23 sections, HIGH) - Do last, most comprehensive

### Per-Pack Process

For EACH pack, complete ALL steps before moving to next:

**Day 1: Setup & Assessment**
- [ ] Create test file: `test_<pack_key>.py`
- [ ] Create proof script: `scripts/dev_validate_<pack_key>.py`
- [ ] Run initial test, document baseline errors/warnings
- [ ] Identify which generators exist vs need creation

**Day 2-3: Generator Fixes**
- [ ] Fix/create each generator following methodology
- [ ] Test incrementally (run test after each 3-5 sections)
- [ ] Fix errors first, then address warnings

**Day 4: Validation & Documentation**
- [ ] Achieve 0 errors in test
- [ ] Run proof script, verify PASS status
- [ ] Create quality report markdown
- [ ] Update progress tracker
- [ ] Run regression tests (ensure other packs unaffected)

**Total Estimate**: 4-5 days per pack = 20-25 days for all 5 packs

---

## Quality Gates

### Must-Pass Criteria (Per Pack)

1. ✅ **Structural**: PACK_SECTION_WHITELIST == pack_schemas.py == WOW template placeholders
2. ✅ **Validation**: 0 errors in `test_<pack_key>.py`
3. ✅ **Content**: No stubby language, concrete tactics, professional tone
4. ✅ **Testing**: Both test file and proof script passing
5. ✅ **Documentation**: Quality report created with section matrix
6. ✅ **Regression**: All existing tests (quick_social_basic, strategy_campaign_standard) still green

### Acceptable Trade-offs

- ⚠️ **Warnings**: Up to 3 intentional warnings per pack (if well-documented)
  - Example: Slightly long sentences for strategic nuance
  - Must document WHY each warning is acceptable
- ⚠️ **Word Count**: Aim for middle of range, not maximum
  - Too short = generic
  - Too long = fluff
  - Sweet spot = comprehensive + concise

---

## Risk Mitigation

### Risks

1. **Scope Creep**: 80 sections is large, could take longer than estimated
2. **Generator Interdependencies**: Fixing one section might affect others
3. **Benchmark Conflicts**: Different packs have different quality standards
4. **Regression**: Changes could break existing hardened packs

### Mitigations

1. **Work Sequentially**: Complete one pack fully before starting next
2. **Test Frequently**: Run tests after every 3-5 section fixes
3. **Use Templates**: Copy patterns from strategy_campaign_standard generators
4. **Run Regression**: After each pack completion, verify:
   - `python test_strategy_campaign_standard.py` (must stay green)
   - `python scripts/dev_validate_strategy_campaign_standard.py` (must stay PASS)
   - `pytest tests/test_wow_markdown_parser.py` (must stay green)

---

## Success Metrics

### Per-Pack Success
- ✅ 0 validation errors
- ✅ <5 validation warnings (documented)
- ✅ All sections use concrete tactics (no "insert here", "will outline")
- ✅ Quality report created
- ✅ Regression tests pass

### Global Success (All 5 Packs)
- ✅ All 5 packs marked [x] complete in `PACK_HARDENING_PROGRESS.md`
- ✅ All 5 quality reports created
- ✅ 0 errors across all 80 sections
- ✅ <15 total warnings across all packs (avg 3 per pack)
- ✅ No regressions in existing tests
- ✅ Ready for client delivery

---

## Next Immediate Step

**START HERE**: Launch GTM Pack (13 sections)

1. Run: `python test_launch_gtm_pack.py` (create if doesn't exist)
2. Document baseline: X errors, Y warnings
3. Begin fixing generators in benchmark order
4. Target: 0 errors by end of Day 3

---

**Document Status**: READY TO EXECUTE  
**Owner**: Development Team  
**Timeline**: 20-25 days (4-5 days per pack)  
**Dependencies**: None (strategy_campaign_standard methodology proven)
