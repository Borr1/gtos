#!/bin/sh
# Session LP -- one r0 baseline lane arm on a 2025 window.
#
# The arm shape is copied verbatim from the March decode event's R0 row
# (run_march_decode_event.sh) so the pools these produce are comparable to the
# January and March pools without any argument reconciliation:
#
#   --arm S0R0 --purpose LANE_ITERATION --keep-outputs
#   --patches CUTS6 --repairs commission_broker_true_gated,swap_horizon_true
#
# Compression happens only AFTER the receipt exists, so a crash mid-gzip can
# never be mistaken for a completed arm.
#
# Usage: lp_run_arm.sh <WINDOW> <SOURCE_PLAN_DIGEST> <PREFIX> [EXTRA_ARGS...]

set -u

ROOT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803
REG=/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json
PREREG_SHA=da6c72627f35179f5f43cf9c3eec20b402ba12ad60af9487ae161f76c2a13a50
OUTDIR="$ROOT/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools/arm_receipts"
ROUTES="$ROOT/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"

CUTS6=authority_hash_content_memo,abc_concrete_types,gc_during_chunk,skip_post_hoc_ledger_recertification,ledger_scalar_projection,missed_pool_projection
REPAIRS=commission_broker_true_gated,swap_horizon_true

WINDOW="${1:?usage: lp_run_arm.sh <WINDOW> <DIGEST> <PREFIX> [EXTRA...]}"
DIGEST="${2:?missing digest}"
PREFIX="${3:?missing prefix}"
shift 3

mkdir -p "$OUTDIR"
LOG="$OUTDIR/${PREFIX}.log"
cd "$ROOT" || exit 1

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ)  START $PREFIX  window=$WINDOW" >> "$LOG"
START=$(date +%s)
env PYTHONDONTWRITEBYTECODE=1 GTOS_MARCH_ONE_SHOT_PREREG_SHA256="$PREREG_SHA" \
  python3 -m src.research_infra.train_engine.runner \
    --arm S0R0 --purpose LANE_ITERATION --keep-outputs \
    --window "$WINDOW" --session LP \
    --lane-input-registry "$REG" \
    --lane-source-plan-digest "$DIGEST" \
    --prefix "$PREFIX" --patches "$CUTS6" --repairs "$REPAIRS" \
    --note "LP 2025 pool baseline ($WINDOW)" \
    --out "$OUTDIR/${PREFIX}_RECEIPT.json" "$@" >> "$LOG" 2>&1
status=$?
END=$(date +%s)
echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ)  END $PREFIX exit=$status wall=$((END-START))s" >> "$LOG"

if [ -f "$OUTDIR/${PREFIX}_RECEIPT.json" ]; then
  echo "    RECEIPT_OK $PREFIX" >> "$LOG"
  find "$ROUTES/$PREFIX" "$ROUTES/${PREFIX}.semantic-diagnostic" \
    -name '*.jsonl' -type f -exec gzip -f {} + 2>/dev/null
  echo "    gzipped $PREFIX ledgers" >> "$LOG"
else
  echo "    NO RECEIPT for $PREFIX -- arm is NOT_EVALUABLE" >> "$LOG"
fi
echo "    free: $(df -h /Users/borr/GTOSActive | tail -1 | awk '{print $4}')" >> "$LOG"
exit $status
