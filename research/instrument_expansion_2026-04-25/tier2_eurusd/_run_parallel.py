"""Launch 12 parallel EURUSD slices for Tier 2 instrument expansion validation.

Slices are sized so each consumes ~$2-3 in API spend (target $25-30 total).
Slices run in parallel on Anthropic tier-4 (no per-account ceiling at this
volume; Sonnet 4.6 effort=max can be saturated).

Usage:
    python research/instrument_expansion_2026-04-25/tier2_eurusd/_run_parallel.py
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SLICE_BUDGET = 3.0  # USD per slice
SYMBOL = "EURUSD"

SLICES = [
    ("s01", "2026-01-02", "2026-01-09"),
    ("s02", "2026-01-12", "2026-01-16"),
    ("s03", "2026-01-19", "2026-01-23"),
    ("s04", "2026-01-26", "2026-01-30"),
    ("s05", "2026-02-02", "2026-02-06"),
    ("s06", "2026-02-09", "2026-02-13"),
    ("s07", "2026-02-16", "2026-02-20"),
    ("s08", "2026-02-23", "2026-02-27"),
    ("s09", "2026-03-02", "2026-03-13"),
    ("s10", "2026-03-16", "2026-03-27"),
    ("s11", "2026-03-30", "2026-04-03"),
    ("s12", "2026-04-06", "2026-04-13"),
]

OUTDIR_BASE = PROJECT_ROOT / "research" / "instrument_expansion_2026-04-25" / "tier2_eurusd"
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
            "--detector-version", "v2",  # v2 is now production, but be explicit
            "--slice-tag", f"eurusd_{slice_id}",
        ]
        env = dict(os.environ)
        # Make sure ANTHROPIC_API_KEY is in environment (the parent shell
        # pre-loaded .env via `set -a && source .env && set +a`).
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
