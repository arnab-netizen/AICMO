#!/bin/bash
# Phase 0: Reproduces Streamlit E2E abort with diagnostics
# Usage: bash scripts/e2e/repro_streamlit_abort.sh

set -euo pipefail

REPO_ROOT="/workspaces/AICMO"
LOG_FILE="/tmp/aicmo_streamlit_e2e.log"
ARTIFACTS_DIR="${AICMO_E2E_ARTIFACT_DIR:-/tmp/aicmo_e2e_artifacts}"
PORT=8501
TIMEOUT=15

cd "$REPO_ROOT"

echo "=== Phase 0: Streamlit E2E Abort Reproduction ==="
echo "Log: $LOG_FILE"
echo "Artifacts: $ARTIFACTS_DIR"

# Kill existing processes
echo "[1/5] Killing existing streamlit/app processes..."
pkill -9 -f "streamlit|python.*app\.py" || true
sleep 2

# Create artifacts dir
mkdir -p "$ARTIFACTS_DIR"

# Start Streamlit with strict logging
echo "[2/5] Starting Streamlit with debug logging..."
rm -f "$LOG_FILE"
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1
export AICMO_PROOF_RUN=1
export AICMO_PERSISTENCE_MODE=db
export AICMO_E2E_ARTIFACT_DIR="$ARTIFACTS_DIR"

timeout $TIMEOUT python -m streamlit run "$REPO_ROOT/app.py" \
  --server.port $PORT \
  --server.runOnSave=false \
  --logger.level=debug \
  2>&1 | tee "$LOG_FILE" &
  
STREAMLIT_PID=$!
sleep 4

# Check server is up
echo "[3/5] Checking Streamlit server is responding..."
if ! curl -s -m 3 "http://localhost:$PORT" > /dev/null 2>&1; then
  echo "❌ Streamlit server not responding on port $PORT"
  echo ""
  echo "=== Last 100 lines of log ==="
  tail -100 "$LOG_FILE"
  kill -9 $STREAMLIT_PID || true
  exit 1
fi
echo "✓ Server responding"

# Fetch page and check for sentinels
echo "[4/5] Fetching page and checking for sentinels..."
PAGE_HTML=$(curl -s "http://localhost:$PORT" | head -5000)

if echo "$PAGE_HTML" | grep -q 'e2e-app-loaded'; then
  echo "✓ e2e-app-loaded sentinel FOUND"
  SENTINEL_FOUND=true
else
  echo "❌ e2e-app-loaded sentinel NOT FOUND"
  SENTINEL_FOUND=false
fi

# List all breadcrumbs found
echo ""
echo "=== Breadcrumb Status ==="
for i in 01 02 03 04 05; do
  testid="e2e-breadcrumb-$i-"
  if echo "$PAGE_HTML" | grep -q "$testid"; then
    FOUND=$(echo "$PAGE_HTML" | grep -o "${testid}[^\"]*" | head -1)
    echo "✓ $FOUND found"
  else
    echo "✗ e2e-breadcrumb-$i-* NOT found"
  fi
done

# Check for fatal exception marker
echo ""
echo "=== Fatal Exception Check ==="
if echo "$PAGE_HTML" | grep -q 'e2e-fatal-exception'; then
  echo "❌ FATAL EXCEPTION DETECTED in HTML"
elif [ -f "$ARTIFACTS_DIR/fatal_exception.json" ]; then
  echo "❌ FATAL EXCEPTION FILE EXISTS"
  cat "$ARTIFACTS_DIR/fatal_exception.json" | head -50
else
  echo "✓ No fatal exceptions detected"
fi

# Show decision
echo ""
echo "=== Result ==="
if [ "$SENTINEL_FOUND" = true ]; then
  echo "✓✓✓ REPRO PASSED: e2e-app-loaded rendered successfully"
  kill -9 $STREAMLIT_PID || true
  exit 0
else
  echo "❌❌❌ REPRO FAILED: Streamlit aborted before rendering sentinels"
  echo ""
  echo "=== Last 200 lines of log ==="
  tail -200 "$LOG_FILE"
  kill -9 $STREAMLIT_PID || true
  exit 1
fi
