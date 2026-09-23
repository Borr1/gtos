"""Broker order/deal lifecycle capture contract for V4.

The functions here are observation and validation helpers. They never call MT5,
place orders, modify positions, disclose credentials, or infer broker-real truth
from replay/proxy rows. Runtime callers supply already-observed request/result
objects and account-history reconciliation packets.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.components.ultimate_candidate_package import (
    build_ultimate_candidate_package_shadow_summary,
)

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "broker_order_lifecycle_capture_v4_packet_v1"
COMPONENT = "broker_order_lifecycle_capture_v4"
EVIDENCE_CLASS = "production_code_integration_broker_order_lifecycle_capture_v4"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
DEFAULT_LOG_PATH = "shadow_logs/broker_order_lifecycle_capture_v4.jsonl"

BROKER_REAL_ACCOUNT_HISTORY_STATUS = "RECONCILED_FROM_ACCOUNT_HISTORY"
REPLAY_OR_PROXY_TOKENS = (
    "replay",
    "proxy",
    "simulated",
    "simulation",
    "backtest",
    "frozen",
)

PRE_ORDER_REQUIRED_FIELDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("candidate_id", ("candidate_id", "gtos_vnext_candidate_id")),
    ("decision_time_utc", ("decision_time_utc", "asof_utc")),
    ("source_hash", ("source_hash", "gtos_vnext_source_event_hash")),
    ("source_path_or_event_details", ("source_file", "source_path", "gtos_vnext_source_event_details")),
    ("selector_row_id", ("gtos_vnext_selector_row_id",)),
    ("selector_proof_hash", ("gtos_vnext_selector_proof_hash", "gtos_vnext_selector_v4_packet_hash")),
    ("scheduler_packet", ("gtos_vnext_scheduler_v4_packet",)),
    ("scheduler_packet_hash", ("gtos_vnext_scheduler_v4_packet_hash",)),
    ("same_symbol_lifecycle_action", ("gtos_vnext_same_symbol_lifecycle_action", "gtos_vnext_lifecycle_action")),
    ("same_symbol_lifecycle_packet", ("gtos_vnext_same_symbol_lifecycle_v4_packet",)),
    ("prop_firm_headroom_snapshot", ("gtos_vnext_prop_firm_headroom_snapshot_v4",)),
    ("execution_policy_id", ("gtos_vnext_execution_policy_id",)),
    ("dynamic_policy_selected", ("gtos_vnext_dynamic_policy_selected",)),
    ("dynamic_policy_applied", ("gtos_vnext_dynamic_policy_applied",)),
    ("selected_cell_risk_pct", ("gtos_vnext_selected_cell_risk_pct",)),
    ("selected_cell_risk_cell_id", ("gtos_vnext_selected_cell_risk_cell_id",)),
    ("geometry_contract", ("gtos_vnext_dynamic_target_stop_geometry_v4", "gtos_vnext_target_stop_geometry_v4")),
)

ORDER_REQUEST_REQUIRED_FIELDS = (
    "action",
    "symbol",
    "volume",
    "type",
    "price",
    "sl",
    "tp",
    "deviation",
    "magic",
    "type_filling",
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _runtime_cfg(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    cfg = config.get("gtos_vnext_runtime") or {}
    return cfg if isinstance(cfg, Mapping) else {}


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def _noneish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _clean_str(value: Any) -> str | None:
    if value in (None, ""):
        return None
    text = str(value).strip()
    return text or None


def _get(source: Any, key: str) -> Any:
    if isinstance(source, Mapping):
        return source.get(key)
    return getattr(source, key, None)


def _first_value(source: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = source.get(key)
        if not _noneish(value):
            return value
    return None


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    return str(value)


def _packet_hash(payload: Mapping[str, Any]) -> str:
    material = {
        key: value
        for key, value in payload.items()
        if key not in {"generated_at_utc", "packet_hash_sha256"}
    }
    raw = json.dumps(
        _json_safe(material),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _contains_replay_or_proxy(*values: Any) -> bool:
    joined = " ".join(str(value or "").lower() for value in values)
    return any(token in joined for token in REPLAY_OR_PROXY_TOKENS)


def _pre_order_missing_fields(trade_params: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for name, keys in PRE_ORDER_REQUIRED_FIELDS:
        if _first_value(trade_params, keys) in (None, "", [], {}):
            missing.append(name)
    return missing


def _order_request_missing_fields(order_request: Mapping[str, Any] | None) -> list[str]:
    request = order_request if isinstance(order_request, Mapping) else {}
    return [field for field in ORDER_REQUEST_REQUIRED_FIELDS if _noneish(request.get(field))]


def _order_result_packet(order_result: Any) -> dict[str, Any]:
    if order_result is None:
        return {
            "present": False,
            "success": False,
            "missing_fields": ["order_result"],
        }
    missing = [
        field
        for field in ("retcode", "order", "volume", "price", "comment")
        if _noneish(_get(order_result, field))
    ]
    order = _get(order_result, "order")
    retcode = _get(order_result, "retcode")
    return {
        "present": True,
        "success": bool(getattr(order_result, "success", False)),
        "missing_fields": missing,
        "retcode": retcode,
        "order_ticket": order,
        "deal_ticket_from_order_result": _get(order_result, "deal"),
        "request_id": _get(order_result, "request_id"),
        "retcode_external": _get(order_result, "retcode_external"),
        "volume": _get(order_result, "volume"),
        "price": _get(order_result, "price"),
        "comment": _get(order_result, "comment"),
    }


def _deal_reconciliation_packet(entry_deal_accounting: Mapping[str, Any] | None) -> dict[str, Any]:
    accounting = entry_deal_accounting if isinstance(entry_deal_accounting, Mapping) else {}
    status = _clean_str(accounting.get("account_history_lookup_status"))
    missing: list[str] = []
    if status != BROKER_REAL_ACCOUNT_HISTORY_STATUS:
        missing.append("account_history_deal_reconciliation")
    for field in ("deal_ticket", "broker_fill_time_utc", "broker_entry_price"):
        if _noneish(accounting.get(field)):
            missing.append(field)
    for field in ("commission", "swap"):
        if accounting.get(field) is None:
            missing.append(field)
    if _contains_replay_or_proxy(status, accounting.get("source_status"), accounting.get("evidence_class")):
        missing.append("broker_real_source_status_not_replay_proxy_or_simulated")
    return {
        "account_history_lookup_status": status,
        "account_history_lookup_attempted": accounting.get("account_history_lookup_attempted"),
        "account_history_lookup_attempt_count": accounting.get("account_history_lookup_attempt_count"),
        "account_history_lookup_window_start_utc": accounting.get("account_history_lookup_window_start_utc"),
        "account_history_lookup_window_end_utc": accounting.get("account_history_lookup_window_end_utc"),
        "account_history_lookup_error": accounting.get("account_history_lookup_error"),
        "account_history_lookup_match_keys": accounting.get("account_history_lookup_match_keys"),
        "deal_ticket": accounting.get("deal_ticket"),
        "broker_fill_time_utc": accounting.get("broker_fill_time_utc"),
        "broker_entry_price": accounting.get("broker_entry_price"),
        "commission": accounting.get("commission"),
        "swap": accounting.get("swap"),
        "missing_fields": sorted(dict.fromkeys(missing)),
        "source_status": (
            "broker_real_account_history_reconciled"
            if not missing
            else "source_required_for_broker_real_entry_label"
        ),
    }


def _lifecycle_identity(trade_params: Mapping[str, Any], trade_state: Any | None) -> dict[str, Any]:
    lifecycle_packet = trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet")
    if not isinstance(lifecycle_packet, Mapping):
        lifecycle_packet = {}
    return {
        "candidate_id": _first_value(trade_params, ("candidate_id", "gtos_vnext_candidate_id")),
        "thesis_id": _first_value(
            trade_params,
            ("gtos_vnext_thesis_id", "thesis_id", "candidate_thesis_id"),
        ),
        "same_symbol_lifecycle_action": _first_value(
            trade_params,
            ("gtos_vnext_same_symbol_lifecycle_action", "gtos_vnext_lifecycle_action"),
        ),
        "parent_ticket": lifecycle_packet.get("parent_ticket"),
        "parent_thesis_id": lifecycle_packet.get("parent_thesis_id"),
        "close_ticket": lifecycle_packet.get("close_ticket"),
        "selected_tickets": lifecycle_packet.get("selected_tickets"),
        "entry_order_ticket": getattr(trade_state, "entry_order_ticket", None),
        "entry_deal_ticket": getattr(trade_state, "entry_deal_ticket", None),
        "ticket": getattr(trade_state, "ticket", None),
        "partial_state": getattr(trade_state, "partial_state", None),
        "be_state": getattr(trade_state, "be_state", None),
        "trailing_state": getattr(trade_state, "trailing_state", None),
        "lifecycle_phase": getattr(trade_state, "lifecycle_phase", None),
    }


def build_broker_order_lifecycle_capture_v4(
    *,
    stage: str,
    trade_params: Mapping[str, Any],
    symbol: str,
    broker_symbol: str | None = None,
    order_request: Mapping[str, Any] | None = None,
    order_result: Any | None = None,
    entry_deal_accounting: Mapping[str, Any] | None = None,
    trade_state: Any | None = None,
    pretrade_cost_model: Mapping[str, Any] | None = None,
    execution_manager_packet: Mapping[str, Any] | None = None,
    order_send_time_utc: str | None = None,
    order_result_time_utc: str | None = None,
    generated_at_utc: str | None = None,
) -> dict[str, Any]:
    """Build a broker lifecycle packet from supplied observations."""
    pre_missing = _pre_order_missing_fields(trade_params)
    request_missing = _order_request_missing_fields(order_request)
    result_packet = _order_result_packet(order_result)
    deal_packet = _deal_reconciliation_packet(entry_deal_accounting)
    package_shadow = build_ultimate_candidate_package_shadow_summary(
        {
            **dict(trade_params),
            "gtos_vnext_execution_manager_v4_packet": execution_manager_packet,
        }
    )
    package_missing = (
        ["ultimate_candidate_package_shadow_authority_not_closed"]
        if package_shadow["packet_present"]
        and package_shadow["authority_closed"] is not True
        else []
    )
    result_success = result_packet["success"]
    deal_missing = list(deal_packet["missing_fields"])
    order_missing = []
    if stage not in {"pre_order_contract", "pre_send"}:
        order_missing.extend(request_missing)
        order_missing.extend(result_packet["missing_fields"])
        if result_success:
            order_missing.extend(deal_missing)
        order_missing.extend(package_missing)

    broker_real_entry_label_ready = bool(result_success and not pre_missing and not order_missing)
    if broker_real_entry_label_ready:
        status = "broker_real_entry_lifecycle_reconciled"
    elif result_success:
        status = "source_required_for_broker_real_entry_label"
    elif result_packet["present"]:
        status = "order_send_result_captured_not_broker_real_entry_label"
    elif pre_missing:
        status = "pre_order_capture_contract_gap"
    else:
        status = "pre_order_capture_contract_ready"

    packet = {
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "generated_at_utc": generated_at_utc or _now_iso(),
        "stage": stage,
        "status": status,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
        "source_boundary": {
            "broker_real_label_rule": "requires_order_send_result_plus_account_history_deal_cost_reconciliation",
            "historical_replay_rule": "replay_proxy_path_labels_cannot_fill_ticket_order_deal_lifecycle_truth",
            "decision_boundary": "pre_order_contract_uses_asof_decision_and_runtime_authority_fields_only",
            "credential_boundary": "no_account_login_or_credentials_written; account ids must be hashed upstream",
        },
        "identity": {
            "symbol": symbol,
            "broker_symbol": broker_symbol or symbol,
            "candidate_id": _first_value(trade_params, ("candidate_id", "gtos_vnext_candidate_id")),
            "decision_time_utc": _first_value(trade_params, ("decision_time_utc", "asof_utc")),
            "trade_id": trade_params.get("trade_id"),
        },
        "pre_order_capture_contract": {
            "status": "ready" if not pre_missing else "source_required",
            "missing_fields": pre_missing,
            "source_hash": _first_value(trade_params, ("source_hash", "gtos_vnext_source_event_hash")),
            "source_path": _first_value(trade_params, ("source_file", "source_path")),
            "selector_row_id": trade_params.get("gtos_vnext_selector_row_id"),
            "selector_proof_hash": _first_value(
                trade_params,
                ("gtos_vnext_selector_proof_hash", "gtos_vnext_selector_v4_packet_hash"),
            ),
            "scheduler_packet_hash": trade_params.get("gtos_vnext_scheduler_v4_packet_hash"),
            "prop_firm_headroom_snapshot_present": isinstance(
                trade_params.get("gtos_vnext_prop_firm_headroom_snapshot_v4"),
                Mapping,
            ),
            "execution_manager_packet_hash": (
                _packet_hash(execution_manager_packet)
                if isinstance(execution_manager_packet, Mapping)
                else None
            ),
        },
        "ultimate_candidate_package_shadow_status": package_shadow["status"],
        "ultimate_candidate_package_shadow_authority_closed": package_shadow[
            "authority_closed"
        ],
        "ultimate_candidate_package_shadow_packet_present": package_shadow[
            "packet_present"
        ],
        "ultimate_candidate_package_shadow_packet_hash": package_shadow["packet_hash"],
        "ultimate_candidate_package_shadow_decision_status": package_shadow[
            "decision_status"
        ],
        "ultimate_candidate_package_shadow_selected_candidate_id": package_shadow[
            "shadow_selected_candidate_id"
        ],
        "ultimate_candidate_package_selected_candidate_id": package_shadow[
            "selected_candidate_id"
        ],
        "ultimate_candidate_package_approved_risk_pct": package_shadow[
            "approved_risk_pct"
        ],
        "ultimate_candidate_package_runtime_effect_now": package_shadow[
            "runtime_effect_now"
        ],
        "ultimate_candidate_package_live_execution_activation_allowed": package_shadow[
            "live_execution_activation_allowed"
        ],
        "ultimate_candidate_package_final_package_selection_allowed": package_shadow[
            "final_package_selection_allowed"
        ],
        "ultimate_candidate_package_order_calls": package_shadow["order_calls"],
        "ultimate_candidate_package_execution_policy_status": package_shadow[
            "execution_policy_status"
        ],
        "ultimate_candidate_package_selected_order_type_architecture": package_shadow[
            "selected_order_type_architecture"
        ],
        "ultimate_candidate_package_execution_order_type_policy_selectable": package_shadow[
            "execution_order_type_policy_selectable"
        ],
        "ultimate_candidate_package_gate_violations": package_shadow[
            "gate_violations"
        ],
        "ultimate_candidate_package_shadow_boundary": package_shadow["summary"],
        "ticket_thesis_lifecycle": _lifecycle_identity(trade_params, trade_state),
        "order_send_observation": {
            "order_send_time_utc": order_send_time_utc,
            "order_result_time_utc": order_result_time_utc,
            "request_missing_fields": request_missing,
            "request": _json_safe(dict(order_request or {})),
            "result": result_packet,
        },
        "deal_cost_reconciliation": deal_packet,
        "pretrade_cost_model": _json_safe(dict(pretrade_cost_model or {})),
        "broker_real_entry_label_ready": broker_real_entry_label_ready,
        "missing_fields": sorted(dict.fromkeys(pre_missing + order_missing)),
        "remaining_capture_requirement": (
            None
            if broker_real_entry_label_ready
            else {
                "required_fields": sorted(dict.fromkeys(pre_missing + order_missing)),
                "requirement_id": "v4u_forward_broker_order_deal_lifecycle_capture",
                "non_generatable_historical_truth": [
                    "original MT5 order/deal ticket state for rows not logged at runtime",
                    "account-history commission/swap/slippage reconciliation for rows without deal exports",
                    "ticket-bound thesis/lifecycle manager decisions not emitted before order",
                ],
            }
        ),
    }
    packet["packet_hash_sha256"] = _packet_hash(packet)
    return packet


def broker_order_lifecycle_capture_v4_enabled(config: Mapping[str, Any] | None) -> bool:
    cfg = _runtime_cfg(config)
    return _truthy(cfg.get("broker_order_lifecycle_capture_v4_enabled", False))


def record_broker_order_lifecycle_capture_v4(
    packet: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    log_path: str | Path | None = None,
) -> None:
    """Append one lifecycle packet when the runtime capture log is enabled."""
    cfg = _runtime_cfg(config)
    enabled = broker_order_lifecycle_capture_v4_enabled(config)
    if not enabled and "broker_order_lifecycle_capture_v4_log_enabled" not in cfg:
        return
    if not _truthy(cfg.get("broker_order_lifecycle_capture_v4_log_enabled", enabled)):
        return
    target = Path(
        log_path
        or cfg.get("broker_order_lifecycle_capture_v4_log_path")
        or DEFAULT_LOG_PATH
    )
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(_json_safe(packet), sort_keys=True, ensure_ascii=True) + "\n"
        for attempt in range(5):
            try:
                with target.open("a", encoding="utf-8", newline="") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
                return
            except OSError:
                if attempt == 4:
                    raise
                time.sleep(0.025)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Broker order lifecycle capture V4 logging failed: %s", exc)


__all__ = [
    "BROKER_REAL_ACCOUNT_HISTORY_STATUS",
    "COMPONENT",
    "DEFAULT_LOG_PATH",
    "EVIDENCE_CLASS",
    "RESULT_USE_STATUS",
    "SCHEMA_VERSION",
    "build_broker_order_lifecycle_capture_v4",
    "broker_order_lifecycle_capture_v4_enabled",
    "record_broker_order_lifecycle_capture_v4",
]
