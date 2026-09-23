"""Pending/no-fill lifecycle V4 state projection.

The production engine still uses software-polled pending intents. This module
adds a source-bound state projection around those events so pending orders,
no-fills, cancel/expiry, risk reservation, path-touch ordering, and broker
ticket truth are machine-checkable evidence instead of loose logger strings.
"""

from __future__ import annotations

import math
from typing import Any


SCHEMA_VERSION = "pending_nofill_lifecycle_v4"

TERMINAL_INTENT_STATES = {
    "expired_48h",
    "cancelled_wrong_side",
    "cancelled_sl_too_close",
    "cancelled_target_reached_without_fill",
    "order_send_success_filled",
    "manual_or_system_cancelled",
}

RETRY_INTENT_STATES = {
    "source_repair_failed_retry",
    "triggered_tick_missing_retry",
    "order_send_failed_retry",
}

INTENT_STATE_TO_V4_STATE = {
    "still_pending_no_trigger": "PENDING_ACTIVE_NO_ENTRY_TOUCH",
    "source_repair_failed_retry": "PENDING_ACTIVE_SOURCE_REPAIR_RETRY",
    "expired_48h": "NO_FILL_EXPIRED",
    "triggered_tick_missing_retry": "PENDING_TRIGGERED_TICK_MISSING_RETRY",
    "cancelled_wrong_side": "NO_FILL_CANCELLED_WRONG_SIDE",
    "cancelled_sl_too_close": "NO_FILL_CANCELLED_SL_TOO_CLOSE",
    "cancelled_target_reached_without_fill": (
        "NO_FILL_CANCELLED_TARGET_REACHED_WITHOUT_ENTRY_TOUCH"
    ),
    "order_send_success_filled": "FILLED_MARKET_ORDER_ON_ENTRY_TOUCH",
    "order_send_failed_retry": "PENDING_TRIGGERED_ORDER_SEND_FAILED_RETRY",
    "manual_or_system_cancelled": "NO_FILL_CANCELLED_SYSTEM_OR_MANUAL",
    "unknown_pending_lifecycle_state": "UNKNOWN_PENDING_LIFECYCLE_STATE",
}

FILL_EVENT_FAMILIES = {
    "order_send_success_filled": "filled",
    "order_send_failed_retry": "fill_attempt_retry",
    "triggered_tick_missing_retry": "entry_touch_retry",
}

NO_FILL_EVENT_FAMILIES = {
    "still_pending_no_trigger": "still_pending",
    "source_repair_failed_retry": "source_repair_retry",
    "expired_48h": "expired",
    "cancelled_wrong_side": "cancelled_wrong_side",
    "cancelled_sl_too_close": "cancelled_sl_too_close",
    "cancelled_target_reached_without_fill": "cancelled_target_first",
    "manual_or_system_cancelled": "manual_or_system_cancelled",
    "unknown_pending_lifecycle_state": "unknown",
}


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def normalize_intent_state(value: Any) -> str:
    state = str(value or "").strip()
    return state if state in INTENT_STATE_TO_V4_STATE else "unknown_pending_lifecycle_state"


def pending_lifecycle_v4_id(
    *,
    broker_namespace: str | None,
    symbol: str | None,
    trade_id: str | None,
) -> str:
    namespace = str(broker_namespace or "broker_namespace_unknown").strip()
    symbol_key = str(symbol or "symbol_unknown").strip()
    trade_key = str(trade_id or "trade_id_unknown").strip()
    return f"pending_lifecycle_v4:{namespace}:{symbol_key}:{trade_key}"


def build_risk_reservation(
    *,
    account_balance: Any,
    risk_pct: Any,
    broker_namespace: str | None,
    symbol: str | None,
    trade_id: str | None,
) -> dict[str, Any]:
    risk = _safe_float(risk_pct)
    balance = _safe_float(account_balance)
    lifecycle_id = pending_lifecycle_v4_id(
        broker_namespace=broker_namespace,
        symbol=symbol,
        trade_id=trade_id,
    )
    base = {
        "pending_lifecycle_v4_id": lifecycle_id,
        "risk_reserved_pct": risk,
        "risk_reserved_cash": None,
        "risk_reservation_status": "RISK_RESERVATION_SOURCE_INCOMPLETE",
        "risk_reservation_scope": "broker_local_pending_intent",
        "risk_reservation_source": "account_balance_x_risk_pct_at_pending_creation",
        "risk_reservation_broker_namespace": broker_namespace,
    }
    if risk is None or risk <= 0:
        base["risk_reservation_status"] = "RISK_RESERVATION_RISK_PCT_MISSING_OR_NONPOSITIVE"
        return base
    if balance is None or balance <= 0:
        base["risk_reservation_status"] = "RISK_RESERVATION_BALANCE_MISSING_OR_NONPOSITIVE"
        return base
    base["risk_reserved_cash"] = round(balance * risk / 100.0, 8)
    base["risk_reservation_status"] = "RISK_RESERVED_BROKER_LOCAL_PENDING_INTENT"
    return base


def broker_ticket_truth_status(row: dict[str, Any]) -> str:
    if _safe_bool(row.get("broker_pending_order_created")):
        if row.get("mt5_order_ticket") or row.get("pending_ticket"):
            return "NATIVE_PENDING_ORDER_TICKET_CAPTURED"
        return "NATIVE_PENDING_ORDER_TICKET_MISSING"
    if _safe_bool(row.get("order_send_success")):
        if (
            row.get("trade_state_ticket")
            or row.get("mt5_position_ticket")
            or row.get("mt5_entry_order_ticket")
            or row.get("mt5_entry_deal_ticket")
        ):
            return "FILLED_MARKET_ORDER_TICKET_CAPTURED"
        return "FILLED_MARKET_ORDER_TICKET_MISSING"
    return "NO_BROKER_PENDING_ORDER_INTERNAL_SOFTWARE_INTENT"


def path_touch_ordering_status(row: dict[str, Any], state: str) -> str:
    if state == "cancelled_target_reached_without_fill":
        return "TARGET_AREA_BEFORE_ENTRY_TOUCH_CAPTURED"
    if _safe_bool(row.get("wrong_side_abort")):
        return "PROTECTIVE_AREA_OR_WRONG_SIDE_BEFORE_FILL_CAPTURED"
    if _safe_bool(row.get("sl_too_close_abort")):
        return "PROTECTIVE_AREA_OR_SL_TOO_CLOSE_BEFORE_FILL_CAPTURED"
    if _safe_bool(row.get("trigger_condition_met")):
        if row.get("tick_bid") is not None or row.get("tick_ask") is not None:
            return "ENTRY_TOUCH_WITH_TICK_SNAPSHOT_CAPTURED"
        return "ENTRY_TOUCH_WITHOUT_TICK_SNAPSHOT_RETRY"
    if state == "still_pending_no_trigger":
        return "NO_ENTRY_TOUCH_AS_OF_CHECK"
    if state == "source_repair_failed_retry":
        return "OHLC_SOURCE_REPAIR_FAILED_NO_TOUCH_CLAIM"
    if state in TERMINAL_INTENT_STATES:
        return "TERMINAL_STATE_CAPTURED_WITHOUT_FULL_PATH_ORDERING"
    return "PATH_TOUCH_ORDERING_NOT_CAPTURED"


def source_completeness_status(row: dict[str, Any], state: str) -> str:
    missing = []
    for key in ("symbol", "side", "trade_id", "entry_price", "stop_loss", "take_profit_1"):
        if row.get(key) in (None, ""):
            missing.append(key)
    if row.get("pending_created_time_utc") in (None, ""):
        missing.append("pending_created_time_utc")
    if row.get("checked_candle_time_utc") in (None, "") and state != "manual_or_system_cancelled":
        missing.append("checked_candle_time_utc")
    if state == "order_send_success_filled" and broker_ticket_truth_status(row).endswith("MISSING"):
        missing.append("broker_ticket_truth")
    if missing:
        return "SOURCE_GAP:" + ",".join(sorted(missing))
    if state in RETRY_INTENT_STATES:
        return "SOURCE_COMPLETE_FOR_RETRY_STATE"
    if state in TERMINAL_INTENT_STATES:
        return "SOURCE_COMPLETE_FOR_TERMINAL_STATE"
    return "SOURCE_COMPLETE_FOR_ACTIVE_PENDING_STATE"


def risk_reservation_lifecycle_status(row: dict[str, Any], state: str) -> tuple[str, str | None]:
    existing = str(row.get("risk_reservation_status") or "").strip()
    if state in TERMINAL_INTENT_STATES:
        if row.get("risk_reserved_pct") is None and row.get("risk_reserved_cash") is None:
            return "NO_RISK_RESERVATION_SOURCE_CAPTURED", "terminal_without_reservation_source"
        return "RISK_RESERVATION_RELEASED_ON_TERMINAL_STATE", state
    if state in RETRY_INTENT_STATES or state == "still_pending_no_trigger":
        if existing:
            return existing, None
        if row.get("risk_reserved_pct") is not None or row.get("risk_reserved_cash") is not None:
            return "RISK_RESERVED_BROKER_LOCAL_PENDING_INTENT", None
        return "NO_RISK_RESERVATION_SOURCE_CAPTURED", None
    return existing or "RISK_RESERVATION_STATUS_UNKNOWN", None


def build_lifecycle_v4_fields(row: dict[str, Any]) -> dict[str, Any]:
    state = normalize_intent_state(row.get("intent_after_check"))
    v4_state = INTENT_STATE_TO_V4_STATE[state]
    terminal = state in TERMINAL_INTENT_STATES
    event_family = FILL_EVENT_FAMILIES.get(state) or NO_FILL_EVENT_FAMILIES.get(state) or "unknown"
    risk_status, release_reason = risk_reservation_lifecycle_status(row, state)
    state_group = (
        "filled_terminal"
        if state == "order_send_success_filled"
        else "nofill_terminal"
        if terminal
        else "retry_active"
        if state in RETRY_INTENT_STATES
        else "active_pending"
        if state == "still_pending_no_trigger"
        else "unknown"
    )
    return {
        "pending_lifecycle_v4_schema_version": SCHEMA_VERSION,
        "pending_lifecycle_v4_state": v4_state,
        "pending_lifecycle_v4_state_group": state_group,
        "pending_lifecycle_v4_event_family": event_family,
        "pending_lifecycle_v4_terminal": terminal,
        "pending_lifecycle_v4_transition_status": (
            "KNOWN_ALLOWED_TRANSITION"
            if state != "unknown_pending_lifecycle_state"
            else "UNKNOWN_TRANSITION_FAIL_CLOSED"
        ),
        "risk_reservation_status": risk_status,
        "risk_reservation_release_reason": release_reason,
        "broker_ticket_truth_status": broker_ticket_truth_status(row),
        "path_touch_ordering_status": path_touch_ordering_status(row, state),
        "v4_source_completeness_status": source_completeness_status(row, state),
        "ftmo_no_copy_boundary": (
            "BROKER_LOCAL_LIFECYCLE_TRUTH_DO_NOT_COPY_redacted_account_TO_FTMO"
        ),
    }


def project_wave2_fixture_row(source_row: dict[str, Any]) -> dict[str, Any]:
    lifecycle = source_row.get("lifecycle_fields") or {}
    base = {
        "row_id": source_row.get("row_id"),
        "material_row_id": source_row.get("material_row_id"),
        "source_sequence_index": source_row.get("source_sequence_index"),
        "symbol": source_row.get("symbol"),
        "broker_symbol": source_row.get("broker_symbol"),
        "source_symbol": source_row.get("source_symbol"),
        "side": source_row.get("side"),
        "trade_id": source_row.get("trade_id"),
        "candidate_id": source_row.get("candidate_id"),
        "decision_time_utc": source_row.get("decision_time_utc"),
        "pending_created_time_utc": source_row.get("pending_created_time_utc"),
        "checked_candle_time_utc": source_row.get("checked_candle_time_utc"),
        "entry_price": source_row.get("entry_price"),
        "stop_loss": source_row.get("stop_loss"),
        "take_profit_1": source_row.get("take_profit_1"),
        "intent_after_check": lifecycle.get("intent_after_check"),
        "broker_fill_state": lifecycle.get("broker_fill_state"),
        "fill_no_fill_label": lifecycle.get("fill_no_fill_label"),
        "trigger_condition_met": lifecycle.get("trigger_condition_met"),
        "order_send_attempted": lifecycle.get("order_send_attempted"),
        "order_send_success": lifecycle.get("order_send_success"),
        "wrong_side_abort": lifecycle.get("wrong_side_abort"),
        "sl_too_close_abort": lifecycle.get("sl_too_close_abort"),
        "broker_pending_order_created": False,
        "reconciliation_status": source_row.get("reconciliation_status"),
        "historical_source_gap_family": source_row.get("historical_source_gap_family"),
        "geometry_capture_status": source_row.get("geometry_capture_status"),
        "source_capture_state": source_row.get("source_capture_state"),
        "missing_or_non_generatable_truth": source_row.get("missing_or_non_generatable_truth") or [],
        "result_use_status": source_row.get("result_use_status"),
    }
    base.update(build_lifecycle_v4_fields(base))
    base["wave2_source_row"] = source_row
    return base
