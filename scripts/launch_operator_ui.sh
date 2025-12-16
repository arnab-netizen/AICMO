#!/usr/bin/env bash
# AICMO Canonical Operator Dashboard V2 Launcher
#
# Updated to run operator_v2.py (modular architecture with 11 tabs)
# Previous: streamlit_pages/aicmo_operator.py
#
# Usage:
#   ./scripts/launch_operator_ui.sh
#   bash scripts/launch_operator_ui.sh --server.port 8501

cd "$(dirname "$0")/.."

python -m streamlit run operator_v2.py "$@"
