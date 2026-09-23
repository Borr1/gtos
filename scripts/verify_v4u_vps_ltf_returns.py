#!/usr/bin/env python3
"""Verify returned VPS/Windows MT5 LTF exports before oracle replay use."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.v4u_vps_ltf_return_verifier import (  # noqa: E402
    verify_ltf_returns,
    write_json,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements-jsonl", required=True, type=Path)
    parser.add_argument("--source-root", action="append", type=Path, default=[])
    parser.add_argument("--output-report-json", required=True, type=Path)
    parser.add_argument("--output-requirement-jsonl", required=True, type=Path)
    parser.add_argument("--mt5-hydration-ledger", type=Path)
    parser.add_argument("--source-search-ledger", type=Path)
    parser.add_argument("--run-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    generated = _utc_now_iso()
    report, rows = verify_ltf_returns(
        requirements_jsonl=args.requirements_jsonl,
        source_roots=tuple(args.source_root),
        run_id=args.run_id,
    )
    write_json(args.output_report_json, report)
    write_jsonl(args.output_requirement_jsonl, rows)
    event = {
        "event_id": "v4u_vps_ltf_return_verifier",
        "generated_at_utc": generated,
        "status": "completed",
        "requirements_jsonl": str(args.requirements_jsonl),
        "source_roots": [str(root) for root in args.source_root],
        "report_artifact": str(args.output_report_json),
        "requirement_row_artifact": str(args.output_requirement_jsonl),
        "requirements_total": report["requirements_total"],
        "requirements_with_accepted_source": report["requirements_with_accepted_source"],
        "return_status_counts": report["return_status_counts"],
        "source_boundary": report["source_boundary"],
        "next_step": report["next_step"],
        "broker_or_live_mutation": False,
        "mt5_live_operation": False,
        "paid_api_or_vendor_call": False,
    }
    if args.mt5_hydration_ledger:
        _append_jsonl(
            args.mt5_hydration_ledger,
            {
                **event,
                "ledger_role": "vps_ltf_return_verifier",
            },
        )
    if args.source_search_ledger:
        _append_jsonl(
            args.source_search_ledger,
            {
                **event,
                "ledger_role": "vps_ltf_return_source_catalog",
                "search_id": "v4u_source_009_vps_ltf_return_verifier",
            },
        )
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


def _append_jsonl(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


if __name__ == "__main__":
    raise SystemExit(main())
