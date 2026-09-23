"""Repair current redacted_account open trade-record lifecycle truth.

This script mutates only local GTOS JSON records. It uses read-only broker
probe evidence already captured by ``probe_dual_mt5_readonly.py`` plus existing
slippage telemetry. It does not import MT5, initialize terminals, send orders,
modify positions, or mutate broker state.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROUTE = Path("research/operations/vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02")
BROKER_PROBE = ROUTE / "DUAL_MT5_TERMINAL_ACCOUNT_PROBE.json"
SLIPPAGE_LOG = Path("shadow_logs/slippage.jsonl")
RECORD_ROOT = Path("knowledge_base/redacted_account_live_bee34003/trade_records")
AUDIT_PATH = ROUTE / "DUAL_CURRENT_OPEN_RECORD_REPAIR_AUDIT.json"
COMPAT_AUDIT_PATH = ROUTE / "DUAL_CURRENT_PARTIAL_RECORD_REPAIR_AUDIT.json"
REPAIR_LEDGER = ROUTE / "DUAL_REPAIR_LEDGER.jsonl"
LIFECYCLE_LEDGER = ROUTE / "DUAL_OPEN_TRADE_LIFECYCLE_LEDGER.jsonl"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    tmp.replace(path)


def _append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")


def _number(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _positive_number(value: Any) -> float | None:
    number = _number(value)
    if number is None or number <= 0:
        return None
    return number


def _positions_by_ticket() -> dict[int, dict[str, Any]]:
    probe = _load_json(BROKER_PROBE)
    positions = probe["probes"]["redacted_account"]["positions"]
    return {int(pos["ticket"]): pos for pos in positions}


def _slippage_rows_by_ticket() -> dict[int, list[dict[str, Any]]]:
    rows: dict[int, list[dict[str, Any]]] = {}
    if not SLIPPAGE_LOG.exists():
        return rows
    for raw in SLIPPAGE_LOG.read_text(encoding="utf-8").splitlines():
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError:
            continue
        ticket = row.get("ticket")
        if ticket is None:
            continue
        try:
            rows.setdefault(int(ticket), []).append(row)
        except (TypeError, ValueError):
            continue
    return rows


def _latest_entry(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    entries = [
        row
        for row in rows
        if row.get("slippage_event_type") == "entry"
        or row.get("partial_exit_lifecycle") == "ENTRY_FULL_POSITION_OPENED"
    ]
    return entries[-1] if entries else None


def _latest_partial(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    partials = [
        row
        for row in rows
        if row.get("partial_close") is True
        or row.get("partial_exit_lifecycle") == "PARTIAL_EXIT"
        or "PARTIAL" in str(row.get("close_event_type") or "").upper()
    ]
    return partials[-1] if partials else None


def _record_ticket_values(record: dict[str, Any]) -> set[int]:
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    values = {
        execution.get("ticket"),
        execution.get("position_ticket"),
        execution.get("entry_order_ticket"),
        execution.get("original_position_ticket"),
    }
    tickets: set[int] = set()
    for value in values:
        try:
            if value not in (None, "", 0, "0"):
                tickets.add(int(value))
        except (TypeError, ValueError):
            continue
    return tickets


def _record_paths_by_ticket() -> dict[int, list[Path]]:
    paths_by_ticket: dict[int, list[Path]] = {}
    for path in RECORD_ROOT.rglob("*.json"):
        try:
            record = _load_json(path)
        except (OSError, json.JSONDecodeError):
            continue
        for ticket in _record_ticket_values(record):
            paths_by_ticket.setdefault(ticket, []).append(path)
    return paths_by_ticket


def _position_direction(position: dict[str, Any], record: dict[str, Any]) -> str:
    pos_type = position.get("type")
    if pos_type == 0:
        return "LONG"
    if pos_type == 1:
        return "SHORT"
    execution = record.get("execution") if isinstance(record.get("execution"), dict) else {}
    direction = execution.get("direction") or record.get("decision_pipeline", {}).get("ai_direction")
    return str(direction or "").upper()


def _risk_released(direction: str, entry_price: float | None, broker_sl: float | None) -> bool:
    if entry_price is None or broker_sl is None:
        return False
    if direction == "LONG":
        return broker_sl >= entry_price
    if direction == "SHORT":
        return broker_sl <= entry_price
    return False


def _positive_time_minutes(value: Any) -> tuple[Any, str]:
    number = _number(value)
    if number is None:
        return value, "not_numeric_or_absent"
    if number < 0:
        return None, "negative_source_value_sanitized"
    return number, "source_value_kept"


def _first_present(*values: Any) -> Any:
    for value in values:
        if value not in (None, ""):
            return value
    return None


def _copy_dynamic_execution_fields(execution: dict[str, Any], instrumentation: dict[str, Any]) -> None:
    fields = (
        "gtos_vnext_dynamic_policy_selected",
        "gtos_vnext_dynamic_policy_applied",
        "gtos_vnext_dynamic_policy_replaced_policy",
        "gtos_vnext_dynamic_policy_candidate_action",
        "gtos_vnext_dynamic_policy_decision_status",
        "gtos_vnext_dynamic_policy_source_quality_action",
        "gtos_vnext_dynamic_policy_exit_management_action",
        "gtos_vnext_dynamic_policy_prop_action",
        "gtos_vnext_dynamic_policy_fixed_target_role",
        "gtos_vnext_execution_policy_id",
        "gtos_vnext_dynamic_be_trigger_r",
        "gtos_vnext_dynamic_final_target_r",
        "gtos_vnext_dynamic_be_trigger_price",
        "gtos_vnext_dynamic_final_target_price",
        "gtos_vnext_dynamic_time_stop_bars",
    )
    for field in fields:
        if execution.get(field) in (None, "") and instrumentation.get(field) not in (None, ""):
            execution[field] = instrumentation[field]
    selected_policy = str(
        _first_present(
            execution.get("gtos_vnext_dynamic_policy_selected"),
            instrumentation.get("gtos_vnext_dynamic_policy_selected"),
        )
        or ""
    ).strip().lower()
    if selected_policy and execution.get("gtos_vnext_dynamic_policy_applied") is None:
        execution["gtos_vnext_dynamic_policy_applied"] = True


def _partial_event(
    *,
    ticket: int,
    broker_position: dict[str, Any],
    partial_row: dict[str, Any],
    entry_row: dict[str, Any] | None,
    broker_volume: float | None,
    broker_sl: float | None,
    broker_tp: float | None,
) -> dict[str, Any]:
    recorded_remaining = _number(partial_row.get("remaining_volume"))
    repaired_minutes, minutes_status = _positive_time_minutes(
        partial_row.get("time_in_trade_minutes")
    )
    return {
        "type": "TP1_PARTIAL_REPAIRED_FROM_SLIPPAGE_AND_BROKER_POSITION",
        "time": partial_row.get("close_time") or partial_row.get("ts"),
        "price": partial_row.get("fill_price"),
        "volume_closed": partial_row.get("volume_closed"),
        "initial_volume": partial_row.get("initial_volume")
        or (entry_row or {}).get("executed_lot_size"),
        "remaining_volume": broker_volume,
        "recorded_remaining_volume": recorded_remaining,
        "remaining_volume_repair_status": (
            "remaining_volume_repaired_from_broker_residual"
            if broker_volume is not None and recorded_remaining != broker_volume
            else "remaining_volume_confirmed_by_broker_residual"
        ),
        "ticket": ticket,
        "old_ticket": ticket,
        "new_ticket": ticket,
        "close_reason": partial_row.get("close_reason"),
        "close_event_type": partial_row.get("close_event_type"),
        "mt5_order_id": partial_row.get("mt5_order_id") or partial_row.get("order_ticket"),
        "mt5_deal_id": partial_row.get("mt5_deal_id") or partial_row.get("deal_ticket"),
        "r_at_close": partial_row.get("close_r_multiple"),
        "time_in_trade_minutes": repaired_minutes,
        "time_in_trade_minutes_source_value": partial_row.get("time_in_trade_minutes"),
        "time_in_trade_minutes_repair_status": minutes_status,
        "sl_at_breakeven_at_close_event": partial_row.get("sl_at_breakeven"),
        "entry_cash_risk_amount": (entry_row or {}).get("cash_risk_amount"),
        "partial_row_cash_risk_amount": partial_row.get("cash_risk_amount"),
        "broker_stop_loss_after_repair": broker_sl,
        "broker_take_profit_after_repair": broker_tp,
        "broker_comment": broker_position.get("comment"),
        "repair_source": str(SLIPPAGE_LOG),
        "repair_source_ts": partial_row.get("ts"),
    }


def _open_risk_status(
    *,
    partial_open: bool,
    released: bool,
    cash_risk: float | None,
) -> tuple[float | None, str]:
    if partial_open and released:
        return 0.0, "residual_risk_released_by_breakeven_or_better_sl"
    if partial_open:
        return cash_risk, "residual_risk_not_released_or_unverified"
    if cash_risk is None:
        return None, "full_position_open_cash_risk_unknown"
    return cash_risk, "full_position_open_cash_risk_from_entry_record_or_slippage"


def _repair_one(
    ticket: int,
    broker_position: dict[str, Any],
    paths_by_ticket: dict[int, list[Path]],
    rows_by_ticket: dict[int, list[dict[str, Any]]],
) -> dict[str, Any]:
    paths = paths_by_ticket.get(ticket) or []
    if not paths:
        return {
            "status": "missing_local_trade_record",
            "ticket": ticket,
            "broker_position": broker_position,
            "runtime_effect_boundary": "no_local_json_mutation_no_mt5_call_no_broker_mutation",
            "recorded_at_utc": _utcnow(),
        }
    path = sorted(paths, key=lambda candidate: candidate.stat().st_mtime, reverse=True)[0]
    record = _load_json(path)
    execution = record.setdefault("execution", {})
    instrumentation = record.setdefault("instrumentation", {})
    lifecycle = record.setdefault("lifecycle", {})
    if not isinstance(execution, dict) or not isinstance(instrumentation, dict):
        raise RuntimeError(f"Malformed record sections for ticket {ticket}: {path}")

    before_execution = dict(execution)
    before_instrumentation = dict(instrumentation)
    rows = rows_by_ticket.get(ticket, [])
    entry_row = _latest_entry(rows)
    partial_row = _latest_partial(rows)
    updated_at = _utcnow()

    broker_volume = _number(broker_position.get("volume"))
    broker_sl = _number(broker_position.get("sl"))
    broker_tp = _number(broker_position.get("tp"))
    broker_entry = _number(broker_position.get("price_open"))
    direction = _position_direction(broker_position, record)
    entry_price = _number(
        _first_present(
            execution.get("entry_price"),
            execution.get("executed_entry_price"),
            (entry_row or {}).get("executed_entry_price"),
            broker_entry,
        )
    )
    initial_volume_candidates = [
        _positive_number(execution.get("initial_volume")),
        _positive_number((partial_row or {}).get("initial_volume")),
        _positive_number((entry_row or {}).get("executed_lot_size")),
        _positive_number(broker_volume),
    ]
    initial_volume = max(
        (candidate for candidate in initial_volume_candidates if candidate is not None),
        default=None,
    )
    selected_policy = str(
        _first_present(
            execution.get("gtos_vnext_dynamic_policy_selected"),
            instrumentation.get("gtos_vnext_dynamic_policy_selected"),
        )
        or ""
    ).strip().lower()
    partial_open = bool(
        partial_row is not None
        or str(broker_position.get("comment") or "").startswith("TP1_")
        or (
            broker_volume is not None
            and initial_volume is not None
            and broker_volume < initial_volume
        )
    )
    released = _risk_released(direction, entry_price, broker_sl)
    existing_cash_risk = _number(execution.get("cash_risk_amount"))
    entry_cash_risk = _positive_number((entry_row or {}).get("cash_risk_amount"))
    cash_risk = existing_cash_risk
    cash_risk_repair_status = "existing_value_kept"
    if (cash_risk is None or cash_risk <= 0.0) and entry_cash_risk is not None:
        cash_risk = entry_cash_risk
        execution["cash_risk_amount"] = cash_risk
        execution["cash_risk_amount_repair"] = {
            "status": "repaired_from_entry_slippage_row",
            "source": str(SLIPPAGE_LOG),
            "source_ts": entry_row.get("ts") if entry_row else None,
            "previous_value": existing_cash_risk,
        }
        cash_risk_repair_status = "repaired_from_entry_slippage_row"
    elif cash_risk is None:
        cash_risk_repair_status = "cash_risk_still_missing_no_positive_entry_source"

    open_risk_amount, open_risk_status = _open_risk_status(
        partial_open=partial_open,
        released=released,
        cash_risk=cash_risk,
    )

    execution.setdefault("original_position_ticket", before_execution.get("position_ticket"))
    execution["ticket"] = ticket
    execution["position_ticket"] = ticket
    execution["direction"] = direction or execution.get("direction")
    execution["entry_price"] = entry_price if entry_price is not None else execution.get("entry_price")
    execution["executed_entry_price"] = _first_present(
        execution.get("executed_entry_price"),
        (entry_row or {}).get("executed_entry_price"),
        broker_entry,
    )
    execution["initial_volume"] = initial_volume
    execution["current_volume"] = broker_volume
    if partial_open:
        execution["residual_volume"] = broker_volume
    execution["broker_stop_loss"] = broker_sl
    execution["active_stop_loss"] = broker_sl
    execution["broker_take_profit"] = broker_tp
    execution["active_take_profit"] = broker_tp
    execution["open_worst_case_cash_risk_amount"] = open_risk_amount
    execution["open_worst_case_cash_risk_status"] = open_risk_status
    execution["last_lifecycle_update_utc"] = updated_at
    execution["active_lifecycle_capture_status"] = (
        "repaired_from_route_broker_probe_and_slippage_rows_no_broker_mutation"
    )
    execution["broker_position_probe_snapshot"] = broker_position
    if selected_policy == "partial_be_runner" and broker_tp not in (None, 0):
        execution["take_profit_2"] = broker_tp
    if entry_row is not None:
        execution["entry_slippage_source_ts"] = entry_row.get("ts")
        entry_deal_ticket = entry_row.get("deal_ticket")
        if _positive_number(entry_deal_ticket) is not None:
            execution["entry_deal_ticket"] = entry_deal_ticket
            execution["entry_deal_ticket_status"] = "entry_deal_ticket_repaired_from_slippage_row"
        elif execution.get("entry_deal_ticket_status") in (None, ""):
            execution["entry_deal_ticket_status"] = (
                "mt5_result_deal_ticket_absent_using_order_position_join_keys"
            )
        if execution.get("entry_order_ticket") in (None, "") and entry_row.get("order_ticket"):
            execution["entry_order_ticket"] = entry_row.get("order_ticket")
    if partial_row is not None:
        execution["partial_slippage_source_ts"] = partial_row.get("ts")
    _copy_dynamic_execution_fields(execution, instrumentation)

    lifecycle["last_lifecycle_update_utc"] = updated_at
    lifecycle["source_repair_boundary"] = "local_record_only_no_broker_mutation"
    lifecycle["broker_position_ticket"] = ticket
    lifecycle["broker_position_volume"] = broker_volume
    lifecycle["broker_stop_loss"] = broker_sl
    lifecycle["broker_take_profit"] = broker_tp
    lifecycle["broker_comment"] = broker_position.get("comment")
    lifecycle["open_worst_case_cash_risk_amount"] = open_risk_amount
    lifecycle["open_worst_case_cash_risk_status"] = open_risk_status

    if partial_open:
        partial_event = _partial_event(
            ticket=ticket,
            broker_position=broker_position,
            partial_row=partial_row or {},
            entry_row=entry_row,
            broker_volume=broker_volume,
            broker_sl=broker_sl,
            broker_tp=broker_tp,
        )
        execution["tp1_hit"] = True
        execution["sl_at_breakeven"] = released
        execution["partial_close_events"] = [partial_event]
        execution["last_lifecycle_result"] = "current_partial_record_repaired_from_broker_probe"
        execution["residual_worst_case_cash_risk_amount"] = 0.0 if released else open_risk_amount
        execution["residual_worst_case_cash_risk_status"] = (
            "released_by_breakeven_or_better_sl" if released else "not_released_or_unverified"
        )
        lifecycle["active_trade_management_events"] = [partial_event]
        lifecycle["last_lifecycle_result"] = execution["last_lifecycle_result"]
        lifecycle["residual_position_ticket"] = ticket
        lifecycle["residual_volume"] = broker_volume
        lifecycle["residual_broker_stop_loss"] = broker_sl
        lifecycle["residual_broker_take_profit"] = broker_tp
        lifecycle["residual_risk_released"] = released
        instrumentation["gtos_vnext_active_lifecycle_truth_status"] = (
            "residual_open_lifecycle_update_repaired_from_broker_probe"
        )
        instrumentation["gtos_vnext_active_lifecycle_last_result"] = execution[
            "last_lifecycle_result"
        ]
        instrumentation["gtos_vnext_active_lifecycle_update_utc"] = updated_at
        instrumentation["gtos_vnext_recovered_partial_closed"] = True
        instrumentation["gtos_vnext_recovered_residual_open"] = True
        instrumentation["gtos_vnext_recovered_partial_close_events"] = [partial_event]
    else:
        execution["tp1_hit"] = bool(execution.get("tp1_hit"))
        execution["sl_at_breakeven"] = released
        execution["last_lifecycle_result"] = "current_full_open_record_aligned_from_broker_probe"
        lifecycle["last_lifecycle_result"] = execution["last_lifecycle_result"]
        instrumentation["gtos_vnext_active_lifecycle_truth_status"] = (
            "full_position_open_lifecycle_aligned_from_broker_probe"
        )
        instrumentation["gtos_vnext_active_lifecycle_last_result"] = execution[
            "last_lifecycle_result"
        ]
        instrumentation["gtos_vnext_active_lifecycle_update_utc"] = updated_at

    _write_json(path, record)

    return {
        "status": "repaired",
        "record_path": str(path),
        "ambiguous_record_paths": [str(candidate) for candidate in paths[1:]],
        "ticket": ticket,
        "symbol": record.get("metadata", {}).get("symbol"),
        "broker_position": broker_position,
        "entry_slippage_source_ts": entry_row.get("ts") if entry_row else None,
        "partial_slippage_source_ts": partial_row.get("ts") if partial_row else None,
        "partial_open_evidence": {
            "partial_row_present": partial_row is not None,
            "broker_comment": broker_position.get("comment"),
            "broker_volume": broker_volume,
            "initial_volume": initial_volume,
            "partial_open": partial_open,
        },
        "cash_risk_repair_status": cash_risk_repair_status,
        "before": {
            "current_volume": before_execution.get("current_volume"),
            "broker_stop_loss": before_execution.get("broker_stop_loss"),
            "broker_take_profit": before_execution.get("broker_take_profit"),
            "active_take_profit": before_execution.get("active_take_profit"),
            "cash_risk_amount": before_execution.get("cash_risk_amount"),
            "open_worst_case_cash_risk_amount": before_execution.get(
                "open_worst_case_cash_risk_amount"
            ),
            "partial_closed": before_instrumentation.get(
                "gtos_vnext_recovered_partial_closed"
            ),
            "residual_open": before_instrumentation.get(
                "gtos_vnext_recovered_residual_open"
            ),
        },
        "after": {
            "current_volume": execution.get("current_volume"),
            "broker_stop_loss": execution.get("broker_stop_loss"),
            "broker_take_profit": execution.get("broker_take_profit"),
            "active_take_profit": execution.get("active_take_profit"),
            "take_profit_2": execution.get("take_profit_2"),
            "cash_risk_amount": execution.get("cash_risk_amount"),
            "open_worst_case_cash_risk_amount": execution.get(
                "open_worst_case_cash_risk_amount"
            ),
            "open_worst_case_cash_risk_status": execution.get(
                "open_worst_case_cash_risk_status"
            ),
            "residual_worst_case_cash_risk_amount": execution.get(
                "residual_worst_case_cash_risk_amount"
            ),
            "partial_closed": instrumentation.get(
                "gtos_vnext_recovered_partial_closed"
            ),
            "residual_open": instrumentation.get("gtos_vnext_recovered_residual_open"),
        },
        "runtime_effect_boundary": "local_json_record_repair_only_no_mt5_call_no_broker_mutation",
        "recorded_at_utc": updated_at,
    }


def main() -> int:
    positions = _positions_by_ticket()
    rows_by_ticket = _slippage_rows_by_ticket()
    paths_by_ticket = _record_paths_by_ticket()
    repairs = [
        _repair_one(ticket, position, paths_by_ticket, rows_by_ticket)
        for ticket, position in sorted(positions.items())
    ]
    status = (
        "repaired"
        if all(row.get("status") == "repaired" for row in repairs)
        else "repaired_with_missing_local_records"
    )
    audit = {
        "schema_version": "dual_current_open_record_repair_audit_v2",
        "status": status,
        "recorded_at_utc": _utcnow(),
        "route_id": "vnext_dual_broker_live_monitoring_repair_supervisor_2026_06_02",
        "runtime_effect_boundary": "local_json_record_repair_only_no_mt5_call_no_broker_mutation",
        "source_probe": str(BROKER_PROBE),
        "source_slippage_log": str(SLIPPAGE_LOG),
        "open_position_count": len(positions),
        "repaired_count": sum(1 for row in repairs if row.get("status") == "repaired"),
        "missing_local_record_count": sum(
            1 for row in repairs if row.get("status") == "missing_local_trade_record"
        ),
        "repairs": repairs,
    }
    _write_json(AUDIT_PATH, audit)
    _write_json(COMPAT_AUDIT_PATH, audit)
    for repair in repairs:
        ledger_row = {
            **repair,
            "repair_class": "current_open_trade_record_lifecycle_truth_repair",
            "source_capture_status": "broker_probe_and_slippage_rows_exact_ticket_bound",
        }
        _append_jsonl(REPAIR_LEDGER, ledger_row)
        _append_jsonl(LIFECYCLE_LEDGER, ledger_row)
    print(json.dumps(audit, indent=2, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
