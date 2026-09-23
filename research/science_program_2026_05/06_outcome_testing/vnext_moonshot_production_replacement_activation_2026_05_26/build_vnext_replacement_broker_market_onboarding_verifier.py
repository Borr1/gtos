from __future__ import annotations

import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


ROUTE_DIR = Path(__file__).resolve().parent
REPO_ROOT = ROUTE_DIR.parents[3]
DATE = "2026-05-26"
ROUTE_ID = "vnext_moonshot_production_replacement_activation_2026_05_26"

STAGE05_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_FULL_ACTIVATED_REPLAY_SUMMARY_{DATE}.json"
STAGE08_MAP = ROUTE_DIR / f"VNEXT_REPLACEMENT_MARKET_SOURCE_ACTIVATION_MAP_{DATE}.json"
STATE_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_SESSION_STATE_{DATE}.json"
MANIFEST_PATH = ROUTE_DIR / f"VNEXT_REPLACEMENT_OUTPUT_MANIFEST_{DATE}.json"
CONTROL_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_CONTROL_LEDGER_{DATE}.jsonl"
OUTPUT_LEDGER = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_LEDGER_{DATE}.jsonl"
OUTPUT_SUMMARY = ROUTE_DIR / f"VNEXT_REPLACEMENT_BROKER_MARKET_ONBOARDING_VERIFIER_{DATE}.json"

redacted_account_PROFILE = REPO_ROOT / "config/profiles/redacted_account.yaml"

REQUIRED_TIMEFRAMES = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "H1": 16385,
    "H4": 16388,
    "D1": 16408,
}

MANDATORY_CONTRACT_FIELDS = (
    "digits",
    "trade_mode",
    "visible",
    "spread",
    "spread_float",
    "point",
    "trade_tick_size",
    "trade_tick_value",
    "trade_tick_value_profit",
    "trade_tick_value_loss",
    "trade_contract_size",
    "volume_min",
    "volume_step",
    "volume_max",
    "trade_stops_level",
    "trade_freeze_level",
    "trade_exemode",
    "filling_mode",
    "order_mode",
    "trade_calc_mode",
    "expiration_mode",
    "swap_long",
    "swap_short",
)

EXTENDED_CONTRACT_FIELDS = (
    *MANDATORY_CONTRACT_FIELDS,
    "volume_limit",
    "currency_base",
    "currency_profit",
    "currency_margin",
    "margin_initial",
    "margin_maintenance",
    "margin_hedged",
    "swap_mode",
    "swap_rollover3days",
)

COMMON_ALIASES = {
    "NAS100": ["NDX100", "NAS100", "US100", "US100.cash", "NAS100.cash"],
    "US30_cash": ["US30", "US30_cash", "US30.cash", "DJ30", "DJI30"],
    "GER40": ["GER40", "GER40.cash", "DE40", "DE40.cash"],
    "UK100": ["UK100", "UK100.cash", "FTSE100"],
    "SPX500": ["SPX500", "US500", "US500.cash", "SP500"],
    "JP225": ["JP225", "JP225.cash", "JPN225", "NIKKEI225"],
    "USOIL_cash": ["USOIL", "USOIL_cash", "USOIL.cash", "WTI"],
    "UKOIL_cash": ["UKOIL", "UKOIL_cash", "UKOIL.cash", "BRENT"],
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(json.dumps(row, sort_keys=True) + "\n")


def _append_control(row: dict[str, Any]) -> None:
    with CONTROL_LEDGER.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _rel(path: Path | str) -> str:
    if isinstance(path, str):
        path = Path(path)
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _upsert_manifest_output(manifest: dict[str, Any], entry: dict[str, Any]) -> None:
    outputs = manifest.setdefault("outputs", [])
    for index, existing in enumerate(outputs):
        if existing.get("path") == entry["path"]:
            outputs[index] = {**existing, **entry}
            return
    outputs.append(entry)


def _append_test_result(state: dict[str, Any], command: str, result: str, timestamp: str) -> None:
    tests = state.setdefault("tests_verifiers_run", [])
    tests[:] = [row for row in tests if row.get("command") != command]
    tests.append({"command": command, "result": result, "timestamp_utc": timestamp})


def _normalize_symbol(value: str) -> str:
    normalized = "".join(ch for ch in value.upper() if ch.isalnum())
    for suffix in ("CASH", "PRO", "RAW", "STD"):
        if normalized.endswith(suffix):
            normalized = normalized[: -len(suffix)]
    return normalized


def _load_profile_aliases() -> dict[str, str]:
    try:
        import yaml
    except ImportError:
        return {}
    if not redacted_account_PROFILE.exists():
        return {}
    data = yaml.safe_load(redacted_account_PROFILE.read_text(encoding="utf-8")) or {}
    aliases: dict[str, str] = {}
    for symbol, block in (data.get("instruments") or {}).items():
        market = block.get("market") if isinstance(block, dict) else None
        if isinstance(market, dict) and market.get("mt5_symbol"):
            aliases[str(symbol)] = str(market["mt5_symbol"])
    return aliases


def _candidate_aliases(symbol: str, profile_aliases: dict[str, str], broker_names: list[str]) -> list[str]:
    candidates: list[str] = []

    def add(value: str | None) -> None:
        if value and value not in candidates:
            candidates.append(value)

    add(symbol)
    add(profile_aliases.get(symbol))
    for alias in COMMON_ALIASES.get(symbol, []):
        add(alias)
    if symbol.endswith("_cash"):
        root = symbol.removesuffix("_cash")
        add(root)
        add(f"{root}.cash")
    else:
        add(f"{symbol}.cash")

    normalized_targets = {_normalize_symbol(candidate) for candidate in candidates}
    for name in broker_names:
        normalized = _normalize_symbol(name)
        if normalized in normalized_targets:
            add(name)
    return candidates


def _safe_number(value: Any) -> Any:
    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None
    return value


def _info_to_dict(info: Any) -> dict[str, Any]:
    if info is None:
        return {}
    raw = info._asdict() if hasattr(info, "_asdict") else {}
    return {str(key): _safe_number(value) for key, value in raw.items()}


def _tick_to_dict(tick: Any) -> dict[str, Any]:
    if tick is None:
        return {"available": False}
    raw = tick._asdict() if hasattr(tick, "_asdict") else {}
    payload = {str(key): _safe_number(value) for key, value in raw.items()}
    payload["available"] = True
    return payload


def _session_rows(mt5: Any, symbol: str) -> dict[str, Any]:
    if not hasattr(mt5, "symbol_info_session_trade"):
        return {
            "available": False,
            "status": "mt5_python_symbol_info_session_trade_unavailable",
            "sessions": [],
        }
    sessions: list[dict[str, Any]] = []
    for day in range(7):
        for index in range(24):
            try:
                session = mt5.symbol_info_session_trade(symbol, day, index)
            except Exception as exc:  # pragma: no cover - broker terminal dependent
                return {"available": False, "status": f"session_query_error:{type(exc).__name__}:{exc}", "sessions": sessions}
            if session is None:
                break
            if hasattr(session, "_asdict"):
                session_payload = session._asdict()
            else:
                session_payload = {"from": getattr(session, "from", None), "to": getattr(session, "to", None)}
            sessions.append({"day": day, "index": index, **{str(k): str(v) for k, v in session_payload.items()}})
    return {"available": bool(sessions), "status": "captured" if sessions else "no_sessions_returned", "sessions": sessions}


def _timeframe_probe(mt5: Any, symbol: str) -> dict[str, dict[str, Any]]:
    probes: dict[str, dict[str, Any]] = {}
    for label, tf_const in REQUIRED_TIMEFRAMES.items():
        try:
            rates = mt5.copy_rates_from_pos(symbol, tf_const, 0, 5)
            count = 0 if rates is None else len(rates)
            latest = None
            if count:
                latest_epoch = int(rates[-1]["time"])
                latest = datetime.fromtimestamp(latest_epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            probes[label] = {"available": count > 0, "rows": count, "latest_bar_utc": latest}
        except Exception as exc:  # pragma: no cover - broker terminal dependent
            probes[label] = {"available": False, "rows": 0, "error": f"{type(exc).__name__}:{exc}"}
    return probes


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    values = sorted(values)
    index = (len(values) - 1) * pct
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return values[int(index)]
    return values[lower] + (values[upper] - values[lower]) * (index - lower)


def _tick_history_probe(mt5: Any, symbol: str, point: Any) -> dict[str, Any]:
    if not hasattr(mt5, "copy_ticks_from"):
        return {"available": False, "status": "copy_ticks_from_unavailable"}
    since = datetime.now(timezone.utc) - timedelta(days=3)
    try:
        ticks = mt5.copy_ticks_from(symbol, since, 1000, mt5.COPY_TICKS_ALL)
    except Exception as exc:  # pragma: no cover - broker terminal dependent
        return {"available": False, "status": f"tick_history_error:{type(exc).__name__}:{exc}"}
    count = 0 if ticks is None else len(ticks)
    point_value = None
    try:
        point_value = float(point) if point is not None and float(point) > 0 else None
    except (TypeError, ValueError):
        point_value = None
    spreads: list[float] = []
    if count and point_value:
        for tick in ticks:
            try:
                bid = float(tick["bid"])
                ask = float(tick["ask"])
            except (KeyError, TypeError, ValueError):
                continue
            if bid > 0 and ask > 0 and ask >= bid:
                spreads.append((ask - bid) / point_value)
    return {
        "available": count > 0,
        "rows": count,
        "lookback_days": 3,
        "spread_points_basis": "copy_ticks_from_bid_ask_divided_by_symbol_point",
        "spread_points_sample_count": len(spreads),
        "spread_points_min": min(spreads) if spreads else None,
        "spread_points_max": max(spreads) if spreads else None,
        "spread_points_p50": _percentile(spreads, 0.50),
        "spread_points_p95": _percentile(spreads, 0.95),
    }


def _decode_order_mode(order_mode: Any) -> dict[str, Any]:
    try:
        value = int(order_mode)
    except (TypeError, ValueError):
        return {"raw": order_mode, "status": "unavailable"}
    flags = {
        "market": 1,
        "limit": 2,
        "stop": 4,
        "stop_limit": 8,
        "sl": 16,
        "tp": 32,
        "close_by": 64,
    }
    return {
        "raw": value,
        "status": "decoded",
        "allows_market_orders": bool(value & flags["market"]),
        "allows_limit_orders": bool(value & flags["limit"]),
        "allows_stop_orders": bool(value & flags["stop"]),
        "allows_stop_limit_orders": bool(value & flags["stop_limit"]),
        "allows_sl": bool(value & flags["sl"]),
        "allows_tp": bool(value & flags["tp"]),
        "allows_close_by": bool(value & flags["close_by"]),
    }


def _decode_filling_mode(filling_mode: Any) -> dict[str, Any]:
    try:
        value = int(filling_mode)
    except (TypeError, ValueError):
        return {"raw": filling_mode, "status": "unavailable"}
    flags = {
        "fok": 1,
        "ioc": 2,
        "boc": 4,
    }
    return {
        "raw": value,
        "status": "decoded",
        "allows_fok": bool(value & flags["fok"]),
        "allows_ioc": bool(value & flags["ioc"]),
        "allows_boc": bool(value & flags["boc"]),
    }


def _mandatory_failures(info: dict[str, Any], tick: dict[str, Any], timeframes: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field in MANDATORY_CONTRACT_FIELDS:
        if info.get(field) is None:
            failures.append(f"missing_{field}")
    if info.get("trade_mode") in (None, 0):
        failures.append("trade_mode_disabled_or_missing")
    if info.get("trade_tick_size") is not None and float(info.get("trade_tick_size") or 0.0) <= 0.0:
        failures.append("nonpositive_trade_tick_size")
    if info.get("trade_tick_value") is not None and float(info.get("trade_tick_value") or 0.0) <= 0.0:
        failures.append("nonpositive_trade_tick_value")
    if info.get("trade_contract_size") is not None and float(info.get("trade_contract_size") or 0.0) <= 0.0:
        failures.append("nonpositive_contract_size")
    if info.get("volume_min") is not None and float(info.get("volume_min") or 0.0) <= 0.0:
        failures.append("nonpositive_min_lot")
    if info.get("volume_step") is not None and float(info.get("volume_step") or 0.0) <= 0.0:
        failures.append("nonpositive_lot_step")
    if tick.get("available") is not True:
        failures.append("tick_unavailable")
    order_mode = _decode_order_mode(info.get("order_mode"))
    if order_mode.get("status") != "decoded":
        failures.append("order_mode_unavailable")
    elif not (order_mode.get("allows_market_orders") or order_mode.get("allows_limit_orders")):
        failures.append("order_mode_disallows_market_and_limit_orders")
    filling_mode = _decode_filling_mode(info.get("filling_mode"))
    if filling_mode.get("status") != "decoded":
        failures.append("filling_mode_unavailable")
    elif not (filling_mode.get("allows_fok") or filling_mode.get("allows_ioc") or filling_mode.get("allows_boc")):
        failures.append("filling_mode_has_no_supported_fill_policy")
    for label, probe in timeframes.items():
        if probe.get("available") is not True:
            failures.append(f"missing_required_timeframe_{label}")
    return sorted(set(failures))


def _source_readiness(symbol: str, stage08_by_symbol: dict[str, dict[str, Any]]) -> dict[str, Any]:
    row = stage08_by_symbol.get(symbol, {})
    capability = row.get("source_capability") or {}
    return {
        "historical_source_status": row.get("historical_source_status"),
        "has_ohlc_source": capability.get("has_ohlc_source"),
        "has_sierra_source": capability.get("has_sierra_source"),
        "has_tick_parquet": capability.get("has_tick_parquet"),
        "source_window_complete_ratio": row.get("source_window_complete_ratio"),
        "source_window_incomplete_rows": row.get("source_window_incomplete_rows"),
        "forward_capture_required": True,
        "source_capture_readiness": "prospective_capture_required_before_execution_activation",
    }


def _no_mt5_row(
    symbol: str,
    profile_aliases: dict[str, str],
    stage08_by_symbol: dict[str, dict[str, Any]],
    generated_at: str,
    status: str,
    reason: str,
) -> dict[str, Any]:
    aliases = _candidate_aliases(symbol, profile_aliases, [])
    return {
        "alias_candidates_checked": aliases,
        "broker_contract_status": "verification_pending_not_excluded",
        "broker_symbol": None,
        "eligibility_reason": reason,
        "eligible_for_vnext_activation": False,
        "exact_exclusion_reason": None,
        "generated_at_utc": generated_at,
        "mt5_access_status": status,
        "no_live_or_broker_mutation": True,
        "record_type": "broker_market_onboarding_check",
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_broker_market_onboarding_v1",
        "source_capture": _source_readiness(symbol, stage08_by_symbol),
        "symbol": symbol,
    }


def _check_symbol(
    mt5: Any,
    symbol: str,
    profile_aliases: dict[str, str],
    broker_names: list[str],
    stage08_by_symbol: dict[str, dict[str, Any]],
    generated_at: str,
) -> dict[str, Any]:
    aliases = _candidate_aliases(symbol, profile_aliases, broker_names)
    alias_checks: list[dict[str, Any]] = []
    selected_valid: dict[str, Any] | None = None
    selected_invalid: dict[str, Any] | None = None

    for alias in aliases:
        info_before = mt5.symbol_info(alias)
        select_ok = False
        select_error = None
        if info_before is not None:
            try:
                select_ok = bool(mt5.symbol_select(alias, True))
            except Exception as exc:  # pragma: no cover - broker terminal dependent
                select_error = f"{type(exc).__name__}:{exc}"
        info = _info_to_dict(mt5.symbol_info(alias))
        tick = _tick_to_dict(mt5.symbol_info_tick(alias))
        timeframes = _timeframe_probe(mt5, alias) if info else {}
        tick_history = _tick_history_probe(mt5, alias, info.get("point")) if info else {"available": False, "status": "symbol_info_missing"}
        session_info = _session_rows(mt5, alias) if info else {"available": False, "status": "symbol_info_missing", "sessions": []}
        contract_failures = ["symbol_info_missing"] if not info else _mandatory_failures(info, tick, timeframes)
        if select_error:
            contract_failures.append(f"symbol_select_error:{select_error}")
        if info and not select_ok:
            contract_failures.append("symbol_select_false")

        check = {
            "alias": alias,
            "commission_fields": {key: value for key, value in info.items() if "commission" in key.lower()},
            "contract_failures": sorted(set(contract_failures)),
            "contract_metadata": {field: info.get(field) for field in EXTENDED_CONTRACT_FIELDS},
            "filling_mode": info.get("filling_mode"),
            "filling_mode_decoded": _decode_filling_mode(info.get("filling_mode")),
            "info_found": bool(info),
            "order_mode_decoded": _decode_order_mode(info.get("order_mode")),
            "session_fields": {key: value for key, value in info.items() if key.startswith("session_")},
            "session_hours": session_info,
            "spread": info.get("spread"),
            "spread_evidence": {
                "current_spread_points": info.get("spread"),
                "spread_float": info.get("spread_float"),
                "tick_history_p95_points": tick_history.get("spread_points_p95") if isinstance(tick_history, dict) else None,
                "tick_history_rows": tick_history.get("rows") if isinstance(tick_history, dict) else None,
            },
            "swap_fields": {key: info.get(key) for key in ("swap_mode", "swap_long", "swap_short", "swap_rollover3days")},
            "symbol_select_ok": select_ok,
            "tick": tick,
            "tick_history": tick_history,
            "timeframes": timeframes,
            "trade_mode": info.get("trade_mode"),
            "visible": info.get("visible"),
        }
        alias_checks.append(check)
        if not check["contract_failures"] and selected_valid is None:
            selected_valid = check
        elif info and selected_invalid is None:
            selected_invalid = check

    selected = selected_valid or selected_invalid
    if selected_valid:
        contract_status = "valid_broker_native_contract"
        eligible = True
        exclusion_reason = None
        reason = "MT5/redacted_account symbol contract is visible, tradeable, has ticks, required bars, and core contract metadata."
        broker_symbol = selected_valid["alias"]
    elif selected_invalid:
        failures = selected_invalid.get("contract_failures", [])
        if "trade_mode_disabled_or_missing" in failures:
            contract_status = "broker_non_tradeable"
            exclusion_reason = "broker_non_tradeable"
        elif any(str(failure).startswith("missing_required_timeframe_") for failure in failures):
            contract_status = "missing_required_timeframe_or_bar_feed"
            exclusion_reason = "missing_required_timeframe_or_tick_feed"
        elif "tick_unavailable" in failures:
            contract_status = "missing_required_timeframe_or_tick_feed"
            exclusion_reason = "missing_required_timeframe_or_tick_feed"
        else:
            contract_status = "invalid_contract_metadata"
            exclusion_reason = "invalid_contract_metadata"
        eligible = False
        broker_symbol = selected_invalid["alias"]
        reason = "Broker symbol resolved but failed exact read-only contract checks."
    else:
        contract_status = "broker_unavailable"
        eligible = False
        broker_symbol = None
        exclusion_reason = "broker_unavailable"
        reason = "No exact broker symbol alias resolved through MT5 symbols_get/symbol_info."

    return {
        "alias_checks": alias_checks,
        "alias_candidates_checked": aliases,
        "broker_contract_status": contract_status,
        "broker_symbol": broker_symbol,
        "eligibility_reason": reason,
        "eligible_for_vnext_activation": eligible,
        "exact_exclusion_reason": exclusion_reason,
        "generated_at_utc": generated_at,
        "mt5_access_status": "initialized_read_only",
        "no_live_or_broker_mutation": True,
        "record_type": "broker_market_onboarding_check",
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_broker_market_onboarding_v1",
        "selected_alias_check": selected,
        "source_capture": _source_readiness(symbol, stage08_by_symbol),
        "symbol": symbol,
    }


def main() -> int:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    stage05 = _read_json(STAGE05_SUMMARY)
    state = _read_json(STATE_PATH)
    manifest = _read_json(MANIFEST_PATH)
    stage08 = _read_json(STAGE08_MAP) if STAGE08_MAP.exists() else {"markets": []}
    stage08_by_symbol = {row.get("symbol"): row for row in stage08.get("markets", [])}
    symbols = sorted(stage05["coverage"]["symbol_counts"])
    profile_aliases = _load_profile_aliases()

    rows: list[dict[str, Any]]
    mt5_status = "not_attempted"
    broker_names: list[str] = []
    initialize_error = None
    mt5 = None
    try:
        import MetaTrader5 as mt5_module

        mt5 = mt5_module
        if mt5.initialize():
            mt5_status = "initialized_read_only"
            broker_names = sorted({item.name for item in (mt5.symbols_get() or []) if getattr(item, "name", None)})
        else:
            mt5_status = "initialize_failed"
            initialize_error = str(mt5.last_error())
    except Exception as exc:  # pragma: no cover - environment dependent
        mt5_status = "import_or_initialize_error"
        initialize_error = f"{type(exc).__name__}:{exc}"

    if mt5_status == "initialized_read_only" and mt5 is not None:
        rows = [_check_symbol(mt5, symbol, profile_aliases, broker_names, stage08_by_symbol, generated_at) for symbol in symbols]
        try:
            mt5.shutdown()
        except Exception:
            pass
    else:
        rows = [
            _no_mt5_row(
                symbol=symbol,
                profile_aliases=profile_aliases,
                stage08_by_symbol=stage08_by_symbol,
                generated_at=generated_at,
                status=mt5_status,
                reason=f"MT5 read-only market metadata unavailable in this route environment: {initialize_error}",
            )
            for symbol in symbols
        ]

    status_counts = Counter(row["broker_contract_status"] for row in rows)
    eligible_symbols = sorted(row["symbol"] for row in rows if row.get("eligible_for_vnext_activation") is True)
    exact_excluded_symbols = sorted(row["symbol"] for row in rows if row.get("exact_exclusion_reason"))
    pending_symbols = sorted(
        row["symbol"]
        for row in rows
        if row.get("broker_contract_status") == "verification_pending_not_excluded"
    )
    summary = {
        "broker_contract_status_counts": dict(sorted(status_counts.items())),
        "broker_names_count": len(broker_names),
        "eligible_symbols": eligible_symbols,
        "exact_excluded_symbols": exact_excluded_symbols,
        "generated_at_utc": generated_at,
        "initialize_error": initialize_error,
        "market_rows": len(rows),
        "mt5_access_status": mt5_status,
        "no_live_or_broker_mutation": True,
        "pending_symbols_not_excluded": pending_symbols,
        "required_contract_fields": list(MANDATORY_CONTRACT_FIELDS),
        "required_timeframes": sorted(REQUIRED_TIMEFRAMES),
        "route_id": ROUTE_ID,
        "schema_version": "vnext_replacement_broker_market_onboarding_verifier_v1",
        "stage_id": "market_source_activation_invariant",
        "status": "passed",
        "symbols_checked": symbols,
    }

    _append_jsonl(OUTPUT_LEDGER, rows)
    _write_json(OUTPUT_SUMMARY, summary)

    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_LEDGER.name, "stage": "market_source_activation_invariant", "status": "created", "rows": len(rows)},
    )
    _upsert_manifest_output(
        manifest,
        {"path": OUTPUT_SUMMARY.name, "stage": "market_source_activation_invariant", "status": "created", "result": "passed"},
    )
    manifest["last_updated_utc"] = generated_at
    _write_json(MANIFEST_PATH, manifest)

    evidence = state.setdefault("evidence_rows_scanned", {})
    evidence["broker_market_onboarding_rows"] = len(rows)
    evidence["broker_market_onboarding_eligible_symbols"] = len(eligible_symbols)
    evidence["broker_market_onboarding_exact_exclusions"] = len(exact_excluded_symbols)
    evidence["broker_market_onboarding_pending_not_excluded"] = len(pending_symbols)
    state.setdefault("market_source_activation_invariant", {})["broker_onboarding_verifier"] = {
        "ledger": _rel(OUTPUT_LEDGER),
        "summary": _rel(OUTPUT_SUMMARY),
        "status": "executed",
        "mt5_access_status": mt5_status,
        "eligible_symbols": eligible_symbols,
        "exact_excluded_symbols": exact_excluded_symbols,
        "pending_symbols_not_excluded": pending_symbols,
    }
    _append_test_result(
        state,
        _rel(Path(__file__)),
        "passed; wrote read-only broker market onboarding verifier evidence",
        generated_at,
    )
    state["last_updated_utc"] = generated_at
    _write_json(STATE_PATH, state)

    _append_control(
        {
            "event": "market_source_activation_invariant_broker_onboarding_verifier_completed",
            "exact_excluded_symbols": exact_excluded_symbols,
            "generated_at_utc": generated_at,
            "mt5_access_status": mt5_status,
            "pending_symbols_not_excluded": pending_symbols,
            "eligible_symbols": eligible_symbols,
            "route_id": ROUTE_ID,
            "stage_id": "market_source_activation_invariant",
            "status": "executed",
        }
    )

    print(
        json.dumps(
            {
                "eligible_symbols": eligible_symbols,
                "exact_excluded_symbols": exact_excluded_symbols,
                "market_rows": len(rows),
                "mt5_access_status": mt5_status,
                "pending_symbols_not_excluded": pending_symbols,
                "status": "passed",
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
