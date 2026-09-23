#!/usr/bin/env bash
# Canonical dry-run invocation for scripts/simulate_t7_parallel.py.
#
# Intended workflow:
#   1) Run THIS script first to verify the planned slice boundaries +
#      spawned commands look right. No subprocesses are spawned, no API
#      cost incurred.
#   2) Once happy with the plan, drop the --dry-run flag (or invoke
#      scripts/simulate_t7_parallel.py directly with the same args) to
#      execute. Each slice is one Anthropic-API-bound subprocess; budget
#      is per-slice so 12 slices x $30 = $360 max in the worst case
#      (typical run is ~$27 split across slices).
#
# .env loading: research scripts (and the inner simulator) rely on
# ANTHROPIC_API_KEY in the environment. Run `set -a && source .env && set +a`
# in the wrapping shell BEFORE invoking this script — that loads .env into
# the current shell, and every Popen child inherits it.
#
# To run live (drop --dry-run):
#   set -a && source .env && set +a
#   python scripts/simulate_t7_parallel.py --source csv \
#     --data-dir data/historical_2026 --start 2026-01-02 \
#     --end 2026-04-13 --symbol XAUUSD --slices 12 --budget 30 \
#     --output-dir research/t7_parallel_smoke
#
# Memory feedback_long_running_subprocess_pattern.md applies: for
# multi-hour runs, dispatch via Bash with run_in_background: true so the
# parent agent doesn't kill the children on early return.

set -euo pipefail

set -a && source .env && set +a
python scripts/simulate_t7_parallel.py \
  --source csv \
  --data-dir data/historical_2026 \
  --start 2026-01-02 \
  --end 2026-04-13 \
  --symbol XAUUSD \
  --slices 12 \
  --budget 30 \
  --output-dir research/t7_parallel_smoke \
  --dry-run
