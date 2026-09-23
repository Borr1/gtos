"""Launch 12 parallel NAS100 slices for Tier 2 instrument expansion validation.

NAS100 is a Tier 2 (top-5 spread efficiency, 4.40% R-cost) US index. F3-style
12-parallel-slice backtest mirrors the XAGUSD agent's exact slicing for direct
comparability of compute, ranges, and aggregation methodology.

Slicing follows the XAGUSD pattern; ~$2-3 per slice, target ~$25-30 total.

KZ_WINDOWS for NAS100 was updated 2026-04-25 in scripts/simulate_t7_live_period.py
to mirror live deep-merged config: london 07:00-10:30 (XAUUSD base leak) +
ny 13:00-17:00 (NAS100 explicit override "Extended from 15:30 — 50.4% cont").

Usage (parent shell must have ANTHROPIC_API_KEY in env):
    set -a && source .env && set +a
    python research/instrument_expansion_2026-04-25/tier2_nas100/_run_parallel.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SLICE_BUDGET = 3.0  # USD per slice
SYMBOL = "NAS100"

# Mirrors XAGUSD slicing exactly (research/instrument_expansion_2026-04-25/tier2_xagusd/).
# Note s12 overlaps s8 (2026-03-12 to 2026-03-20). Kept identical for direct
# A-vs-A comparability across Tier 2 instruments.
SLICES = [
    ("s1",  "2026-01-02", "2026-01-10"),
    ("s2",  "2026-01-13", "2026-01-21"),
    ("s3",  "2026-01-22", "2026-01-30"),
    ("s4",  "2026-02-02", "2026-02-10"),
    ("s5",  "2026-02-11", "2026-02-19"),
    ("s6",  "2026-02-20", "2026-03-02"),
    ("s7",  "2026-03-03", "2026-03-11"),
    ("s8",  "2026-03-12", "2026-03-20"),
    ("s9",  "2026-03-23", "2026-03-31"),
    ("s10", "2026-04-01", "2026-04-08"),
    ("s11", "2026-04-09", "2026-04-13"),
    ("s12", "2026-03-16", "2026-03-23"),
]

OUTDIR_BASE = PROJECT_ROOT / "research" / "instrument_expansion_2026-04-25" / "tier2_nas100"
DATA_DIR = PROJECT_ROOT / "data" / "historical_2026"
SIM_SCRIPT = PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"


def main() -> None:
    procs = []
    for slice_id, start, end in SLICES:
        slice_dir = OUTDIR_BASE / slice_id
        slice_dir.mkdir(parents=True, exist_ok=True)
        log_path = OUTDIR_BASE / f"{slice_id}.log"
        cmd = [
            sys.executable, str(SIM_SCRIPT),
            "--source", "csv",
            "--symbol", SYMBOL,
            "--start", start,
            "--end", end,
            "--budget", f"{SLICE_BUDGET}",
            "--data-dir", str(DATA_DIR),
            "--output-dir", str(slice_dir),
            "--detector-version", "v2",  # v2 production active post-Sunday merge
            "--slice-tag", f"nas100_{slice_id}",
        ]
        env = dict(os.environ)
        with open(log_path, "w") as logfh:
            p = subprocess.Popen(cmd, stdout=logfh, stderr=subprocess.STDOUT, env=env)
        procs.append((slice_id, p, log_path))
        print(f"[launch] {slice_id} pid={p.pid} log={log_path.name}")

    # Wait
    failures = 0
    for slice_id, p, log_path in procs:
        rc = p.wait()
        status = "OK" if rc == 0 else f"FAIL rc={rc}"
        print(f"[done]   {slice_id} {status}")
        if rc != 0:
            failures += 1

    print(f"\nDONE. {len(procs) - failures}/{len(procs)} slices succeeded.")
    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
