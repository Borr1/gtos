#!/usr/bin/env python3
"""Append recovered FVG/OB exact geometry to forward confluence rows.

This is research/shadow repair only. It reads existing decision-time candidate
rows and appends enriched ``fvg_ob_confluence`` rows when exact FVG/OB bounds
can be recovered from the candidate's captured MSO snapshot. It does not call
AI, MT5, canaries, broker/order APIs, or paid data sources.
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

from src.research_infra.evidence_selection import latest_by_candidate
from src.research_infra.forward_capture import (
    PROMOTION_VERDICT,
    fvg_ob_geometry_from_candidate_row,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_CONFLUENCE = Path("shadow_logs/fvg_ob_confluence.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.json")
DEFAULT_REPORT_MD = Path("research/program_control/FVG_OB_CONFLUENCE_SOURCE_GEOMETRY_BACKFILL_2026-05-12.md")

EXACT_GEOMETRY_STATUSES = {
    "FVG_AND_OB_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO",
    "FVG_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO",
    "OB_EXACT_BOUNDS_MATCHED_FROM_DECISION_MSO",
}
MANUAL_BACKFILL_STATUS = "FVG_OB_EXACT_GEOMETRY_RECOVERED_FROM_STRATEGY_FOLLOW_DECISION_MSO"
NO_LEAK_STATUS = "DECISION_TIME_MSO_ONLY_NO_POST_OUTCOME_FIELDS"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            row = json.loads(text)
            if isinstance(row, dict):
                row["_line_no"] = line_no
                rows.append(row)
    return rows


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def _has_exact_geometry(row: dict[str, Any]) -> bool:
    return bool(row.get("fvg_bounds") or row.get("ob_bounds"))


def summarize_existing_recovered_geometry(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    count = 0
    for row in rows:
        if row.get("manual_backfill_status") != MANUAL_BACKFILL_STATUS:
            continue
        if row.get("geometry_recovery_no_leak_status") != NO_LEAK_STATUS:
            continue
        if not _has_exact_geometry(row):
            continue
        count += 1
        source_status = str(row.get("exact_geometry_source_status") or "UNKNOWN")
        status_counts[source_status] += 1
        if len(examples) < 20:
            examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "symbol": row.get("symbol"),
                    "decision_time_utc": row.get("decision_time_utc"),
                    "exact_geometry_source_status": source_status,
                    "fvg_bounds": row.get("fvg_bounds"),
                    "ob_bounds": row.get("ob_bounds"),
                }
            )
    return {
        "rows": count,
        "status_counts": dict(sorted(status_counts.items())),
        "examples": examples,
    }


def build_enriched_confluence_rows(
    *,
    confluence_rows: list[dict[str, Any]],
    candidate_rows: list[dict[str, Any]],
    generated_at_utc: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates = latest_by_candidate(candidate_rows)
    confluence = latest_by_candidate(confluence_rows)
    status_counts: Counter[str] = Counter()
    examples: list[dict[str, Any]] = []
    enriched: list[dict[str, Any]] = []

    for candidate_id, row in sorted(confluence.items()):
        if _has_exact_geometry(row):
            status_counts["already_exact_geometry"] += 1
            continue
        candidate = candidates.get(candidate_id)
        if not candidate:
            status_counts["candidate_source_missing"] += 1
            continue
        geometry = fvg_ob_geometry_from_candidate_row(candidate)
        source_status = str(geometry.get("exact_geometry_source_status") or "")
        if source_status not in EXACT_GEOMETRY_STATUSES:
            status_counts[source_status or "geometry_not_recovered"] += 1
            continue

        repaired = {
            key: value
            for key, value in row.items()
            if key != "_line_no"
        }
        repaired.update(
            {
                **geometry,
                "created_at_utc": generated_at_utc,
                "backfilled_at_utc": generated_at_utc,
                "manual_backfill_status": MANUAL_BACKFILL_STATUS,
                "geometry_recovery_source": "strategy_follow_candidates.decision_time_structural_fields",
                "geometry_recovery_source_candidate_created_at_utc": candidate.get("created_at_utc"),
                "geometry_recovery_no_leak_status": NO_LEAK_STATUS,
                "promotion_verdict": PROMOTION_VERDICT,
                "no_ai_calls": True,
                "no_canary_required": True,
                "no_execution": True,
                "paid_fetch_attempted": False,
                "paid_data_calls": 0,
            }
        )
        enriched.append(repaired)
        status_counts["enriched_rows"] += 1
        if len(examples) < 20:
            examples.append(
                {
                    "candidate_id": candidate_id,
                    "symbol": repaired.get("symbol"),
                    "decision_time_utc": repaired.get("decision_time_utc"),
                    "exact_geometry_source_status": source_status,
                    "fvg_bounds": repaired.get("fvg_bounds"),
                    "ob_bounds": repaired.get("ob_bounds"),
                }
            )

    summary = {
        "candidate_rows_available": len(candidate_rows),
        "confluence_latest_candidates": len(confluence),
        "status_counts": dict(sorted(status_counts.items())),
        "examples": examples,
        "existing_recovered_geometry": summarize_existing_recovered_geometry(confluence_rows),
    }
    return enriched, summary


def write_report(report: dict[str, Any], json_path: Path, md_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# FVG/OB Confluence Source Geometry Backfill - 2026-05-12",
        "",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Candidate rows available: `{report['summary']['candidate_rows_available']}`",
        f"- Latest confluence candidates: `{report['summary']['confluence_latest_candidates']}`",
        f"- Existing recovered geometry rows: `{report['summary']['existing_recovered_geometry']['rows']}`",
        f"- Rows appended: `{report['rows_appended']}`",
        "",
        "## Status Counts",
        "",
        f"`{report['summary']['status_counts']}`",
        "",
        "## Examples",
        "",
        f"`{report['summary']['examples']}`",
        "",
        "## Safety",
        "",
        f"- No AI calls: `{report['no_ai_calls']}`",
        f"- No canary required: `{report['no_canary_required']}`",
        f"- No execution: `{report['no_execution']}`",
        f"- Paid fetch attempted: `{report['paid_fetch_attempted']}`",
        f"- Paid data calls: `{report['paid_data_calls']}`",
    ]
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--confluence", type=Path, default=DEFAULT_CONFLUENCE)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows, summary = build_enriched_confluence_rows(
        confluence_rows=read_jsonl(args.confluence),
        candidate_rows=read_jsonl(args.candidates),
        generated_at_utc=generated_at,
    )
    if not args.dry_run:
        append_jsonl(args.confluence, rows)
    report = {
        "schema_version": "fvg_ob_confluence_source_geometry_backfill_v1",
        "generated_at_utc": generated_at,
        "status": (
            "OK_RESEARCH_GEOMETRY_BACKFILL_APPENDED"
            if rows
            else (
                "OK_GEOMETRY_RECOVERY_PRESENT_NO_APPENDABLE_ROWS"
                if summary["existing_recovered_geometry"]["rows"]
                else "OK_NO_APPENDABLE_GEOMETRY_ROWS"
            )
        ),
        "promotion_verdict": PROMOTION_VERDICT,
        "confluence_log_path": str(args.confluence),
        "candidate_log_path": str(args.candidates),
        "dry_run": bool(args.dry_run),
        "rows_appended": 0 if args.dry_run else len(rows),
        "rows_appendable": len(rows),
        "summary": summary,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }
    write_report(report, args.report_json, args.report_md)
    print(json.dumps({"status": report["status"], "rows_appendable": len(rows), "rows_appended": report["rows_appended"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
