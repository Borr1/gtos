#!/usr/bin/env bash
# GTOS Live Monitor — persistent poll loop.
# Wakes at every M15 boundary +30s, runs scripts/_live_monitor_iter.py, prints summary line.
# Exits when pipeline_state/stop_live_monitor.flag exists.

set -u

ROOT="/c/Users/MSI/Documents/ai-trading-agent"
STOP_FLAG="$ROOT/pipeline_state/stop_live_monitor.flag"

cd "$ROOT" || exit 1

while true; do
    # Stop flag check
    if [ -f "$STOP_FLAG" ]; then
        echo "STOP_FLAG_OBSERVED at $(date -u +%Y-%m-%dT%H:%M:%SZ) — exiting"
        python "$ROOT/scripts/_live_monitor_iter.py" 2>&1
        break
    fi

    # Compute sleep to next M15 boundary +30s
    SLEEP_S=$(python -c "
from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc)
next_min = ((now.minute // 15) + 1) * 15
target = now.replace(minute=0, second=30, microsecond=0) + timedelta(minutes=next_min)
print(int((target - now).total_seconds()))
")

    if [ "$SLEEP_S" -gt 0 ]; then
        sleep "$SLEEP_S"
    fi

    # Run iteration; tail prints the summary line
    OUT=$(python "$ROOT/scripts/_live_monitor_iter.py" 2>&1 | tail -1)
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | $OUT"
done
