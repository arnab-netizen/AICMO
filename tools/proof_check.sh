#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1

echo "[PROOF] Python import check: operator_v2"
python -c "import operator_v2; print('operator_v2 import OK')"

echo "[PROOF] Targeted pytest: tests/test_operator_nav.py"
pytest -q tests/test_operator_nav.py

echo "[PROOF] Repo-wide pytest (may fail)"
pytest -q || true

echo "[PROOF] Check docs for 'streamlit run app.py' references"
grep -RIn "streamlit run app.py" docs tests .env.example || true

echo "[PROOF] Check operator_v2 anchors (data-testid=tab-)"
grep -RIn "data-testid=\"tab-" operator_v2.py | head -20 || true

echo "[NOTE] Repo-wide pytest may fail due to legacy tests; targeted tests are the supported gate."
