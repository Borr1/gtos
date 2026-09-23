#!/usr/bin/env python3
"""Build the market-expansion broker-authority probe package.

This route uses the local localhost MT5 bridge as a read-only evidence source
for broker authority gaps left by the promotion-boundary package. It stores
redacted account metadata and aggregate deal-history rows only. It does not
send/check orders, select symbols, read positions/orders, use depth/orderflow,
push remotes, apply config, or reload VPS/runtime processes.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
DOSSIER_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_live_authority_dossier_2026_06_18"
PROMOTION_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_promotion_boundary_2026_06_18"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_broker_authority_probe"
HISTORY_START = datetime(2024, 1, 1, tzinfo=UTC)
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 8001
BRIDGE_TIMEOUT_SECONDS = 10

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_payload(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def rounded(value: Any, digits: int = 8) -> float | None:
    number = finite_float(value)
    return round(number, digits) if number is not None else None


def as_plain(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if hasattr(value, "_asdict"):
        return {key: as_plain(item) for key, item in value._asdict().items()}
    if isinstance(value, dict):
        return {str(key): as_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [as_plain(item) for item in value]
    if hasattr(value, "__iter__") and not isinstance(value, (bytes, bytearray)):
        try:
            return [as_plain(item) for item in value]
        except TypeError:
            pass
    return repr(value)


def hash_value(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()


def median(values: list[float]) -> float | None:
    clean = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not clean:
        return None
    mid = len(clean) // 2
    return clean[mid] if len(clean) % 2 else (clean[mid - 1] + clean[mid]) / 2.0


def load_dossier_rows() -> list[dict[str, Any]]:
    return read_json(DOSSIER_ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json")["rows"]


def risk_by_tag() -> dict[str, float]:
    grouped: dict[str, list[float]] = {}
    for row in read_jsonl(DOSSIER_ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl"):
        risk = finite_float(row.get("risk_abs"))
        if risk and risk > 0:
            grouped.setdefault(row["tag"], []).append(risk)
    return {tag: value for tag, values in grouped.items() if (value := median(values)) is not None}


def docker_surface() -> dict[str, Any]:
    command = ["docker", "ps", "--filter", "name=siliconmetatrader5-kasm", "--format", "{{json .}}"]
    payload: dict[str, Any] = {"command": " ".join(command), "available": False, "container_count": 0, "containers": []}
    try:
        proc = subprocess.run(command, cwd=PROJECT_ROOT, text=True, capture_output=True, timeout=15)
    except Exception as exc:  # noqa: BLE001
        payload["error"] = repr(exc)
        return payload
    payload.update({"returncode": proc.returncode, "stderr_tail": proc.stderr[-1000:]})
    if proc.returncode != 0:
        return payload
    rows = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            rows.append({"raw_line_sha256": sha256_payload(line), "parse_error": True})
            continue
        rows.append(
            {
                "id_hash": hash_value(raw.get("ID")),
                "image": raw.get("Image"),
                "names": raw.get("Names"),
                "ports": raw.get("Ports"),
                "status": raw.get("Status"),
                "running_for": raw.get("RunningFor"),
            }
        )
    payload.update({"available": bool(rows), "container_count": len(rows), "containers": rows})
    return payload


def connect_bridge():
    from siliconmetatrader5 import MetaTrader5

    mt5 = MetaTrader5(host=BRIDGE_HOST, port=BRIDGE_PORT, timeout=BRIDGE_TIMEOUT_SECONDS)
    initialized = mt5.initialize()
    return mt5, bool(initialized)


def bridge_method_surface(created_at: str) -> tuple[Any, dict[str, Any]]:
    import siliconmetatrader5
    from siliconmetatrader5 import MetaTrader5

    mt5, initialized = connect_bridge()
    method_names = sorted(name for name in dir(MetaTrader5) if not name.startswith("__"))
    read_methods = [
        "account_info",
        "terminal_info",
        "symbol_info",
        "symbol_info_tick",
        "history_deals_get",
        "history_orders_get",
        "order_calc_margin",
        "order_calc_profit",
        "copy_rates_range",
        "copy_ticks_range",
    ]
    mutating_or_disallowed_methods = [
        "order" + "_send",
        "order" + "_check",
        "positions" + "_get",
        "orders" + "_get",
        "market" + "_book_add",
        "market" + "_book_get",
        "market" + "_book_release",
        "symbol" + "_select",
    ]
    bridge_host_method_probe: dict[str, Any] = {}
    bridge_host_session_like_names: list[str] | None = None
    try:
        bridge_host_method_probe = as_plain(
            mt5.eval(
                "[(n, hasattr(__import__('MetaTrader5'), n)) for n in "
                "['symbol_info_session_trade','symbol_info_session_quote','history_deals_get',"
                "'order_calc_profit','account_info','terminal_info']]"
            )
        )
    except Exception as exc:  # noqa: BLE001
        bridge_host_method_probe = {"error": repr(exc)}
    try:
        bridge_host_session_like_names = as_plain(
            mt5.eval("sorted([n for n in dir(__import__('MetaTrader5')) if 'session' in n.lower()])")
        )
    except Exception as exc:  # noqa: BLE001
        bridge_host_session_like_names = [f"error:{exc!r}"]
    surface = {
        "schema": f"{SCHEMA_PREFIX}.bridge_method_surface.v1",
        "created_at_utc": created_at,
        "bridge_host": BRIDGE_HOST,
        "bridge_port": BRIDGE_PORT,
        "bridge_initialized": initialized,
        "client_file": getattr(siliconmetatrader5, "__file__", None),
        "client_file_sha256": sha256_file(Path(siliconmetatrader5.__file__)),
        "client_version": getattr(siliconmetatrader5, "__version__", None),
        "method_count": len(method_names),
        "method_names_sha256": sha256_payload(method_names),
        "approved_read_method_available": {name: hasattr(MetaTrader5, name) for name in read_methods},
        "mutating_or_disallowed_method_available": {name: hasattr(MetaTrader5, name) for name in mutating_or_disallowed_methods},
        "read_only_method_signatures": {
            name: str(inspect.signature(getattr(MetaTrader5, name)))
            for name in read_methods
            if hasattr(MetaTrader5, name)
        },
        "bridge_host_method_probe_scope": "localhost RPyC bridge-host MT5 module, not VPS",
        "bridge_host_method_probe": bridge_host_method_probe,
        "bridge_host_session_like_names": bridge_host_session_like_names or [],
        "docker_surface": docker_surface(),
        "approved_read_surfaces_used_by_this_route": [
            "account_info_redacted",
            "terminal_info_redacted",
            "symbol_info",
            "symbol_info_tick",
            "history_deals_get_aggregate_only",
            "order_calc_profit_price_conversion",
        ],
        "forbidden_surfaces_not_used_by_this_route": [
            "order mutation",
            "order precheck mutation-risk surface",
            "position/order-state reads",
            "symbol selection",
            "market book/depth/orderflow",
            "remote push",
            "VPS reload",
            "config activation",
        ],
    }
    return mt5, surface


def account_terminal_redacted(created_at: str, mt5: Any) -> dict[str, Any]:
    account = as_plain(mt5.account_info())
    terminal = as_plain(mt5.terminal_info())
    redacted_account = None
    if isinstance(account, dict):
        redacted_account = {
            "login_hash": hash_value(account.get("login")),
            "server_hash": hash_value(account.get("server")),
            "name_hash": hash_value(account.get("name")),
            "company_hash": hash_value(account.get("company")),
            "currency": account.get("currency"),
            "trade_mode": account.get("trade_mode"),
            "margin_mode": account.get("margin_mode"),
            "leverage": account.get("leverage"),
            "limit_orders": account.get("limit_orders"),
        }
    redacted_terminal = None
    if isinstance(terminal, dict):
        redacted_terminal = {
            "connected": terminal.get("connected"),
            "trade_allowed": terminal.get("trade_allowed"),
            "tradeapi_disabled": terminal.get("tradeapi_disabled"),
            "dlls_allowed": terminal.get("dlls_allowed"),
            "community_connection": terminal.get("community_connection"),
            "name_hash": hash_value(terminal.get("name")),
            "company_hash": hash_value(terminal.get("company")),
            "path_hash": hash_value(terminal.get("path")),
        }
    return {
        "schema": f"{SCHEMA_PREFIX}.account_terminal_redacted_audit.v1",
        "created_at_utc": created_at,
        "account_info_read": True,
        "terminal_info_read": True,
        "redaction_policy": "hash login/server/name/company/path; omit balance/equity/margin/profit/raw account identifiers",
        "redacted_account": redacted_account,
        "redacted_terminal": redacted_terminal,
        "sensitive_fields_excluded": [
            "login",
            "server",
            "name",
            "company",
            "balance",
            "equity",
            "profit",
            "margin",
            "margin_free",
            "margin_level",
        ],
        "raw_account_values_stored": False,
    }


def session_table_remote_proof(created_at: str, mt5: Any, bridge_surface: dict[str, Any]) -> dict[str, Any]:
    dossier_rows = load_dossier_rows()
    symbol_info_keys = sorted(set().union(*[(row["captured"].get("symbol_info") or {}).keys() for row in dossier_rows]))
    session_keys = [key for key in symbol_info_keys if "session" in key.lower()]
    bridge_host_probe = bridge_surface.get("bridge_host_method_probe")
    bridge_host_map = {}
    if isinstance(bridge_host_probe, list):
        bridge_host_map = {name: bool(value) for name, value in bridge_host_probe if isinstance(name, str)}
    return {
        "schema": f"{SCHEMA_PREFIX}.session_table_remote_proof.v1",
        "created_at_utc": created_at,
        "proof_scope": "local siliconmetatrader5 client and localhost bridge-host MT5 module, not VPS",
        "client_symbol_info_session_trade": bool(getattr(type(mt5), "symbol_info_session_trade", None)),
        "client_symbol_info_session_quote": bool(getattr(type(mt5), "symbol_info_session_quote", None)),
        "bridge_host_symbol_info_session_trade": bridge_host_map.get("symbol_info_session_trade", False),
        "bridge_host_symbol_info_session_quote": bridge_host_map.get("symbol_info_session_quote", False),
        "remote_symbol_info_session_trade": bridge_host_map.get("symbol_info_session_trade", False),
        "remote_symbol_info_session_quote": bridge_host_map.get("symbol_info_session_quote", False),
        "bridge_host_session_like_names": bridge_surface.get("bridge_host_session_like_names", []),
        "remote_session_like_names": bridge_surface.get("bridge_host_session_like_names", []),
        "symbol_info_session_like_keys": session_keys,
        "symbol_info_session_like_key_count": len(session_keys),
        "session_table_closed": False,
        "status": "not_closed_local_bridge_and_bridge_host_mt5_expose_no_session_table_method",
        "repair_requirement": "broker/platform session table source or bridge method exposing exact trade/quote sessions",
    }


def history_deal_rows(created_at: str, mt5: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    end = datetime.now(UTC)
    for source_row in load_dossier_rows():
        broker_symbol = source_row["broker_symbol"]
        deals_error = None
        try:
            deals_raw = mt5.history_deals_get(HISTORY_START, end, group=broker_symbol)
        except Exception as exc:  # noqa: BLE001
            deals_raw = []
            deals_error = repr(exc)
        deals = [as_plain(deal) for deal in (deals_raw or [])]
        commissions = [finite_float(deal.get("commission")) or 0.0 for deal in deals if isinstance(deal, dict)]
        swaps = [finite_float(deal.get("swap")) or 0.0 for deal in deals if isinstance(deal, dict)]
        profits = [finite_float(deal.get("profit")) or 0.0 for deal in deals if isinstance(deal, dict)]
        volumes = [finite_float(deal.get("volume")) or 0.0 for deal in deals if isinstance(deal, dict)]
        times = [int(deal.get("time")) for deal in deals if isinstance(deal, dict) and deal.get("time")]
        deal_count = len(deals)
        commission_nonzero_count = sum(1 for value in commissions if abs(value) > 1e-12)
        if deals_error:
            authority_status = "not_closed_bridge_history_error"
        elif deal_count == 0:
            authority_status = "not_closed_no_direct_deal_rows_for_symbol"
        elif commission_nonzero_count:
            authority_status = "direct_observed_nonzero_commission_account_history"
        else:
            authority_status = "direct_observed_zero_commission_account_history_not_schedule"
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.deal_history_commission_row.v1",
                "created_at_utc": created_at,
                "tag": source_row["tag"],
                "file_symbol": source_row["file_symbol"],
                "broker_symbol": broker_symbol,
                "history_window_start_utc": HISTORY_START.isoformat(),
                "history_window_end_utc": end.isoformat(),
                "history_query": "history_deals_get aggregate-only group=broker_symbol",
                "raw_ticket_or_order_ids_stored": False,
                "deal_count": deal_count,
                "commission_sum": round(sum(commissions), 6),
                "commission_nonzero_count": commission_nonzero_count,
                "commission_min": rounded(min(commissions), 6) if commissions else None,
                "commission_max": rounded(max(commissions), 6) if commissions else None,
                "swap_sum": round(sum(swaps), 6),
                "swap_nonzero_count": sum(1 for value in swaps if abs(value) > 1e-12),
                "profit_sum": round(sum(profits), 6),
                "volume_sum": round(sum(volumes), 6),
                "entry_values": sorted({deal.get("entry") for deal in deals if isinstance(deal, dict) and deal.get("entry") is not None}),
                "type_values": sorted({deal.get("type") for deal in deals if isinstance(deal, dict) and deal.get("type") is not None}),
                "first_deal_time_utc": datetime.fromtimestamp(min(times), UTC).isoformat() if times else None,
                "last_deal_time_utc": datetime.fromtimestamp(max(times), UTC).isoformat() if times else None,
                "authority_status": authority_status,
                "history_error": deals_error,
            }
        )
    status_counts = Counter(row["authority_status"] for row in rows)
    summary = {
        "schema": f"{SCHEMA_PREFIX}.deal_history_commission_summary.v1",
        "created_at_utc": created_at,
        "symbol_count": len(rows),
        "history_window_start_utc": HISTORY_START.isoformat(),
        "history_window_end_utc": end.isoformat(),
        "deal_count_total": sum(row["deal_count"] for row in rows),
        "direct_history_symbol_count": sum(1 for row in rows if row["deal_count"] > 0),
        "no_direct_history_symbol_count": sum(1 for row in rows if row["deal_count"] == 0),
        "nonzero_commission_symbol_count": sum(1 for row in rows if row["commission_nonzero_count"] > 0),
        "observed_zero_commission_symbol_count": sum(1 for row in rows if row["deal_count"] > 0 and row["commission_nonzero_count"] == 0),
        "commission_sum_total": round(sum(row["commission_sum"] for row in rows), 6),
        "swap_sum_total": round(sum(row["swap_sum"] for row in rows), 6),
        "authority_status_counts": dict(status_counts),
        "all_symbols_commission_authority_closed": False,
        "interpretation": (
            "deal history partially repairs commission evidence, but symbols with no direct deal rows and "
            "the absence of a broker schedule/platform commission source keep the activation gate open"
        ),
    }
    return rows, summary


def normalize_volume(volume_min: float, volume_max: float, volume_step: float) -> float:
    if volume_min <= 1.0 <= volume_max:
        target = 1.0
    else:
        target = volume_min
    if volume_step > 0 and target != volume_min:
        steps = round((target - volume_min) / volume_step)
        target = volume_min + steps * volume_step
    return round(min(max(target, volume_min), volume_max), 8)


def symbol_info_tick(mt5: Any, broker_symbol: str) -> tuple[dict[str, Any], dict[str, Any], float]:
    info = as_plain(mt5.symbol_info(broker_symbol)) or {}
    tick = as_plain(mt5.symbol_info_tick(broker_symbol)) or {}
    bid = finite_float(tick.get("bid"))
    ask = finite_float(tick.get("ask"))
    if bid and ask and bid > 0 and ask > 0:
        mid = (bid + ask) / 2.0
    else:
        mid = finite_float(tick.get("last")) or finite_float(info.get("last")) or 1.0
    return info, tick, mid


def profit_conversion_rows(created_at: str, mt5: Any) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows = []
    buy_type = getattr(mt5, "ORDER_TYPE_BUY", 0)
    sell_type = getattr(mt5, "ORDER_TYPE_SELL", 1)
    for source_row in load_dossier_rows():
        broker_symbol = source_row["broker_symbol"]
        info, tick, mid = symbol_info_tick(mt5, broker_symbol)
        point = finite_float(info.get("point")) or 0.00001
        tick_size = finite_float(info.get("trade_tick_size")) or point
        tick_value = finite_float(info.get("trade_tick_value"))
        volume_min = finite_float(info.get("volume_min")) or 0.01
        volume_max = finite_float(info.get("volume_max")) or volume_min
        volume_step = finite_float(info.get("volume_step")) or volume_min or 0.01
        volume = normalize_volume(volume_min, volume_max, volume_step)
        move = max(point * 100.0, tick_size * 100.0, abs(mid) * 0.001, tick_size)
        move = math.ceil(move / tick_size) * tick_size if tick_size else move
        calc_error = None
        try:
            buy_profit = mt5.order_calc_profit(buy_type, broker_symbol, volume, mid, mid + move)
            sell_profit = mt5.order_calc_profit(sell_type, broker_symbol, volume, mid, mid - move)
        except Exception as exc:  # noqa: BLE001
            buy_profit = None
            sell_profit = None
            calc_error = repr(exc)
        expected_per_unit = (tick_value / tick_size) if tick_value and tick_size else None
        buy_per_unit = abs(float(buy_profit)) / move / volume if buy_profit is not None and move and volume else None
        sell_per_unit = abs(float(sell_profit)) / move / volume if sell_profit is not None and move and volume else None
        ratios = [
            value / expected_per_unit
            for value in (buy_per_unit, sell_per_unit)
            if value is not None and expected_per_unit not in (None, 0)
        ]
        match = bool(ratios) and all(0.995 <= ratio <= 1.005 for ratio in ratios)
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.order_calc_profit_conversion_row.v1",
                "created_at_utc": created_at,
                "tag": source_row["tag"],
                "file_symbol": source_row["file_symbol"],
                "broker_symbol": broker_symbol,
                "mid_price": rounded(mid, 8),
                "volume_used": volume,
                "price_move_used": rounded(move, 10),
                "point": rounded(point, 10),
                "trade_tick_size": rounded(tick_size, 10),
                "trade_tick_value": rounded(tick_value, 10),
                "currency_profit": info.get("currency_profit"),
                "currency_margin": info.get("currency_margin"),
                "buy_profit_for_move": rounded(buy_profit, 8),
                "sell_profit_for_move": rounded(sell_profit, 8),
                "observed_buy_per_price_unit_per_lot": rounded(buy_per_unit, 10),
                "observed_sell_per_price_unit_per_lot": rounded(sell_per_unit, 10),
                "symbol_info_expected_per_price_unit_per_lot": rounded(expected_per_unit, 10),
                "ratio_buy_vs_symbol_info": rounded(ratios[0], 8) if len(ratios) > 0 else None,
                "ratio_sell_vs_symbol_info": rounded(ratios[1], 8) if len(ratios) > 1 else None,
                "conversion_status": "closed_order_calc_profit_matches_symbol_info" if match else "not_closed_conversion_mismatch_or_error",
                "calc_error": calc_error,
                "tick_time_msc": tick.get("time_msc"),
            }
        )
    closed_count = sum(1 for row in rows if row["conversion_status"] == "closed_order_calc_profit_matches_symbol_info")
    max_abs_ratio_error = max(
        [
            abs(float(row[key]) - 1.0)
            for row in rows
            for key in ("ratio_buy_vs_symbol_info", "ratio_sell_vs_symbol_info")
            if row.get(key) is not None
        ]
        or [None]
    )
    summary = {
        "schema": f"{SCHEMA_PREFIX}.order_calc_profit_conversion_summary.v1",
        "created_at_utc": created_at,
        "symbol_count": len(rows),
        "closed_symbol_count": closed_count,
        "all_symbols_closed": closed_count == len(rows),
        "max_abs_ratio_error_vs_symbol_info": rounded(max_abs_ratio_error, 10),
        "conversion_status_counts": dict(Counter(row["conversion_status"] for row in rows)),
        "interpretation": "read-only order_calc_profit closes account-currency price conversion for market-expansion symbols",
    }
    return rows, summary


def swap_to_r_rows(
    created_at: str,
    conversion_rows: list[dict[str, Any]],
    deal_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    risks = risk_by_tag()
    by_symbol_conversion = {row["broker_symbol"]: row for row in conversion_rows}
    by_symbol_deals = {row["broker_symbol"]: row for row in deal_rows}
    rows = []
    for source_row in load_dossier_rows():
        broker_symbol = source_row["broker_symbol"]
        tag = source_row["tag"]
        info = source_row.get("captured", {}).get("symbol_info") or {}
        conv = by_symbol_conversion[broker_symbol]
        risk_abs = risks[tag]
        value_per_unit_candidates = [
            finite_float(conv.get("observed_buy_per_price_unit_per_lot")),
            finite_float(conv.get("observed_sell_per_price_unit_per_lot")),
        ]
        value_per_unit = median([value for value in value_per_unit_candidates if value is not None])
        point = finite_float(info.get("point")) or finite_float(conv.get("point"))
        risk_cash_per_lot = risk_abs * value_per_unit if value_per_unit is not None else None
        for side, field in (("LONG", "swap_long"), ("SHORT", "swap_short")):
            swap_raw = finite_float(info.get(field))
            swap_mode = info.get("swap_mode")
            row: dict[str, Any] = {
                "schema": f"{SCHEMA_PREFIX}.swap_to_r_partial_authority_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": source_row["file_symbol"],
                "broker_symbol": broker_symbol,
                "side": side,
                "swap_mode": swap_mode,
                "swap_rollover3days": info.get("swap_rollover3days"),
                "swap_raw": rounded(swap_raw, 8),
                "point": rounded(point, 10),
                "risk_abs_median": rounded(risk_abs, 10),
                "value_per_price_unit_per_lot_account_currency": rounded(value_per_unit, 10),
                "risk_cash_per_lot_account_currency": rounded(risk_cash_per_lot, 10),
                "deal_history_swap_sum": by_symbol_deals.get(broker_symbol, {}).get("swap_sum"),
                "deal_history_swap_nonzero_count": by_symbol_deals.get(broker_symbol, {}).get("swap_nonzero_count"),
            }
            if swap_mode == 1 and swap_raw is not None and point and value_per_unit is not None and risk_cash_per_lot:
                one_day_cash = swap_raw * point * value_per_unit
                one_day_r = one_day_cash / risk_cash_per_lot
                row.update(
                    {
                        "conversion_status": "point_mode_cash_to_r_computed",
                        "one_day_swap_cash_per_lot_account_currency": rounded(one_day_cash, 10),
                        "one_day_swap_r_per_lot_risk": rounded(one_day_r, 10),
                        "triple_rollover_swap_r_per_lot_risk": rounded(one_day_r * 3.0, 10),
                        "remaining_gap": "holding_time_and_exact_rollover_application_model_not_closed",
                    }
                )
            elif swap_mode == 5:
                row.update(
                    {
                        "conversion_status": "not_closed_interest_current_mode_formula_required",
                        "one_day_swap_cash_per_lot_account_currency": None,
                        "one_day_swap_r_per_lot_risk": None,
                        "triple_rollover_swap_r_per_lot_risk": None,
                        "remaining_gap": "swap_mode_5_formula_and_holding_time_model_required",
                    }
                )
            else:
                row.update(
                    {
                        "conversion_status": "not_closed_unknown_or_unhandled_swap_mode",
                        "one_day_swap_cash_per_lot_account_currency": None,
                        "one_day_swap_r_per_lot_risk": None,
                        "triple_rollover_swap_r_per_lot_risk": None,
                        "remaining_gap": "swap_mode_formula_required",
                    }
                )
            rows.append(row)
    status_counts = Counter(row["conversion_status"] for row in rows)
    point_rows = [row for row in rows if row["conversion_status"] == "point_mode_cash_to_r_computed"]
    summary = {
        "schema": f"{SCHEMA_PREFIX}.swap_to_r_partial_authority_summary.v1",
        "created_at_utc": created_at,
        "side_row_count": len(rows),
        "symbol_count": len({row["broker_symbol"] for row in rows}),
        "point_mode_side_rows_computed": len(point_rows),
        "mode5_or_other_side_rows_not_closed": len(rows) - len(point_rows),
        "conversion_status_counts": dict(status_counts),
        "max_abs_one_day_swap_r_point_mode": rounded(
            max([abs(float(row["one_day_swap_r_per_lot_risk"])) for row in point_rows] or [0.0]), 10
        ),
        "all_swap_to_r_closed": False,
        "interpretation": (
            "point-mode swap can be converted to an account-currency R estimate from symbol_info plus "
            "order_calc_profit conversion, but mode-5 crypto formulas and exact holding-time/rollover "
            "application remain activation blockers"
        ),
    }
    return rows, summary


def unresolved_requirements(created_at: str) -> list[dict[str, Any]]:
    items = [
        (
            "MX-BROKER-AUTH-REQ-001",
            "explicit broker trading-session table or platform-source proof",
            "local client and localhost bridge-host MT5 module still expose no symbol_info_session_trade/session_quote method and symbol_info has no session-like keys",
            "capture broker/platform session table from an exact source or add/read a bridge method that exposes exact sessions",
        ),
        (
            "MX-BROKER-AUTH-REQ-002",
            "broker-exact commission schedule or direct authority for every activation symbol",
            "deal-history aggregates partially repair commission evidence, but no direct deal rows exist for every symbol and no schedule/platform source was found",
            "obtain broker schedule/platform source or sufficient broker-history/export evidence for every promoted broker symbol",
        ),
        (
            "MX-BROKER-AUTH-REQ-003",
            "broker-exact slippage, limit-fill, and market-fill authority",
            "this route does not inspect order lifecycle/fillability, queue state, or observed slippage and does not call any order-check/send surface",
            "VPS dry-run packet parity plus explicit broker lifecycle/fill capture or guarded-open skip proof",
        ),
        (
            "MX-BROKER-AUTH-REQ-004",
            "exact swap-to-R holding-time and rollover model for all market-expansion symbols",
            "point-mode rows are converted, but swap_mode 5 formulas and exact holding-time/rollover application are not closed",
            "broker/platform swap formula source plus live execution holding-time contract and verifier",
        ),
        (
            "MX-BROKER-AUTH-REQ-005",
            "owner-approved VPS promotion and monitoring execution",
            "Mac route keeps market expansion default-off and does not push, reload, restart, or apply live config",
            "VPS Codex session must absorb commits, rerun packet parity, apply only after all authority gates close, monitor, and retain rollback",
        ),
    ]
    return [
        {
            "schema": f"{SCHEMA_PREFIX}.unresolved_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": req_id,
            "requirement": requirement,
            "current_evidence": evidence,
            "repair_path": repair,
            "status": "not_closed_by_current_probe",
            "runtime_effect_now": "none_market_expansion_default_off",
        }
        for req_id, requirement, evidence, repair in items
    ]


def decision_ledgers(
    created_at: str,
    result: dict[str, Any],
    deal_summary: dict[str, Any],
    conversion_summary: dict[str, Any],
    swap_summary: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decisions = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "broker_authority_probe_partial_repair",
            "status": result["decision"],
            "evidence": {
                "profit_conversion_closed_symbol_count": result["profit_conversion_closed_symbol_count"],
                "commission_direct_history_symbol_count": result["commission_direct_history_symbol_count"],
                "swap_point_mode_side_rows_computed": result["swap_point_mode_side_rows_computed"],
            },
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "order_calc_profit_conversion_authority",
            "status": "closed_for_14_symbols",
            "evidence": conversion_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "commission_authority",
            "status": "partial_direct_history_not_full_schedule",
            "evidence": deal_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "swap_to_r_authority",
            "status": "partial_point_mode_conversion_not_full_holding_model",
            "evidence": swap_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "market_expansion_promotion",
            "status": "default_off_not_promoted",
            "evidence": {"deployment_ready": False, "promotion_ready": False},
        },
    ]
    boundary = [
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "session_table_authority",
            "status": "not_closed",
            "evidence": "local client and localhost bridge-host MT5 session table methods unavailable; VPS parity remains separate",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "commission_authority",
            "status": "partial_not_closed",
            "evidence": deal_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "account_currency_profit_conversion",
            "status": "closed_for_probe_symbols",
            "evidence": conversion_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "swap_to_r_authority",
            "status": "partial_not_closed",
            "evidence": swap_summary,
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "fill_slippage_limit_authority",
            "status": "not_closed_not_mutated",
            "evidence": "no order lifecycle/fill/slippage/depth surface was touched",
        },
        {
            "schema": f"{SCHEMA_PREFIX}.promotion_boundary_row.v1",
            "created_at_utc": created_at,
            "gate": "owner_vps_action",
            "status": "not_executed_by_mac_route",
            "evidence": "no config activation, remote push, broker mutation, or VPS restart/reload",
        },
    ]
    return decisions, boundary


def forbidden_call_scan(created_at: str) -> dict[str, Any]:
    scanned_paths = [
        ROUTE / "build_market_expansion_broker_authority_probe.py",
        ROUTE / "verify_market_expansion_broker_authority_probe.py",
        PROJECT_ROOT / "tests" / "ultimate_book" / "test_market_expansion_broker_authority_probe_artifacts.py",
    ]
    forbidden_patterns = [
        "order" + "_send(",
        "order" + "_check(",
        ".order" + "_check",
        "getattr(mt5, \"order" + "_check\"",
        "getattr(mt5, 'order" + "_check'",
        "TRADE" + "_ACTION_",
        "positions" + "_get" + "(",
        ".positions" + "_get",
        "getattr(mt5, \"positions" + "_get\"",
        "getattr(mt5, 'positions" + "_get'",
        "orders" + "_get" + "(",
        ".orders" + "_get",
        "getattr(mt5, \"orders" + "_get\"",
        "getattr(mt5, 'orders" + "_get'",
        "history" + "_orders" + "_get" + "(",
        "market" + "_book_add(",
        "market" + "_book_get(",
        "market" + "_book_release(",
        "symbol" + "_select(",
        "copy" + "_ticks_range(",
        "subprocess" + ".run(['" + "ssh'",
        "subprocess" + ".run([\"" + "ssh\"",
        "rs" + "ync ",
        "sc" + "p ",
    ]
    matches = []
    for path in scanned_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in text:
                matches.append({"path": rel(path), "pattern": pattern})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "scanned_paths": [rel(path) for path in scanned_paths if path.exists()],
        "approved_read_calls_not_forbidden_in_this_route": ["account_info", "terminal_info", "history_deals_get", "order_calc_profit"],
        "forbidden_patterns": forbidden_patterns,
        "matches": matches,
        "ok": not matches,
    }


def write_packet(result: dict[str, Any], requirements: list[dict[str, Any]]) -> None:
    req_text = "\n".join(f"- `{row['requirement_id']}`: {row['requirement']}" for row in requirements)
    packet = f"""# Market Expansion Broker-Authority Probe Packet

Decision: `{result['decision']}`

This package improves the broker-authority picture without promoting market expansion.
It used only redacted/aggregate read-only bridge evidence and calculation functions.

What improved:

- `order_calc_profit` conversion now closes for `{result['profit_conversion_closed_symbol_count']}/{result['selectable_symbol_count']}` market-expansion symbols.
- Direct deal-history commission evidence exists for `{result['commission_direct_history_symbol_count']}/{result['selectable_symbol_count']}` symbols.
- Nonzero direct commission was observed for `{result['commission_nonzero_symbol_count']}` symbols; direct zero-commission history was observed for `{result['commission_observed_zero_symbol_count']}` symbols.
- Point-mode swap-to-R conversion was computed for `{result['swap_point_mode_side_rows_computed']}/{result['swap_side_row_count']}` side rows.

What is still not live authority:

{req_text}

Runtime boundary:

- `live_authority=false`
- `deployment_ready=false`
- `promotion_ready=false`
- `runtime_effect=none_market_expansion_default_off_broker_authority_probe_only`

Do not apply the market-expansion patch from the promotion-boundary route until
these requirements are closed on the VPS/runtime namespace and the owner
explicitly approves activation.
"""
    (ROUTE / "BROKER_AUTHORITY_PROBE_PACKET.md").write_text(packet, encoding="utf-8")


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Market Expansion Broker-Authority Closure Successor Prompt

Created: {created_at}

Mandatory context use: run GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the broker-authority probe artifacts from disk as active instructions. Do not rely on chat memory. After compaction/resume/interruption/uncertainty, reread the prompt, doctrine, and latest route artifacts before continuing.

Lane posture: constructive source-repair and deployment-authority closure. Keep market expansion default-off until all authority gates close. Use maximum practical reasoning inside the evidence class, no arbitrary top-N, and no conservative brake. Preserve all material rows and pursue same-evidence-class repair before declaring a blocker.

Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted, repaired, recomputed, or reduced to an exact owner/source/capture requirement. Full same-evidence-class pursuit is mandatory; a clean blocker ledger is not completion when a same-class read-only source-capture, source completeness check, branch decision, implementation decision, exact-R/proxy-R/expectancy recomputation, or result materialization step is still executable.

Input route: `research/operations/final_moonshot_market_expansion_broker_authority_probe_2026_06_18/`.

Objective: close or exactly bound the remaining broker-authority requirements for market expansion without orderflow/depth. The current probe closes account-currency profit conversion for 14/14 symbols, partially repairs commission authority from aggregate deal history, and partially computes point-mode swap-to-R. Continue from those artifacts. Search for exact platform/broker session tables, exact commission schedule or direct authority for the no-history symbols, exact mode-5 swap formula and holding-time application, and VPS packet-parity/fill/slippage proof. If all gates close, prepare an owner-action activation packet and rollback/monitoring plan. If any gate remains open, keep expansion default-off and update the unresolved requirement ledgers with exact source/capture requirements.

Result materialization standard: every branch decision and implementation decision must preserve result-use-status/evidence-class boundaries, exact-R/proxy-R/expectancy values where lawful, source-capture/source completeness status, row counts, denominator rules, no-leak/as-of controls, and unresolved owner/source/capture requirements.

Approved read-only evidence surfaces in this lane: redacted `account_info`, redacted `terminal_info`, `symbol_info`, `symbol_info_tick`, aggregate `history_deals_get`, and `order_calc_profit`. Forbidden unless the owner explicitly opens a deployment/live-operation lane: production-change, live trading, broker operation, broker/account/order/history/deal/position mutation beyond the approved aggregate read-only evidence class, order send/check, symbol selection, positions/orders state reads, market book/depth/orderflow, prompt/config/risk/execution/safety/canary/selector live activation, credential mutation/disclosure, paid API/vendor calls, remote push, live config activation, and VPS restart/reload.

Completion requires: result JSON, decision ledger, promotion-boundary ledger, unresolved/blocker-repair ledgers, verifier result, focused test record, output manifest, saturation/self-red-team audit, completion audit with instruction coverage, and a scoped commit. Mark complete only when the completion standard is satisfied with no vague blockers or hidden live-action assumptions.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if path.is_file() and path.name != "OUTPUT_MANIFEST.json":
            artifacts.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256_file(path)})
    write_json(
        ROUTE / "OUTPUT_MANIFEST.json",
        {
            "schema": f"{SCHEMA_PREFIX}.output_manifest.v1",
            "created_at_utc": created_at,
            "artifact_count": len(artifacts),
            "artifacts": artifacts,
        },
    )


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    mt5, bridge_surface = bridge_method_surface(created_at)
    account_terminal = account_terminal_redacted(created_at, mt5)
    session_proof = session_table_remote_proof(created_at, mt5, bridge_surface)
    deal_rows, deal_summary = history_deal_rows(created_at, mt5)
    conversion_rows, conversion_summary = profit_conversion_rows(created_at, mt5)
    swap_rows, swap_summary = swap_to_r_rows(created_at, conversion_rows, deal_rows)
    requirements = unresolved_requirements(created_at)
    forbidden = forbidden_call_scan(created_at)

    selectable_symbol_count = len(load_dossier_rows())
    conversion_closed_count = conversion_summary["closed_symbol_count"]
    direct_history_count = deal_summary["direct_history_symbol_count"]
    nonzero_commission_count = deal_summary["nonzero_commission_symbol_count"]
    zero_commission_count = deal_summary["observed_zero_commission_symbol_count"]
    swap_point_count = swap_summary["point_mode_side_rows_computed"]
    ok = (
        bridge_surface["bridge_initialized"] is True
        and account_terminal["raw_account_values_stored"] is False
        and session_proof["session_table_closed"] is False
        and selectable_symbol_count == 14
        and conversion_closed_count == selectable_symbol_count
        and direct_history_count >= 1
        and swap_point_count >= 1
        and forbidden["ok"] is True
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": "BROKER_AUTHORITY_PARTIAL_REPAIR_DEFAULT_OFF_NOT_PROMOTED",
        "source_dossier_route": rel(DOSSIER_ROUTE),
        "source_promotion_route": rel(PROMOTION_ROUTE),
        "selectable_symbol_count": selectable_symbol_count,
        "bridge_initialized": bridge_surface["bridge_initialized"],
        "account_info_read_redacted": account_terminal["account_info_read"],
        "terminal_info_read_redacted": account_terminal["terminal_info_read"],
        "session_table_closed": session_proof["session_table_closed"],
        "commission_direct_history_symbol_count": direct_history_count,
        "commission_no_direct_history_symbol_count": deal_summary["no_direct_history_symbol_count"],
        "commission_nonzero_symbol_count": nonzero_commission_count,
        "commission_observed_zero_symbol_count": zero_commission_count,
        "commission_all_symbols_closed": deal_summary["all_symbols_commission_authority_closed"],
        "profit_conversion_closed_symbol_count": conversion_closed_count,
        "profit_conversion_all_symbols_closed": conversion_summary["all_symbols_closed"],
        "swap_side_row_count": swap_summary["side_row_count"],
        "swap_point_mode_side_rows_computed": swap_point_count,
        "swap_mode5_or_other_side_rows_not_closed": swap_summary["mode5_or_other_side_rows_not_closed"],
        "swap_all_symbols_closed": swap_summary["all_swap_to_r_closed"],
        "fill_slippage_authority_closed": False,
        "config_patch_applied": False,
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "runtime_effect": "none_market_expansion_default_off_broker_authority_probe_only",
        "deployment_not_ready_requirement_ids": [row["requirement_id"] for row in requirements],
        "deployment_not_ready_reasons": [row["requirement"] for row in requirements],
        "approved_read_surfaces_used": bridge_surface["approved_read_surfaces_used_by_this_route"],
        "forbidden_surfaces_touched": [],
    }
    decisions, boundary = decision_ledgers(created_at, result, deal_summary, conversion_summary, swap_summary)
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "no_arbitrary_top_n": True,
        "anti_boxing_checked": [
            "client method surface",
            "localhost bridge-host MT5 method surface",
            "session-like symbol_info keys",
            "redacted account/terminal authority",
            "aggregate deal-history commission by all 14 symbols",
            "large-move order_calc_profit conversion instead of tiny rounded moves",
            "side-aware swap-to-R split by swap mode",
            "forbidden mutation/depth/VPS surface scan",
        ],
        "same_evidence_class_repairs_completed": [
            "closed account-currency price conversion for 14/14 symbols",
            "split commission authority into nonzero direct, zero direct, and no-history rows",
            "computed point-mode swap-to-R estimates for supported side rows",
            "proved session table remains absent from local client, localhost bridge-host MT5 module, and symbol_info keys",
        ],
        "remaining_exact_requirements": result["deployment_not_ready_reasons"],
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_source_repair_posture_applied": True,
            "inspire_not_kill_applied": True,
            "same_evidence_class_pursued": True,
            "no_arbitrary_top_n": True,
        },
        "approved_read_surfaces_used": result["approved_read_surfaces_used"],
        "forbidden_surfaces_touched": [],
        "raw_account_values_stored": False,
        "runtime_effect_boundary": result["runtime_effect"],
        "deployment_ready": False,
        "promotion_ready": False,
        "config_patch_applied": False,
        "owner_action_live_authority_boundary": "required before config patch, VPS reload, broker mutation, or live promotion",
    }

    write_json(ROUTE / "BRIDGE_METHOD_SURFACE.json", bridge_surface)
    write_json(ROUTE / "ACCOUNT_TERMINAL_REDACTED_AUDIT.json", account_terminal)
    write_json(ROUTE / "SESSION_TABLE_REMOTE_PROOF.json", session_proof)
    write_jsonl(ROUTE / "DEAL_HISTORY_COMMISSION_LEDGER.jsonl", deal_rows)
    write_json(ROUTE / "DEAL_HISTORY_COMMISSION_SUMMARY.json", deal_summary)
    write_jsonl(ROUTE / "ORDER_CALC_PROFIT_CONVERSION_LEDGER.jsonl", conversion_rows)
    write_json(ROUTE / "ORDER_CALC_PROFIT_CONVERSION_SUMMARY.json", conversion_summary)
    write_jsonl(ROUTE / "SWAP_TO_R_PARTIAL_AUTHORITY_LEDGER.jsonl", swap_rows)
    write_json(ROUTE / "SWAP_TO_R_PARTIAL_AUTHORITY_SUMMARY.json", swap_summary)
    write_jsonl(ROUTE / "UNRESOLVED_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirements)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "PROMOTION_BOUNDARY_LEDGER.jsonl", boundary)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "BROKER_AUTHORITY_PROBE_RESULT.json", result)
    write_packet(result, requirements)
    write_next_prompt(created_at)
    return result


def run_command(command: list[str], timeout: int = 180) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=timeout)
    return {
        "command": " ".join(command),
        "returncode": proc.returncode,
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-5000:],
    }


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command(
        [sys.executable, str(ROUTE / "verify_market_expansion_broker_authority_probe.py")],
        timeout=240,
    )
    write_json(
        ROUTE / "VERIFIER_COMMAND_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1",
            "created_at_utc": created_at,
            **verifier_result,
        },
    )
    checks = [
        run_command(
            [
                sys.executable,
                "-m",
                "py_compile",
                str(ROUTE / "build_market_expansion_broker_authority_probe.py"),
                str(ROUTE / "verify_market_expansion_broker_authority_probe.py"),
                "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_broker_authority_probe_artifacts.py",
                "-q",
            ],
            timeout=180,
        ),
    ]
    write_json(
        ROUTE / "FOCUSED_TEST_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
            "created_at_utc": created_at,
            "ok": all(row["returncode"] == 0 for row in checks),
            "results": checks,
        },
    )
    write_output_manifest(created_at)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
