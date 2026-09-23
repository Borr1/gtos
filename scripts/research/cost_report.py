#!/usr/bin/env python
"""Print the cost-tracker aggregate for a given run_tag.

Usage:
    python scripts/research/cost_report.py --run-tag phase1_a1
    python scripts/research/cost_report.py --run-tag phase1_a1 --since 2026-04-26
    python scripts/research/cost_report.py --run-tag phase1_a1 \\
        --since 2026-04-26T08:00:00+00:00 --until 2026-04-27T00:00:00+00:00

This script is RESEARCH-only — it READS ``shadow_logs/research_cost.jsonl``
written by ``src/research_infra/cost_tracker.CostTracker.log_call``. It
does not call any APIs.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Make ``src.research_infra...`` importable when invoked from a fresh shell.
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from src.research_infra.cost_tracker import CostTracker  # noqa: E402


def _parse_when(s: str | None) -> datetime | None:
    if s is None:
        return None
    try:
        dt = datetime.fromisoformat(s)
    except ValueError as exc:
        raise SystemExit(
            f"--since/--until: cannot parse {s!r} as ISO 8601 "
            f"(e.g. 2026-04-26 or 2026-04-26T08:00:00+00:00): {exc}"
        )
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


def _print_report(report) -> None:
    print(f"Run tag           : {report.run_tag}")
    print(f"Calls             : {report.n_calls}")
    print(f"Window start (UTC): {report.start_iso or '—'}")
    print(f"Window end   (UTC): {report.end_iso or '—'}")
    print(f"Input tokens      : {report.total_input_tokens:,}")
    print(f"Output tokens     : {report.total_output_tokens:,}")
    print(f"Cache read tokens : {report.total_cache_read_tokens:,}")
    print(f"Cache write tokens: {report.total_cache_write_tokens:,}")
    print(f"Total USD         : ${report.total_usd:.6f}")
    print()
    if not report.per_model:
        return
    print(f"{'Model':<25} {'Calls':>8} {'In tok':>12} {'Out tok':>12} {'USD':>12}")
    print("-" * 73)
    for model in sorted(report.per_model):
        m = report.per_model[model]
        print(
            f"{model:<25} "
            f"{m['n_calls']:>8} "
            f"{m['total_input_tokens']:>12,} "
            f"{m['total_output_tokens']:>12,} "
            f"${m['total_usd']:>11.6f}"
        )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument(
        "--run-tag",
        required=True,
        help="Tag to aggregate (e.g. phase1_a1_dumb_baseline).",
    )
    p.add_argument(
        "--since",
        default=None,
        help="Inclusive lower bound (ISO 8601). Naive datetimes are UTC.",
    )
    p.add_argument(
        "--until",
        default=None,
        help="Exclusive upper bound (ISO 8601). Naive datetimes are UTC.",
    )
    p.add_argument(
        "--log-path",
        default=str(_REPO_ROOT / "shadow_logs" / "research_cost.jsonl"),
        help="Path to the cost JSONL (default: shadow_logs/research_cost.jsonl).",
    )
    args = p.parse_args(argv)

    since = _parse_when(args.since)
    until = _parse_when(args.until)

    tracker = CostTracker(log_path=Path(args.log_path))
    report = tracker.aggregate(run_tag=args.run_tag, since=since, until=until)
    _print_report(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
