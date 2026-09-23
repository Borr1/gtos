#!/usr/bin/env python3
"""Audit V4U source-partial rows against the BrokerOrderLifecycleCaptureV4 contract."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.components.broker_order_lifecycle_capture_v4 import (
    ORDER_REQUEST_REQUIRED_FIELDS,
    PRE_ORDER_REQUIRED_FIELDS,
    SCHEMA_VERSION,
)

DEFAULT_ROUTE_DIR = Path(
    "research/operations/final_moonshot_v4_ultimate_system_repair_from_wave4r_2026_06_06"
)
DEFAULT_CONFIG_PATH = Path("config/agent_config.yaml")
SOURCE_PARTIAL_LEDGER = "V4U_SOURCE_PARTIAL_REQUIREMENT_LEDGER.jsonl"
AUDIT_JSON = "V4U_BROKER_LIFECYCLE_CAPTURE_CONTRACT_AUDIT.json"
REQUIREMENT_JSONL = "V4U_BROKER_LIFECYCLE_CAPTURE_REQUIREMENT_LEDGER.jsonl"

BROKER_LIFECYCLE_GAP_KEYS = {
    "missing_ticket",
    "ticket_bound_state_not_confirmed",
    "broker_position_not_confirmed",
    "account_history_deal_reconciliation",
    "close_order_retcode",
    "order_modify_retcode",
    "spread_r_at_order_send",
    "slippage_r_at_fill",
    "commission",
    "swap",
    "missing_historical_live_cost_lifecycle_fields",
    "net_r_missing_historical_cost_lifecycle_fields",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            text = line.strip()
            if not text:
                continue
            payload = json.loads(text)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{line_number} is not a JSON object")
            rows.append(payload)
    return rows


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True, ensure_ascii=True) + "\n")


def load_runtime_config(config_path: Path) -> dict[str, Any]:
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    runtime = config.get("gtos_vnext_runtime") or {}
    if not isinstance(runtime, dict):
        runtime = {}
    return runtime


def build_requirement_rows(source_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pre_order_fields = [name for name, _keys in PRE_ORDER_REQUIRED_FIELDS]
    order_request_fields = list(ORDER_REQUEST_REQUIRED_FIELDS)
    broker_real_fields = [
        "order_result.retcode",
        "order_result.order",
        "order_result.deal",
        "order_result.price",
        "account_history_lookup_status=RECONCILED_FROM_ACCOUNT_HISTORY",
        "deal_ticket",
        "broker_fill_time_utc",
        "broker_entry_price",
        "commission",
        "swap",
    ]
    requirement_rows: list[dict[str, Any]] = []
    for idx, row in enumerate(source_rows, start=1):
        gap_counter = Counter(row.get("top_source_gaps") or {})
        lifecycle_gap_count = sum(
            int(gap_counter.get(key, 0) or 0) for key in BROKER_LIFECYCLE_GAP_KEYS
        )
        requirement_rows.append(
            {
                "schema_version": "v4u_broker_lifecycle_capture_requirement_v1",
                "requirement_group_id": f"broker_lifecycle_capture_req_{idx:04d}",
                "source_path": row.get("source_path"),
                "source_sha256": row.get("source_sha256"),
                "source_path_status": row.get("source_path_status"),
                "row_count": row.get("row_count"),
                "symbols": row.get("symbols"),
                "years": row.get("years"),
                "sample_asof_utc": row.get("sample_asof_utc"),
                "sample_candidate_ids": row.get("sample_candidate_ids"),
                "source_partial_current_status": "historical_rows_remain_source_required",
                "contract_schema": SCHEMA_VERSION,
                "pre_order_required_fields": pre_order_fields,
                "order_request_required_fields": order_request_fields,
                "broker_real_entry_label_required_fields": broker_real_fields,
                "broker_lifecycle_gap_count": lifecycle_gap_count,
                "top_source_gaps": row.get("top_source_gaps") or {},
                "required_runtime_capture_mechanism": (
                    "BrokerOrderLifecycleCaptureV4 must write pre-order source, "
                    "scheduler, lifecycle, prop-headroom, order request/result, "
                    "deal, commission, swap, spread/slippage, and ticket/thesis fields."
                ),
                "historical_truth_boundary": (
                    "Do not infer ticket/order/deal/lifecycle/cost truth from replay "
                    "path or M15 source rows."
                ),
            }
        )
    return requirement_rows


def build_audit(route_dir: Path, config_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    source_path = route_dir / SOURCE_PARTIAL_LEDGER
    source_rows = read_jsonl(source_path)
    requirement_rows = build_requirement_rows(source_rows)
    row_count_total = sum(int(row.get("row_count") or 0) for row in requirement_rows)
    lifecycle_gap_groups = sum(1 for row in requirement_rows if row["broker_lifecycle_gap_count"] > 0)
    lifecycle_gap_rows = sum(int(row.get("row_count") or 0) for row in requirement_rows if row["broker_lifecycle_gap_count"] > 0)
    gap_counter: Counter[str] = Counter()
    for row in requirement_rows:
        gap_counter.update(row.get("top_source_gaps") or {})

    runtime = load_runtime_config(config_path)
    config_status = {
        "execution_manager_v4_broker_lifecycle_capture_contract_required": bool(
            runtime.get("execution_manager_v4_broker_lifecycle_capture_contract_required")
        ),
        "broker_order_lifecycle_capture_v4_enabled": bool(
            runtime.get("broker_order_lifecycle_capture_v4_enabled")
        ),
        "broker_order_lifecycle_capture_v4_log_enabled": bool(
            runtime.get("broker_order_lifecycle_capture_v4_log_enabled")
        ),
        "broker_order_lifecycle_capture_v4_schema": runtime.get(
            "broker_order_lifecycle_capture_v4_schema"
        ),
        "broker_order_lifecycle_capture_v4_log_path": runtime.get(
            "broker_order_lifecycle_capture_v4_log_path"
        ),
    }
    audit = {
        "schema_version": "v4u_broker_lifecycle_capture_contract_audit_v1",
        "generated_at_utc": utc_now_iso(),
        "status": (
            "active_contract_implemented_historical_rows_remain_capture_required"
            if all(
                [
                    config_status[
                        "execution_manager_v4_broker_lifecycle_capture_contract_required"
                    ],
                    config_status["broker_order_lifecycle_capture_v4_enabled"],
                    config_status["broker_order_lifecycle_capture_v4_log_enabled"],
                    config_status["broker_order_lifecycle_capture_v4_schema"]
                    == SCHEMA_VERSION,
                ]
            )
            else "config_contract_incomplete"
        ),
        "contract_schema": SCHEMA_VERSION,
        "source_partial_requirement_ledger": str(source_path),
        "source_partial_requirement_groups": len(requirement_rows),
        "source_partial_rows_total": row_count_total,
        "broker_lifecycle_gap_groups": lifecycle_gap_groups,
        "broker_lifecycle_gap_rows": lifecycle_gap_rows,
        "top_broker_lifecycle_gap_counts": {
            key: int(gap_counter.get(key, 0)) for key in sorted(BROKER_LIFECYCLE_GAP_KEYS)
        },
        "pre_order_required_fields": [name for name, _keys in PRE_ORDER_REQUIRED_FIELDS],
        "order_request_required_fields": list(ORDER_REQUEST_REQUIRED_FIELDS),
        "broker_real_entry_label_required_fields": [
            "order_result.retcode",
            "order_result.order",
            "order_result.deal",
            "order_result.price",
            "account_history_lookup_status=RECONCILED_FROM_ACCOUNT_HISTORY",
            "deal_ticket",
            "broker_fill_time_utc",
            "broker_entry_price",
            "commission",
            "swap",
        ],
        "implemented_code": [
            "src/components/broker_order_lifecycle_capture_v4.py",
            "src/components/execution_manager_v4.py",
            "src/components/execution.py",
            "config/agent_config.yaml",
            "tests/test_broker_order_lifecycle_capture_v4.py",
            "tests/test_execution_manager_v4.py",
            "tests/test_wave3_5_v4_authority_activation.py",
        ],
        "config_status": config_status,
        "source_boundary": (
            "source-partial historical rows remain fail-closed until the exact "
            "ticket/order/deal/cost/lifecycle fields are captured or exported; "
            "replay/proxy path data is not broker-real lifecycle truth"
        ),
        "requirement_ledger": REQUIREMENT_JSONL,
    }
    return audit, requirement_rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path, default=DEFAULT_ROUTE_DIR)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    audit, requirement_rows = build_audit(args.route_dir, args.config)
    if args.write:
        write_json(args.route_dir / AUDIT_JSON, audit)
        write_jsonl(args.route_dir / REQUIREMENT_JSONL, requirement_rows)
    print(json.dumps(audit, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
