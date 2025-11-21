#!/usr/bin/env bash
set -euo pipefail

echo "== AICMO Local Simulation =="

echo
echo "1) Running backend tests..."
pytest -q

echo
echo "2) Scanning for stubs / TODOs..."
python tools/scan_for_stubs.py

echo
echo "✅ Local simulation completed: tests green and no obvious stubs."
