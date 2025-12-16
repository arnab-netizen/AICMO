#!/bin/bash
#
# Start Streamlit in E2E mode with all required environment variables
#
# Usage: ./scripts/start_e2e_streamlit.sh

set -euo pipefail

echo "🚀 Starting AICMO in E2E Mode..."

# E2E Mode Configuration
export AICMO_E2E_MODE=1
export AICMO_E2E_DIAGNOSTICS=1
export AICMO_PROOF_RUN=1

# Persistence & Determinism
export AICMO_PERSISTENCE_MODE=db
export AICMO_TEST_SEED=e2e-deterministic-seed-2025

# Artifact Directory
export AICMO_E2E_ARTIFACT_DIR="${AICMO_E2E_ARTIFACT_DIR:-/workspaces/AICMO/artifacts/e2e}"
mkdir -p "$AICMO_E2E_ARTIFACT_DIR"

# Network Egress Lock
export AICMO_EGRESS_ALLOWLIST="^https?://127\.0\.0\.1,^https?://localhost,^https?://0\.0\.0\.0,^https?://.*\.local,^https?://internal\..*"

# Database Configuration (use test DB)
export DATABASE_URL="${DATABASE_URL:-sqlite:///$AICMO_E2E_ARTIFACT_DIR/e2e_test.db}"

# Streamlit Configuration
export STREAMLIT_SERVER_PORT=8501
export STREAMLIT_SERVER_HEADLESS=true

# Validation Contracts
export AICMO_CONTRACTS_PATH="/workspaces/AICMO/tests/e2e/specs/client_outputs.contract.json"

echo "✅ Environment configured:"
echo "   E2E_MODE: $AICMO_E2E_MODE"
echo "   PROOF_RUN: $AICMO_PROOF_RUN"
echo "   ARTIFACT_DIR: $AICMO_E2E_ARTIFACT_DIR"
echo "   DATABASE_URL: $DATABASE_URL"
echo ""

# Patch HTTP libraries to enforce egress lock
python3 -c "
from aicmo.safety import EgressLock
lock = EgressLock()
lock.patch_http_libraries()
print('✅ Network egress lock enabled')
"

# Start Streamlit (canonical UI: aicmo_operator.py)
echo "🌐 Starting Streamlit on port $STREAMLIT_SERVER_PORT..."
streamlit run /workspaces/AICMO/streamlit_pages/aicmo_operator.py \
    --server.port=$STREAMLIT_SERVER_PORT \
    --server.headless=true \
    --server.address=0.0.0.0
