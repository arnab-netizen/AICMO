#!/bin/bash
#
# CI E2E Gate Script
#
# This script runs the complete E2E gate check and exits with:
# - 0 if all tests pass and validation is GREEN
# - 1 if any tests fail or validation is not PASS
#
# Usage: ./scripts/ci_e2e_gate.sh

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ARTIFACT_DIR="${AICMO_E2E_ARTIFACT_DIR:-$PROJECT_ROOT/artifacts/e2e}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 AICMO E2E Client Output Gate - CI Run"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Clean artifact directory
echo "🧹 Cleaning artifact directory..."
rm -rf "$ARTIFACT_DIR"
mkdir -p "$ARTIFACT_DIR"

# Start Streamlit in background
echo "🚀 Starting AICMO in E2E mode..."
"$SCRIPT_DIR/start_e2e_streamlit.sh" &
STREAMLIT_PID=$!

# Wait for Streamlit to be ready
echo "⏳ Waiting for Streamlit to start..."
for i in {1..30}; do
    if curl -s http://localhost:8501 > /dev/null 2>&1; then
        echo "✅ Streamlit ready"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Streamlit failed to start"
        kill $STREAMLIT_PID 2>/dev/null || true
        exit 1
    fi
    sleep 1
done

# Run Playwright tests
echo ""
echo "🧪 Running E2E tests..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

TEST_FAILED=0

# Positive tests
echo ""
echo "📋 Running positive tests..."
if ! npx playwright test tests/playwright/e2e_strict/positive_tests.spec.ts; then
    echo "❌ Positive tests failed"
    TEST_FAILED=1
else
    echo "✅ Positive tests passed"
fi

# Negative tests
echo ""
echo "🚫 Running negative tests..."
if ! npx playwright test tests/playwright/e2e_strict/negative_tests.spec.ts; then
    echo "❌ Negative tests failed"
    TEST_FAILED=1
else
    echo "✅ Negative tests passed"
fi

# Stop Streamlit
echo ""
echo "🛑 Stopping Streamlit..."
kill $STREAMLIT_PID 2>/dev/null || true
wait $STREAMLIT_PID 2>/dev/null || true

# Check validation report
echo ""
echo "📊 Checking validation report..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if ! "$SCRIPT_DIR/check_e2e_validation.sh"; then
    echo "❌ Validation check failed"
    TEST_FAILED=1
fi

# Final result
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $TEST_FAILED -eq 0 ]; then
    echo "✅ E2E GATE: GREEN"
    echo "   All tests passed and validation is PASS"
    echo "   Safe to deliver client-facing outputs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo "❌ E2E GATE: RED"
    echo "   Tests failed or validation is not PASS"
    echo "   DO NOT deliver client-facing outputs"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Upload artifacts on failure
    if [ -d "$ARTIFACT_DIR" ]; then
        echo ""
        echo "📦 Artifacts available at: $ARTIFACT_DIR"
        echo "   - validation_report.json"
        echo "   - manifest.json"
        echo "   - proof_run_ledger.json"
        echo "   - (all generated outputs)"
    fi
    
    exit 1
fi
