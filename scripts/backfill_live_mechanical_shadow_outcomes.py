#!/usr/bin/env python3
"""Backfill/refresh live mechanical strategy shadow outcome rows.

Reads live forward candidate rows plus candidate path-follow snapshots and
emits per-strategy outcome/status rows. This is read-only with respect to live
trading state: no AI, no canary, no paid data, no order API.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.live_mechanical_shadow import (  # noqa: E402
    DEFAULT_CANDIDATES,
    DEFAULT_LTF_PATH_ORDER,
    DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE,
    DEFAULT_OUTPUT,
    DEFAULT_PENDING_LIFECYCLE,
    DEFAULT_PATHS,
    run,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--pending-lifecycle", type=Path, default=DEFAULT_PENDING_LIFECYCLE)
    parser.add_argument("--ltf-path-order", type=Path, default=DEFAULT_LTF_PATH_ORDER)
    parser.add_argument(
        "--moonshot-selected-action-source-capture",
        type=Path,
        default=DEFAULT_MOONSHOT_SELECTED_ACTION_SOURCE_CAPTURE,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--latest-paths-only",
        action="store_true",
        help="Evaluate only the latest path row per candidate instead of the full historical path log.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Do not append to the output log; report rows that would be written.",
    )
    parser.add_argument(
        "--dry-run-output",
        type=Path,
        default=None,
        help="Optional JSONL path for the dry-run rows that would be appended.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run(
        candidates_path=args.candidates,
        paths_path=args.paths,
        pending_lifecycle_path=args.pending_lifecycle,
        ltf_path_order_path=args.ltf_path_order,
        moonshot_selected_action_source_capture_path=args.moonshot_selected_action_source_capture,
        output_path=args.output,
        latest_paths_only=args.latest_paths_only,
        dry_run=args.dry_run,
        dry_run_output_path=args.dry_run_output,
    )
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
