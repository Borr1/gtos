#!/bin/bash
# Launch the three mini-backtests in parallel against xauusd_s3.
#
# Each runs in its own Python process so the monkey-patching does not
# collide. Outputs go under mini_backtest_{variant}_{slice}/all_results.json.
#
# Expected total cost: ~$5 ($1.5-2 per variant × 3 variants)
# Expected wall time: ~12-15 min (270 candles → ~40-50 API calls per variant)

set -eu

cd /c/Users/MSI/Documents/ai-trading-agent/ && set -a && source .env && set +a
cd /c/Users/MSI/Documents/ai-trading-agent/.claude/worktrees/agent-a1db28f0ce9151186/

mkdir -p logs

SLICE=xauusd_s3
BUDGET=2.5

echo "Launching parallel mini-backtests on $SLICE (budget \$$BUDGET per variant)..."

python -u research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
    --variant v3_control --slice $SLICE --budget $BUDGET \
    > logs/dp4_mb_v3.log 2>&1 &
PID_V3=$!
echo "v3_control PID=$PID_V3"

python -u research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
    --variant lira --slice $SLICE --budget $BUDGET \
    > logs/dp4_mb_lira.log 2>&1 &
PID_LIRA=$!
echo "lira PID=$PID_LIRA"

python -u research/v4_prompt_engineering/dp4_lira/run_mini_backtest.py \
    --variant nocot --slice $SLICE --budget $BUDGET \
    > logs/dp4_mb_nocot.log 2>&1 &
PID_NOCOT=$!
echo "nocot PID=$PID_NOCOT"

echo "All three launched. Waiting for completion..."
wait $PID_V3 $PID_LIRA $PID_NOCOT
echo "All three done."
