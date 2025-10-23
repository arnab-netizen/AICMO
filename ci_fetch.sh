#!/usr/bin/env bash
set -euo pipefail

# ---------- Config ----------
REPO="${REPO:-arnab-netizen/AICMO}"     # override via env if you like
WORKFLOW="${WORKFLOW:-CI}"              # workflow name as shown in Actions UI
LIMIT="${LIMIT:-20}"
MAX_RETRIES="${MAX_RETRIES:-5}"
RETRY_SLEEP_SECS="${RETRY_SLEEP_SECS:-3}"
# ----------------------------

retry() {
  local n=0
  until "$@"; do
    exit_code=$?
    n=$((n+1))
    if [ "$n" -ge "$MAX_RETRIES" ]; then
      echo "Retry: giving up after $n attempts (last exit $exit_code)"
      return "$exit_code"
    fi
    echo "Retry: attempt $n failed (exit $exit_code). Sleeping ${RETRY_SLEEP_SECS}s then retrying..."
    sleep "$RETRY_SLEEP_SECS"
  done
}

echo "Repo: $REPO | Workflow: $WORKFLOW | Limit: $LIMIT"

echo "Listing recent runs…"
runs_json="$(gh run list \
  --repo "$REPO" \
  --workflow "$WORKFLOW" \
  --limit "$LIMIT" \
  --json databaseId,conclusion,status,headSha,url,name,createdAt,displayTitle \
)"

# Build a compact array of runs
runs_compact="$(echo "$runs_json" | jq -r '.[] | {id:.databaseId, status, conclusion, created:.createdAt, url, title:.displayTitle}' )"

pick_run() {
  # 1) latest successful
  sel_success=$(echo "$runs_json" | jq '[.[] | select(.conclusion=="success")] | max_by(.createdAt) // empty')
  if [ -n "${sel_success}" ] && [ "${sel_success}" != "null" ]; then
    echo "$sel_success"
    return 0
  fi

  # 2) else latest in_progress or queued
  sel_active=$(echo "$runs_json" | jq '[.[] | select(.status=="in_progress" or .status=="queued")] | max_by(.createdAt) // empty')
  if [ -n "${sel_active}" ] && [ "${sel_active}" != "null" ]; then
    echo "$sel_active"
    return 0
  fi

  # 3) else just the most recent run overall
  sel_latest=$(echo "$runs_json" | jq 'max_by(.createdAt)')
  echo "$sel_latest"
}

picked="$(pick_run)"
if [ -z "$picked" ] || [ "$picked" = "null" ]; then
  echo "No runs found for workflow '$WORKFLOW' in $REPO"; exit 1
fi

RUN_ID="$(echo "$picked" | jq -r '.databaseId')"
RUN_STATUS="$(echo "$picked" | jq -r '.status')"
RUN_CONCL="$(echo "$picked" | jq -r '.conclusion // "none"')"
RUN_URL="$(echo "$picked" | jq -r '.url')"

echo "Selected run: $RUN_ID"
echo "  status: $RUN_STATUS"
echo "  conclusion: $RUN_CONCL"
echo "  url: $RUN_URL"

# If it’s not completed, wait for it
if [ "$RUN_STATUS" != "completed" ]; then
  echo "Run $RUN_ID is $RUN_STATUS — watching until it finishes…"
  gh run watch "$RUN_ID" --repo "$REPO"
fi

# Re-fetch the final status
final="$(gh run view "$RUN_ID" --repo "$REPO" --json status,conclusion,headSha,url,createdAt)"
FINAL_STATUS="$(echo "$final" | jq -r '.status')"
FINAL_CONCL="$(echo "$final" | jq -r '.conclusion // "none"')"
echo "Final status: $FINAL_STATUS | conclusion: $FINAL_CONCL"

# Prepare folders
ART_DIR="artifacts/$RUN_ID"
LOG_DIR="logs/$RUN_ID"
mkdir -p "$ART_DIR" "$LOG_DIR"

# -------- Download artifacts (best effort with retries) --------
echo "Checking artifacts for run $RUN_ID…"
arts="$(gh api "repos/$REPO/actions/runs/$RUN_ID/artifacts" --jq '.artifacts')"
count="$(echo "$arts" | jq 'length')"
if [ "$count" -gt 0 ]; then
  echo "Found $count artifact(s). Downloading to $ART_DIR/"
  # Try the simple gh run download first (it handles extraction)
  if ! retry gh run download "$RUN_ID" --repo "$REPO" --dir "$ART_DIR"; then
    echo "Fallback: downloading each artifact via API…"
    echo "$arts" | jq -r '.[] | @base64' | while read -r row; do
      _jq(){ echo "$row" | base64 --decode | jq -r "$1"; }
      A_ID="$(_jq '.id')"
      A_NAME="$(_jq '.name')"
      OUT_ZIP="$ART_DIR/${A_NAME}-${A_ID}.zip"
      echo "  -> $A_NAME ($A_ID)"
      retry gh api -H "Accept: application/zip" \
        -o "$OUT_ZIP" \
        "repos/$REPO/actions/artifacts/$A_ID/zip" || true
    done
  fi
else
  echo "No artifacts attached to run $RUN_ID."
fi

# -------- Download logs --------
echo "Saving combined run log…"
retry gh run view "$RUN_ID" --repo "$REPO" --log > "$LOG_DIR/combined.log" || true

echo "Fetching per-job logs…"
jobs="$(gh run view "$RUN_ID" --repo "$REPO" --json jobs --jq '.jobs')"
echo "$jobs" | jq -r '.[] | @base64' | while read -r row; do
  _jq(){ echo "$row" | base64 --decode | jq -r "$1"; }
  J_ID="$(_jq '.databaseId // .id')"
  J_NAME_RAW="$(_jq '.name')"
  # sanitize filename
  J_NAME="$(echo "$J_NAME_RAW" | tr ' /:' '___' | tr -cd '[:alnum:]_.-')"
  OUT_LOG_BASE="$LOG_DIR/job-${J_ID}-${J_NAME}"
  OUT_ZIP="$OUT_LOG_BASE.zip"
  OUT_LOG="$OUT_LOG_BASE.log"
  echo "  -> $J_NAME ($J_ID)"
  # Try to download the job logs as a zip via the API (requires Accept header)
  if retry gh api -H "Accept: application/zip" -o "$OUT_ZIP" "repos/$REPO/actions/jobs/$J_ID/logs"; then
    # Attempt to unzip into the logs dir; if unzip missing or fails, keep the zip
    if command -v unzip >/dev/null 2>&1; then
      unzip -o "$OUT_ZIP" -d "$LOG_DIR" >/dev/null 2>&1 || echo "[warn] unzip failed for $OUT_ZIP"
      # If unzip created a single file, try to consolidate into OUT_LOG
      if [ -f "$LOG_DIR/logs.txt" ]; then
        mv -f "$LOG_DIR/logs.txt" "$OUT_LOG" || true
      fi
    else
      echo "[warn] unzip not available; saved job logs zip at $OUT_ZIP"
    fi
  else
    echo "[warn] could not download logs for job $J_ID; skipping"
  fi
done

echo
echo "Done."
echo "Artifacts dir: $ART_DIR"
echo "Logs dir:      $LOG_DIR"
