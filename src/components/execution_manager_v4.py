"""Execution Manager V4 admission packet and fail-closed evaluator.

The module is active production-code integration for the local V4 authority
path. When ``execution_manager_v4_apply_to_execution`` is enabled, fatal packet
defects block the entry before any MT5 order request is sent. Physical broker
deployment remains controlled by the runtime halt surface.
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.components.dynamic_target_stop_geometry_v4 import (
    build_target_stop_geometry_v4_contract,
)
from src.components.broker_order_lifecycle_capture_v4 import (
    build_broker_order_lifecycle_capture_v4,
)
from src.components.prop_firm_headroom_v4 import (
    build_prop_firm_headroom_snapshot_v4_from_account_state,
    evaluate_prop_firm_headroom_snapshot_v4,
    find_prop_firm_headroom_account_state_v4,
    find_prop_firm_headroom_snapshot_v4,
)
from src.components.selector_v4 import selector_v4_action_blocks_execution

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "execution_manager_v4_packet_v1"
COMPONENT = "execution_manager_v4"
EVIDENCE_CLASS = "production_code_integration_source_bound_execution_manager_v4"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
DEFAULT_LOG_PATH = "shadow_logs/execution_manager_v4_decisions.jsonl"
VALID_ACTIONS = {"disabled", "observe_only", "allow", "block"}
REPLAY_LIFECYCLE_RECONCILE_ACTIONS = {
    "new_position",
    "same_direction_scale_in",
    "close_and_reverse",
    "replace_pending",
}
LIFECYCLE_MANAGER_ACTIONS = {"close_existing", "reduce_existing", "close_and_reverse"}
SOURCE_REQUIRED_FAIL_CLOSED = "source_required_fail_closed"

@dataclass(frozen=True)
class ExecutionManagerV4Decision:
    """Evaluated V4 entry-admission decision."""

    packet: dict[str, Any]
    action: str
    should_block: bool
    fatal_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]


def _runtime_cfg(config: Mapping[str, Any] | None) -> Mapping[str, Any]:
    if not isinstance(config, Mapping):
        return {}
    cfg = config.get("gtos_vnext_runtime") or {}
    return cfg if isinstance(cfg, Mapping) else {}


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}
    return bool(value)


def execution_manager_v4_enabled(config: Mapping[str, Any] | None) -> bool:
    cfg = _runtime_cfg(config)
    return _truthy(cfg.get("execution_manager_v4_enabled", False))


def execution_manager_v4_apply_to_execution(config: Mapping[str, Any] | None) -> bool:
    cfg = _runtime_cfg(config)
    return _truthy(cfg.get("execution_manager_v4_apply_to_execution", False))


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _utc_datetime(value: str) -> datetime:
    text = str(value or "").strip()
    if not text:
        raise ValueError("generated_at_utc_invalid")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("generated_at_utc_invalid") from exc
    if parsed.tzinfo is None:
        raise ValueError("generated_at_utc_timezone_required")
    return parsed.astimezone(timezone.utc)


def _noneish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _first_value(source: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = source.get(key)
        if not _noneish(value):
            return value
    return None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _str_list(value: Any) -> list[str]:
    if value in (None, ""):
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, Mapping):
        return [str(value)]
    try:
        return [str(item) for item in value if str(item).strip()]
    except TypeError:
        return [str(value)]


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _replay_no_broker_authority(trade_params: Mapping[str, Any]) -> bool:
    """True only for local replay rows that explicitly forbid broker mutation."""

    if not _truthy(trade_params.get("gtos_vnext_live_as_if_replay_no_broker_authority")):
        return False
    broker_mutation = trade_params.get("gtos_vnext_replay_broker_mutation_enabled")
    if broker_mutation in (None, ""):
        return False
    return _truthy(broker_mutation) is False


def _normalize_lifecycle_action(value: Any) -> str | None:
    text = _clean_str(value)
    if not text:
        return None
    return text.lower().replace("-", "_")


def _runtime_risk_authority(trade_params: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in (
        "gtos_vnext_timewarp_runtime_risk_authority_v4",
        "gtos_vnext_runtime_risk_authority_v4",
        "runtime_risk_authority",
    ):
        value = trade_params.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _active_lifecycle_reconcile_packets(
    risk_authority: Mapping[str, Any],
) -> list[tuple[str, Mapping[str, Any]]]:
    packets: list[tuple[str, Mapping[str, Any]]] = []
    for key in (
        "source_required_package_risk_lifecycle_reconcile",
        "package_same_direction_scale_in_lifecycle_reconcile",
        "package_opposite_side_close_reverse_lifecycle_reconcile",
        "package_pending_replacement_lifecycle_reconcile",
    ):
        packet = _mapping(risk_authority.get(key))
        if _truthy(packet.get("applied")):
            packets.append((key, packet))
    return packets


def _replay_signed_package_authority_valid(
    risk_authority: Mapping[str, Any],
    target_action: str | None,
) -> bool:
    if target_action not in REPLAY_LIFECYCLE_RECONCILE_ACTIONS:
        return False
    if not _truthy(risk_authority.get("package_new_entry_authority_valid")):
        return False
    failures = _str_list(risk_authority.get("package_new_entry_authority_failures"))
    if failures:
        return False
    signed_target = _normalize_lifecycle_action(
        risk_authority.get("package_new_entry_authority_target_action_intent")
        or risk_authority.get("target_action_intent")
    )
    return signed_target == target_action


def _broker_lifecycle_truth_satisfied(
    risk_authority: Mapping[str, Any],
    reconcile_packets: list[tuple[str, Mapping[str, Any]]],
) -> bool:
    if _truthy(
        risk_authority.get("broker_order_lifecycle_truth_satisfied")
        or risk_authority.get("broker_lifecycle_truth_satisfied")
        or risk_authority.get("source_required_broker_lifecycle_truth_satisfied")
    ):
        return True
    return any(
        _truthy(
            packet.get("broker_order_lifecycle_truth_satisfied")
            or packet.get("broker_lifecycle_truth_satisfied")
            or packet.get("source_required_broker_lifecycle_truth_satisfied")
        )
        for _, packet in reconcile_packets
    )


def _reconciled_lifecycle_action(
    risk_authority: Mapping[str, Any],
    reconcile_packets: list[tuple[str, Mapping[str, Any]]],
) -> str | None:
    for value in (
        risk_authority.get("same_symbol_lifecycle_reconciled_action"),
        risk_authority.get("same_symbol_lifecycle_action"),
        risk_authority.get("scheduler_lifecycle_reconcile_required_action"),
        risk_authority.get("scheduler_action_intent_for_risk"),
        risk_authority.get("scheduler_effective_action_intent"),
        risk_authority.get("package_new_entry_authority_target_action_intent"),
    ):
        action = _normalize_lifecycle_action(value)
        if action in REPLAY_LIFECYCLE_RECONCILE_ACTIONS:
            return action
    for _, packet in reconcile_packets:
        for value in (
            packet.get("same_symbol_lifecycle_reconciled_action"),
            packet.get("same_symbol_lifecycle_action"),
            packet.get("scheduler_lifecycle_reconcile_required_action"),
            packet.get("scheduler_action_intent"),
            packet.get("scheduler_effective_action_intent"),
            packet.get("package_new_entry_authority_target_action_intent"),
        ):
            action = _normalize_lifecycle_action(value)
            if action in REPLAY_LIFECYCLE_RECONCILE_ACTIONS:
                return action
    return None


def _lifecycle_replay_reconcile_context(
    trade_params: Mapping[str, Any],
    *,
    action: str | None,
    permitted: Any,
) -> dict[str, Any]:
    risk_authority = _runtime_risk_authority(trade_params)
    reconcile_packets = _active_lifecycle_reconcile_packets(risk_authority)
    target_action = _reconciled_lifecycle_action(risk_authority, reconcile_packets)
    permission_reconcile_applied = _truthy(
        risk_authority.get("same_symbol_lifecycle_permission_reconcile_applied")
    ) or bool(reconcile_packets)
    signed_authority_valid = _replay_signed_package_authority_valid(
        risk_authority,
        target_action,
    )
    broker_truth_satisfied = _broker_lifecycle_truth_satisfied(
        risk_authority,
        reconcile_packets,
    )
    replay_no_broker_authority = _replay_no_broker_authority(trade_params)
    source_required_origin = action == SOURCE_REQUIRED_FAIL_CLOSED
    applied = bool(
        replay_no_broker_authority
        and permission_reconcile_applied
        and target_action
        and (signed_authority_valid or broker_truth_satisfied)
        and (source_required_origin or permitted is False)
    )
    return {
        "applied": applied,
        "replay_no_broker_authority": replay_no_broker_authority,
        "permission_reconcile_applied": permission_reconcile_applied,
        "signed_package_authority_valid": signed_authority_valid,
        "broker_lifecycle_truth_satisfied": broker_truth_satisfied,
        "source_required_origin": source_required_origin,
        "original_action": action,
        "original_permitted_order_intent": permitted,
        "reconciled_action": target_action if applied else None,
        "target_action": target_action,
        "reconcile_sources": [name for name, _ in reconcile_packets],
        "permission_reconcile_reason": _clean_str(
            risk_authority.get("same_symbol_lifecycle_permission_reconcile_reason")
        ),
    }


def _trade_params_with_reconciled_lifecycle(
    trade_params: Mapping[str, Any],
    lifecycle: Mapping[str, Any],
) -> Mapping[str, Any]:
    reconcile = _mapping(lifecycle.get("replay_lifecycle_reconcile"))
    if not reconcile.get("applied"):
        return trade_params
    action = lifecycle.get("action")
    if not action:
        return trade_params
    adjusted = dict(trade_params)
    adjusted["gtos_vnext_same_symbol_lifecycle_action"] = action
    adjusted["gtos_vnext_lifecycle_action"] = action
    packet = lifecycle.get("packet")
    if isinstance(packet, Mapping):
        adjusted["gtos_vnext_same_symbol_lifecycle_v4_packet"] = packet
    return adjusted


def _source_completeness(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    source_path = _first_value(
        trade_params,
        (
            "source_file",
            "source_path",
            "gtos_vnext_source_file",
            "gtos_vnext_source_path",
        ),
    )
    source_hash = _first_value(
        trade_params,
        (
            "source_hash",
            "gtos_vnext_source_hash",
            "gtos_vnext_source_event_hash",
            "gtos_vnext_selector_proof_hash",
        ),
    )
    source_event_details = trade_params.get("gtos_vnext_source_event_details")
    selector_row_id = _clean_str(trade_params.get("gtos_vnext_selector_row_id"))

    missing: list[str] = []
    if _noneish(source_path) and _noneish(source_event_details):
        missing.append("source_file_or_gtos_vnext_source_event_details")
    if _noneish(source_hash):
        missing.append("source_hash_or_gtos_vnext_source_event_hash")
    if _noneish(selector_row_id):
        missing.append("gtos_vnext_selector_row_id")

    return {
        "status": "source_complete" if not missing else "source_incomplete",
        "missing_fields": missing,
        "source_path": source_path,
        "source_hash": source_hash,
        "source_event_details_present": not _noneish(source_event_details),
        "selector_row_id": selector_row_id,
        "selector_proof_hash": _clean_str(
            trade_params.get("gtos_vnext_selector_proof_hash")
        ),
        "no_leak_status": "as_of_fields_only_required_for_runtime_entry",
    }


def _dynamic_policy_context(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    selected = _clean_str(trade_params.get("gtos_vnext_dynamic_policy_selected"))
    execution_policy_id = _clean_str(trade_params.get("gtos_vnext_execution_policy_id"))
    applied = _truthy(trade_params.get("gtos_vnext_dynamic_policy_applied", False))
    missing: list[str] = []
    if not selected:
        missing.append("gtos_vnext_dynamic_policy_selected")
    if not applied:
        missing.append("gtos_vnext_dynamic_policy_applied")
    if not execution_policy_id:
        missing.append("gtos_vnext_execution_policy_id")
    return {
        "status": "dynamic_policy_complete" if not missing else "dynamic_policy_incomplete",
        "missing_fields": missing,
        "selected_policy": selected,
        "execution_policy_id": execution_policy_id,
        "applied": applied,
        "replaced_policy": _clean_str(
            trade_params.get("gtos_vnext_dynamic_policy_replaced_policy")
        ),
        "trigger_r": _float_or_none(trade_params.get("gtos_vnext_dynamic_be_trigger_r")),
        "final_target_r": _float_or_none(
            trade_params.get("gtos_vnext_dynamic_final_target_r")
        ),
        "time_stop_bars": trade_params.get("gtos_vnext_dynamic_time_stop_bars"),
    }


def _selected_cell_context(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    selected_cell_id = _clean_str(trade_params.get("gtos_vnext_selected_cell_risk_cell_id"))
    selected_risk_pct = _float_or_none(trade_params.get("gtos_vnext_selected_cell_risk_pct"))
    selected_policy = _clean_str(
        trade_params.get("gtos_vnext_selected_cell_risk_selected_policy")
    )
    identity_status = _clean_str(
        trade_params.get("gtos_vnext_selected_cell_risk_policy_identity_status")
    )
    unresolved = _str_list(
        trade_params.get("gtos_vnext_selected_cell_risk_execution_critical_unresolved_reasons")
        or trade_params.get("gtos_vnext_selected_cell_risk_unresolved_reasons")
    )
    missing: list[str] = []
    if not selected_cell_id:
        missing.append("gtos_vnext_selected_cell_risk_cell_id")
    if selected_risk_pct is None or selected_risk_pct <= 0:
        missing.append("gtos_vnext_selected_cell_risk_pct")
    if not selected_policy:
        missing.append("gtos_vnext_selected_cell_risk_selected_policy")
    if not identity_status:
        missing.append("gtos_vnext_selected_cell_risk_policy_identity_status")
    if unresolved:
        missing.append("selected_cell_execution_critical_unresolved_reasons")
    return {
        "status": "selected_cell_complete" if not missing else "selected_cell_incomplete",
        "missing_fields": missing,
        "selected_cell_id": selected_cell_id,
        "selected_risk_pct": selected_risk_pct,
        "selected_policy": selected_policy,
        "policy_identity_status": identity_status,
        "unresolved_reasons": unresolved,
        "decision_basis": _clean_str(
            trade_params.get("gtos_vnext_selected_cell_risk_decision_basis")
        ),
    }


def _selector_v4_context(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    packet = trade_params.get("gtos_vnext_selector_v4_packet")
    if not isinstance(packet, Mapping):
        packet = trade_params.get("selector_v4_packet")
    if not isinstance(packet, Mapping):
        packet = {}
    action = _clean_str(
        trade_params.get("gtos_vnext_selector_v4_action")
        or trade_params.get("selector_v4_action")
        or packet.get("action")
    )
    reason = _clean_str(
        trade_params.get("gtos_vnext_selector_v4_reason")
        or trade_params.get("selector_v4_reason")
        or packet.get("reason")
        or packet.get("final_reason")
    )
    packet_hash = _clean_str(
        trade_params.get("gtos_vnext_selector_v4_packet_hash")
        or trade_params.get("selector_v4_packet_hash")
        or packet.get("packet_hash")
        or packet.get("packet_hash_sha256")
    )
    normalized = (action or "").strip().lower().replace("_", "-")
    missing: list[str] = []
    if not action:
        missing.append("gtos_vnext_selector_v4_action")
    if not packet and not packet_hash:
        missing.append("gtos_vnext_selector_v4_packet_or_hash")
    return {
        "status": "selector_v4_complete" if not missing else "selector_v4_incomplete",
        "missing_fields": missing,
        "action": action,
        "normalized_action": normalized,
        "reason": reason,
        "packet_hash": packet_hash,
        "packet_present": bool(packet),
        "blocking_action": selector_v4_action_blocks_execution(normalized),
        "source_status": packet.get("source_status") if packet else None,
    }


def _geometry_contract_context(
    *,
    config: Mapping[str, Any] | None,
    trade_params: Mapping[str, Any],
    symbol: str,
) -> dict[str, Any]:
    raw = (
        trade_params.get("gtos_vnext_dynamic_target_stop_geometry_v4")
        or trade_params.get("gtos_vnext_target_stop_geometry_v4_packet")
        or trade_params.get("target_stop_geometry_v4")
    )
    explicit_packet_present = isinstance(raw, Mapping)
    if explicit_packet_present:
        contract = dict(raw)
    else:
        source_window_complete = trade_params.get("source_window_complete")
        if source_window_complete in (None, ""):
            source_window_complete = bool(trade_params.get("gtos_vnext_source_event_hash"))
        source_context = {
            "source_mode": trade_params.get("source_mode") or "runtime_trade_params",
            "source_path_feature_status": (
                trade_params.get("source_path_feature_status")
                or trade_params.get("gtos_vnext_source_path_feature_status")
                or "runtime_asof_execution_manager_trade_params"
            ),
            "source_window_complete": source_window_complete,
            "selected_policy_ordered_path_status": trade_params.get(
                "selected_policy_ordered_path_status"
            )
            or trade_params.get("gtos_vnext_selected_policy_ordered_path_status")
            or "asof_runtime_path_ordering_not_required_before_order_send",
            "selected_policy_same_bar_ambiguous": trade_params.get(
                "selected_policy_same_bar_ambiguous"
            )
            or trade_params.get("gtos_vnext_selected_policy_same_bar_ambiguous"),
        }
        contract = build_target_stop_geometry_v4_contract(
            config=config,
            selected_policy=trade_params.get("gtos_vnext_dynamic_policy_selected"),
            execution_policy_id=trade_params.get("gtos_vnext_execution_policy_id"),
            source_event=source_context,
            trade_params=trade_params,
            direction=trade_params.get("direction"),
            entry_price=trade_params.get("entry_price"),
            stop_loss=trade_params.get("stop_loss"),
            final_target_r=trade_params.get("gtos_vnext_dynamic_final_target_r"),
            final_target_price=trade_params.get(
                "gtos_vnext_dynamic_final_target_price"
            ),
        )
    source = contract.get("source_completeness") if isinstance(contract, Mapping) else {}
    target = contract.get("target_destination") if isinstance(contract, Mapping) else {}
    missing = []
    if not isinstance(contract, Mapping):
        missing.append("geometry_contract")
        status = "geometry_contract_missing"
    else:
        status = str(contract.get("status") or "")
        if status != "source_bound_geometry_contract_ready":
            missing.append(f"geometry_contract_status:{status or 'missing'}")
        for field in (source or {}).get("missing_source_fields") or []:
            missing.append(str(field))
        if (source or {}).get("selected_policy_same_bar_ambiguous") is True:
            missing.append("selected_policy_same_bar_ambiguous")
        if (
            target or {}
        ).get("exit_management_contract_status") == "policy_specific_management_field_gap":
            missing.append("policy_specific_management_field_gap")
    return {
        "status": status,
        "contract": contract if isinstance(contract, Mapping) else None,
        "missing_fields": sorted(dict.fromkeys(missing)),
        "explicit_packet_present": explicit_packet_present,
        "terminal_order_guard": "execution_manager_v4_blocks_gapped_geometry_before_order",
    }


def _cost_context(
    pretrade_cost_model: Mapping[str, Any] | None,
    trade_params: Mapping[str, Any],
) -> dict[str, Any]:
    model = pretrade_cost_model if isinstance(pretrade_cost_model, Mapping) else {}
    status = _clean_str(model.get("status"))
    authority = _clean_str(model.get("authority"))
    cost_source_gap_status = _clean_str(model.get("cost_source_gap_status"))
    fallback_is_authority = _truthy(model.get("candidate_cost_r_fallback_is_authority"))
    spread_r = _float_or_none(model.get("spread_r"))
    max_spread_r = _float_or_none(model.get("max_spread_r"))
    commission_status = _clean_str(
        model.get("commission_model_status")
        or trade_params.get("gtos_vnext_commission_model_status")
    )
    missing: list[str] = []
    if not model:
        missing.append("gtos_vnext_pretrade_cost_model")
    elif status not in {"PASSED", "REFUSED"}:
        missing.append("pretrade_cost_model_status_passed")
    if model:
        if authority != "broker_calibrated_replay_cost":
            missing.append(
                "pretrade_cost_model_authority_broker_calibrated_replay_cost"
            )
        if cost_source_gap_status != "source_bound_cost_authority_present":
            missing.append(
                "pretrade_cost_model_source_bound_cost_authority_present"
            )
        if fallback_is_authority:
            missing.append("pretrade_cost_model_candidate_cost_fallback_not_authority")
    if commission_status is None:
        missing.append("gtos_vnext_commission_model_status")
    return {
        "status": "cost_complete" if not missing else "cost_incomplete",
        "missing_fields": missing,
        "pretrade_cost_model_status": status,
        "pretrade_cost_model_authority": authority,
        "cost_source_gap_status": cost_source_gap_status,
        "candidate_cost_r_fallback_is_authority": fallback_is_authority,
        "spread_r": spread_r,
        "max_spread_r": max_spread_r,
        "commission_model_status": commission_status,
        "refusal_reason": model.get("refusal_reason"),
        "cost_model_source": trade_params.get("gtos_vnext_cost_model_source"),
    }


def _pending_context(
    pending: Mapping[str, Any] | None,
    trade_params: Mapping[str, Any],
) -> dict[str, Any]:
    pending = pending if isinstance(pending, Mapping) else {}
    limit_price = _float_or_none(
        pending.get("limit_price") or trade_params.get("pending_limit_price")
    )
    stop_loss = _float_or_none(pending.get("stop_loss") or trade_params.get("stop_loss"))
    current_price = _float_or_none(pending.get("current_price"))
    original_sl_distance = _float_or_none(pending.get("original_sl_distance"))
    if original_sl_distance is None and limit_price is not None and stop_loss is not None:
        original_sl_distance = abs(limit_price - stop_loss)
    entry_drift_r = None
    if (
        current_price is not None
        and limit_price is not None
        and original_sl_distance is not None
        and original_sl_distance > 0
    ):
        entry_drift_r = abs(current_price - limit_price) / original_sl_distance

    order_mode = _clean_str(
        pending.get("pending_order_mode")
        or trade_params.get("pending_order_mode")
        or "MARKET_ENTRY_OR_UNKNOWN"
    )
    stage = _clean_str(pending.get("stage")) or "market_entry"
    missing: list[str] = []
    if stage.startswith("pending") and limit_price is None:
        missing.append("pending_limit_price")
    if stage == "pending_fill_triggered" and current_price is None:
        missing.append("current_tick_price_at_pending_touch")

    return {
        "status": "pending_context_complete" if not missing else "pending_context_incomplete",
        "missing_fields": missing,
        "stage": stage,
        "pending_order_mode": order_mode,
        "pending_created_time_utc": pending.get("pending_created_time_utc")
        or trade_params.get("pending_created_time_utc"),
        "pending_candles_elapsed": pending.get("pending_candles_elapsed")
        or trade_params.get("pending_candles_elapsed"),
        "limit_price": limit_price,
        "current_price": current_price,
        "original_sl_distance": original_sl_distance,
        "entry_drift_r": entry_drift_r,
        "trigger_condition_met": pending.get("trigger_condition_met"),
        "candle_time_utc": pending.get("candle_time_utc"),
    }


def _scheduler_v4_context(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    packet = trade_params.get("gtos_vnext_scheduler_v4_packet")
    if not isinstance(packet, Mapping):
        packet = {}
    decision = packet.get("decision") if isinstance(packet.get("decision"), Mapping) else {}
    ultimate_candidate_package = _ultimate_candidate_package_shadow_context(packet)
    current_candidate_id = _clean_str(
        trade_params.get("gtos_vnext_scheduler_v4_current_candidate_id")
        or trade_params.get("candidate_id")
        or trade_params.get("gtos_vnext_candidate_id")
        or trade_params.get("gtos_vnext_selector_row_id")
    )
    selected_candidate_id = _clean_str(
        trade_params.get("gtos_vnext_scheduler_v4_selected_candidate_id")
        or decision.get("selected_candidate_id")
    )
    selected_candidate_ids_raw = (
        trade_params.get("gtos_vnext_scheduler_v4_selected_candidate_ids")
        or decision.get("selected_candidate_ids")
        or []
    )
    if isinstance(selected_candidate_ids_raw, str):
        selected_candidate_ids = [
            value.strip()
            for value in selected_candidate_ids_raw.split(",")
            if value.strip()
        ]
    elif isinstance(selected_candidate_ids_raw, (list, tuple, set)):
        selected_candidate_ids = [
            value
            for item in selected_candidate_ids_raw
            if (value := _clean_str(item))
        ]
    else:
        selected_candidate_ids = []
    if selected_candidate_id and selected_candidate_id not in selected_candidate_ids:
        selected_candidate_ids.insert(0, selected_candidate_id)
    selected_action = _clean_str(
        trade_params.get("gtos_vnext_scheduler_v4_selected_action_class")
        or decision.get("selected_action_class")
    )
    packet_hash = _clean_str(
        trade_params.get("gtos_vnext_scheduler_v4_packet_hash")
        or packet.get("packet_hash_sha256")
        or packet.get("packet_hash")
    )
    missing: list[str] = []
    if not packet:
        missing.append("gtos_vnext_scheduler_v4_packet")
    if not packet_hash:
        missing.append("gtos_vnext_scheduler_v4_packet_hash")
    if not current_candidate_id:
        missing.append("gtos_vnext_scheduler_v4_current_candidate_id")
    if not selected_candidate_ids and selected_action != "zero_trade":
        missing.append("gtos_vnext_scheduler_v4_selected_candidate_id")
    if not selected_action:
        missing.append("gtos_vnext_scheduler_v4_selected_action_class")
    missing_runtime_truth = list(
        (packet.get("source_boundary") or {}).get("missing_runtime_truth") or []
    )
    selected_option = (
        decision.get("selected_option")
        if isinstance(decision.get("selected_option"), Mapping)
        else {}
    )
    selected_options_raw = decision.get("selected_options") or ()
    selected_options = [
        option for option in selected_options_raw if isinstance(option, Mapping)
    ]
    matching_selected_options = [
        option
        for option in ([selected_option] if selected_option else []) + selected_options
        if (
            not current_candidate_id
            or _clean_str(option.get("candidate_id")) == current_candidate_id
        )
    ]
    selected_option_runtime_eligible = any(
        option.get("runtime_eligible") is True for option in matching_selected_options
    )
    replay_no_broker_authority = _replay_no_broker_authority(trade_params)
    replay_runtime_effect_now = bool(
        replay_no_broker_authority
        and selected_action not in {None, "", "zero_trade"}
        and selected_candidate_ids
        and current_candidate_id in selected_candidate_ids
        and selected_option_runtime_eligible
    )
    blocking_reason = None
    if missing_runtime_truth:
        blocking_reason = "scheduler_v4_missing_runtime_truth"
    elif selected_action == "zero_trade":
        blocking_reason = "scheduler_v4_selected_zero_trade"
    elif (
        selected_candidate_ids
        and current_candidate_id
        and current_candidate_id not in selected_candidate_ids
    ):
        blocking_reason = "scheduler_v4_candidate_not_selected"
    elif (
        decision
        and decision.get("runtime_effect_now") is not True
        and not replay_runtime_effect_now
    ):
        blocking_reason = "scheduler_v4_selected_action_not_runtime_eligible"
    return {
        "status": "scheduler_v4_complete" if not missing else "scheduler_v4_incomplete",
        "missing_fields": missing,
        "packet_present": bool(packet),
        "packet_hash": packet_hash,
        "current_candidate_id": current_candidate_id,
        "selected_candidate_id": selected_candidate_id,
        "selected_candidate_ids": selected_candidate_ids,
        "selected_action_class": selected_action,
        "runtime_effect_now": decision.get("runtime_effect_now"),
        "replay_no_broker_authority": replay_no_broker_authority,
        "replay_runtime_effect_now": replay_runtime_effect_now,
        "selected_option_runtime_eligible": selected_option_runtime_eligible,
        "missing_runtime_truth": missing_runtime_truth,
        "blocking_reason": blocking_reason,
        "ultimate_candidate_package_shadow": ultimate_candidate_package,
        "packet": packet or None,
    }


def _gate_not_false(packet: Mapping[str, Any], key: str) -> bool:
    value = packet.get(key)
    return value is not False and value not in (None, "")


def _order_calls_not_zero(packet: Mapping[str, Any]) -> bool:
    value = packet.get("order_calls")
    if value in (None, "", False, 0):
        return False
    try:
        return float(value) != 0.0
    except (TypeError, ValueError):
        return True


def _ultimate_candidate_package_shadow_context(
    scheduler_packet: Mapping[str, Any],
) -> dict[str, Any]:
    packet = scheduler_packet.get("ultimate_candidate_package_shadow")
    if not isinstance(packet, Mapping):
        decision = scheduler_packet.get("decision")
        if isinstance(decision, Mapping):
            packet = decision.get("ultimate_candidate_package_shadow")
    if not isinstance(packet, Mapping):
        return {
            "status": "ultimate_candidate_package_shadow_not_present",
            "packet_present": False,
            "blocking_reason": None,
            "gate_violations": [],
            "packet": None,
        }

    policy = packet.get("execution_policy_shadow")
    if not isinstance(policy, Mapping):
        policy = {}

    gate_violations: list[str] = []
    for gate in (
        "apply_to_execution",
        "live_activation_allowed_by_config",
        "final_package_selected_by_config",
        "runtime_effect_now",
        "candidate_use_allowed_now",
        "selected_package_denominator_use_allowed",
        "denominator_expansion_allowed",
        "clean_label_use_allowed",
        "training_use_allowed",
        "model_training_allowed",
        "final_package_selection_allowed",
        "deployment_dossier_allowed",
        "vps_handoff_allowed",
        "live_execution_activation_allowed",
        "broker_account_order_history_deal_position_mutation_allowed",
        "broker_operation",
        "paid_api_or_vendor_call",
    ):
        if _gate_not_false(packet, gate):
            gate_violations.append(f"{gate}_not_false")

    if packet.get("default_off") is not True:
        gate_violations.append("default_off_not_true")
    if packet.get("shadow_only") is not True:
        gate_violations.append("shadow_only_not_true")
    if packet.get("selected_candidate_id") not in (None, ""):
        gate_violations.append("selected_candidate_id_not_closed")

    approved_risk = _float_or_none(packet.get("approved_risk_pct"))
    if approved_risk is not None and approved_risk != 0.0:
        gate_violations.append("approved_risk_pct_not_zero")
    if _order_calls_not_zero(packet):
        gate_violations.append("order_calls_not_zero")

    if policy:
        for gate in (
            "apply_to_execution",
            "live_activation_allowed_by_config",
            "final_package_selected_by_config",
            "runtime_effect_now",
            "candidate_use_allowed_now",
            "selected_package_denominator_use_allowed",
            "denominator_expansion_allowed",
            "clean_label_use_allowed",
            "training_use_allowed",
            "model_training_allowed",
            "final_package_selection_allowed",
            "deployment_dossier_allowed",
            "vps_handoff_allowed",
            "live_execution_activation_allowed",
            "broker_account_order_history_deal_position_mutation_allowed",
            "broker_operation",
            "paid_api_or_vendor_call",
            "execution_order_type_policy_selectable",
            "missed_fill_opportunity_cost_allowed",
            "limit_first_vs_guarded_market_comparison_allowed",
            "broker_real_expectancy_claim_allowed",
        ):
            if _gate_not_false(policy, gate):
                gate_violations.append(f"execution_policy_shadow.{gate}_not_false")
        if policy.get("selected_order_type_architecture") not in (None, ""):
            gate_violations.append(
                "execution_policy_shadow.selected_order_type_architecture_not_closed"
            )
        approved_policy_risk = _float_or_none(policy.get("approved_risk_pct"))
        if approved_policy_risk is not None and approved_policy_risk != 0.0:
            gate_violations.append(
                "execution_policy_shadow.approved_risk_pct_not_zero"
            )
        if _order_calls_not_zero(policy):
            gate_violations.append("execution_policy_shadow.order_calls_not_zero")

    blocking_reason = (
        "ultimate_candidate_package_shadow_authority_not_closed"
        if gate_violations
        else None
    )
    return {
        "status": (
            "default_off_shadow_authority_closed"
            if blocking_reason is None
            else "ultimate_candidate_package_shadow_authority_open"
        ),
        "packet_present": True,
        "packet_hash": _clean_str(
            packet.get("packet_hash_sha256") or packet.get("packet_hash")
        ),
        "decision_status": packet.get("decision_status"),
        "shadow_selected_candidate_id": packet.get("shadow_selected_candidate_id"),
        "selected_candidate_id": packet.get("selected_candidate_id"),
        "approved_risk_pct": approved_risk,
        "runtime_effect_now": packet.get("runtime_effect_now"),
        "live_execution_activation_allowed": packet.get(
            "live_execution_activation_allowed"
        ),
        "final_package_selection_allowed": packet.get(
            "final_package_selection_allowed"
        ),
        "order_calls": packet.get("order_calls"),
        "execution_policy_status": policy.get("policy_status"),
        "selected_order_type_architecture": policy.get(
            "selected_order_type_architecture"
        ),
        "execution_order_type_policy_selectable": policy.get(
            "execution_order_type_policy_selectable"
        ),
        "missed_fill_opportunity_cost_allowed": policy.get(
            "missed_fill_opportunity_cost_allowed"
        ),
        "gate_violations": gate_violations,
        "blocking_reason": blocking_reason,
        "packet": dict(packet),
    }


def _prop_firm_headroom_context(
    *,
    config: Mapping[str, Any] | None,
    trade_params: Mapping[str, Any],
    requested_risk_pct: Any,
    now_utc: datetime,
) -> dict[str, Any]:
    snapshot = find_prop_firm_headroom_snapshot_v4(trade_params)
    snapshot_source = "prebuilt_snapshot" if snapshot is not None else None
    if snapshot is None:
        account_state = find_prop_firm_headroom_account_state_v4(trade_params)
        if account_state is not None:
            snapshot = build_prop_firm_headroom_snapshot_v4_from_account_state(
                account_state,
                config=config,
                now_utc=now_utc,
            )
            snapshot_source = "runtime_account_state_adapter"
    evaluation = evaluate_prop_firm_headroom_snapshot_v4(
        snapshot=snapshot,
        requested_risk_pct=requested_risk_pct,
        config=config,
        now_utc=now_utc,
    )
    return {
        "status": (
            "source_bound_broker_real_headroom_ready"
            if evaluation.allowed
            else "source_gap_or_invalid_headroom"
        ),
        "blocking_reason": None
        if evaluation.allowed
        else f"prop_firm_headroom_v4_{evaluation.reason}",
        "missing_fields": list(evaluation.missing_fields),
        "requested_risk_pct": evaluation.requested_risk_pct,
        "max_allowed_new_trade_risk_pct": evaluation.max_allowed_new_trade_risk_pct,
        "source_status": evaluation.source_status,
        "snapshot_source": snapshot_source,
        "evidence_class": evaluation.evidence_class,
        "captured_at_utc": evaluation.captured_at_utc,
        "snapshot_age_seconds": evaluation.snapshot_age_seconds,
        "packet": evaluation.to_packet(),
        "terminal_order_guard": (
            "execution_manager_v4_requires_prop_firm_headroom_snapshot_before_order"
        ),
    }


def _lifecycle_context(trade_params: Mapping[str, Any]) -> dict[str, Any]:
    packet = trade_params.get("gtos_vnext_same_symbol_lifecycle_v4_packet")
    if not isinstance(packet, Mapping):
        packet = {}
    raw_action = _clean_str(
        trade_params.get("gtos_vnext_same_symbol_lifecycle_action")
        or packet.get("action")
        or trade_params.get("gtos_vnext_lifecycle_action")
    )
    action = _normalize_lifecycle_action(raw_action)
    permitted = packet.get("permitted_order_intent")
    replay_reconcile = _lifecycle_replay_reconcile_context(
        trade_params,
        action=action,
        permitted=permitted,
    )
    effective_packet: Mapping[str, Any] = packet
    if replay_reconcile["applied"] and replay_reconcile["reconciled_action"]:
        action = replay_reconcile["reconciled_action"]
        permitted = True
        effective_packet = {
            **dict(packet),
            "action": action,
            "permitted_order_intent": True,
            "original_action": replay_reconcile["original_action"],
            "original_permitted_order_intent": replay_reconcile[
                "original_permitted_order_intent"
            ],
            "replay_lifecycle_reconcile_applied": True,
            "replay_lifecycle_reconcile_sources": replay_reconcile[
                "reconcile_sources"
            ],
            "replay_lifecycle_reconcile_reason": replay_reconcile[
                "permission_reconcile_reason"
            ],
        }
    missing: list[str] = []
    if not packet:
        missing.append("gtos_vnext_same_symbol_lifecycle_v4_packet")
    if not action:
        missing.append("gtos_vnext_same_symbol_lifecycle_action")
    blocking_reason = None
    if packet and permitted is False:
        blocking_reason = f"same_symbol_lifecycle_v4_not_permitted:{action or 'unknown'}"
    if action in LIFECYCLE_MANAGER_ACTIONS and not replay_reconcile["applied"]:
        blocking_reason = f"same_symbol_lifecycle_v4_manager_action_required:{action}"
    return {
        "status": (
            "same_symbol_lifecycle_v4_complete"
            if not missing
            else "same_symbol_lifecycle_v4_incomplete"
        ),
        "missing_fields": missing,
        "action": action,
        "permitted_order_intent": permitted,
        "original_action": replay_reconcile["original_action"],
        "original_permitted_order_intent": replay_reconcile[
            "original_permitted_order_intent"
        ],
        "blocking_reason": blocking_reason,
        "packet": effective_packet or None,
        "replay_lifecycle_reconcile": replay_reconcile,
        "ticket_bound_state_required": True,
        "expected_entry_ticket_fields": [
            "trade_state.ticket",
            "entry_order_ticket",
            "entry_deal_ticket",
        ],
        "same_symbol_owner": "same_symbol_same_instrument_lifecycle_v4",
        "same_symbol_handoff_status": "dependency_contract_required_before_v4_promotion",
        "no_duplicate_exposure_rule": "execution_must_consume_lifecycle_owner_decision_before_broker_order",
        "requested_lifecycle_action": trade_params.get("gtos_vnext_lifecycle_action"),
    }


def evaluate_execution_manager_v4(
    *,
    config: Mapping[str, Any] | None,
    trade_params: Mapping[str, Any],
    symbol: str,
    broker_symbol: str | None = None,
    pretrade_cost_model: Mapping[str, Any] | None = None,
    pending: Mapping[str, Any] | None = None,
    trigger: str | None = None,
    generated_at_utc: str | None = None,
) -> ExecutionManagerV4Decision:
    """Build and evaluate a V4 execution packet.

    The packet is always source-bound metadata. It blocks only when the V4
    component is both enabled and applied to execution in config.
    """
    effective_generated_at_utc = generated_at_utc or _now_iso()
    evaluation_now_utc = _utc_datetime(effective_generated_at_utc)
    cfg = _runtime_cfg(config)
    enabled = execution_manager_v4_enabled(config)
    apply_to_execution = execution_manager_v4_apply_to_execution(config)
    production_path = _truthy(trade_params.get("gtos_vnext_production_execution_path"))
    dynamic_applied = _truthy(trade_params.get("gtos_vnext_dynamic_policy_applied"))
    runtime_path = bool(production_path or dynamic_applied)
    replay_no_broker_authority = _replay_no_broker_authority(trade_params)

    source = _source_completeness(trade_params)
    dynamic_policy = _dynamic_policy_context(trade_params)
    selected_cell = _selected_cell_context(trade_params)
    selector_v4 = _selector_v4_context(trade_params)
    scheduler_v4 = _scheduler_v4_context(trade_params)
    geometry_contract = _geometry_contract_context(
        config=config,
        trade_params=trade_params,
        symbol=symbol,
    )
    cost = _cost_context(pretrade_cost_model, trade_params)
    pending_context = _pending_context(pending, trade_params)
    lifecycle = _lifecycle_context(trade_params)
    prop_firm_headroom = _prop_firm_headroom_context(
        config=config,
        trade_params=trade_params,
        requested_risk_pct=selected_cell.get("selected_risk_pct"),
        now_utc=evaluation_now_utc,
    )
    lifecycle_trade_params = _trade_params_with_reconciled_lifecycle(
        trade_params,
        lifecycle,
    )
    broker_lifecycle_capture = build_broker_order_lifecycle_capture_v4(
        stage="pre_order_contract",
        trade_params=lifecycle_trade_params,
        symbol=symbol,
        broker_symbol=broker_symbol or symbol,
        pretrade_cost_model=pretrade_cost_model,
        generated_at_utc=effective_generated_at_utc,
    )

    fatal: list[str] = []
    warnings: list[str] = []

    source_required = _truthy(
        cfg.get("execution_manager_v4_source_completeness_required", True)
    )
    dynamic_required = _truthy(
        cfg.get("execution_manager_v4_dynamic_policy_required", True)
    )
    selected_cell_required = _truthy(
        cfg.get("execution_manager_v4_selected_cell_risk_required", True)
    )
    selector_required = _truthy(
        cfg.get("execution_manager_v4_selector_v4_packet_required", False)
    )
    geometry_required = _truthy(
        cfg.get("execution_manager_v4_geometry_contract_required", True)
    )
    explicit_geometry_required = _truthy(
        cfg.get("execution_manager_v4_explicit_geometry_packet_required", True)
    )
    cost_required = _truthy(cfg.get("execution_manager_v4_cost_model_required", True))
    lifecycle_required = _truthy(
        cfg.get("execution_manager_v4_lifecycle_owner_required_for_promotion", True)
    )
    scheduler_required = _truthy(
        cfg.get("execution_manager_v4_scheduler_v4_packet_required", True)
    )
    prop_firm_headroom_required = _truthy(
        cfg.get("execution_manager_v4_prop_firm_headroom_required", True)
    )
    broker_lifecycle_capture_required = _truthy(
        cfg.get("execution_manager_v4_broker_lifecycle_capture_contract_required", True)
    )

    if runtime_path and source_required and source["missing_fields"]:
        fatal.extend(f"missing_source:{field}" for field in source["missing_fields"])
    if runtime_path and dynamic_required and dynamic_policy["missing_fields"]:
        fatal.extend(
            f"missing_dynamic_policy:{field}" for field in dynamic_policy["missing_fields"]
        )
    if runtime_path and selected_cell_required and selected_cell["missing_fields"]:
        fatal.extend(
            f"missing_selected_cell:{field}" for field in selected_cell["missing_fields"]
        )
    if runtime_path and selector_required and selector_v4["missing_fields"]:
        fatal.extend(f"missing_selector_v4:{field}" for field in selector_v4["missing_fields"])
    if runtime_path and selector_v4["blocking_action"]:
        fatal.append(
            "selector_v4_action_blocks_execution:"
            f"{selector_v4['normalized_action']}"
        )
    if runtime_path and scheduler_required and scheduler_v4["missing_fields"]:
        fatal.extend(
            f"missing_scheduler_v4:{field}" for field in scheduler_v4["missing_fields"]
        )
    if runtime_path and scheduler_v4["blocking_reason"]:
        fatal.append(scheduler_v4["blocking_reason"])
    package_block = scheduler_v4["ultimate_candidate_package_shadow"].get(
        "blocking_reason"
    )
    if runtime_path and package_block:
        fatal.append(package_block)
    if runtime_path and prop_firm_headroom_required and prop_firm_headroom["blocking_reason"]:
        if (
            replay_no_broker_authority
            and prop_firm_headroom["blocking_reason"]
            == "prop_firm_headroom_v4_snapshot_not_broker_real"
        ):
            warnings.append(
                "live_promotion_only:"
                f"{prop_firm_headroom['blocking_reason']}"
            )
        else:
            fatal.append(prop_firm_headroom["blocking_reason"])
    if (
        runtime_path
        and broker_lifecycle_capture_required
        and broker_lifecycle_capture["pre_order_capture_contract"]["missing_fields"]
    ):
        fatal.extend(
            f"missing_broker_lifecycle_capture:{field}"
            for field in broker_lifecycle_capture["pre_order_capture_contract"][
                "missing_fields"
            ]
        )
    if runtime_path and geometry_required and geometry_contract["missing_fields"]:
        fatal.extend(
            f"missing_geometry_contract:{field}"
            for field in geometry_contract["missing_fields"]
        )
    if (
        runtime_path
        and geometry_required
        and explicit_geometry_required
        and not geometry_contract["explicit_packet_present"]
    ):
        fatal.append("missing_geometry_contract:explicit_geometry_packet_required")
    if runtime_path and cost_required and cost["missing_fields"]:
        fatal.extend(f"missing_cost:{field}" for field in cost["missing_fields"])
    if runtime_path and lifecycle_required and lifecycle["missing_fields"]:
        fatal.extend(
            f"missing_lifecycle:{field}" for field in lifecycle["missing_fields"]
        )
    if runtime_path and lifecycle["blocking_reason"]:
        fatal.append(lifecycle["blocking_reason"])
    elif lifecycle_required and not runtime_path:
        warnings.append("same_symbol_lifecycle_owner_packet_required_before_promotion")

    max_pending_drift_r = _float_or_none(
        cfg.get("execution_manager_v4_max_pending_fill_entry_drift_r", 0.25)
    )
    entry_drift_r = pending_context.get("entry_drift_r")
    if (
        pending_context.get("stage") == "pending_fill_triggered"
        and max_pending_drift_r is not None
        and entry_drift_r is not None
        and entry_drift_r > max_pending_drift_r
    ):
        fatal.append(
            "pending_fill_entry_drift_r_exceeds_limit:"
            f"{entry_drift_r:.6f}>{max_pending_drift_r:.6f}"
        )

    if not enabled:
        action = "disabled"
        should_block = False
        runtime_status = "disabled_by_config"
    elif apply_to_execution and fatal:
        action = "block"
        should_block = True
        runtime_status = "apply_to_execution_blocked"
    elif apply_to_execution:
        action = "allow"
        should_block = False
        runtime_status = "apply_to_execution_allowed"
    else:
        action = "observe_only"
        should_block = False
        runtime_status = "configured_observe_only_no_block"

    packet = {
        "schema_version": SCHEMA_VERSION,
        "component": COMPONENT,
        "generated_at_utc": effective_generated_at_utc,
        "evidence_class": EVIDENCE_CLASS,
        "result_use_status": RESULT_USE_STATUS,
        "validation_result_status": False,
        "outcome_result_rows_status": False,
        "broker_runtime_change_status": False,
        "config": {
            "enabled": enabled,
            "apply_to_execution": apply_to_execution,
            "runtime_status": runtime_status,
            "production_code_disposition": (
                "active" if apply_to_execution else "observe_only"
            )
            if enabled
            else "disabled",
        },
        "action": action,
        "should_block": should_block,
        "fatal_reasons": fatal,
        "warning_reasons": warnings,
        "identity": {
            "symbol": symbol,
            "broker_symbol": broker_symbol or symbol,
            "trigger": trigger,
            "trade_id": trade_params.get("trade_id"),
            "candidate_id": trade_params.get("candidate_id"),
            "production_path": production_path,
            "dynamic_policy_applied": dynamic_applied,
            "replay_no_broker_authority": replay_no_broker_authority,
            "replay_broker_mutation_enabled": trade_params.get(
                "gtos_vnext_replay_broker_mutation_enabled"
            ),
        },
        "source_completeness": source,
        "selector_v4": selector_v4,
        "scheduler_v4": scheduler_v4,
        "geometry_contract": geometry_contract,
        "cost_context": cost,
        "entry_timing": {
            "entry_price": _float_or_none(trade_params.get("entry_price")),
            "stop_loss": _float_or_none(trade_params.get("stop_loss")),
            "take_profit_1": _float_or_none(trade_params.get("take_profit_1")),
            "decision_time_utc": trade_params.get("decision_time_utc"),
            "pending_context": pending_context,
            "falsification_labels_required": [
                "MFE",
                "MAE",
                "time_to_profit",
                "time_to_destination",
                "giveback",
                "stale_thesis",
                "stop_target_efficiency",
                "opportunity_cost",
            ],
        },
        "pending_intent_contract": {
            "pending_order_mode": pending_context.get("pending_order_mode"),
            "native_pending_broker_ticket_required_if_native": True,
            "internal_candle_polled_intent_must_log_touch_cancel_expiry": True,
            "historical_pending_truth_status": "non_generatable_without_forward_capture",
        },
        "lifecycle_contract": lifecycle,
        "broker_order_lifecycle_capture_v4": broker_lifecycle_capture,
        "prop_firm_headroom_contract": prop_firm_headroom,
        "semantic_dependencies": {
            "same_symbol_same_instrument_lifecycle_v4": "ticket_lifecycle_owner",
            "probability_debate_team_engine_v4": "numeric_action_theses_owner",
            "follow_avoid_mixed_numeric_confluence_v4": "numeric_source_confluence_owner",
            "prop_firm_headroom_v4": "broker_real_account_headroom_authority",
            "broker_order_lifecycle_capture_v4": "ticket_order_deal_cost_lifecycle_authority",
            "cost_swap_slippage_broker_constraint_engine": "broker_cost_constraints_owner",
            "feature_label_store": "future_ml_label_capture_owner",
        },
        "dynamic_policy_context": dynamic_policy,
        "selected_cell_context": selected_cell,
    }

    return ExecutionManagerV4Decision(
        packet=packet,
        action=action,
        should_block=should_block,
        fatal_reasons=tuple(fatal),
        warning_reasons=tuple(warnings),
    )


def record_execution_manager_v4_decision(
    packet: Mapping[str, Any],
    *,
    config: Mapping[str, Any] | None = None,
    log_path: str | Path | None = None,
) -> None:
    """Append one V4 decision packet. This is best-effort telemetry."""
    cfg = _runtime_cfg(config)
    if not execution_manager_v4_enabled(config) and "execution_manager_v4_log_enabled" not in cfg:
        return
    if not _truthy(cfg.get("execution_manager_v4_log_enabled", True)):
        return
    target = Path(log_path or cfg.get("execution_manager_v4_log_path") or DEFAULT_LOG_PATH)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(packet, sort_keys=True, default=str) + "\n"
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
        logger.warning("Execution Manager V4 decision logging failed: %s", exc)


__all__ = [
    "COMPONENT",
    "EVIDENCE_CLASS",
    "RESULT_USE_STATUS",
    "SCHEMA_VERSION",
    "ExecutionManagerV4Decision",
    "evaluate_execution_manager_v4",
    "execution_manager_v4_apply_to_execution",
    "execution_manager_v4_enabled",
    "record_execution_manager_v4_decision",
]
