#!/usr/bin/env python3
"""Backfill append-only pending-limit lifecycle contract audit rows."""

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

from src.research_infra.pending_limit_lifecycle_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    PROMOTION_VERDICT,
    SCHEMA_VERSION,
    build_pending_limit_lifecycle_audit_rows,
    read_persisted_pending_intents,
)
from src.research_infra.trade_record_candidate_backfill import (
    DEFAULT_TRADE_RECORD_ROOT,
    iter_trade_record_candidates,
)


DEFAULT_CANDIDATES = Path("shadow_logs/strategy_follow_candidates.jsonl")
DEFAULT_LIFECYCLE = Path("shadow_logs/pending_limit_lifecycle.jsonl")
DEFAULT_JOIN = Path("shadow_logs/pending_limit_lifecycle_join_backfill.jsonl")
DEFAULT_PATHS = Path("shadow_logs/candidate_path_follow.jsonl")
DEFAULT_LTF = Path("shadow_logs/candidate_ltf_path_order.jsonl")
DEFAULT_ACCOUNT_TRUTH = Path("shadow_logs/account_truth_reconciliation_status.jsonl")
DEFAULT_PENDING_META = Path("knowledge_base/meta")
DEFAULT_OUTPUT = Path("shadow_logs/pending_limit_lifecycle_audit.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO005_PENDING_LIMIT_LIFECYCLE_AUDIT_2026-05-05.md")
VOLATILE_APPEND_FIELDS = {"created_at_utc", "backfilled_at_utc"}


def read_jsonl_with_lines(path: Path, issues: list[dict[str, Any]] | None = None) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, start=1):
            text = line.strip()
            if text:
                try:
                    rows.append((line_no, json.loads(text)))
                except json.JSONDecodeError as exc:
                    if issues is not None:
                        issues.append(
                            {
                                "path": str(path),
                                "line_no": line_no,
                                "error": str(exc),
                                "snippet": text[:240],
                            }
                        )
    return rows


def existing_rows_by_key(path: Path, issues: list[dict[str, Any]] | None = None) -> dict[str, dict[str, Any]]:
    return {str(row.get("row_key")): row for _, row in read_jsonl_with_lines(path, issues) if row.get("row_key")}


def dedupe_jsonl_issues(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, int, str, str]] = set()
    for issue in issues:
        key = (
            str(issue.get("path") or ""),
            int(issue.get("line_no") or 0),
            str(issue.get("error") or ""),
            str(issue.get("snippet") or ""),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(issue)
    return deduped


def row_changed(existing: dict[str, Any] | None, computed: dict[str, Any]) -> bool:
    if existing is None:
        return True
    keys = (set(existing) | set(computed)) - VOLATILE_APPEND_FIELDS
    return any(existing.get(key) != computed.get(key) for key in keys)


def append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n")


def latest_decision_date_prefix(candidate_rows: list[tuple[int, dict[str, Any]]]) -> str | None:
    prefixes = sorted(
        {
            str(row.get("decision_time_utc") or "")[:10]
            for _, row in candidate_rows
            if len(str(row.get("decision_time_utc") or "")) >= 10
        }
    )
    return prefixes[-1] if prefixes else None


def build_report(
    rows: list[dict[str, Any]],
    appended_rows: list[dict[str, Any]],
    output_path: Path,
    *,
    audit_rows_available: int,
    source_jsonl_issues: list[dict[str, Any]],
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("pending_limit_lifecycle_audit_status") or "UNKNOWN") for row in rows)
    final_counts = Counter(str(row.get("final_state") or "UNKNOWN") for row in rows)
    final_status_counts = Counter(str(row.get("final_state_status") or "UNKNOWN") for row in rows)
    uniqueness_counts = Counter(str(row.get("trade_id_global_uniqueness_status") or "UNKNOWN") for row in rows)
    match_counts = Counter(str(row.get("candidate_match_status") or "UNKNOWN") for row in rows)
    trade_record_match_counts = Counter(str(row.get("trade_record_match_status") or "UNKNOWN") for row in rows)
    limitation_counts: Counter[str] = Counter()
    action_counts: Counter[str] = Counter()
    action_examples: list[dict[str, Any]] = []
    unjoinable_examples: list[dict[str, Any]] = []
    collision_examples: list[dict[str, Any]] = []
    for row in rows:
        limitation_counts.update(row.get("documented_limitation_codes") or [])
        action_counts.update(row.get("action_required_codes") or [])
        if row.get("pending_limit_lifecycle_audit_status") == ACTION_REQUIRED:
            action_examples.append(
                {
                    "candidate_id": row.get("candidate_id"),
                    "raw_trade_id": row.get("raw_trade_id"),
                    "symbol": row.get("symbol"),
                    "action_required_codes": row.get("action_required_codes") or [],
                }
            )
        if row.get("candidate_match_status") == "NO_SHADOW_CANDIDATE_MATCH" and row.get("trade_record_match_status") == "NO_TRADE_RECORD_MATCH":
            unjoinable_examples.append(
                {
                    "raw_trade_id": row.get("raw_trade_id"),
                    "symbol": row.get("symbol"),
                    "pending_intent_global_key": row.get("pending_intent_global_key"),
                }
            )
        if row.get("raw_trade_id_collision_symbols"):
            collision_examples.append(
                {
                    "raw_trade_id": row.get("raw_trade_id"),
                    "symbol": row.get("symbol"),
                    "collision_symbols": row.get("raw_trade_id_collision_symbols"),
                    "pending_intent_global_key": row.get("pending_intent_global_key"),
                }
            )

    return {
        "schema_version": "lto005_pending_limit_lifecycle_audit_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": "ACTION_REQUIRED" if action_examples or source_jsonl_issues else "OK_WITH_DOCUMENTED_PENDING_LIFECYCLE_LIMITATIONS",
        "audit_log_path": str(output_path),
        "audit_log_schema": SCHEMA_VERSION,
        "counts": {
            "lifecycle_groups_considered": len(rows),
            "audit_rows_appended": len(appended_rows),
            "audit_rows_appended_this_run": len(appended_rows),
            "audit_rows_available": audit_rows_available,
            "source_jsonl_issue_count": len(source_jsonl_issues),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "pending_limit_lifecycle_audit_status_counts": dict(status_counts),
        "final_state_counts": dict(final_counts),
        "final_state_status_counts": dict(final_status_counts),
        "trade_id_global_uniqueness_status_counts": dict(uniqueness_counts),
        "candidate_match_status_counts": dict(match_counts),
        "trade_record_match_status_counts": dict(trade_record_match_counts),
        "documented_limitation_counts": dict(limitation_counts),
        "action_required_counts": dict(action_counts),
        "raw_trade_id_collision_examples": collision_examples[:25],
        "unjoinable_lifecycle_examples": unjoinable_examples[:25],
        "action_required_examples": action_examples[:25],
        "source_jsonl_issues": source_jsonl_issues[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# LTO-005 Pending-Limit Lifecycle Audit - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Lifecycle groups considered: `{report['counts']['lifecycle_groups_considered']}`",
        f"- Audit rows available: `{report['counts']['audit_rows_available']}`",
        f"- Audit rows appended this run: `{report['counts']['audit_rows_appended_this_run']}`",
        f"- Source JSONL issues: `{report['counts']['source_jsonl_issue_count']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Final States",
        "",
        f"`{report['final_state_counts']}`",
        "",
        "## Candidate And Trade-Record Matches",
        "",
        f"- Candidate match statuses: `{report['candidate_match_status_counts']}`",
        f"- Trade-record match statuses: `{report['trade_record_match_status_counts']}`",
        "",
        "## Raw Trade ID Uniqueness",
        "",
        f"- Status counts: `{report['trade_id_global_uniqueness_status_counts']}`",
        f"- Collision examples: `{report['raw_trade_id_collision_examples']}`",
        "",
        "## Documented Limitation Counts",
        "",
        f"`{report['documented_limitation_counts']}`",
        "",
        "## Action Required Counts",
        "",
        f"`{report['action_required_counts']}`",
        "",
        "## Source JSONL Issues",
        "",
        f"`{report['source_jsonl_issues']}`",
        "",
        "## Unjoinable Lifecycle Examples",
        "",
        f"`{report['unjoinable_lifecycle_examples']}`",
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
    parser.add_argument("--lifecycle", type=Path, default=DEFAULT_LIFECYCLE)
    parser.add_argument("--join-backfill", type=Path, default=DEFAULT_JOIN)
    parser.add_argument("--paths", type=Path, default=DEFAULT_PATHS)
    parser.add_argument("--ltf-paths", type=Path, default=DEFAULT_LTF)
    parser.add_argument("--account-truth", type=Path, default=DEFAULT_ACCOUNT_TRUTH)
    parser.add_argument("--trade-record-root", type=Path, default=DEFAULT_TRADE_RECORD_ROOT)
    parser.add_argument("--pending-meta", type=Path, default=DEFAULT_PENDING_META)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--decision-date-prefix",
        default="latest",
        help="Use a YYYY-MM-DD prefix, 'latest' for the latest candidate date, or 'all' for all historical source rows.",
    )
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    jsonl_issues: list[dict[str, Any]] = []
    candidate_rows = read_jsonl_with_lines(args.candidates, jsonl_issues)
    if str(args.decision_date_prefix).lower() == "latest":
        decision_date_prefix = latest_decision_date_prefix(candidate_rows)
    elif str(args.decision_date_prefix).lower() in {"all", "none", ""}:
        decision_date_prefix = None
    else:
        decision_date_prefix = args.decision_date_prefix
    trade_records, trade_record_skipped = iter_trade_record_candidates(args.trade_record_root)
    lifecycle_rows = read_jsonl_with_lines(args.lifecycle, jsonl_issues)
    join_rows = read_jsonl_with_lines(args.join_backfill, jsonl_issues)
    path_rows = read_jsonl_with_lines(args.paths, jsonl_issues)
    ltf_rows = read_jsonl_with_lines(args.ltf_paths, jsonl_issues)
    account_truth_rows = read_jsonl_with_lines(args.account_truth, jsonl_issues)
    rows = build_pending_limit_lifecycle_audit_rows(
        candidate_rows,
        lifecycle_rows,
        generated_at_utc=generated_at,
        join_rows=join_rows,
        path_rows=path_rows,
        ltf_rows=ltf_rows,
        trade_record_candidates=trade_records,
        account_truth_rows=account_truth_rows,
        persisted_pending_intents=read_persisted_pending_intents(args.pending_meta),
        decision_date_prefix=decision_date_prefix,
    )
    existing = existing_rows_by_key(args.output, jsonl_issues)
    append_rows = [row for row in rows if row_changed(existing.get(str(row.get("row_key"))), row)]
    append_jsonl(args.output, append_rows)

    audit_rows_available = len(read_jsonl_with_lines(args.output, jsonl_issues))
    report = build_report(
        rows,
        append_rows,
        args.output,
        audit_rows_available=audit_rows_available,
        source_jsonl_issues=dedupe_jsonl_issues(jsonl_issues),
    )
    report["trade_record_skipped"] = trade_record_skipped
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
