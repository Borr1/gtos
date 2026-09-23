#!/bin/sh
# Assemble the LM-MAT deliverables from the build log and the registry.
# Metadata only; reads no pack shard and no economic field.
set -u
OUT=/Users/borr/GTOSActive/worktrees/fa2-integration-20260803/docs/audits/fable5-vision-audit-20260725/phase19/receipts/materialization
cd /Users/borr/GTOSActive/worktrees/fa2-integration-20260803 || exit 1

# 1. Disk trajectory, straight from the log's own `free=` stamps.
python3 - "$OUT/build_log.txt" "$OUT/DISK_TRAJECTORY.json" <<'PY'
import json, re, sys
src, dst = sys.argv[1], sys.argv[2]
rows = []
for line in open(src, encoding="utf-8"):
    m = re.match(r"^(\S+Z) \[(\w+)\] (.*?) free=([\d.]+)GB\s*$", line.strip())
    if m:
        rows.append({"utc": m.group(1), "window": m.group(2),
                     "event": m.group(3), "free_gb": float(m.group(4))})
    m2 = re.match(r"^(\S+Z) DRIVER (.*?)\(free=(\d+)GB.*$", line.strip())
    if m2:
        rows.append({"utc": m2.group(1), "window": "-",
                     "event": "DRIVER " + m2.group(2).strip(),
                     "free_gb": float(m2.group(3))})
head = [
    {"utc": "session-start", "window": "-",
     "event": "df at session start, before any recovery", "free_gb": 19.0},
    {"utc": "after-gzip", "window": "-",
     "event": "after gzipping 149 FA2 route jsonl ledgers (5.35GB -> 0.50GB)",
     "free_gb": 24.0},
]
json.dump({"schema": "gtos.lane.materialization.disk_trajectory.v1",
           "note": ("Free space on / in GB. The step from 24 to ~44 GB was NOT "
                    "this session: a concurrent estate process released space "
                    "while december_2025 was materializing. Recorded so the "
                    "recovery this session actually performed (+4.85 GB) is not "
                    "over-credited."),
           "rows": head + rows}, open(dst, "w"), indent=1)
print(f"disk trajectory rows: {len(head)+len(rows)}")
PY

# 2. Which windows completed, from the log's terminal lines.
BUILT=$(grep -oE "\[[a-z_0-9]+\] COMPLETE" "$OUT/build_log.txt" | sed -E 's/\[([a-z_0-9]+)\] COMPLETE/\1/' | awk '!seen[$0]++' | paste -sd, -)
echo "built windows: $BUILT"

# 3. Machine receipt.
nice -n 19 python3 "$OUT/summarize_windows.py" --windows "$BUILT" \
  --disk-trajectory "$OUT/DISK_TRAJECTORY.json" \
  --out "$OUT/LM_MAT_RESULT.json"

# 4. Final rule-2 fence.
nice -n 19 python3 "$OUT/verify_pre_existing.py" --label final
