#!/usr/bin/env python3
"""Backfill LTO-026 trade-record inventory index and lifecycle audit rows."""

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

from src.research_infra.trade_index_lifecycle_audit import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_BLOCKERS,
    INDEX_SCHEMA_VERSION,
    PROMOTION_VERDICT,
    REPORT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    build_inventory_index,
    build_rolling_status,
    build_trade_index_lifecycle_rows,
    read_json,
    read_jsonl_with_lines,
    read_trade_records,
)


DEFAULT_TRADE_RECORD_ROOT = Path("knowledge_base/trade_records")
DEFAULT_LEGACY_INDEX = Path("knowledge_base/index/_trade_index.json")
DEFAULT_PENDING_AUDIT = Path("shadow_logs/pending_limit_lifecycle_audit.jsonl")
DEFAULT_AUDIT_LOG = Path("shadow_logs/trade_index_lifecycle_audit.jsonl")
DEFAULT_INVENTORY_INDEX = Path("knowledge_base/index/trade_record_inventory_index_2026-05-05.json")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO026_TRADE_INDEX_LIFECYCLE_COMPLETENESS_2026-05-05.md")
VOLATILE_APPEND_FIELDS = {"created_at_utc", "backfilled_at_utc"}


def existing_rows_by_key(path: Path) -> dict[str, dict[str, Any]]:
    return {str(row.get("row_key")): row for _line, row in read_jsonl_with_lines(path) if row.get("row_key")}


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


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_report(
    *,
    rows: list[dict[str, Any]],
    appended: list[dict[str, Any]],
    legacy_index: dict[str, Any] | None,
    audit_log_path: Path,
    inventory_index_path: Path,
) -> dict[str, Any]:
    rolling = build_rolling_status(rows, legacy_index=legacy_index)
    status_counts = Counter(str(row.get("trade_index_lifecycle_status") or "UNKNOWN") for row in rows)
    action_examples = [
        {
            "source_path": row.get("source_path"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "action_required_codes": row.get("action_required_codes") or [],
        }
        for row in rows
        if row.get("trade_index_lifecycle_status") == ACTION_REQUIRED
    ]
    blocker_examples = [
        {
            "source_path": row.get("source_path"),
            "candidate_id": row.get("candidate_id"),
            "symbol": row.get("symbol"),
            "lifecycle_completeness": row.get("lifecycle_completeness"),
            "documented_limitation_codes": row.get("documented_limitation_codes") or [],
        }
        for row in rows
        if row.get("documented_limitation_codes")
    ]
    status = "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_LIFECYCLE_BLOCKERS"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "promotion_verdict": PROMOTION_VERDICT,
        "status": status,
        "audit_log_path": str(audit_log_path),
        "audit_log_schema": SCHEMA_VERSION,
        "inventory_index_path": str(inventory_index_path),
        "inventory_index_schema": INDEX_SCHEMA_VERSION,
        "counts": {
            "rows_considered": len(rows),
            "rows_appended_this_run": len(appended),
            "rows_available": len(read_jsonl_with_lines(audit_log_path)),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_blockers": status_counts.get(COMPLETE_WITH_BLOCKERS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "legacy_index_migration_plan": {
            "legacy_index_path": str(DEFAULT_LEGACY_INDEX),
            "legacy_index_current_use": "deprecated_for_current_live_or_oos_counts",
            "replacement": str(inventory_index_path),
            "consumer_policy": "new current-inventory consumers should read the versioned inventory index or aggregate knowledge_base/trade_records directly; older research consumers may keep using _trade_index.json only as a frozen historical cohort with source flags",
            "legacy_index_was_not_overwritten": True,
        },
        "action_required_examples": action_examples[:25],
        "documented_blocker_examples": blocker_examples[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-026 Trade Index Lifecycle Completeness - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Promotion verdict:** `{report['promotion_verdict']}`",
        "",
        "## Counts",
        "",
        f"- Trade-record rows considered: `{report['counts']['rows_considered']}`",
        f"- Audit rows available: `{report['counts']['rows_available']}`",
        f"- Audit rows appended this run: `{report['counts']['rows_appended_this_run']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented blockers: `{report['counts']['complete_with_documented_blockers']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Index Boundary",
        "",
        f"- Current inventory index: `{report['inventory_index_path']}`",
        f"- Inventory index count equals trade-record count: `{rolling['index_count_equals_trade_record_count']}`",
        f"- Trade-record count: `{rolling['trade_record_count']}`",
        f"- Legacy `_trade_index.json` count: `{rolling['legacy_trade_index_count']}`",
        f"- Count delta current minus legacy: `{rolling['legacy_vs_current_count_delta']}`",
        "- Legacy `_trade_index.json` was not overwritten; it remains a frozen historical cohort only.",
        "",
        "## Lifecycle Completeness",
        "",
        f"- Lifecycle completeness counts: `{rolling['lifecycle_completeness_counts']}`",
        f"- Limit-placed rows: `{rolling['limit_placed_rows']}`",
        f"- Limit-placed rows without lifecycle truth: `{rolling['limit_placed_without_lifecycle_truth_rows']}`",
        f"- Raw trade-id collision rows: `{rolling['raw_trade_id_collision_rows']}`",
        f"- Exit-present/execution-null rows: `{rolling['exit_present_execution_null_rows']}`",
        "",
        "## Migration Plan",
        "",
        f"- Replacement: `{report['legacy_index_migration_plan']['replacement']}`",
        f"- Consumer policy: {report['legacy_index_migration_plan']['consumer_policy']}",
        "",
        "## Safety Counters",
        "",
        f"- no_ai_calls: `{report['no_ai_calls']}`",
        f"- no_canary_required: `{report['no_canary_required']}`",
        f"- no_execution: `{report['no_execution']}`",
        f"- paid_data_calls: `{report['paid_data_calls']}`",
    ]
    if report["documented_blocker_examples"]:
        lines.extend(["", "## Documented Blocker Examples", "", "```json", json.dumps(report["documented_blocker_examples"], indent=2, sort_keys=True), "```"])
    if report["action_required_examples"]:
        lines.extend(["", "## Action Required Examples", "", "```json", json.dumps(report["action_required_examples"], indent=2, sort_keys=True), "```"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trade-record-root", type=Path, default=DEFAULT_TRADE_RECORD_ROOT)
    parser.add_argument("--legacy-index", type=Path, default=DEFAULT_LEGACY_INDEX)
    parser.add_argument("--pending-audit-log", type=Path, default=DEFAULT_PENDING_AUDIT)
    parser.add_argument("--audit-log", type=Path, default=DEFAULT_AUDIT_LOG)
    parser.add_argument("--inventory-index", type=Path, default=DEFAULT_INVENTORY_INDEX)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).isoformat()
    trade_records = read_trade_records(args.trade_record_root)
    rows = build_trade_index_lifecycle_rows(
        trade_records=trade_records,
        trade_records_root=args.trade_record_root,
        pending_lifecycle_audit_rows=read_jsonl_with_lines(args.pending_audit_log),
        generated_at_utc=generated_at,
    )
    existing = existing_rows_by_key(args.audit_log)
    appended = [row for row in rows if row_changed(existing.get(str(row.get("row_key"))), row)]
    append_jsonl(args.audit_log, appended)

    legacy_index = read_json(args.legacy_index)
    inventory_index = build_inventory_index(rows, generated_at_utc=generated_at, legacy_index_path=str(args.legacy_index))
    write_json(args.inventory_index, inventory_index)
    report = build_report(
        rows=rows,
        appended=appended,
        legacy_index=legacy_index,
        audit_log_path=args.audit_log,
        inventory_index_path=args.inventory_index,
    )
    write_json(args.report_json, report)
    write_markdown(report, args.report_md)
    print(
        json.dumps(
            {
                "status": report["status"],
                "rows_considered": report["counts"]["rows_considered"],
                "rows_appended": report["counts"]["rows_appended_this_run"],
                "rows_available": report["counts"]["rows_available"],
                "action_required": report["counts"]["action_required"],
                "inventory_index": str(args.inventory_index),
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
