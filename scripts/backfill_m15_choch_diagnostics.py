#!/usr/bin/env python3
"""Backfill append-only diagnostics for m15_choch_exists L2 failures."""

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

from src.research_infra.m15_choch_diagnostics import (
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_m15_choch_diagnostic_rows,
    build_report,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_OPPORTUNITIES = Path("shadow_logs/live_candidate_opportunity_clusters.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/m15_choch_diagnostic_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.json")
DEFAULT_REPORT_MD = Path("research/program_control/M15_CHOCH_DIAGNOSTIC_AUDIT_2026-05-06.md")


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


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":"), default=str) + "\n")


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# M15 CHoCH Diagnostic Audit - 2026-05-06",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Objective",
        "",
        (
            "Expand diagnostics for `m15_choch_exists` failures by joining the "
            "decision-time L2 reason to later path and opportunity evidence. This "
            "does not loosen the gate or change live execution."
        ),
        "",
        "## Counts",
        "",
        f"- M15 CHoCH failures considered: `{report['counts']['m15_choch_failures_considered']}`",
        f"- Audit rows appended: `{report['counts']['audit_rows_appended']}`",
        f"- Joined to latest path: `{report['counts']['joined_to_latest_path']}`",
        f"- Waiting for path: `{report['counts']['waiting_for_path']}`",
        "",
        "## Later Path Outcomes",
        "",
        f"`{report['later_path_outcome_counts']}`",
        "",
        "## Gate Interpretation",
        "",
        f"`{report['gate_interpretation_counts']}`",
        "",
        "## Opportunity Counting",
        "",
        f"`{report['opportunity_counting_status_counts']}`",
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
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument(
        "--decision-date-prefix",
        default=None,
        help="Optional ISO date prefix such as 2026-05-05.",
    )
    parser.add_argument(
        "--generated-at-utc",
        default=None,
        help="Optional fixed timestamp for deterministic tests.",
    )
    args = parser.parse_args()

    generated_at = args.generated_at_utc or datetime.now(timezone.utc).isoformat()
    rows = build_m15_choch_diagnostic_rows(
        read_jsonl_with_lines(args.candidates),
        generated_at_utc=generated_at,
        path_rows=read_jsonl_with_lines(args.paths),
        opportunity_rows=read_jsonl_with_lines(args.opportunities),
        decision_date_prefix=args.decision_date_prefix,
    )
    seen = existing_row_keys(args.output)
    append_rows = [row for row in rows if str(row.get("row_key")) not in seen]
    append_jsonl(args.output, append_rows)

    report = build_report(rows, append_rows, str(args.output))
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(report, indent=2, sort_keys=True, default=str), encoding="utf-8")
    write_markdown(report, args.report_md)

    print(
        json.dumps(
            {
                "status": report["status"],
                "promotion_verdict": PROMOTION_VERDICT,
                "audit_log_schema": SCHEMA_VERSION,
                "counts": report["counts"],
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
