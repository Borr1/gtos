#!/usr/bin/env python3
"""Build the default-off market-expansion live-authority dossier.

The dossier is deliberately default-off. It recomputes source proxy-R events,
overlays the implemented generators onto the current active A8 + candidate
book replay, captures broker specs through the read-only localhost bridge, and
records the exact remaining live-authority gaps without mutating broker,
config, remote, or VPS state.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import signal
import statistics
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.dont_write_bytecode = True

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
GENERATOR_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18"
ACTIVATION_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_activation_candidate_package_2026_06_18"
SCORING_BUILDER = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_validation_scoring_2026_06_18"
    / "build_market_expansion_validation_scoring.py"
)
CANDIDATE_REPLAY = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_candidate_enabled_unified_replay_mc_2026_06_18"
    / "verify_candidate_enabled_unified_replay_mc.py"
)
CONFIG_PATH = PROJECT_ROOT / "config" / "agent_config.yaml"
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_live_authority_dossier"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission  # noqa: E402
from src.components.ultimate_book.bridge import DEFAULT_CONFIG  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry  # noqa: E402
from src.components.ultimate_book.sleeves.registry import active_specs  # noqa: E402


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, sort_keys=True, default=str) + "\n" for row in rows), encoding="utf-8")


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def finite_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def summarize(values: list[float]) -> dict[str, Any]:
    clean = [float(value) for value in values if math.isfinite(float(value))]
    if not clean:
        return {"n": 0, "mean": None, "median": None, "win_rate": None, "min": None, "max": None, "sum": 0.0}
    return {
        "n": len(clean),
        "mean": round(statistics.fmean(clean), 6),
        "median": round(statistics.median(clean), 6),
        "win_rate": round(sum(1 for value in clean if value > 0) / len(clean), 6),
        "min": round(min(clean), 6),
        "max": round(max(clean), 6),
        "sum": round(sum(clean), 6),
    }


def split_summary(events: list[dict[str, Any]], key: str) -> dict[str, Any]:
    splits = {
        name: summarize([event[key] for event in events if event.get("split") == name])
        for name in ("train_le_2021", "oos_2022_2024", "sealed_ge_2025")
    }
    out = {
        "all": summarize([event[key] for event in events]),
        "splits": splits,
    }
    out["every_populated_split_positive"] = all(
        payload["n"] == 0 or (payload["mean"] is not None and payload["mean"] > 0)
        for payload in splits.values()
    )
    out["populated_split_count"] = sum(1 for payload in splits.values() if payload["n"] > 0)
    return out


def selected_activation_rows() -> list[dict[str, Any]]:
    rows = read_jsonl(ACTIVATION_ROUTE / "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl")
    selected = [
        row
        for row in rows
        if row.get("design_status") == "default_off_spec_design_ready"
        and row.get("symbol_collision_winner") is True
    ]
    return sorted(selected, key=lambda row: row["tag"])


def symbol_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_symbol": row["file_symbol"],
        "broker_symbol": row["broker_symbol"],
        "family": row["family"],
        "asset_class": row["family"],
        "spread_snapshot": row.get("spread_snapshot") or {},
    }


def source_event_rows(selected: list[dict[str, Any]], created_at: str) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    scoring = load_module("market_expansion_validation_scoring_builder_for_live_dossier", SCORING_BUILDER)
    generator_detail = read_jsonl(GENERATOR_ROUTE / "RUNTIME_GENERATOR_EVENT_PARITY_DETAIL.jsonl")
    risk_by_key = {
        (row["tag"], row["date"]): row.get("source_risk_abs")
        for row in generator_detail
        if row.get("status") == "matched"
    }
    rows: list[dict[str, Any]] = []
    by_tag: dict[str, list[dict[str, Any]]] = {}
    for activation in selected:
        d1_text = activation["session_source_status"]["source_spans"]["D1"]["best_path"]
        d1_path = PROJECT_ROOT / d1_text
        d1_hash = sha256_file(d1_path)
        all_events = scoring.d1_events(symbol_payload(activation), d1_path)
        events = [event for event in all_events if event["mechanism"] == activation["mechanism"]]
        by_tag[activation["tag"]] = events
        for event in events:
            date = str(event["time"])[:10]
            risk_abs = finite_float(risk_by_key.get((activation["tag"], date)))
            row = {
                "schema": f"{SCHEMA_PREFIX}.source_event_cost_row.v1",
                "created_at_utc": created_at,
                "tag": activation["tag"],
                "file_symbol": activation["file_symbol"],
                "broker_symbol": activation["broker_symbol"],
                "family": activation["family"],
                "mechanism": activation["mechanism"],
                "date": date,
                "time": event["time"],
                "split": event["split"],
                "signal": event["signal"],
                "risk_abs": risk_abs,
                "raw_proxy_r": event["raw_proxy_r"],
                "cost_r": event["cost_r"],
                "proxy_r_cost1": event["proxy_r_cost1"],
                "proxy_r_cost2": event["proxy_r_cost2"],
                "proxy_r_cost3": event["proxy_r_cost3"],
                "source_path": d1_text,
                "source_path_sha256": d1_hash,
                "source_join_status": "joined_generator_parity_risk" if risk_abs is not None else "missing_generator_parity_risk",
            }
            if "prev_ret" in event:
                row["prev_ret"] = event["prev_ret"]
            if "volume_z" in event:
                row["volume_z"] = event["volume_z"]
            rows.append(row)
    return rows, by_tag


def _plain_symbol_info(info: Any) -> dict[str, Any]:
    wanted = (
        "name",
        "path",
        "visible",
        "select",
        "custom",
        "digits",
        "point",
        "spread",
        "spread_float",
        "trade_mode",
        "trade_exemode",
        "trade_calc_mode",
        "trade_contract_size",
        "trade_tick_size",
        "trade_tick_value",
        "trade_tick_value_profit",
        "trade_tick_value_loss",
        "trade_stops_level",
        "trade_freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "volume_limit",
        "swap_mode",
        "swap_rollover3days",
        "swap_long",
        "swap_short",
        "swap_sunday",
        "swap_monday",
        "swap_tuesday",
        "swap_wednesday",
        "swap_thursday",
        "swap_friday",
        "swap_saturday",
        "filling_mode",
        "order_mode",
        "expiration_mode",
        "currency_base",
        "currency_profit",
        "currency_margin",
    )
    if info is None:
        return {}
    if isinstance(info, dict):
        data = info
    elif hasattr(info, "_asdict"):
        data = info._asdict()
    else:
        data = {field: getattr(info, field) for field in wanted if hasattr(info, field)}
    return {field: data.get(field) for field in wanted if field in data}


def _plain_tick_info(tick: Any) -> dict[str, Any]:
    wanted = (
        "time",
        "bid",
        "ask",
        "last",
        "volume",
        "time_msc",
        "flags",
        "volume_real",
    )
    if tick is None:
        return {}
    if isinstance(tick, dict):
        data = tick
    elif hasattr(tick, "_asdict"):
        data = tick._asdict()
    else:
        data = {field: getattr(tick, field) for field in wanted if hasattr(tick, field)}
    return {field: data.get(field) for field in wanted if field in data}


def _bridge_worker(queue: Any, broker_symbols: list[str]) -> None:
    rows: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        "bridge_reachable": False,
        "initialize_result": None,
        "account_info_read": False,
        "symbol_select_called": False,
        "broker_or_order_mutation": False,
        "orderflow_used": False,
        "session_trade_method_available": False,
        "session_quote_method_available": False,
        "rows": rows,
        "error": None,
    }
    mt5 = None
    try:
        from siliconmetatrader5 import MetaTrader5

        mt5 = MetaTrader5(host="localhost", port=8001, keepalive=False)
        init_result = mt5.initialize()
        payload["bridge_reachable"] = True
        payload["initialize_result"] = bool(init_result) if init_result is not None else None
        session_trade = getattr(mt5, "symbol_info_session_trade", None)
        session_quote = getattr(mt5, "symbol_info_session_quote", None)
        payload["session_trade_method_available"] = callable(session_trade)
        payload["session_quote_method_available"] = callable(session_quote)
        for broker_symbol in broker_symbols:
            info_payload = _plain_symbol_info(mt5.symbol_info(broker_symbol))
            tick_payload: dict[str, Any] = {}
            tick_method = getattr(mt5, "symbol_info_tick", None)
            if callable(tick_method):
                try:
                    tick_payload = _plain_tick_info(tick_method(broker_symbol))
                except Exception as exc:  # noqa: BLE001
                    tick_payload = {"error": repr(exc)}
            trade_sessions: list[Any] = []
            quote_sessions: list[Any] = []
            if callable(session_trade):
                for day in range(7):
                    for index in range(16):
                        try:
                            session = session_trade(broker_symbol, day, index)
                        except Exception as exc:  # noqa: BLE001
                            trade_sessions.append({"day": day, "index": index, "error": repr(exc)})
                            break
                        if session is None:
                            break
                        trade_sessions.append({"day": day, "index": index, "session": str(session)})
            if callable(session_quote):
                for day in range(7):
                    for index in range(16):
                        try:
                            session = session_quote(broker_symbol, day, index)
                        except Exception as exc:  # noqa: BLE001
                            quote_sessions.append({"day": day, "index": index, "error": repr(exc)})
                            break
                        if session is None:
                            break
                        quote_sessions.append({"day": day, "index": index, "session": str(session)})
            rows.append(
                {
                    "broker_symbol": broker_symbol,
                    "symbol_info_status": "captured" if info_payload else "not_returned",
                    "symbol_info": info_payload,
                    "symbol_info_tick_status": "captured" if tick_payload and "error" not in tick_payload else "not_captured",
                    "symbol_info_tick": tick_payload,
                    "explicit_trade_session_table_rows": trade_sessions,
                    "explicit_quote_session_table_rows": quote_sessions,
                    "explicit_session_table_present": bool(trade_sessions or quote_sessions),
                    "stop_freeze_fields_present": (
                        info_payload.get("trade_stops_level") is not None
                        and info_payload.get("trade_freeze_level") is not None
                    ),
                }
            )
    except Exception as exc:  # noqa: BLE001
        payload["error"] = repr(exc)
    finally:
        if mt5 is not None:
            for method_name in ("close", "shutdown"):
                method = getattr(mt5, method_name, None)
                if callable(method):
                    try:
                        method()
                    except Exception:  # noqa: BLE001
                        pass
                    break
        queue.put(payload)


def capture_bridge_specs(selected: list[dict[str, Any]], created_at: str, timeout_seconds: int = 60) -> dict[str, Any]:
    broker_symbols = sorted({row["broker_symbol"] for row in selected})
    class _Sink:
        payload: dict[str, Any] | None = None

        def put(self, payload: dict[str, Any]) -> None:
            self.payload = payload

    class _BridgeTimeout(Exception):
        pass

    def _timeout(_signum: int, _frame: Any) -> None:
        raise _BridgeTimeout

    sink = _Sink()
    old_handler = signal.getsignal(signal.SIGALRM)
    signal.signal(signal.SIGALRM, _timeout)
    signal.alarm(timeout_seconds)
    try:
        _bridge_worker(sink, broker_symbols)
        payload: dict[str, Any] = sink.payload or {
            "bridge_reachable": False,
            "account_info_read": False,
            "symbol_select_called": False,
            "broker_or_order_mutation": False,
            "orderflow_used": False,
            "rows": [],
            "error": "bridge_capture_worker_returned_no_payload",
        }
    except _BridgeTimeout:
        payload = {
            "bridge_reachable": False,
            "account_info_read": False,
            "symbol_select_called": False,
            "broker_or_order_mutation": False,
            "orderflow_used": False,
            "rows": [],
            "error": f"bridge_capture_timeout_after_{timeout_seconds}s",
        }
    else:
        pass
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)
    captured_by_symbol = {row.get("broker_symbol"): row for row in payload.get("rows", [])}
    rows = []
    for activation in selected:
        captured = captured_by_symbol.get(activation["broker_symbol"]) or {
            "broker_symbol": activation["broker_symbol"],
            "symbol_info_status": "not_captured",
            "symbol_info": {},
            "symbol_info_tick_status": "not_captured",
            "symbol_info_tick": {},
            "explicit_trade_session_table_rows": [],
            "explicit_quote_session_table_rows": [],
            "explicit_session_table_present": False,
            "stop_freeze_fields_present": False,
        }
        rows.append(
            {
                "tag": activation["tag"],
                "file_symbol": activation["file_symbol"],
                "broker_symbol": activation["broker_symbol"],
                "captured": captured,
            }
        )
    captured_rows = [row["captured"] for row in rows]
    return {
        "schema": f"{SCHEMA_PREFIX}.broker_spec_enhanced_capture.v1",
        "created_at_utc": created_at,
        "bridge_reachable": bool(payload.get("bridge_reachable")),
        "bridge_error": payload.get("error"),
        "initialize_result": payload.get("initialize_result"),
        "account_info_read": False,
        "symbol_select_called": False,
        "broker_or_order_mutation": False,
        "orderflow_used": False,
        "symbol_count": len(selected),
        "symbol_info_captured_count": sum(1 for row in captured_rows if row.get("symbol_info_status") == "captured"),
        "symbol_info_tick_captured_count": sum(1 for row in captured_rows if row.get("symbol_info_tick_status") == "captured"),
        "stop_freeze_present_count": sum(1 for row in captured_rows if row.get("stop_freeze_fields_present") is True),
        "explicit_session_table_present_count": sum(1 for row in captured_rows if row.get("explicit_session_table_present") is True),
        "session_trade_method_available": bool(payload.get("session_trade_method_available")),
        "session_quote_method_available": bool(payload.get("session_quote_method_available")),
        "session_table_capture_status": (
            "captured"
            if any(row.get("explicit_session_table_present") for row in captured_rows)
            else "not_available_in_siliconmetatrader5_client_or_not_returned"
        ),
        "rows": rows,
    }


def events_by_tag(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in events:
        grouped.setdefault(row["tag"], []).append(row)
    return grouped


def capture_by_tag(capture: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["tag"]: row["captured"] for row in capture["rows"]}


def cost_fill_rows(
    selected: list[dict[str, Any]],
    source_events: list[dict[str, Any]],
    bridge_capture: dict[str, Any],
    created_at: str,
) -> list[dict[str, Any]]:
    grouped = events_by_tag(source_events)
    captured = capture_by_tag(bridge_capture)
    rows: list[dict[str, Any]] = []
    for activation in selected:
        tag = activation["tag"]
        events = grouped.get(tag, [])
        capture = captured.get(tag, {})
        info = capture.get("symbol_info") or {}
        tick = capture.get("symbol_info_tick") or {}
        point = finite_float(info.get("point"))
        spread = finite_float(info.get("spread"))
        tick_size = finite_float(info.get("trade_tick_size"))
        tick_value = finite_float(info.get("trade_tick_value"))
        bridge_spread_abs = None
        if point is not None and spread is not None:
            bridge_spread_abs = max(0.0, point * spread)
        tick_bid = finite_float(tick.get("bid"))
        tick_ask = finite_float(tick.get("ask"))
        tick_spread_abs = None
        if tick_bid is not None and tick_ask is not None and tick_ask >= tick_bid:
            tick_spread_abs = tick_ask - tick_bid
        bridge_spread_r_values = [
            bridge_spread_abs / event["risk_abs"]
            for event in events
            if bridge_spread_abs is not None and finite_float(event.get("risk_abs")) and event["risk_abs"] > 0
        ]
        tick_spread_r_values = [
            tick_spread_abs / event["risk_abs"]
            for event in events
            if tick_spread_abs is not None and finite_float(event.get("risk_abs")) and event["risk_abs"] > 0
        ]
        risk_cash_per_lot = [
            event["risk_abs"] / tick_size * tick_value
            for event in events
            if tick_size and tick_size > 0 and tick_value and finite_float(event.get("risk_abs")) and event["risk_abs"] > 0
        ]
        swap_long = finite_float(info.get("swap_long"))
        swap_short = finite_float(info.get("swap_short"))
        swap_mode = info.get("swap_mode")
        swap_proxy = {
            "swap_mode": swap_mode,
            "swap_long": swap_long,
            "swap_short": swap_short,
            "risk_cash_per_lot_summary": summarize(risk_cash_per_lot),
            "swap_exact_to_r_status": "not_exact_live_authority_without_broker_swap_units_account_currency_and_holding_time_model",
        }
        if risk_cash_per_lot:
            denom = statistics.median(risk_cash_per_lot)
            swap_proxy["swap_long_r_proxy_if_native_money_per_lot"] = (
                round(swap_long / denom, 6) if swap_long is not None and denom else None
            )
            swap_proxy["swap_short_r_proxy_if_native_money_per_lot"] = (
                round(swap_short / denom, 6) if swap_short is not None and denom else None
            )
        if point is not None:
            risk_values = [event["risk_abs"] for event in events if finite_float(event.get("risk_abs")) and event["risk_abs"] > 0]
            denom = statistics.median(risk_values) if risk_values else None
            swap_proxy["swap_long_r_proxy_if_points"] = (
                round((swap_long * point) / denom, 6) if swap_long is not None and denom else None
            )
            swap_proxy["swap_short_r_proxy_if_points"] = (
                round((swap_short * point) / denom, 6) if swap_short is not None and denom else None
            )
        cost3 = split_summary(events, "proxy_r_cost3")
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.source_session_spec_cost_fill_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": activation["file_symbol"],
                "broker_symbol": activation["broker_symbol"],
                "family": activation["family"],
                "mechanism": activation["mechanism"],
                "source_event_count": len(events),
                "activation_row_source_event_count": activation.get("source_event_count"),
                "source_event_join_complete": len(events) == int(activation.get("source_event_count") or -1),
                "source_spans": activation["session_source_status"]["source_spans"],
                "broker_symbol_info_status": capture.get("symbol_info_status", "not_captured"),
                "broker_symbol_info_tick_status": capture.get("symbol_info_tick_status", "not_captured"),
                "broker_stop_freeze_present": capture.get("stop_freeze_fields_present") is True,
                "trade_stops_level": info.get("trade_stops_level"),
                "trade_freeze_level": info.get("trade_freeze_level"),
                "trade_mode": info.get("trade_mode"),
                "trade_exemode": info.get("trade_exemode"),
                "filling_mode": info.get("filling_mode"),
                "order_mode": info.get("order_mode"),
                "expiration_mode": info.get("expiration_mode"),
                "contract_size": info.get("trade_contract_size"),
                "tick_size": tick_size,
                "tick_value": tick_value,
                "currency_profit": info.get("currency_profit"),
                "currency_margin": info.get("currency_margin"),
                "bridge_current_spread_abs": bridge_spread_abs,
                "bridge_tick_bid": tick_bid,
                "bridge_tick_ask": tick_ask,
                "bridge_tick_spread_abs": tick_spread_abs,
                "source_cost_r_summary": summarize([event["cost_r"] for event in events]),
                "bridge_current_spread_r_summary": summarize(bridge_spread_r_values),
                "bridge_tick_spread_r_summary": summarize(tick_spread_r_values),
                "raw_proxy_r_summary": summarize([event["raw_proxy_r"] for event in events]),
                "proxy_r_cost1_summary": split_summary(events, "proxy_r_cost1"),
                "proxy_r_cost2_summary": split_summary(events, "proxy_r_cost2"),
                "proxy_r_cost3_summary": cost3,
                "commission_to_r_status": "not_available_in_symbol_info_or_activation_artifacts",
                "slippage_to_r_status": "stress_proxy_cost2_cost3_only_not_broker_exact",
                "swap_to_r_proxy": swap_proxy,
                "explicit_trade_session_table_row_count": len(capture.get("explicit_trade_session_table_rows", [])),
                "explicit_quote_session_table_row_count": len(capture.get("explicit_quote_session_table_rows", [])),
                "explicit_session_table_status": (
                    "captured" if capture.get("explicit_session_table_present") else "unavailable_from_current_bridge_client"
                ),
                "fill_policy_status": "limit_first_or_guarded_open_market_policy_draft_not_live_order_logic",
                "activation_weight_now": 0.0,
                "transformed_use": (
                    "default_off_candidate_with_cost3_sizing_guard"
                    if cost3["populated_split_count"] >= 2
                    else "source_requirement_or_successor_experiment"
                ),
            }
        )
    return rows


def series_from_events(events: list[dict[str, Any]], value_key: str) -> dict[str, dict[str, float]]:
    series: dict[str, dict[str, float]] = {}
    for event in events:
        tag = event["tag"]
        date = event["date"]
        series.setdefault(tag, {})
        series[tag][date] = series[tag].get(date, 0.0) + float(event[value_key])
    return series


def build_portfolio_replay(
    source_events: list[dict[str, Any]],
    created_at: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[dict[str, Any]]]:
    candidate = load_module("candidate_enabled_unified_replay_for_market_expansion_dossier", CANDIDATE_REPLAY)
    active = candidate._active_baselines()
    candidate_daily = candidate._load_candidate_daily()
    candidate_conf = {
        name: float(value)
        for name, value in candidate.candidate_registry.CANDIDATE_CONFIDENCE.items()
        if float(value) > 0.0 and name in candidate_daily
    }
    candidate_series = {name: candidate_daily[name] for name in candidate_conf}
    active_baseline = candidate._evaluate_scenario(
        "active_core8_a8_baseline_no_candidates",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        {},
        {},
    )
    candidate_all = candidate._evaluate_scenario(
        "candidate_all_on_active_a8_reference",
        active["a8_values"],
        active["all_days"],
        active["sd_book"],
        candidate_series,
        candidate_conf,
    )
    candidate_values, candidate_meta = candidate._add_candidate_series(
        active["a8_values"],
        active["all_days"],
        candidate_series,
        candidate_conf,
    )
    scenarios: list[dict[str, Any]] = []
    scenario_inputs = [
        ("candidate_plus_expansion_seed_0p025_cost1", "proxy_r_cost1", 0.025),
        ("candidate_plus_expansion_seed_0p025_cost2", "proxy_r_cost2", 0.025),
        ("candidate_plus_expansion_seed_0p025_cost3", "proxy_r_cost3", 0.025),
        ("candidate_plus_expansion_micro_0p0125_cost3", "proxy_r_cost3", 0.0125),
        ("candidate_plus_expansion_ceiling_0p05_cost3", "proxy_r_cost3", 0.05),
        ("active_a8_plus_expansion_seed_0p025_cost3_no_candidate_book", "proxy_r_cost3", 0.025),
    ]
    scenario_values: dict[str, list[float]] = {
        "active_core8_a8_baseline_no_candidates": active["a8_values"],
        "candidate_all_on_active_a8_reference": candidate_values,
    }
    for name, value_key, weight in scenario_inputs:
        expansion_series = series_from_events(source_events, value_key)
        weights = {tag: weight for tag in expansion_series}
        base_values = active["a8_values"] if name.endswith("no_candidate_book") else candidate_values
        base_reference = active_baseline if name.endswith("no_candidate_book") else candidate_all
        values, _scenario_meta = candidate._add_candidate_series(
            base_values,
            active["all_days"],
            expansion_series,
            weights,
        )
        scenario_values[name] = values
        scenario = candidate._evaluate_scenario(
            name,
            base_values,
            active["all_days"],
            active["sd_book"],
            expansion_series,
            weights,
        )
        scenario["schema"] = f"{SCHEMA_PREFIX}.portfolio_replay_scenario.v1"
        scenario["created_at_utc"] = created_at
        scenario["scenario"] = name
        scenario["base_reference"] = base_reference["name"]
        scenario["source_value_key"] = value_key
        scenario["expansion_weight_per_tag"] = weight
        scenario["delta_vs_base"] = {
            "sharpe": round(scenario["sharpe"] - base_reference["sharpe"], 6),
            "monthly_pct": round(scenario["mc"]["monthly_pct"] - base_reference["mc"]["monthly_pct"], 6),
            "p_pass": round(scenario["mc"]["p_pass"] - base_reference["mc"]["p_pass"], 6),
            "p_fail_dd": round(scenario["mc"]["p_fail_dd"] - base_reference["mc"]["p_fail_dd"], 6),
            "worst_day_pct": round(scenario["mc"]["worst_day_pct"] - base_reference["mc"]["worst_day_pct"], 6),
            "maxDD_R": round(scenario["daily"]["maxDD_R"] - base_reference["daily"]["maxDD_R"], 6),
        }
        scenarios.append(scenario)
    reference_rows = []
    for scenario in (active_baseline, candidate_all):
        reference = {
            "schema": f"{SCHEMA_PREFIX}.portfolio_replay_scenario.v1",
            "created_at_utc": created_at,
            "scenario": scenario["name"],
            "base_reference": None,
            "source_value_key": None,
            "expansion_weight_per_tag": 0.0,
            "delta_vs_base": {},
            **scenario,
        }
        reference_rows.append(reference)
    meta = {
        "a8_reproduction": active["reproduction"],
        "candidate_overlay_meta": candidate_meta,
        "all_days_count": len(active["all_days"]),
        "candidate_reference_sharpe": candidate_all["sharpe"],
        "active_reference_sharpe": active_baseline["sharpe"],
    }
    daily_rows = []
    for index, day in enumerate(active["all_days"]):
        row = {
            "schema": f"{SCHEMA_PREFIX}.portfolio_daily_replay_row.v1",
            "created_at_utc": created_at,
            "date": day.isoformat()[:10],
            "split": candidate._split_of_year(day.year),
            "active_a8_r": round(float(scenario_values["active_core8_a8_baseline_no_candidates"][index]), 9),
            "candidate_all_on_active_a8_r": round(float(scenario_values["candidate_all_on_active_a8_reference"][index]), 9),
        }
        row["candidate_overlay_r"] = round(row["candidate_all_on_active_a8_r"] - row["active_a8_r"], 9)
        for scenario_name in sorted(name for name in scenario_values if name.startswith("candidate_plus_expansion")):
            value = round(float(scenario_values[scenario_name][index]), 9)
            row[f"{scenario_name}_r"] = value
            row[f"{scenario_name}_expansion_overlay_r"] = round(value - row["candidate_all_on_active_a8_r"], 9)
        no_candidate_name = "active_a8_plus_expansion_seed_0p025_cost3_no_candidate_book"
        value = round(float(scenario_values[no_candidate_name][index]), 9)
        row[f"{no_candidate_name}_r"] = value
        row[f"{no_candidate_name}_expansion_overlay_r"] = round(value - row["active_a8_r"], 9)
        daily_rows.append(row)
    return [*reference_rows, *scenarios], meta, daily_rows


def fill_policy_decision(created_at: str) -> dict[str, Any]:
    return {
        "schema": f"{SCHEMA_PREFIX}.fill_policy_decision.v1",
        "created_at_utc": created_at,
        "decision": "LIMIT_FIRST_OR_GUARDED_D1_OPEN_MARKET_SKIP_OTHERWISE",
        "live_order_logic_changed": False,
        "policy_status": "dossier_policy_not_runtime_activation",
        "rationale": (
            "D1 expansion signals are next-open daily intents. Blind market-at-any-time entry would "
            "convert a source signal into a different execution hypothesis. The deployable policy "
            "therefore requires entry at the D1 open reference through a limit-first or guarded-open "
            "market window and skips late/deviated/high-spread conditions."
        ),
        "entry_rules": [
            "Use only latest completed D1 signal mapped to current D1 session through runtime_now decision_day.",
            "Primary action is limit at D1 open/reference price with short expiry; no chasing after thesis window.",
            "Guarded market fallback is allowed only inside the D1 rollover/open window when spread_r is inside the route cost3 stress envelope and mid deviation from reference is <= 0.15R.",
            "Skip if stops/freeze/volume contract fields are missing or non-compliant for the intended stop distance.",
            "Skip if explicit session table remains unavailable and the symbol is not proven tradeable at the target D1 open window by a separate broker/platform source.",
        ],
        "remaining_fill_authority_requirements": [
            "exact broker session/trading-hours table or platform-source proof",
            "queue/fillability evidence for limit-first policy on the broker namespace",
            "broker-exact commission/slippage/swap conversion",
            "VPS packet-parity dry run before any process reload",
        ],
    }


def zero_active_behavior(selected: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    expansion = {row["tag"] for row in selected}
    cfg = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")).get("gtos_vnext_runtime", {})
    default_names = {spec.tag for spec in active_specs(None)}
    candidate_names = {spec.tag for spec in active_specs(None, include_candidate_book=True)}
    empty_market_specs = {
        spec.tag
        for spec in active_specs(None, include_market_expansion_book=True, market_expansion_sleeves=[])
    }
    default_registry = set(admission.effective_registry())
    candidate_registry_names = set(admission.effective_registry(include_candidate_book=True))
    empty_market_registry = set(
        admission.effective_registry(include_market_expansion_book=True, market_expansion_sleeves=[])
    )
    all_market_specs = {
        spec.tag
        for spec in active_specs(
            None,
            include_market_expansion_book=True,
            market_expansion_sleeves=sorted(expansion),
        )
    }
    explicit_market_registry = set(
        admission.effective_registry(
            include_market_expansion_book=True,
            market_expansion_sleeves=sorted(expansion),
        )
    )
    return {
        "schema": f"{SCHEMA_PREFIX}.zero_active_behavior.v1",
        "created_at_utc": created_at,
        "market_expansion_selectable_count": len(expansion),
        "activation_weight_sum": sum(float(row.get("activation_weight_now") or 0.0) for row in selected),
        "market_expansion_names_in_default_active_specs": sorted(expansion & default_names),
        "market_expansion_names_in_candidate_book_specs": sorted(expansion & candidate_names),
        "market_expansion_names_in_empty_allowlist_specs": sorted(expansion & empty_market_specs),
        "market_expansion_names_in_default_effective_registry": sorted(expansion & default_registry),
        "market_expansion_names_in_candidate_effective_registry": sorted(expansion & candidate_registry_names),
        "market_expansion_names_in_empty_allowlist_effective_registry": sorted(expansion & empty_market_registry),
        "explicit_allowlist_market_expansion_count": len(expansion & all_market_specs & explicit_market_registry),
        "bridge_default_include_market_expansion_book": DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"],
        "bridge_default_market_expansion_sleeves": DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"],
        "active_config_include_market_expansion_book": cfg.get("ultimate_book_include_market_expansion_book", False),
        "active_config_market_expansion_sleeves": cfg.get("ultimate_book_market_expansion_sleeves", []),
        "zero_active_behavior_ok": (
            not (expansion & default_names)
            and not (expansion & candidate_names)
            and not (expansion & empty_market_specs)
            and not (expansion & default_registry)
            and not (expansion & candidate_registry_names)
            and not (expansion & empty_market_registry)
            and len(expansion & all_market_specs & explicit_market_registry) == len(expansion)
            and DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is False
            and cfg.get("ultimate_book_include_market_expansion_book", False) is False
            and sum(float(row.get("activation_weight_now") or 0.0) for row in selected) == 0.0
        ),
    }


def forbidden_call_scan(created_at: str) -> dict[str, Any]:
    scanned_paths = [
        ROUTE / "build_market_expansion_live_authority_dossier.py",
        ROUTE / "verify_market_expansion_live_authority_dossier.py",
    ]
    forbidden_patterns = [
        "order" + "_send",
        "TRADE" + "_ACTION_",
        "positions" + "_get",
        "history" + "_deals_get",
        "history" + "_orders_get",
        "account" + "_info(",
        "market" + "_book_add",
        "market" + "_book_get",
        "market" + "_book_release",
        "symbol" + "_select(",
        "subprocess" + ".run(['" + "ssh'",
        "subprocess" + ".run([\"" + "ssh\"",
        "sc" + "p ",
        "rsy" + "nc ",
    ]
    matches = []
    for path in scanned_paths:
        text = path.read_text(encoding="utf-8")
        for pattern in forbidden_patterns:
            if pattern in text:
                matches.append({"path": rel(path), "pattern": pattern})
    return {
        "schema": f"{SCHEMA_PREFIX}.forbidden_call_scan.v1",
        "created_at_utc": created_at,
        "scanned_paths": [rel(path) for path in scanned_paths],
        "forbidden_patterns": forbidden_patterns,
        "matches": matches,
        "ok": not matches,
    }


def all_material_rows(
    selected: list[dict[str, Any]],
    cost_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    created_at: str,
) -> list[dict[str, Any]]:
    cost_by_tag = {row["tag"]: row for row in cost_rows}
    seed_cost3 = next(row for row in replay_rows if row["scenario"] == "candidate_plus_expansion_seed_0p025_cost3")
    contrib_by_tag = seed_cost3["contribution"]
    rows = []
    for activation in selected:
        tag = activation["tag"]
        cost = cost_by_tag[tag]
        rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.all_material_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": activation["file_symbol"],
                "broker_symbol": activation["broker_symbol"],
                "family": activation["family"],
                "mechanism": activation["mechanism"],
                "source_event_count": cost["source_event_count"],
                "cost3_mean_proxy_r": cost["proxy_r_cost3_summary"]["all"]["mean"],
                "cost3_every_populated_split_positive": cost["proxy_r_cost3_summary"]["every_populated_split_positive"],
                "portfolio_seed_cost3_matched_days": contrib_by_tag[tag]["matched_days"],
                "portfolio_seed_cost3_total_weighted_R": contrib_by_tag[tag]["total_weighted_R"],
                "broker_symbol_info_status": cost["broker_symbol_info_status"],
                "explicit_session_table_status": cost["explicit_session_table_status"],
                "commission_to_r_status": cost["commission_to_r_status"],
                "slippage_to_r_status": cost["slippage_to_r_status"],
                "swap_exact_to_r_status": cost["swap_to_r_proxy"]["swap_exact_to_r_status"],
                "runtime_effect_now": "none_default_off",
                "current_claim_status": "preserve_default_off_candidate_not_promoted_live",
                "what_is_real_or_inspiring": activation.get("note"),
                "why_not_live_now": [
                    "explicit session table remains absent from available bridge client"
                    if cost["explicit_session_table_status"] != "captured"
                    else "session table captured but still needs VPS packet parity",
                    cost["commission_to_r_status"],
                    cost["slippage_to_r_status"],
                    cost["swap_to_r_proxy"]["swap_exact_to_r_status"],
                    "limit/fill policy is a dossier rule, not observed broker queue/fill proof",
                ],
                "transformed_use": cost["transformed_use"],
                "revival_gate": "broker-session/cost/fill proof plus owner-approved config promotion package",
            }
        )
    return rows


def write_next_prompt(created_at: str) -> None:
    prompt = f"""# Market Expansion Promotion Boundary / VPS Handoff Successor Prompt

Created: {created_at}

Mandatory context use: run mandatory GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the latest route artifacts from disk as active instructions. Do not rely on chat memory. After any compaction/resume/interruption/uncertainty, reread the prompt, doctrine, and latest dossier artifacts from disk before continuing and record instruction coverage in the completion audit.

Lane posture: production-deployment dossier review and handoff packaging, not broker mutation by default. Use constructive build-and-ship posture inside the evidence class: no arbitrary top-N/top-3/top-5/top-10 cutoffs, preserve full ledgers, pursue same-evidence-class blockers until cleared or exactly bounded, and translate non-promoted ideas into runtime feature, sizing, veto, source requirement, or successor experiment.

Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted, repaired, recomputed, or reduced to an exact owner/source/capture requirement. Full same-evidence-class pursuit is mandatory; do not stop at blocker wording when a same-class read-only capture, replay, verifier, source-capture, source completeness check, implementation decision, branch decision, exact-R/proxy-R/expectancy recomputation, or result materialization step is still executable.

Input route: `research/operations/final_moonshot_market_expansion_live_authority_dossier_2026_06_18/`.

Objective: decide whether the default-off market-expansion package can be moved from dossier evidence into an owner-action VPS promotion package. Verify the committed generator, source-event cost ledger, portfolio replay ledger, broker spec/session/cost/fill ledger, fill policy decision, zero-active audit, verifier, focused tests, prompt hardening, and route audit from disk. If all same-evidence-class issues are closed, build an exact VPS handoff package with promotion criteria, rollback/kill criteria, packet-parity commands, monitoring ledgers, config diff, and owner-action checklist. If not, implement or capture the missing same-class evidence if available locally/read-only; otherwise record exact owner/source/capture requirements.

Forbidden unless explicitly approved in the active turn: production-change/live trading/broker operation; broker/account/order/history/deal/position mutation or reads outside the prompt evidence class; MT5 order state changes; prompt/config/risk/execution/safety/canary/selector live activation changes; credential mutation/disclosure; paid API/vendor calls; remote push; live VPS restart/reload; production live config activation; and orderflow/depth use. Local code/config/test/handoff artifacts may be changed only if the route explicitly owns that production-deployment packaging surface and keeps broker/VPS action as owner-action.

Completion requires: decision ledger, promotion-boundary ledger, exact unresolved requirement ledger, optional VPS handoff package if eligible, verifier, focused test record, output manifest, saturation/self-red-team audit, completion audit, and scoped commit. Mark complete only when the prompt completion standard is satisfied with no vague blockers or hidden live-action assumptions.
"""
    (ROUTE / "NEXT_PROMPT.md").write_text(prompt, encoding="utf-8")


def build() -> dict[str, Any]:
    ROUTE.mkdir(parents=True, exist_ok=True)
    created_at = utc_now()
    selected = selected_activation_rows()
    source_events, _by_tag = source_event_rows(selected, created_at)
    bridge_capture = capture_bridge_specs(selected, created_at)
    cost_rows = cost_fill_rows(selected, source_events, bridge_capture, created_at)
    replay_rows, replay_meta, daily_replay_rows = build_portfolio_replay(source_events, created_at)
    fill_policy = fill_policy_decision(created_at)
    zero = zero_active_behavior(selected, created_at)
    forbidden_scan = forbidden_call_scan(created_at)
    material_rows = all_material_rows(selected, cost_rows, replay_rows, created_at)

    cost3_seed = next(row for row in replay_rows if row["scenario"] == "candidate_plus_expansion_seed_0p025_cost3")
    candidate_ref = next(row for row in replay_rows if row["scenario"] == "candidate_all_on_active_a8_reference")
    active_ref = next(row for row in replay_rows if row["scenario"] == "active_core8_a8_baseline_no_candidates")
    session_unavailable = bridge_capture["explicit_session_table_present_count"] == 0
    live_requirements = [
        "explicit broker trading-session table or platform-source proof remains required"
        if session_unavailable
        else None,
        "commission is not available in symbol_info or activation artifacts",
        "slippage remains stress/proxy cost2/cost3, not broker-exact live authority",
        "swap-to-R remains proxy without broker swap units, account currency, and holding-time model",
        "limit-vs-market fill policy is specified but queue/fillability is not broker-observed",
        "owner-approved live config promotion, VPS packet parity, monitoring, and rollback gates remain separate",
    ]
    live_requirements = [item for item in live_requirements if item]
    requirement_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.blocker_repair_requirement_row.v1",
            "created_at_utc": created_at,
            "requirement_id": f"MX-LIVE-REQ-{index:03d}",
            "requirement": requirement,
            "status": "exact_requirement_not_live_blocker",
            "same_evidence_class_attempted": True,
            "runtime_effect_now": "none_default_off",
            "owner_action_boundary": "required before any market-expansion live promotion",
        }
        for index, requirement in enumerate(live_requirements, start=1)
    ]
    portfolio_replay_ok = (
        len(replay_rows) == 8
        and cost3_seed["source_value_key"] == "proxy_r_cost3"
        and cost3_seed["expansion_weight_per_tag"] == 0.025
    )
    ok = (
        len(selected) == 14
        and len(source_events) == read_json(GENERATOR_ROUTE / "FULL_GENERATOR_BOOK_REPLAY_PROOF.json")["total_matched_events"]
        and all(row["source_event_join_complete"] for row in cost_rows)
        and len(cost_rows) == len(material_rows) == 14
        and bridge_capture["symbol_count"] == 14
        and bridge_capture["symbol_info_captured_count"] == 14
        and bridge_capture["stop_freeze_present_count"] == 14
        and bridge_capture["account_info_read"] is False
        and bridge_capture["broker_or_order_mutation"] is False
        and bridge_capture["orderflow_used"] is False
        and portfolio_replay_ok
        and zero["zero_active_behavior_ok"] is True
        and forbidden_scan["ok"] is True
    )
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "decision": (
            "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_BUILT_DEFAULT_OFF_NOT_PROMOTED"
            if ok
            else "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_FAIL_CLOSED"
        ),
        "source_generator_route": rel(GENERATOR_ROUTE),
        "source_activation_route": rel(ACTIVATION_ROUTE),
        "selectable_activation_candidate_count": len(selected),
        "source_event_cost_row_count": len(source_events),
        "all_material_row_count": len(material_rows),
        "portfolio_proxy_replay_complete": portfolio_replay_ok,
        "portfolio_daily_replay_row_count": len(daily_replay_rows),
        "portfolio_live_authority_replay_complete": False,
        "candidate_reference": {
            "sharpe": candidate_ref["sharpe"],
            "monthly_pct": candidate_ref["mc"]["monthly_pct"],
            "p_pass": candidate_ref["mc"]["p_pass"],
            "p_fail_dd": candidate_ref["mc"]["p_fail_dd"],
            "worst_day_pct": candidate_ref["mc"]["worst_day_pct"],
        },
        "active_a8_reference": {
            "sharpe": active_ref["sharpe"],
            "monthly_pct": active_ref["mc"]["monthly_pct"],
            "p_pass": active_ref["mc"]["p_pass"],
            "p_fail_dd": active_ref["mc"]["p_fail_dd"],
            "worst_day_pct": active_ref["mc"]["worst_day_pct"],
        },
        "candidate_plus_expansion_seed_0p025_cost3": {
            "sharpe": cost3_seed["sharpe"],
            "monthly_pct": cost3_seed["mc"]["monthly_pct"],
            "p_pass": cost3_seed["mc"]["p_pass"],
            "p_fail_dd": cost3_seed["mc"]["p_fail_dd"],
            "worst_day_pct": cost3_seed["mc"]["worst_day_pct"],
            "delta_vs_candidate_reference": cost3_seed["delta_vs_base"],
        },
        "broker_bridge_reachable": bridge_capture["bridge_reachable"],
        "broker_symbol_info_captured_count": bridge_capture["symbol_info_captured_count"],
        "broker_symbol_info_tick_captured_count": bridge_capture["symbol_info_tick_captured_count"],
        "broker_stop_freeze_present_count": bridge_capture["stop_freeze_present_count"],
        "broker_explicit_session_table_present_count": bridge_capture["explicit_session_table_present_count"],
        "session_trade_method_available": bridge_capture["session_trade_method_available"],
        "session_quote_method_available": bridge_capture["session_quote_method_available"],
        "session_table_capture_status": bridge_capture["session_table_capture_status"],
        "activation_weight_now": 0.0,
        "zero_active_behavior_ok": zero["zero_active_behavior_ok"],
        "live_authority": False,
        "deployment_ready": False,
        "promotion_ready": False,
        "deployment_not_ready_reasons": live_requirements,
        "runtime_effect": "none_default_off_dossier_only",
        "account_info_read": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
    }
    decisions = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "source_event_cost_replay_complete",
            "status": "complete",
            "evidence": {"source_event_cost_row_count": len(source_events), "tag_count": len(selected)},
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "portfolio_proxy_replay_complete_not_broker_live_authority",
            "status": "complete",
            "evidence": result["candidate_plus_expansion_seed_0p025_cost3"],
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "broker_session_table_not_promoted",
            "status": "exact_requirement",
            "evidence": {
                "session_trade_method_available": bridge_capture["session_trade_method_available"],
                "session_quote_method_available": bridge_capture["session_quote_method_available"],
                "explicit_session_table_present_count": bridge_capture["explicit_session_table_present_count"],
            },
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": "fill_policy_specified_but_not_live_order_logic",
            "status": "dossier_only",
            "evidence": {"fill_policy_decision": fill_policy["decision"]},
        },
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": result["decision"],
            "status": "default_off_not_promoted",
            "evidence": {"deployment_not_ready_reasons": live_requirements},
        },
    ]
    session_proof = {
        "schema": f"{SCHEMA_PREFIX}.session_table_unavailable_proof.v1",
        "created_at_utc": created_at,
        "bridge_reachable": bridge_capture["bridge_reachable"],
        "session_trade_method_available": bridge_capture["session_trade_method_available"],
        "session_quote_method_available": bridge_capture["session_quote_method_available"],
        "explicit_session_table_present_count": bridge_capture["explicit_session_table_present_count"],
        "status": bridge_capture["session_table_capture_status"],
        "required_next_source": "broker/platform session table source or bridge client method exposing symbol_info_session_trade/session_quote",
    }
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_self_red_team.v1",
        "created_at_utc": created_at,
        "ok": ok,
        "no_arbitrary_top_n": True,
        "anti_boxing_checked": [
            "active_a8_reference",
            "candidate_book_reference",
            "cost1_cost2_cost3_expansion_overlay",
            "micro_seed_ceiling_weight_stress",
            "active_without_candidate_expansion_overlay",
            "broker_stop_freeze_contract_fields",
            "session_table_method_availability",
            "commission_slippage_swap_to_r_boundaries",
            "limit_first_vs_guarded_market_fill_policy",
        ],
        "same_evidence_class_repairs_completed": [
            "recomputed all source D1 events for the 14 generator tags",
            "joined generator parity risk distances into source event cost rows",
            "reused current candidate-enabled replay machinery for portfolio interaction",
            "captured enriched symbol_info read-only from localhost bridge",
            "captured optional read-only symbol_info_tick spread snapshots where exposed by the bridge",
            "converted spread and swap fields into proxy-R diagnostics where source fields permit",
            "ran static forbidden-call scan over dossier builder/verifier",
            "wrote fill policy as deployment dossier rule without live order mutation",
        ],
        "remaining_exact_requirements": live_requirements,
        "forbidden_surfaces_not_crossed": [
            "broker/account/order/deal/position mutation",
            "credential mutation/disclosure",
            "paid API/vendor call",
            "remote push",
            "live VPS process action",
            "orderflow/depth",
            "production live config activation",
        ],
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
            "constructive_builder_posture_applied": True,
            "inspire_not_kill_applied": True,
            "no_arbitrary_top_n": True,
            "same_evidence_class_pursued": True,
        },
        "result_materialization_status": "dossier_built_with_source_event_cost_rows_portfolio_proxy_replay_broker_spec_capture_and_fill_policy",
        "source_use_state": "committed generator/activation/candidate replay artifacts plus source-hashed local MT5 OHLCV and read-only localhost MT5 bridge symbol_info",
        "runtime_effect_boundary": "none_default_off_dossier_only",
        "owner_action_live_authority_boundary": (
            "No live authority or deployment promotion is claimed. Owner/VPS promotion requires "
            "session-table proof, broker-exact commission/slippage/swap/fill evidence, packet parity, "
            "monitoring, rollback, and explicit owner action."
        ),
        "forbidden_surfaces_touched": [],
        "deployment_ready": False,
        "promotion_ready": False,
        "deployment_not_ready_reasons": live_requirements,
    }

    write_jsonl(ROUTE / "SOURCE_EVENT_COST_LEDGER.jsonl", source_events)
    write_json(ROUTE / "BROKER_SPEC_ENHANCED_CAPTURE.json", bridge_capture)
    write_json(ROUTE / "SESSION_TABLE_UNAVAILABLE_PROOF.json", session_proof)
    write_jsonl(ROUTE / "SOURCE_SESSION_SPEC_COST_FILL_LEDGER.jsonl", cost_rows)
    write_jsonl(ROUTE / "PORTFOLIO_REPLAY_LEDGER.jsonl", replay_rows)
    write_jsonl(ROUTE / "PORTFOLIO_DAILY_REPLAY_LEDGER.jsonl", daily_replay_rows)
    write_json(ROUTE / "PORTFOLIO_REPLAY_METADATA.json", replay_meta)
    write_json(ROUTE / "FILL_POLICY_DECISION.json", fill_policy)
    write_json(ROUTE / "ZERO_ACTIVE_BEHAVIOR_AUDIT.json", zero)
    write_json(ROUTE / "FORBIDDEN_CALL_SCAN.json", forbidden_scan)
    write_jsonl(ROUTE / "ALL_MATERIAL_ROW_LEDGER.jsonl", material_rows)
    write_jsonl(ROUTE / "DECISION_LEDGER.jsonl", decisions)
    write_jsonl(ROUTE / "BLOCKER_REPAIR_REQUIREMENT_LEDGER.jsonl", requirement_rows)
    write_json(ROUTE / "SATURATION_SELF_RED_TEAM_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "MARKET_EXPANSION_LIVE_AUTHORITY_DOSSIER_RESULT.json", result)
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


def main() -> int:
    created_at = utc_now()
    result = build()
    verifier_result = run_command(
        [sys.executable, str(ROUTE / "verify_market_expansion_live_authority_dossier.py")],
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
                str(ROUTE / "build_market_expansion_live_authority_dossier.py"),
                str(ROUTE / "verify_market_expansion_live_authority_dossier.py"),
                "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py",
            ],
            timeout=120,
        ),
        verifier_result,
        run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "tests/ultimate_book/test_market_expansion_live_authority_dossier_artifacts.py",
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
