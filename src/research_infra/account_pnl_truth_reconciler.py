"""Account/PnL truth and evidence-class reconciliation helpers.

Research/tooling only. This module classifies local PnL/R artifacts without
promoting local notification dollars or path labels into broker truth.
"""

from __future__ import annotations

import hashlib
from collections import Counter
from datetime import datetime, timezone
from typing import Any


SCHEMA_VERSION = "account_pnl_truth_reconciliation_v1"
COMPLETE = "ACCOUNT_PNL_TRUTH_COMPLETE"
COMPLETE_WITH_LIMITATIONS = "ACCOUNT_PNL_TRUTH_COMPLETE_WITH_DOCUMENTED_LIMITATIONS"
ACTION_REQUIRED = "ACCOUNT_PNL_TRUTH_ACTION_REQUIRED"

ACCOUNT_HISTORY_REALIZED_R = "ACCOUNT_HISTORY_REALIZED_R"
ACCOUNT_HISTORY_PROFIT = "ACCOUNT_HISTORY_PROFIT"
LOCAL_NOTIFICATION_R_INPUT = "LOCAL_NOTIFICATION_R_INPUT"
LOCAL_RISK_DOLLAR_PROJECTION = "LOCAL_RISK_DOLLAR_PROJECTION"
LOCAL_DAILY_PNL_AGGREGATE = "LOCAL_DAILY_PNL_AGGREGATE"


def _stable_hash(*parts: Any) -> str:
    payload = "|".join(str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:32]


def _rows_with_lines(rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None) -> list[tuple[int, dict[str, Any]]]:
    if not rows:
        return []
    first = rows[0]
    if isinstance(first, tuple):
        return [(int(line), row) for line, row in rows if isinstance(row, dict)]  # type: ignore[misc]
    return [(index, row) for index, row in enumerate(rows, start=1) if isinstance(row, dict)]  # type: ignore[arg-type]


def _num(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _broker_rows_by_trade_id(rows: list[tuple[int, dict[str, Any]]]) -> dict[str, dict[str, Any]]:
    by_trade: dict[str, dict[str, Any]] = {}
    for _line, row in rows:
        trade_id = str(row.get("trade_id") or row.get("fill_id") or "")
        if not trade_id:
            continue
        if row.get("accounting_evidence_class") == "ACCOUNT_HISTORY_REALIZED":
            by_trade[trade_id] = row
    return by_trade


def _mt5_deals_by_ticket(rows: list[tuple[int, dict[str, Any]]]) -> dict[int, dict[str, Any]]:
    deals: dict[int, dict[str, Any]] = {}
    for _line, row in rows:
        ticket = _int_or_none(row.get("ticket"))
        if ticket is not None:
            deals[ticket] = row
    return deals


def _deal_for_broker_row(
    broker_row: dict[str, Any] | None,
    mt5_deals_by_ticket: dict[int, dict[str, Any]],
) -> dict[str, Any] | None:
    if not broker_row:
        return None
    source_links = broker_row.get("source_links") or {}
    deal_id = _int_or_none(source_links.get("mt5_export_deal_id"))
    if deal_id is None:
        return None
    return mt5_deals_by_ticket.get(deal_id)


def _source_has_native_evidence(row: dict[str, Any]) -> bool:
    return any(
        row.get(key)
        for key in (
            "r_evidence_class",
            "dollar_evidence_class",
            "pnl_evidence_class",
            "evidence_class",
        )
    )


def _base_row(*, generated_at_utc: str, source_scope: str, source_log: str, source_line: int | None) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "created_at_utc": generated_at_utc,
        "backfilled_at_utc": generated_at_utc,
        "source_scope": source_scope,
        "source_log": source_log,
        "source_line": source_line,
        "no_ai_calls": True,
        "no_canary_required": True,
        "no_execution": True,
        "ai_calls": 0,
        "canary_calls": 0,
        "order_calls": 0,
        "paid_data_calls": 0,
        "paid_fetch_attempted": False,
        "no_leak_status": "POST_DECISION_ACCOUNTING_RECONCILIATION_NOT_DECISION_FEATURE",
    }


def build_daily_pnl_history_row(
    source_row: dict[str, Any],
    *,
    source_line: int,
    broker_row: dict[str, Any] | None,
    mt5_deal: dict[str, Any] | None,
    generated_at_utc: str,
) -> dict[str, Any]:
    limitations: list[str] = []
    actions: list[str] = []
    result_r = _num(source_row.get("result_r"))
    realized_usd = _num(source_row.get("realized_usd"))
    risk_dollars = _num(source_row.get("risk_dollars"))
    broker_actual_r = _num((broker_row or {}).get("broker_actual_r"))
    broker_profit = _num((mt5_deal or {}).get("profit"))

    if result_r is not None and broker_actual_r is None:
        limitations.append("LOCAL_R_INPUT_NOT_ACCOUNT_HISTORY_REALIZED")
    if realized_usd is not None and broker_profit is None:
        limitations.append("LOCAL_RISK_DOLLAR_PROJECTION_NOT_BROKER_PROFIT")
    if realized_usd is not None and broker_profit is not None and round(realized_usd - broker_profit, 2) != 0.0:
        limitations.append("LOCAL_RISK_DOLLAR_DIFFERS_FROM_BROKER_PROFIT")
    if not _source_has_native_evidence(source_row):
        limitations.append("LEGACY_SOURCE_ROW_MISSING_NATIVE_EVIDENCE_CLASS_BACKFILLED_HERE")

    r_class = ACCOUNT_HISTORY_REALIZED_R if broker_actual_r is not None else LOCAL_NOTIFICATION_R_INPUT
    dollar_class = ACCOUNT_HISTORY_PROFIT if broker_profit is not None else LOCAL_RISK_DOLLAR_PROJECTION
    if not r_class or not dollar_class:
        actions.append("PNL_OR_R_CLAIM_MISSING_EVIDENCE_CLASS")

    status = ACTION_REQUIRED if actions else COMPLETE_WITH_LIMITATIONS if limitations else COMPLETE
    source_sig = _stable_hash(
        SCHEMA_VERSION,
        "daily_pnl_history",
        source_line,
        source_row.get("ts_utc"),
        source_row.get("trade_id"),
        result_r,
        realized_usd,
        broker_actual_r,
        broker_profit,
    )
    row = _base_row(
        generated_at_utc=generated_at_utc,
        source_scope="daily_pnl_history_trade",
        source_log="shadow_logs/daily_pnl_history.jsonl",
        source_line=source_line,
    )
    row.update(
        {
            "row_key": _stable_hash("account_pnl_truth", source_sig),
            "source_dependency_signature": source_sig,
            "trade_id": source_row.get("trade_id"),
            "symbol": source_row.get("symbol"),
            "source_ts_utc": source_row.get("ts_utc"),
            "result_r": result_r,
            "realized_usd": realized_usd,
            "risk_dollars": risk_dollars,
            "broker_actual_r": broker_actual_r,
            "broker_profit": broker_profit,
            "mt5_deal_id": _int_or_none((mt5_deal or {}).get("ticket")),
            "mt5_order_id": _int_or_none((mt5_deal or {}).get("order")),
            "r_evidence_class": r_class,
            "dollar_evidence_class": dollar_class,
            "actual_r_claim_allowed": broker_actual_r is not None,
            "actual_dollar_claim_allowed": broker_profit is not None,
            "account_pnl_truth_status": status,
            "documented_limitation_codes": sorted(set(limitations)),
            "action_required_codes": actions,
            "source_links": {
                "broker_actual_r_audit_row_key": (broker_row or {}).get("row_key"),
                "mt5_export_deal_id": (mt5_deal or {}).get("ticket"),
                "mt5_export_order_id": (mt5_deal or {}).get("order"),
                "mt5_export_profit": (mt5_deal or {}).get("profit"),
            },
        }
    )
    return row


def build_daily_pnl_state_rows(
    state: dict[str, Any] | None,
    *,
    generated_at_utc: str,
) -> list[dict[str, Any]]:
    if not state:
        return []
    rows: list[dict[str, Any]] = []
    for index, trade in enumerate(state.get("trades") or [], start=1):
        source_sig = _stable_hash(
            SCHEMA_VERSION,
            "daily_pnl_state_trade",
            state.get("date"),
            index,
            trade.get("trade_id"),
            trade.get("result_r"),
            trade.get("realized_usd"),
        )
        row = _base_row(
            generated_at_utc=generated_at_utc,
            source_scope="daily_pnl_state_trade",
            source_log="shadow_logs/daily_pnl.json",
            source_line=None,
        )
        row.update(
            {
                "row_key": _stable_hash("account_pnl_truth", source_sig),
                "source_dependency_signature": source_sig,
                "trade_id": trade.get("trade_id"),
                "symbol": trade.get("symbol"),
                "source_ts_utc": None,
                "result_r": _num(trade.get("result_r")),
                "realized_usd": _num(trade.get("realized_usd")),
                "risk_dollars": None,
                "broker_actual_r": None,
                "broker_profit": None,
                "mt5_deal_id": None,
                "mt5_order_id": None,
                "r_evidence_class": trade.get("r_evidence_class") or LOCAL_NOTIFICATION_R_INPUT,
                "dollar_evidence_class": trade.get("dollar_evidence_class") or LOCAL_RISK_DOLLAR_PROJECTION,
                "actual_r_claim_allowed": False,
                "actual_dollar_claim_allowed": False,
                "account_pnl_truth_status": COMPLETE_WITH_LIMITATIONS,
                "documented_limitation_codes": ["DAILY_PNL_STATE_IS_LOCAL_ROLLING_STATE_NOT_ACCOUNT_HISTORY"],
                "action_required_codes": [],
                "source_links": {"daily_pnl_date": state.get("date"), "trade_index": index},
            }
        )
        rows.append(row)
    if state.get("total_r") is not None or state.get("total_usd") is not None:
        source_sig = _stable_hash(
            SCHEMA_VERSION,
            "daily_pnl_state_aggregate",
            state.get("date"),
            state.get("total_r"),
            state.get("total_usd"),
            len(state.get("trades") or []),
        )
        row = _base_row(
            generated_at_utc=generated_at_utc,
            source_scope="daily_pnl_state_aggregate",
            source_log="shadow_logs/daily_pnl.json",
            source_line=None,
        )
        row.update(
            {
                "row_key": _stable_hash("account_pnl_truth", source_sig),
                "source_dependency_signature": source_sig,
                "trade_id": None,
                "symbol": None,
                "source_ts_utc": None,
                "result_r": _num(state.get("total_r")),
                "realized_usd": _num(state.get("total_usd")),
                "risk_dollars": None,
                "broker_actual_r": None,
                "broker_profit": None,
                "mt5_deal_id": None,
                "mt5_order_id": None,
                "r_evidence_class": LOCAL_DAILY_PNL_AGGREGATE,
                "dollar_evidence_class": LOCAL_DAILY_PNL_AGGREGATE,
                "actual_r_claim_allowed": False,
                "actual_dollar_claim_allowed": False,
                "account_pnl_truth_status": COMPLETE_WITH_LIMITATIONS,
                "documented_limitation_codes": ["AGGREGATE_LOCAL_DAILY_PNL_NOT_ACCOUNT_HISTORY_PROFIT"],
                "action_required_codes": [],
                "source_links": {"daily_pnl_date": state.get("date"), "trade_count": len(state.get("trades") or [])},
            }
        )
        rows.append(row)
    return rows


def build_mt5_deal_profit_rows(
    mt5_deal_rows: list[tuple[int, dict[str, Any]]],
    *,
    generated_at_utc: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, deal in mt5_deal_rows:
        if deal.get("entry") not in {1, "1"}:
            continue
        profit = _num(deal.get("profit"))
        source_sig = _stable_hash(
            SCHEMA_VERSION,
            "mt5_close_deal",
            deal.get("ticket"),
            deal.get("order"),
            deal.get("position_id"),
            profit,
        )
        row = _base_row(
            generated_at_utc=generated_at_utc,
            source_scope="mt5_account_history_close_deal",
            source_log=str(deal.get("_source_path") or "data/account_history/mt5_deals_*.jsonl"),
            source_line=line_no,
        )
        row.update(
            {
                "row_key": _stable_hash("account_pnl_truth", source_sig),
                "source_dependency_signature": source_sig,
                "trade_id": None,
                "symbol": deal.get("symbol"),
                "source_ts_utc": deal.get("time_utc"),
                "result_r": None,
                "realized_usd": profit,
                "risk_dollars": None,
                "broker_actual_r": None,
                "broker_profit": profit,
                "mt5_deal_id": _int_or_none(deal.get("ticket")),
                "mt5_order_id": _int_or_none(deal.get("order")),
                "r_evidence_class": None,
                "dollar_evidence_class": ACCOUNT_HISTORY_PROFIT,
                "actual_r_claim_allowed": False,
                "actual_dollar_claim_allowed": profit is not None,
                "account_pnl_truth_status": COMPLETE if profit is not None else ACTION_REQUIRED,
                "documented_limitation_codes": [],
                "action_required_codes": [] if profit is not None else ["MT5_CLOSE_DEAL_PROFIT_MISSING"],
                "source_links": {"position_id": deal.get("position_id"), "magic": deal.get("magic")},
            }
        )
        rows.append(row)
    return rows


def build_account_pnl_truth_rows(
    *,
    daily_pnl_state: dict[str, Any] | None,
    daily_pnl_history_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    broker_actual_r_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    mt5_deal_rows: list[tuple[int, dict[str, Any]]] | list[dict[str, Any]] | None,
    generated_at_utc: str | None = None,
) -> list[dict[str, Any]]:
    generated = generated_at_utc or datetime.now(timezone.utc).isoformat()
    history_with_lines = _rows_with_lines(daily_pnl_history_rows)
    broker_with_lines = _rows_with_lines(broker_actual_r_rows)
    mt5_with_lines = _rows_with_lines(mt5_deal_rows)
    broker_by_trade = _broker_rows_by_trade_id(broker_with_lines)
    mt5_by_ticket = _mt5_deals_by_ticket(mt5_with_lines)
    rows: list[dict[str, Any]] = []
    for line_no, history in history_with_lines:
        broker_row = broker_by_trade.get(str(history.get("trade_id") or ""))
        rows.append(
            build_daily_pnl_history_row(
                history,
                source_line=line_no,
                broker_row=broker_row,
                mt5_deal=_deal_for_broker_row(broker_row, mt5_by_ticket),
                generated_at_utc=generated,
            )
        )
    rows.extend(build_daily_pnl_state_rows(daily_pnl_state, generated_at_utc=generated))
    rows.extend(build_mt5_deal_profit_rows(mt5_with_lines, generated_at_utc=generated))
    return rows


def build_rolling_status(rows: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(row.get("account_pnl_truth_status") or "UNKNOWN") for row in rows)
    scope_counts = Counter(str(row.get("source_scope") or "UNKNOWN") for row in rows)
    r_class_counts = Counter(str(row.get("r_evidence_class") or "NONE") for row in rows)
    dollar_class_counts = Counter(str(row.get("dollar_evidence_class") or "NONE") for row in rows)
    return {
        "reconciliation_rows": len(rows),
        "status_counts": dict(sorted(status_counts.items())),
        "source_scope_counts": dict(sorted(scope_counts.items())),
        "r_evidence_class_counts": dict(sorted(r_class_counts.items())),
        "dollar_evidence_class_counts": dict(sorted(dollar_class_counts.items())),
        "actual_r_claim_allowed_rows": sum(1 for row in rows if row.get("actual_r_claim_allowed") is True),
        "actual_dollar_claim_allowed_rows": sum(1 for row in rows if row.get("actual_dollar_claim_allowed") is True),
        "action_required_rows": status_counts.get(ACTION_REQUIRED, 0),
    }
