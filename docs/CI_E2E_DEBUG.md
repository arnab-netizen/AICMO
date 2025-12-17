# CI E2E Debug Instructions

If the E2E GitHub Actions workflow fails, collect the following evidence and attach to the issue or share with the engineering team. Do NOT include any secrets.

1. Failing step name
   - From the Actions UI, open the workflow run and note the step name that failed.

2. Last 120 lines of that step log
   - In Actions UI, open the failing step and copy the last ~120 lines of the log.

3. Backend readiness failure
   - If the failure occurred during the backend readiness step, collect the last 100 lines of `backend.log` from the run artifacts (or artifacts uploaded by the workflow).

4. Streamlit readiness failure
   - If the failure occurred during the Streamlit readiness step, collect the last 100 lines of `streamlit.log` from the run artifacts.

5. Playwright artifacts
   - Download `playwright-report` and `test-results` artifacts from the Actions run if present. Attach the `trace.zip` or the HTML report.

6. Console / browser errors
   - If Playwright reports browser console errors, include the console log from the Playwright run (available in the report or test output).

7. Failure reproduction commands (local)
   - To reproduce the environment locally (requires Node >=18 and Python 3.11):

```bash
# start backend (from repo root)
uvicorn backend.app:app --host 127.0.0.1 --port 8000

# start Streamlit (canonical)
BACKEND_URL=http://127.0.0.1:8000 AICMO_DEV_STUBS=0 AICMO_STRICT_TABKEYS=1 streamlit run operator_v2.py --server.port 8502 --server.headless true

# run Playwright locally
npm ci
npx playwright install --with-deps
npm run test:e2e -- --reporter=line
```

8. What not to share
   - Do not include API keys, secrets, or private environment variable values in logs or issue descriptions.

If you want, paste the failing step log here and I will diagnose the first failure and propose a fix (we will not loosen tests).