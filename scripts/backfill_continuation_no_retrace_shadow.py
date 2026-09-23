#!/usr/bin/env python3
"""Backfill append-only continuation/no-retrace shadow rows."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.research_infra.continuation_no_retrace import (
    CANDIDATE_SCHEMA_VERSION,
    PREREGISTRATION_VERSION,
    PROMOTION_VERDICT,
    RESOLUTION_SCHEMA_VERSION,
    STRATEGY_ID,
    build_continuation_rows,
    build_report,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_OPPORTUNITIES = Path("shadow_logs/live_candidate_opportunity_clusters.jsonl")
DEFAULT_TRADE_RECORDS = Path("knowledge_base/trade_records")
DEFAULT_CANDIDATE_OUTPUT = Path("shadow_logs/continuation_no_retrace_candidates.jsonl")
DEFAULT_RESOLUTION_OUTPUT = Path("shadow_logs/continuation_no_retrace_resolutions.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.json")
DEFAULT_REPORT_MD = Path("research/program_control/CONTINUATION_NO_RETRACE_AUDIT_2026-05-06.md")


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
                item = json.loads(text)
            except json.JSONDecodeError:
                continue
            if isinstance(item, dict):
                rows.append((line_no, item))
    return rows


def existing_row_keys(path: Path) -> set[str]:
    return {
        str(row.get("row_key"))
        for _, row in read_jsonl_with_lines(path)
        if row.get("row_key")
    }


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> int:
    if not rows:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")
    return len(rows)


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Continuation/No-Retrace Shadow Audit - 2026-05-06",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Strategy:** `{report['strategy_id']}`",
        f"**Preregistration:** `{report['preregistration_version']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Objective",
        "",
        (
            "Build append-only shadow rows for the preregistered "
            "continuation/no-retrace lane without changing the live retest "
            "strategy or loosening `m15_choch_exists`."
        ),
        "",
        "## Counts",
        "",
        f"- Eligible candidates: `{report['counts']['eligible_candidates']}`",
        f"- Candidate rows appended: `{report['counts']['candidate_rows_appended']}`",
        f"- Resolution rows: `{report['counts']['resolution_rows']}`",
        f"- Resolution rows appended: `{report['counts']['resolution_rows_appended']}`",
        f"- Distance proxy available: `{report['counts']['distance_proxy_available']}`",
        "",
        "## Later Path Outcomes",
        "",
        f"`{report['later_path_outcome_counts']}`",
        "",
        "## Aggregate Counting",
        "",
        f"`{report['aggregate_counting_status_counts']}`",
        "",
        "## Source Blockers",
        "",
        f"`{report['source_blocker_counts']}`",
        "",
        "## Skipped",
        "",
        f"`{report['skipped']}`",
        "",
        "## Ambiguity Status",
        "",
        report["ambiguity_status"],
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
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--opportunities", type=Path, default=DEFAULT_OPPORTUNITIES)
    parser.add_argument("--trade-records", type=Path, default=DEFAULT_TRADE_RECORDS)
    parser.add_argument("--candidate-output", type=Path, default=DEFAULT_CANDIDATE_OUTPUT)
    parser.add_argument("--resolution-output", type=Path, default=DEFAULT_RESOLUTION_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--decision-date-prefix", default=None)
    parser.add_argument("--generated-at-utc", default=None)
    args = parser.parse_args()

    generated_at = args.generated_at_utc or datetime.now(timezone.utc).isoformat()
    candidate_rows, resolution_rows, skipped = build_continuation_rows(
        read_jsonl_with_lines(args.candidates),
        generated_at_utc=generated_at,
        trade_records_root=args.trade_records,
        path_rows=read_jsonl_with_lines(args.paths),
        opportunity_rows=read_jsonl_with_lines(args.opportunities),
        decision_date_prefix=args.decision_date_prefix,
    )

    seen_candidates = existing_row_keys(args.candidate_output)
    seen_resolutions = existing_row_keys(args.resolution_output)
    append_candidates = [row for row in candidate_rows if str(row.get("row_key")) not in seen_candidates]
    append_resolutions = [row for row in resolution_rows if str(row.get("row_key")) not in seen_resolutions]
    appended_candidate_count = append_jsonl(args.candidate_output, append_candidates)
    appended_resolution_count = append_jsonl(args.resolution_output, append_resolutions)

    report = build_report(
        candidate_rows,
        resolution_rows,
        appended_candidates=appended_candidate_count,
        appended_resolutions=appended_resolution_count,
        skipped=skipped,
        candidate_output_path=str(args.candidate_output),
        resolution_output_path=str(args.resolution_output),
    )
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "strategy_id": STRATEGY_ID,
                "preregistration_version": PREREGISTRATION_VERSION,
                "candidate_schema": CANDIDATE_SCHEMA_VERSION,
                "resolution_schema": RESOLUTION_SCHEMA_VERSION,
                "counts": report["counts"],
                "report_json": str(args.report_json),
                "report_md": str(args.report_md),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
