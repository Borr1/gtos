"""Pending-limit lifecycle contract audit helpers.

This module is research/tooling only. It reads append-only shadow rows,
candidate/path evidence, trade-record source files, and optional persisted
pending-intent files to verify that LIMIT_PLACED records have explicit
fill/no-fill lifecycle truth. It does not call AI, canaries, MT5, broker
orders, or paid data sources.
"""

from __future__ import annotations

import pickle
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from src.research_infra.evidence_selection import latest_by_candidate as latest_evidence_by_candidate
from src.research_infra.trade_record_candidate_backfill import TradeRecordCandidate


PROMOTION_VERDICT = "NO_PROMOTION_VERDICT"
SCHEMA_VERSION = "pending_limit_lifecycle_audit_v1"
COMPLETE = "PENDING_LIMIT_LIFECYCLE_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "PENDING_LIMIT_LIFECYCLE_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "PENDING_LIMIT_LIFECYCLE_ACTION_REQUIRED"
STALE_INTERNAL_PENDING_GRACE = timedelta(hours=12)

LIMIT_PLACED_OUTCOMES = {"LIMIT_PLACED", "ORDER_PLACED", "PENDING_LIMIT"}
TERMINAL_NO_FILL_STATES = {
    "cancelled_wrong_side",
    "cancelled_sl_too_close",
    "cancelled_target_reached_without_fill",
    "expired_48h",
    "manual_or_system_cancelled",
}
RETRY_OR_UNRESOLVED_STATES = {
    "triggered_tick_missing_retry",
    "order_send_failed_retry",
}


class _PlainPendingIntent:
    """Unpickle persisted PendingLimitIntent rows without importing execution."""


class _PendingIntentUnpickler(pickle.Unpickler):
    def find_class(self, module: str, name: str) -> Any:  # noqa: D401
        if module == "src.components.execution" and name == "PendingLimitIntent":
            return _PlainPendingIntent
        raise pickle.UnpicklingError(f"unsupported persisted class {module}.{name}")


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def prices_match(left: Any, right: Any, *, tolerance: float = 1e-6) -> bool:
    a = safe_float(left)
    b = safe_float(right)
    return a is not None and b is not None and abs(a - b) <= tolerance


def _roundable(value: Any) -> str:
    number = safe_float(value)
    if number is None:
        return str(value or "")
    return f"{number:.8f}".rstrip("0").rstrip(".")


def _latest_timestamp(row: dict[str, Any]) -> datetime:
    return (
        parse_utc(row.get("fill_time_utc"))
        or parse_utc(row.get("created_at_utc"))
        or parse_utc(row.get("timestamp_utc"))
        or parse_utc(row.get("checked_candle_time_utc"))
        or parse_utc(row.get("asof_cutoff_utc"))
        or datetime.min.replace(tzinfo=timezone.utc)
    )


def _earliest_lifecycle_timestamp(rows: list[dict[str, Any]]) -> datetime | None:
    timestamps = [_latest_timestamp(row) for row in rows]
    timestamps = [ts for ts in timestamps if ts != datetime.min.replace(tzinfo=timezone.utc)]
    return min(timestamps) if timestamps else None


def _has_payload(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _candidate_params(candidate: dict[str, Any]) -> dict[str, Any]:
    params = candidate.get("trade_parameters")
    return params if isinstance(params, dict) else {}


def _candidate_side(candidate: dict[str, Any]) -> str:
    return str(candidate.get("side") or _candidate_params(candidate).get("direction") or "").upper()


def _trade_record_limit_intent(record_candidate: TradeRecordCandidate) -> dict[str, Any]:
    intent = record_candidate.record.get("limit_intent")
    return intent if isinstance(intent, dict) else {}


def _trade_record_entry(record_candidate: TradeRecordCandidate) -> Any:
    return _trade_record_limit_intent(record_candidate).get(
        "limit_price",
        record_candidate.trade_parameters.get("entry_price"),
    )


def _trade_record_side(record_candidate: TradeRecordCandidate) -> str:
    return str(record_candidate.side or record_candidate.trade_parameters.get("direction") or "").upper()


def _candidate_matches_lifecycle(candidate: dict[str, Any], lifecycle: dict[str, Any]) -> bool:
    if lifecycle.get("candidate_id"):
        return str(lifecycle.get("candidate_id")) == str(candidate.get("candidate_id") or "")
    params = _candidate_params(candidate)
    return (
        str(candidate.get("symbol") or "") == str(lifecycle.get("symbol") or "")
        and _candidate_side(candidate) == str(lifecycle.get("side") or "").upper()
        and prices_match(params.get("entry_price"), lifecycle.get("entry_price"))
        and prices_match(params.get("stop_loss"), lifecycle.get("stop_loss"))
        and prices_match(params.get("take_profit_1"), lifecycle.get("take_profit_1"))
    )


def _trade_record_matches_lifecycle(record_candidate: TradeRecordCandidate, lifecycle: dict[str, Any]) -> bool:
    intent = _trade_record_limit_intent(record_candidate)
    trade_id = str(intent.get("trade_id") or "")
    if trade_id and trade_id != str(lifecycle.get("trade_id") or ""):
        return False
    return (
        record_candidate.symbol == str(lifecycle.get("symbol") or "")
        and _trade_record_side(record_candidate) == str(lifecycle.get("side") or "").upper()
        and prices_match(_trade_record_entry(record_candidate), lifecycle.get("entry_price"))
        and prices_match(intent.get("stop_loss", record_candidate.trade_parameters.get("stop_loss")), lifecycle.get("stop_loss"))
        and prices_match(
            intent.get("take_profit_1", record_candidate.trade_parameters.get("take_profit_1")),
            lifecycle.get("take_profit_1"),
        )
    )


def _persisted_intent_matches_lifecycle(intent: dict[str, Any], lifecycle: dict[str, Any]) -> bool:
    return (
        str(intent.get("symbol") or "") == str(lifecycle.get("symbol") or "")
        and str(intent.get("trade_id") or "") == str(lifecycle.get("trade_id") or "")
        and str(intent.get("side") or intent.get("direction") or "").upper()
        == str(lifecycle.get("side") or "").upper()
        and prices_match(intent.get("entry_price") or intent.get("limit_price"), lifecycle.get("entry_price"))
        and prices_match(intent.get("stop_loss"), lifecycle.get("stop_loss"))
        and prices_match(intent.get("take_profit_1"), lifecycle.get("take_profit_1"))
    )


def lifecycle_group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str]:
    return (
        str(row.get("symbol") or ""),
        str(row.get("trade_id") or ""),
        str(row.get("side") or "").upper(),
        _roundable(row.get("entry_price")),
        _roundable(row.get("stop_loss")),
        _roundable(row.get("take_profit_1")),
    )


def pending_intent_global_key(row: dict[str, Any]) -> str:
    placed = str(row.get("pending_created_time_utc") or row.get("placed_time") or "")
    symbol, trade_id, side, entry, stop, tp1 = lifecycle_group_key(row)
    return "|".join((symbol, trade_id, placed, side, entry, stop, tp1))


def latest_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return latest_evidence_by_candidate(rows)


def read_persisted_pending_intents(meta_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not meta_root.exists():
        return rows
    for path in sorted(meta_root.glob("pending_intent_*.pkl")):
        try:
            with path.open("rb") as handle:
                obj = _PendingIntentUnpickler(handle).load()
        except Exception:  # noqa: BLE001
            rows.append(
                {
                    "source_path": str(path),
                    "symbol": path.stem.removeprefix("pending_intent_"),
                    "read_status": "UNREADABLE_PERSISTED_PENDING_INTENT",
                }
            )
            continue
        payload = dict(getattr(obj, "__dict__", {}) or {})
        payload.update(
            {
                "source_path": str(path),
                "symbol": path.stem.removeprefix("pending_intent_"),
                "side": payload.get("direction"),
                "entry_price": payload.get("limit_price"),
                "pending_created_time_utc": payload.get("placed_time"),
                "read_status": "READ_OK",
            }
        )
        rows.append(payload)
    return rows


def _classify_final_state(latest: dict[str, Any]) -> tuple[str, str]:
    state = str(latest.get("intent_after_check") or "")
    if state == "still_pending_no_trigger":
        return "NO_FILL_STILL_PENDING", "STILL_ACTIVE_PENDING"
    if state == "cancelled_wrong_side":
        return "NO_FILL_CANCELLED_WRONG_SIDE", "FINAL_TERMINAL_NO_FILL"
    if state == "cancelled_sl_too_close":
        return "NO_FILL_CANCELLED_SL_TOO_CLOSE", "FINAL_TERMINAL_NO_FILL"
    if state == "cancelled_target_reached_without_fill":
        return "NO_FILL_CANCELLED_TARGET_REACHED_WITHOUT_ENTRY_TOUCH", "FINAL_TERMINAL_NO_FILL"
    if state == "expired_48h":
        return "NO_FILL_EXPIRED", "FINAL_TERMINAL_NO_FILL"
    if state == "manual_or_system_cancelled":
        return "NO_FILL_CANCELLED_SYSTEM_OR_MANUAL", "FINAL_TERMINAL_NO_FILL"
    if state == "order_send_success_filled":
        return "BROKER_FILLED_AWAITING_EXIT_OR_ACCOUNT_TRUTH", "BROKER_FILL_PENDING_EXIT_TRUTH"
    if state in RETRY_OR_UNRESOLVED_STATES:
        return state.upper(), "TRIGGERED_BUT_UNRESOLVED_RETRY"
    return "UNKNOWN_PENDING_LIFECYCLE_FINAL_STATE", "ACTION_REQUIRED_UNKNOWN_FINAL_STATE"


def _is_true(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "1"}
    return bool(value)


def _has_broker_order_reference(latest: dict[str, Any]) -> bool:
    return any(
        latest.get(field)
        for field in (
            "mt5_order_ticket",
            "pending_ticket",
            "trade_state_ticket",
            "broker_order_ticket",
            "order_ticket",
        )
    )


def _is_stale_internal_pending_without_broker_order(
    *,
    latest: dict[str, Any],
    generated_at_utc: str,
    final_state_status: str,
) -> bool:
    if final_state_status != "STILL_ACTIVE_PENDING":
        return False
    if str(latest.get("pending_order_mode") or "") != "INTERNAL_CANDLE_POLLED_INTENT":
        return False
    if _is_true(latest.get("broker_pending_order_created")):
        return False
    if _is_true(latest.get("order_send_attempted")) or _is_true(latest.get("order_send_success")):
        return False
    if _has_broker_order_reference(latest):
        return False
    pending_created = parse_utc(latest.get("pending_created_time_utc") or latest.get("placed_time"))
    generated_at = parse_utc(generated_at_utc)
    if not pending_created or not generated_at:
        return False
    return generated_at - pending_created >= STALE_INTERNAL_PENDING_GRACE


def _missed_move_classification(path_row: dict[str, Any] | None, ltf_row: dict[str, Any] | None) -> str:
    path_label = str((path_row or {}).get("path_label") or "")
    ltf_status = str((ltf_row or {}).get("terminal_outcome_status") or "")
    if "without_entry_touch_to_tp_area" in path_label or ltf_status == "NO_ENTRY_TP1_AREA_REACHED_WITHOUT_ENTRY_TOUCH":
        return "NO_FILL_TP_AREA_REACHED_WITHOUT_LIMIT_TOUCH"
    if ltf_status.startswith("ENTRY_THEN"):
        return ltf_status
    if path_label:
        return f"PATH_LABEL:{path_label}"
    return "NO_PATH_MOVE_CLASSIFICATION_AVAILABLE"


def _matching_join_rows(group_rows: list[dict[str, Any]], join_rows: list[tuple[int, dict[str, Any]]]) -> list[dict[str, Any]]:
    sample = group_rows[-1]
    out: list[dict[str, Any]] = []
    for _, row in join_rows:
        if str(row.get("source_lifecycle_trade_id") or row.get("trade_id") or "") != str(sample.get("trade_id") or ""):
            continue
        disambig = row.get("symbol_price_disambiguation") if isinstance(row.get("symbol_price_disambiguation"), dict) else {}
        if disambig:
            if str(disambig.get("symbol") or "") != str(sample.get("symbol") or ""):
                continue
            if not prices_match(disambig.get("entry_price"), sample.get("entry_price")):
                continue
        elif str(row.get("symbol") or "") != str(sample.get("symbol") or ""):
            continue
        out.append(row)
    return out


def _required_field_statuses(
    *,
    latest: dict[str, Any],
    matched_candidate: dict[str, Any] | None,
    matched_trade_record: TradeRecordCandidate | None,
    persisted_intent: dict[str, Any] | None,
    final_state_status: str,
    generated_at_utc: str,
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    statuses["candidate_id"] = (
        "RAW_CAPTURED"
        if latest.get("candidate_id")
        else "RECOVERED_FROM_SHADOW_CANDIDATE_JOIN"
        if matched_candidate
        else "RECOVERED_FROM_TRADE_RECORD_LIMIT_INTENT"
        if matched_trade_record
        else "SOURCE_NOT_CAPTURED"
    )
    statuses["decision_time_utc"] = (
        "RAW_CAPTURED"
        if latest.get("decision_time_utc")
        else "RECOVERED_FROM_SHADOW_CANDIDATE_JOIN"
        if matched_candidate
        else "RECOVERED_FROM_TRADE_RECORD_LIMIT_INTENT"
        if matched_trade_record
        else "SOURCE_NOT_CAPTURED"
    )
    statuses["source_symbol"] = "RAW_CAPTURED" if latest.get("source_symbol") else "SOURCE_NOT_CAPTURED"
    geometry_complete = all(
        latest.get(field) is not None for field in ("symbol", "entry_price", "stop_loss", "take_profit_1", "side")
    )
    statuses["trade_geometry"] = "RAW_CAPTURED_COMPLETE" if geometry_complete else "ACTION_REQUIRED_MISSING_GEOMETRY"
    statuses["order_send_status"] = (
        "RAW_CAPTURED_COMPLETE"
        if latest.get("order_send_attempted") is not None and latest.get("order_send_success") is not None
        else "ACTION_REQUIRED_MISSING_ORDER_SEND_STATUS"
    )
    if str(latest.get("intent_after_check") or "") in TERMINAL_NO_FILL_STATES:
        statuses["cancel_reason"] = (
            "RAW_CAPTURED" if latest.get("cancel_reason") or latest.get("reason") else "ACTION_REQUIRED_MISSING_CANCEL_REASON"
        )
    else:
        statuses["cancel_reason"] = "NOT_APPLICABLE"
    statuses["final_state"] = "CLASSIFIED" if not final_state_status.startswith("ACTION_REQUIRED") else "ACTION_REQUIRED"
    if persisted_intent:
        statuses["persisted_pending_intent"] = "MATCHED_ACTIVE_PERSISTED_INTENT"
    elif _is_stale_internal_pending_without_broker_order(
        latest=latest,
        generated_at_utc=generated_at_utc,
        final_state_status=final_state_status,
    ):
        statuses["persisted_pending_intent"] = "DOCUMENTED_STALE_INTERNAL_INTENT_NOT_PERSISTED_NO_BROKER_ORDER"
    elif final_state_status == "STILL_ACTIVE_PENDING":
        statuses["persisted_pending_intent"] = "ACTION_REQUIRED_ACTIVE_PENDING_INTENT_NOT_PERSISTED"
    else:
        statuses["persisted_pending_intent"] = "NOT_APPLICABLE_TERMINAL_OR_ABSENT"
    return statuses


def _action_codes_from_statuses(statuses: dict[str, str]) -> list[str]:
    return sorted({f"{field.upper()}:{status}" for field, status in statuses.items() if status.startswith("ACTION_REQUIRED")})


def _source_row_from_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    params = _candidate_params(candidate)
    return {
        "symbol": candidate.get("symbol"),
        "broker_symbol": candidate.get("broker_symbol"),
        "source_symbol": candidate.get("source_symbol"),
        "side": candidate.get("side") or params.get("direction"),
        "candidate_id": candidate.get("candidate_id"),
        "decision_time_utc": candidate.get("decision_time_utc"),
        "trade_id": candidate.get("trade_id"),
        "entry_price": params.get("entry_price"),
        "stop_loss": params.get("stop_loss"),
        "take_profit_1": params.get("take_profit_1"),
        "pending_created_time_utc": None,
    }


def _source_row_from_trade_record(record_candidate: TradeRecordCandidate) -> dict[str, Any]:
    intent = _trade_record_limit_intent(record_candidate)
    record = record_candidate.record
    return {
        "symbol": record_candidate.symbol,
        "broker_symbol": record_candidate.broker_symbol,
        "source_symbol": None,
        "side": record_candidate.side or record_candidate.trade_parameters.get("direction"),
        "candidate_id": record_candidate.candidate_id,
        "decision_time_utc": record_candidate.decision_time_utc,
        "trade_id": intent.get("trade_id"),
        "entry_price": _trade_record_entry(record_candidate),
        "stop_loss": intent.get("stop_loss", record_candidate.trade_parameters.get("stop_loss")),
        "take_profit_1": intent.get("take_profit_1", record_candidate.trade_parameters.get("take_profit_1")),
        "pending_created_time_utc": None,
        "_trade_record_has_execution": _has_payload(record.get("execution")),
        "_trade_record_has_exit": _has_payload(record.get("exit")),
        "_trade_record_has_pending_lifecycle": _has_payload(record.get("pending_lifecycle")),
    }


def _limit_candidates(candidate_rows: list[tuple[int, dict[str, Any]]], decision_date_prefix: str | None) -> list[dict[str, Any]]:
    out = []
    for _, row in candidate_rows:
        if decision_date_prefix and not str(row.get("decision_time_utc") or "").startswith(decision_date_prefix):
            continue
        if str(row.get("final_outcome_at_log") or "") in LIMIT_PLACED_OUTCOMES:
            out.append(row)
    return out


def _limit_trade_records(
    trade_records: list[TradeRecordCandidate],
    *,
    decision_date_prefix: str | None,
    lifecycle_trade_ids: set[str],
) -> list[TradeRecordCandidate]:
    out: list[TradeRecordCandidate] = []
    for record in trade_records:
        intent_trade_id = str(_trade_record_limit_intent(record).get("trade_id") or "")
        in_scope = (
            (decision_date_prefix and record.decision_time_utc.startswith(decision_date_prefix))
            or bool(intent_trade_id and intent_trade_id in lifecycle_trade_ids)
            or decision_date_prefix is None
        )
        if in_scope and str(record.final_outcome or "") in LIMIT_PLACED_OUTCOMES:
            out.append(record)
    return out


def _account_truth_by_candidate(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    return latest_by_candidate(rows)


def build_pending_limit_lifecycle_audit_row(
    *,
    group_rows: list[dict[str, Any]],
    generated_at_utc: str,
    raw_trade_id_collision_symbols: list[str],
    matched_candidate: dict[str, Any] | None,
    candidate_match_status: str,
    matched_trade_record: TradeRecordCandidate | None,
    trade_record_match_status: str,
    matching_join_rows: list[dict[str, Any]],
    persisted_intent: dict[str, Any] | None,
    path_row: dict[str, Any] | None,
    ltf_row: dict[str, Any] | None,
    account_truth_row: dict[str, Any] | None,
) -> dict[str, Any]:
    sorted_group = sorted(group_rows, key=_latest_timestamp)
    latest = sorted_group[-1]
    final_state, final_state_status = _classify_final_state(latest)
    statuses = _required_field_statuses(
        latest=latest,
        matched_candidate=matched_candidate,
        matched_trade_record=matched_trade_record,
        persisted_intent=persisted_intent,
        final_state_status=final_state_status,
        generated_at_utc=generated_at_utc,
    )
    actions = _action_codes_from_statuses(statuses)
    limitations: list[str] = []

    if not latest.get("candidate_id"):
        if matched_candidate:
            limitations.append("LEGACY_LIFECYCLE_ROW_CANDIDATE_ID_NOT_CAPTURED_RECOVERED_FROM_CANDIDATE")
        elif matched_trade_record:
            limitations.append("LEGACY_LIFECYCLE_ROW_CANDIDATE_ID_NOT_CAPTURED_RECOVERED_FROM_TRADE_RECORD")
        else:
            actions.append("LIFECYCLE_CANDIDATE_ID_UNRECOVERABLE")
    if not latest.get("decision_time_utc"):
        if matched_candidate or matched_trade_record:
            limitations.append("LEGACY_LIFECYCLE_ROW_DECISION_TIME_NOT_CAPTURED_RECOVERED")
        else:
            actions.append("LIFECYCLE_DECISION_TIME_UNRECOVERABLE")
    if not latest.get("source_symbol"):
        limitations.append("LEGACY_LIFECYCLE_ROW_SOURCE_SYMBOL_NOT_CAPTURED")
    if raw_trade_id_collision_symbols:
        limitations.append("LEGACY_RAW_TRADE_ID_NOT_GLOBALLY_UNIQUE")
    if any(row.get("manual_backfill_status") == "SOURCE_NOT_CAPTURED" for row in matching_join_rows):
        limitations.append("LEGACY_JOIN_BACKFILL_ROW_SOURCE_NOT_CAPTURED_SUPERSEDED_BY_AUDIT")
    if matched_trade_record and matched_trade_record.record.get("pending_lifecycle") is None:
        limitations.append("TRADE_RECORD_PENDING_LIFECYCLE_FIELD_NOT_EMBEDDED")
    if matched_trade_record and matched_trade_record.record.get("execution") is None:
        limitations.append("TRADE_RECORD_EXECUTION_FIELD_NULL_NO_BROKER_FILL_CLAIM")
    if persisted_intent and not persisted_intent.get("candidate_id"):
        limitations.append("PERSISTED_PENDING_INTENT_CANDIDATE_ID_NOT_CAPTURED")
    if persisted_intent and not persisted_intent.get("decision_time_utc"):
        limitations.append("PERSISTED_PENDING_INTENT_DECISION_TIME_NOT_CAPTURED")
    if (
        statuses["persisted_pending_intent"]
        == "DOCUMENTED_STALE_INTERNAL_INTENT_NOT_PERSISTED_NO_BROKER_ORDER"
    ):
        limitations.append("STALE_INTERNAL_PENDING_INTENT_NOT_PERSISTED_NO_BROKER_ORDER")
    if not path_row:
        limitations.append("CANDIDATE_PATH_ROW_NOT_AVAILABLE_FOR_LIFECYCLE_GROUP")
    if account_truth_row:
        status = str(account_truth_row.get("account_truth_status") or "")
        if "MISMATCH" in status:
            actions.append("BROKER_POSITION_MISMATCH_REPORTED_BY_ACCOUNT_TRUTH")
        elif account_truth_row.get("actual_r_claim_allowed") is False:
            limitations.append("ACCOUNT_TRUTH_SOURCE_BLOCKED_NO_BROKER_ACTUAL_R")

    if final_state_status.startswith("ACTION_REQUIRED"):
        actions.append(final_state_status)
    if str(latest.get("intent_after_check") or "") == "order_send_success_filled" and not (
        latest.get("trade_state_ticket") or latest.get("pending_ticket")
    ):
        actions.append("FILLED_STATE_WITHOUT_BROKER_TICKET")

    audit_status = ACTION_REQUIRED if actions else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
    candidate_id = (
        latest.get("candidate_id")
        or (matched_candidate or {}).get("candidate_id")
        or (matched_trade_record.candidate_id if matched_trade_record else None)
    )
    decision_time = (
        latest.get("decision_time_utc")
        or (matched_candidate or {}).get("decision_time_utc")
        or (matched_trade_record.decision_time_utc if matched_trade_record else None)
    )
    global_key = pending_intent_global_key(latest)
    join_status_counts = Counter(str(row.get("join_status") or "UNKNOWN") for row in matching_join_rows)
    row_key = f"{global_key}|{SCHEMA_VERSION}"
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "pending_intent_global_key": global_key,
        "raw_trade_id": latest.get("trade_id"),
        "raw_trade_id_collision_symbols": raw_trade_id_collision_symbols,
        "trade_id_global_uniqueness_status": (
            "LEGACY_COLLIDES_ACROSS_SYMBOLS" if raw_trade_id_collision_symbols else "UNIQUE_IN_LIFECYCLE_LOG"
        ),
        "candidate_id": candidate_id,
        "candidate_match_status": candidate_match_status,
        "trade_record_candidate_id": matched_trade_record.candidate_id if matched_trade_record else None,
        "trade_record_match_status": trade_record_match_status,
        "trade_record_path": str(matched_trade_record.path) if matched_trade_record else None,
        "symbol": latest.get("symbol"),
        "broker_symbol": latest.get("broker_symbol"),
        "source_symbol": latest.get("source_symbol"),
        "side": latest.get("side"),
        "decision_time_utc": decision_time,
        "entry_price": latest.get("entry_price"),
        "stop_loss": latest.get("stop_loss"),
        "take_profit_1": latest.get("take_profit_1"),
        "lifecycle_row_count": len(group_rows),
        "latest_lifecycle_timestamp_utc": latest.get("timestamp_utc"),
        "latest_lifecycle_checked_candle_time_utc": latest.get("checked_candle_time_utc"),
        "latest_lifecycle_intent_after_check": latest.get("intent_after_check"),
        "latest_lifecycle_fill_no_fill_label": latest.get("fill_no_fill_label"),
        "latest_lifecycle_broker_fill_state": latest.get("broker_fill_state"),
        "latest_lifecycle_order_send_attempted": latest.get("order_send_attempted"),
        "latest_lifecycle_order_send_success": latest.get("order_send_success"),
        "latest_lifecycle_cancel_reason": latest.get("cancel_reason") or latest.get("reason"),
        "final_state": final_state,
        "final_state_status": final_state_status,
        "missed_move_classification": _missed_move_classification(path_row, ltf_row),
        "path_label": (path_row or {}).get("path_label"),
        "ltf_terminal_outcome_status": (ltf_row or {}).get("terminal_outcome_status"),
        "persisted_pending_intent_status": statuses["persisted_pending_intent"],
        "persisted_pending_intent_path": (persisted_intent or {}).get("source_path"),
        "join_backfill_row_count": len(matching_join_rows),
        "join_backfill_status_counts": dict(join_status_counts),
        "required_field_statuses": statuses,
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
        "pending_limit_lifecycle_audit_status": audit_status,
        "manual_backfill_status": "BACKFILLED_FROM_LIFECYCLE_CANDIDATE_TRADE_RECORD_PATH_AND_PENDING_INTENT_ROWS",
        "no_leak_status": "POST_DECISION_PENDING_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_missing_lifecycle_audit_row(
    *,
    source_row: dict[str, Any],
    generated_at_utc: str,
    source_kind: str,
    lifecycle_logger_started_at_utc: str | None = None,
) -> dict[str, Any]:
    candidate_id = source_row.get("candidate_id")
    row_key = f"{source_kind}|{candidate_id or source_row.get('trade_id')}|{SCHEMA_VERSION}"
    logger_started_at = parse_utc(lifecycle_logger_started_at_utc)
    decision_time = parse_utc(source_row.get("decision_time_utc"))
    predates_lifecycle_logger = bool(logger_started_at and decision_time and decision_time < logger_started_at)
    has_trade_record_exit = bool(source_row.get("_trade_record_has_exit"))
    has_trade_record_execution = bool(source_row.get("_trade_record_has_execution"))
    has_trade_record_pending_lifecycle = bool(source_row.get("_trade_record_has_pending_lifecycle"))

    limitations: list[str] = []
    actions: list[str] = []
    if not source_row.get("source_symbol"):
        limitations.append("SOURCE_SYMBOL_NOT_CAPTURED")
    if source_kind == "trade_record":
        if not has_trade_record_pending_lifecycle:
            limitations.append("TRADE_RECORD_PENDING_LIFECYCLE_FIELD_NOT_EMBEDDED")
        if not has_trade_record_execution:
            limitations.append("TRADE_RECORD_EXECUTION_FIELD_NULL_NO_BROKER_FILL_CLAIM")
        if has_trade_record_exit and not has_trade_record_execution:
            limitations.append("TRADE_RECORD_EXIT_PRESENT_BUT_EXECUTION_FIELD_NULL")

    if has_trade_record_exit:
        final_state = "TRADE_RECORD_EXIT_PRESENT_NO_LIFECYCLE_GROUP"
        final_state_status = "FINAL_STATE_RECOVERED_FROM_TRADE_RECORD_EXIT"
        missed_move = "TRADE_RECORD_EXIT_PRESENT_NO_PENDING_LIFECYCLE_GROUP"
        limitations.append("PENDING_LIFECYCLE_GROUP_MISSING_RECOVERED_FROM_TRADE_RECORD_EXIT")
    elif has_trade_record_execution:
        final_state = "TRADE_RECORD_EXECUTION_PRESENT_NO_LIFECYCLE_GROUP"
        final_state_status = "FINAL_STATE_RECOVERED_FROM_TRADE_RECORD_EXECUTION"
        missed_move = "TRADE_RECORD_EXECUTION_PRESENT_NO_PENDING_LIFECYCLE_GROUP"
        limitations.append("PENDING_LIFECYCLE_GROUP_MISSING_RECOVERED_FROM_TRADE_RECORD_EXECUTION")
    elif has_trade_record_pending_lifecycle:
        final_state = "TRADE_RECORD_EMBEDDED_PENDING_LIFECYCLE_NO_LOG_GROUP"
        final_state_status = "FINAL_STATE_RECOVERED_FROM_TRADE_RECORD_PENDING_LIFECYCLE"
        missed_move = "TRADE_RECORD_PENDING_LIFECYCLE_PRESENT_NO_LOG_GROUP"
        limitations.append("PENDING_LIFECYCLE_GROUP_MISSING_RECOVERED_FROM_TRADE_RECORD_PENDING_LIFECYCLE")
    elif predates_lifecycle_logger:
        final_state = "LEGACY_PENDING_LIFECYCLE_TRUTH_UNRECOVERABLE"
        final_state_status = "DOCUMENTED_UNRECOVERABLE_PRE_LIFECYCLE_LOGGER_SOURCE"
        missed_move = "NO_LIFECYCLE_GROUP_PRE_LOGGER_UNRECOVERABLE"
        limitations.extend(
            [
                "LEGACY_SOURCE_PREDATES_PENDING_LIFECYCLE_LOGGER",
                "PENDING_LIFECYCLE_GROUP_UNRECOVERABLE_PRE_LOGGER",
            ]
        )
    else:
        final_state = "PENDING_LIFECYCLE_GROUP_MISSING"
        final_state_status = "ACTION_REQUIRED_MISSING_LIFECYCLE_TRUTH"
        missed_move = "NO_LIFECYCLE_GROUP"
        actions.append("LIMIT_PLACED_SOURCE_HAS_NO_MATCHING_PENDING_LIFECYCLE_GROUP")

    status = ACTION_REQUIRED if actions else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
    if final_state_status.startswith("FINAL_STATE_RECOVERED"):
        final_state_field_status = "RECOVERED_FROM_TRADE_RECORD"
    elif final_state_status.startswith("DOCUMENTED"):
        final_state_field_status = "DOCUMENTED_LIMITATION"
    else:
        final_state_field_status = "ACTION_REQUIRED"
    if actions:
        persisted_intent_status = "UNKNOWN_NO_LIFECYCLE_GROUP"
    elif predates_lifecycle_logger:
        persisted_intent_status = "NOT_APPLICABLE_PRE_LIFECYCLE_LOGGER_SOURCE"
    else:
        persisted_intent_status = "NOT_APPLICABLE_RECOVERED_FROM_TRADE_RECORD_SOURCE"
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": row_key,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "pending_intent_global_key": pending_intent_global_key(source_row),
        "raw_trade_id": source_row.get("trade_id"),
        "raw_trade_id_collision_symbols": [],
        "trade_id_global_uniqueness_status": "UNKNOWN_NO_LIFECYCLE_GROUP",
        "candidate_id": candidate_id,
        "candidate_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP" if source_kind == "shadow_candidate" else "NOT_APPLICABLE",
        "trade_record_candidate_id": candidate_id if source_kind == "trade_record" else None,
        "trade_record_match_status": "SOURCE_ONLY_NO_LIFECYCLE_GROUP" if source_kind == "trade_record" else "NOT_APPLICABLE",
        "trade_record_path": source_row.get("trade_record_path"),
        "symbol": source_row.get("symbol"),
        "broker_symbol": source_row.get("broker_symbol"),
        "source_symbol": source_row.get("source_symbol"),
        "side": source_row.get("side"),
        "decision_time_utc": source_row.get("decision_time_utc"),
        "entry_price": source_row.get("entry_price"),
        "stop_loss": source_row.get("stop_loss"),
        "take_profit_1": source_row.get("take_profit_1"),
        "lifecycle_row_count": 0,
        "latest_lifecycle_timestamp_utc": None,
        "latest_lifecycle_checked_candle_time_utc": None,
        "latest_lifecycle_intent_after_check": None,
        "latest_lifecycle_fill_no_fill_label": None,
        "latest_lifecycle_broker_fill_state": None,
        "latest_lifecycle_order_send_attempted": None,
        "latest_lifecycle_order_send_success": None,
        "latest_lifecycle_cancel_reason": None,
        "final_state": final_state,
        "final_state_status": final_state_status,
        "missed_move_classification": missed_move,
        "path_label": None,
        "ltf_terminal_outcome_status": None,
        "persisted_pending_intent_status": persisted_intent_status,
        "persisted_pending_intent_path": None,
        "join_backfill_row_count": 0,
        "join_backfill_status_counts": {},
        "required_field_statuses": {
            "candidate_id": "RAW_CAPTURED" if candidate_id else "ACTION_REQUIRED_MISSING_CANDIDATE_ID",
            "decision_time_utc": "RAW_CAPTURED" if source_row.get("decision_time_utc") else "ACTION_REQUIRED_MISSING_DECISION_TIME",
            "source_symbol": "RAW_CAPTURED" if source_row.get("source_symbol") else "SOURCE_NOT_CAPTURED",
            "trade_geometry": "RAW_CAPTURED_COMPLETE",
            "order_send_status": (
                "RECOVERED_FROM_TRADE_RECORD"
                if final_state_status.startswith("FINAL_STATE_RECOVERED")
                else "DOCUMENTED_LIMITATION_PRE_LIFECYCLE_LOGGER"
                if predates_lifecycle_logger
                else "ACTION_REQUIRED_MISSING_ORDER_SEND_STATUS"
            ),
            "cancel_reason": "NOT_APPLICABLE",
            "final_state": final_state_field_status,
            "persisted_pending_intent": persisted_intent_status,
        },
        "documented_limitation_codes": sorted(set(limitations)),
        "action_required_codes": sorted(set(actions)),
        "pending_limit_lifecycle_audit_status": status,
        "manual_backfill_status": (
            "SOURCE_ONLY_NO_LIFECYCLE_GROUP"
            if actions
            else "DOCUMENTED_SOURCE_ONLY_NO_LIFECYCLE_GROUP_PRE_LOGGER"
            if predates_lifecycle_logger
            else "RECOVERED_SOURCE_ONLY_NO_LIFECYCLE_GROUP_FROM_TRADE_RECORD"
        ),
        "pending_lifecycle_logger_started_at_utc": lifecycle_logger_started_at_utc,
        "no_leak_status": "POST_DECISION_PENDING_LIFECYCLE_AUDIT_NO_DECISION_FEATURE",
        "promotion_verdict": PROMOTION_VERDICT,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_pending_limit_lifecycle_audit_rows(
    candidate_rows: list[tuple[int, dict[str, Any]]],
    lifecycle_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
    join_rows: list[tuple[int, dict[str, Any]]] | None = None,
    path_rows: list[tuple[int, dict[str, Any]]] | None = None,
    ltf_rows: list[tuple[int, dict[str, Any]]] | None = None,
    trade_record_candidates: list[TradeRecordCandidate] | None = None,
    account_truth_rows: list[tuple[int, dict[str, Any]]] | None = None,
    persisted_pending_intents: list[dict[str, Any]] | None = None,
    decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    candidates = [row for _, row in candidate_rows]
    lifecycle_payloads = [row for _, row in lifecycle_rows]
    lifecycle_logger_started_at = _earliest_lifecycle_timestamp(lifecycle_payloads)
    lifecycle_logger_started_at_utc = lifecycle_logger_started_at.isoformat() if lifecycle_logger_started_at else None
    grouped: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in lifecycle_payloads:
        grouped[lifecycle_group_key(row)].append(row)

    trade_id_symbols: dict[str, set[str]] = defaultdict(set)
    for row in lifecycle_payloads:
        if row.get("trade_id"):
            trade_id_symbols[str(row.get("trade_id"))].add(str(row.get("symbol") or ""))

    lifecycle_trade_ids = {str(row.get("trade_id") or "") for row in lifecycle_payloads if row.get("trade_id")}
    scoped_trade_records = _limit_trade_records(
        trade_record_candidates or [],
        decision_date_prefix=decision_date_prefix,
        lifecycle_trade_ids=lifecycle_trade_ids,
    )
    scoped_candidates = _limit_candidates(candidate_rows, decision_date_prefix)
    latest_paths = latest_by_candidate(path_rows or [])
    latest_ltf = latest_by_candidate(ltf_rows or [])
    account_by_candidate = _account_truth_by_candidate(account_truth_rows or [])
    persisted = persisted_pending_intents or []

    matched_candidate_ids: set[str] = set()
    matched_trade_record_ids: set[str] = set()
    rows: list[dict[str, Any]] = []

    for _, group in sorted(grouped.items(), key=lambda item: lifecycle_group_key(item[1][-1])):
        sorted_group = sorted(group, key=_latest_timestamp)
        latest = sorted_group[-1]
        candidate_matches = [candidate for candidate in candidates if _candidate_matches_lifecycle(candidate, latest)]
        trade_record_matches = [record for record in scoped_trade_records if _trade_record_matches_lifecycle(record, latest)]
        persisted_matches = [intent for intent in persisted if _persisted_intent_matches_lifecycle(intent, latest)]

        matched_candidate = candidate_matches[0] if len(candidate_matches) == 1 else None
        matched_trade_record = trade_record_matches[0] if len(trade_record_matches) == 1 else None
        candidate_status = (
            "MATCHED_BY_CANDIDATE_ID_OR_SYMBOL_SIDE_PRICE_GEOMETRY"
            if matched_candidate
            else "AMBIGUOUS_MULTIPLE_CANDIDATES"
            if len(candidate_matches) > 1
            else "NO_SHADOW_CANDIDATE_MATCH"
        )
        trade_record_status = (
            "MATCHED_BY_LIMIT_INTENT_TRADE_ID_OR_SYMBOL_SIDE_PRICE_GEOMETRY"
            if matched_trade_record
            else "AMBIGUOUS_MULTIPLE_TRADE_RECORDS"
            if len(trade_record_matches) > 1
            else "NO_TRADE_RECORD_MATCH"
        )
        if matched_candidate:
            matched_candidate_ids.add(str(matched_candidate.get("candidate_id") or ""))
        if matched_trade_record:
            matched_trade_record_ids.add(matched_trade_record.candidate_id)

        cid = str((matched_candidate or {}).get("candidate_id") or (matched_trade_record.candidate_id if matched_trade_record else ""))
        collision_symbols = sorted(
            symbol
            for symbol in trade_id_symbols.get(str(latest.get("trade_id") or ""), set())
            if symbol and symbol != str(latest.get("symbol") or "")
        )
        join_matches = _matching_join_rows(sorted_group, join_rows or [])
        rows.append(
            build_pending_limit_lifecycle_audit_row(
                group_rows=sorted_group,
                generated_at_utc=generated_at_utc,
                raw_trade_id_collision_symbols=collision_symbols,
                matched_candidate=matched_candidate,
                candidate_match_status=candidate_status,
                matched_trade_record=matched_trade_record,
                trade_record_match_status=trade_record_status,
                matching_join_rows=join_matches,
                persisted_intent=persisted_matches[0] if len(persisted_matches) == 1 else None,
                path_row=latest_paths.get(cid),
                ltf_row=latest_ltf.get(cid),
                account_truth_row=account_by_candidate.get(cid),
            )
        )

    matched_group_keys = {row["pending_intent_global_key"] for row in rows}
    scoped_trade_record_ids = {record.candidate_id for record in scoped_trade_records}
    source_only_candidate_ids: set[str] = set()
    source_only_global_keys: set[str] = set()
    for candidate in scoped_candidates:
        source = _source_row_from_candidate(candidate)
        source_key = pending_intent_global_key(source)
        candidate_id = str(candidate.get("candidate_id") or "")
        if candidate_id in matched_candidate_ids:
            continue
        if candidate_id in scoped_trade_record_ids:
            continue
        if source_key in matched_group_keys:
            continue
        row = build_missing_lifecycle_audit_row(
            source_row=source,
            generated_at_utc=generated_at_utc,
            source_kind="shadow_candidate",
            lifecycle_logger_started_at_utc=lifecycle_logger_started_at_utc,
        )
        rows.append(row)
        if candidate_id:
            source_only_candidate_ids.add(candidate_id)
        source_only_global_keys.add(source_key)
    for record in scoped_trade_records:
        if record.candidate_id in matched_trade_record_ids:
            continue
        source = _source_row_from_trade_record(record)
        source["trade_record_path"] = str(record.path)
        source_key = pending_intent_global_key(source)
        if record.candidate_id in source_only_candidate_ids:
            continue
        if source_key in matched_group_keys or source_key in source_only_global_keys:
            continue
        row = build_missing_lifecycle_audit_row(
            source_row=source,
            generated_at_utc=generated_at_utc,
            source_kind="trade_record",
            lifecycle_logger_started_at_utc=lifecycle_logger_started_at_utc,
        )
        rows.append(row)
        source_only_candidate_ids.add(record.candidate_id)
        source_only_global_keys.add(source_key)

    return sorted(rows, key=lambda row: str(row.get("row_key") or ""))
