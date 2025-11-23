# Backend API Endpoint Audit

**Total Routes**: 23
**Successfully Tested**: 9
**Skipped**: 12
**Errored**: 0

## Test Results

All detailed results saved in:
- routes.json (full route list)
- smoke_test_results.json (test execution results)

## Tested Endpoints (200 OK)

- ✅ /docs (200)
- ✅ /docs/oauth2-redirect (200)
- ✅ /redoc (200)
- ✅ /health (200)
- ✅ /health/db (200)
- ✅ /api/learn/debug/summary (200)
- ✅ /templates/intake (200)
- ✅ /aicmo/industries (200)

## Errored Endpoints


## Skipped Endpoints

- ⏭️  /api/learn/from-report: no known sample payload
- ⏭️  /api/learn/from-files: no known sample payload
- ⏭️  /intake/json: no known sample payload
- ⏭️  /intake/file: no known sample payload
- ⏭️  /reports/marketing_plan: no known sample payload
- ⏭️  /reports/campaign_blueprint: no known sample payload
- ⏭️  /reports/social_calendar: no known sample payload
- ⏭️  /reports/performance_review: no known sample payload
- ⏭️  /aicmo/revise: no known sample payload
- ⏭️  /aicmo/export/pdf: export endpoints need valid report; skipped to avoid artifacts
- ⏭️  /aicmo/export/pptx: export endpoints need valid report; skipped to avoid artifacts
- ⏭️  /aicmo/export/zip: export endpoints need valid report; skipped to avoid artifacts
