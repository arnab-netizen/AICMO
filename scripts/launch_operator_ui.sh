#!/usr/bin/env bash
# AICMO Canonical Operator Dashboard Launcher
#
# Usage:
#   ./scripts/launch_operator_ui.sh
#   bash scripts/launch_operator_ui.sh --server.port 8501

cd "$(dirname "$0")/.."

python -m streamlit run streamlit_pages/aicmo_operator.py "$@"
