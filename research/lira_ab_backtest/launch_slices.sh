#!/bin/bash
# LIRA A/B 12-slice backtest launcher.
#
# Spawns 12 parallel python processes — XAUUSD x8 (12-day windows) + USDJPY x4 (25-day windows).
# Each process invokes research/lira_ab_backtest/run_lira_slice.py with --detector-version v2.
# Slice boundaries match A2 v2-active backtest (research/a2_v2_active_backtest/launch.log).
#
# Usage (foreground; agent dispatches via run_in_background=true):
#   bash research/lira_ab_backtest/launch_slices.sh
#
# Logs: research/lira_ab_backtest/slices/<slice>/run.log
# Artifacts: research/lira_ab_backtest/slices/<slice>/all_results.json
#            research/lira_ab_backtest/slices/<slice>/<SYMBOL>_t7_simulation.json

set -u

PROJ="/c/Users/MSI/Documents/ai-trading-agent"
WT="/c/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-a685f35b3eddac6d4"
BUDGET=6
LAUNCH_LOG="$WT/research/lira_ab_backtest/launch.log"

# Load .env from project root.
cd "$PROJ" && set -a && source .env && set +a
cd "$WT"

# Slice definitions — symbol:slice_name:start:end
# XAUUSD x8 (12-day windows, 2026-01-02..2026-04-13)
# USDJPY x4 (25-day windows, 2026-01-02..2026-04-13)
# Mirrors research/a2_v2_active_backtest/launch.log exactly.
SLICES=(
    "XAUUSD:xauusd_s1:2026-01-02:2026-01-14"
    "XAUUSD:xauusd_s2:2026-01-15:2026-01-27"
    "XAUUSD:xauusd_s3:2026-01-28:2026-02-09"
    "XAUUSD:xauusd_s4:2026-02-10:2026-02-22"
    "XAUUSD:xauusd_s5:2026-02-23:2026-03-07"
    "XAUUSD:xauusd_s6:2026-03-08:2026-03-20"
    "XAUUSD:xauusd_s7:2026-03-21:2026-04-02"
    "XAUUSD:xauusd_s8:2026-04-03:2026-04-13"
    "USDJPY:usdjpy_s1:2026-01-02:2026-01-26"
    "USDJPY:usdjpy_s2:2026-01-27:2026-02-20"
    "USDJPY:usdjpy_s3:2026-02-21:2026-03-17"
    "USDJPY:usdjpy_s4:2026-03-18:2026-04-13"
)

> "$LAUNCH_LOG"
echo "LIRA A/B 12-slice launch — $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LAUNCH_LOG"
echo "Budget per slice: \$$BUDGET. Total budget: \$$((BUDGET * 12))" | tee -a "$LAUNCH_LOG"
echo "" | tee -a "$LAUNCH_LOG"

PIDS=()
for entry in "${SLICES[@]}"; do
    SYMBOL="${entry%%:*}"
    rest="${entry#*:}"
    SLICE_NAME="${rest%%:*}"
    rest="${rest#*:}"
    START="${rest%%:*}"
    END="${rest#*:}"

    OUT_DIR="$WT/research/lira_ab_backtest/slices/$SLICE_NAME"
    mkdir -p "$OUT_DIR"
    LOG="$OUT_DIR/run.log"

    echo "Launching $SLICE_NAME: $SYMBOL $START..$END (budget \$$BUDGET) -> $OUT_DIR" | tee -a "$LAUNCH_LOG"

    python -u research/lira_ab_backtest/run_lira_slice.py \
        --symbol "$SYMBOL" \
        --start "$START" \
        --end "$END" \
        --output-dir "$OUT_DIR" \
        --budget "$BUDGET" \
        > "$LOG" 2>&1 &
    PID=$!
    PIDS+=("$PID")
    echo "  PID=$PID" | tee -a "$LAUNCH_LOG"
done

echo "" | tee -a "$LAUNCH_LOG"
echo "All 12 slices launched. PIDs: ${PIDS[*]}" | tee -a "$LAUNCH_LOG"
echo "Waiting for completion..." | tee -a "$LAUNCH_LOG"

for PID in "${PIDS[@]}"; do
    wait "$PID"
    EC=$?
    echo "  PID $PID exited with code $EC" | tee -a "$LAUNCH_LOG"
done

echo "" | tee -a "$LAUNCH_LOG"
echo "All slices complete — $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$LAUNCH_LOG"
