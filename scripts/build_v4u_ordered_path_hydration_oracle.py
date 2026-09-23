#!/usr/bin/env python3
"""Build the V4U rolling ordered-path hydration/oracle artifacts.

This is a read-only local-source runner. It does not connect to MT5 by itself;
it records exact MT5 read-only probe/export commands for windows that still
lack eligible local M1/tick evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.research_infra.v4u_ordered_path_hydration import (  # noqa: E402
    append_jsonl,
    build_rolling_hydration_oracle,
    utc_now_iso,
    write_json,
    write_jsonl,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ordered-path-ledger", required=True, type=Path)
    parser.add_argument("--candidate-ledger", required=True, type=Path)
    parser.add_argument("--source-root", action="append", type=Path, default=[])
    parser.add_argument("--scratch-root", required=True, type=Path)
    parser.add_argument("--output-report-json", required=True, type=Path)
    parser.add_argument("--output-oracle-jsonl", required=True, type=Path)
    parser.add_argument("--mt5-hydration-ledger", type=Path)
    parser.add_argument("--ordered-path-oracle-ledger", type=Path)
    parser.add_argument("--source-search-ledger", type=Path)
    parser.add_argument("--storage-ledger", type=Path)
    parser.add_argument("--run-id")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    generated = utc_now_iso()
    report, rows = build_rolling_hydration_oracle(
        ordered_path_ledger=args.ordered_path_ledger,
        candidate_ledger=args.candidate_ledger,
        source_roots=tuple(args.source_root),
        scratch_root=args.scratch_root,
        run_id=args.run_id,
    )
    write_json(args.output_report_json, report)
    write_jsonl(args.output_oracle_jsonl, rows)

    report_hash = _sha256(args.output_report_json)
    oracle_hash = _sha256(args.output_oracle_jsonl)
    metrics = report["metrics"]
    event = {
        "event_id": "v4u_ordered_path_rolling_hydration_oracle",
        "generated_at_utc": generated,
        "status": "completed",
        "evidence_label": "read-only local M1/tick rolling hydration and ordered-path oracle",
        "implemented_code": [
            "src/research_infra/v4u_ordered_path_hydration.py",
            "scripts/build_v4u_ordered_path_hydration_oracle.py",
        ],
        "report_artifact": str(args.output_report_json),
        "report_sha256": report_hash,
        "oracle_row_artifact": str(args.output_oracle_jsonl),
        "oracle_row_sha256": oracle_hash,
        "oracle_rows": len(rows),
        "metrics": {
            "ordered_touch_missing_rows": metrics["ordered_touch_missing_rows"],
            "rolling_window_count": metrics["rolling_window_count"],
            "rolling_windows_with_eligible_ltf": metrics["rolling_windows_with_eligible_ltf"],
            "rolling_windows_with_mt5_binary_cache_candidate": metrics.get(
                "rolling_windows_with_mt5_binary_cache_candidate",
                0,
            ),
            "decision_packet_leakage_rows": metrics["decision_packet_leakage_rows"],
            "coverage_status_counts": metrics["coverage_status_counts"],
            "oracle_status_counts": metrics["oracle_status_counts"],
            "mt5_binary_cache_status_counts": metrics.get("mt5_binary_cache_status_counts", {}),
            "mt5_binary_cache_label_counts_seen_in_rows": metrics.get(
                "mt5_binary_cache_label_counts_seen_in_rows",
                {},
            ),
        },
        "source_boundary": report["source_boundary"],
        "scratch_cleanup": report["scratch_cleanup"],
        "broker_or_live_mutation": False,
        "mt5_live_operation": False,
        "paid_api_or_vendor_call": False,
    }
    if args.mt5_hydration_ledger:
        append_jsonl(
            args.mt5_hydration_ledger,
            {
                **event,
                "ledger_role": "mt5_hydration",
                "status": (
                    "completed_no_local_ltf_conversion"
                    if metrics["rolling_windows_with_eligible_ltf"] == 0
                    else "completed_local_ltf_oracle_rows_materialized"
                ),
                "remaining_required_work": (
                    "run listed read-only MT5 M1/tick probes or exports for exact windows "
                    "without eligible local LTF files"
                ),
            },
        )
    if args.ordered_path_oracle_ledger:
        append_jsonl(
            args.ordered_path_oracle_ledger,
            {
                **event,
                "ledger_role": "ordered_path_oracle",
                "full_row_ledger": str(args.output_oracle_jsonl),
                "remaining_required_work": (
                    "hydrate eligible M1/tick sources for rows whose oracle_status remains "
                    "not_run_no_eligible_ltf_source"
                ),
            },
        )
    if args.source_search_ledger:
        append_jsonl(
            args.source_search_ledger,
            {
                "search_id": "v4u_source_007_rolling_day_session_window_hydration_oracle",
                "generated_at_utc": generated,
                "status": "completed",
                "commands": [
                    "scripts/build_v4u_ordered_path_hydration_oracle.py over Wave4R ordered-path gaps",
                    "joined candidate microscope rows for session/geometry/source hashes",
                    "indexed local/package M1/tick roots and rejected proxy M15 sources",
                    "deleted lane-owned scratch after durable report and oracle row ledger",
                ],
                "searched_paths": [str(path) for path in args.source_root],
                "positive_evidence": {
                    "ordered_touch_missing_rows": metrics["ordered_touch_missing_rows"],
                    "candidate_rows_joined": metrics["candidate_rows_joined"],
                    "rolling_window_count": metrics["rolling_window_count"],
                    "rolling_windows_with_mt5_binary_cache_candidate": metrics.get(
                        "rolling_windows_with_mt5_binary_cache_candidate",
                        0,
                    ),
                    "mt5_binary_cache_status_counts": metrics.get(
                        "mt5_binary_cache_status_counts",
                        {},
                    ),
                    "source_index_summary": report["source_index_summary"],
                },
                "negative_or_gap_evidence": {
                    "rolling_windows_without_eligible_ltf": metrics[
                        "rolling_windows_without_eligible_ltf"
                    ],
                    "decision_packet_leakage_rows": metrics["decision_packet_leakage_rows"],
                    "proxy_sources_used_as_broker_native_truth": report["verdict"][
                        "proxy_sources_used_as_broker_native_truth"
                    ],
                },
                "next_action": (
                    "execute exact read-only MT5/cache export commands for needed windows, "
                    "then rerun this oracle to convert recovered windows into ordered path truth"
                ),
                "source_boundary": report["source_boundary"],
            },
        )
    if args.storage_ledger:
        append_jsonl(
            args.storage_ledger,
            {
                "event_id": "v4u_storage_rolling_ordered_path_hydration_scratch_cleanup",
                "generated_at_utc": generated,
                "status": report["scratch_cleanup"]["cleanup_status"],
                "scratch_cleanup": report["scratch_cleanup"],
                "durable_artifacts": [
                    {
                        "path": str(args.output_report_json),
                        "sha256": report_hash,
                    },
                    {
                        "path": str(args.output_oracle_jsonl),
                        "sha256": oracle_hash,
                        "rows": len(rows),
                    },
                ],
                "storage_policy": (
                    "lane-owned day/session/window scratch is deleted after hashes, row "
                    "counts, source labels, and oracle rows are durable"
                ),
            },
        )
    print(json.dumps(event, indent=2, sort_keys=True))
    return 0


def _sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
