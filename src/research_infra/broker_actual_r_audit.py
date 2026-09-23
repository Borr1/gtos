"""Broker actual-R, slippage, cost, and exit-accounting audit helpers.

This module is research/tooling only. It separates account-history-realized
evidence from live R artifacts and synthetic path labels so local PnL/shadow
files cannot be mistaken for broker actual-R truth.

It does not call AI, canaries, MT5, broker orders, or paid data sources.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "broker_actual_r_audit_v1"
COMPLETE = "BROKER_ACTUAL_R_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "BROKER_ACTUAL_R_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "BROKER_ACTUAL_R_ACTION_REQUIRED"

ACCOUNT_HISTORY_REALIZED = "ACCOUNT_HISTORY_REALIZED"
LIVE_R_ARTIFACT = "LIVE_R_ARTIFACT"
RESEARCH_MEASURED = "RESEARCH_MEASURED"
SYNTHETIC_PATH_R = "SYNTHETIC_PATH_R"

ACCOUNTING_EVIDENCE_CLASSES = {
    ACCOUNT_HISTORY_REALIZED,
    LIVE_R_ARTIFACT,
    RESEARCH_MEASURED,
    SYNTHETIC_PATH_R,
}

_SYMBOL_ALIASES = {
    "NDX100": "NAS100",
    "NAS100.cash": "NAS100",
    "NAS100_cash": "NAS100",
    "US30.cash": "US30",
    "US30_cash": "US30",
}


def parse_utc(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        ts = value
    else:
        try:
            ts = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts.astimezone(timezone.utc)


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line), row) for line, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _canonical_symbol(symbol: Any) -> str:
    text = str(symbol or "")
    return _SYMBOL_ALIASES.get(text, text)


def _actual_close(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("actual_close")
    return value if isinstance(value, dict) else {}


def _actual_r_from_close(row: dict[str, Any]) -> Any:
    close = _actual_close(row)
    for key in ("realized_R", "realized_r", "actual_r", "r_multiple"):
        if close.get(key) is not None:
            return close.get(key)
    return None


def _slippage_clock(row: dict[str, Any]) -> datetime:
    return parse_utc(row.get("ts")) or parse_utc(row.get("created_at_utc")) or datetime.min.replace(tzinfo=timezone.utc)


def _nearest_slippage_for_fill(fill_row: dict[str, Any], slippage_rows: list[tuple[int, dict[str, Any]]]) -> dict[str, Any] | None:
    symbol = str(fill_row.get("instrument") or fill_row.get("symbol") or "")
    entry_time = parse_utc(fill_row.get("entry_time"))
    if not symbol or not entry_time:
        return None
    candidates: list[tuple[float, int, dict[str, Any]]] = []
    for line_no, row in slippage_rows:
        if str(row.get("symbol") or "") != symbol:
            continue
        ts = _slippage_clock(row)
        diff = abs((ts - entry_time).total_seconds())
        if diff <= 120:
            candidates.append((diff, line_no, row))
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1]))[2]


def _slippage_status(row: dict[str, Any] | None) -> str:
    if not row:
        return "NO_ENTRY_SLIPPAGE_ROW_JOINED"
    if row.get("fill_price") in {0, 0.0, "0", "0.0"}:
        return "ENTRY_SLIPPAGE_ROW_BROKER_ZERO_FILL_PRICE_RECORDED_NOT_USED_AS_ACTUAL_FILL"
    return "ENTRY_SLIPPAGE_ROW_JOINED"


def _deal_time(row: dict[str, Any]) -> datetime | None:
    return (
        parse_utc(row.get("time_utc"))
        or parse_utc(row.get("time"))
        or parse_utc(row.get("created_at_utc"))
    )


def _is_close_deal(row: dict[str, Any]) -> bool:
    entry = row.get("entry")
    return entry in {1, "1", "DEAL_ENTRY_OUT", "OUT"}


def _same_int(left: Any, right: Any) -> bool:
    if left is None or right is None:
        return False
    try:
        return int(left) == int(right)
    except (TypeError, ValueError):
        return False


def _nearest_mt5_close_deal_for_fill(
    fill_row: dict[str, Any],
    slippage_row: dict[str, Any] | None,
    mt5_deal_rows: list[tuple[int, dict[str, Any]]],
) -> dict[str, Any] | None:
    symbol = str(fill_row.get("instrument") or fill_row.get("symbol") or "")
    if not symbol:
        return None
    exit_time = parse_utc(_actual_close(fill_row).get("exit_time"))
    position_ticket = (slippage_row or {}).get("ticket")
    candidates: list[tuple[int, float, int, dict[str, Any]]] = []
    for line_no, deal in mt5_deal_rows:
        deal_symbol = str(deal.get("symbol") or "")
        if deal_symbol and _canonical_symbol(deal_symbol) != _canonical_symbol(symbol):
            continue
        if not _is_close_deal(deal):
            continue
        ticket_match = any(
            _same_int(position_ticket, deal.get(key))
            for key in ("position_id", "order", "ticket")
        )
        deal_time = _deal_time(deal)
        if exit_time and deal_time:
            seconds = abs((deal_time - exit_time).total_seconds())
        else:
            seconds = 0.0
        if ticket_match:
            candidates.append((0, seconds, line_no, deal))
            continue
        # Conservative fallback: same symbol and close time within five minutes.
        if exit_time and deal_time and seconds <= 300:
            candidates.append((1, seconds, line_no, deal))
    if not candidates:
        return None
    return min(candidates, key=lambda item: (item[0], item[1], item[2]))[3]


def _account_truth_actual_r(row: dict[str, Any]) -> Any:
    for key in ("broker_actual_r", "actual_r", "realized_r", "realized_R", "r_multiple"):
        if row.get(key) is not None:
            return row.get(key)
    return None


def _num(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _cash_risk_amount(row: dict[str, Any]) -> float | None:
    for key in ("cash_risk_amount", "risk_amount", "dollar_risk", "account_risk_amount"):
        value = _num(row.get(key))
        if value is not None and value > 0:
            return value
    balance = _num(row.get("account_balance") or row.get("balance_at_entry"))
    risk_pct = _num(row.get("risk_pct") or row.get("risk_pct_at_entry"))
    if balance is not None and risk_pct is not None and balance > 0 and risk_pct > 0:
        return balance * (risk_pct / 100.0)
    return None


def _broker_net_r_fields(
    *,
    broker_profit: Any,
    commission: Any,
    swap: Any,
    cash_risk_amount: float | None,
) -> dict[str, Any]:
    profit = _num(broker_profit)
    commission_value = _num(commission)
    swap_value = _num(swap)
    if profit is None:
        status = "BROKER_PROFIT_SOURCE_NOT_CAPTURED"
        net_profit = None
        net_r = None
    elif commission_value is None or swap_value is None:
        status = "COMMISSION_OR_SWAP_SOURCE_NOT_CAPTURED"
        net_profit = None
        net_r = None
    elif cash_risk_amount is None or cash_risk_amount <= 0:
        status = "CASH_RISK_SOURCE_NOT_CAPTURED"
        net_profit = None
        net_r = None
    else:
        net_profit = round(profit + commission_value + swap_value, 8)
        net_r = round(net_profit / cash_risk_amount, 6)
        status = "CAPTURED"
    return {
        "broker_profit": profit,
        "broker_commission": commission_value,
        "broker_swap": swap_value,
        "cash_risk_amount": cash_risk_amount,
        "broker_net_profit": net_profit,
        "broker_net_r": net_r,
        "broker_net_r_status": status,
    }


def build_candidate_account_truth_audit_row(
    account_row: dict[str, Any],
    *,
    generated_at_utc: str,
) -> dict[str, Any]:
    action_codes: list[str] = []
    limitation_codes: list[str] = []
    actual_allowed = account_row.get("actual_r_claim_allowed")
    actual_r = _account_truth_actual_r(account_row)
    if actual_allowed is True and actual_r is None:
        action_codes.append("ACCOUNT_TRUTH_ALLOWS_ACTUAL_R_BUT_VALUE_MISSING")
    if actual_allowed is False:
        limitation_codes.append("ACCOUNT_HISTORY_REALIZED_DEAL_NOT_ATTACHED")
    if account_row.get("manual_backfill_status") == "SOURCE_BLOCKED":
        limitation_codes.append("CANONICAL_ACCOUNT_HISTORY_EXPORT_MISSING")

    accounting_class = ACCOUNT_HISTORY_REALIZED if actual_allowed is True and actual_r is not None else LIVE_R_ARTIFACT
    net_fields = _broker_net_r_fields(
        broker_profit=account_row.get("broker_profit") or account_row.get("profit"),
        commission=account_row.get("commission"),
        swap=account_row.get("swap"),
        cash_risk_amount=_cash_risk_amount(account_row),
    )
    audit_status = ACTION_REQUIRED if action_codes else COMPLETE_WITH_LIMITATIONS if limitation_codes else COMPLETE
    source_signature = _stable_hash(
        SCHEMA_VERSION,
        "candidate_account_truth",
        account_row.get("row_key"),
        account_row.get("candidate_id"),
        account_row.get("account_truth_status"),
        actual_allowed,
        actual_r,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("broker_actual_r_audit", source_signature),
        "source_dependency_signature": source_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "audit_scope": "candidate_account_truth",
        "candidate_id": account_row.get("candidate_id"),
        "fill_id": None,
        "symbol": account_row.get("symbol"),
        "broker_symbol": account_row.get("broker_symbol"),
        "decision_time_utc": account_row.get("decision_time_utc"),
        "trade_id": account_row.get("trade_id"),
        "ticket": None,
        "accounting_evidence_class": accounting_class,
        "actual_r_claim_allowed": bool(actual_allowed is True and actual_r is not None),
        "broker_actual_r": actual_r if accounting_class == ACCOUNT_HISTORY_REALIZED else None,
        **net_fields,
        "account_truth_status": account_row.get("account_truth_status"),
        "truth_lane": account_row.get("truth_lane"),
        "entry_slippage_status": "NOT_FILL_SCOPE",
        "exit_accounting_status": "ACCOUNT_HISTORY_REQUIRED_FOR_EXIT_ACCOUNTING",
        "commission_status": "ACCOUNT_HISTORY_REQUIRED",
        "swap_status": "ACCOUNT_HISTORY_REQUIRED",
        "close_reason_status": "ACCOUNT_HISTORY_REQUIRED",
        "time_in_trade_status": "ACCOUNT_HISTORY_REQUIRED",
        "source_links": {
            "account_truth_row_key": account_row.get("row_key"),
            "account_truth_manual_backfill_status": account_row.get("manual_backfill_status"),
        },
        "broker_actual_r_audit_status": audit_status,
        "action_required_codes": action_codes,
        "documented_limitation_codes": sorted(set(limitation_codes)),
        "manual_backfill_status": "BACKFILLED_OR_REFRESHED_FROM_ACCOUNT_TRUTH_ROWS",
        "no_leak_status": "POST_DECISION_ACCOUNTING_AUDIT_NOT_DECISION_FEATURE",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_filled_trade_audit_row(
    fill_row: dict[str, Any],
    *,
    slippage_row: dict[str, Any] | None,
    mt5_deal_row: dict[str, Any] | None = None,
    generated_at_utc: str,
) -> dict[str, Any]:
    action_codes: list[str] = []
    limitation_codes: list[str] = []
    close = _actual_close(fill_row)
    realized_r = _actual_r_from_close(fill_row)
    broker_reconciled = close.get("broker_deal_reconciled") is True
    mt5_export_joined = mt5_deal_row is not None
    if broker_reconciled and realized_r is None:
        action_codes.append("BROKER_RECONCILED_FILL_MISSING_REALIZED_R")
    if mt5_export_joined and realized_r is None:
        action_codes.append("MT5_EXPORT_JOINED_BUT_REALIZED_R_MISSING")
    if broker_reconciled or (mt5_export_joined and realized_r is not None):
        accounting_class = ACCOUNT_HISTORY_REALIZED
        if mt5_export_joined:
            limitation_codes.append("ACTUAL_R_COMPUTED_FROM_TRADE_RECORD_R_FORMULA_USING_MT5_DEAL_CLOSE")
            if not broker_reconciled:
                limitation_codes.append("LEGACY_ROW_BROKER_DEAL_RECONCILED_FLAG_FALSE_BUT_MT5_EXPORT_JOINED")
        else:
            limitation_codes.append("LEGACY_MT5_DEAL_RECONCILED_ROW_NOT_CANONICAL_EXPORT")
    elif realized_r is not None:
        accounting_class = LIVE_R_ARTIFACT
        limitation_codes.append("REALIZED_R_PRESENT_WITHOUT_BROKER_DEAL_RECONCILED_TRUE")
    else:
        accounting_class = RESEARCH_MEASURED
        limitation_codes.append("NO_REALIZED_R_ON_FILLED_TRADE_ROW")

    slip_status = _slippage_status(slippage_row)
    if slip_status != "ENTRY_SLIPPAGE_ROW_JOINED":
        limitation_codes.append(slip_status)
    commission_value = (mt5_deal_row or {}).get("commission", close.get("commission"))
    swap_value = (mt5_deal_row or {}).get("swap", close.get("swap"))
    broker_profit_value = (mt5_deal_row or {}).get("profit", close.get("profit"))
    net_fields = _broker_net_r_fields(
        broker_profit=broker_profit_value,
        commission=commission_value,
        swap=swap_value,
        cash_risk_amount=_cash_risk_amount(fill_row),
    )
    close_reason_value = close.get("exit_reason") or (mt5_deal_row or {}).get("reason")
    if commission_value is None:
        limitation_codes.append("COMMISSION_SOURCE_NOT_CAPTURED")
    if swap_value is None:
        limitation_codes.append("SWAP_SOURCE_NOT_CAPTURED")
    if not close_reason_value:
        limitation_codes.append("CLOSE_REASON_SOURCE_NOT_CAPTURED")

    audit_status = ACTION_REQUIRED if action_codes else COMPLETE_WITH_LIMITATIONS if limitation_codes else COMPLETE
    fill_id = str(fill_row.get("fill_id") or "")
    source_signature = _stable_hash(
        SCHEMA_VERSION,
        "mt5_export_realized_rule_v2",
        "filled_trade_reconciliation",
        fill_id,
        fill_row.get("entry_time"),
        (slippage_row or {}).get("ticket"),
        (mt5_deal_row or {}).get("ticket"),
        (mt5_deal_row or {}).get("order"),
        (mt5_deal_row or {}).get("profit"),
        commission_value,
        swap_value,
        realized_r,
        broker_reconciled,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "row_key": _stable_hash("broker_actual_r_audit", source_signature),
        "source_dependency_signature": source_signature,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "audit_scope": "filled_trade_reconciliation",
        "candidate_id": None,
        "fill_id": fill_id,
        "symbol": fill_row.get("instrument") or fill_row.get("symbol"),
        "broker_symbol": fill_row.get("instrument") or fill_row.get("symbol"),
        "decision_time_utc": fill_row.get("entry_time"),
        "trade_id": fill_id,
        "ticket": (slippage_row or {}).get("ticket"),
        "accounting_evidence_class": accounting_class,
        "actual_r_claim_allowed": accounting_class == ACCOUNT_HISTORY_REALIZED and realized_r is not None,
        "broker_actual_r": realized_r if accounting_class == ACCOUNT_HISTORY_REALIZED else None,
        **net_fields,
        "account_truth_status": (
            "BROKER_DEAL_RECONCILED_TRUE"
            if broker_reconciled
            else "MT5_ACCOUNT_HISTORY_EXPORT_JOINED"
            if mt5_export_joined
            else "BROKER_DEAL_RECONCILED_NOT_TRUE"
        ),
        "truth_lane": (
            "ACCOUNT_HISTORY_REALIZED"
            if accounting_class == ACCOUNT_HISTORY_REALIZED
            else "LIVE_R_ARTIFACT_NOT_ACCOUNT_HISTORY"
        ),
        "entry_slippage_status": slip_status,
        "exit_accounting_status": "EXIT_ROW_PRESENT",
        "commission_status": "COMMISSION_CAPTURED" if commission_value is not None else "COMMISSION_SOURCE_NOT_CAPTURED",
        "swap_status": "SWAP_CAPTURED" if swap_value is not None else "SWAP_SOURCE_NOT_CAPTURED",
        "close_reason_status": "CLOSE_REASON_CAPTURED" if close_reason_value else "CLOSE_REASON_SOURCE_NOT_CAPTURED",
        "time_in_trade_status": "ENTRY_EXIT_TIMES_PRESENT"
        if fill_row.get("entry_time") and close.get("exit_time")
        else "TIME_IN_TRADE_SOURCE_NOT_CAPTURED",
        "source_links": {
            "fill_id": fill_id,
            "slippage_ticket": (slippage_row or {}).get("ticket"),
            "slippage_ts": (slippage_row or {}).get("ts"),
            "broker_deal_reconciled": broker_reconciled,
            "mt5_export_deal_joined": mt5_export_joined,
            "mt5_export_deal_id": (mt5_deal_row or {}).get("ticket"),
            "mt5_export_order_id": (mt5_deal_row or {}).get("order"),
            "mt5_export_position_id": (mt5_deal_row or {}).get("position_id"),
            "mt5_export_deal_time_utc": (mt5_deal_row or {}).get("time_utc")
            or str((mt5_deal_row or {}).get("time") or ""),
        },
        "broker_actual_r_audit_status": audit_status,
        "action_required_codes": action_codes,
        "documented_limitation_codes": sorted(set(limitation_codes)),
        "manual_backfill_status": (
            "BACKFILLED_OR_REFRESHED_FROM_MT5_ACCOUNT_HISTORY_EXPORT"
            if mt5_export_joined else "BACKFILLED_OR_REFRESHED_FROM_FILLED_TRADE_ROWS"
        ),
        "no_leak_status": "POST_DECISION_ACCOUNTING_AUDIT_NOT_DECISION_FEATURE",
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
    }


def build_broker_actual_r_audit_rows(
    account_truth_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    slippage_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    j46_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    mt5_deal_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None = None,
    *,
    generated_at_utc: str | None = None,
    account_decision_date_prefix: str | None = None,
) -> list[dict[str, Any]]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    account_with_lines = _rows_with_lines(account_truth_rows)
    slippage_with_lines = _rows_with_lines(slippage_rows)
    j46_with_lines = _rows_with_lines(j46_rows)
    mt5_deal_with_lines = _rows_with_lines(mt5_deal_rows)
    rows: list[dict[str, Any]] = []
    for _line_no, account_row in account_with_lines:
        if account_decision_date_prefix and not str(account_row.get("decision_time_utc") or "").startswith(account_decision_date_prefix):
            continue
        rows.append(build_candidate_account_truth_audit_row(account_row, generated_at_utc=generated))
    for _line_no, fill_row in j46_with_lines:
        slippage_row = _nearest_slippage_for_fill(fill_row, slippage_with_lines)
        rows.append(
            build_filled_trade_audit_row(
                fill_row,
                slippage_row=slippage_row,
                mt5_deal_row=_nearest_mt5_close_deal_for_fill(
                    fill_row,
                    slippage_row,
                    mt5_deal_with_lines,
                ),
                generated_at_utc=generated,
            )
        )
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("broker_actual_r_audit_status") or "UNKNOWN") for row in rows)
    scope_counts = Counter(str(row.get("audit_scope") or "UNKNOWN") for row in rows)
    evidence_counts = Counter(str(row.get("accounting_evidence_class") or "UNKNOWN") for row in rows)
    entry_slippage_counts = Counter(str(row.get("entry_slippage_status") or "UNKNOWN") for row in rows)
    return {
        "audit_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "audit_scope_counts": dict(sorted(scope_counts.items())),
        "accounting_evidence_class_counts": dict(sorted(evidence_counts.items())),
        "entry_slippage_status_counts": dict(sorted(entry_slippage_counts.items())),
        "broker_actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "account_history_realized_rows": evidence_counts.get(ACCOUNT_HISTORY_REALIZED, 0),
        "live_r_artifact_rows": evidence_counts.get(LIVE_R_ARTIFACT, 0),
        "action_required_rows": status_counts.get(ACTION_REQUIRED, 0),
    }
