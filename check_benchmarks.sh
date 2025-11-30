#!/bin/bash
# AICMO Benchmark Validation Helper
# Usage: ./check_benchmarks.sh [pack_key|--all]

set -e

echo "🔍 AICMO Benchmark Validation Helper"
echo "===================================="
echo ""

# Ensure we're in REAL mode (no stub mode)
unset AICMO_STUB_MODE

if [ "$1" == "--all" ]; then
    echo "📋 Checking ALL packs..."
    echo ""
    python -m backend.debug.print_benchmark_issues --all
elif [ -n "$1" ]; then
    echo "📋 Checking pack: $1"
    echo ""
    python -m backend.debug.print_benchmark_issues "$1"
else
    echo "Usage:"
    echo "  ./check_benchmarks.sh strategy_campaign_premium"
    echo "  ./check_benchmarks.sh --all"
    echo ""
    echo "Available packs:"
    python -c "from backend.main import PACKAGE_PRESETS; print('\\n'.join('  - ' + k for k in sorted(PACKAGE_PRESETS.keys())))"
fi
