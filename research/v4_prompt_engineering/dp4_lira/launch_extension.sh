#!/bin/bash
# DP4 extension — launch a single (variant, slice) mini-backtest with proper logging.
#
# Usage:
#   ./launch_extension.sh <variant> <slice>
#
# Examples:
#   ./launch_extension.sh v3_control xauusd_s7
#   ./launch_extension.sh lira usdjpy_s3
#   ./launch_extension.sh nocot usdjpy_s3
#
# Each invocation runs SEQUENTIALLY (foreground) so the caller can decide
# whether to background the whole script with run_in_background. This
# avoids the bash subshell-PID-vanish issue where chained `&` calls die.

set -eu

VARIANT="${1:?usage: $0 <variant> <slice>}"
SLICE="${2:?usage: $0 <variant> <slice>}"
BUDGET="${3:-2.5}"

PROJ=/c/Users/MSI/Documents/ai-trading-agent
WT=$PROJ/.claude/worktrees/agent-a1db28f0ce9151186
LOG=$WT/logs/dp4_mb_${VARIANT}_${SLICE}.log

# Load .env from project root.
cd "$PROJ" && set -a && source .env && set +a

cd "$WT"
mkdir -p logs

echo "Launching mini-backtest variant=$VARIANT slice=$SLICE budget=\$$BUDGET log=$LOG"

python -u research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
    --variant "$VARIANT" --slice "$SLICE" --budget "$BUDGET" \
    > "$LOG" 2>&1

echo "Done variant=$VARIANT slice=$SLICE  log=$LOG"
