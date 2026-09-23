#!/usr/bin/env python3
"""Backfill append-only V2b forward-pair resolution audit rows."""

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

from src.research_infra.v2b_forward_pair_resolution_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    WAITING,
    build_rolling_status,
    build_v2b_forward_pair_audit_rows,
)


DEFAULT_PAIRS = Path("shadow_logs/v2b_forward_pairs.jsonl")
DEFAULT_RESOLUTIONS = Path("shadow_logs/v2b_forward_pair_resolutions.jsonl")
DEFAULT_MECHANICAL = Path("shadow_logs/live_mechanical_strategy_shadow_outcomes.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_LTF = Path("shadow_logs/candidate_ltf_path_order.jsonl")
DEFAULT_ACCOUNT_TRUTH = Path("shadow_logs/account_truth_reconciliation_status.jsonl")
DEFAULT_OPPORTUNITIES = Path("shadow_logs/live_candidate_opportunity_clusters.jsonl")
DEFAULT_PENDING_LIFECYCLE_AUDIT = Path("shadow_logs/pending_limit_lifecycle_audit.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/v2b_forward_pair_resolution_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO006_V2B_FORWARD_PAIR_RESOLUTION_AUDIT_2026-05-05.md")


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
    status_counts = Counter(str(row.get("v2b_forward_pair_resolution_audit_status") or "UNKNOWN") for row in rows)
    path_counts = Counter(str(row.get("path_outcome_status") or row.get("path_label") or "UNKNOWN") for row in rows)
    opportunity_counts = Counter(str(row.get("duplicate_aware_counting_status") or "UNKNOWN") for row in rows)
    action_examples: list[dict[str, Any]] = []
    unresolved_examples: list[dict[str, Any]] = []
    for row in rows:
        if row.get("v2b_forward_pair_resolution_audit_status") == ACTION_REQUIRED:
            action_examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "action_required_codes": row.get("action_required_codes") or [],
                }
            )
        if row.get("actual_synthetic_label_lane") == "UNRESOLVED_PATH":
            unresolved_examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "path_outcome_status": row.get("path_outcome_status"),
                    "ob_boundary_status": (row.get("ob_boundary_outcome") or {}).get("r_counting_status"),
                    "baseline_status": (row.get("j46_baseline_outcome") or {}).get("r_counting_status"),
                }
            )

    return {
        "schema_version": "lto006_v2b_forward_pair_resolution_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_V2B_LIMITATIONS",
        "audit_log_path": str(output_path),
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "v2b_pair_rows_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "audit_rows_appended_this_run": len(appended_rows),
            "audit_rows_available": len(read_jsonl_with_lines(output_path)),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "waiting_for_path": status_counts.get(WAITING, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "path_outcome_status_counts": dict(path_counts),
        "duplicate_aware_counting_status_counts": dict(opportunity_counts),
        "action_required_examples": action_examples[:25],
        "unresolved_path_examples": unresolved_examples[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-006 V2b Forward-Pair Resolution Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- V2b pair rows considered: `{report['counts']['v2b_pair_rows_considered']}`",
        f"- Audit rows available: `{report['counts']['audit_rows_available']}`",
        f"- Audit rows appended this run: `{report['counts']['audit_rows_appended_this_run']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Waiting for path: `{report['counts']['waiting_for_path']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Rolling Status",
        "",
        f"- Resolved pairs: `{rolling['resolved_pair_count']}`",
        f"- R-counted pairs: `{rolling['r_counted_pair_count']}`",
        f"- Broker actual-R counted pairs: `{rolling['broker_actual_r_counted_pair_count']}`",
        f"- Synthetic path-R counted pairs: `{rolling['synthetic_path_r_counted_pair_count']}`",
        f"- Duplicate-aware countable R pairs: `{rolling['duplicate_aware_countable_r_pair_count']}`",
        f"- Sample-floor progress: `{rolling['sample_floor_progress']}`",
        f"- Ambiguity rate: `{rolling['ambiguity_rate']}`",
        f"- No-leak status: `{rolling['no_leak_status']}`",
        "",
        "## Concentration",
        "",
        f"- Symbol counts: `{rolling['symbol_counts']}`",
        f"- Session counts: `{rolling['session_counts']}`",
        f"- Symbol/session counts: `{rolling['symbol_session_counts']}`",
        f"- Largest symbol share: `{rolling['largest_symbol_share']}`",
        "",
        "## Label Lanes",
        "",
        f"`{rolling['label_lane_counts']}`",
        "",
        "## Path Outcomes",
        "",
        f"`{report['path_outcome_status_counts']}`",
        "",
        "## Duplicate-Aware Counting",
        "",
        f"`{report['duplicate_aware_counting_status_counts']}`",
        "",
        "## Documented Limitation Counts",
        "",
        f"`{rolling['documented_limitation_counts']}`",
        "",
        "## Action Required Counts",
        "",
        f"`{rolling['action_required_counts']}`",
        "",
        "## Unresolved Examples",
        "",
        f"`{report['unresolved_path_examples']}`",
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
    parser.add_argument("--pairs", type=Path, default=DEFAULT_PAIRS)
    parser.add_argument("--resolutions", type=Path, default=DEFAULT_RESOLUTIONS)
    parser.add_argument("--mechanical", type=Path, default=DEFAULT_MECHANICAL)
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--ltf-paths", type=Path, default=DEFAULT_LTF)
    parser.add_argument("--account-truth", type=Path, default=DEFAULT_ACCOUNT_TRUTH)
    parser.add_argument("--opportunities", type=Path, default=DEFAULT_OPPORTUNITIES)
    parser.add_argument("--pending-lifecycle-audit", type=Path, default=DEFAULT_PENDING_LIFECYCLE_AUDIT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--decision-date-prefix", default=None)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_v2b_forward_pair_audit_rows(
        read_jsonl_with_lines(args.pairs),
        read_jsonl_with_lines(args.resolutions),
        mechanical_rows=read_jsonl_with_lines(args.mechanical),
        path_rows=read_jsonl_with_lines(args.paths),
        ltf_rows=read_jsonl_with_lines(args.ltf_paths),
        account_truth_rows=read_jsonl_with_lines(args.account_truth),
        opportunity_rows=read_jsonl_with_lines(args.opportunities),
        pending_lifecycle_audit_rows=read_jsonl_with_lines(args.pending_lifecycle_audit),
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
                    "resolved_pair_count": report["rolling_status"]["resolved_pair_count"],
                    "r_counted_pair_count": report["rolling_status"]["r_counted_pair_count"],
                    "duplicate_aware_countable_r_pair_count": report["rolling_status"]["duplicate_aware_countable_r_pair_count"],
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
