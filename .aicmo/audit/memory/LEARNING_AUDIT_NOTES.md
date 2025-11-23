# Learning & Package Preset Audit Notes

## Findings

### Phase 5A: Learning from Reports
- Status: ⚠️ PARTIAL
- The `/aicmo/generate` endpoint returned HTTP 422 due to validation error against `GenerateRequest` schema
- The endpoint requires full `ClientInputBrief` with nested structure: brand, audience, goal, voice, product_service, assets_constraints, operations, strategy_extras
- Memory engine (aicmo.memory.engine) confirmed working with 4574+ items stored
- Retrieval from memory verified successful (5 results returned for test query)
- Not fully tested end-to-end due to schema complexity

### Phase 5B: Learning from Files
- Status: ❌ FAILED
- The `/api/learn/from-files` endpoint returned HTTP 422
- Endpoint signature expects specific request format not identified in available tests
- File creation and upload logic confirmed working
- Memory roundtrip on temp file marker not verified

### Phase 6: Package Presets
- Status: ⚠️ PARTIAL
- Successfully discovered PACKAGE_PRESETS dict in streamlit_pages/aicmo_operator.py
- Found 9 presets: "Quick Social Pack (Basic)", "Strategy + Campaign Pack (Standard)", etc.
- Attempted POST to `/aicmo/generate` with preset flags returned HTTP 422
- Root cause: GenerateRequest validation failure (same as Phase 5A)
- Presets object structure accessible but not tested against actual endpoint

## Issues Blocking Full Testing
1. GenerateRequest model requires complete, nested ClientInputBrief
2. Learning endpoints may have different payload format than what was attempted
3. No payload examples found in existing backend tests for learning endpoints

## Recommendations for Further Investigation
- Review backend/tests/ for actual GenerateRequest payloads used in working tests
- Check learning endpoint definitions in backend/services/learning.py or similar
- Consider using existing test fixtures as reference for correct payload structure
