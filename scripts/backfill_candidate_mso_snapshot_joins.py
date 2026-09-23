#!/usr/bin/env python3
"""Backfill candidate-to-MSO decision-time snapshot joins.

This is append-only research tooling. It reads existing shadow rows, joins
candidate rows to exact same-symbol/same-decision-time pre-AI MSO rows, writes
new join rows only for row_keys not already present, and emits a summary report.
It does not call AI, canary checks, MT5, broker order APIs, or paid data.
"""

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

from src.research_infra.mso_snapshot_join import (
    JOIN_MISSING,
    JOIN_SCHEMA_VERSION,
    JOINED_EXACT,
    PROMOTION_VERDICT,
    build_candidate_mso_join_rows,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_EVALUATIONS = Path("shadow_logs/strategy_follow_evaluations.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/candidate_mso_snapshot_joins.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO001_MSO_SNAPSHOT_JOIN_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO001_MSO_SNAPSHOT_JOIN_AUDIT_2026-05-05.md")


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            rows.append((line_no, json.loads(text)))
    return rows


def existing_row_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for _, row in read_jsonl_with_lines(path):
        key = row.get("row_key")
        if key:
            keys.add(str(key))
    return keys


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    join_status_counts = Counter(str(row.get("join_status") or "UNKNOWN") for row in rows)
    comparison_counts = Counter(str(row.get("context_comparison_status") or "UNKNOWN") for row in rows)
    missing = [
        {
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "decision_time_utc": row.get("decision_time_utc"),
            "nearest_mso_delta_seconds": row.get("nearest_mso_delta_seconds"),
            "nearest_mso_candidate_id": row.get("nearest_mso_candidate_id"),
        }
        for row in rows
        if row.get("join_status") == JOIN_MISSING
    ]
    mismatches = [
        {
            "candidate_id": row.get("candidate_id"),
            "context_mismatches": row.get("context_mismatches") or [],
        }
        for row in rows
        if row.get("context_mismatches")
    ]
    return {
        "schema_version": "lto001_mso_snapshot_join_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if mismatches else "OK_WITH_DOCUMENTED_MSO_JOIN_LIMITATIONS",
        "join_log_path": str(output_path),
        "join_log_schema": JOIN_SCHEMA_VERSION,
        "counts": {
            "candidate_rows_considered": len(rows),
            "join_rows_appended": len(appended_rows),
            "joined_exact": join_status_counts.get(JOINED_EXACT, 0),
            "mso_join_missing": join_status_counts.get(JOIN_MISSING, 0),
            "context_mismatches": len(mismatches),
        },
        "join_status_counts": dict(join_status_counts),
        "context_comparison_status_counts": dict(comparison_counts),
        "mso_join_missing_candidates": missing,
        "context_mismatch_examples": mismatches[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# LTO-001 MSO Snapshot Join Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Candidate rows considered: `{report['counts']['candidate_rows_considered']}`",
        f"- Join rows appended: `{report['counts']['join_rows_appended']}`",
        f"- Joined exact MSO snapshots: `{report['counts']['joined_exact']}`",
        f"- MSO join missing rows: `{report['counts']['mso_join_missing']}`",
        f"- Context mismatches: `{report['counts']['context_mismatches']}`",
        "",
        "## Join Status Counts",
        "",
        f"`{report['join_status_counts']}`",
        "",
        "## Context Comparison Status Counts",
        "",
        f"`{report['context_comparison_status_counts']}`",
        "",
        "## Missing MSO Join Candidates",
        "",
    ]
    if report["mso_join_missing_candidates"]:
        for item in report["mso_join_missing_candidates"]:
            lines.append(
                "- `{candidate_id}` `{symbol}` `{decision_time_utc}` nearest_delta=`{nearest_mso_delta_seconds}` nearest=`{nearest_mso_candidate_id}`".format(
                    **item
                )
            )
    else:
        lines.append("None.")
    lines.extend(
        [
            "",
            "## Safety",
            "",
            f"- No AI calls: `{report['no_ai_calls']}`",
            f"- No canary required: `{report['no_canary_required']}`",
            f"- No execution: `{report['no_execution']}`",
            f"- Paid fetch attempted: `{report['paid_fetch_attempted']}`",
            f"- Paid data calls: `{report['paid_data_calls']}`",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--evaluations", type=Path, default=DEFAULT_EVALUATIONS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--decision-date-prefix", default=None)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    candidates = read_jsonl_with_lines(args.candidates)
    evaluations = read_jsonl_with_lines(args.evaluations)
    rows = build_candidate_mso_join_rows(
        candidates,
        evaluations,
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
                "join_log_path": report["join_log_path"],
                "report_json": str(args.report_json),
                "report_md": str(args.report_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
