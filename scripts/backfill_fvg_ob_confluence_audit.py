#!/usr/bin/env python3
"""Backfill append-only FVG/OB confluence audit rows."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.fvg_ob_confluence_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    WAITING,
    build_fvg_ob_confluence_audit_rows,
    build_rolling_status,
)


DEFAULT_CONFLUENCE = Path("shadow_logs/fvg_ob_confluence.jsonl")
DEFAULT_RESOLUTIONS = Path("shadow_logs/fvg_ob_confluence_resolutions.jsonl")
DEFAULT_MECHANICAL = Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_LTF = Path("shadow_logs/candidate_ltf_path_order.jsonl")
DEFAULT_OPPORTUNITIES = Path("shadow_logs/live_candidate_opportunity_clusters.jsonl")
DEFAULT_STRUCTURAL = Path("shadow_logs/live_structural_strategy_metadata.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/fvg_ob_confluence_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO008_FVG_OB_CONFLUENCE_AUDIT_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if text:
                rows.append((line_no, json.loads(text)))
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for _, row in read_jsonl_with_lines(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    status_counts = Counter(str(row.get("fvg_ob_confluence_audit_status") or "UNKNOWN") for row in rows)
    action_examples: list[dict[str, Any]] = []
    source_blocked_examples: list[dict[str, Any]] = []
    for row in rows:
        if row.get("fvg_ob_confluence_audit_status") == ACTION_REQUIRED:
            action_examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "action_required_codes": row.get("action_required_codes") or [],
                }
            )
        limitations = set(row.get("documented_limitation_codes") or [])
        if "FVG_BOUNDS_SOURCE_NOT_CAPTURED" in limitations or "STANDALONE_FVG_ENTRY_GEOMETRY_SOURCE_NOT_CAPTURED" in limitations:
            source_blocked_examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "bucket_state": row.get("bucket_state"),
                    "source_capture_statuses": row.get("source_capture_statuses"),
                }
            )

    return {
        "schema_version": "lto008_fvg_ob_confluence_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_FVG_OB_LIMITATIONS",
        "audit_log_path": str(output_path),
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "confluence_rows_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "audit_rows_appended_this_run": len(appended_rows),
            "audit_rows_available": len(read_jsonl_with_lines(output_path)),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "waiting_for_path": status_counts.get(WAITING, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "action_required_examples": action_examples[:25],
        "source_blocked_examples": source_blocked_examples[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-008 FVG/OB Confluence Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Confluence rows considered: `{report['counts']['confluence_rows_considered']}`",
        f"- Audit rows available: `{report['counts']['audit_rows_available']}`",
        f"- Audit rows appended this run: `{report['counts']['audit_rows_appended_this_run']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Waiting for path: `{report['counts']['waiting_for_path']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Rolling Status",
        "",
        f"- Resolved path rows: `{rolling['resolved_path_rows']}`",
        f"- Exact bounds captured rows: `{rolling['exact_bounds_captured_rows']}`",
        f"- Duplicate-aware countable path rows: `{rolling['duplicate_aware_countable_path_rows']}`",
        f"- No-leak status: `{rolling['no_leak_status']}`",
        "",
        "## Buckets",
        "",
        f"- Bucket counts: `{rolling['bucket_counts']}`",
        f"- Relation states: `{rolling['relation_state_counts']}`",
        "",
        "## Source Capture",
        "",
        f"`{rolling['source_capture_status_counts']}`",
        "",
        "## Scoreability",
        "",
        f"- FVG/OB confluence: `{rolling['fvg_ob_scoreability_counts']}`",
        f"- FVG mid edge: `{rolling['fvg_mid_edge_scoreability_counts']}`",
        "",
        "## Path Outcomes",
        "",
        f"`{rolling['path_outcome_status_counts']}`",
        "",
        "## Documented Limitation Counts",
        "",
        f"`{rolling['documented_limitation_counts']}`",
        "",
        "## Action Required Counts",
        "",
        f"`{rolling['action_required_counts']}`",
        "",
        "## Source-Blocked Examples",
        "",
        f"`{report['source_blocked_examples']}`",
        "",
        "## Safety",
        "",
        f"- No AI calls: `{report['no_ai_calls']}`",
        f"- No canary required: `{report['no_canary_required']}`",
        f"- No execution: `{report['no_execution']}`",
        f"- Paid fetch attempted: `{report['paid_fetch_attempted']}`",
        f"- Paid data calls: `{report['paid_data_calls']}`",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confluence", type=Path, default=DEFAULT_CONFLUENCE)
    parser.add_argument("--resolutions", type=Path, default=DEFAULT_RESOLUTIONS)
    parser.add_argument("--mechanical", type=Path, default=DEFAULT_MECHANICAL)
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--ltf-paths", type=Path, default=DEFAULT_LTF)
    parser.add_argument("--opportunities", type=Path, default=DEFAULT_OPPORTUNITIES)
    parser.add_argument("--structural", type=Path, default=DEFAULT_STRUCTURAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--decision-date-prefix", default=None)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_fvg_ob_confluence_audit_rows(
        read_jsonl_with_lines(args.confluence),
        read_jsonl_with_lines(args.resolutions),
        mechanical_rows=read_jsonl_with_lines(args.mechanical),
        path_rows=read_jsonl_with_lines(args.paths),
        ltf_rows=read_jsonl_with_lines(args.ltf_paths),
        opportunity_rows=read_jsonl_with_lines(args.opportunities),
        structural_rows=read_jsonl_with_lines(args.structural),
        generated_at_utc=generated_at,
        decision_date_prefix=args.decision_date_prefix,
    )
    seen = existing_row_keys(args.output)
    append_rows = [row for row in rows if str(row.get("row_key")) not in seen]
    append_jsonl(args.output, append_rows)

    report = build_report(rows, append_rows, args.output)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "counts": report["counts"],
                "rolling_status": {
                    "resolved_path_rows": report["rolling_status"]["resolved_path_rows"],
                    "exact_bounds_captured_rows": report["rolling_status"]["exact_bounds_captured_rows"],
                    "duplicate_aware_countable_path_rows": report["rolling_status"]["duplicate_aware_countable_path_rows"],
                    "no_leak_status": report["rolling_status"]["no_leak_status"],
                },
                "audit_log_path": report["audit_log_path"],
                "report_json": str(args.report_json),
                "report_md": str(args.report_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
