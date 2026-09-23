#!/usr/bin/env python3
"""Backfill append-only candidate path-follow contract audit rows."""

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

from src.research_infra.candidate_path_contract import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_candidate_path_contract_rows,
)
from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate


DEFAULT_PATH_ROWS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_LTF_ROWS = Path("shadow_logs/candidate_ltf_path_order.jsonl")
DEFAULT_OUTPUT = Path("shadow_logs/candidate_path_contract_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO003_CANDIDATE_PATH_CONTRACT_AUDIT_2026-05-05.md")


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


def latest_ltf_by_candidate(path: Path) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(read_jsonl_with_lines(path))


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
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def build_report(rows: list[dict[str, Any]], appended_rows: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    status_counts = Counter(str(row.get("path_contract_status") or "UNKNOWN") for row in rows)
    limitation_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    for row in rows:
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])
    action_examples = [
        {"candidate_id": row.get("candidate_id"), "action_required_codes": row.get("action_required_codes") or []}
        for row in rows
        if row.get("path_contract_status") == ACTION_REQUIRED
    ][:25]
    return {
        "schema_version": "lto003_candidate_path_contract_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_PATH_LIMITATIONS",
        "audit_log_path": str(output_path),
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "path_candidates_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "path_contract_status_counts": dict(status_counts),
        "documented_limitation_counts": dict(limitation_counts),
        "action_required_counts": dict(action_counts),
        "action_required_examples": action_examples,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# LTO-003 Candidate Path Contract Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Path candidates considered: `{report['counts']['path_candidates_considered']}`",
        f"- Audit rows appended: `{report['counts']['audit_rows_appended']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Status Counts",
        "",
        f"`{report['path_contract_status_counts']}`",
        "",
        "## Documented Limitation Counts",
        "",
        f"`{report['documented_limitation_counts']}`",
        "",
        "## Action Required Counts",
        "",
        f"`{report['action_required_counts']}`",
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
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATH_ROWS)
    parser.add_argument("--ltf-paths", type=Path, default=DEFAULT_LTF_ROWS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    rows = build_candidate_path_contract_rows(
        read_jsonl_with_lines(args.paths),
        generated_at_utc=generated_at,
        ltf_rows_by_candidate=latest_ltf_by_candidate(args.ltf_paths),
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
