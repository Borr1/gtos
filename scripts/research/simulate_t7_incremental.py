#!/usr/bin/env python3
"""Incremental T7 simulation driver (L55, Phase 1).

Re-evaluates only the candles whose evaluation inputs / prompt / config-relevant
subset changed since a prior run, then merges fresh + reused into a single
``all_results.json``-shaped output. Saves ~90% wall clock on iterative prompt
work compared to a full T7 rerun.

Workflow
--------
1. Build an :class:`IncrementalRunPlan` and emit the diff stats.
2. (Skipped under ``--dry-run``.) Slice the changed candles into runnable
   date ranges and invoke ``scripts/simulate_t7_live_period.py`` once per
   slice as an isolated subprocess. Each slice writes its own
   ``all_results.json`` under ``--output-dir/_slices/<tag>/``.
3. Merge prior + fresh into a consolidated output at
   ``--output-dir/incremental_<symbol>_<start>_<end>.json``.

Memory `feedback_long_running_subprocess_pattern.md`
----------------------------------------------------
The inner T7 simulator can take several minutes per slice (each slice still
runs the deterministic gates + the AI calls for its candles). When this CLI
is dispatched from a Claude Code agent that returns before the children
finish, the children get killed. The harness pattern: invoke this script
from the **main** Bash tool with ``run_in_background: true`` (the parent
shell stays alive for the lifetime of the children).

Memory `project_research_scripts_missing_dotenv.md`
---------------------------------------------------
The inner simulator does ``load_dotenv`` itself, but THIS wrapper does not
spawn a fresh shell — it spawns child processes that inherit the wrapper's
env. So if you run this from a session that has not loaded .env, do::

    set -a && source .env && set +a
    python scripts/research/simulate_t7_incremental.py ...

This script never calls the Anthropic API directly; only the inner T7
simulator does, and only for the slices we ask it to run.

Usage
-----
::

    python scripts/research/simulate_t7_incremental.py \\
      --prior-results research/t7_2026q1_v3/all_results.json \\
      --prompt src/prompts/primary_analyzer_prompt.py \\
      --config config/agent_config.yaml \\
      --start 2026-01-02 --end 2026-04-13 \\
      --symbol XAUUSD \\
      --output-dir research/t7_incremental_v4_test

    # Plan-only (no spawn)
    python scripts/research/simulate_t7_incremental.py \\
      --prior-results .../all_results.json \\
      --prompt .../primary_analyzer_prompt.py \\
      --config .../agent_config.yaml \\
      --start 2026-01-02 --end 2026-04-13 \\
      --symbol XAUUSD \\
      --output-dir /tmp/plan \\
      --dry-run

Exit codes
----------
0 — clean run (or dry-run plan emitted successfully).
1 — one or more inner simulator slices failed; partial output still merged.
2 — argument / planning error (no subprocess spawned).
"""

from __future__ import annotations

import argparse
import json
import logging
import shlex
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")
logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Local import.
from src.research_infra.incremental_engine import (  # noqa: E402
    CandleRef,
    IncrementalRunPlan,
    RunPlan,
    candle_key,
    merge_results,
)

INNER_SCRIPT = _PROJECT_ROOT / "scripts" / "simulate_t7_live_period.py"


# ════════════════════════════════════════════════════════════════════════════
# Slicing — group changed candles into runnable date ranges
# ════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class DateRangeSlice:
    """One contiguous date range that contains 1+ changed candles.

    The inner simulator's CLI takes ``--start`` / ``--end`` (inclusive). To
    avoid expanding a sparse set of changed candles into a contiguous big
    range (which would reprocess unchanged candles in between, defeating the
    point), we group candles by date FIRST and emit one slice per
    *contiguous run* of dates that have changed candles. Days with NO
    changed candles act as breakpoints.

    For example, changed candles on Jan-2, Jan-3, Jan-7, Jan-8 produce two
    slices: 2026-01-02..2026-01-03 and 2026-01-07..2026-01-08, NOT one
    spanning Jan-2..Jan-8.
    """

    start: date
    end: date
    candles: tuple[CandleRef, ...]

    @property
    def tag(self) -> str:
        return f"{self.start.isoformat()}_{self.end.isoformat()}"


def _candle_date(c: CandleRef) -> date:
    """Extract the date portion of ``c.candle_time`` (ISO-8601)."""
    s = c.candle_time
    # Tolerate trailing 'Z' (UTC) and offset suffixes.
    if not s:
        raise ValueError(f"CandleRef has empty candle_time: {c}")
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s).date()
    except ValueError as e:
        # Fall back to first 10 chars (YYYY-MM-DD).
        try:
            return date.fromisoformat(s[:10])
        except ValueError:
            raise ValueError(f"unparseable candle_time {c.candle_time!r}: {e}") from e


def slice_changed_candles(
    changed: list[CandleRef],
    max_gap_days: int = 0,
) -> list[DateRangeSlice]:
    """Group ``changed`` candles into contiguous date-range slices.

    Parameters
    ----------
    changed :
        List of candles needing re-evaluation. Order is irrelevant; the
        function sorts by date internally.
    max_gap_days :
        Number of consecutive empty days that are still considered "in the
        same slice". Default 0 (any gap breaks the slice). A value of 1
        would coalesce Jan-2 and Jan-4 into one slice, etc.

    Returns
    -------
    list[DateRangeSlice]
        Sorted by ``start``. Each slice's ``candles`` tuple is itself sorted
        by ``(candle_time, symbol, kill_zone)`` for deterministic downstream
        invocation.
    """
    if not changed:
        return []

    # Bucket candles by date.
    by_date: dict[date, list[CandleRef]] = defaultdict(list)
    for c in changed:
        by_date[_candle_date(c)].append(c)
    sorted_dates = sorted(by_date.keys())

    # Walk dates and break a slice whenever the gap exceeds max_gap_days.
    slices: list[DateRangeSlice] = []
    cur_start = sorted_dates[0]
    cur_end = sorted_dates[0]
    cur_candles: list[CandleRef] = list(by_date[cur_start])

    for d in sorted_dates[1:]:
        gap = (d - cur_end).days - 1
        if gap > max_gap_days:
            slices.append(_finalize_slice(cur_start, cur_end, cur_candles))
            cur_start = d
            cur_candles = list(by_date[d])
        else:
            cur_candles.extend(by_date[d])
        cur_end = d
    slices.append(_finalize_slice(cur_start, cur_end, cur_candles))
    return slices


def _finalize_slice(start: date, end: date, candles: list[CandleRef]) -> DateRangeSlice:
    sorted_candles = sorted(
        candles, key=lambda c: (c.candle_time, c.symbol, c.kill_zone)
    )
    return DateRangeSlice(start=start, end=end, candles=tuple(sorted_candles))


# ════════════════════════════════════════════════════════════════════════════
# Subprocess invocation (mockable)
# ════════════════════════════════════════════════════════════════════════════


def build_inner_command(
    slc: DateRangeSlice,
    args: argparse.Namespace,
    output_dir: Path,
) -> list[str]:
    """Construct the argv for one slice's inner-simulator call.

    The inner simulator accepts ``--start``, ``--end``, ``--symbol``,
    ``--output-dir``, ``--source``, ``--data-dir``, ``--budget``,
    ``--detector-version`` (and a few others we don't pass through).
    """
    cmd: list[str] = [
        sys.executable,
        str(INNER_SCRIPT),
        "--source", args.source,
        "--start", slc.start.isoformat(),
        "--end", slc.end.isoformat(),
        "--symbol", args.symbol,
        "--budget", str(args.budget),
        "--output-dir", str(output_dir),
    ]
    if args.data_dir:
        cmd.extend(["--data-dir", args.data_dir])
    if args.detector_version:
        cmd.extend(["--detector-version", args.detector_version])
    return cmd


def run_inner_simulator(
    slc: DateRangeSlice,
    args: argparse.Namespace,
    output_dir: Path,
    runner=None,
) -> tuple[int, Path]:
    """Run the inner simulator for one slice. Returns (returncode, log_path).

    ``runner`` defaults to ``subprocess.run`` and exists so tests can inject
    a fake. The function never raises on a non-zero exit; callers inspect
    the return code.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = output_dir / "run.log"
    cmd = build_inner_command(slc, args, output_dir)
    logger.info("[%s] spawn: %s", slc.tag, " ".join(shlex.quote(c) for c in cmd))

    runner = runner or subprocess.run
    try:
        with open(log_path, "w", encoding="utf-8") as log_handle:
            completed = runner(
                cmd,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                cwd=str(_PROJECT_ROOT),
            )
        rc = getattr(completed, "returncode", 0)
    except OSError as e:
        logger.error("[%s] spawn failed: %s", slc.tag, e)
        return -1, log_path
    return rc, log_path


# ════════════════════════════════════════════════════════════════════════════
# Plan-printing helpers
# ════════════════════════════════════════════════════════════════════════════


def format_plan_summary(plan: RunPlan) -> list[str]:
    """Return human-readable plan lines (one entry per line)."""
    lines = [
        f"Total candles in prior   : {plan.n_total_candles}",
        f"Unchanged (will skip)    : {plan.n_unchanged}",
        f"Changed (will re-evaluate): {plan.n_changed}",
        f"Reuse ratio              : {plan.reuse_ratio*100:.2f}%",
        f"Prompt changed           : {plan.prompt_changed}",
        f"Config-subset changed    : {plan.config_changed}",
        f"Prior prompt hash        : {plan.prior_prompt_hash}",
        f"Current prompt hash      : {plan.current_prompt_hash}",
        f"Prior config hash        : {plan.prior_config_hash}",
        f"Current config hash      : {plan.current_config_hash}",
    ]
    return lines


def print_plan(plan: RunPlan, slices: list[DateRangeSlice], args: argparse.Namespace) -> None:
    """Emit the full plan to stdout (used by --dry-run and the live path)."""
    print("=" * 78)
    print("INCREMENTAL T7 PLAN")
    print("=" * 78)
    for line in format_plan_summary(plan):
        print(line)
    print("-" * 78)
    print(f"Slices                   : {len(slices)}")
    for s in slices:
        print(f"  [{s.tag}] {len(s.candles)} candles")
    print("-" * 78)
    if args.dry_run:
        print("DRY RUN -- no subprocesses will be spawned. Done.")
    print("=" * 78)


# ════════════════════════════════════════════════════════════════════════════
# Fresh-result aggregation across slice outputs
# ════════════════════════════════════════════════════════════════════════════


def collect_fresh_records(
    slices: list[DateRangeSlice],
    base_output_dir: Path,
) -> tuple[dict[str, dict], list[str]]:
    """Walk per-slice ``all_results.json`` files and collect candle records.

    Returns
    -------
    fresh_map :
        ``candle_key -> record`` for every successful slice. Later slices
        overwrite earlier ones if the same key appears twice (defensive; should
        not happen given non-overlapping slices).
    errors :
        Per-slice diagnostic strings for missing/unparseable outputs.
    """
    fresh: dict[str, dict] = {}
    errors: list[str] = []
    slices_dir = base_output_dir / "_slices"
    for s in slices:
        out = slices_dir / s.tag / "all_results.json"
        if not out.exists():
            errors.append(f"missing slice output: {out}")
            continue
        try:
            with open(out, "r", encoding="utf-8") as f:
                payload = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            errors.append(f"unparseable {out}: {e}")
            continue
        for record in payload.get("results", []):
            if not isinstance(record, dict):
                continue
            fresh[candle_key(record)] = record
    return fresh, errors


# ════════════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════════════


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Incremental T7 simulator driver. Re-evaluates only candles whose "
            "inputs / prompt / config-relevant subset changed since a prior run."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Example (XAUUSD Q1, prompt-only iteration):\n"
            "  python scripts/research/simulate_t7_incremental.py \\\n"
            "    --prior-results research/t7_2026q1_v3/all_results.json \\\n"
            "    --prompt src/prompts/primary_analyzer_prompt.py \\\n"
            "    --config config/agent_config.yaml \\\n"
            "    --start 2026-01-02 --end 2026-04-13 \\\n"
            "    --symbol XAUUSD \\\n"
            "    --output-dir research/t7_incremental_v4_test\n"
        ),
    )
    parser.add_argument("--prior-results", required=True,
                        help="Path to a prior run's all_results.json")
    parser.add_argument("--prompt", required=True,
                        help="Path to the current PA prompt file")
    parser.add_argument("--config", required=True,
                        help="Path to agent_config.yaml (or a profile-merged copy)")
    parser.add_argument("--start", required=True, help="Window start (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="Window end (YYYY-MM-DD)")
    parser.add_argument("--symbol", required=True, help="Single instrument")
    parser.add_argument("--output-dir", required=True,
                        help="Output base directory. Per-slice outputs go under "
                             "<dir>/_slices/<tag>/, consolidated JSON at "
                             "<dir>/incremental_<symbol>_<start>_<end>.json")
    parser.add_argument("--source", choices=["csv", "mt5"], default="csv",
                        help="Inner data source. Default csv.")
    parser.add_argument("--data-dir", default=None,
                        help="CSV directory for the inner simulator")
    parser.add_argument("--budget", type=float, default=10.0,
                        help="Per-slice USD budget passed to the inner simulator")
    parser.add_argument("--detector-version", default=None,
                        help="Optional override of market_state.detector_version "
                             "(passed through to the inner simulator)")
    parser.add_argument("--max-gap-days", type=int, default=0,
                        help="Max consecutive empty days kept inside a single "
                             "slice. Default 0 (any gap breaks the slice).")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the plan + slice manifest and exit. No "
                             "subprocesses spawned.")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None, *, runner=None) -> int:
    args = parse_args(argv)

    try:
        window_start = date.fromisoformat(args.start)
        window_end = date.fromisoformat(args.end)
    except ValueError as e:
        logger.error("Bad date: %s", e)
        return 2
    if window_end < window_start:
        logger.error("--end %s precedes --start %s", window_end, window_start)
        return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: build plan.
    try:
        irp = IncrementalRunPlan(
            prior_results_path=args.prior_results,
            current_prompt_path=args.prompt,
            current_config_path=args.config,
        )
        plan = irp.compute_diff()
    except (FileNotFoundError, ValueError) as e:
        logger.error("Plan failed: %s", e)
        return 2

    slices = slice_changed_candles(plan.changed_candles, max_gap_days=args.max_gap_days)
    print_plan(plan, slices, args)

    # Persist the plan to disk so downstream consumers can audit.
    plan_path = output_dir / "incremental_plan.json"
    with open(plan_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "args": {
                    "prior_results": args.prior_results,
                    "prompt": args.prompt,
                    "config": args.config,
                    "start": args.start,
                    "end": args.end,
                    "symbol": args.symbol,
                    "source": args.source,
                    "data_dir": args.data_dir,
                    "budget": args.budget,
                    "detector_version": args.detector_version,
                    "max_gap_days": args.max_gap_days,
                    "dry_run": args.dry_run,
                },
                "plan": plan.to_dict(),
                "slices": [
                    {
                        "tag": s.tag,
                        "start": s.start.isoformat(),
                        "end": s.end.isoformat(),
                        "n_candles": len(s.candles),
                    }
                    for s in slices
                ],
            },
            f,
            indent=2,
        )
    logger.info("Plan saved: %s", plan_path)

    if args.dry_run:
        return 0

    # Step 2: spawn one inner-simulator subprocess per slice.
    if not INNER_SCRIPT.exists():
        logger.error("Inner script not found: %s", INNER_SCRIPT)
        return 2

    slices_dir = output_dir / "_slices"
    failed_slices: list[dict] = []
    for s in slices:
        per_slice_dir = slices_dir / s.tag
        rc, log_path = run_inner_simulator(s, args, per_slice_dir, runner=runner)
        if rc != 0:
            failed_slices.append({
                "tag": s.tag,
                "start": s.start.isoformat(),
                "end": s.end.isoformat(),
                "returncode": rc,
                "log_path": str(log_path),
            })
            logger.warning("[%s] FAILED rc=%s — see %s", s.tag, rc, log_path)

    # Step 3: collect fresh + merge.
    fresh_map, fresh_errors = collect_fresh_records(slices, output_dir)
    for err in fresh_errors:
        logger.warning("collect_fresh: %s", err)

    # Re-load prior payload (cheap).
    with open(args.prior_results, "r", encoding="utf-8") as f:
        prior_payload = json.load(f)

    fresh_map_with_meta = dict(fresh_map)
    fresh_map_with_meta["__meta__"] = {
        "current_prompt_hash": plan.current_prompt_hash,
        "current_config_hash": plan.current_config_hash,
        "prompt_path": str(args.prompt),
        "config_path": str(args.config),
        "n_failed_slices": len(failed_slices),
    }
    merged = merge_results(prior_payload, fresh_map_with_meta)
    if failed_slices:
        merged["incremental_meta"]["failed_slices"] = failed_slices

    # Stamp top-level hashes too so the merged file is itself a valid prior
    # for the NEXT incremental run.
    merged["incremental_meta"]["prompt_hash"] = plan.current_prompt_hash
    merged["incremental_meta"]["config_hash"] = plan.current_config_hash

    consolidated_path = output_dir / (
        f"incremental_{args.symbol}_{window_start.isoformat()}_{window_end.isoformat()}.json"
    )
    with open(consolidated_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2)
    logger.info("Consolidated output: %s", consolidated_path)

    return 0 if not failed_slices else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
