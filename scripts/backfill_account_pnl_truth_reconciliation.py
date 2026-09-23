#!/usr/bin/env python3
"""Backfill append-only LTO-025 account/PnL truth reconciliation rows."""

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

from src.research_infra.account_pnl_truth_reconciler import (
    ACTION_REQUIRED,
    COMPLETE,
    COMPLETE_WITH_LIMITATIONS,
    SCHEMA_VERSION,
    build_account_pnl_truth_rows,
    build_rolling_status,
)


DEFAULT_DAILY_PNL = Path("shadow_logs/daily_pnl.json")
DEFAULT_DAILY_PNL_HISTORY = Path("shadow_logs/daily_pnl_history.jsonl")
DEFAULT_BROKER_AUDIT = Path("shadow_logs/broker_actual_r_audit.jsonl")
DEFAULT_MT5_DEALS = Path("data/account_history")
DEFAULT_OUTPUT = Path("shadow_logs/account_pnl_truth_reconciliation.jsonl")
DEFAULT_REPORT_JSON = Path("research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.json")
DEFAULT_REPORT_MD = Path("research/program_control/LTO025_ACCOUNT_PNL_TRUTH_RECONCILIATION_2026-05-05.md")


def read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_sources(path: Path) -> list[Path]:
    if path.is_dir():
        return sorted(path.glob("mt5_deals_*.jsonl"))
    return [path]


def read_jsonl_with_lines(path: Path) -> list[tuple[int, dict[str, Any]]]:
    if not path.exists():
        return []
    rows: list[tuple[int, dict[str, Any]]] = []
    seen_mt5_deals: set[tuple[Any, ...]] = set()
    for source in _jsonl_sources(path):
        with source.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, start=1):
                text = line.strip()
                if not text:
                    continue
                row = json.loads(text)
                row["_source_path"] = str(source)
                if row.get("schema_version") == "mt5_account_history_deal_export_v1":
                    deal_key = (
                        row.get("ticket"),
                        row.get("order"),
                        row.get("position_id"),
                        row.get("entry"),
                        row.get("time_utc"),
                    )
                    if deal_key in seen_mt5_deals:
                        continue
                    seen_mt5_deals.add(deal_key)
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


def build_report(rows: list[dict[str, Any]], appended: list[dict[str, Any]], output_path: Path) -> dict[str, Any]:
    rolling = build_rolling_status(rows)
    status_counts = Counter(str(row.get("account_pnl_truth_status") or "UNKNOWN") for row in rows)
    action_examples = [
        {
            "source_scope": row.get("source_scope"),
            "source_log": row.get("source_log"),
            "source_line": row.get("source_line"),
            "trade_id": row.get("trade_id"),
            "action_required_codes": row.get("action_required_codes") or [],
        }
        for row in rows
        if row.get("account_pnl_truth_status") == ACTION_REQUIRED
    ]
    return {
        "schema_version": "lto025_account_pnl_truth_reconciliation_v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "result_scope": "ACCOUNT_PNL_AND_MT5_DEAL_MATERIALIZATION",
        "status": "ACTION_REQUIRED" if action_examples else "OK_WITH_DOCUMENTED_PNL_TRUTH_LIMITATIONS",
        "reconciliation_log_path": str(output_path),
        "reconciliation_log_schema": SCHEMA_VERSION,
        "counts": {
            "rows_considered": len(rows),
            "rows_appended_this_run": len(appended),
            "rows_available": len(read_jsonl_with_lines(output_path)),
            "complete": status_counts.get(COMPLETE, 0),
            "complete_with_documented_limitations": status_counts.get(COMPLETE_WITH_LIMITATIONS, 0),
            "action_required": status_counts.get(ACTION_REQUIRED, 0),
        },
        "rolling_status": rolling,
        "action_required_examples": action_examples[:25],
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "paid_fetch_attempted": False,
        "paid_data_calls": 0,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    rolling = report["rolling_status"]
    lines = [
        "# LTO-025 Account/PnL Truth Reconciliation - 2026-05-05",
        "",
        f"**Schema:** `{report['schema_version']}`",
        f"**Generated:** `{report['generated_at_utc']}`",
        f"**Status:** `{report['status']}`",
        f"**Result scope:** `{report['result_scope']}`",
        "",
        "## Counts",
        "",
        f"- Reconciliation rows available: `{report['counts']['rows_available']}`",
        f"- Reconciliation rows appended this run: `{report['counts']['rows_appended_this_run']}`",
        f"- Complete: `{report['counts']['complete']}`",
        f"- Complete with documented limitations: `{report['counts']['complete_with_documented_limitations']}`",
        f"- Action required: `{report['counts']['action_required']}`",
        "",
        "## Evidence Classes",
        "",
        f"- R evidence: `{rolling['r_evidence_class_counts']}`",
        f"- Dollar evidence: `{rolling['dollar_evidence_class_counts']}`",
        "",
        "## Truth Boundary",
        "",
        f"- Actual R claim allowed rows: `{rolling['actual_r_claim_allowed_rows']}`",
        f"- Actual dollar claim allowed rows: `{rolling['actual_dollar_claim_allowed_rows']}`",
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
    parser.add_argument("--daily-pnl", type=Path, default=DEFAULT_DAILY_PNL)
    parser.add_argument("--daily-pnl-history", type=Path, default=DEFAULT_DAILY_PNL_HISTORY)
    parser.add_argument("--broker-audit-log", type=Path, default=DEFAULT_BROKER_AUDIT)
    parser.add_argument("--mt5-deals-log", type=Path, default=DEFAULT_MT5_DEALS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report-json", type=Path, default=DEFAULT_REPORT_JSON)
    parser.add_argument("--report-md", type=Path, default=DEFAULT_REPORT_MD)
    args = parser.parse_args()

    rows = build_account_pnl_truth_rows(
        daily_pnl_state=read_json(args.daily_pnl),
        daily_pnl_history_rows=read_jsonl_with_lines(args.daily_pnl_history),
        broker_actual_r_rows=read_jsonl_with_lines(args.broker_audit_log),
        mt5_deal_rows=read_jsonl_with_lines(args.mt5_deals_log),
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
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
                "rows_considered": report["counts"]["rows_considered"],
                "rows_appended": len(appended),
                "rows_available": report["counts"]["rows_available"],
                "action_required": report["counts"]["action_required"],
            },
            sort_keys=True,
        )
    )
    return 1 if report["status"] == "ACTION_REQUIRED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
