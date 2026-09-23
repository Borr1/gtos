#!/bin/sh
# Build ONE virgin lane window, end to end, outcome-blind. Session LM-MAT.
#
# Serial by construction and rule-2 fenced between every mutating step: the five
# pre-existing windows are re-verified after materialization, after the
# source-plan binding and after the pack build, so a corruption is caught at the
# step that caused it rather than at the end of a seven-window run.
#
# The March one-shot env var is set for the two steps that open the registry
# through `LaneInputRegistry`, and only because the registry now carries
# `march_window_registered: true`, which that class refuses outright without it
# (lane_rematerialization.py:2251-2257). No March day is ever requested here:
# every window is 2025 calendar, so `authorize_window`'s blackout branch never
# fires and no registry/surface-map swap occurs -- provable from the receipts,
# whose `registry_id` and `surface_map_id` carry no `+march_one_shot:` suffix.
#
# Usage: build_window.sh <window_id>

set -u

ROOT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803
HOLD=/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1
REG="$HOLD/LANE_INPUT_REGISTRY.json"
PREREG_SHA=da6c72627f35179f5f43cf9c3eec20b402ba12ad60af9487ae161f76c2a13a50
OUT="$ROOT/docs/audits/fable5-vision-audit-20260725/phase19/receipts/materialization"
FENCE="$OUT/verify_pre_existing.py"
LOG="$OUT/build_log.txt"

W="${1:?usage: build_window.sh <window_id>}"
# 2 when this script is the only job; 1 when several windows run concurrently,
# so N parallel windows cost N cores rather than 2N. The swarm shares this box.
EW="${GTOS_LM_ENCODING_WORKERS:-2}"
cd "$ROOT" || exit 1
mkdir -p "$OUT/receipts"

free() { df -k / | tail -1 | awk '{printf "%.2f", $4/1048576}'; }
note() { echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) [$W] $1 free=$(free)GB" | tee -a "$LOG"; }

fence() {
  out=$(nice -n 19 python3 "$FENCE" --label "$W:$1" 2>&1)
  st=$?
  echo "$out" | tee -a "$LOG"
  if [ $st -ne 0 ]; then
    echo "RULE-2 FENCE FAILED after $1 -- STOPPING" | tee -a "$LOG"
    exit 9
  fi
}

note "START"
fence pre

note "step 1/3 materialize-window"
nice -n 19 env PYTHONDONTWRITEBYTECODE=1 python3 -m src.research_infra.lane_rematerialization \
  materialize-window --registry "$REG" --window "$W" \
  --out "$OUT/receipts/SOURCES_$W.json" >> "$LOG" 2>&1
st=$?
note "step 1 exit=$st"
[ $st -eq 0 ] || exit 1
fence materialize

note "step 2/3 bind-source-plan"
nice -n 19 env PYTHONDONTWRITEBYTECODE=1 GTOS_MARCH_ONE_SHOT_PREREG_SHA256="$PREREG_SHA" \
  python3 -m src.research_infra.lane_rematerialization \
  bind-source-plan --registry "$REG" --window "$W" \
  --out "$OUT/receipts/SOURCE_PLAN_$W.json" >> "$LOG" 2>&1
st=$?
note "step 2 exit=$st"
[ $st -eq 0 ] || exit 2
fence source-plan

note "step 3/3 build-packs"
nice -n 19 env PYTHONDONTWRITEBYTECODE=1 GTOS_MARCH_ONE_SHOT_PREREG_SHA256="$PREREG_SHA" \
  python3 -m src.research_infra.lane_rematerialization \
  build-packs --registry "$REG" --window "$W" --encoding-workers "$EW" \
  --out "$OUT/receipts/PACKS_$W.json" >> "$LOG" 2>&1
st=$?
note "step 3 exit=$st"
[ $st -eq 0 ] || exit 3
fence packs

note "COMPLETE"
