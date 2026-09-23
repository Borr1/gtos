"""Tier 2 backtest orchestrator — survives main-thread bash dispatch.

Runs 5 instruments x 6 slices = 30 parallel simulate_t7_live_period.py
sub-processes with a concurrency cap. Each slice writes to its own
output dir. Tagged so ADR-005 shadow rows attribute correctly.

Run via main thread: `python scripts/run_tier2_backtests.py`
"""
from __future__ import annotations

import concurrent.futures
import os
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SIMULATE = REPO_ROOT / "scripts" / "simulate_t7_live_period.py"
DATA_DIR = REPO_ROOT / "data" / "historical_2026"
OUT_BASE = REPO_ROOT / "research" / "instrument_expansion_2026-04-25"

INSTRUMENTS = ["XAGUSD", "NAS100", "GER40", "UK100", "EURUSD"]

# 7 slices covering Jan 2 - Apr 24, 2026 (full available data window)
# NAS100 data ends Apr 17; sim handles missing-end-data gracefully.
SLICES = [
    ("s1", "2026-01-02", "2026-01-15"),
    ("s2", "2026-01-16", "2026-01-31"),
    ("s3", "2026-02-01", "2026-02-15"),
    ("s4", "2026-02-16", "2026-03-02"),
    ("s5", "2026-03-03", "2026-03-22"),
    ("s6", "2026-03-23", "2026-04-13"),
    ("s7", "2026-04-14", "2026-04-24"),
]

PER_SLICE_BUDGET = 4.0  # USD; 7 slices x $4 = $28 per instrument; 5 instruments = $140
MAX_CONCURRENT = 12  # cap on simultaneous sims (Tier 4 should handle, F3 used 12)


def run_slice(symbol: str, slice_id: str, start: str, end: str) -> dict:
    """Run a single sim slice, capture stdout/stderr to logfile."""
    out_dir = OUT_BASE / f"tier2_{symbol.lower()}" / slice_id
    out_dir.mkdir(parents=True, exist_ok=True)
    log_path = OUT_BASE / f"tier2_{symbol.lower()}" / f"{slice_id}.log"
    slice_tag = f"{symbol.lower()}_{slice_id}"

    cmd = [
        sys.executable,
        str(SIMULATE),
        "--source", "csv",
        "--data-dir", str(DATA_DIR),
        "--start", start,
        "--end", end,
        "--symbol", symbol,
        "--budget", str(PER_SLICE_BUDGET),
        "--output-dir", str(out_dir),
        "--slice-tag", slice_tag,
    ]

    started = time.time()
    try:
        with log_path.open("w", encoding="utf-8") as logfile:
            proc = subprocess.run(
                cmd,
                stdout=logfile,
                stderr=subprocess.STDOUT,
                timeout=5400,  # 90 min hard cap per slice
                cwd=str(REPO_ROOT),
                env={**os.environ},
            )
        return {
            "symbol": symbol,
            "slice": slice_id,
            "returncode": proc.returncode,
            "wall_seconds": round(time.time() - started, 1),
            "log": str(log_path),
        }
    except subprocess.TimeoutExpired:
        return {
            "symbol": symbol,
            "slice": slice_id,
            "returncode": -1,
            "wall_seconds": round(time.time() - started, 1),
            "log": str(log_path),
            "error": "timeout",
        }
    except Exception as e:
        return {
            "symbol": symbol,
            "slice": slice_id,
            "returncode": -2,
            "wall_seconds": round(time.time() - started, 1),
            "log": str(log_path),
            "error": str(e),
        }


def main():
    jobs = [
        (sym, sid, start, end)
        for sym in INSTRUMENTS
        for sid, start, end in SLICES
    ]
    print(f"[orchestrator] launching {len(jobs)} slices, max_concurrent={MAX_CONCURRENT}")
    print(f"[orchestrator] est. cost {len(jobs) * PER_SLICE_BUDGET:.0f} USD")
    print(f"[orchestrator] start time {time.strftime('%Y-%m-%d %H:%M:%S')}")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as ex:
        futs = {
            ex.submit(run_slice, sym, sid, start, end): (sym, sid)
            for sym, sid, start, end in jobs
        }
        for fut in concurrent.futures.as_completed(futs):
            sym, sid = futs[fut]
            try:
                r = fut.result()
            except Exception as e:
                r = {"symbol": sym, "slice": sid, "returncode": -3, "error": str(e)}
            print(f"[orchestrator] done {r['symbol']}/{r['slice']} rc={r.get('returncode')} wall={r.get('wall_seconds', '?')}s")
            results.append(r)

    print(f"\n[orchestrator] all done. summary:")
    by_sym = {}
    for r in results:
        by_sym.setdefault(r["symbol"], []).append(r)
    for sym, slices in by_sym.items():
        ok = sum(1 for s in slices if s.get("returncode") == 0)
        print(f"  {sym}: {ok}/{len(slices)} slices succeeded")

    # Write summary file
    import json
    summary_path = OUT_BASE / "tier2_orchestrator_summary.json"
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "n_jobs": len(jobs),
            "results": results,
        }, f, indent=2)
    print(f"[orchestrator] summary -> {summary_path}")


if __name__ == "__main__":
    main()
