#!/usr/bin/env python3
"""Backfill append-only LTO-021 exit-management no-event status rows."""

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

from src.research_infra.exit_management_no_event_audit import (  # noqa: E402
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_EVENTS,
    EVENT_LOG_NAMES,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_exit_management_status_rows,
    build_rolling_status,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PENDING = Path("shadow_logs/pending_limit_lifecycle_join_backfill.jsonl")
DEFAULT_ACCOUNT = Path("shadow_logs/account_truth_reconciliation_status.jsonl")
DEFAULT_BROKER = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/exit_management_shadow_status.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO021_EXIT_MANAGEMENT_NO_EVENT_STATUS_2026-05-05.md")


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


def event_file_status(root: Path, path: Path) -> str:
    resolved = path if path.is_absolute() else root / path
    if not resolved.exists():
        return "EVENT_LOG_FILE_MISSING_NO_EVENT_STATUS_REQUIRED"
    if resolved.stat().st_size == 0:
        return "EVENT_LOG_FILE_EMPTY_NO_EVENT_STATUS_REQUIRED"
    return "EVENT_LOG_FILE_HAS_EVENT_ROWS"


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    status_counts = Counter(str(row.get("exit_management_status") or "UNKNOWN") for row in rows)
    action_examples = [
        {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "action_required_codes": row.get("action_required_codes") or [],
            "fill_state": row.get("fill_state"),
            "be_shadow_status": row.get("be_shadow_status"),
            "partial_close_shadow_status": row.get("partial_close_shadow_status"),
            "time_in_trade_shadow_status": row.get("time_in_trade_shadow_status"),
        }
        for row in rows
        if row.get("exit_management_status") == ACTION_REQUIRED
    ]
    return {
        "schema_version": "lto021_exit_management_no_event_status_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples else "OK_EXIT_MANAGEMENT_NO_EVENT_STATUS_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "counts": {
            "candidate_rows_considered": len(rows),
            "status_rows_appended": len(appended_rows),
            "status_rows_appended_this_run": len(appended_rows),
            "status_rows_available": len(read_jsonl_with_lines(output_path)),
            "no_event_documented": status_counts.get(COMPLETE, 0),
            "event_rows_present": status_counts.get(COMPLETE_WITH_EVENTS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "action_required_examples": action_examples[:25],
        "claim_boundary": (
            "Actual BE, partial-close, and time-in-trade event rows remain in their own logs. "
            "This status lane only proves missing/empty event logs are expected no-event states."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-021 Exit-Management No-Event Status - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Candidate rows considered: `{report['counts']['candidate_rows_considered']}`",
        f"- Status rows available: `{report['counts']['status_rows_available']}`",
        f"- Status rows appended this run: `{report['counts']['status_rows_appended_this_run']}`",
        f"- No-event documented: `{report['counts']['no_event_documented']}`",
        f"- Event rows present: `{report['counts']['event_rows_present']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Status Breakdown",
        "",
        f"- Fill states: `{rolling['fill_state_counts']}`",
        f"- BE statuses: `{rolling['be_shadow_status_counts']}`",
        f"- Partial-close statuses: `{rolling['partial_close_shadow_status_counts']}`",
        f"- Time-in-trade statuses: `{rolling['time_in_trade_shadow_status_counts']}`",
        f"- Documented no-event codes: `{rolling['documented_no_event_code_counts']}`",
        f"- Actual event row totals: `{rolling['actual_event_row_totals']}`",
        "",
        "## Boundary",
        "",
        report["claim_boundary"],
        "",
        "## Safety Counters",
        "",
        f"- no_ai_calls: `{report['no_ai_calls']}`",
        f"- no_canary_required: `{report['no_canary_required']}`",
        f"- no_execution: `{report['no_execution']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--pending", type=Path, default=DEFAULT_PENDING)
    parser.add_argument("--account", type=Path, default=DEFAULT_ACCOUNT)
    parser.add_argument("--broker", type=Path, default=DEFAULT_BROKER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--decision-date-prefix", default=None)
    args = parser.parse_args()

    root = args.root
    event_statuses = {
        event_name: event_file_status(root, Path("shadow_logs") / file_name)
        for event_name, file_name in EVENT_LOG_NAMES.items()
    }
    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_exit_management_status_rows(
        read_jsonl_with_lines(args.candidates),
        pending_rows=read_jsonl_with_lines(args.pending),
        account_rows=read_jsonl_with_lines(args.account),
        broker_rows=read_jsonl_with_lines(args.broker),
        be_event_rows=read_jsonl_with_lines(Path("shadow_logs") / EVENT_LOG_NAMES["be"]),
        partial_event_rows=read_jsonl_with_lines(Path("shadow_logs") / EVENT_LOG_NAMES["partial_close"]),
        time_in_trade_rows=read_jsonl_with_lines(Path("shadow_logs") / EVENT_LOG_NAMES["time_in_trade"]),
        event_log_file_statuses=event_statuses,
        generated_at_utc=generated_at,
        decision_date_prefix=args.decision_date_prefix,
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
                "candidate_rows_considered": report["counts"]["candidate_rows_considered"],
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
