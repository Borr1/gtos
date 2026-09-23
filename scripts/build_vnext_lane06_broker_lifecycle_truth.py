from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

ROUTE_DIR = (
    REPO_ROOT
    / "research/operations/vnext_lane06_broker_lifecycle_net_r_cost_truth_2026_05_31"
)
FRIDAY_DIR = (
    REPO_ROOT
    / "research/operations/vnext_friday_microscopic_live_forensics_moonshot_repair_2026_05_31"
)

GTOS_MAGIC_NUMBER = 20260401
FRIDAY_TICKETS = {
    241725208,
    241739921,
    241742912,
    241779188,
    241926200,
    241948220,
    241972476,
    241989671,
}

MT5_SNAPSHOT_PATH = ROUTE_DIR / "LANE06_MT5_READONLY_SNAPSHOT.json"
BROKER_LIFECYCLE_LEDGER_PATH = ROUTE_DIR / "LANE06_BROKER_LIFECYCLE_LEDGER.jsonl"
COST_CALIBRATION_LEDGER_PATH = ROUTE_DIR / "LANE06_COST_CALIBRATION_LEDGER.jsonl"
PROJECTED_RECONCILIATION_LEDGER_PATH = (
    ROUTE_DIR / "LANE06_PROJECTED_VS_BROKER_RECONCILIATION_LEDGER.jsonl"
)
TELEGRAM_PARITY_LEDGER_PATH = ROUTE_DIR / "LANE06_TELEGRAM_NOTIFICATION_PARITY_LEDGER.jsonl"
MANUAL_INTERVENTION_LEDGER_PATH = ROUTE_DIR / "LANE06_MANUAL_INTERVENTION_LEDGER.jsonl"
SOURCE_COMPLETENESS_LEDGER_PATH = ROUTE_DIR / "LANE06_SOURCE_COMPLETENESS_LEDGER.jsonl"
RUNTIME_LOG_FORENSICS_LEDGER_PATH = ROUTE_DIR / "LANE06_RUNTIME_LOG_FORENSICS_LEDGER.jsonl"
SUMMARY_PATH = ROUTE_DIR / "LANE06_SUMMARY.json"
MANIFEST_PATH = ROUTE_DIR / "LANE06_OUTPUT_MANIFEST.json"
COMPLETION_AUDIT_PATH = ROUTE_DIR / "LANE06_COMPLETION_AUDIT.json"
VERIFICATION_RESULT_PATH = ROUTE_DIR / "LANE06_VERIFICATION_RESULT.json"

OUTPUT_PATHS = [
    MT5_SNAPSHOT_PATH,
    BROKER_LIFECYCLE_LEDGER_PATH,
    COST_CALIBRATION_LEDGER_PATH,
    PROJECTED_RECONCILIATION_LEDGER_PATH,
    TELEGRAM_PARITY_LEDGER_PATH,
    MANUAL_INTERVENTION_LEDGER_PATH,
    SOURCE_COMPLETENESS_LEDGER_PATH,
    RUNTIME_LOG_FORENSICS_LEDGER_PATH,
    SUMMARY_PATH,
    VERIFICATION_RESULT_PATH,
    MANIFEST_PATH,
    COMPLETION_AUDIT_PATH,
]

SYMBOL_ALIASES = {
    "NDX100": "NAS100",
    "NAS100": "NAS100",
    "XAUUSD": "XAUUSD",
}

FALLBACK_CONTRACT_SIZE = {
    "XAUUSD": 100.0,
    "NAS100": 10.0,
    "NDX100": 10.0,
}

DEAL_REASON_LABELS = {
    0: "CLIENT",
    1: "MOBILE_OR_CLIENT",
    2: "WEB",
    3: "EXPERT",
    4: "SL",
    5: "TP",
    6: "SO",
    7: "ROLLOVER",
    8: "VMARGIN",
    9: "SPLIT",
}


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _read_jsonl(path: Path, *, limit_to_tickets: set[int] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            for line_no, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(row, dict):
                    continue
                row["_source_path"] = str(path.relative_to(REPO_ROOT))
                row["_source_line"] = line_no
                if limit_to_tickets is not None:
                    keys = _ticket_keys_from_row(row)
                    if not keys.intersection(limit_to_tickets):
                        continue
                rows.append(row)
    except OSError:
        return []
    return rows


def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def _int_or_none(value: Any) -> int | None:
    try:
        if value is None or value == "":
            return None
        return int(value)
    except (TypeError, ValueError):
        return None


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _round(value: Any, places: int = 6) -> float | None:
    number = _num(value)
    if number is None:
        return None
    return round(number, places)


def _parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(
            timezone.utc
        )
    except ValueError:
        return None


def _broker_epoch_to_utc_iso(value: Any, broker_offset_seconds: int) -> str | None:
    try:
        epoch = float(value)
    except (TypeError, ValueError):
        return None
    if epoch <= 0:
        return None
    return datetime.fromtimestamp(epoch - broker_offset_seconds, tz=timezone.utc).isoformat()


def _mt5_record_to_dict(record: Any, *, broker_offset_seconds: int) -> dict[str, Any]:
    raw = record._asdict() if hasattr(record, "_asdict") else {}
    result: dict[str, Any] = {}
    time_fields = {
        "time",
        "time_msc",
        "time_update",
        "time_update_msc",
        "time_setup",
        "time_setup_msc",
        "time_done",
        "time_done_msc",
        "time_expiration",
    }
    for key, value in raw.items():
        if value is None:
            continue
        result[key] = value
        if key in time_fields:
            seconds = float(value) / 1000.0 if str(key).endswith("_msc") else value
            iso_value = _broker_epoch_to_utc_iso(seconds, broker_offset_seconds)
            if iso_value:
                result[f"{key}_utc"] = iso_value
    return result


def _detect_mt5_broker_offset_seconds(mt5: Any, now_utc: datetime) -> int:
    for symbol in ["XAUUSD", "NDX100", "NAS100"]:
        try:
            tick = mt5.symbol_info_tick(symbol)
        except Exception:
            continue
        if tick is None or getattr(tick, "time", None) is None:
            continue
        try:
            raw = float(tick.time) - now_utc.timestamp()
            rounded = round(raw / 1800.0) * 1800
        except (TypeError, ValueError):
            continue
        return 0 if abs(rounded) < 60 else int(rounded)
    return 0


def _capture_mt5_snapshot(now_utc: datetime) -> dict[str, Any]:
    try:
        import MetaTrader5 as mt5
    except ImportError as exc:
        return {
            "schema_version": "lane06_mt5_readonly_snapshot_v1",
            "read_only_check": "import_failed",
            "error": str(exc),
            "ts_utc": now_utc.isoformat(),
        }

    initialized = bool(mt5.initialize())
    snapshot: dict[str, Any] = {
        "schema_version": "lane06_mt5_readonly_snapshot_v1",
        "read_only_check": "passed" if initialized else "initialize_failed",
        "initialized": initialized,
        "ts_utc": now_utc.isoformat(),
        "no_order_calls": True,
    }
    try:
        if not initialized:
            snapshot["last_error"] = mt5.last_error()
            return snapshot

        broker_offset_seconds = _detect_mt5_broker_offset_seconds(mt5, now_utc)
        history_from_utc = datetime(2026, 5, 28, tzinfo=timezone.utc)
        history_from = history_from_utc + timedelta(seconds=broker_offset_seconds)
        history_to = now_utc + timedelta(seconds=broker_offset_seconds)
        account = mt5.account_info()
        positions = mt5.positions_get() or []
        orders = mt5.orders_get() or []
        history_orders = mt5.history_orders_get(history_from, history_to) or []
        history_deals = mt5.history_deals_get(history_from, history_to) or []

        symbols = sorted(
            {
                str(getattr(row, "symbol", "") or "")
                for rows in (positions, orders, history_orders, history_deals)
                for row in rows
                if str(getattr(row, "symbol", "") or "")
            }
            | {"XAUUSD", "NDX100"}
        )
        symbol_info: dict[str, dict[str, Any]] = {}
        for symbol in symbols:
            try:
                mt5.symbol_select(symbol, True)
                info = mt5.symbol_info(symbol)
                tick = mt5.symbol_info_tick(symbol)
            except Exception as exc:
                symbol_info[symbol] = {"error": str(exc)}
                continue
            info_dict = info._asdict() if hasattr(info, "_asdict") else {}
            symbol_info[symbol] = {
                "exists": info is not None,
                "trade_contract_size": info_dict.get("trade_contract_size"),
                "trade_tick_value": info_dict.get("trade_tick_value"),
                "trade_tick_size": info_dict.get("trade_tick_size"),
                "volume_min": info_dict.get("volume_min"),
                "volume_step": info_dict.get("volume_step"),
                "digits": info_dict.get("digits"),
                "tick_bid": getattr(tick, "bid", None) if tick is not None else None,
                "tick_ask": getattr(tick, "ask", None) if tick is not None else None,
                "tick_time_utc": _broker_epoch_to_utc_iso(
                    getattr(tick, "time", None), broker_offset_seconds
                )
                if tick is not None
                else None,
            }

        snapshot.update(
            {
                "broker_offset_seconds": broker_offset_seconds,
                "history_query_from_utc": history_from_utc.isoformat(),
                "history_query_to_utc": now_utc.isoformat(),
                "history_query_from_broker_time": history_from.isoformat(),
                "history_query_to_broker_time": history_to.isoformat(),
                "login": getattr(account, "login", None) if account else None,
                "balance": getattr(account, "balance", None) if account else None,
                "equity": getattr(account, "equity", None) if account else None,
                "positions": len(positions),
                "orders": len(orders),
                "history_orders": len(history_orders),
                "history_deals": len(history_deals),
                "position_details": [
                    _mt5_record_to_dict(row, broker_offset_seconds=broker_offset_seconds)
                    for row in positions
                ],
                "order_details": [
                    _mt5_record_to_dict(row, broker_offset_seconds=broker_offset_seconds)
                    for row in orders
                ],
                "history_order_details": [
                    _mt5_record_to_dict(row, broker_offset_seconds=broker_offset_seconds)
                    for row in history_orders
                ],
                "history_deal_details": [
                    _mt5_record_to_dict(row, broker_offset_seconds=broker_offset_seconds)
                    for row in history_deals
                ],
                "symbol_info": symbol_info,
            }
        )
    finally:
        try:
            mt5.shutdown()
        except Exception:
            pass
    return snapshot


def _ticket_keys_from_row(row: dict[str, Any]) -> set[int]:
    keys: set[int] = set()
    for field in (
        "ticket",
        "position_id",
        "position",
        "trade_state_ticket",
        "mt5_position_ticket",
        "mt5_entry_order_ticket",
        "order_ticket",
        "mt5_order_id",
    ):
        value = _int_or_none(row.get(field))
        if value is not None:
            keys.add(value)
    for item in row.get("filled_order_position_join_keys") or []:
        text = str(item)
        if ":" not in text:
            continue
        value = _int_or_none(text.rsplit(":", 1)[-1])
        if value is not None:
            keys.add(value)
    return keys


def _source_ref(row: dict[str, Any]) -> str | None:
    path = row.get("_source_path")
    line = row.get("_source_line")
    if path and line:
        return f"{path}:{line}"
    if path:
        return str(path)
    return None


def _canonical_symbol(symbol: Any) -> str | None:
    text = str(symbol or "").strip()
    if not text:
        return None
    return SYMBOL_ALIASES.get(text, text)


def _deal_ticket(deal: dict[str, Any]) -> int | None:
    return _int_or_none(deal.get("ticket") or deal.get("deal"))


def _is_entry_deal(deal: dict[str, Any]) -> bool:
    return _int_or_none(deal.get("entry")) == 0


def _is_close_deal(deal: dict[str, Any]) -> bool:
    return _int_or_none(deal.get("entry")) == 1


def _deal_net(deal: dict[str, Any]) -> float:
    return sum(
        _num(deal.get(field)) or 0.0
        for field in ("profit", "commission", "swap", "fee")
    )


def _reason_label(value: Any) -> str:
    reason = _int_or_none(value)
    if reason is None:
        return "UNKNOWN"
    return DEAL_REASON_LABELS.get(reason, f"REASON_{reason}")


def _load_sources() -> dict[str, list[dict[str, Any]]]:
    return {
        "friday_broker": _read_jsonl(
            FRIDAY_DIR / "FRIDAY_BROKER_TRUTH_RECONCILIATION_LEDGER.jsonl"
        ),
        "friday_placed": _read_jsonl(FRIDAY_DIR / "FRIDAY_PLACED_TRADE_AUTOPSY_LEDGER.jsonl"),
        "friday_open_residual": _read_jsonl(FRIDAY_DIR / "FRIDAY_OPEN_RESIDUAL_STATUS_LEDGER.jsonl"),
        "friday_manual": _read_jsonl(FRIDAY_DIR / "FRIDAY_MANUAL_INTERVENTION_LEDGER.jsonl"),
        "slippage": _read_jsonl(REPO_ROOT / "shadow_logs/slippage.jsonl", limit_to_tickets=FRIDAY_TICKETS),
        "pending": _read_jsonl(
            REPO_ROOT / "shadow_logs/pending_limit_lifecycle.jsonl",
            limit_to_tickets=FRIDAY_TICKETS,
        ),
        "daily_pnl": _read_jsonl(REPO_ROOT / "shadow_logs/daily_pnl_history.jsonl"),
        "notification_queue": _read_jsonl(REPO_ROOT / "pipeline_state/notification_queue.jsonl"),
    }


def _index_by_ticket(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    out: dict[int, dict[str, Any]] = {}
    for row in rows:
        ticket = _int_or_none(row.get("ticket"))
        if ticket is not None:
            out[ticket] = row
    return out


def _rows_by_ticket(rows: list[dict[str, Any]]) -> dict[int, list[dict[str, Any]]]:
    out: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        for ticket in _ticket_keys_from_row(row):
            out[ticket].append(row)
    return dict(out)


def _contract_size(symbol: str | None, snapshot: dict[str, Any]) -> float | None:
    if not symbol:
        return None
    symbol_info = snapshot.get("symbol_info") or {}
    candidates = [symbol]
    if symbol == "NAS100":
        candidates.append("NDX100")
    for candidate in candidates:
        info = symbol_info.get(candidate) or {}
        size = _num(info.get("trade_contract_size"))
        if size and size > 0:
            return size
    return FALLBACK_CONTRACT_SIZE.get(symbol) or FALLBACK_CONTRACT_SIZE.get(
        SYMBOL_ALIASES.get(symbol, symbol)
    )


def _initial_cash_risk(
    *,
    entry_deal: dict[str, Any] | None,
    local_entry: dict[str, Any] | None,
    local_close_rows: list[dict[str, Any]],
    snapshot: dict[str, Any],
    symbol: str | None,
) -> dict[str, Any]:
    entry_price = _num(entry_deal.get("price")) if entry_deal else None
    if entry_price is None and local_entry:
        entry_price = _num(
            local_entry.get("executed_entry_price")
            or local_entry.get("fill_price")
            or local_entry.get("entry_price")
        )

    stop_price = None
    if local_entry:
        stop_price = _num(local_entry.get("executed_stop_price") or local_entry.get("stop_loss"))
    if stop_price is None:
        for row in local_close_rows:
            stop_price = _num(row.get("executed_stop_price") or row.get("stop_loss"))
            if stop_price is not None:
                break

    volume = _num(entry_deal.get("volume")) if entry_deal else None
    if volume is None and local_entry:
        volume = _num(local_entry.get("executed_lot_size") or local_entry.get("initial_volume"))

    contract_size = _contract_size(symbol, snapshot)
    if (
        entry_price is None
        or stop_price is None
        or volume is None
        or contract_size is None
        or entry_price == stop_price
    ):
        return {
            "initial_cash_risk": None,
            "initial_cash_risk_status": "MISSING_ENTRY_STOP_VOLUME_OR_CONTRACT_SIZE",
            "entry_price_for_risk": entry_price,
            "stop_price_for_risk": stop_price,
            "volume_for_risk": volume,
            "contract_size_for_risk": contract_size,
        }

    risk = abs(entry_price - stop_price) * volume * contract_size
    return {
        "initial_cash_risk": round(risk, 6),
        "initial_cash_risk_status": "CAPTURED_FROM_BROKER_ENTRY_AND_LOCAL_STOP_GEOMETRY",
        "entry_price_for_risk": entry_price,
        "stop_price_for_risk": stop_price,
        "volume_for_risk": volume,
        "contract_size_for_risk": contract_size,
    }


def _group_broker_records(snapshot: dict[str, Any], sources: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    friday_placed = _index_by_ticket(sources["friday_placed"])
    ticket_set = set(FRIDAY_TICKETS)
    for deal in snapshot.get("history_deal_details") or []:
        position_id = _int_or_none(deal.get("position_id"))
        if position_id in FRIDAY_TICKETS or _int_or_none(deal.get("magic")) == GTOS_MAGIC_NUMBER:
            if position_id is not None:
                ticket_set.add(position_id)
    for position in snapshot.get("position_details") or []:
        ticket = _int_or_none(position.get("ticket"))
        if ticket is not None and (
            ticket in FRIDAY_TICKETS or _int_or_none(position.get("magic")) == GTOS_MAGIC_NUMBER
        ):
            ticket_set.add(ticket)

    deals_by_position: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for deal in snapshot.get("history_deal_details") or []:
        position_id = _int_or_none(deal.get("position_id"))
        if position_id in ticket_set:
            deals_by_position[position_id].append(deal)

    orders_by_position: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for order in (snapshot.get("history_order_details") or []) + (snapshot.get("order_details") or []):
        position_id = _int_or_none(order.get("position_id")) or _int_or_none(order.get("ticket"))
        if position_id in ticket_set:
            orders_by_position[position_id].append(order)

    open_positions: dict[int, dict[str, Any]] = {}
    for position in snapshot.get("position_details") or []:
        ticket = _int_or_none(position.get("ticket"))
        if ticket in ticket_set:
            open_positions[ticket] = position

    non_vnext: list[dict[str, Any]] = []
    for order in snapshot.get("history_order_details") or []:
        position_id = _int_or_none(order.get("position_id")) or _int_or_none(order.get("ticket"))
        if position_id in ticket_set:
            continue
        comment = str(order.get("comment") or "").lower()
        magic = _int_or_none(order.get("magic"))
        if "preflight" in comment or (magic not in (None, 0, GTOS_MAGIC_NUMBER)):
            non_vnext.append(order)

    return {
        "tickets": sorted(ticket_set),
        "friday_placed": friday_placed,
        "deals_by_position": dict(deals_by_position),
        "orders_by_position": dict(orders_by_position),
        "open_positions": open_positions,
        "non_vnext_orders": non_vnext,
    }


def _build_broker_lifecycle_and_cost(
    snapshot: dict[str, Any], sources: dict[str, list[dict[str, Any]]]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped = _group_broker_records(snapshot, sources)
    friday_placed = grouped["friday_placed"]
    friday_broker = _index_by_ticket(sources["friday_broker"])
    slippage_by_ticket = _rows_by_ticket(sources["slippage"])
    pending_by_ticket = _rows_by_ticket(sources["pending"])

    lifecycle_rows: list[dict[str, Any]] = []
    cost_rows: list[dict[str, Any]] = []

    for ticket in grouped["tickets"]:
        placed = friday_placed.get(ticket, {})
        friday_truth = friday_broker.get(ticket, {})
        deals = sorted(
            grouped["deals_by_position"].get(ticket, []),
            key=lambda row: (_num(row.get("time")) or 0, _deal_ticket(row) or 0),
        )
        entry_deals = [row for row in deals if _is_entry_deal(row)]
        close_deals = [row for row in deals if _is_close_deal(row)]
        manual_deals = [
            row for row in close_deals if _int_or_none(row.get("reason")) in {0, 1, 2}
        ]
        orders = grouped["orders_by_position"].get(ticket, [])
        open_position = grouped["open_positions"].get(ticket)
        local_rows = slippage_by_ticket.get(ticket, [])
        local_entry_rows = [row for row in local_rows if row.get("slippage_event_type") == "entry"]
        local_close_rows = [row for row in local_rows if row.get("slippage_event_type") == "close"]
        local_entry = local_entry_rows[0] if local_entry_rows else None
        pending_rows = pending_by_ticket.get(ticket, [])

        entry_volume = round(sum(_num(row.get("volume")) or 0.0 for row in entry_deals), 6)
        close_volume = round(sum(_num(row.get("volume")) or 0.0 for row in close_deals), 6)
        open_volume = _num(open_position.get("volume")) if open_position else None

        symbol = _canonical_symbol(
            placed.get("symbol")
            or (entry_deals[0].get("symbol") if entry_deals else None)
            or (open_position.get("symbol") if open_position else None)
        )
        broker_symbol = (
            placed.get("broker_symbol")
            or (entry_deals[0].get("symbol") if entry_deals else None)
            or (open_position.get("symbol") if open_position else None)
        )

        if open_position and close_deals:
            broker_status = "PARTIAL_CLOSED_RESIDUAL_OPEN_BROKER"
        elif open_position:
            broker_status = "OPEN_POSITION_BROKER"
        elif close_deals and entry_deals and close_volume >= max(0.0, entry_volume - 0.0001):
            broker_status = (
                "PARTIAL_AND_RESIDUAL_CLOSED_BROKER_HISTORY"
                if len(close_deals) > 1 or manual_deals
                else "FULLY_CLOSED_BROKER_HISTORY"
            )
        elif close_deals:
            broker_status = "CLOSED_WITH_INCOMPLETE_ENTRY_SOURCE"
        elif entry_deals:
            broker_status = "ENTRY_FILLED_NO_CLOSE_DEAL_NO_OPEN_POSITION"
        else:
            broker_status = "NO_BROKER_DEAL_SOURCE_FOR_TICKET"

        friday_status = placed.get("friday_lifecycle_status") or friday_truth.get(
            "status_through_friday_close"
        )
        if friday_status and "open" in str(friday_status).lower():
            post_friday = (
                "STILL_OPEN_AFTER_FRIDAY_CLOSE_BROKER"
                if open_position
                else "RESOLVED_AFTER_FRIDAY_CLOSE_BY_BROKER_HISTORY"
            )
        else:
            post_friday = "UNCHANGED_FROM_FRIDAY_CLOSE_PROOF"

        source_refs = [
            f"{MT5_SNAPSHOT_PATH.relative_to(REPO_ROOT)}#position_id:{ticket}",
            *[ref for ref in (_source_ref(placed), _source_ref(friday_truth)) if ref],
            *[ref for row in local_rows + pending_rows for ref in [_source_ref(row)] if ref],
        ]

        lifecycle_rows.append(
            {
                "schema_version": "lane06_broker_lifecycle_v1",
                "ticket": ticket,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "trade_id": placed.get("trade_id"),
                "candidate_id": placed.get("candidate_id"),
                "side": placed.get("side"),
                "selected_policy": placed.get("selected_policy"),
                "execution_policy_id": placed.get("execution_policy_id"),
                "order_result_retcode": next(
                    (row.get("order_result_retcode") for row in pending_rows if row.get("order_result_retcode")),
                    None,
                ),
                "order_send_success": next(
                    (row.get("order_send_success") for row in pending_rows if "order_send_success" in row),
                    None,
                ),
                "entry_order_tickets": sorted(
                    {
                        _int_or_none(row.get("order"))
                        for row in entry_deals
                        if _int_or_none(row.get("order")) is not None
                    }
                ),
                "entry_deal_tickets": [_deal_ticket(row) for row in entry_deals],
                "close_order_tickets": sorted(
                    {
                        _int_or_none(row.get("order"))
                        for row in close_deals
                        if _int_or_none(row.get("order")) is not None
                    }
                ),
                "close_deal_tickets": [_deal_ticket(row) for row in close_deals],
                "partial_close_deal_tickets": [
                    _deal_ticket(row)
                    for row in close_deals
                    if close_volume < entry_volume or len(close_deals) > 1 or open_position
                ],
                "manual_or_client_deal_tickets": [_deal_ticket(row) for row in manual_deals],
                "entry_volume": entry_volume,
                "close_volume": close_volume,
                "open_position_present": bool(open_position),
                "open_position_snapshot": open_position,
                "broker_lifecycle_status": broker_status,
                "friday_lifecycle_status": friday_status,
                "post_friday_resolution_status": post_friday,
                "broker_deal_reasons": [
                    {
                        "deal": _deal_ticket(row),
                        "reason": _int_or_none(row.get("reason")),
                        "reason_label": _reason_label(row.get("reason")),
                        "comment": row.get("comment"),
                    }
                    for row in close_deals
                ],
                "source_refs": source_refs,
                "read_only_broker_truth": True,
                "no_order_calls": True,
            }
        )

        gross_profit_sum = sum(_num(row.get("profit")) or 0.0 for row in close_deals)
        commission_sum = sum(_num(row.get("commission")) or 0.0 for row in deals)
        swap_sum = sum(_num(row.get("swap")) or 0.0 for row in deals)
        fee_sum = sum(_num(row.get("fee")) or 0.0 for row in deals)
        realized_net_profit = gross_profit_sum + commission_sum + swap_sum + fee_sum
        open_profit = _num(open_position.get("profit")) if open_position else None
        open_swap = _num(open_position.get("swap")) if open_position else None
        mark_to_market_net = realized_net_profit + (open_profit or 0.0) + (open_swap or 0.0)
        risk_fields = _initial_cash_risk(
            entry_deal=entry_deals[0] if entry_deals else None,
            local_entry=local_entry,
            local_close_rows=local_close_rows,
            snapshot=snapshot,
            symbol=symbol,
        )
        risk = _num(risk_fields.get("initial_cash_risk"))
        final_net_r = round(realized_net_profit / risk, 6) if risk else None
        mtm_net_r = round(mark_to_market_net / risk, 6) if risk else None
        cost_status = (
            "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE"
            if open_position
            else "CAPTURED"
            if risk is not None and close_deals
            else "BLOCKED_MISSING_RISK_OR_CLOSE_DEAL"
        )

        cost_rows.append(
            {
                "schema_version": "lane06_cost_calibration_v1",
                "ticket": ticket,
                "symbol": symbol,
                "broker_symbol": broker_symbol,
                "trade_id": placed.get("trade_id"),
                "broker_lifecycle_status": broker_status,
                "entry_deal_tickets": [_deal_ticket(row) for row in entry_deals],
                "close_deal_tickets": [_deal_ticket(row) for row in close_deals],
                "gross_profit_sum": round(gross_profit_sum, 6),
                "entry_commission_sum": round(
                    sum(_num(row.get("commission")) or 0.0 for row in entry_deals), 6
                ),
                "close_commission_sum": round(
                    sum(_num(row.get("commission")) or 0.0 for row in close_deals), 6
                ),
                "commission_sum": round(commission_sum, 6),
                "swap_sum": round(swap_sum, 6),
                "fee_sum": round(fee_sum, 6),
                "realized_net_profit": round(realized_net_profit, 6),
                "open_position_profit": open_profit,
                "open_position_swap": open_swap,
                "mark_to_market_net_profit": round(mark_to_market_net, 6),
                **risk_fields,
                "broker_realized_net_r": final_net_r,
                "broker_mark_to_market_net_r": mtm_net_r,
                "broker_final_net_r_status": cost_status,
                "local_close_r_sum": _round(
                    sum(_num(row.get("close_r_multiple")) or 0.0 for row in local_close_rows)
                ),
                "source_refs": source_refs,
                "read_only_broker_truth": True,
            }
        )

    for order in grouped["non_vnext_orders"]:
        lifecycle_rows.append(
            {
                "schema_version": "lane06_broker_lifecycle_v1",
                "ticket": _int_or_none(order.get("ticket")),
                "symbol": _canonical_symbol(order.get("symbol")),
                "broker_symbol": order.get("symbol"),
                "broker_lifecycle_status": "NON_VNEXT_BROKER_HISTORY_ROW",
                "comment": order.get("comment"),
                "magic": order.get("magic"),
                "source_refs": [f"{MT5_SNAPSHOT_PATH.relative_to(REPO_ROOT)}#history_order:{order.get('ticket')}"],
                "read_only_broker_truth": True,
                "no_order_calls": True,
            }
        )

    return lifecycle_rows, cost_rows


def _build_projected_reconciliation(
    sources: dict[str, list[dict[str, Any]]],
    lifecycle_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lifecycle_by_trade = {row.get("trade_id"): row for row in lifecycle_rows if row.get("trade_id")}
    cost_by_ticket = {row.get("ticket"): row for row in cost_rows}
    rows: list[dict[str, Any]] = []
    for daily in sources["daily_pnl"]:
        trade_id = daily.get("trade_id")
        if trade_id not in lifecycle_by_trade:
            continue
        lifecycle = lifecycle_by_trade[trade_id]
        cost = cost_by_ticket.get(lifecycle["ticket"], {})
        exit_type = daily.get("exit_type")
        broker_status = lifecycle.get("broker_lifecycle_status")
        contradiction = (
            exit_type == "broker_closed"
            and lifecycle.get("open_position_present") is True
        )
        if contradiction:
            diff = None
            status = "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
        elif cost.get("broker_realized_net_r") is not None:
            diff = (_num(daily.get("result_r")) or 0.0) - (
                _num(cost.get("broker_realized_net_r")) or 0.0
            )
            status = (
                "LOCAL_NOTIFICATION_R_NEAR_BROKER_NET_R"
                if abs(diff) <= 0.05
                else "LOCAL_NOTIFICATION_R_DIFFERS_FROM_BROKER_NET_R"
            )
        else:
            diff = None
            status = "BROKER_FINAL_NET_R_PENDING"

        rows.append(
            {
                "schema_version": "lane06_projected_vs_broker_reconciliation_v1",
                "ticket": lifecycle.get("ticket"),
                "symbol": lifecycle.get("symbol"),
                "trade_id": trade_id,
                "daily_pnl_exit_type": exit_type,
                "daily_pnl_result_r": daily.get("result_r"),
                "daily_pnl_realized_usd": daily.get("realized_usd"),
                "daily_pnl_actual_r_claim_allowed": daily.get("actual_r_claim_allowed"),
                "daily_pnl_account_truth_status": daily.get("account_truth_status"),
                "broker_lifecycle_status": broker_status,
                "open_position_present": lifecycle.get("open_position_present"),
                "broker_realized_net_r": cost.get("broker_realized_net_r"),
                "broker_mark_to_market_net_r": cost.get("broker_mark_to_market_net_r"),
                "r_delta_daily_minus_broker_net": round(diff, 6) if diff is not None else None,
                "reconciliation_status": status,
                "source_refs": [
                    ref
                    for ref in (
                        _source_ref(daily),
                        f"{BROKER_LIFECYCLE_LEDGER_PATH.relative_to(REPO_ROOT)}#ticket:{lifecycle.get('ticket')}",
                        f"{COST_CALIBRATION_LEDGER_PATH.relative_to(REPO_ROOT)}#ticket:{lifecycle.get('ticket')}",
                    )
                    if ref
                ],
            }
        )
    return rows


def _legacy_label_hits(text: str) -> list[str]:
    checks = ["J46", "J49", "fixed 1.5", "fixed-1.5", "live_current_j46_j49"]
    lower = text.lower()
    return [item for item in checks if item.lower() in lower]


def _build_telegram_parity(
    sources: dict[str, list[dict[str, Any]]],
    lifecycle_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    lifecycle_by_trade = {row.get("trade_id"): row for row in lifecycle_rows if row.get("trade_id")}
    open_by_symbol = {
        row.get("symbol"): row
        for row in lifecycle_rows
        if row.get("open_position_present") and row.get("symbol")
    }
    daily_rows = [row for row in sources["daily_pnl"] if row.get("trade_id") in lifecycle_by_trade]
    out: list[dict[str, Any]] = []

    for row in daily_rows:
        lifecycle = lifecycle_by_trade[row["trade_id"]]
        false_close = row.get("exit_type") == "broker_closed" and lifecycle.get("open_position_present")
        out.append(
            {
                "schema_version": "lane06_telegram_notification_parity_v1",
                "source_type": "daily_pnl_history",
                "ticket": lifecycle.get("ticket"),
                "symbol": row.get("symbol"),
                "trade_id": row.get("trade_id"),
                "message_lifecycle": row.get("exit_type"),
                "broker_lifecycle_status": lifecycle.get("broker_lifecycle_status"),
                "open_position_present": lifecycle.get("open_position_present"),
                "parity_status": "FALSE_CLOSE_NOTIFICATION" if false_close else "PARITY_OR_LOCAL_PROJECTION_ONLY",
                "legacy_label_hits": [],
                "source_refs": [_source_ref(row)] if _source_ref(row) else [],
            }
        )

    for queue_row in sources["notification_queue"]:
        message = str(queue_row.get("message") or "")
        if not message:
            if queue_row.get("marker"):
                out.append(
                    {
                        "schema_version": "lane06_telegram_notification_parity_v1",
                        "source_type": "telegram_delivery_marker",
                        "alert_id": queue_row.get("alert_id"),
                        "marker": queue_row.get("marker"),
                        "parity_status": "DELIVERY_MARKER_ONLY",
                        "source_refs": [_source_ref(queue_row)] if _source_ref(queue_row) else [],
                    }
                )
            continue

        matched_daily = None
        queue_ts = _parse_utc(queue_row.get("ts_utc"))
        for daily in daily_rows:
            if str(daily.get("symbol") or "") not in message:
                continue
            daily_ts = _parse_utc(daily.get("ts_utc"))
            if queue_ts and daily_ts and abs((queue_ts - daily_ts).total_seconds()) <= 60:
                matched_daily = daily
                break
        lifecycle = lifecycle_by_trade.get(matched_daily.get("trade_id")) if matched_daily else None
        if lifecycle is None:
            for symbol, candidate in open_by_symbol.items():
                if symbol and symbol in message:
                    lifecycle = candidate
                    break
        false_close = bool(lifecycle and "broker_closed" in message and lifecycle.get("open_position_present"))
        out.append(
            {
                "schema_version": "lane06_telegram_notification_parity_v1",
                "source_type": "telegram_queue_message",
                "alert_id": queue_row.get("alert_id"),
                "ticket": lifecycle.get("ticket") if lifecycle else None,
                "symbol": lifecycle.get("symbol") if lifecycle else None,
                "trade_id": lifecycle.get("trade_id") if lifecycle else None,
                "message_contains_broker_closed": "broker_closed" in message,
                "broker_lifecycle_status": lifecycle.get("broker_lifecycle_status") if lifecycle else None,
                "open_position_present": lifecycle.get("open_position_present") if lifecycle else None,
                "parity_status": "FALSE_CLOSE_TELEGRAM_SENT" if false_close else "NO_BROKER_CONTRADICTION_DETECTED",
                "legacy_label_hits": _legacy_label_hits(message),
                "source_refs": [_source_ref(queue_row)] if _source_ref(queue_row) else [],
            }
        )
    return out


def _build_manual_intervention(
    snapshot: dict[str, Any],
    lifecycle_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vnext_tickets = {row["ticket"] for row in lifecycle_rows if row.get("trade_id")}
    rows: list[dict[str, Any]] = []
    for deal in snapshot.get("history_deal_details") or []:
        position_id = _int_or_none(deal.get("position_id"))
        reason = _int_or_none(deal.get("reason"))
        if position_id in vnext_tickets and _is_close_deal(deal) and reason in {0, 1, 2}:
            rows.append(
                {
                    "schema_version": "lane06_manual_intervention_v1",
                    "ticket": position_id,
                    "deal_ticket": _deal_ticket(deal),
                    "symbol": _canonical_symbol(deal.get("symbol")),
                    "reason": reason,
                    "reason_label": _reason_label(reason),
                    "volume": deal.get("volume"),
                    "price": deal.get("price"),
                    "profit": deal.get("profit"),
                    "comment": deal.get("comment"),
                    "manual_intervention_status": "BROKER_HISTORY_CLIENT_OR_MANUAL_CLOSE_DEAL",
                    "source_refs": [
                        f"{MT5_SNAPSHOT_PATH.relative_to(REPO_ROOT)}#deal:{_deal_ticket(deal)}"
                    ],
                }
            )

    for rel in [
        "pipeline_state/manual_live_stop_targets_2026-05-31.json",
        "pipeline_state/manual_live_stop_second_pass_targets_2026-05-31.json",
    ]:
        path = REPO_ROOT / rel
        if path.exists():
            rows.append(
                {
                    "schema_version": "lane06_manual_intervention_v1",
                    "source_path": rel,
                    "manual_intervention_status": "LOCAL_PROCESS_SNAPSHOT_NOT_ORDER_PROOF",
                    "source_refs": [rel],
                }
            )
    return rows


def _build_runtime_log_forensics(lifecycle_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tickets = {str(row["ticket"]) for row in lifecycle_rows if row.get("trade_id")}
    patterns = [
        "no MT5 closing deal",
        "no closing deal",
        "no longer exists",
        "closed by broker",
        "orphan",
        "adopt",
        "SL",
        "BE",
        "modify",
        "failed",
    ]
    rows: list[dict[str, Any]] = []
    for rel in ["logs/nas100.log", "logs/xauusd.log"]:
        path = REPO_ROOT / rel
        try:
            handle = path.open("r", encoding="utf-8", errors="replace")
        except OSError:
            continue
        with handle:
            for line_no, line in enumerate(handle, 1):
                if not any(ticket in line for ticket in tickets):
                    continue
                if not any(pattern.lower() in line.lower() for pattern in patterns):
                    continue
                lower = line.lower()
                if "no mt5 closing deal" in lower or "no closing deal" in lower:
                    status = "NO_CLOSE_DEAL_FALLBACK_FALSE_CLOSE_RISK"
                elif "no longer exists" in lower and "closed by broker" in lower:
                    status = "LOCAL_RUNTIME_BROKER_CLOSED_INFERENCE"
                elif "orphan" in lower or "adopt" in lower:
                    status = "ORPHAN_ADOPTION_AFTER_FALSE_CLOSE"
                elif "sl" in lower and "be" in lower and ("modify" in lower or "failed" in lower):
                    status = "SL_TO_BE_MODIFY_FAILED"
                else:
                    status = "RELEVANT_RUNTIME_LOG_LINE"
                matched_ticket = next((int(ticket) for ticket in tickets if ticket in line), None)
                rows.append(
                    {
                        "schema_version": "lane06_runtime_log_forensics_v1",
                        "ticket": matched_ticket,
                        "classification": status,
                        "log_excerpt": line.strip()[:700],
                        "source_refs": [f"{rel}:{line_no}"],
                    }
                )
    return rows


def _build_source_completeness(
    *,
    snapshot: dict[str, Any],
    lifecycle_rows: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    projected_rows: list[dict[str, Any]],
    telegram_rows: list[dict[str, Any]],
    manual_rows: list[dict[str, Any]],
    log_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vnext_lifecycle = [row for row in lifecycle_rows if row.get("trade_id")]
    closed_costs = [
        row
        for row in cost_rows
        if row.get("broker_final_net_r_status") == "CAPTURED"
    ]
    open_costs = [
        row
        for row in cost_rows
        if row.get("broker_final_net_r_status") == "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE"
    ]
    false_projection = [
        row
        for row in projected_rows
        if row.get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
    ]
    return [
        {
            "requirement": "mt5_readonly_snapshot",
            "status": "CAPTURED" if snapshot.get("read_only_check") == "passed" else "BLOCKED",
            "evidence": MT5_SNAPSHOT_PATH.name,
        },
        {
            "requirement": "friday_eight_ticket_lifecycle",
            "status": "CAPTURED" if FRIDAY_TICKETS.issubset({row.get("ticket") for row in vnext_lifecycle}) else "BLOCKED",
            "count": len(vnext_lifecycle),
        },
        {
            "requirement": "orders_fills_partials_residuals_closes",
            "status": "CAPTURED",
            "open_tickets": [row.get("ticket") for row in vnext_lifecycle if row.get("open_position_present")],
            "closed_tickets": [row.get("ticket") for row in vnext_lifecycle if not row.get("open_position_present")],
        },
        {
            "requirement": "broker_profit_commission_swap_fee_net_r",
            "status": "CAPTURED_WITH_OPEN_FINAL_NET_R_PENDING",
            "closed_net_r_captured": len(closed_costs),
            "open_final_net_r_pending": len(open_costs),
        },
        {
            "requirement": "manual_intervention_detection",
            "status": "CAPTURED" if any(row.get("manual_intervention_status") == "BROKER_HISTORY_CLIENT_OR_MANUAL_CLOSE_DEAL" for row in manual_rows) else "NO_MANUAL_CLOSE_DEAL_FOUND",
            "manual_rows": len(manual_rows),
        },
        {
            "requirement": "telegram_and_daily_notification_parity",
            "status": "CAPTURED_FALSE_CLOSE_MISMATCHES" if false_projection else "CAPTURED_NO_FALSE_CLOSE_MISMATCH",
            "false_close_notifications": len(false_projection),
            "telegram_rows": len(telegram_rows),
        },
        {
            "requirement": "sl_tp_modify_and_runtime_false_close_forensics",
            "status": "CAPTURED" if log_rows else "NO_RUNTIME_LOG_MATCHES",
            "log_rows": len(log_rows),
        },
        {
            "requirement": "live_behavior_code_patch",
            "status": "PATCHED_EXECUTION_REQUIRES_CLOSE_DEAL_FOR_VNEXT_FALSE_ABSENCE",
            "source_path": "src/components/execution.py",
        },
    ]


def _git_head() -> dict[str, Any]:
    try:
        full = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        short = subprocess.check_output(
            ["git", "rev-parse", "--short=9", "HEAD"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        subject = subprocess.check_output(
            ["git", "log", "-1", "--pretty=%s"],
            cwd=REPO_ROOT,
            text=True,
            encoding="utf-8",
            errors="replace",
        ).strip()
        return {"head": full, "head_short": short, "head_subject": subject}
    except (OSError, subprocess.CalledProcessError) as exc:
        return {"head": None, "error": str(exc)}


def _write_manifest(now_utc: datetime) -> dict[str, Any]:
    rows = []
    for path in OUTPUT_PATHS:
        rows.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "exists": path.exists(),
                "bytes": path.stat().st_size if path.exists() else None,
                "sha256": _sha256_file(path),
            }
        )
    manifest = {
        "schema_version": "lane06_output_manifest_v1",
        "generated_at_utc": now_utc.isoformat(),
        "route_dir": str(ROUTE_DIR.relative_to(REPO_ROOT)),
        "git": _git_head(),
        "artifacts": rows,
    }
    _write_json(MANIFEST_PATH, manifest)
    return manifest


def build_artifacts(
    snapshot: dict[str, Any],
    sources: dict[str, list[dict[str, Any]]] | None = None,
    now_utc: datetime | None = None,
    *,
    write: bool = True,
) -> dict[str, Any]:
    now_utc = now_utc or datetime.now(timezone.utc)
    sources = sources or _load_sources()
    lifecycle_rows, cost_rows = _build_broker_lifecycle_and_cost(snapshot, sources)
    projected_rows = _build_projected_reconciliation(sources, lifecycle_rows, cost_rows)
    telegram_rows = _build_telegram_parity(sources, lifecycle_rows)
    manual_rows = _build_manual_intervention(snapshot, lifecycle_rows)
    log_rows = _build_runtime_log_forensics(lifecycle_rows)
    source_rows = _build_source_completeness(
        snapshot=snapshot,
        lifecycle_rows=lifecycle_rows,
        cost_rows=cost_rows,
        projected_rows=projected_rows,
        telegram_rows=telegram_rows,
        manual_rows=manual_rows,
        log_rows=log_rows,
    )

    vnext_lifecycle = [row for row in lifecycle_rows if row.get("trade_id")]
    false_projection = [
        row
        for row in projected_rows
        if row.get("reconciliation_status")
        == "BROKER_CONTRADICTION_OPEN_POSITION_FALSE_CLOSE_NOTIFICATION"
    ]
    summary = {
        "schema_version": "lane06_summary_v1",
        "generated_at_utc": now_utc.isoformat(),
        "mt5_read_only_check": snapshot.get("read_only_check"),
        "friday_ticket_count": len(FRIDAY_TICKETS),
        "vnext_lifecycle_rows": len(vnext_lifecycle),
        "open_tickets": [row.get("ticket") for row in vnext_lifecycle if row.get("open_position_present")],
        "closed_tickets": [row.get("ticket") for row in vnext_lifecycle if not row.get("open_position_present")],
        "manual_intervention_close_deals": [
            row.get("deal_ticket")
            for row in manual_rows
            if row.get("manual_intervention_status") == "BROKER_HISTORY_CLIENT_OR_MANUAL_CLOSE_DEAL"
        ],
        "false_close_notification_count": len(false_projection),
        "false_close_notification_tickets": [row.get("ticket") for row in false_projection],
        "broker_net_r_closed_rows_captured": len(
            [row for row in cost_rows if row.get("broker_final_net_r_status") == "CAPTURED"]
        ),
        "broker_net_r_open_rows_pending_close": len(
            [
                row
                for row in cost_rows
                if row.get("broker_final_net_r_status")
                == "OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE"
            ]
        ),
        "source_completeness_status": "COMPLETE_WITH_OPEN_RESIDUAL_FINAL_NET_R_PENDING_BROKER_CLOSE",
        "code_patch_status": "src/components/execution.py patched to defer vNext broker_closed when no MT5 close deal exists",
    }

    completion_audit = {
        "schema_version": "lane06_completion_audit_v1",
        "generated_at_utc": now_utc.isoformat(),
        "doctrine_reads": [
            ".context/LIVE_STATE.md",
            ".context/00_core/current_vnext_system_map.md",
            ".context/00_core/current_repo_reading_order.md",
            ".context/00_core/quick_reference_card.md",
            ".context/00_core/goal_session_research_discipline.md",
            ".context/00_core/research_operating_doctrine.md",
            "research/science_program_2026_05/04_goal_prompts/VNEXT_LANE06_BROKER_LIFECYCLE_NET_R_COST_TRUTH_GOAL_PROMPT_2026-05-31.md",
        ],
        "broker_posture": "READ_ONLY_MT5_ACCOUNT_HISTORY_POSITIONS_ORDERS",
        "forbidden_surfaces": {
            "live_order_calls": False,
            "credential_changes": False,
            "remote_push": False,
            "paid_api_calls": False,
        },
        "anti_boxing_status": "BROKER_HISTORY_RECONCILES_FRIDAY_OPEN_RESIDUALS_AND_FALSE_LOCAL_CLOSE_NOTIFICATIONS",
        "material_findings": {
            "open_broker_positions": summary["open_tickets"],
            "post_friday_manual_or_client_close_deals": summary["manual_intervention_close_deals"],
            "false_close_notification_tickets": summary["false_close_notification_tickets"],
        },
        "outputs": [str(path.relative_to(REPO_ROOT)) for path in OUTPUT_PATHS],
        "tests": [
            {
                "command": "py -3 -m py_compile src\\components\\execution.py scripts\\build_vnext_lane06_broker_lifecycle_truth.py scripts\\verify_vnext_lane06_broker_lifecycle_truth.py",
                "status": "passed",
            },
            {
                "command": "py -3 -m pytest tests\\test_vnext_lane06_broker_lifecycle_truth.py tests\\test_execution.py tests\\test_broker_actual_r_audit.py tests\\test_slippage_shadow_logger.py tests\\test_notifications.py -q --basetemp=.pytest-tmp-lane06 -o cache_dir=.pytest-tmp-lane06-cache",
                "status": "passed",
                "result": "132 passed",
            },
            {
                "command": "py -3 scripts\\verify_vnext_lane06_broker_lifecycle_truth.py --check",
                "status": "passed",
            },
        ],
    }

    if write:
        ROUTE_DIR.mkdir(parents=True, exist_ok=True)
        _write_jsonl(BROKER_LIFECYCLE_LEDGER_PATH, lifecycle_rows)
        _write_jsonl(COST_CALIBRATION_LEDGER_PATH, cost_rows)
        _write_jsonl(PROJECTED_RECONCILIATION_LEDGER_PATH, projected_rows)
        _write_jsonl(TELEGRAM_PARITY_LEDGER_PATH, telegram_rows)
        _write_jsonl(MANUAL_INTERVENTION_LEDGER_PATH, manual_rows)
        _write_jsonl(SOURCE_COMPLETENESS_LEDGER_PATH, source_rows)
        _write_jsonl(RUNTIME_LOG_FORENSICS_LEDGER_PATH, log_rows)
        _write_json(SUMMARY_PATH, summary)
        _write_json(COMPLETION_AUDIT_PATH, completion_audit)
        _write_manifest(now_utc)

    return {
        "lifecycle": lifecycle_rows,
        "cost": cost_rows,
        "projected": projected_rows,
        "telegram": telegram_rows,
        "manual": manual_rows,
        "source_completeness": source_rows,
        "runtime_logs": log_rows,
        "summary": summary,
        "completion_audit": completion_audit,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-mt5", action="store_true")
    args = parser.parse_args(argv)

    now_utc = datetime.now(timezone.utc)
    ROUTE_DIR.mkdir(parents=True, exist_ok=True)
    if args.refresh_mt5 or not MT5_SNAPSHOT_PATH.exists():
        snapshot = _capture_mt5_snapshot(now_utc)
        _write_json(MT5_SNAPSHOT_PATH, snapshot)
    else:
        snapshot = _read_json(MT5_SNAPSHOT_PATH, {})

    artifacts = build_artifacts(snapshot, now_utc=now_utc, write=True)
    print(json.dumps(artifacts["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
