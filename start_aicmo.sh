#!/bin/bash
# Start AICMO services with LLM enhancement enabled

set -a
export OPENAI_API_KEY="${OPENAI_API_KEY:-your-openai-api-key-here}"
export AICMO_OPENAI_MODEL="gpt-4o-mini"
export AICMO_USE_LLM=1
set +a

cd /workspaces/AICMO
source .venv-1/bin/activate

echo "🚀 Starting AICMO with LLM enhancement enabled..."
echo ""
echo "Environment variables set:"
echo "  ✅ OPENAI_API_KEY: ${OPENAI_API_KEY:0:30}..."
echo "  ✅ AICMO_OPENAI_MODEL: $AICMO_OPENAI_MODEL"
echo "  ✅ AICMO_USE_LLM: $AICMO_USE_LLM"
echo ""
echo "Services:"
echo "  📊 Backend:   http://127.0.0.1:8000"
echo "  📱 Streamlit: http://127.0.0.1:8501"
echo ""

# Start backend in background
echo "Starting backend..."
uvicorn backend.main:app --reload --port 8000 &
BACKEND_PID=$!

sleep 3

# Start Streamlit wrapper
echo "Starting Streamlit..."
python run_streamlit.py

# Cleanup on exit
trap "kill $BACKEND_PID 2>/dev/null" EXIT
