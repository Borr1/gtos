#!/usr/bin/env python3
"""Build broker-R reconciliation coverage report.

Separates MT5/deal-backed actual R from internal lifecycle labels and
synthetic/path labels. It does not infer broker actual R from OHLC paths.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "broker_r_reconciliation_coverage_v1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def read_trade_records(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    rows = []
    for path in root.rglob("*.json"):
        try:
            payload = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
        except (OSError, json.JSONDecodeError):
            continue
        payload["_source_path"] = str(path)
        rows.append(payload)
    return rows


def _has_broker_actual_r(record: dict[str, Any]) -> bool:
    exit_block = record.get("exit") or {}
    if any(key in exit_block for key in ("actual_r", "realized_R", "realized_r", "r_multiple")):
        return True
    actual_close = record.get("actual_close") or {}
    return any(key in actual_close for key in ("realized_R", "realized_r", "actual_r"))


def _has_execution(record: dict[str, Any]) -> bool:
    return bool(record.get("execution"))


def _has_synthetic_path(record: dict[str, Any]) -> bool:
    text = json.dumps(record, sort_keys=True)
    return "synthetic" in text.lower() or "path" in text.lower() or "hypothetical" in text.lower()


def summarize(
    *,
    trade_records: list[dict[str, Any]],
    lifecycle_rows: list[dict[str, Any]],
    slippage_rows: list[dict[str, Any]],
    j46_rows: list[dict[str, Any]],
    mt5_deal_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    records_with_broker_r = sum(1 for row in trade_records if _has_broker_actual_r(row))
    records_with_execution = sum(1 for row in trade_records if _has_execution(row))
    records_with_synthetic = sum(1 for row in trade_records if _has_synthetic_path(row))
    lifecycle_filled = sum(
        1 for row in lifecycle_rows if row.get("intent_after_check") == "order_send_success_filled"
    )
    j46_broker_reconciled = sum(
        1
        for row in j46_rows
        if (row.get("actual_close") or {}).get("broker_deal_reconciled") is True
    )
    mt5_close_deals = sum(1 for row in mt5_deal_rows if row.get("entry") in {1, "1"})
    mt5_agent_deals = sum(1 for row in mt5_deal_rows if row.get("magic") == 20260401)
    blocker = (
        "Canonical MT5 deal-history export is present. Broker actual-R still "
        "requires per-trade joins and must not be inferred from synthetic path rows."
        if mt5_deal_rows else
        "No canonical MT5 deal-history export is present in this repo snapshot; "
        "broker actual-R cannot be inferred from synthetic path rows."
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": utc_now_iso(),
        "promotion_verdict": PROMOTION_VERDICT,
        "coverage": {
            "trade_records_total": len(trade_records),
            "trade_records_with_broker_actual_r": records_with_broker_r,
            "trade_records_with_internal_execution_block": records_with_execution,
            "trade_records_with_synthetic_or_path_fields": records_with_synthetic,
            "pending_lifecycle_rows": len(lifecycle_rows),
            "pending_lifecycle_internal_filled_rows": lifecycle_filled,
            "slippage_rows": len(slippage_rows),
            "j46_shadow_rows": len(j46_rows),
            "j46_rows_with_broker_deal_reconciled_true": j46_broker_reconciled,
            "mt5_deal_history_rows": len(mt5_deal_rows),
            "mt5_close_deal_rows": mt5_close_deals,
            "mt5_agent_magic_deal_rows": mt5_agent_deals,
        },
        "join_plan": [
            "Join pending lifecycle to slippage by trade_id where present, then by ticket and nearest timestamp when trade_id is absent.",
            "Join slippage to MT5 deal/account history by ticket and symbol; broker actual R is valid only when close/deal evidence exists.",
            "Join trade_records by metadata.trade_id/candle time/symbol to lifecycle rows; do not overwrite broker_actual_r with synthetic/path R.",
            "Keep LIMIT_PLACED rows without lifecycle telemetry as unrecoverable for broker actual-R unless MT5 deal history proves a fill.",
        ],
        "mt5_probe_command": "python scripts/export_mt5_account_history_readonly.py --start 2026-04-27 --end 2026-05-05 --output data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl --execute",
        "blocker": blocker,
    }


def render_md(payload: dict[str, Any]) -> str:
    coverage = payload["coverage"]
    lines = [
        "# Broker-R Reconciliation Coverage",
        "",
        f"**Promotion verdict:** `{payload['promotion_verdict']}`",
        "",
        "## Coverage",
        "",
        "| Metric | Count |",
        "|---|---:|",
    ]
    for key, value in coverage.items():
        lines.append(f"| `{key}` | {value} |")
    lines.extend(
        [
            "",
            "## Join Plan",
            "",
            *[f"{idx}. {item}" for idx, item in enumerate(payload["join_plan"], start=1)],
            "",
            "## MT5 Probe",
            "",
            f"`{payload['mt5_probe_command']}`",
            "",
            "## Blocker",
            "",
            payload["blocker"],
        ]
    )
    return "\n".join(lines) + "\n"


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    return summarize(
        trade_records=read_trade_records(Path(args.trade_records_root)),
        lifecycle_rows=read_jsonl(Path(args.lifecycle_log)),
        slippage_rows=read_jsonl(Path(args.slippage_log)),
        j46_rows=read_jsonl(Path(args.j46_log)),
        mt5_deal_rows=read_jsonl(Path(args.mt5_deals_log)),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trade-records-root", default="knowledge_base/trade_records")
    parser.add_argument("--lifecycle-log", default="shadow_logs/pending_limit_lifecycle.jsonl")
    parser.add_argument("--slippage-log", default="shadow_logs/slippage.jsonl")
    parser.add_argument("--j46-log", default="shadow_logs/j46_j49_shadow_outcomes.jsonl")
    parser.add_argument("--mt5-deals-log", default="data/account_history/mt5_deals_2026-04-27_2026-05-05.jsonl")
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-md", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = build_payload(args)
    output_json = Path(args.output_json)
    output_md = Path(args.output_md)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    output_md.write_text(render_md(payload), encoding="utf-8")
    print(json.dumps(payload["coverage"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
