# Playwright E2E — AICMO

Requirements:

- Node >= 18

Local run (install deps first):

```bash
npm ci
npx playwright install --with-deps
npm run test:e2e
```

Run headful:

```bash
npm run test:e2e:headed
```

Streamlit entrypoint (canonical for E2E):

```bash
BACKEND_URL=http://127.0.0.1:8000 AICMO_DEV_STUBS=0 streamlit run operator_v2.py --server.port 8502 --server.headless true
```

Environment variables (copy `.env.example` to `.env` and edit):

- `AICMO_UI_BASE_URL` (default http://127.0.0.1:8502)
- `BACKEND_URL` (used by the Streamlit UI to contact backend)
- `AICMO_BACKEND_BASE_URL` (used by backend contract tests, default http://127.0.0.1:8000)
- `AICMO_DEV_STUBS` must be unset or `0` for production-style testing
- `AICMO_STRICT_TABKEYS` optional: set to `1` to make tab_key mismatches raise a hard error

CI notes:

- Use Node 18+ runner (GitHub Actions provided below).
- Tests will retry on CI based on Playwright config.
- Traces, videos and screenshots are retained on failure and uploaded by the workflow.

Known limitation:

- Node/npm (>=18) is required to run Playwright locally or in CI.
- Playwright tests must run in CI or a local Node-enabled environment — do not attempt to run them inside the Streamlit container.

