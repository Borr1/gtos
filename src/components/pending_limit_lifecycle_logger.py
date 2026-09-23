"""Pending-limit lifecycle shadow logger.

This module records local pending-limit intent state transitions as append-only
JSONL. It is observation-only: failures are swallowed and no return value is
used by trading code.
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from src.components.pending_nofill_lifecycle_v4 import build_lifecycle_v4_fields

logger = logging.getLogger(__name__)

try:  # pragma: no cover - exercised on Windows in production
    import msvcrt
except ImportError:  # pragma: no cover - non-Windows fallback
    msvcrt = None  # type: ignore[assignment]

try:  # pragma: no cover - non-Windows fallback
    import fcntl
except ImportError:  # pragma: no cover - Windows
    fcntl = None  # type: ignore[assignment]

PENDING_LIMIT_LIFECYCLE_LOG_PATH = "shadow_logs/pending_limit_lifecycle.jsonl"
SCHEMA_VERSION = "pending_limit_lifecycle_v1"
RESULT_USE_STATUS = "RESULT_MATERIALIZATION_REQUIRED"
EVIDENCE_CLASS = "INTERNAL_LIMIT_LIFECYCLE"
INTERNAL_PENDING_ORDER_MODE = "INTERNAL_CANDLE_POLLED_INTENT"
_JSONL_LOCK_RETRIES = 200
_JSONL_LOCK_SLEEP_SECONDS = 0.025

VALID_STATES = {
    "still_pending_no_trigger",
    "expired_48h",
    "source_repair_failed_retry",
    "triggered_tick_missing_retry",
    "execution_manager_v4_blocked",
    "cancelled_wrong_side",
    "cancelled_sl_too_close",
    "cancelled_target_reached_without_fill",
    "order_send_success_filled",
    "order_send_failed_retry",
    "manual_or_system_cancelled",
    "unknown_pending_lifecycle_state",
    "runtime_halt_cancelled_no_order_send",
}

DENOMINATOR_FORWARD_CAPTURE_RUNTIME_CONFIG_FIELD = (
    "denominator_forward_capture_runtime_config"
)
DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_FIELD = "denominator_forward_capture_log_path"
DENOMINATOR_FORWARD_CAPTURE_REQUIREMENT_FAMILIES_FIELD = (
    "denominator_forward_capture_requirement_families"
)
DENOMINATOR_FORWARD_CAPTURE_PENDING_CREATED_FAMILY = (
    "pending_created_exact_decision_time"
)
DENOMINATOR_FORWARD_CAPTURE_M15_GRID_FAMILY = "m15_grid_order_lifecycle"
DENOMINATOR_FORWARD_CAPTURE_DEFAULT_REQUIREMENT_FAMILIES = (
    DENOMINATOR_FORWARD_CAPTURE_PENDING_CREATED_FAMILY,
    DENOMINATOR_FORWARD_CAPTURE_M15_GRID_FAMILY,
)
_DENOMINATOR_FORWARD_CAPTURE_FLAT_CONFIG_KEYS = (
    "denominator_forward_capture_contract_enabled",
    "denominator_forward_capture_contract_log_enabled",
    "denominator_forward_capture_contract_log_path",
)
ULTIMATE_CANDIDATE_PACKAGE_SHADOW_CONTEXT_FIELDS = (
    "ultimate_candidate_package_shadow_status",
    "ultimate_candidate_package_shadow_authority_closed",
    "ultimate_candidate_package_shadow_packet_present",
    "ultimate_candidate_package_shadow_packet_hash",
    "ultimate_candidate_package_shadow_decision_status",
    "ultimate_candidate_package_shadow_selected_candidate_id",
    "ultimate_candidate_package_selected_candidate_id",
    "ultimate_candidate_package_approved_risk_pct",
    "ultimate_candidate_package_runtime_effect_now",
    "ultimate_candidate_package_live_execution_activation_allowed",
    "ultimate_candidate_package_final_package_selection_allowed",
    "ultimate_candidate_package_order_calls",
    "ultimate_candidate_package_execution_policy_status",
    "ultimate_candidate_package_selected_order_type_architecture",
    "ultimate_candidate_package_execution_order_type_policy_selectable",
    "ultimate_candidate_package_gate_violations",
)

_FILL_LABEL_BY_STATE = {
    "still_pending_no_trigger": "no_fill_still_pending",
    "expired_48h": "no_fill_expired",
    "source_repair_failed_retry": "no_fill_source_repair_failed_retry",
    "triggered_tick_missing_retry": "triggered_tick_missing_retry",
    "execution_manager_v4_blocked": "no_fill_execution_manager_v4_blocked",
    "cancelled_wrong_side": "no_fill_cancelled_wrong_side",
    "cancelled_sl_too_close": "no_fill_cancelled_sl_too_close",
    "cancelled_target_reached_without_fill": "no_fill_cancelled_target_reached_without_entry_touch",
    "order_send_success_filled": "internal_filled_broker_ticket_known",
    "order_send_failed_retry": "triggered_order_send_failed_retry",
    "manual_or_system_cancelled": "no_fill_cancelled",
    "unknown_pending_lifecycle_state": "unknown_pending_lifecycle_state",
    "runtime_halt_cancelled_no_order_send": "no_fill_runtime_halt_cancelled",
}

REQUIRED_FIELDS = (
    "schema_version",
    "created_at_utc",
    "timestamp_utc",
    "symbol",
    "broker_symbol",
    "source_symbol",
    "session",
    "kill_zone",
    "side",
    "regime",
    "candidate_id",
    "trade_id",
    "evidence_class",
    "decision_time_utc",
    "asof_cutoff_utc",
    "source_file",
    "source_hash",
    "no_leak_status",
    "result_use_status",
    "pending_created_time_utc",
    "pending_ticket",
    "pending_lifecycle_v4_id",
    "pending_order_mode",
    "broker_pending_order_created",
    "mt5_order_ticket",
    "native_pending_order_type",
    "risk_reserved_pct",
    "risk_reserved_cash",
    "risk_reservation_status",
    "risk_reservation_scope",
    "risk_reservation_source",
    "risk_reservation_broker_namespace",
    "risk_reservation_release_reason",
    "fill_time_utc",
    "expiry_time_utc",
    "cancel_reason",
    "pending_horizon_start_utc",
    "pending_horizon_end_utc",
    "cancel_expiry_reason_status",
    "broker_fill_state",
    "entry_price",
    "stop_loss",
    "take_profit_1",
    "spread",
    "decision_spread_value_source_safe",
    "decision_spread_unit",
    "entry_touch_spread_value_source_safe",
    "entry_touch_spread_unit",
    "slippage_price",
    "actual_r",
    "synthetic_path_r",
    "fill_no_fill_label",
    "checked_candle_time_utc",
    "checked_candle_open",
    "checked_candle_high",
    "checked_candle_low",
    "checked_candle_close",
    "tick_bid",
    "tick_ask",
    "source_branch",
    "check_context",
    "candles_elapsed_before",
    "candles_elapsed_after",
    "trigger_condition_met",
    "terminal_area_touch_status",
    "terminal_area_first_touch_utc",
    "protective_area_touch_status",
    "protective_area_first_touch_utc",
    "event_order_resolution_method",
    "same_tick_same_bar_ambiguity_status",
    "tick_available",
    "current_price_used",
    "wrong_side_abort",
    "sl_too_close_abort",
    "order_send_attempted",
    "order_send_success",
    "trade_state_ticket",
    "mt5_position_ticket",
    "mt5_entry_order_ticket",
    "mt5_entry_deal_ticket",
    "order_result_retcode",
    "filled_order_position_join_keys",
    "exact_r_join_key_status",
    "ultimate_candidate_package_shadow_status",
    "ultimate_candidate_package_shadow_authority_closed",
    "ultimate_candidate_package_shadow_packet_present",
    "ultimate_candidate_package_shadow_packet_hash",
    "ultimate_candidate_package_shadow_decision_status",
    "ultimate_candidate_package_shadow_selected_candidate_id",
    "ultimate_candidate_package_selected_candidate_id",
    "ultimate_candidate_package_approved_risk_pct",
    "ultimate_candidate_package_runtime_effect_now",
    "ultimate_candidate_package_live_execution_activation_allowed",
    "ultimate_candidate_package_final_package_selection_allowed",
    "ultimate_candidate_package_order_calls",
    "ultimate_candidate_package_execution_policy_status",
    "ultimate_candidate_package_selected_order_type_architecture",
    "ultimate_candidate_package_execution_order_type_policy_selectable",
    "ultimate_candidate_package_gate_violations",
    "intent_after_check",
    "record_path",
    "raw_data_m15_count",
    "latest_m15_time_utc",
    "last_limit_check_candle_time_before",
    "reason",
    "pending_lifecycle_v4_schema_version",
    "pending_lifecycle_v4_state",
    "pending_lifecycle_v4_state_group",
    "pending_lifecycle_v4_event_family",
    "pending_lifecycle_v4_terminal",
    "pending_lifecycle_v4_transition_status",
    "broker_ticket_truth_status",
    "path_touch_ordering_status",
    "v4_source_completeness_status",
    "ftmo_no_copy_boundary",
)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        dt = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)


def _capture_noneish(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) == 0
    return False


def _first_capture_value(*values: Any) -> Any:
    for value in values:
        if not _capture_noneish(value):
            return value
    return None


def _set_capture_default(event: dict[str, Any], key: str, value: Any) -> None:
    if _capture_noneish(event.get(key)) and not _capture_noneish(value):
        event[key] = value


def _clean_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


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


def _first_mapping(*values: Any) -> Mapping[str, Any]:
    for value in values:
        if isinstance(value, Mapping) and value:
            return value
    return {}


def _ultimate_candidate_package_shadow_source(
    fields: Mapping[str, Any],
) -> Mapping[str, Any]:
    scheduler_packet = _mapping(fields.get("gtos_vnext_scheduler_v4_packet"))
    scheduler_decision = _mapping(scheduler_packet.get("decision"))
    execution_packet = _mapping(fields.get("gtos_vnext_execution_manager_v4_packet"))
    execution_scheduler = _mapping(execution_packet.get("scheduler_v4"))
    execution_scheduler_packet = _mapping(execution_scheduler.get("packet"))
    execution_scheduler_decision = _mapping(execution_scheduler_packet.get("decision"))

    return _first_mapping(
        fields.get("ultimate_candidate_package_shadow"),
        scheduler_packet.get("ultimate_candidate_package_shadow"),
        scheduler_decision.get("ultimate_candidate_package_shadow"),
        execution_scheduler.get("ultimate_candidate_package_shadow"),
        execution_scheduler_packet.get("ultimate_candidate_package_shadow"),
        execution_scheduler_decision.get("ultimate_candidate_package_shadow"),
    )


def _ultimate_candidate_package_shadow_summary(
    fields: Mapping[str, Any],
) -> dict[str, Any]:
    source = _ultimate_candidate_package_shadow_source(fields)
    if not source:
        return {
            "status": "ultimate_candidate_package_shadow_not_present",
            "authority_closed": None,
            "packet_present": False,
            "packet_hash": None,
            "decision_status": None,
            "shadow_selected_candidate_id": None,
            "selected_candidate_id": None,
            "approved_risk_pct": None,
            "runtime_effect_now": None,
            "live_execution_activation_allowed": None,
            "final_package_selection_allowed": None,
            "order_calls": None,
            "execution_policy_status": None,
            "selected_order_type_architecture": None,
            "execution_order_type_policy_selectable": None,
            "gate_violations": [],
            "summary": {
                "status": "ultimate_candidate_package_shadow_not_present",
                "packet_present": False,
                "authority_closed": None,
            },
        }

    packet = _mapping(source.get("packet")) or source
    policy = _mapping(packet.get("execution_policy_shadow"))
    gate_violations = list(source.get("gate_violations") or [])

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
        violation = f"{gate}_not_false"
        if _gate_not_false(packet, gate) and violation not in gate_violations:
            gate_violations.append(violation)

    for gate, expected in (("default_off", True), ("shadow_only", True)):
        violation = f"{gate}_not_true"
        if packet.get(gate) is not expected and violation not in gate_violations:
            gate_violations.append(violation)

    if packet.get("selected_candidate_id") not in (None, ""):
        violation = "selected_candidate_id_not_closed"
        if violation not in gate_violations:
            gate_violations.append(violation)

    approved_risk = _float_or_none(
        source.get("approved_risk_pct", packet.get("approved_risk_pct"))
    )
    if approved_risk is not None and approved_risk != 0.0:
        violation = "approved_risk_pct_not_zero"
        if violation not in gate_violations:
            gate_violations.append(violation)
    if _order_calls_not_zero(packet):
        violation = "order_calls_not_zero"
        if violation not in gate_violations:
            gate_violations.append(violation)

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
            violation = f"execution_policy_shadow.{gate}_not_false"
            if _gate_not_false(policy, gate) and violation not in gate_violations:
                gate_violations.append(violation)
        if policy.get("selected_order_type_architecture") not in (None, ""):
            violation = "execution_policy_shadow.selected_order_type_architecture_not_closed"
            if violation not in gate_violations:
                gate_violations.append(violation)
        policy_risk = _float_or_none(policy.get("approved_risk_pct"))
        if policy_risk is not None and policy_risk != 0.0:
            violation = "execution_policy_shadow.approved_risk_pct_not_zero"
            if violation not in gate_violations:
                gate_violations.append(violation)
        if _order_calls_not_zero(policy):
            violation = "execution_policy_shadow.order_calls_not_zero"
            if violation not in gate_violations:
                gate_violations.append(violation)

    authority_closed = not gate_violations
    status = (
        source.get("status")
        if source.get("status")
        in {
            "default_off_shadow_authority_closed",
            "ultimate_candidate_package_shadow_authority_open",
        }
        else (
            "default_off_shadow_authority_closed"
            if authority_closed
            else "ultimate_candidate_package_shadow_authority_open"
        )
    )
    execution_policy_status = _first_capture_value(
        source.get("execution_policy_status"),
        policy.get("policy_status"),
    )
    selected_order_type = _first_capture_value(
        source.get("selected_order_type_architecture"),
        policy.get("selected_order_type_architecture"),
    )
    order_type_selectable = _first_capture_value(
        source.get("execution_order_type_policy_selectable"),
        policy.get("execution_order_type_policy_selectable"),
    )
    packet_hash = _first_capture_value(
        source.get("packet_hash"),
        source.get("packet_hash_sha256"),
        packet.get("packet_hash_sha256"),
        packet.get("packet_hash"),
    )
    summary = {
        "status": status,
        "authority_closed": authority_closed,
        "packet_present": True,
        "packet_hash": packet_hash,
        "decision_status": _first_capture_value(
            source.get("decision_status"),
            packet.get("decision_status"),
        ),
        "shadow_selected_candidate_id": _first_capture_value(
            source.get("shadow_selected_candidate_id"),
            packet.get("shadow_selected_candidate_id"),
        ),
        "selected_candidate_id": _first_capture_value(
            source.get("selected_candidate_id"),
            packet.get("selected_candidate_id"),
        ),
        "approved_risk_pct": approved_risk,
        "runtime_effect_now": _first_capture_value(
            source.get("runtime_effect_now"),
            packet.get("runtime_effect_now"),
        ),
        "live_execution_activation_allowed": _first_capture_value(
            source.get("live_execution_activation_allowed"),
            packet.get("live_execution_activation_allowed"),
        ),
        "final_package_selection_allowed": _first_capture_value(
            source.get("final_package_selection_allowed"),
            packet.get("final_package_selection_allowed"),
        ),
        "order_calls": _first_capture_value(
            source.get("order_calls"),
            packet.get("order_calls"),
        ),
        "execution_policy_status": execution_policy_status,
        "selected_order_type_architecture": selected_order_type,
        "execution_order_type_policy_selectable": order_type_selectable,
        "gate_violations": gate_violations,
    }
    return {**summary, "summary": summary}


def _derive_stable_decision_window_id(row: dict[str, Any]) -> str | None:
    explicit = _first_capture_value(
        row.get("stable_decision_window_id"),
        row.get("decision_window_id"),
        row.get("gtos_vnext_decision_window_id"),
    )
    if explicit is not None:
        return str(explicit)
    symbol = row.get("symbol") or row.get("broker_symbol") or row.get("source_symbol")
    side = row.get("side") or row.get("direction")
    decision_time = row.get("decision_time_utc")
    candidate_id = row.get("candidate_id") or row.get("gtos_vnext_candidate_id")
    if all(
        not _capture_noneish(value)
        for value in (symbol, side, decision_time, candidate_id)
    ):
        return f"{symbol}:{side}:{candidate_id}:{decision_time}"
    return None


def _denominator_forward_capture_event(row: dict[str, Any]) -> dict[str, Any]:
    event = dict(row)
    candidate_id = _first_capture_value(
        row.get("row_bound_candidate_id"),
        row.get("selected_candidate_id"),
        row.get("candidate_id"),
        row.get("gtos_vnext_candidate_id"),
    )
    order_ticket = _first_capture_value(
        row.get("pending_ticket_or_order_ticket"),
        row.get("pending_ticket"),
        row.get("order_ticket"),
        row.get("mt5_order_ticket"),
        row.get("mt5_entry_order_ticket"),
        row.get("trade_state_ticket"),
    )
    lifecycle_state = _first_capture_value(
        row.get("lifecycle_state"),
        row.get("pending_lifecycle_v4_state"),
        row.get("intent_after_check"),
    )
    cancel_or_tif = _first_capture_value(
        row.get("cancel_replace_or_time_in_force"),
        row.get("time_in_force"),
        row.get("cancel_reason"),
        row.get("expiry_time_utc"),
        row.get("cancel_expiry_reason_status"),
    )
    _set_capture_default(event, "row_bound_candidate_id", candidate_id)
    _set_capture_default(
        event, "original_candidate_id", row.get("original_candidate_id") or candidate_id
    )
    _set_capture_default(
        event, "stable_decision_window_id", _derive_stable_decision_window_id(row)
    )
    _set_capture_default(
        event,
        "order_type",
        row.get("order_type")
        or row.get("native_pending_order_type")
        or row.get("broker_order_entry_mode"),
    )
    _set_capture_default(event, "pending_ticket_or_order_ticket", order_ticket)
    _set_capture_default(event, "lifecycle_state", lifecycle_state)
    _set_capture_default(
        event, "fill_or_no_fill", row.get("fill_no_fill_label") or row.get("broker_fill_state")
    )
    _set_capture_default(event, "cancel_replace_or_time_in_force", cancel_or_tif)
    _set_capture_default(
        event,
        "broker_profile_namespace",
        row.get("broker_profile_namespace")
        or row.get("risk_reservation_broker_namespace")
        or row.get("broker_account_namespace"),
    )
    _set_capture_default(
        event,
        "source_event_hash",
        row.get("source_event_hash") or row.get("source_hash"),
    )
    for field_name in ULTIMATE_CANDIDATE_PACKAGE_SHADOW_CONTEXT_FIELDS:
        _set_capture_default(event, field_name, row.get(field_name))
    return event


def _denominator_forward_capture_runtime_config(entry: dict[str, Any]) -> dict[str, Any]:
    configured = entry.get(DENOMINATOR_FORWARD_CAPTURE_RUNTIME_CONFIG_FIELD)
    if isinstance(configured, dict):
        return dict(configured)
    return {
        key: entry[key]
        for key in _DENOMINATOR_FORWARD_CAPTURE_FLAT_CONFIG_KEYS
        if key in entry
    }


def _denominator_forward_capture_families(entry: dict[str, Any]) -> tuple[str, ...]:
    configured = entry.get(DENOMINATOR_FORWARD_CAPTURE_REQUIREMENT_FAMILIES_FIELD)
    if isinstance(configured, str):
        families = (configured,)
    elif isinstance(configured, (list, tuple, set)):
        families = tuple(str(value) for value in configured)
    else:
        families = DENOMINATOR_FORWARD_CAPTURE_DEFAULT_REQUIREMENT_FAMILIES
    return tuple(family for family in families if family.strip())


def _record_denominator_forward_capture(row: dict[str, Any], entry: dict[str, Any]) -> None:
    try:
        from src.components.denominator_forward_capture_contract import (
            record_denominator_forward_capture_event,
        )

        event = _denominator_forward_capture_event(row)
        runtime_config = _denominator_forward_capture_runtime_config(entry)
        log_path = entry.get(DENOMINATOR_FORWARD_CAPTURE_LOG_PATH_FIELD)
        for family in _denominator_forward_capture_families(entry):
            record_denominator_forward_capture_event(
                event,
                requirement_family=family,
                runtime_config=runtime_config,
                log_path=log_path,
            )
    except Exception as exc:  # noqa: BLE001 - forward capture must stay fail-open.
        logger.warning(
            "Failed to write denominator forward-capture row (non-blocking): %s",
            exc,
        )


def build_pending_limit_lifecycle_entry(**fields: Any) -> dict[str, Any]:
    """Return a schema-stable pending-limit lifecycle row.

    Unknown fields are preserved at the end so future research joins can add
    context without changing existing field semantics.
    """
    now = utc_now_iso()
    state = str(fields.get("intent_after_check") or "")
    if state not in VALID_STATES:
        state = "unknown_pending_lifecycle_state"
    trigger_condition_met = fields.get("trigger_condition_met")
    tick_spread = fields.get("spread")
    decision_spread = fields.get("decision_spread_value_source_safe")
    entry_touch_spread = fields.get("entry_touch_spread_value_source_safe")
    if entry_touch_spread is None and trigger_condition_met is True:
        entry_touch_spread = tick_spread
    cancel_reason = fields.get("cancel_reason")
    terminal_status = fields.get("terminal_area_touch_status")
    if terminal_status is None:
        if state == "cancelled_target_reached_without_fill":
            terminal_status = "TERMINAL_AREA_TOUCHED_WITHOUT_ENTRY_SOURCE_SAFE"
        elif trigger_condition_met is False:
            terminal_status = "TERMINAL_AREA_NOT_TOUCHED_AS_OF_CHECK_SOURCE_SAFE"
        else:
            terminal_status = "TERMINAL_AREA_STATUS_NOT_CAPTURED"
    protective_status = fields.get("protective_area_touch_status")
    if protective_status is None:
        if fields.get("wrong_side_abort") or fields.get("sl_too_close_abort"):
            protective_status = "PROTECTIVE_AREA_TOUCHED_OR_TOO_CLOSE_SOURCE_SAFE"
        elif trigger_condition_met is False:
            protective_status = "PROTECTIVE_AREA_NOT_TOUCHED_AS_OF_CHECK_SOURCE_SAFE"
        else:
            protective_status = "PROTECTIVE_AREA_STATUS_NOT_CAPTURED"
    event_order = fields.get("event_order_resolution_method")
    if event_order is None:
        if state == "cancelled_target_reached_without_fill":
            event_order = "TARGET_AREA_BEFORE_ENTRY_TOUCH_M15_CANDLE_PROXY"
        elif trigger_condition_met is True and fields.get("tick_available") is False:
            event_order = "ENTRY_TOUCH_M15_CANDLE_TICK_MISSING_RETRY"
        elif trigger_condition_met is True:
            event_order = "ENTRY_TOUCH_CONFIRMED_BY_M15_AND_TICK_SNAPSHOT"
        elif trigger_condition_met is False:
            event_order = "NO_ENTRY_TOUCH_AS_OF_CHECK"
        else:
            event_order = "LIFECYCLE_EVENT_STATE_ONLY"
    package_shadow = _ultimate_candidate_package_shadow_summary(fields)

    entry: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": fields.get("created_at_utc") or now,
        "timestamp_utc": fields.get("timestamp_utc") or now,
        "symbol": fields.get("symbol"),
        "broker_symbol": fields.get("broker_symbol"),
        "source_symbol": fields.get("source_symbol"),
        "session": fields.get("session"),
        "kill_zone": fields.get("kill_zone"),
        "side": fields.get("side") or fields.get("direction"),
        "regime": fields.get("regime"),
        "candidate_id": fields.get("candidate_id"),
        "trade_id": fields.get("trade_id"),
        "evidence_class": fields.get("evidence_class") or EVIDENCE_CLASS,
        "decision_time_utc": fields.get("decision_time_utc"),
        "asof_cutoff_utc": fields.get("asof_cutoff_utc"),
        "source_file": fields.get("source_file"),
        "source_hash": fields.get("source_hash"),
        "no_leak_status": fields.get("no_leak_status") or "AS_OF_LIVE_CANDLE_OR_TICK",
        "result_use_status": fields.get("result_use_status") or RESULT_USE_STATUS,
        "pending_created_time_utc": fields.get("pending_created_time_utc"),
        "pending_ticket": fields.get("pending_ticket"),
        "pending_lifecycle_v4_id": fields.get("pending_lifecycle_v4_id"),
        "pending_order_mode": fields.get("pending_order_mode")
        or INTERNAL_PENDING_ORDER_MODE,
        "broker_pending_order_created": bool(
            fields.get("broker_pending_order_created", False)
        ),
        "mt5_order_ticket": fields.get("mt5_order_ticket"),
        "native_pending_order_type": fields.get("native_pending_order_type"),
        "risk_reserved_pct": fields.get("risk_reserved_pct"),
        "risk_reserved_cash": fields.get("risk_reserved_cash"),
        "risk_reservation_status": fields.get("risk_reservation_status"),
        "risk_reservation_scope": fields.get("risk_reservation_scope"),
        "risk_reservation_source": fields.get("risk_reservation_source"),
        "risk_reservation_broker_namespace": fields.get(
            "risk_reservation_broker_namespace"
        ),
        "fill_time_utc": fields.get("fill_time_utc"),
        "expiry_time_utc": fields.get("expiry_time_utc"),
        "cancel_reason": cancel_reason,
        "pending_horizon_start_utc": fields.get("pending_horizon_start_utc")
        or fields.get("pending_created_time_utc"),
        "pending_horizon_end_utc": fields.get("pending_horizon_end_utc")
        or fields.get("expiry_time_utc"),
        "cancel_expiry_reason_status": fields.get("cancel_expiry_reason_status")
        or (
            "CANCEL_OR_EXPIRY_REASON_CAPTURED_SOURCE_SAFE"
            if cancel_reason
            else "NOT_APPLICABLE"
        ),
        "broker_fill_state": fields.get("broker_fill_state"),
        "entry_price": fields.get("entry_price"),
        "stop_loss": fields.get("stop_loss"),
        "take_profit_1": fields.get("take_profit_1"),
        "spread": tick_spread,
        "decision_spread_value_source_safe": decision_spread,
        "decision_spread_unit": fields.get("decision_spread_unit"),
        "entry_touch_spread_value_source_safe": entry_touch_spread,
        "entry_touch_spread_unit": fields.get("entry_touch_spread_unit")
        or ("spread_cents" if entry_touch_spread is not None else None),
        "slippage_price": fields.get("slippage_price"),
        "actual_r": fields.get("actual_r"),
        "synthetic_path_r": fields.get("synthetic_path_r"),
        "fill_no_fill_label": fields.get("fill_no_fill_label") or _FILL_LABEL_BY_STATE[state],
        "checked_candle_time_utc": fields.get("checked_candle_time_utc"),
        "checked_candle_open": fields.get("checked_candle_open"),
        "checked_candle_high": fields.get("checked_candle_high"),
        "checked_candle_low": fields.get("checked_candle_low"),
        "checked_candle_close": fields.get("checked_candle_close"),
        "tick_bid": fields.get("tick_bid"),
        "tick_ask": fields.get("tick_ask"),
        "source_branch": fields.get("source_branch"),
        "check_context": fields.get("check_context"),
        "candles_elapsed_before": fields.get("candles_elapsed_before"),
        "candles_elapsed_after": fields.get("candles_elapsed_after"),
        "trigger_condition_met": trigger_condition_met,
        "terminal_area_touch_status": terminal_status,
        "terminal_area_first_touch_utc": fields.get("terminal_area_first_touch_utc"),
        "protective_area_touch_status": protective_status,
        "protective_area_first_touch_utc": fields.get("protective_area_first_touch_utc"),
        "event_order_resolution_method": event_order,
        "same_tick_same_bar_ambiguity_status": fields.get("same_tick_same_bar_ambiguity_status")
        or "NOT_EVALUATED_BY_LIFECYCLE_LOGGER",
        "tick_available": fields.get("tick_available"),
        "current_price_used": fields.get("current_price_used"),
        "wrong_side_abort": fields.get("wrong_side_abort"),
        "sl_too_close_abort": fields.get("sl_too_close_abort"),
        "order_send_attempted": fields.get("order_send_attempted"),
        "order_send_success": fields.get("order_send_success"),
        "trade_state_ticket": fields.get("trade_state_ticket"),
        "mt5_position_ticket": fields.get("mt5_position_ticket"),
        "mt5_entry_order_ticket": fields.get("mt5_entry_order_ticket"),
        "mt5_entry_deal_ticket": fields.get("mt5_entry_deal_ticket"),
        "order_result_retcode": fields.get("order_result_retcode"),
        "filled_order_position_join_keys": fields.get("filled_order_position_join_keys")
        or [],
        "exact_r_join_key_status": fields.get("exact_r_join_key_status")
        or "NO_FILLED_ORDER_POSITION_KEYS_FOR_CURRENT_STATE",
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
        "ultimate_candidate_package_shadow_summary": package_shadow["summary"],
        "intent_after_check": state,
        "record_path": fields.get("record_path"),
        "raw_data_m15_count": fields.get("raw_data_m15_count"),
        "latest_m15_time_utc": fields.get("latest_m15_time_utc"),
        "last_limit_check_candle_time_before": fields.get("last_limit_check_candle_time_before"),
        "reason": fields.get("reason"),
    }

    for key, value in fields.items():
        if key not in entry:
            entry[key] = value

    entry.update(build_lifecycle_v4_fields(entry))

    return {key: _json_safe(value) for key, value in entry.items()}


def _append_jsonl_locked(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(row, sort_keys=True) + "\n"
    lock_path = path.with_suffix(path.suffix + ".lock")

    with open(lock_path, "a+b") as lock_f:
        locked = False
        for _ in range(_JSONL_LOCK_RETRIES):
            try:
                lock_f.seek(0)
                if msvcrt is not None:
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_NBLCK, 1)
                elif fcntl is not None:
                    fcntl.flock(lock_f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
                break
            except OSError:
                time.sleep(_JSONL_LOCK_SLEEP_SECONDS)
        if not locked:
            raise TimeoutError(f"JSONL lock busy: {lock_path}")

        try:
            with open(path, "a", encoding="utf-8", newline="") as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
        finally:
            try:
                lock_f.seek(0)
                if msvcrt is not None:
                    msvcrt.locking(lock_f.fileno(), msvcrt.LK_UNLCK, 1)
                elif fcntl is not None:
                    fcntl.flock(lock_f.fileno(), fcntl.LOCK_UN)
            except OSError as exc:
                logger.warning("Pending-limit lifecycle JSONL unlock failed: %s", exc)


def record_pending_limit_lifecycle(
    entry: dict[str, Any],
    log_path: str | None = None,
) -> None:
    """Append one pending-limit lifecycle row. Never raises."""
    try:
        row = build_pending_limit_lifecycle_entry(**entry)
        path = Path(log_path or PENDING_LIMIT_LIFECYCLE_LOG_PATH)
        _append_jsonl_locked(path, row)
        try:
            from src.research_infra.forward_capture import (
                SCID_FORWARD_SOURCE_CAPTURE_PATH,
                record_scid_forward_capture_lifecycle_event,
            )

            scid_path = path.parent / Path(SCID_FORWARD_SOURCE_CAPTURE_PATH).name
            record_scid_forward_capture_lifecycle_event(row, log_path=scid_path)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Failed to write SCID pending-limit lifecycle row (non-blocking): %s",
                exc,
            )
        _record_denominator_forward_capture(row, entry)
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Failed to write pending-limit lifecycle shadow row (non-blocking): %s",
            exc,
        )
