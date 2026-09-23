#!/usr/bin/env python3
"""Verify dual-broker source/target namespace and no-copy boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.dual_broker_execution_follower import (  # noqa: E402
    DEFAULT_CONFIG_PATH,
    DEFAULT_PROFILE,
    dual_broker_architecture_contract,
    load_target_base_config,
)
from src.components.dual_broker_intent_bus import (  # noqa: E402
    MARKET_ENTRY,
    build_intent_from_execution_inputs,
    source_target_boundary_violations,
)

FORBIDDEN_TARGET_AUTHORITY_FIELDS = (
    "primary_lot_copy",
    "primary_fill_price_copy",
    "primary_cash_pnl_copy",
    "primary_cost_swap_fee_copy",
    "primary_symbol_spec_session_copy",
    "primary_order_deal_position_lifecycle_copy",
)

redacted_account_TARGET_PROJECTION_FIELDS = (
    "copy_primary_lots_or_fill_prices",
    "copy_primary_cash_pnl",
    "copy_primary_cost_swap_fee",
    "copy_primary_symbol_spec_session",
    "copy_primary_order_deal_position_lifecycle",
)

REQUIRED_ROUTE_FILES = (
    "WAVE3_CONTEXT_ANCHOR.json",
    "WAVE3_DUAL_BROKER_NAMESPACE_CONTRACT.json",
    "WAVE3_SOURCE_TARGET_EVIDENCE_BOUNDARY_LEDGER.jsonl",
    "WAVE3_PRODUCTION_CODE_DISPOSITION_LEDGER.jsonl",
    "WAVE3_DECISION_LEDGER.jsonl",
    "WAVE3_OUTPUT_MANIFEST.json",
    "WAVE3_COMPLETION_AUDIT.md",
    "WAVE3_SATURATION_SELF_RED_TEAM.md",
)


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data if isinstance(data, dict) else {}


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return str(value)


def _json_file_status(path: Path) -> dict[str, Any]:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"path": str(path), "parse_ok": False, "error": str(exc)}
    return {"path": str(path), "parse_ok": True}


def _jsonl_file_status(path: Path) -> dict[str, Any]:
    rows = 0
    parse_errors = 0
    status_counts: dict[str, int] = {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            rows += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                continue
            if isinstance(row, dict):
                for key in ("status", "production_code_disposition", "runtime_disposition"):
                    value = row.get(key)
                    if isinstance(value, str) and value:
                        status_counts[f"{key}={value}"] = (
                            status_counts.get(f"{key}={value}", 0) + 1
                        )
    return {
        "path": str(path),
        "rows": rows,
        "parse_errors": parse_errors,
        "status_counts": dict(sorted(status_counts.items())),
    }


def _route_artifact_status(route_dir: Path | None) -> dict[str, Any]:
    if route_dir is None:
        return {"checked": False, "reason": "route_dir_not_provided"}
    missing = [
        name for name in REQUIRED_ROUTE_FILES if not (route_dir / name).exists()
    ]
    json_status = [
        _json_file_status(path)
        for path in sorted(route_dir.glob("*.json"))
        if path.name != "WAVE3_VERIFICATION_RESULT.json"
    ]
    jsonl_status = [
        _jsonl_file_status(path)
        for path in sorted(route_dir.glob("*.jsonl"))
    ]
    return {
        "checked": True,
        "route_dir": str(route_dir),
        "missing_required_files": missing,
        "json_files_checked": json_status,
        "jsonl_files_checked": jsonl_status,
        "json_parse_error_count": sum(
            1 for row in json_status if row.get("parse_ok") is not True
        ),
        "jsonl_parse_error_count": sum(
            int(row.get("parse_errors") or 0) for row in jsonl_status
        ),
    }


def _profile_checks(project_root: Path) -> dict[str, Any]:
    ftmo_account = _load_yaml(project_root / "config/profiles/operator_profile.yaml")
    ftmo_alias = _load_yaml(project_root / "config/profiles/ftmo.yaml")
    redacted_account = _load_yaml(project_root / "config/profiles/redacted_account.yaml")

    profile_errors: list[str] = []
    for profile_name, cfg in (
        ("operator_profile", ftmo_account),
        ("ftmo", ftmo_alias),
    ):
        dual = cfg.get("dual_broker") if isinstance(cfg.get("dual_broker"), dict) else {}
        authority = (
            dual.get("target_authority")
            if isinstance(dual.get("target_authority"), dict)
            else {}
        )
        if dual.get("role") != "follower_projector_only":
            profile_errors.append(f"{profile_name}.role_not_follower_projector_only")
        for key in FORBIDDEN_TARGET_AUTHORITY_FIELDS:
            if authority.get(key) != "forbidden":
                profile_errors.append(f"{profile_name}.{key}_not_forbidden")
        if authority.get("target_broker_truth_source") != "target_broker_local_only":
            profile_errors.append(f"{profile_name}.target_truth_not_local_only")

    fn_dual = (
        redacted_account.get("dual_broker")
        if isinstance(redacted_account.get("dual_broker"), dict)
        else {}
    )
    projection = (
        fn_dual.get("target_projection")
        if isinstance(fn_dual.get("target_projection"), dict)
        else {}
    )
    if fn_dual.get("role") != "primary_full_runtime":
        profile_errors.append("redacted_account.role_not_primary_full_runtime")
    for key in redacted_account_TARGET_PROJECTION_FIELDS:
        if projection.get(key) != "forbidden":
            profile_errors.append(f"redacted_account.{key}_not_forbidden")
    if projection.get("target_broker_truth_source") != "target_broker_local_only":
        profile_errors.append("redacted_account.target_truth_not_local_only")

    base_config = load_target_base_config(DEFAULT_CONFIG_PATH, DEFAULT_PROFILE)
    contract = dual_broker_architecture_contract(
        base_config,
        target_namespace="operator_profile",
        source_namespace="redacted_account_live_bee34003",
        order_enabled=False,
    )
    if contract.get("status") != "passed":
        profile_errors.extend(f"contract:{item}" for item in contract.get("errors") or [])

    return {
        "profile_errors": profile_errors,
        "ftmo_contract_status": contract,
    }


def _intent_boundary_checks() -> dict[str, Any]:
    unsafe_primary_order = {
        "record_path": "knowledge_base/redacted_account_live_bee34003/trade_records/XAUUSD/record.json",
        "ticket": 234432798,
        "entry_order_ticket": 234432798,
        "entry_deal_ticket": 234432799,
        "entry_price": 2350.11,
        "initial_volume": 0.50,
        "commission": -4.0,
        "swap": -2.0,
        "contract_size": 100.0,
        "pending_order_mode": "INTERNAL_CANDLE_POLLED_INTENT",
    }
    intent = build_intent_from_execution_inputs(
        intent_type=MARKET_ENTRY,
        source_profile="redacted_account",
        source_runtime_namespace="redacted_account_live_bee34003",
        source_symbol="XAUUSD",
        source_mt5_symbol="XAUUSD",
        trade_params={
            "direction": "LONG",
            "entry_price": 2350.0,
            "stop_loss": 2340.0,
            "take_profit_1": 2370.0,
        },
        source_trade_id="boundary_verifier_source_trade",
        primary_order=unsafe_primary_order,
    )
    sanitized_violations = source_target_boundary_violations(intent)
    malicious = dict(intent)
    malicious["primary_order"] = unsafe_primary_order
    malicious_violations = source_target_boundary_violations(malicious)
    return {
        "sanitized_primary_order": intent.get("primary_order"),
        "sanitized_violations": sanitized_violations,
        "malicious_violation_count": len(malicious_violations),
        "malicious_violations": malicious_violations,
    }


def build_report(route_dir: Path | None = None) -> dict[str, Any]:
    profile = _profile_checks(PROJECT_ROOT)
    intent = _intent_boundary_checks()
    route = _route_artifact_status(route_dir)
    errors: list[str] = []
    errors.extend(profile["profile_errors"])
    if intent["sanitized_violations"]:
        errors.extend(f"sanitized_intent:{item}" for item in intent["sanitized_violations"])
    if intent["malicious_violation_count"] <= 0:
        errors.append("malicious_intent_not_detected")
    if route.get("checked"):
        errors.extend(f"missing_route_file:{item}" for item in route["missing_required_files"])
        if route["json_parse_error_count"]:
            errors.append("route_json_parse_errors")
        if route["jsonl_parse_error_count"]:
            errors.append("route_jsonl_parse_errors")
    return {
        "schema_version": "dual_broker_source_target_boundary_verifier_v1",
        "status": "passed" if not errors else "failed",
        "ok": not errors,
        "errors": errors,
        "profile_checks": profile,
        "intent_boundary_checks": intent,
        "route_artifact_status": route,
        "boundary_fields": {
            "RESULT_MATERIALIZATION_REQUIRED": True,
            "validation_result_status": False,
            "outcome_result_rows_status": False,
            "broker_runtime_change_status": False,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--route-dir", type=Path)
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()

    report = build_report(args.route_dir)
    text = json.dumps(_jsonable(report), indent=2, sort_keys=True)
    if args.write:
        args.write.parent.mkdir(parents=True, exist_ok=True)
        args.write.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
