"""Append resolver/backfill rows for live shadow capture gaps.

This is read-only with respect to live trading. It does not call AI, canary,
Databento, or order APIs. Existing JSONL rows are never rewritten.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.live_shadow_gap_closure import close_gaps  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=str(ROOT))
    parser.add_argument("--max-hours", type=float, default=8.0)
    parser.add_argument(
        "--skip-mt5",
        action="store_true",
        help="Skip MT5 M1 reads and emit explicit source-blocked LTF rows.",
    )
    parser.add_argument(
        "--candidate-id",
        action="append",
        default=[],
        help="Refresh only the specified candidate_id. May be repeated.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = close_gaps(
        root=Path(args.root),
        max_hours=args.max_hours,
        skip_mt5=bool(args.skip_mt5),
        candidate_ids=set(args.candidate_id) or None,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
