#!/bin/bash
#
# Check E2E Validation Report
#
# This script reads the validation report and checks if it meets GREEN criteria:
# 1. Global status = PASS
# 2. All artifacts = PASS
# 3. No placeholders
# 4. No forbidden phrases
# 5. No external sends in proof-run
# 6. No egress violations
#
# Usage: ./scripts/check_e2e_validation.sh

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ARTIFACT_DIR="${AICMO_E2E_ARTIFACT_DIR:-$PROJECT_ROOT/artifacts/e2e}"
VALIDATION_REPORT="$ARTIFACT_DIR/validation_report.json"

echo "📊 Checking E2E Validation Report..."
echo ""

# Check if validation report exists
if [ ! -f "$VALIDATION_REPORT" ]; then
    echo "❌ Validation report not found: $VALIDATION_REPORT"
    exit 1
fi

# Check if jq is available
if ! command -v jq &> /dev/null; then
    echo "❌ jq is required but not installed"
    echo "   Install: sudo apt-get install jq"
    exit 1
fi

# Read report
GLOBAL_STATUS=$(jq -r '.global_status' "$VALIDATION_REPORT")
echo "Global Status: $GLOBAL_STATUS"

if [ "$GLOBAL_STATUS" != "PASS" ]; then
    echo "❌ Global status is not PASS"
    echo ""
    echo "Failure Summary:"
    jq -r '.artifacts[] | select(.status == "FAIL") | "  - \(.artifact_id): \(.issues | join(", "))"' "$VALIDATION_REPORT"
    exit 1
fi

# Check all artifacts
echo ""
echo "Artifact Status:"
FAILED_ARTIFACTS=$(jq -r '.artifacts[] | select(.status == "FAIL") | .artifact_id' "$VALIDATION_REPORT")

if [ -n "$FAILED_ARTIFACTS" ]; then
    echo "❌ Some artifacts failed validation:"
    echo "$FAILED_ARTIFACTS" | while read -r artifact; do
        echo "  - $artifact"
        jq -r ".artifacts[] | select(.artifact_id == \"$artifact\") | .issues[]" "$VALIDATION_REPORT" | while read -r issue; do
            echo "    - $issue"
        done
    done
    exit 1
fi

# List all artifacts
jq -r '.artifacts[] | "  ✅ \(.artifact_id) - \(.status)"' "$VALIDATION_REPORT"

# Check proof-run compliance
echo ""
echo "Proof-Run Checks:"

NO_EXTERNAL_SENDS=$(jq -r '.proof_run_checks.no_external_sends' "$VALIDATION_REPORT")
echo "  No external sends: $NO_EXTERNAL_SENDS"

if [ "$NO_EXTERNAL_SENDS" != "true" ]; then
    echo "❌ External sends detected in proof-run mode"
    jq -r '.proof_run_checks.external_send_attempts[]' "$VALIDATION_REPORT"
    exit 1
fi

NO_EGRESS=$(jq -r '.proof_run_checks.no_unexpected_egress' "$VALIDATION_REPORT")
echo "  No unexpected egress: $NO_EGRESS"

if [ "$NO_EGRESS" != "true" ]; then
    echo "❌ Unexpected network egress detected"
    jq -r '.proof_run_checks.egress_violations[] | "  - \(.url): \(.reason)"' "$VALIDATION_REPORT"
    exit 1
fi

# Check for placeholders
echo ""
echo "Content Quality Checks:"

PLACEHOLDERS_FOUND=$(jq '[.artifacts[].section_validations[].placeholder_scan.has_placeholders] | any' "$VALIDATION_REPORT")
echo "  Placeholders found: $PLACEHOLDERS_FOUND"

if [ "$PLACEHOLDERS_FOUND" == "true" ]; then
    echo "❌ Placeholders detected in outputs"
    jq -r '.artifacts[] | .section_validations[] | select(.placeholder_scan.has_placeholders == true) | "  - \(.section_id): \(.placeholder_scan.placeholders_found | join(", "))"' "$VALIDATION_REPORT"
    exit 1
fi

FORBIDDEN_PHRASES_FOUND=$(jq '[.artifacts[].section_validations[].forbidden_phrase_scan.has_forbidden_phrases] | any' "$VALIDATION_REPORT")
echo "  Forbidden phrases found: $FORBIDDEN_PHRASES_FOUND"

if [ "$FORBIDDEN_PHRASES_FOUND" == "true" ]; then
    echo "❌ Forbidden phrases detected in outputs"
    jq -r '.artifacts[] | .section_validations[] | select(.forbidden_phrase_scan.has_forbidden_phrases == true) | "  - \(.section_id): \(.forbidden_phrase_scan.phrases_found | join(", "))"' "$VALIDATION_REPORT"
    exit 1
fi

# Check word counts
WORD_COUNT_ISSUES=$(jq '[.artifacts[].section_validations[] | select(.word_count_valid == false)] | length' "$VALIDATION_REPORT")
echo "  Word count issues: $WORD_COUNT_ISSUES"

if [ "$WORD_COUNT_ISSUES" != "0" ]; then
    echo "❌ Word count validation failed"
    jq -r '.artifacts[] | .section_validations[] | select(.word_count_valid == false) | "  - \(.section_id): \(.word_count) words (expected minimum in contract)"' "$VALIDATION_REPORT"
    exit 1
fi

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ VALIDATION: GREEN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "All checks passed:"
echo "  ✅ Global status is PASS"
echo "  ✅ All artifacts validated successfully"
echo "  ✅ No placeholders in outputs"
echo "  ✅ No forbidden phrases in outputs"
echo "  ✅ Word counts meet requirements"
echo "  ✅ No external sends in proof-run"
echo "  ✅ No unexpected network egress"
echo ""
echo "Safe to deliver client-facing outputs ✨"
echo ""

exit 0
