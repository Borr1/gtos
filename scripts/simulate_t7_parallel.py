#!/usr/bin/env python3
"""Parallel wrapper around scripts/simulate_t7_live_period.py.

Splits a [start, end] date range into N contiguous slices and runs the
existing single-process T7 simulator (`simulate_t7_live_period.py`) once
per slice as an isolated subprocess. Each slice writes its own
`all_results.json` + per-symbol JSON into a slice-specific output
directory, so a per-slice failure does NOT corrupt sibling slices.
Slices that already have a complete `all_results.json` can be skipped
via `--resume`.

Why this exists
---------------
The single-process T7 simulator takes 30-60 min for a 4-month XAUUSD
window because it serialises one Anthropic API call per kill-zone
candle. The CEO is on Anthropic tier 4 (rate limits comfortably above
12-16 concurrent inferences for `effort=max`), so splitting the window
into 8-16 weekly slices and running them in parallel cuts wall clock
from 30-60 min to <10 min with no change to per-slice statistics.

Memory `feedback_parallelize_aggressively_tier4.md`: target 8-16
concurrent slices, NOT 2-4. Default `--slices 12` is the canonical
choice for the 4-month window (Jan 2 - Apr 13 2026).

Memory `feedback_long_running_subprocess_pattern.md`: agent threads
kill their Python children on return. For multi-hour runs the harness
that wraps this script (the CEO will run it via Bash with
`run_in_background: true`) keeps the parent alive long enough for
all subprocesses to finish. This script supports being run that way
— it has no interactive prompts, deterministic exit codes, and
structured stdout (one JSON-ish progress line per state change).

Memory `project_research_scripts_missing_dotenv.md`: research scripts
do NOT auto-load `.env`. Each subprocess inherits the parent's env, so
sourcing once in the wrapping shell is enough. The helper at
`scripts/research/t7_parallel_dryrun.sh` shows the canonical pattern:

    set -a && source .env && set +a
    python scripts/simulate_t7_parallel.py --source csv \\
      --data-dir data/historical_2026 --start 2026-01-02 \\
      --end 2026-04-13 --symbol XAUUSD --slices 12 --budget 30 \\
      --output-dir research/t7_parallel_smoke

Output layout
-------------
For `--output-dir <DIR>` and N slices:

    <DIR>/
      slice_001_2026-01-02_2026-01-08/
        all_results.json           # written by simulate_t7_live_period.py
        XAUUSD_t7_simulation.json  # per-symbol output
        t7_live_simulation_report.md
        run.log                    # captured stdout+stderr
      slice_002_2026-01-09_2026-01-15/
        ...
      t7_parallel_<SYMBOL>_<START>_<END>.json   # consolidated, deterministic

The consolidated file always contains `failed_slices: [...]` (empty
on a clean run) so downstream consumers can detect partial runs
without re-checking the filesystem.

Out of scope
------------
- LLM API calls (the inner simulator does that).
- Modifying simulate_t7_live_period.py (additive only).
- Per-slice budget rebalancing — each slice gets `--budget` as-is.

Exit codes
----------
0 — every slice exited cleanly
1 — one or more slices failed (consolidated still written for the
    successful ones; `failed_slices` is populated)
2 — argument / planning error (no subprocesses spawned)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import shlex
import subprocess
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Anthropic tier-4 rate-limit conservative cap. The Anthropic API tier-4
# input-token bucket comfortably accommodates 16 concurrent Sonnet 4.6
# `effort=max` inferences per second (each call ≈ 25k input tokens, tier-4
# input is 4M tokens/min ⇒ headroom even at 16 concurrent for a 1 req/s
# inner cadence). We also bound by os.cpu_count() because each slice
# spawns its own Python interpreter (MSO build is CPU-bound). 16 is the
# safe ceiling on both axes; users who want more should bump it
# explicitly via --max-concurrent and accept rate-limit retry warnings.
MAX_CONCURRENT_HARD_CAP = 16


# ── Slicing ──────────────────────────────────────────────────────────────


@dataclass
class Slice:
    """One contiguous date range plus its on-disk identity."""

    index: int           # 1-based for human-readable directory names
    start: date          # inclusive
    end: date            # inclusive
    output_dir: Path     # per-slice subdirectory

    @property
    def tag(self) -> str:
        # Zero-padded so lexical sort matches numeric order through 999 slices.
        return f"slice_{self.index:03d}_{self.start.isoformat()}_{self.end.isoformat()}"

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "output_dir": str(self.output_dir),
            "tag": self.tag,
        }


def plan_slices(start: date, end: date, n_slices: int, base_output_dir: Path) -> list[Slice]:
    """Split ``[start, end]`` inclusive into ``n_slices`` contiguous date ranges.

    Properties guaranteed by this function:

    1. **No gaps and no overlaps** — slice K's `end + 1 day` equals slice
       K+1's `start` for every K. Combined coverage is exactly `[start, end]`.
    2. **Approximately equal length** — the longest slice is at most one
       day longer than the shortest.
    3. **Edge case (range smaller than slice count)** — if `(end - start) + 1 < n_slices`,
       we emit one slice per day instead of empty/zero-day slices.
    4. **Weekend hygiene (best effort)** — when the natural slice boundary
       would land on a Saturday or Sunday, we shift it forward to the next
       Monday IF that doesn't leave the slice empty AND it doesn't push
       the boundary past `end`. Production trading data has no weekend
       candles, so the shift is a no-op for outcomes; it just avoids
       weird stdout like `slice_005_2026-02-14_2026-02-21` (Sat → Sat).
       Boundary days that already fall on a weekday are left alone.

    Raises ValueError on malformed input (handled by main() with exit code 2).
    """
    if end < start:
        raise ValueError(f"end {end} is before start {start}")
    if n_slices < 1:
        raise ValueError(f"n_slices must be >= 1, got {n_slices}")

    total_days = (end - start).days + 1  # inclusive
    if total_days < n_slices:
        # One slice per day — never produce empty slices.
        n_slices = total_days

    # Distribute days as evenly as possible. Remainder goes to the first
    # `remainder` slices (each one gets +1 day). This keeps the longest
    # slice at most 1 day longer than the shortest.
    base_len = total_days // n_slices
    remainder = total_days % n_slices

    slices: list[Slice] = []
    cursor = start
    for i in range(n_slices):
        slice_len = base_len + (1 if i < remainder else 0)
        slice_start = cursor
        slice_end = cursor + timedelta(days=slice_len - 1)

        # Weekend-hygiene shift on the START of slice 2..N. Don't touch the
        # very first start (must equal the user's `start`) or the very last
        # end (must equal `end`). Snap the boundary forward to Monday only
        # if that keeps the slice non-empty.
        if i > 0 and slice_start.weekday() >= 5:
            shift_days = 7 - slice_start.weekday()  # 5→Sat needs 2, 6→Sun needs 1
            shifted = slice_start + timedelta(days=shift_days)
            if shifted <= slice_end:
                # Adjust both this slice's start and the previous slice's end.
                slices[-1] = Slice(
                    index=slices[-1].index,
                    start=slices[-1].start,
                    end=shifted - timedelta(days=1),
                    output_dir=slices[-1].output_dir,
                )
                slice_start = shifted

        s = Slice(
            index=i + 1,
            start=slice_start,
            end=slice_end,
            output_dir=base_output_dir,  # final path filled below
        )
        slices.append(s)
        cursor = slice_end + timedelta(days=1)

    # Now that boundaries are final, assign per-slice output_dir using each
    # slice's tag (which depends on slice_start/slice_end after weekend shifts).
    for s in slices:
        s.output_dir = base_output_dir / s.tag

    # Verification of contiguity invariants (cheap; runs once per planning call)
    assert slices[0].start == start, f"first slice start {slices[0].start} != {start}"
    assert slices[-1].end == end, f"last slice end {slices[-1].end} != {end}"
    for prev, nxt in zip(slices, slices[1:]):
        assert prev.end + timedelta(days=1) == nxt.start, \
            f"gap or overlap between slice {prev.index} (end={prev.end}) and slice {nxt.index} (start={nxt.start})"

    return slices


# ── Subprocess spawning ──────────────────────────────────────────────────


def build_command(slc: Slice, args: argparse.Namespace, inner_script: Path) -> list[str]:
    """Construct the argv for one slice's `simulate_t7_live_period.py` invocation.

    The inner simulator's CLI is treated as the source of truth — we pass
    through every flag we accept that has a 1:1 inner counterpart and
    REPLACE `--start` / `--end` with the slice's own boundaries.
    `--output-dir` becomes the per-slice subdirectory so each slice's
    `all_results.json` is independent.
    """
    cmd = [
        sys.executable,
        str(inner_script),
        "--source", args.source,
        "--start", slc.start.isoformat(),
        "--end", slc.end.isoformat(),
        "--symbol", args.symbol,
        "--budget", str(args.budget),
        "--output-dir", str(slc.output_dir),
    ]
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    if args.dry_run:
        # Pass through to the inner simulator so the per-slice run also
        # skips API calls. (The wrapper's --dry-run also blocks spawning
        # entirely; this branch is only for the rare case someone wants
        # the inner pipeline-funnel breakdown per slice.)
        cmd.append("--dry-run")
    return cmd


def slice_is_complete(slc: Slice) -> bool:
    """Return True if the slice has a non-empty `all_results.json`.

    Used by `--resume` to skip slices that already finished. We require
    the file to be parseable JSON with a `results` list — a partially
    written file (process killed mid-write) would fail the parse and be
    re-run, which is the correct conservative behaviour.
    """
    out = slc.output_dir / "all_results.json"
    if not out.exists():
        return False
    try:
        with open(out, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return False
    return isinstance(data, dict) and "results" in data


@dataclass
class SliceResult:
    """Outcome of running one slice subprocess."""

    slc: Slice
    returncode: int | None  # None = skipped via --resume, never spawned
    stdout_path: Path | None
    skipped: bool = False
    error: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.skipped or self.returncode == 0

    def to_dict(self) -> dict:
        d = self.slc.to_dict()
        d.update({
            "returncode": self.returncode,
            "stdout_path": str(self.stdout_path) if self.stdout_path else None,
            "skipped": self.skipped,
            "error": self.error,
            "succeeded": self.succeeded,
        })
        return d


def run_slices(
    slices: list[Slice],
    args: argparse.Namespace,
    inner_script: Path,
    max_concurrent: int,
) -> list[SliceResult]:
    """Spawn one subprocess per slice with a sliding window of `max_concurrent`.

    Each slice's stdout+stderr is captured to `slice/run.log`. The poll
    loop wakes every 0.5s; that's tight enough to keep wall-clock
    overhead negligible (slices take >30s each in practice) and loose
    enough that the CPU stays >99% idle while waiting. On per-slice
    failure we record the exit code + log path but do NOT abort siblings
    — partial runs are useful for diagnosis.
    """
    pending = list(slices)
    running: list[tuple[Slice, subprocess.Popen, Path, "object"]] = []
    results: list[SliceResult] = []

    while pending or running:
        # Fill the concurrency window.
        while pending and len(running) < max_concurrent:
            slc = pending.pop(0)

            if args.resume and slice_is_complete(slc):
                logger.info("[%s] resume: skipping (all_results.json already present)", slc.tag)
                results.append(SliceResult(slc=slc, returncode=None, stdout_path=None, skipped=True))
                continue

            slc.output_dir.mkdir(parents=True, exist_ok=True)
            log_path = slc.output_dir / "run.log"
            log_handle = open(log_path, "w", encoding="utf-8")
            cmd = build_command(slc, args, inner_script)
            logger.info("[%s] spawn: %s", slc.tag, " ".join(shlex.quote(c) for c in cmd))
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=log_handle,
                    stderr=subprocess.STDOUT,
                    cwd=str(_PROJECT_ROOT),
                )
            except OSError as e:
                log_handle.close()
                logger.error("[%s] spawn failed: %s", slc.tag, e)
                results.append(SliceResult(
                    slc=slc, returncode=-1, stdout_path=log_path,
                    error=f"spawn failed: {e}",
                ))
                continue
            running.append((slc, proc, log_path, log_handle))

        # Poll for completed children.
        time.sleep(0.5)
        still_running: list[tuple[Slice, subprocess.Popen, Path, "object"]] = []
        for slc, proc, log_path, log_handle in running:
            rc = proc.poll()
            if rc is None:
                still_running.append((slc, proc, log_path, log_handle))
                continue
            log_handle.close()
            if rc == 0:
                logger.info("[%s] complete (rc=0)", slc.tag)
            else:
                logger.warning("[%s] FAILED (rc=%s) — see %s", slc.tag, rc, log_path)
            results.append(SliceResult(slc=slc, returncode=rc, stdout_path=log_path))
        running = still_running

    return results


# ── Aggregation ──────────────────────────────────────────────────────────


def aggregate_results(
    slices: list[Slice],
    slice_results: list[SliceResult],
    symbol: str,
    overall_start: date,
    overall_end: date,
) -> dict:
    """Read each successful slice's `all_results.json` and merge deterministically.

    Determinism rules:
      1. Slices are processed in ascending order of `slice.index`
         (== chronological order of `slice.start` after weekend-shift).
      2. Within each slice, results are sorted by `(candle_time, symbol,
         kill_zone)` lex tuple so identical inputs always produce
         identical output regardless of inner-process ordering.
      3. `failed_slices` is sorted by index.

    Skipped slices (via `--resume`) are aggregated normally because their
    on-disk results are valid — the wrapper only skipped re-spawning the
    subprocess.
    """
    by_index = {sr.slc.index: sr for sr in slice_results}

    merged_results: list[dict] = []
    failed_slices: list[dict] = []
    total_cost = 0.0
    successful_slices = 0

    for slc in sorted(slices, key=lambda s: s.index):
        sr = by_index.get(slc.index)
        if sr is None:
            failed_slices.append({**slc.to_dict(), "error": "no result entry"})
            continue
        if not sr.succeeded:
            failed_slices.append({
                **slc.to_dict(),
                "returncode": sr.returncode,
                "stdout_path": str(sr.stdout_path) if sr.stdout_path else None,
                "error": sr.error or f"exit code {sr.returncode}",
            })
            continue

        per_slice_path = slc.output_dir / "all_results.json"
        if not per_slice_path.exists():
            failed_slices.append({
                **slc.to_dict(),
                "error": f"slice exited 0 but {per_slice_path} missing",
            })
            continue

        try:
            with open(per_slice_path, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            failed_slices.append({
                **slc.to_dict(),
                "error": f"could not parse {per_slice_path}: {e}",
            })
            continue

        slice_rows = payload.get("results") or []
        # Stable per-slice sort. ``candle_time`` is ISO-8601 so lexical
        # sort == chronological. (Symbol/kill_zone are tiebreakers for
        # the rare case of multiple instruments per slice — currently
        # the parallel runner pins a single --symbol, but the rule keeps
        # the function robust if that ever changes.)
        slice_rows = sorted(
            slice_rows,
            key=lambda r: (
                r.get("candle_time", ""),
                r.get("symbol", ""),
                r.get("kill_zone", ""),
            ),
        )
        merged_results.extend(slice_rows)
        total_cost += float(payload.get("total_cost") or 0.0)
        successful_slices += 1

    return {
        "symbol": symbol,
        "start": overall_start.isoformat(),
        "end": overall_end.isoformat(),
        "n_slices_planned": len(slices),
        "n_slices_succeeded": successful_slices,
        "n_slices_failed": len(failed_slices),
        "total_cost": round(total_cost, 4),
        "results": merged_results,
        "failed_slices": sorted(failed_slices, key=lambda f: f.get("index", 0)),
        "slice_manifest": [s.to_dict() for s in sorted(slices, key=lambda s: s.index)],
    }


def consolidated_filename(symbol: str, start: date, end: date) -> str:
    return f"t7_parallel_{symbol}_{start.isoformat()}_{end.isoformat()}.json"


# ── Dry-run plan ─────────────────────────────────────────────────────────


def emit_dry_run_plan(
    slices: list[Slice],
    args: argparse.Namespace,
    inner_script: Path,
    max_concurrent: int,
) -> None:
    """Print the planned slice boundaries + spawn commands without executing."""
    print("=" * 78)
    print("DRY RUN -- no subprocesses will be spawned")
    print("=" * 78)
    print(f"Inner script        : {inner_script}")
    print(f"Symbol              : {args.symbol}")
    print(f"Source              : {args.source}")
    print(f"Data dir            : {args.data_dir or '<inner default>'}")
    print(f"Overall window      : {args.start} -> {args.end}")
    print(f"Slices              : {len(slices)}")
    print(f"Max concurrent      : {max_concurrent}")
    print(f"Per-slice budget    : ${args.budget}")
    print(f"Output base         : {args.output_dir}")
    print(f"Resume mode         : {args.resume}")
    print("-" * 78)
    for slc in slices:
        marker = " [RESUMED]" if (args.resume and slice_is_complete(slc)) else ""
        print(f"[{slc.tag}]{marker}")
        cmd = build_command(slc, args, inner_script)
        print("  $ " + " ".join(shlex.quote(c) for c in cmd))
    print("-" * 78)
    print(f"Consolidated output : "
          f"{Path(args.output_dir) / consolidated_filename(args.symbol, slices[0].start, slices[-1].end)}")
    print("=" * 78)


# ── CLI ─────────────────────────────────────────────────────────────────


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Parallel wrapper around scripts/simulate_t7_live_period.py",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example (4-month XAUUSD, 12 weekly slices, dry-run):\n"
            "  python scripts/simulate_t7_parallel.py \\\n"
            "    --source csv --data-dir data/historical_2026 \\\n"
            "    --start 2026-01-02 --end 2026-04-13 --symbol XAUUSD \\\n"
            "    --slices 12 --budget 30 \\\n"
            "    --output-dir research/t7_parallel_smoke --dry-run"
        ),
    )
    parser.add_argument("--source", choices=["csv", "mt5"], default="csv",
                        help="Inner data source. csv requires --data-dir.")
    parser.add_argument("--data-dir", default=None,
                        help="CSV directory (passed through to the inner simulator).")
    parser.add_argument("--start", required=True,
                        help="Overall window start (YYYY-MM-DD, inclusive).")
    parser.add_argument("--end", required=True,
                        help="Overall window end (YYYY-MM-DD, inclusive).")
    parser.add_argument("--symbol", required=True,
                        help="Single instrument to simulate (e.g. XAUUSD).")
    parser.add_argument("--slices", type=int, default=12,
                        help="Number of contiguous date slices. Default 12 "
                             "(canonical for the 4-month window).")
    parser.add_argument("--budget", type=float, required=True,
                        help="Per-slice USD budget cap passed to the inner simulator.")
    parser.add_argument("--output-dir", required=True,
                        help="Base directory. Each slice gets its own subdirectory; "
                             "the consolidated JSON is written here.")
    parser.add_argument("--max-concurrent", type=int, default=None,
                        help="Concurrent subprocesses. Default = "
                             "min(slices, os.cpu_count(), 16). Hard cap = 16 "
                             "(Anthropic tier-4 rate-limit conservative).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the planned slice boundaries + spawn commands "
                             "and exit. No subprocesses are spawned.")
    parser.add_argument("--resume", action="store_true",
                        help="Skip slices whose all_results.json is already present "
                             "and parseable. Re-runs everything else.")
    return parser.parse_args(argv)


def resolve_max_concurrent(slices_count: int, requested: int | None) -> int:
    """Compute the effective `max_concurrent` and log the reasoning.

    Cap stack (smallest wins): MAX_CONCURRENT_HARD_CAP, os.cpu_count(),
    slice count, user-requested.
    """
    cpu = os.cpu_count() or 4
    default = min(slices_count, cpu, MAX_CONCURRENT_HARD_CAP)
    if requested is None:
        return default
    if requested < 1:
        raise ValueError(f"--max-concurrent must be >= 1 (got {requested})")
    if requested > MAX_CONCURRENT_HARD_CAP:
        logger.warning(
            "--max-concurrent=%d exceeds Anthropic tier-4 conservative cap %d. "
            "Capping to %d. Bump MAX_CONCURRENT_HARD_CAP in the script if you "
            "have explicit confirmation that the rate-limit headroom exists.",
            requested, MAX_CONCURRENT_HARD_CAP, MAX_CONCURRENT_HARD_CAP,
        )
        return MAX_CONCURRENT_HARD_CAP
    return min(requested, slices_count)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    inner_script = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"
    if not inner_script.exists():  # pragma: no cover - defensive
        logger.error("Inner script not found: %s", inner_script)
        return 2

    try:
        start = date.fromisoformat(args.start)
        end = date.fromisoformat(args.end)
    except ValueError as e:
        logger.error("Bad date: %s", e)
        return 2

    base_output_dir = Path(args.output_dir)
    base_output_dir.mkdir(parents=True, exist_ok=True)

    try:
        slices = plan_slices(start, end, args.slices, base_output_dir)
        max_concurrent = resolve_max_concurrent(len(slices), args.max_concurrent)
    except ValueError as e:
        logger.error("Planning error: %s", e)
        return 2

    logger.info(
        "Planned %d slices over %s..%s (max_concurrent=%d)",
        len(slices), start, end, max_concurrent,
    )

    if args.dry_run:
        emit_dry_run_plan(slices, args, inner_script, max_concurrent)
        return 0

    # Spawn + collect.
    slice_results = run_slices(slices, args, inner_script, max_concurrent)

    # Aggregate (always, even if some slices failed — partial output is useful).
    consolidated = aggregate_results(slices, slice_results, args.symbol, start, end)
    consolidated_path = base_output_dir / consolidated_filename(args.symbol, start, end)
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(consolidated, f, indent=2)
    logger.info("Consolidated output: %s", consolidated_path)
    logger.info(
        "Slices: %d planned, %d succeeded, %d failed",
        consolidated["n_slices_planned"],
        consolidated["n_slices_succeeded"],
        consolidated["n_slices_failed"],
    )

    # Exit code: 0 only if every slice succeeded.
    return 0 if consolidated["n_slices_failed"] == 0 else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
