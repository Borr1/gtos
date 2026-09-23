#!/bin/sh
# Serial driver: build the remaining virgin windows, most-recent first, with a
# hard disk floor. Session LM-MAT.
#
# The floor is checked BEFORE each window rather than after, and against a
# projected cost rather than the current free figure, because the failure mode
# worth avoiding is a window that dies half-built: a partial window is
# NOT_EVALUABLE and has to be deleted, so three complete windows beat seven
# half-built ones. Projected cost is measured, not guessed -- ~3.8 GB for a
# tick-bearing month (2.5 tick + 0.05 M1 + 1.2 pack) and ~1.3 GB for one the
# captured tick archive does not reach.
#
# Usage: build_all.sh <window_id> [<window_id> ...]

set -u

OUT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/materialization
LOG="$OUT/build_log.txt"
FLOOR_GB=8

free_gb() { df -k / | tail -1 | awk '{printf "%d", $4/1048576}'; }

for W in "$@"; do
  case "$W" in
    october_2025|november_2025|december_2025) COST=4 ;;
    *) COST=2 ;;
  esac
  FREE=$(free_gb)
  NEED=$((FLOOR_GB + COST))
  if [ "$FREE" -lt "$NEED" ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DRIVER STOP before $W: free=${FREE}GB < floor+cost=${NEED}GB" | tee -a "$LOG"
    echo "DRIVER_STOPPED_ON_DISK $W" | tee -a "$LOG"
    exit 0
  fi
  echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DRIVER START $W (free=${FREE}GB, projected cost ${COST}GB)" | tee -a "$LOG"
  sh "$OUT/build_window.sh" "$W"
  st=$?
  if [ $st -ne 0 ]; then
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DRIVER: $W FAILED exit=$st -- stopping the run" | tee -a "$LOG"
    echo "DRIVER_STOPPED_ON_FAILURE $W exit=$st" | tee -a "$LOG"
    exit $st
  fi
done
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) DRIVER COMPLETE: $*" | tee -a "$LOG"
echo "DRIVER_ALL_COMPLETE" | tee -a "$LOG"
