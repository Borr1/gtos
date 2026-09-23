#!/usr/bin/env python3
"""Capture exact read-only broker-day truth for every configured GTOS account.

The output separates trading cash, non-trading balance operations, current
equity/floating PnL, firm daily-loss reference, open risk, orders, deals, and
position-group lifecycle. Login identifiers are emitted only as SHA-256.

This script never selects symbols and never sends, modifies, cancels, or closes
an order. It deliberately over-fetches MT5 history in broker wall-clock space,
then filters every timestamp against the exact UTC reset boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.utils.broker_accounting import (  # noqa: E402
    TRADE_DEAL_TYPES,
    trade_deal_cash_delta,
    trade_deals_cash_delta,
)
from src.utils.broker_clock import (  # noqa: E402
    broker_epoch_to_utc,
    daily_reset_offset_hours,
    offset_seconds_at_utc,
    resolve_rule,
)


ACCOUNTS = (
    {
        "label": "FTMO",
        "profile": "operator_profile",
        "server_rule": "FTMO-Server3",
        "firm_reset_rule": "Europe/Prague",
        "day_anchor": "pipeline_state/ultimate_book/operator_profile/day_anchor.json",
    },
    {
        "label": "redacted_account",
        "profile": "redacted_account",
        "server_rule": "redacted_account-Server 2",
        "firm_reset_rule": None,
        "day_anchor": "pipeline_state/ultimate_book/redacted_account_live_bee34003/day_anchor.json",
    },
)

DEAL_ENTRY_NAME = {0: "in", 1: "out", 2: "inout", 3: "out_by"}
DEAL_TYPE_NAME = {
    0: "buy",
    1: "sell",
    2: "balance",
    3: "credit",
    4: "charge",
    5: "correction",
    6: "bonus",
    7: "commission",
    8: "commission_daily",
    9: "commission_monthly",
    10: "commission_agent_daily",
    11: "commission_agent_monthly",
    12: "interest",
    13: "buy_canceled",
    14: "sell_canceled",
    15: "dividend",
    16: "dividend_franked",
    17: "tax",
}
ORDER_TYPE_NAME = {
    0: "buy",
    1: "sell",
    2: "buy_limit",
    3: "sell_limit",
    4: "buy_stop",
    5: "sell_stop",
    6: "buy_stop_limit",
    7: "sell_stop_limit",
    8: "close_by",
}
ORDER_STATE_NAME = {
    0: "started",
    1: "placed",
    2: "canceled",
    3: "partial",
    4: "filled",
    5: "rejected",
    6: "expired",
    7: "request_add",
    8: "request_modify",
    9: "request_cancel",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def finite(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"nonfinite_numeric_value:{value!r}")
    return result


def sha256_text(value: Any) -> str:
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def surface_for_magic(magic: int) -> str:
    if magic == 20260401:
        return "gtos_production"
    if magic == 0:
        return "f5_minimal_experiment"
    if magic == 0:
        return "manual_or_unattributed"
    return "foreign_or_legacy_magic"


def reset_offset_hours(at_utc: datetime, firm_rule: str | None, server_rule: Any) -> float:
    if firm_rule:
        value = daily_reset_offset_hours(at_utc, firm_rule)
        if value is None:
            raise RuntimeError(f"unresolved_firm_reset_rule:{firm_rule}")
        return float(value)
    return float(offset_seconds_at_utc(at_utc, server_rule)) / 3600.0


def reset_window_start_utc(
    now_utc: datetime,
    *,
    firm_rule: str | None,
    server_rule: Any,
) -> datetime:
    """Resolve local midnight, including an offset transition since midnight."""

    now = now_utc.astimezone(timezone.utc)
    offset_now = reset_offset_hours(now, firm_rule, server_rule)
    local_midnight = (now + timedelta(hours=offset_now)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = local_midnight - timedelta(hours=offset_now)
    offset_at_start = reset_offset_hours(start, firm_rule, server_rule)
    if offset_at_start != offset_now:
        start = local_midnight - timedelta(hours=offset_at_start)
    return start


def raw_cash_delta(row: Any) -> float:
    return sum(finite(getattr(row, name, 0.0)) for name in ("profit", "commission", "swap", "fee"))


def load_day_anchor(path: Path, reset_date: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "path": str(path.relative_to(REPO_ROOT)),
        "exists": path.is_file(),
        "date_matches": False,
        "balance": None,
        "equity": None,
        "firm_daily_reference": None,
    }
    if not path.is_file():
        return result
    try:
        row = json.loads(path.read_text(encoding="utf-8"))
        result["recorded_date"] = row.get("date")
        result["date_matches"] = row.get("date") == reset_date
        if result["date_matches"]:
            balance = finite(row.get("balance"))
            equity = finite(row.get("equity"), balance)
            result.update(
                {
                    "balance": balance,
                    "equity": equity,
                    "firm_daily_reference": max(balance, equity),
                    "source_status": "persisted_at_reset_window_live_governor_anchor",
                }
            )
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        result["error"] = repr(exc)
    return result


def compact_account(account: Any) -> dict[str, Any]:
    return {
        "login_sha256": sha256_text(account.login),
        "server": str(account.server),
        "company": str(account.company),
        "currency": str(account.currency),
        "balance": finite(account.balance),
        "equity": finite(account.equity),
        "floating_pnl": finite(account.equity) - finite(account.balance),
        "broker_reported_profit": finite(account.profit),
        "credit": finite(account.credit),
        "margin": finite(account.margin),
        "margin_free": finite(account.margin_free),
        "margin_level": finite(account.margin_level),
        "leverage": int(account.leverage),
        "trade_allowed": bool(account.trade_allowed),
        "trade_expert": bool(account.trade_expert),
        "trade_mode": int(account.trade_mode),
        "margin_mode": int(account.margin_mode),
    }


def compact_terminal(terminal: Any) -> dict[str, Any]:
    return {
        "connected": bool(terminal.connected),
        "trade_allowed": bool(terminal.trade_allowed),
        "build": int(terminal.build),
        "company": str(terminal.company),
        "name": str(terminal.name),
        "path": str(terminal.path),
        "data_path": str(terminal.data_path),
    }


def identity_match(profile: dict[str, Any], account: Any, terminal: Any) -> dict[str, Any]:
    expected = ((profile.get("broker_profile") or {}).get("expected_account") or {})
    checks = {
        "login_sha256": sha256_text(account.login) == expected.get("login_sha256"),
        "server": str(account.server) == str(expected.get("server")),
        "company": str(account.company) == str(expected.get("company")),
        "currency": str(account.currency) == str(expected.get("currency")),
        "terminal_path_prefix": str(terminal.path).lower().startswith(
            str(expected.get("terminal_path") or "").lower()
        ),
        "terminal_data_path": str(terminal.data_path).lower()
        == str(expected.get("terminal_data_path") or "").lower(),
    }
    return {"checks": checks, "all_match": all(checks.values())}


def compact_deal(deal: Any, server_rule: Any) -> dict[str, Any]:
    deal_type = int(deal.type)
    entry = int(deal.entry)
    row = {
        "ticket": int(deal.ticket),
        "order": int(deal.order),
        "position_id": int(deal.position_id),
        "time_utc": iso(broker_epoch_to_utc(deal.time, server_rule)),
        "type": deal_type,
        "type_name": DEAL_TYPE_NAME.get(deal_type, f"unknown_{deal_type}"),
        "entry": entry,
        "entry_name": DEAL_ENTRY_NAME.get(entry, f"unknown_{entry}"),
        "magic": int(deal.magic),
        "surface": surface_for_magic(int(deal.magic)),
        "reason": int(deal.reason),
        "symbol": str(deal.symbol),
        "volume": finite(deal.volume),
        "price": finite(deal.price),
        "profit": finite(deal.profit),
        "commission": finite(deal.commission),
        "swap": finite(deal.swap),
        "fee": finite(deal.fee),
        "comment": str(deal.comment),
        "external_id": str(deal.external_id),
    }
    row["cash_delta"] = raw_cash_delta(deal)
    row["trading_cash_delta"] = trade_deal_cash_delta(deal)
    return row


def compact_history_order(order: Any, server_rule: Any) -> dict[str, Any]:
    order_type = int(order.type)
    state = int(order.state)
    return {
        "ticket": int(order.ticket),
        "position_id": int(order.position_id),
        "position_by_id": int(order.position_by_id),
        "time_setup_utc": iso(broker_epoch_to_utc(order.time_setup, server_rule)),
        "time_done_utc": iso(broker_epoch_to_utc(order.time_done, server_rule))
        if int(order.time_done or 0) > 0
        else None,
        "type": order_type,
        "type_name": ORDER_TYPE_NAME.get(order_type, f"unknown_{order_type}"),
        "state": state,
        "state_name": ORDER_STATE_NAME.get(state, f"unknown_{state}"),
        "magic": int(order.magic),
        "surface": surface_for_magic(int(order.magic)),
        "reason": int(order.reason),
        "symbol": str(order.symbol),
        "volume_initial": finite(order.volume_initial),
        "volume_current": finite(order.volume_current),
        "price_open": finite(order.price_open),
        "price_current": finite(order.price_current),
        "sl": finite(order.sl),
        "tp": finite(order.tp),
        "comment": str(order.comment),
        "external_id": str(order.external_id),
    }


def stop_risk(mt5: Any, *, side: int, symbol: str, volume: float, entry: float, sl: float) -> dict[str, Any]:
    if not sl or not entry or not volume:
        return {"status": "missing_or_zero_stop", "cash_risk": None}
    order_side = mt5.ORDER_TYPE_BUY if side == 0 else mt5.ORDER_TYPE_SELL
    value = mt5.order_calc_profit(order_side, symbol, volume, entry, sl)
    if value is None:
        return {"status": "order_calc_profit_failed", "cash_risk": None, "last_error": mt5.last_error()}
    loss = min(0.0, finite(value))
    return {"status": "broker_order_calc_profit", "cash_risk": abs(loss), "signed_pnl_at_stop": loss}


def compact_position(position: Any, mt5: Any, equity: float, server_rule: Any) -> dict[str, Any]:
    risk = stop_risk(
        mt5,
        side=int(position.type),
        symbol=str(position.symbol),
        volume=finite(position.volume),
        entry=finite(position.price_open),
        sl=finite(position.sl),
    )
    if risk.get("cash_risk") is not None:
        risk["equity_pct"] = risk["cash_risk"] / equity * 100.0 if equity else None
    return {
        "ticket": int(position.ticket),
        "identifier": int(position.identifier),
        "time_utc": iso(broker_epoch_to_utc(position.time, server_rule)),
        "type": int(position.type),
        "side": "buy" if int(position.type) == 0 else "sell",
        "magic": int(position.magic),
        "surface": surface_for_magic(int(position.magic)),
        "symbol": str(position.symbol),
        "volume": finite(position.volume),
        "price_open": finite(position.price_open),
        "price_current": finite(position.price_current),
        "sl": finite(position.sl),
        "tp": finite(position.tp),
        "profit": finite(position.profit),
        "swap": finite(position.swap),
        "comment": str(position.comment),
        "stop_risk": risk,
    }


def compact_pending_order(order: Any, mt5: Any, equity: float, server_rule: Any) -> dict[str, Any]:
    order_type = int(order.type)
    side = 0 if order_type in {0, 2, 4, 6} else 1
    risk = stop_risk(
        mt5,
        side=side,
        symbol=str(order.symbol),
        volume=finite(order.volume_current or order.volume_initial),
        entry=finite(order.price_open),
        sl=finite(order.sl),
    )
    if risk.get("cash_risk") is not None:
        risk["equity_pct"] = risk["cash_risk"] / equity * 100.0 if equity else None
    return {
        "ticket": int(order.ticket),
        "time_setup_utc": iso(broker_epoch_to_utc(order.time_setup, server_rule)),
        "type": order_type,
        "type_name": ORDER_TYPE_NAME.get(order_type, f"unknown_{order_type}"),
        "state": int(order.state),
        "state_name": ORDER_STATE_NAME.get(int(order.state), f"unknown_{int(order.state)}"),
        "magic": int(order.magic),
        "surface": surface_for_magic(int(order.magic)),
        "symbol": str(order.symbol),
        "volume_initial": finite(order.volume_initial),
        "volume_current": finite(order.volume_current),
        "price_open": finite(order.price_open),
        "sl": finite(order.sl),
        "tp": finite(order.tp),
        "comment": str(order.comment),
        "stop_risk": risk,
    }


def position_groups(deals: Iterable[dict[str, Any]], open_positions: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    by_position: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deal in deals:
        if deal["position_id"]:
            by_position[int(deal["position_id"])].append(deal)
    open_ids = {int(position["identifier"]) for position in open_positions}
    rows = []
    for position_id, group in sorted(by_position.items()):
        group.sort(key=lambda row: (row["time_utc"], row["ticket"]))
        entries = [row for row in group if row["entry"] in {0, 2}]
        exits = [row for row in group if row["entry"] in {1, 2, 3}]
        rows.append(
            {
                "position_id": position_id,
                "status": "open" if position_id in open_ids else "closed_or_flat",
                "symbols": sorted({row["symbol"] for row in group}),
                "magics": sorted({row["magic"] for row in group}),
                "surfaces": sorted({row["surface"] for row in group}),
                "comments": sorted({row["comment"] for row in group}),
                "entry_deal_count": len(entries),
                "exit_deal_count": len(exits),
                "deal_count": len(group),
                "entry_time_utc": entries[0]["time_utc"] if entries else None,
                "exit_time_utc": exits[-1]["time_utc"] if exits else None,
                "cash_delta": sum(row["cash_delta"] for row in group),
                "profit": sum(row["profit"] for row in group),
                "commission": sum(row["commission"] for row in group),
                "swap": sum(row["swap"] for row in group),
                "fee": sum(row["fee"] for row in group),
                "deal_tickets": [row["ticket"] for row in group],
                "order_tickets": sorted({row["order"] for row in group}),
            }
        )
    return rows


def surface_rollups(deals: Iterable[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for surface in sorted({row["surface"] for row in deals}):
        rows = [row for row in deals if row["surface"] == surface]
        result[surface] = {
            "deal_count": len(rows),
            "position_count": len({row["position_id"] for row in rows if row["position_id"]}),
            "trading_cash_delta": sum(row["trading_cash_delta"] for row in rows),
            "profit": sum(row["profit"] for row in rows),
            "commission": sum(row["commission"] for row in rows),
            "swap": sum(row["swap"] for row in rows),
            "fee": sum(row["fee"] for row in rows),
            "symbols": dict(Counter(row["symbol"] for row in rows)),
        }
    return result


def capture_account(spec: dict[str, Any], mt5: Any, now: datetime) -> dict[str, Any]:
    profile_path = REPO_ROOT / "config" / "profiles" / f"{spec['profile']}.yaml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    mt5_cfg = profile.get("mt5") or {}
    terminal_path = str(mt5_cfg.get("terminal_path") or "")
    result: dict[str, Any] = {
        "label": spec["label"],
        "profile": spec["profile"],
        "profile_path": str(profile_path.relative_to(REPO_ROOT)),
        "terminal_path": terminal_path,
        "initialize_ok": False,
    }
    if not mt5.initialize(path=terminal_path, portable=bool(mt5_cfg.get("portable", True))):
        result["last_error"] = mt5.last_error()
        return result
    result["initialize_ok"] = True
    try:
        account = mt5.account_info()
        terminal = mt5.terminal_info()
        if account is None or terminal is None:
            result["last_error"] = mt5.last_error()
            return result
        server_rule = resolve_rule(spec["server_rule"])
        window_start = reset_window_start_utc(
            now,
            firm_rule=spec["firm_reset_rule"],
            server_rule=server_rule,
        )
        reset_date = (
            window_start
            + timedelta(hours=reset_offset_hours(window_start, spec["firm_reset_rule"], server_rule))
        ).date().isoformat()
        query_from = now - timedelta(hours=40)
        query_to = now + timedelta(hours=16)
        raw_deals = mt5.history_deals_get(query_from, query_to)
        raw_history_orders = mt5.history_orders_get(query_from, query_to)
        if raw_deals is None or raw_history_orders is None:
            result["history_read_status"] = "failed"
            result["last_error"] = mt5.last_error()
            return result
        deals = [
            compact_deal(row, server_rule)
            for row in raw_deals
            if window_start <= broker_epoch_to_utc(row.time, server_rule) <= now
        ]
        history_orders = []
        for row in raw_history_orders:
            setup = broker_epoch_to_utc(row.time_setup, server_rule)
            done = broker_epoch_to_utc(row.time_done, server_rule) if int(row.time_done or 0) > 0 else None
            if (window_start <= setup <= now) or (done is not None and window_start <= done <= now):
                history_orders.append(compact_history_order(row, server_rule))
        raw_positions = list(mt5.positions_get() or ())
        raw_pending = list(mt5.orders_get() or ())
        account_row = compact_account(account)
        positions = [
            compact_position(row, mt5, account_row["equity"], server_rule)
            for row in raw_positions
        ]
        pending = [
            compact_pending_order(row, mt5, account_row["equity"], server_rule)
            for row in raw_pending
        ]
        trade_source_rows = [row for row in raw_deals if int(row.type) in TRADE_DEAL_TYPES and window_start <= broker_epoch_to_utc(row.time, server_rule) <= now]
        nontrade_source_rows = [row for row in raw_deals if int(row.type) not in TRADE_DEAL_TYPES and window_start <= broker_epoch_to_utc(row.time, server_rule) <= now]
        trading_cash = trade_deals_cash_delta(trade_source_rows)
        nontrading_cash = sum(raw_cash_delta(row) for row in nontrade_source_rows)
        all_cash = trading_cash + nontrading_cash
        opening_balance_before_all_cash = account_row["balance"] - all_cash
        reconstructed_opening_balance = account_row["balance"] - trading_cash
        anchor = load_day_anchor(REPO_ROOT / spec["day_anchor"], reset_date)
        if anchor.get("firm_daily_reference") is not None:
            daily_reference = finite(anchor["firm_daily_reference"])
            daily_reference_status = anchor.get("source_status")
        else:
            daily_reference = reconstructed_opening_balance
            daily_reference_status = "reconstructed_balance_only_day_start_equity_unavailable"
        open_risk_cash = sum(
            finite(row["stop_risk"].get("cash_risk"))
            for row in positions
            if row["stop_risk"].get("cash_risk") is not None
        )
        pending_risk_cash = sum(
            finite(row["stop_risk"].get("cash_risk"))
            for row in pending
            if row["stop_risk"].get("cash_risk") is not None
        )
        result.update(
            {
                "history_read_status": "complete",
                "identity": identity_match(profile, account, terminal),
                "terminal": compact_terminal(terminal),
                "account": account_row,
                "reset_window": {
                    "start_utc": iso(window_start),
                    "end_utc": iso(now),
                    "reset_date": reset_date,
                    "firm_reset_rule": spec["firm_reset_rule"] or "server_midnight",
                    "server_clock_rule": spec["server_rule"],
                    "server_offset_hours_at_capture": offset_seconds_at_utc(now, server_rule) / 3600.0,
                    "query_from_utc_argument": iso(query_from),
                    "query_to_utc_argument": iso(query_to),
                    "query_contract": "broker_wall_clock_overfetch_then_exact_converted_utc_filter",
                },
                "performance": {
                    "opening_balance_before_all_broker_cash": opening_balance_before_all_cash,
                    "reconstructed_opening_balance_after_nontrading_adjustments": reconstructed_opening_balance,
                    "trading_cash_delta": trading_cash,
                    "nontrading_cash_delta": nontrading_cash,
                    "all_broker_cash_delta": all_cash,
                    "current_balance": account_row["balance"],
                    "current_equity": account_row["equity"],
                    "floating_pnl": account_row["floating_pnl"],
                    "firm_daily_reference": daily_reference,
                    "firm_daily_reference_status": daily_reference_status,
                    "firm_daily_equity_delta": account_row["equity"] - daily_reference,
                    "firm_daily_equity_pct": (
                        (account_row["equity"] - daily_reference) / daily_reference * 100.0
                        if daily_reference
                        else None
                    ),
                    "day_anchor": anchor,
                },
                "risk": {
                    "open_position_count": len(positions),
                    "pending_order_count": len(pending),
                    "open_stop_risk_cash": open_risk_cash,
                    "open_stop_risk_equity_pct": open_risk_cash / account_row["equity"] * 100.0
                    if account_row["equity"]
                    else None,
                    "pending_stop_risk_cash": pending_risk_cash,
                    "positions_missing_stop_count": sum(
                        row["stop_risk"]["status"] == "missing_or_zero_stop" for row in positions
                    ),
                    "pending_missing_stop_count": sum(
                        row["stop_risk"]["status"] == "missing_or_zero_stop" for row in pending
                    ),
                },
                "denominators": {
                    "deal_count": len(deals),
                    "trading_deal_count": len(trade_source_rows),
                    "nontrading_deal_count": len(nontrade_source_rows),
                    "history_order_count": len(history_orders),
                    "position_group_count": len({row["position_id"] for row in deals if row["position_id"]}),
                    "current_position_count": len(positions),
                    "current_pending_order_count": len(pending),
                },
                "surface_rollups": surface_rollups(deals),
                "position_groups": position_groups(deals, positions),
                "deals": deals,
                "history_orders": history_orders,
                "positions": positions,
                "pending_orders": pending,
                "conservation": {
                    "balance_identity_residual": account_row["balance"]
                    - (opening_balance_before_all_cash + all_cash),
                    "trading_cash_row_sum_residual": trading_cash
                    - sum(row["trading_cash_delta"] for row in deals),
                    "position_group_cash_residual": trading_cash
                    - sum(row["cash_delta"] for row in position_groups(deals, positions)),
                    "deal_surface_count_residual": len(deals)
                    - sum(row["deal_count"] for row in surface_rollups(deals).values()),
                },
            }
        )
        result["status"] = "passed" if result["identity"]["all_match"] and all(
            abs(float(value)) < 1e-6 for value in result["conservation"].values()
        ) else "issues_detected"
        return result
    finally:
        mt5.shutdown()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        import MetaTrader5 as mt5  # type: ignore
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "failed", "error": f"MetaTrader5_import:{exc!r}"}), file=sys.stderr)
        return 2

    captured_at = utc_now()
    accounts = {spec["label"]: capture_account(spec, mt5, captured_at) for spec in ACCOUNTS}
    payload = {
        "schema_version": "gtos_live_broker_day_truth_v1",
        "captured_at_utc": iso(captured_at),
        "evidence_class": "broker_real_read_only_account_deal_order_position_truth",
        "read_only_contract": {
            "calls": [
                "MetaTrader5.initialize",
                "MetaTrader5.account_info",
                "MetaTrader5.terminal_info",
                "MetaTrader5.history_deals_get",
                "MetaTrader5.history_orders_get",
                "MetaTrader5.positions_get",
                "MetaTrader5.orders_get",
                "MetaTrader5.order_calc_profit",
                "MetaTrader5.shutdown",
            ],
            "forbidden_calls_made": [],
            "symbol_select_called": False,
            "broker_mutation": "none",
        },
        "accounts": accounts,
        "status": "passed" if all(row.get("status") == "passed" for row in accounts.values()) else "issues_detected",
    }
    write_json_atomic(args.output.resolve(), payload)
    print(
        json.dumps(
            {
                "status": payload["status"],
                "captured_at_utc": payload["captured_at_utc"],
                "accounts": {
                    label: {
                        "status": row.get("status"),
                        "balance": (row.get("account") or {}).get("balance"),
                        "equity": (row.get("account") or {}).get("equity"),
                        "trading_cash_delta": (row.get("performance") or {}).get("trading_cash_delta"),
                        "firm_daily_equity_delta": (row.get("performance") or {}).get("firm_daily_equity_delta"),
                        "positions": (row.get("risk") or {}).get("open_position_count"),
                        "orders": (row.get("risk") or {}).get("pending_order_count"),
                    }
                    for label, row in accounts.items()
                },
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
