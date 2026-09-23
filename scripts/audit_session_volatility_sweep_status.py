#!/usr/bin/env python3
"""Backfill and audit LTO-022 session-volatility/sweep status rows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.session_volatility_sweep_status import (  # noqa: E402
    ACTION_REQUIRED,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    append_missing_no_event_rows,
    build_rolling_status,
    build_status_rows,
    target_previous_utc_date,
)


DEFAULT_OUTPUT = Path("shadow_logs/session_volatility_sweep_status.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO022_SESSION_VOLATILITY_SWEEP_STATUS_2026-05-05.md")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(row, dict):
                rows.append(row)
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {str(row.get("row_key")) for row in read_jsonl(path) if row.get("row_key")}


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build_report(
    rows: list[dict[str, Any]],
    *,
    target_date: date,
    output_path: Path,
    appended_rows: list[dict[str, Any]],
    no_event_rows_written: dict[str, int],
) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    action_rows = [row for row in rows if row.get("coverage_status") == ACTION_REQUIRED]
    return {
        "schema_version": "lto022_session_volatility_sweep_status_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_rows else "OK_SESSION_VOL_SWEEP_STATUS_DOCUMENTED",
        "status_log_path": str(output_path),
        "status_log_schema": SCHEMA_VERSION,
        "target_date": target_date.isoformat(),
        "counts": {
            "status_rows_built": len(rows),
            "status_rows_appended_this_run": len(appended_rows),
            "status_rows_available": len(read_jsonl(output_path)),
            "action_required": len(action_rows),
            "event_rows": rolling["event_row_total"],
            "no_event_rows": rolling["no_event_row_total"],
        },
        "no_event_rows_written": no_event_rows_written,
        "rolling_status": rolling,
        "rows": rows,
        "action_required_examples": action_rows[:20],
        "claim_boundary": (
            "This audit proves H25/H16 monitor cadence and explicit event/no-event "
            "coverage for the configured symbol/session/date lanes. It does not "
            "validate a strategy edge or change trading decisions."
        ),
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-022 Session Volatility / Sweep Status - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        f"**Target date:** `{report['target_date']}`",
        "",
        "## Counts",
        "",
        f"- Status rows built: `{report['counts']['status_rows_built']}`",
        f"- Status rows available: `{report['counts']['status_rows_available']}`",
        f"- Status rows appended this run: `{report['counts']['status_rows_appended_this_run']}`",
        f"- Event rows: `{report['counts']['event_rows']}`",
        f"- No-event rows: `{report['counts']['no_event_rows']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        f"- CSV no-event rows written: `{report['no_event_rows_written']}`",
        "",
        "## Status Breakdown",
        "",
        f"- Coverage status counts: `{rolling['coverage_status_counts']}`",
        f"- Source counts: `{rolling['source_counts']}`",
        f"- Source-file status counts: `{rolling['source_file_status_counts']}`",
        f"- Action-required codes: `{rolling['action_required_code_counts']}`",
        "",
        "## Source Rows",
        "",
    ]
    for row in report["rows"]:
        lines.append(
            "- "
            f"`{row['source_name']}` `{row['target_date']}`: "
            f"coverage `{row['coverage_status']}`, events `{row['event_row_count']}`, "
            f"no-events `{row['no_event_row_count']}`, latest run `{row['latest_run_time_utc']}`"
        )
    lines.extend(
        [
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
    )
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--date", default=None, help="Target date to audit (YYYY-MM-DD). Default: previous UTC date.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--skip-no-event-backfill", action="store_true")
    args = parser.parse_args()

    target_date = date.fromisoformat(args.date) if args.date else target_previous_utc_date()
    root = args.root
    output = args.output if args.output.is_absolute() else root / args.output
    report_json = args.report_json if args.report_json.is_absolute() else root / args.report_json
    report_md = args.report_md if args.report_md.is_absolute() else root / args.report_md

    written = {"session_volatility_log.csv": 0, "sweep_divergence_log.csv": 0}
    if not args.skip_no_event_backfill:
        written = append_missing_no_event_rows(root, target_date)

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_status_rows(root=root, target_date=target_date, generated_at_utc=generated_at)
    existing = existing_row_keys(output)
    appended = [row for row in rows if str(row.get("row_key")) not in existing]
    append_jsonl(output, appended)

    report = build_report(
        rows,
        target_date=target_date,
        output_path=output,
        appended_rows=appended,
        no_event_rows_written=written,
    )
    report_json.parent.mkdir(parents=True, exist_ok=True)
    report_json.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_markdown(report, report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "target_date": report["target_date"],
                "status_rows_appended": len(appended),
                "status_rows_available": report["counts"]["status_rows_available"],
                "action_required": report["counts"]["action_required"],
                "no_event_rows_written": written,
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
