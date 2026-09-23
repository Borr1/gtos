#!/bin/sh
# Session LP -- build each window's diagnostic pool the moment its arm lands.
#
# The arms are hours long and finish at unpredictable times; a human (or agent)
# polling for them is the slowest part of the pipeline and the part most likely
# to drop one. This watches for each `*_RECEIPT.json`, waits for the route's
# ledgers to be gzipped by `lp_run_arm.sh` (which compresses only AFTER the
# receipt exists, so gzip presence is a completion signal and not a race), then
# projects the pool.
#
# june/august/september are stamped READ-RESTRICTED: built, unspent, held out.
# Building a pool is not reading it -- the artifact is an input, and its first
# economic read is a look that must be declared before it happens.

set -u
ROOT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803
BASE="$ROOT/docs/audits/fable5-vision-audit-20260725/phase19/receipts/pools"
A="$BASE/arm_receipts"
ROUTES="$ROOT/research/operations/final_moonshot_ultimate_system_denominator_to_deployment_execution_2026_06_20/attempt_5_typed_sparse"
LOG=/tmp/lp_supervise.log

# prefix|window_id|start|end|digest|restricted
SPECS="LP_JUN_2025_S0R0|june_2025|2025-06-03|2025-06-30|b2de9cb0e396beffc06bdb18e50d3b168f9848d1f48996d0eab84891da66ab2e|1
LP_AUG_2025_S0R0|august_2025|2025-08-01|2025-08-30|e604c43af82ed4625d56d0c45e618d69ed6db46d0fb1a855930bc57b65aebe3f|1
LP_SEP_2025_S0R0|september_2025|2025-09-01|2025-09-30|3df3c931dcdec9d29589cc079ac89db433965c7141f245cd6148669cd875ab03|1
LP_OCT_2025_S0R0|october_2025|2025-10-01|2025-10-31|b36eb41c0d382ad9e9df5d51502d45a569b719fac591737a5a6f73a23ec32178|0
LP_NOV_2025_S0R0|november_2025|2025-11-01|2025-11-29|b51195fed36a96ef28d5ace9da8dcc14d4be646dc01344febbe12f10f874bc62|0
LP_DEC_2025_S0R0|december_2025|2025-12-01|2025-12-31|b63e8d9115ff8c01288ed46bdd4bd3693ad1c31b8aff4e8eea2e9d620d9696b1|0"

mkdir -p "$BASE"
cd "$ROOT" || exit 1

i=0
while [ $i -lt 6000 ]; do
  pending=0
  echo "$SPECS" | while IFS='|' read -r prefix window start end digest restricted; do
    [ -n "$prefix" ] || continue
    out="$BASE/${window}_S0R0_POOL_V1.json"
    pool="$BASE/LP_${window}_S0R0_POOL_V1.jsonl.gz"
    [ -f "$out" ] && continue
    rcpt="$A/${prefix}_RECEIPT.json"
    ledger="$ROUTES/$prefix/${prefix}_MISSED_OPPORTUNITY_LEDGER.jsonl.gz"
    [ -f "$rcpt" ] || continue
    [ -f "$ledger" ] || continue
    echo "=== $(date -u +%H:%M:%S) building pool for $window" >> "$LOG"
    if [ "$restricted" = "1" ]; then
      RR=--read-restricted
    else
      RR=
    fi
    python3 "$BASE/lp_pool.py" --prefix "$prefix" --window-id "$window" \
      --capture "$start" "$end" --source-plan-digest "$digest" \
      --compact "$pool" --out "$out" $RR >> "$LOG" 2>&1
    echo "    exit=$? for $window" >> "$LOG"
  done
  n=$(ls "$BASE"/*_S0R0_POOL_V1.json 2>/dev/null | wc -l | tr -d ' ')
  [ "$n" -ge 6 ] && break
  i=$((i+1)); sleep 20
done
echo "=== $(date -u +%H:%M:%S) SUPERVISOR COMPLETE, $n pools" >> "$LOG"
