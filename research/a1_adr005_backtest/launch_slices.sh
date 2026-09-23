#!/usr/bin/env bash
# ADR-005 A1 backtest — 12 parallel slices (XAUUSD x 8 + USDJPY x 4).
# Reuses session-38 F3 slice boundaries for apples-to-apples comparability.
set -e
: "${ANTHROPIC_API_KEY:?ANTHROPIC_API_KEY must be set}"

ROOT="research/a1_adr005_backtest/slices"
mkdir -p "$ROOT"

declare -a SLICES=(
  "xauusd_s1 XAUUSD    2026-01-02 2026-01-14 6"
  "xauusd_s2 XAUUSD    2026-01-15 2026-01-27 6"
  "xauusd_s3 XAUUSD    2026-01-28 2026-02-09 6"
  "xauusd_s4 XAUUSD    2026-02-10 2026-02-22 6"
  "xauusd_s5 XAUUSD    2026-02-23 2026-03-07 6"
  "xauusd_s6 XAUUSD    2026-03-08 2026-03-20 6"
  "xauusd_s7 XAUUSD    2026-03-21 2026-04-02 6"
  "xauusd_s8 XAUUSD    2026-04-03 2026-04-13 6"
  "usdjpy_s1 USDJPY    2026-01-02 2026-01-26 6"
  "usdjpy_s2 USDJPY    2026-01-27 2026-02-20 6"
  "usdjpy_s3 USDJPY    2026-02-21 2026-03-17 6"
  "usdjpy_s4 USDJPY    2026-03-18 2026-04-13 6"
)

for row in "${SLICES[@]}"; do
  read -r tag sym start end budget <<< "$row"
  outdir="$ROOT/$tag"
  mkdir -p "$outdir"
  logpath="$outdir/candidate_features_log.jsonl"
  stdout="$outdir/run.log"
  echo "Launching $tag: $sym $start..$end (budget \$${budget}) -> $logpath"
  python scripts/simulate_t7_live_period.py \
    --source csv \
    --data-dir data/historical_2026 \
    --symbol "$sym" \
    --start "$start" \
    --end "$end" \
    --budget "$budget" \
    --output-dir "$outdir" \
    --a1-backtest-log-path "$logpath" \
    --slice-tag "$tag" \
    > "$stdout" 2>&1 &
  echo "  PID=$!"
done

wait
echo "All slices complete."
