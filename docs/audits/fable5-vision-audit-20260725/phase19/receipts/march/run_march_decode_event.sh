#!/bin/sh
# The March decode event -- MARCH_PREREG_V1 §3. Six arms, STRICTLY SERIAL, one event.
#
# Compositions are copied verbatim from the prereg's table and are not computed
# here: a script that derived them from a shorter description could drift from
# the declaration, and the declaration is the thing under test.
#
# Rules this script enforces mechanically, because they are the ones a tired
# operator breaks:
#   * serial only -- no backgrounding, no parallel arms (H3: the evidence
#     accumulation is 4-5 GB/arm and two arms measure ~1.1-1.3x net anyway);
#   * an arm that errors does NOT stop the event -- the prereg makes that arm
#     NOT_EVALUABLE and the remaining arms still run (§7);
#   * each route's *.jsonl is gzipped only AFTER its receipt is written, so a
#     crash mid-compression cannot be mistaken for a completed arm;
#   * no analysis runs here. §3: "No analysis of ANY arm until all six receipts
#     exist."
#
# Usage: run_march_decode_event.sh <MARCH_SOURCE_PLAN_DIGEST>

set -u

ROOT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803
REG=/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/LANE_INPUT_REGISTRY.json
PREREG_SHA=da6c72627f35179f5f43cf9c3eec20b402ba12ad60af9487ae161f76c2a13a50
OUTDIR="$ROOT/docs/audits/fable5-vision-audit-20260725/phase19/receipts/march/arm_receipts"
ROUTES="$ROOT/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"
LOG=/tmp/march_decode_event.log

DIGEST="${1:?usage: run_march_decode_event.sh <MARCH_SOURCE_PLAN_DIGEST>}"

CUTS6=authority_hash_content_memo,abc_concrete_types,gc_during_chunk,skip_post_hoc_ledger_recertification,ledger_scalar_projection,missed_pool_projection
SCHEMA3=decision_semantics_projection,condition_feature_propagation,hard_eligibility_observability
BELIEF5=belief_cost_single_charge,belief_hash_term_removal,belief_confidence_constant_retire,belief_ev_walked_contract,belief_fill_probability_deweight

mkdir -p "$OUTDIR"
cd "$ROOT" || exit 1

run_arm() {
  prefix="$1"; patches="$2"; repairs="$3"; note="$4"
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ)  START $prefix  ($note)" >> "$LOG"
  env PYTHONDONTWRITEBYTECODE=1 GTOS_MARCH_ONE_SHOT_PREREG_SHA256="$PREREG_SHA" \
    python3 -m src.research_infra.train_engine.runner \
      --arm S0R0 --purpose LANE_ITERATION --keep-outputs \
      --window march_2026 --session MARCH_EXEC \
      --lane-input-registry "$REG" \
      --lane-source-plan-digest "$DIGEST" \
      --prefix "$prefix" --patches "$patches" --repairs "$repairs" \
      --note "$note" --out "$OUTDIR/${prefix}_RECEIPT.json" >> "$LOG" 2>&1
  status=$?
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ)  END   $prefix exit=$status" >> "$LOG"
  # Compress only after the receipt exists. Ledgers stay readable via gzip.
  if [ -f "$OUTDIR/${prefix}_RECEIPT.json" ]; then
    find "$ROUTES/$prefix" "$ROUTES/${prefix}.semantic-diagnostic" \
      -name '*.jsonl' -type f -exec gzip -f {} + 2>/dev/null
    echo "    gzipped $prefix ledgers; free: $(df -h /Users/borr/GTOSActive | tail -1 | awk '{print $4}')" >> "$LOG"
  else
    echo "    NO RECEIPT for $prefix -- arm is NOT_EVALUABLE, event continues" >> "$LOG"
  fi
}

run_arm FA2_M_R0      "$CUTS6"          "commission_broker_true_gated,swap_horizon_true" "March R0 baseline (CJ recipe, frozen costs)"
run_arm FA2_M_ARM_I   "$CUTS6"          "spread_input_truth,commission_broker_true_gated,swap_horizon_true,cost_ruler_harmonize" "March arm (i) R-COST-TRUTH"
run_arm FA2_M_ARM_II  "$CUTS6,$SCHEMA3" "spread_input_truth,commission_broker_true_gated,swap_horizon_true,cost_ruler_harmonize,$BELIEF5" "March arm (ii) + R-BELIEF + R-SCHEMA"
run_arm FA2_M_ARM_III "$CUTS6,$SCHEMA3" "spread_input_truth,commission_broker_true,swap_horizon_true,$BELIEF5,cost_ceiling_0p05" "March arm (iii) + declared 0.05 ceiling"
run_arm FA2_M_ARM_IV  "$CUTS6"          "commission_broker_true_gated,swap_horizon_true,spread_input_truth_inert_control,cost_ruler_inert_control,belief_cost_inert_control,belief_hash_inert_control,belief_confidence_inert_control,belief_ev_walked_inert_control,belief_fill_probability_inert_control,candidate_breaker_inert_control" "March arm (iv) inert controls"
run_arm FA2_M_ARM_V   "$CUTS6,$SCHEMA3" "spread_input_truth,commission_broker_true,swap_horizon_true,$BELIEF5,cost_ceiling_0p05,candidate_breaker_transform" "March arm (v) the edge in"

echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ)  EVENT COMPLETE" >> "$LOG"
ls -la "$OUTDIR" >> "$LOG"
