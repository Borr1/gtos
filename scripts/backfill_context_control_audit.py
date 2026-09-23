#!/usr/bin/env python3
"""Backfill append-only context/control audit rows."""

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

from src.research_infra.context_control_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_context_control_audit_rows,
    build_rolling_status,
)


DEFAULT_CONTEXT = Path("shadow_logs/context_control_ledger.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/context_control_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO009_CONTEXT_CONTROL_AUDIT_2026-05-05.md")


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
    status_counts = Counter(str(row.get("context_control_audit_status") or "UNKNOWN") for row in rows)
    action_examples = [
        {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "action_required_codes": row.get("action_required_codes") or [],
            "direct_validation_problem_paths": row.get("direct_validation_problem_paths") or [],
        }
        for row in rows
        if row.get("context_control_audit_status") == ACTION_REQUIRED
    ]
    limitation_examples = [
        {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "documented_limitation_codes": row.get("documented_limitation_codes") or [],
        }
        for row in rows
        if row.get("context_control_audit_status") == COMPLETE_WITH_LIMITATIONS
    ]
    return {
        "schema_version": "lto009_context_control_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_CONTEXT_CONTROL_LIMITATIONS",
        "audit_log_path": str(output_path),
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "context_rows_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "audit_rows_appended_this_run": len(appended_rows),
            "audit_rows_available": len(read_jsonl_with_lines(output_path)),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "action_required_examples": action_examples[:25],
        "limitation_examples": limitation_examples[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-009 Context/Control Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Context rows considered: `{report['counts']['context_rows_considered']}`",
        f"- Audit rows available: `{report['counts']['audit_rows_available']}`",
        f"- Audit rows appended this run: `{report['counts']['audit_rows_appended_this_run']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Control Boundary",
        "",
        f"- Control-only rows: `{rolling['control_only_rows']}`",
        f"- No-promotion rows: `{rolling['no_promotion_rows']}`",
        f"- Direct strategy-validation status counts: `{rolling['direct_strategy_validation_status_counts']}`",
        f"- Source evidence-class counts: `{rolling['source_evidence_class_counts']}`",
        "",
        "## Context Families",
        "",
        f"`{rolling['context_family_source_status_counts']}`",
        "",
        "## Exploratory Outcomes",
        "",
        f"`{rolling['exploratory_outcome_label_counts']}`",
        "",
        "## Limitations",
        "",
        "- Existing CL/ZN/VIX/VXM point-in-time values are not captured in the current 2026-05-04 context rows.",
        "- Existing rows remain usable only as control/exploratory context, not direct strategy validation.",
        "- Legacy rows use `CROSS_INSTRUMENT_CONTEXT`; audit rows normalize them to `CONTROL_ONLY` without rewriting the source log.",
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
    parser.add_argument("--context-log", type=Path, default=DEFAULT_CONTEXT)
    parser.add_argument("--path-log", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--decision-date-prefix", default=None)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_context_control_audit_rows(
        read_jsonl_with_lines(args.context_log),
        read_jsonl_with_lines(args.path_log),
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
                "context_rows_considered": report["counts"]["context_rows_considered"],
                "audit_rows_appended": len(appended),
                "audit_rows_available": report["counts"]["audit_rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
