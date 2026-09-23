#!/usr/bin/env python3
"""Backfill append-only LTO-016 J46-J49 exit-comparator audit rows."""

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

from src.research_infra.j46_j49_exit_comparator_audit import (  # noqa: E402
    ACTION_REQUIRED,
    CANDIDATE_NO_FILL_CONTEXT,
    CANDIDATE_PATH_SYNTHETIC_ONLY,
    FILLED_JOINED,
    FILLED_MISSING,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_j46_j49_exit_comparator_audit_rows,
    build_rolling_status,
)


DEFAULT_J46_OUTCOMES = Path("shadow_logs/j46_j49_shadow_outcomes.jsonl")
DEFAULT_BROKER_AUDIT = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PATH_FOLLOW = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/j46_j49_exit_comparator_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO016_J46_J49_EXIT_COMPARATOR_AUDIT_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append((line_no, row))
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
    status_counts = Counter(str(row.get("j46_j49_exit_comparator_status") or "UNKNOWN") for row in rows)
    action_rows = [
        {
            "row_key": row.get("row_key"),
            "row_type": row.get("row_type"),
            "candidate_id": row.get("candidate_id"),
            "fill_id": row.get("fill_id"),
            "symbol": row.get("symbol"),
            "status": row.get("j46_j49_exit_comparator_status"),
            "action_required_codes": row.get("action_required_codes") or [],
        }
        for row in rows
        if row.get("j46_j49_exit_comparator_status") == ACTION_REQUIRED or row.get("action_required_codes")
    ]
    return {
        "schema_version": "lto016_j46_j49_exit_comparator_audit_report_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_rows else "OK_J46_J49_EXIT_COMPARATOR_AUDIT_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "rows_computed": len(rows),
            "status_rows_available": len(read_jsonl_with_lines(output_path)),
            "status_rows_appended_this_run": len(appended_rows),
            "filled_account_history_joined": status_counts.get(FILLED_JOINED, 0),
            "filled_account_history_missing": status_counts.get(FILLED_MISSING, 0),
            "candidate_no_fill_context": status_counts.get(CANDIDATE_NO_FILL_CONTEXT, 0),
            "candidate_path_synthetic_only": status_counts.get(CANDIDATE_PATH_SYNTHETIC_ONLY, 0),
            "action_required": len(action_rows),
            "actual_r_claim_allowed_rows": rolling["actual_r_claim_allowed_rows"],
        },
        "rolling_status": rolling,
        "action_required_examples": action_rows[:25],
        "claim_boundary": (
            "Filled J46/J49 comparator rows may claim actual-R only when joined to ACCOUNT_HISTORY_REALIZED broker audit evidence. "
            "Candidate context rows prevent fill-only rows from being mistaken for the full candidate universe and never claim actual-R."
        ),
        "ml_goal_contribution": (
            "This audit converts the exit-comparator lane into ML-ready label-quality and sample-eligibility metadata: "
            "account-history-realized fills can become target labels after K55 target refresh, while no-fill/path-only rows become "
            "explicit non-label or synthetic-path context."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    counts = report["counts"]
    rolling = report["rolling_status"]
    lines = [
        "# LTO-016 J46-J49 Exit Comparator Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Rows computed: `{counts['rows_computed']}`",
        f"- Status rows available: `{counts['status_rows_available']}`",
        f"- Status rows appended this run: `{counts['status_rows_appended_this_run']}`",
        f"- Filled account-history joined: `{counts['filled_account_history_joined']}`",
        f"- Filled account-history missing: `{counts['filled_account_history_missing']}`",
        f"- Candidate no-fill context: `{counts['candidate_no_fill_context']}`",
        f"- Candidate path synthetic-only: `{counts['candidate_path_synthetic_only']}`",
        f"- Actual-R claim allowed rows: `{counts['actual_r_claim_allowed_rows']}`",
        f"- Action required: `{counts['action_required']}`",
        "",
        "## Status Breakdown",
        "",
        f"- Status counts: `{rolling['status_counts']}`",
        f"- Row type counts: `{rolling['row_type_counts']}`",
        f"- ML label eligibility counts: `{rolling['ml_label_eligibility_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        f"- Documented limitations: `{rolling['documented_limitation_code_counts']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
        "## ML Goal Contribution",
        "",
        report["ml_goal_contribution"],
        "",
        "## Safety Counters",
        "",
        f"- ai_calls: `{report['ai_calls']}`",
        f"- canary_calls: `{report['canary_calls']}`",
        f"- order_calls: `{report['order_calls']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["action_required_examples"]:
        lines.extend(
            [
                "",
                "## Action Required Examples",
                "",
                "```json",
                json.dumps(report["action_required_examples"], indent=2, sort_keys=True),
                "```",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--j46-outcomes", type=Path, default=DEFAULT_J46_OUTCOMES)
    parser.add_argument("--broker-audit", type=Path, default=DEFAULT_BROKER_AUDIT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--path-follow", type=Path, default=DEFAULT_PATH_FOLLOW)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_j46_j49_exit_comparator_audit_rows(
        read_jsonl_with_lines(args.j46_outcomes),
        broker_rows=read_jsonl_with_lines(args.broker_audit),
        candidate_rows=read_jsonl_with_lines(args.candidates),
        path_rows=read_jsonl_with_lines(args.path_follow),
        generated_at_utc=generated_at,
    )
    existing = existing_row_keys(args.output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(args.output, appended)

    report = build_report(rows, appended, args.output)
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows_computed": report["counts"]["rows_computed"],
                "status_rows_appended": len(appended),
                "status_rows_available": report["counts"]["status_rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
