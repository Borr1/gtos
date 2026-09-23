#!/usr/bin/env python3
"""Build the V4U VPS/Windows MT5 LTF hydration handoff package.

This does not connect to MT5. It converts the current rolling ordered-path
oracle's exact requirements into broker-labeled read-only probe/export commands
for execution later on the Windows/VPS terminal.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.v4u_vps_ltf_handoff import (  # noqa: E402
    DEFAULT_SOURCE_BROKER,
    DEFAULT_SOURCE_ROLE,
    build_handoff_package,
    utc_now_iso,
    write_json,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--oracle-report", required=True, type=Path)
    parser.add_argument("--output-manifest-json", required=True, type=Path)
    parser.add_argument("--output-requirements-jsonl", required=True, type=Path)
    parser.add_argument("--output-powershell", required=True, type=Path)
    parser.add_argument("--source-broker", default=DEFAULT_SOURCE_BROKER)
    parser.add_argument("--source-role", default=DEFAULT_SOURCE_ROLE)
    parser.add_argument("--python-executable", default="python")
    parser.add_argument(
        "--output-root",
        default="data/mt5_research_exports",
        help="Root where VPS read-only probe/export artifacts should be written.",
    )
    parser.add_argument(
        "--symbol-map",
        action="append",
        default=[],
        help="Override FILE_SYMBOL:MT5_SYMBOL mapping; repeatable.",
    )
    parser.add_argument("--max-requirements", type=int)
    parser.add_argument("--mt5-hydration-ledger", type=Path)
    parser.add_argument("--source-search-ledger", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.max_requirements is not None and args.max_requirements <= 0:
        raise ValueError("--max-requirements must be positive when provided")
    oracle_report = json.loads(args.oracle_report.read_text(encoding="utf-8"))
    package = build_handoff_package(
        oracle_report=oracle_report,
        source_broker=args.source_broker,
        source_role=args.source_role,
        python_executable=args.python_executable,
        output_root=args.output_root,
        mt5_symbol_map=_parse_symbol_map(args.symbol_map),
        max_requirements=args.max_requirements,
    )
    write_json(args.output_manifest_json, package.manifest)
    write_jsonl(args.output_requirements_jsonl, package.requirement_rows)
    args.output_powershell.parent.mkdir(parents=True, exist_ok=True)
    args.output_powershell.write_text(package.powershell_text, encoding="utf-8")

    generated = utc_now_iso()
    event = {
        "event_id": "v4u_vps_mt5_ltf_handoff_package",
        "generated_at_utc": generated,
        "status": "completed",
        "source_broker": package.manifest["source_broker"],
        "source_role": package.manifest["source_role"],
        "source_truth_scope": package.manifest["source_truth_scope"],
        "replaces_missing_frozen_path_source": package.manifest[
            "replaces_missing_frozen_path_source"
        ],
        "not_redacted_account_native": package.manifest["not_redacted_account_native"],
        "input_oracle_report": str(args.oracle_report),
        "manifest_artifact": str(args.output_manifest_json),
        "requirements_artifact": str(args.output_requirements_jsonl),
        "powershell_artifact": str(args.output_powershell),
        "exact_requirement_groups_input": package.manifest[
            "exact_requirement_groups_input"
        ],
        "exact_requirement_groups_packaged": package.manifest[
            "exact_requirement_groups_packaged"
        ],
        "candidate_rows_total": package.manifest["candidate_rows_total"],
        "source_boundary": package.manifest["source_boundary"],
        "hard_boundaries": package.manifest["hard_boundaries"],
        "next_step": package.manifest["post_export_next_step"],
    }
    if args.mt5_hydration_ledger:
        _append_jsonl(
            args.mt5_hydration_ledger,
            {
                **event,
                "ledger_role": "vps_mt5_ltf_handoff",
                "remaining_required_work": (
                    "execute these read-only FTMO MT5 probes/exports on Windows/VPS, "
                    "then rerun ordered-path oracle and full replay when LTF rows exist"
                ),
            },
        )
    if args.source_search_ledger:
        _append_jsonl(
            args.source_search_ledger,
            {
                **event,
                "search_id": "v4u_source_008_vps_ftmo_ltf_handoff_package",
                "ledger_role": "source_hydration_handoff",
                "commands": [
                    "read V4U_ORDERED_PATH_ROLLING_HYDRATION_ORACLE_REPORT.json",
                    "packaged exact day/session/symbol/window requirements",
                    "emitted FTMO owner-authorized path-override provenance flags",
                    "emitted comma-separated tick windows for robust parser handling",
                ],
            },
        )

    print(
        json.dumps(
            {
                "status": "completed",
                "manifest": str(args.output_manifest_json),
                "requirements": str(args.output_requirements_jsonl),
                "powershell": str(args.output_powershell),
                "exact_requirement_groups_packaged": package.manifest[
                    "exact_requirement_groups_packaged"
                ],
                "candidate_rows_total": package.manifest["candidate_rows_total"],
                "source_broker": package.manifest["source_broker"],
                "source_role": package.manifest["source_role"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def _parse_symbol_map(items: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for raw in items:
        if ":" not in raw:
            raise argparse.ArgumentTypeError(
                f"--symbol-map must be FILE_SYMBOL:MT5_SYMBOL, got {raw!r}"
            )
        file_symbol, mt5_symbol = raw.split(":", 1)
        file_symbol = file_symbol.strip().upper()
        mt5_symbol = mt5_symbol.strip()
        if not file_symbol or not mt5_symbol:
            raise argparse.ArgumentTypeError(
                f"--symbol-map must be FILE_SYMBOL:MT5_SYMBOL, got {raw!r}"
            )
        mapping[file_symbol] = mt5_symbol
    return mapping


def _append_jsonl(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
