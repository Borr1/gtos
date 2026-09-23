#!/usr/bin/env python3
"""Build the GTOS primitive-science goal program scaffold.

This writes research-control artifacts only: schemas, empty registries,
worktree launch maps, source/budget ledgers, and per-lane goal prompts.
It does not create external worktrees, fetch data, call AI/canaries/MT5, place
orders, or alter live trading behavior.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.science_goal_program import (  # noqa: E402
    PROGRAM_ROOT,
    RESULT_BOUNDARY,
    SCHEMA_VERSION,
    build_payload,
    utc_now_iso,
    write_outputs,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--generated-at-utc", default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(generated_at_utc=args.generated_at_utc or utc_now_iso())
    outputs = write_outputs(payload, root=args.root)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "result_boundary": RESULT_BOUNDARY,
                "schema_version": SCHEMA_VERSION,
                "program_root": str(PROGRAM_ROOT),
                "lane_count": payload["lane_count"],
                "science_lane_count": payload["science_lane_count"],
                "files_written": len(outputs),
                "ai_calls": payload["ai_calls"],
                "mt5_calls": payload["mt5_calls"],
                "paid_data_calls": payload["paid_data_calls"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
