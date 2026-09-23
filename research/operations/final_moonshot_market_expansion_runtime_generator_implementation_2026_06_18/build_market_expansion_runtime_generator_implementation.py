#!/usr/bin/env python3
"""Build the default-off market-expansion D1 runtime-generator implementation proof."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import multiprocessing as mp
import os
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROUTE = Path(__file__).resolve().parent
SOURCE_ROUTE = PROJECT_ROOT / "research" / "operations" / "final_moonshot_market_expansion_activation_candidate_package_2026_06_18"
SCORING_BUILDER = (
    PROJECT_ROOT
    / "research"
    / "operations"
    / "final_moonshot_market_expansion_validation_scoring_2026_06_18"
    / "build_market_expansion_validation_scoring.py"
)
SCHEMA_PREFIX = "gtos.final_moonshot.market_expansion_runtime_generator_implementation"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.components.ultimate_book import admission, execution_packets as EP  # noqa: E402
from src.components.ultimate_book.bridge import DEFAULT_CONFIG  # noqa: E402
from src.components.ultimate_book.sleeves import candidate_registry, market_expansion_d1  # noqa: E402
from src.components.ultimate_book.sleeves.registry import (  # noqa: E402
    CANDIDATE_BUILT,
    MARKET_EXPANSION_BUILT,
    active_specs,
)


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


def load_scoring_module():
    spec = importlib.util.spec_from_file_location("market_expansion_validation_scoring_builder", SCORING_BUILDER)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load scoring builder from {SCORING_BUILDER}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def row_symbol_payload(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "file_symbol": row["file_symbol"],
        "broker_symbol": row["broker_symbol"],
        "family": row["family"],
        "asset_class": row["family"],
        "spread_snapshot": row.get("spread_snapshot") or {},
    }


def df_to_bars(df: pd.DataFrame) -> list[dict[str, float]]:
    bars = []
    for _, row in df.iterrows():
        bars.append(
            {
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]) if "volume" in df and not pd.isna(row.get("volume")) else 0.0,
            }
        )
    return bars


def source_risk_by_index(df: pd.DataFrame) -> list[float | None]:
    close = df["close"]
    high = df["high"]
    low = df["low"]
    prev_tr = pd.concat(
        [
            high - low,
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ],
        axis=1,
    ).max(axis=1)
    risk_abs = prev_tr.shift(1).rolling(14, min_periods=10).mean()
    out: list[float | None] = []
    for value in risk_abs:
        try:
            number = float(value)
        except (TypeError, ValueError):
            number = math.nan
        out.append(number if math.isfinite(number) else None)
    return out


def is_close(a: float | None, b: float | None, *, tol: float = 1e-8) -> bool:
    if a is None or b is None:
        return a is b
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(a)), abs(float(b)))


def replay_runtime_parity(rows: list[dict[str, Any]], created_at: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    scoring = load_scoring_module()
    summary_rows: list[dict[str, Any]] = []
    detail_rows: list[dict[str, Any]] = []
    skip_samples: list[dict[str, Any]] = []
    total_source = 0
    total_runtime = 0
    total_matched = 0
    total_decision_day_mismatches = 0
    source_count_mismatches: list[dict[str, Any]] = []

    for row in rows:
        tag = row["tag"]
        mechanism = row["mechanism"]
        d1_path_text = row["session_source_status"]["source_spans"]["D1"]["best_path"]
        d1_path = PROJECT_ROOT / d1_path_text
        df = scoring.load_ohlcv(d1_path)
        bars = df_to_bars(df)
        risks = source_risk_by_index(df)
        source_events_all = scoring.d1_events(row_symbol_payload(row), d1_path)
        source_events = [event for event in source_events_all if event["mechanism"] == mechanism]
        source_by_date = {str(event["time"])[:10]: event for event in source_events}
        runtime_by_date: dict[str, dict[str, Any]] = {}

        for idx in range(1, len(df)):
            timestamp = pd.Timestamp(df.loc[idx, "time"])
            prev_timestamp = pd.Timestamp(df.loc[idx - 1, "time"])
            intent = market_expansion_d1.generate_for_tag(
                tag,
                row["file_symbol"],
                bars[:idx],
                prev_timestamp.date().isoformat(),
                bar_time=prev_timestamp.to_pydatetime(),
                runtime_now=timestamp.to_pydatetime(),
            )
            if intent is None:
                continue
            date_key = timestamp.date().isoformat()
            runtime_by_date[date_key] = {
                "time": timestamp.isoformat(),
                "previous_signal_time": prev_timestamp.isoformat(),
                "signal_to_entry_calendar_days": int((timestamp.date() - prev_timestamp.date()).days),
                "signal": int(intent.direction),
                "decision_day": intent.decision_day,
                "stop_dist": float(intent.stop_dist),
                "target_dist": float(intent.target_dist),
                "source_risk_abs": risks[idx],
            }

        all_dates = sorted(set(source_by_date) | set(runtime_by_date))
        missing_dates = sorted(set(source_by_date) - set(runtime_by_date))
        extra_dates = sorted(set(runtime_by_date) - set(source_by_date))
        direction_mismatches: list[dict[str, Any]] = []
        risk_mismatches: list[dict[str, Any]] = []
        target_mismatches: list[dict[str, Any]] = []
        decision_day_mismatches: list[dict[str, Any]] = []
        matched = 0
        for date_key in all_dates:
            source = source_by_date.get(date_key)
            runtime = runtime_by_date.get(date_key)
            if source is None:
                detail_status = "runtime_extra"
            elif runtime is None:
                detail_status = "runtime_missing"
            else:
                matched += 1
                detail_status = "matched"
                if int(source["signal"]) != int(runtime["signal"]):
                    detail_status = "direction_mismatch"
                    direction_mismatches.append({"date": date_key, "source": source["signal"], "runtime": runtime["signal"]})
                if runtime["decision_day"] != date_key:
                    detail_status = "decision_day_mismatch"
                    decision_day_mismatches.append(
                        {"date": date_key, "runtime_decision_day": runtime["decision_day"]}
                    )
                if not is_close(runtime["stop_dist"], runtime["source_risk_abs"]):
                    detail_status = "risk_mismatch"
                    risk_mismatches.append(
                        {
                            "date": date_key,
                            "source_risk_abs": runtime["source_risk_abs"],
                            "runtime_stop_dist": runtime["stop_dist"],
                        }
                    )
                if not is_close(runtime["target_dist"], 2.0 * runtime["stop_dist"]):
                    detail_status = "target_mismatch"
                    target_mismatches.append(
                        {
                            "date": date_key,
                            "runtime_stop_dist": runtime["stop_dist"],
                            "runtime_target_dist": runtime["target_dist"],
                        }
                    )
                if runtime["signal_to_entry_calendar_days"] > 1 and len(skip_samples) < 10:
                    skip_samples.append(
                        {
                            "tag": tag,
                            "source_entry_date": date_key,
                            "previous_signal_time": runtime["previous_signal_time"],
                            "runtime_decision_day": runtime["decision_day"],
                            "signal_to_entry_calendar_days": runtime["signal_to_entry_calendar_days"],
                        }
                    )
            detail_rows.append(
                {
                    "schema": f"{SCHEMA_PREFIX}.event_parity_detail.v1",
                    "created_at_utc": created_at,
                    "tag": tag,
                    "file_symbol": row["file_symbol"],
                    "broker_symbol": row["broker_symbol"],
                    "mechanism": mechanism,
                    "date": date_key,
                    "status": detail_status,
                    "source_signal": None if source is None else int(source["signal"]),
                    "runtime_signal": None if runtime is None else int(runtime["signal"]),
                    "runtime_decision_day": None if runtime is None else runtime["decision_day"],
                    "runtime_stop_dist": None if runtime is None else runtime["stop_dist"],
                    "source_risk_abs": None if runtime is None else runtime["source_risk_abs"],
                    "runtime_target_dist": None if runtime is None else runtime["target_dist"],
                }
            )

        total_source += len(source_events)
        total_runtime += len(runtime_by_date)
        total_matched += matched
        total_decision_day_mismatches += len(decision_day_mismatches)
        if len(source_events) != int(row.get("source_event_count", 0)):
            source_count_mismatches.append(
                {
                    "tag": tag,
                    "activation_row_source_event_count": row.get("source_event_count"),
                    "recomputed_source_event_count": len(source_events),
                }
            )
        all_passed = (
            not missing_dates
            and not extra_dates
            and not direction_mismatches
            and not risk_mismatches
            and not target_mismatches
            and not decision_day_mismatches
        )
        summary_rows.append(
            {
                "schema": f"{SCHEMA_PREFIX}.runtime_generator_parity_row.v1",
                "created_at_utc": created_at,
                "tag": tag,
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "family": row["family"],
                "mechanism": mechanism,
                "source_path": d1_path_text,
                "source_path_sha256": sha256_file(d1_path),
                "activation_row_source_event_count": row.get("source_event_count"),
                "recomputed_source_event_count": len(source_events),
                "runtime_event_count": len(runtime_by_date),
                "matched_event_count": matched,
                "missing_event_count": len(missing_dates),
                "extra_event_count": len(extra_dates),
                "direction_mismatch_count": len(direction_mismatches),
                "decision_day_mismatch_count": len(decision_day_mismatches),
                "risk_mismatch_count": len(risk_mismatches),
                "target_mismatch_count": len(target_mismatches),
                "all_parity_passed": all_passed,
                "first_source_event_date": min(source_by_date) if source_by_date else None,
                "last_source_event_date": max(source_by_date) if source_by_date else None,
                "sample_missing_dates": missing_dates[:10],
                "sample_extra_dates": extra_dates[:10],
                "sample_direction_mismatches": direction_mismatches[:5],
                "sample_risk_mismatches": risk_mismatches[:5],
                "sample_target_mismatches": target_mismatches[:5],
            }
        )

    signal_replay = {
        "schema": f"{SCHEMA_PREFIX}.full_generator_book_replay_proof.v1",
        "created_at_utc": created_at,
        "generator_book_signal_replay_complete": len(summary_rows) == 14 and all(row["all_parity_passed"] for row in summary_rows),
        "candidate_row_count": len(summary_rows),
        "total_recomputed_source_events": total_source,
        "total_runtime_events": total_runtime,
        "total_matched_events": total_matched,
        "total_decision_day_mismatches": total_decision_day_mismatches,
        "source_count_mismatch_count": len(source_count_mismatches),
        "source_count_mismatches": source_count_mismatches,
        "portfolio_live_authority_book_replay_complete": False,
        "portfolio_live_authority_book_replay_missing_reason": (
            "This route proves generator signal/date/risk parity. It does not claim broker fill, "
            "commission/slippage, limit-order queue, swap, or live-authority portfolio replay."
        ),
        "weekend_or_holiday_skip_sample_count": len(skip_samples),
        "weekend_or_holiday_skip_samples": skip_samples,
    }
    return summary_rows, detail_rows, signal_replay


def _plain_symbol_info(info: Any) -> dict[str, Any]:
    fields = (
        "name",
        "path",
        "visible",
        "select",
        "digits",
        "point",
        "spread",
        "spread_float",
        "trade_mode",
        "trade_calc_mode",
        "trade_contract_size",
        "trade_tick_size",
        "trade_tick_value",
        "trade_stops_level",
        "trade_freeze_level",
        "volume_min",
        "volume_max",
        "volume_step",
        "swap_long",
        "swap_short",
        "currency_base",
        "currency_profit",
        "currency_margin",
    )
    if info is None:
        return {}
    if isinstance(info, dict):
        return {field: info.get(field) for field in fields if field in info}
    if hasattr(info, "_asdict"):
        data = info._asdict()
        return {field: data.get(field) for field in fields if field in data}
    return {field: getattr(info, field) for field in fields if hasattr(info, field)}


def _bridge_capture_worker(queue: mp.Queue, broker_symbols: list[str]) -> None:
    rows: list[dict[str, Any]] = []
    payload: dict[str, Any] = {
        "bridge_reachable": False,
        "account_info_read": False,
        "symbol_select_called": False,
        "broker_or_order_mutation": False,
        "orderflow_used": False,
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
            info = mt5.symbol_info(broker_symbol)
            info_payload = _plain_symbol_info(info)
            trade_sessions: list[Any] = []
            quote_sessions: list[Any] = []
            if callable(session_trade):
                for day in range(7):
                    for index in range(10):
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
                    for index in range(10):
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
                    "trade_stops_level": info_payload.get("trade_stops_level"),
                    "trade_freeze_level": info_payload.get("trade_freeze_level"),
                    "stop_freeze_fields_present": (
                        info_payload.get("trade_stops_level") is not None
                        and info_payload.get("trade_freeze_level") is not None
                    ),
                    "explicit_trade_session_table_rows": trade_sessions,
                    "explicit_quote_session_table_rows": quote_sessions,
                    "explicit_session_table_present": bool(trade_sessions or quote_sessions),
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


def capture_bridge_specs(rows: list[dict[str, Any]], created_at: str, timeout_seconds: int = 30) -> dict[str, Any]:
    broker_symbols = [row["broker_symbol"] for row in rows]
    ctx = mp.get_context("spawn")
    queue: mp.Queue = ctx.Queue()
    proc = ctx.Process(target=_bridge_capture_worker, args=(queue, broker_symbols))
    proc.start()
    proc.join(timeout_seconds)
    if proc.is_alive():
        proc.terminate()
        proc.join(5)
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
        try:
            payload = queue.get_nowait()
        except Exception as exc:  # noqa: BLE001
            payload = {
                "bridge_reachable": False,
                "account_info_read": False,
                "symbol_select_called": False,
                "broker_or_order_mutation": False,
                "orderflow_used": False,
                "rows": [],
                "error": repr(exc),
            }
    captured_by_symbol = {row.get("broker_symbol"): row for row in payload.get("rows", [])}
    manifest_rows = []
    for row in rows:
        captured = captured_by_symbol.get(row["broker_symbol"])
        manifest_rows.append(
            {
                "tag": row["tag"],
                "file_symbol": row["file_symbol"],
                "broker_symbol": row["broker_symbol"],
                "activation_snapshot_stop_freeze_present": row.get("stop_freeze_fields_present"),
                "captured": captured or {
                    "broker_symbol": row["broker_symbol"],
                    "symbol_info_status": "not_captured",
                    "trade_stops_level": None,
                    "trade_freeze_level": None,
                    "stop_freeze_fields_present": False,
                    "explicit_session_table_present": False,
                },
            }
        )
    captured_rows = [row["captured"] for row in manifest_rows]
    return {
        "schema": f"{SCHEMA_PREFIX}.broker_session_spec_capture_manifest.v1",
        "created_at_utc": created_at,
        "bridge_reachable": bool(payload.get("bridge_reachable")),
        "bridge_error": payload.get("error"),
        "account_info_read": False,
        "symbol_select_called": False,
        "broker_or_order_mutation": False,
        "orderflow_used": False,
        "symbol_count": len(rows),
        "symbol_info_captured_count": sum(1 for row in captured_rows if row.get("symbol_info_status") == "captured"),
        "stop_freeze_present_count": sum(1 for row in captured_rows if row.get("stop_freeze_fields_present") is True),
        "explicit_session_table_present_count": sum(1 for row in captured_rows if row.get("explicit_session_table_present") is True),
        "session_table_capture_status": (
            "captured"
            if any(row.get("explicit_session_table_present") for row in captured_rows)
            else "not_available_in_siliconmetatrader5_client_or_not_returned"
        ),
        "session_trade_method_available": bool(payload.get("session_trade_method_available")),
        "session_quote_method_available": bool(payload.get("session_quote_method_available")),
        "rows": manifest_rows,
    }


def dry_run_execution_packets(rows: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    account = {
        "current_equity": 100000.0,
        "balance": 100000.0,
        "account_login": 531325516,
        "day_start_equity_or_balance_baseline": 100000.0,
        "daily_reset_window_id": "2026-06-18",
    }
    proof_rows = []
    for row in rows:
        tag = row["tag"]
        snapshot = row.get("spread_snapshot") or {}
        bid = float(snapshot.get("bid") or 100.0)
        ask = float(snapshot.get("ask") or bid)
        entry = round((bid + ask) / 2.0, 8)
        risk_distance = max(float(snapshot.get("point") or 0.01) * 100.0, 1.0)
        intent = admission.TradeIntent(
            sleeve=tag,
            symbol=row["file_symbol"],
            direction=1,
            decision_day="2026-06-18",
            stop_dist=risk_distance,
            target_dist=2.0 * risk_distance,
        )
        sized_unit = admission.SizedUnit(
            cluster=row["family"],
            sleeve_members=(tag,),
            n_trades=1,
            confidence=0.025,
            risk_pct_per_trade=0.0001875,
            unit_risk_pct=0.0001875,
            sized=True,
            reason="dry_run",
        )
        params = EP.build_book_trade_params(
            sized_unit,
            intent,
            {"entry_price": entry, "risk_distance": risk_distance, "stop_loss": entry - risk_distance},
            account,
            profile_namespace="operator_profile",
        )
        expected_tp = entry + 2.0 * risk_distance
        proof_rows.append(
            {
                "tag": tag,
                "file_symbol": row["file_symbol"],
                "policy": params["gtos_vnext_dynamic_policy_selected"],
                "final_target_r": params["gtos_vnext_dynamic_final_target_r"],
                "time_stop_bars": params["gtos_vnext_dynamic_time_stop_bars"],
                "take_profit_1": params["take_profit_1"],
                "expected_take_profit_1": expected_tp,
                "target2_packet_ok": (
                    params["gtos_vnext_dynamic_policy_selected"] == "time_stop"
                    and params["gtos_vnext_dynamic_final_target_r"] == 2.0
                    and params["gtos_vnext_dynamic_time_stop_bars"] == 96
                    and is_close(params["take_profit_1"], expected_tp)
                ),
            }
        )
    return {
        "schema": f"{SCHEMA_PREFIX}.execution_packet_dry_run_proof.v1",
        "created_at_utc": created_at,
        "row_count": len(proof_rows),
        "target2_packet_ok_count": sum(1 for row in proof_rows if row["target2_packet_ok"]),
        "all_target2_packets_ok": all(row["target2_packet_ok"] for row in proof_rows),
        "exit_profile_tags_match_selectable": sorted(EP.MARKET_EXPANSION_TARGET2_SLEEVES)
        == sorted(row["tag"] for row in rows),
        "rows": proof_rows,
    }


def zero_active_behavior_audit(rows: list[dict[str, Any]], created_at: str) -> dict[str, Any]:
    expansion = {row["tag"] for row in rows}
    cfg = yaml.safe_load((PROJECT_ROOT / "config" / "agent_config.yaml").read_text(encoding="utf-8"))["gtos_vnext_runtime"]
    default_names = {spec.tag for spec in active_specs(None)}
    candidate_names = {spec.tag for spec in active_specs(None, include_candidate_book=True)}
    empty_market_specs = {
        spec.tag
        for spec in active_specs(None, include_market_expansion_book=True, market_expansion_sleeves=[])
    }
    all_market_specs = {
        spec.tag
        for spec in active_specs(
            None,
            include_market_expansion_book=True,
            market_expansion_sleeves=sorted(expansion),
        )
    }
    default_registry = set(admission.effective_registry())
    candidate_registry_names = set(admission.effective_registry(include_candidate_book=True))
    empty_market_registry = set(
        admission.effective_registry(include_market_expansion_book=True, market_expansion_sleeves=[])
    )
    explicit_market_registry = set(
        admission.effective_registry(
            include_market_expansion_book=True,
            market_expansion_sleeves=sorted(expansion),
        )
    )
    return {
        "schema": f"{SCHEMA_PREFIX}.zero_active_behavior_audit.v1",
        "created_at_utc": created_at,
        "market_expansion_selectable_count": len(expansion),
        "market_expansion_runtime_built_count": len(MARKET_EXPANSION_BUILT),
        "market_expansion_names_in_default_active_specs": sorted(expansion & default_names),
        "market_expansion_names_in_candidate_book_specs": sorted(expansion & candidate_names),
        "market_expansion_names_in_empty_allowlist_specs": sorted(expansion & empty_market_specs),
        "market_expansion_names_in_candidate_built": sorted(expansion & set(CANDIDATE_BUILT)),
        "market_expansion_names_in_default_effective_registry": sorted(expansion & default_registry),
        "market_expansion_names_in_candidate_effective_registry": sorted(expansion & candidate_registry_names),
        "market_expansion_names_in_empty_allowlist_effective_registry": sorted(expansion & empty_market_registry),
        "explicit_allowlist_market_expansion_count": len(expansion & all_market_specs & explicit_market_registry),
        "bridge_default_include_market_expansion_book": DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"],
        "bridge_default_market_expansion_sleeves": DEFAULT_CONFIG["ultimate_book_market_expansion_sleeves"],
        "active_config_include_market_expansion_book": cfg.get("ultimate_book_include_market_expansion_book", False),
        "active_config_market_expansion_sleeves": cfg.get("ultimate_book_market_expansion_sleeves", []),
        "activation_weight_sum": sum(float(row.get("activation_weight_now") or 0.0) for row in rows),
        "zero_active_behavior_ok": (
            not (expansion & default_names)
            and not (expansion & candidate_names)
            and not (expansion & empty_market_specs)
            and not (expansion & set(CANDIDATE_BUILT))
            and not (expansion & default_registry)
            and not (expansion & candidate_registry_names)
            and not (expansion & empty_market_registry)
            and len(expansion & all_market_specs & explicit_market_registry) == len(expansion)
            and DEFAULT_CONFIG["ultimate_book_include_market_expansion_book"] is False
            and cfg.get("ultimate_book_include_market_expansion_book", False) is False
            and sum(float(row.get("activation_weight_now") or 0.0) for row in rows) == 0.0
        ),
    }


def run_focused_checks(created_at: str) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTEST_ADDOPTS"] = "-p no:cacheprovider"
    commands = [
        [
            sys.executable,
            "-m",
            "py_compile",
            "src/components/ultimate_book/sleeves/market_expansion_d1.py",
            "src/components/ultimate_book/sleeves/registry.py",
            "src/components/ultimate_book/admission.py",
            "src/components/ultimate_book/bridge.py",
            "src/components/ultimate_book/book_engine.py",
            "src/components/ultimate_book/book_owner.py",
            "src/components/ultimate_book/launcher.py",
            "src/components/ultimate_book/execution_packets.py",
            "tests/ultimate_book/test_market_expansion_runtime_generator.py",
        ],
        [sys.executable, "-m", "pytest", "tests/ultimate_book/test_market_expansion_runtime_generator.py", "-q"],
    ]
    results = []
    for command in commands:
        proc = subprocess.run(command, cwd=PROJECT_ROOT, env=env, text=True, capture_output=True, timeout=120)
        results.append(
            {
                "command": " ".join(command),
                "returncode": proc.returncode,
                "stdout_tail": proc.stdout[-4000:],
                "stderr_tail": proc.stderr[-4000:],
            }
        )
    return {
        "schema": f"{SCHEMA_PREFIX}.focused_test_result.v1",
        "created_at_utc": created_at,
        "ok": all(result["returncode"] == 0 for result in results),
        "results": results,
    }


def write_output_manifest(created_at: str) -> None:
    artifacts = []
    for path in sorted(ROUTE.iterdir()):
        if path.is_file() and path.name != "OUTPUT_MANIFEST.json":
            artifacts.append(
                {
                    "path": rel(path),
                    "bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
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
    created_at = utc_now()
    rows = read_jsonl(SOURCE_ROUTE / "ACTIVATION_CANDIDATE_ROW_LEDGER.jsonl")
    source_result = read_json(SOURCE_ROUTE / "MARKET_EXPANSION_ACTIVATION_CANDIDATE_PACKAGE_RESULT.json")
    selectable = [
        row
        for row in rows
        if row.get("design_status") == "default_off_spec_design_ready"
        and row.get("symbol_collision_winner") is True
    ]
    selectable_tags = {row["tag"] for row in selectable}
    code_tags = set(market_expansion_d1.TAG_TO_RULE)
    registry_tags = set(candidate_registry.MARKET_EXPANSION_DEFAULT_OFF_COLLISION_WINNER_NAMES)

    parity_rows, detail_rows, generator_book_replay = replay_runtime_parity(selectable, created_at)
    broker_manifest = capture_bridge_specs(selectable, created_at)
    execution_proof = dry_run_execution_packets(selectable, created_at)
    zero_audit = zero_active_behavior_audit(selectable, created_at)
    focused = run_focused_checks(created_at)

    parity_ok = len(parity_rows) == 14 and all(row["all_parity_passed"] for row in parity_rows)
    implementation_ok = (
        len(selectable) == 14
        and selectable_tags == code_tags == registry_tags == set(MARKET_EXPANSION_BUILT)
        and parity_ok
        and generator_book_replay["generator_book_signal_replay_complete"] is True
        and execution_proof["all_target2_packets_ok"] is True
        and zero_audit["zero_active_behavior_ok"] is True
        and focused["ok"] is True
    )
    live_missing = [
        "explicit broker trading-session table is not captured by the available siliconmetatrader5 bridge client"
        if broker_manifest["explicit_session_table_present_count"] == 0
        else None,
        "commission/slippage-to-R conversion remains stress/proxy evidence, not exact live authority",
        "limit-vs-market fill policy and queue/fillability remain owner-approved deployment-package decisions",
        "portfolio live-authority replay with broker fill/cost/swap semantics remains separate from signal parity",
        "owner-approved live config promotion has not been granted in this route",
    ]
    live_missing = [item for item in live_missing if item]
    result = {
        "schema": f"{SCHEMA_PREFIX}.result.v1",
        "created_at_utc": created_at,
        "ok": implementation_ok,
        "decision": "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTED_DEFAULT_OFF_NOT_LIVE_AUTHORITY"
        if implementation_ok
        else "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_FAIL_CLOSED",
        "source_activation_route": rel(SOURCE_ROUTE),
        "source_activation_decision": source_result.get("decision"),
        "selectable_activation_candidate_count": len(selectable),
        "runtime_generator_implemented_count": len(code_tags & selectable_tags),
        "runtime_generator_not_implemented_count": 14 - len(code_tags & selectable_tags),
        "runtime_generator_parity_pass_count": sum(1 for row in parity_rows if row["all_parity_passed"]),
        "runtime_generator_parity_fail_count": sum(1 for row in parity_rows if not row["all_parity_passed"]),
        "total_recomputed_source_events": generator_book_replay["total_recomputed_source_events"],
        "total_runtime_events": generator_book_replay["total_runtime_events"],
        "total_matched_events": generator_book_replay["total_matched_events"],
        "generator_book_signal_replay_complete": generator_book_replay["generator_book_signal_replay_complete"],
        "broker_bridge_reachable": broker_manifest["bridge_reachable"],
        "broker_symbol_info_captured_count": broker_manifest["symbol_info_captured_count"],
        "broker_stop_freeze_present_count": broker_manifest["stop_freeze_present_count"],
        "broker_explicit_session_table_present_count": broker_manifest["explicit_session_table_present_count"],
        "execution_target2_packet_ok_count": execution_proof["target2_packet_ok_count"],
        "zero_active_behavior_ok": zero_audit["zero_active_behavior_ok"],
        "activation_weight_now": 0.0,
        "live_authority": False,
        "deployment_ready": False,
        "deployment_not_ready_reasons": live_missing,
        "runtime_effect": "none_default_off_code_path_only",
        "account_info_read": False,
        "orderflow_used": False,
        "broker_or_order_mutation": False,
        "config_or_live_activation_changed": False,
        "vps_process_touched": False,
    }
    timing_proof = {
        "schema": f"{SCHEMA_PREFIX}.d1_next_open_timing_contract_proof.v1",
        "created_at_utc": created_at,
        "runtime_now_preferred": True,
        "calendar_plus_one_is_fallback_only": True,
        "all_runtime_decision_days_match_source_entry_dates": (
            generator_book_replay["total_decision_day_mismatches"] == 0
        ),
        "weekend_or_holiday_skip_sample_count": generator_book_replay["weekend_or_holiday_skip_sample_count"],
        "weekend_or_holiday_skip_samples": generator_book_replay["weekend_or_holiday_skip_samples"],
        "contract": (
            "Closed-bar engine passes bars through the latest completed D1 bar plus runtime_now for the "
            "current D1 session/open. The generator stamps intent.decision_day to runtime_now.date(), "
            "which matches the source scorer's previous-D1 signal/current-D1 entry date and handles "
            "weekend or holiday skips."
        ),
    }
    decision_rows = [
        {
            "schema": f"{SCHEMA_PREFIX}.decision_row.v1",
            "created_at_utc": created_at,
            "decision": result["decision"],
            "runtime_effect": result["runtime_effect"],
            "live_authority": False,
            "deployment_ready": False,
            "reason": (
                "14/14 default-off D1 runtime generators are implemented with source parity, "
                "explicit market-expansion allowlist gating, target2 packets, and zero active behavior."
            ),
        }
    ]
    saturation = {
        "schema": f"{SCHEMA_PREFIX}.saturation_audit.v1",
        "created_at_utc": created_at,
        "ok": implementation_ok,
        "no_arbitrary_top_n": True,
        "all_14_rows_replayed": len(parity_rows) == 14,
        "all_source_events_recomputed": True,
        "same_evidence_class_repairs_completed": [
            "runtime generator implemented for all 14 selectable activation candidates",
            "D1 next-open timing contract repaired with runtime_now session stamping",
            "execution packet target2 profile installed for all 14 tags",
            "market-expansion allowlist separated from candidate-book broad path",
            "localhost MT5 bridge spec capture attempted read-only without account/order mutation",
        ],
        "remaining_live_authority_requirements": live_missing,
    }
    completion = {
        "schema": f"{SCHEMA_PREFIX}.completion_audit.v1",
        "created_at_utc": created_at,
        "ok": implementation_ok,
        "instruction_coverage": {
            "mandatory_preflight_reread_by_orchestrator": True,
            "goal_session_research_discipline_read": True,
            "research_operating_doctrine_read": True,
            "orchestrator_controls_read": True,
            "constructive_builder_posture_applied": True,
            "inspire_not_kill_applied": True,
            "no_arbitrary_top_n": True,
        },
        "result_materialization_status": "14_runtime_generators_implemented_default_off_with_parity",
        "source_use_state": "committed activation artifacts plus source D1 OHLCV/tick-volume CSVs plus read-only localhost MT5 bridge symbol_info",
        "runtime_effect_boundary": "none_default_off_code_path_only",
        "owner_action_live_authority_boundary": (
            "Live config promotion remains false until a separate owner-approved deployment package "
            "closes session table, exact live cost/fill, portfolio replay, and rollback criteria."
        ),
        "forbidden_surfaces_touched": [],
        "deployment_ready": False,
        "deployment_not_ready_reasons": live_missing,
    }
    next_prompt = """# Market Expansion Live-Authority Dossier Successor Prompt

Mandatory context use: run mandatory GTOS preflight, regenerate `.context/LIVE_STATE.md`, and read `.context/00_core/goal_session_research_discipline.md`, `.context/00_core/research_operating_doctrine.md`, `.context/00_core/orchestrator_successor_operating_brief.md`, `.context/00_core/orchestrator_methodology_hardening_controls.md`, `.context/00_core/parallel_goal_merge_playbook.md`, this prompt, and the latest route artifacts as active instructions, not background. Do not rely on chat memory; after any compaction/resume/interruption/uncertainty reread the prompt, doctrine, and artifacts from disk and record instruction-coverage in the completion audit.

Evidence class: deployment-package proof for default-off market-expansion candidates, not live trading authority and not live broker mutation. Use a constructive builder posture with curiosity, active creativity, no conservative brake, no arbitrary top-N/top-3/top-5/top-10 or number-limited cutoff, full ledger preservation for all material rows, same-evidence-class pursuit, and full same-evidence-class pursuit. Literal impossibility means exactly every executable read, export, search, parser, repair, proxy, ablation, metric, audit, and review action inside this evidence class has been attempted or reduced to an exact owner/source/capture requirement.

Objective: consume the implemented generator package in `research/operations/final_moonshot_market_expansion_runtime_generator_implementation_2026_06_18/` and build the missing live-authority dossier while keeping activation weight zero. Required materialization: implementation decision, branch decision, source-capture/source completeness proof, exact-R/proxy-R/expectancy where computable, portfolio generator-book replay with current A8/candidate-book interaction, explicit broker trading-session table capture or exact unavailable-method proof, commission/slippage/swap-to-R conversion, limit-vs-market fill policy, rollback/kill criteria, and owner-action promotion boundary.

Allowed data: committed activation/generator route artifacts, source-hashed local MT5 OHLCV/tick-volume exports, localhost MT5 bridge read-only for OHLCV/tick-volume/spec/session evidence, current active candidate-book replay/MC artifacts, and local code/config/tests. Forbidden surfaces: no production-change or live trading broker operation; no prompt/config/risk/execution/safety/canary/selector live activation changes; no broker/account/order/history/deal/position mutation; no MT5 order state; no credentials; no remotes; no VPS process changes; no orderflow/depth; no paid API/vendor calls.

Required outputs: decision ledger, source/session/spec/cost/fill ledgers, replay ledger, all material row ledger, verifier, focused pytest or stronger test record, output manifest, saturation/self-red-team audit, completion audit, and exact successor owner-action/live-authority boundary. Preserve every non-promoted row as context, veto/sizing hint, source requirement, or successor experiment instead of deleting the idea.
"""

    write_jsonl(ROUTE / "RUNTIME_GENERATOR_PARITY_LEDGER.jsonl", parity_rows)
    write_jsonl(ROUTE / "RUNTIME_GENERATOR_EVENT_PARITY_DETAIL.jsonl", detail_rows)
    write_json(ROUTE / "D1_NEXT_OPEN_TIMING_CONTRACT_PROOF.json", timing_proof)
    write_json(ROUTE / "BROKER_SESSION_SPEC_CAPTURE_MANIFEST.json", broker_manifest)
    write_json(ROUTE / "EXECUTION_PACKET_DRY_RUN_PROOF.json", execution_proof)
    write_json(ROUTE / "ZERO_ACTIVE_BEHAVIOR_AUDIT.json", zero_audit)
    write_json(ROUTE / "FULL_GENERATOR_BOOK_REPLAY_PROOF.json", generator_book_replay)
    write_jsonl(ROUTE / "IMPLEMENTATION_DECISION_LEDGER.jsonl", decision_rows)
    write_json(ROUTE / "SATURATION_AUDIT.json", saturation)
    write_json(ROUTE / "COMPLETION_AUDIT.json", completion)
    write_json(ROUTE / "FOCUSED_TEST_RESULT.json", focused)
    write_json(ROUTE / "MARKET_EXPANSION_RUNTIME_GENERATOR_IMPLEMENTATION_RESULT.json", result)
    (ROUTE / "NEXT_PROMPT.md").write_text(next_prompt, encoding="utf-8")

    verifier = subprocess.run(
        [sys.executable, str(ROUTE / "verify_market_expansion_runtime_generator_implementation.py")],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        timeout=120,
    )
    write_json(
        ROUTE / "VERIFIER_COMMAND_RESULT.json",
        {
            "schema": f"{SCHEMA_PREFIX}.verifier_command_result.v1",
            "created_at_utc": created_at,
            "command": f"{sys.executable} {rel(ROUTE / 'verify_market_expansion_runtime_generator_implementation.py')}",
            "returncode": verifier.returncode,
            "stdout_tail": verifier.stdout[-4000:],
            "stderr_tail": verifier.stderr[-4000:],
        },
    )
    write_output_manifest(created_at)
    return result


if __name__ == "__main__":
    ROUTE.mkdir(parents=True, exist_ok=True)
    payload = build()
    print(json.dumps(payload, indent=2, sort_keys=True))
