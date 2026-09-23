"""Expanded-market proxy-R performance over reachable OHLC sources."""

from __future__ import annotations

import os
import csv
import hashlib
from collections import Counter
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any


EXPANDED_MARKET_PROXY_R_PERFORMANCE_SURFACE = (
    "src/research_infra/moonshot_expanded_market_proxy_r_performance.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

TIME_COLUMNS = ("time", "timestamp", "datetime", "date", "candle_close_utc")
NUMERIC_ALIASES = {
    "open": ("open", "o"),
    "high": ("high", "h"),
    "low": ("low", "l"),
    "close": ("close", "c"),
}
TIMEFRAMES = ("M1", "M5", "M15", "H1", "H4", "D1")
DEFAULT_HORIZONS = ("h4", "h16", "h32")
SESSION_ALIASES = {
    "ALL_SESSIONS": "ALL_SESSIONS",
    "ALL_AVAILABLE_OR_UNMAPPED_SESSIONS": "ALL_SESSIONS",
    "tokyo": "tokyo_kz",
    "tokyo_kz": "tokyo_kz",
    "london": "london_core",
    "london_kz": "london_core",
    "london_core": "london_core",
    "ny": "ny_core",
    "ny_kz": "ny_core",
    "ny_core": "ny_core",
    "off_kz": "off_core_session",
    "off_core_session": "off_core_session",
}


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": BOUNDARY_SCHEMA,
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_proxy_r_performance_surface"] = EXPANDED_MARKET_PROXY_R_PERFORMANCE_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def normalized_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    normalized = {normalized_header(name): name for name in fieldnames}
    resolved: dict[str, str | None] = {}
    for logical, aliases in NUMERIC_ALIASES.items():
        resolved[logical] = next((normalized[alias] for alias in aliases if alias in normalized), None)
    resolved["time"] = next((normalized[alias] for alias in TIME_COLUMNS if alias in normalized), None)
    return resolved


def long_path(path: Path) -> str:
    text = str(path)
    if os.name == "nt" and len(text) >= 240 and not text.startswith("\\\\?\\"):
        return "\\\\?\\" + text
    return text


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with open(long_path(path), "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def symbol_key(symbol: Any) -> str:
    return normalized(symbol).upper()


def parse_source_symbol_timeframe(path: Path) -> tuple[str | None, str | None]:
    stem = path.stem
    if "_" not in stem:
        return None, None
    symbol, timeframe = stem.rsplit("_", 1)
    if timeframe not in TIMEFRAMES:
        return None, None
    return symbol, timeframe


def source_aliases(symbol: Any) -> set[str]:
    key = symbol_key(symbol)
    aliases = {key}
    if key == "US30":
        aliases.update({"US30_CASH", "US30_YM", "US30_MYM"})
    if key == "UKOUSD":
        aliases.add("UKOIL_CASH")
    if key == "USOIL_CASH":
        aliases.add("USOIL_CASH")
    if key.endswith("_CASH"):
        aliases.add(key.replace("_CASH", "_cash").upper())
    if "XAUUSD" in key or key in {"GC", "MGC"}:
        aliases.update({"XAUUSD", "XAUUSD_GC", "XAUUSD_MGC", "XAUUSD_SCID"})
    if "XAGUSD" in key or key in {"SI", "SIL"}:
        aliases.update({"XAGUSD", "XAGUSD_SI", "XAGUSD_SIL"})
    if "NAS100" in key or key in {"NQ", "MNQ"}:
        aliases.update({"NAS100", "NAS100_NQ", "NAS100_MNQ"})
    if "SPX" in key or key in {"ES", "MES"}:
        aliases.update({"SPX500", "SPX_ES", "SPX_MES"})
    if "US30" in key or key in {"YM", "MYM"}:
        aliases.update({"US30", "US30_CASH", "US30_YM", "US30_MYM"})
    if key.endswith("_6J"):
        aliases.add("USDJPY")
    if key.endswith("_6B"):
        aliases.add("GBPUSD")
    if key.endswith("_6E"):
        aliases.add("EURUSD")
    return aliases


def is_ohlc_csv(path: Path) -> tuple[bool, dict[str, str | None]]:
    try:
        with open(long_path(path), "r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.reader(handle)
            header = next(reader, [])
    except OSError:
        return False, {}
    columns = resolve_columns(header)
    required = (columns.get("open"), columns.get("high"), columns.get("low"), columns.get("close"), columns.get("time"))
    return None not in required, columns


def discover_ohlc_csv_sources(repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((repo_root / "data").rglob("*.csv")):
        symbol, timeframe = parse_source_symbol_timeframe(path)
        if not symbol or not timeframe:
            continue
        is_ohlc, columns = is_ohlc_csv(path)
        rel_path = path.relative_to(repo_root).as_posix()
        rows.append(
            {
                "source_path": rel_path,
                "source_symbol": symbol,
                "source_symbol_key": symbol_key(symbol),
                "source_timeframe": timeframe,
                "source_file_sha256": sha256_file(path) if is_ohlc else None,
                "source_access_status": "OHLC_CSV_REACHABLE" if is_ohlc else "CSV_NOT_OHLC",
                "resolved_columns": columns,
            }
        )
    return rows


def parse_dt(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    for candidate in (text, text.replace(" ", "T")):
        try:
            parsed = datetime.fromisoformat(candidate)
            return parsed.replace(tzinfo=None)
        except ValueError:
            pass
    for fmt in ("%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            pass
    return None


def load_ohlc_rows(repo_root: Path, source_path: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    path = repo_root / source_path
    if not path.exists():
        return [], {
            "source_path": source_path,
            "source_access_status": "SOURCE_FILE_MISSING",
            "source_file_sha256": None,
            "parsed_ohlc_rows": 0,
            "rows_streamed": 0,
        }
    with open(long_path(path), "r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = resolve_columns(reader.fieldnames or [])
        required = (columns.get("open"), columns.get("high"), columns.get("low"), columns.get("close"), columns.get("time"))
        if None in required:
            return [], {
                "source_path": source_path,
                "source_access_status": "SOURCE_OHLC_COLUMNS_MISSING",
                "source_file_sha256": sha256_file(path),
                "parsed_ohlc_rows": 0,
                "rows_streamed": 0,
                "resolved_columns": columns,
            }
        rows: list[dict[str, Any]] = []
        rows_streamed = 0
        for raw in reader:
            rows_streamed += 1
            open_value = as_float(raw.get(columns["open"] or ""))
            high_value = as_float(raw.get(columns["high"] or ""))
            low_value = as_float(raw.get(columns["low"] or ""))
            close_value = as_float(raw.get(columns["close"] or ""))
            if None in (open_value, high_value, low_value, close_value):
                continue
            row_time = raw.get(columns["time"] or "")
            rows.append(
                {
                    "time": row_time,
                    "dt": parse_dt(row_time),
                    "open": open_value,
                    "high": high_value,
                    "low": low_value,
                    "close": close_value,
                }
            )
    return rows, {
        "source_path": source_path,
        "source_access_status": "OHLC_CSV_REACHABLE",
        "source_file_sha256": sha256_file(path),
        "parsed_ohlc_rows": len(rows),
        "rows_streamed": rows_streamed,
        "first_time": rows[0]["time"] if rows else None,
        "last_time": rows[-1]["time"] if rows else None,
    }


def canonical_session(session: Any) -> str | None:
    text = normalized(session)
    return SESSION_ALIASES.get(text, SESSION_ALIASES.get(text.lower()))


def numeric_sessions(session: Any) -> list[str]:
    canonical = canonical_session(session)
    if canonical:
        return [canonical]
    return []


def numeric_horizons(horizon_id: Any) -> list[str]:
    text = normalized(horizon_id)
    if text.startswith("h") and text[1:].isdigit():
        return [text]
    if text in {"ALL_HORIZONS", "ALL_AVAILABLE_OR_UNMAPPED_HORIZONS"}:
        return list(DEFAULT_HORIZONS)
    return []


def horizon_bar_count(horizon_id: str) -> int | None:
    if horizon_id.startswith("h") and horizon_id[1:].isdigit():
        return int(horizon_id[1:])
    return None


def hour_float(dt_value: datetime) -> float:
    return dt_value.hour + dt_value.minute / 60.0 + dt_value.second / 3600.0


def in_session(dt_value: datetime | None, session: str, timeframe: str) -> bool:
    if session == "ALL_SESSIONS":
        return True
    if timeframe == "D1":
        return True
    if dt_value is None:
        return False
    hour = hour_float(dt_value)
    london = 7.0 <= hour < 12.0
    ny = 13.0 <= hour < 17.0
    tokyo = 0.0 <= hour < 3.0
    if session == "london_core":
        return london
    if session == "ny_core":
        return ny
    if session == "tokyo_kz":
        return tokyo
    if session == "off_core_session":
        return not (london or ny or tokyo)
    return False


def cost_proxy_for_symbol(symbol: str, cost_by_symbol: dict[str, dict[str, Any]]) -> dict[str, Any]:
    for alias in source_aliases(symbol):
        if alias in cost_by_symbol:
            row = cost_by_symbol[alias]
            mean_cost = as_float(row.get("mean_cost_r")) or 0.0
            stress_cost = as_float(row.get("stress_cost_r"))
            max_cost = as_float(row.get("max_cost_r"))
            return {
                "cost_adjustment_r": mean_cost,
                "stress_cost_adjustment_r": stress_cost if stress_cost not in (None, 0.0) else max(mean_cost * 2.0, max_cost or 0.0),
                "cost_proxy_status": "SYMBOL_COST_LEDGER_PROXY_USED",
                "cost_proxy_symbol": row.get("symbol"),
            }
    key = symbol_key(symbol)
    generic = 0.02 if any(token in key for token in ("BTC", "ETH", "OIL", "UK100", "GER40", "JP225", "VIX")) else 0.01
    return {
        "cost_adjustment_r": generic,
        "stress_cost_adjustment_r": generic * 3.0,
        "cost_proxy_status": "GENERIC_DENOMINATOR_COST_PROXY_USED",
        "cost_proxy_symbol": None,
    }


def median_range(rows: list[dict[str, Any]]) -> float | None:
    ranges = [abs(float(row["high"]) - float(row["low"])) for row in rows if row.get("high") is not None and row.get("low") is not None]
    ranges = [value for value in ranges if value > 0]
    return median(ranges) if ranges else None


def event_path_result(
    rows: list[dict[str, Any]],
    index: int,
    horizon_bars: int,
    side: str,
    denominator_price: float,
) -> tuple[str, float, float, float, int | None]:
    entry = float(rows[index]["close"])
    if side == "LONG":
        target = entry + denominator_price
        stop = entry - denominator_price
    else:
        target = entry - denominator_price
        stop = entry + denominator_price
    end_index = min(index + horizon_bars, len(rows) - 1)
    exit_close = float(rows[end_index]["close"])
    raw = (exit_close - entry) / denominator_price
    if side == "SHORT":
        raw = -raw
    if raw >= 1.0:
        return "HORIZON_CLOSE_TARGET_PROXY_RESULT", 1.0, target, stop, horizon_bars
    if raw <= -1.0:
        return "HORIZON_CLOSE_STOP_PROXY_RESULT", -1.0, target, stop, horizon_bars
    return "NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT", raw, target, stop, None


def score_source_session_horizon(
    source: dict[str, Any],
    rows: list[dict[str, Any]],
    session: str,
    horizon_id: str,
    side: str,
    cost_proxy: dict[str, Any],
) -> dict[str, Any]:
    horizon_bars = horizon_bar_count(horizon_id)
    if horizon_bars is None:
        return {"score_status": "HORIZON_NOT_NUMERIC", "effective_n": 0}
    if len(rows) <= horizon_bars:
        return {"score_status": "SOURCE_UNDER_HORIZON_LENGTH", "effective_n": 0}
    source_range = median_range(rows)
    if source_range is None or source_range <= 0:
        return {"score_status": "SOURCE_DENOMINATOR_RANGE_UNAVAILABLE", "effective_n": 0}

    cost_r = float(cost_proxy.get("cost_adjustment_r") or 0.0)
    stress_cost_r = float(cost_proxy.get("stress_cost_adjustment_r") or cost_r)
    values: list[float] = []
    cost_values: list[float] = []
    stress_values: list[float] = []
    win_count = 0
    loss_count = 0
    zero_count = 0
    ambiguous_count = 0
    path_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()
    timestamp_counts: Counter[str] = Counter()
    first_event: dict[str, Any] | None = None
    target_first_total = 0
    stop_first_total = 0
    neither_total = 0

    for index in range(0, len(rows) - horizon_bars):
        row = rows[index]
        if not in_session(row.get("dt"), session, normalized(source.get("source_timeframe"))):
            continue
        entry = float(row["close"])
        denominator_price = max(source_range, abs(entry) * 0.000001)
        path_result, gross_r, target, stop, first_touch_bars = event_path_result(
            rows,
            index,
            horizon_bars,
            side,
            denominator_price,
        )
        if path_result == "AMBIGUOUS_TARGET_AND_STOP_SAME_BAR":
            ambiguous_count += 1
            stress_r = -1.0 - stress_cost_r
        else:
            stress_r = gross_r - stress_cost_r
        cost_adjusted = gross_r - cost_r
        values.append(gross_r)
        cost_values.append(cost_adjusted)
        stress_values.append(stress_r)
        path_counts[path_result] += 1
        if path_result in {"TARGET_FIRST_PROXY_PATH", "HORIZON_CLOSE_TARGET_PROXY_RESULT"}:
            target_first_total += 1
        elif path_result in {"STOP_FIRST_PROXY_PATH", "HORIZON_CLOSE_STOP_PROXY_RESULT"}:
            stop_first_total += 1
        elif path_result == "NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT":
            neither_total += 1
        if cost_adjusted > 0:
            win_count += 1
        elif cost_adjusted < 0:
            loss_count += 1
        else:
            zero_count += 1
        dt_value = row.get("dt")
        month_counts[dt_value.strftime("%Y-%m") if isinstance(dt_value, datetime) else "UNPARSED_TIME"] += 1
        timestamp_counts[normalized(row.get("time"))] += 1
        if first_event is None:
            first_event = {
                "entry_reference": "source_bar_close_then_forward_horizon_path",
                "entry_reference_time": row.get("time"),
                "proxy_entry_price": rounded(entry),
                "proxy_denominator_price": rounded(denominator_price),
                "proxy_target_price": rounded(target),
                "proxy_stop_price": rounded(stop),
                "first_touch_bars": first_touch_bars,
            }

    effective_n = len(values)
    if effective_n == 0:
        return {
            "score_status": "NO_ELIGIBLE_SESSION_HORIZON_ENTRIES",
            "effective_n": 0,
            "horizon_bars": horizon_bars,
        }
    duplicate_count = sum(count - 1 for count in timestamp_counts.values() if count > 1)
    top_month = max(month_counts.values()) if month_counts else 0
    dominant_path = path_counts.most_common(1)[0][0] if path_counts else "NO_PATH_RESULT"
    first_event = first_event or {}
    expectancy = average(cost_values)
    stress_expectancy = average(stress_values)
    decision = expanded_market_decision(expectancy, stress_expectancy, effective_n, top_month / effective_n)
    return {
        "score_status": "EXPANDED_MARKET_PROXY_R_SCORED",
        "horizon_bars": horizon_bars,
        "entry_reference": first_event.get("entry_reference"),
        "entry_reference_time": first_event.get("entry_reference_time"),
        "proxy_entry_price": first_event.get("proxy_entry_price"),
        "proxy_denominator_price": first_event.get("proxy_denominator_price"),
        "proxy_target_price": first_event.get("proxy_target_price"),
        "proxy_stop_price": first_event.get("proxy_stop_price"),
        "path_order_result": dominant_path,
        "path_order_counts": dict(sorted(path_counts.items())),
        "fill_status": "FILLED_PROXY_FROM_OHLC_CLOSE_ENTRY",
        "gross_simulated_r": rounded(average(values)),
        "cost_adjusted_simulated_r": rounded(expectancy),
        "stress_simulated_r": rounded(stress_expectancy),
        "win_count": win_count,
        "loss_count": loss_count,
        "zero_count": zero_count,
        "target_first_count": target_first_total,
        "stop_first_count": stop_first_total,
        "neither_count": neither_total,
        "ambiguous_count": ambiguous_count,
        "effective_n": effective_n,
        "duplicate_row_count": duplicate_count,
        "effective_n_after_duplicate_collapse": effective_n - duplicate_count,
        "concentration_top_month_share": rounded(top_month / effective_n),
        "first_touch_bars": first_event.get("first_touch_bars"),
        "cost_adjustment_r": rounded(cost_r),
        "stress_cost_adjustment_r": rounded(stress_cost_r),
        "cost_proxy_status": cost_proxy.get("cost_proxy_status"),
        "cost_proxy_symbol": cost_proxy.get("cost_proxy_symbol"),
        "follow_inverse_default_off_avoid_class": class_from_decision(decision),
        "keep_kill_redesign_implement_decision": decision,
    }


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def expanded_market_decision(
    expectancy: float | None,
    stress_expectancy: float | None,
    effective_n: int,
    concentration_share: float,
) -> str:
    if expectancy is None:
        return "REDESIGN_EXPANDED_MARKET_REPLAY_IMPLEMENTATION"
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_UNDERPOWERED"
    if concentration_share > 0.70:
        return "REDESIGN_EXPANDED_MARKET_CONCENTRATION"
    if expectancy >= 0.10 and (stress_expectancy or expectancy) > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_PROXY_R_SCORER"
    if expectancy <= -0.20 and (stress_expectancy or expectancy) <= -0.20:
        return "KILL_EXPANDED_MARKET_BRANCH"
    if expectancy < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET"
    return "REDESIGN_EXPANDED_MARKET_SIGNAL_GEOMETRY"


def performance_row_from_score(
    seed_row: dict[str, Any],
    source: dict[str, Any],
    session: str,
    horizon_id: str,
    side: str,
    score: dict[str, Any],
    sequence: int,
    market_population_row_id: str | None,
) -> dict[str, Any]:
    row = {
        "expanded_market_performance_row_id": f"OHLC-GTOS-EXPANDED-MARKET-PROXY-R-PERF-{sequence:07d}",
        "input_expansion_matrix_row_id": seed_row.get("market_timeframe_session_horizon_expansion_row_id"),
        "input_market_population_row_id": market_population_row_id,
        "seed_source_component": seed_row.get("source_component"),
        "seed_decision": seed_row.get("decision"),
        "symbol": source.get("source_symbol") or seed_row.get("symbol"),
        "seed_symbol": seed_row.get("symbol"),
        "source_symbol": source.get("source_symbol"),
        "market_timeframe": source.get("source_timeframe"),
        "route_session": session,
        "seed_route_session": seed_row.get("route_session"),
        "horizon_id": horizon_id,
        "seed_horizon_id": seed_row.get("horizon_id"),
        "side": side,
        "source_path": source.get("source_path"),
        "source_file_sha256": source.get("source_file_sha256"),
        "source_access_status": source.get("source_access_status"),
        "source_rows_streamed": source.get("rows_streamed"),
        "source_parsed_ohlc_rows": source.get("parsed_ohlc_rows"),
        "source_first_time": source.get("first_time"),
        "source_last_time": source.get("last_time"),
        "score_status": score.get("score_status"),
        "entry_reference": score.get("entry_reference"),
        "entry_reference_time": score.get("entry_reference_time"),
        "proxy_entry_price": score.get("proxy_entry_price"),
        "proxy_denominator_price": score.get("proxy_denominator_price"),
        "proxy_target_price": score.get("proxy_target_price"),
        "proxy_stop_price": score.get("proxy_stop_price"),
        "path_order_result": score.get("path_order_result"),
        "path_order_counts": score.get("path_order_counts") or {},
        "fill_status": score.get("fill_status"),
        "gross_simulated_r": score.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": score.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": score.get("stress_simulated_r"),
        "cost_adjustment_r": score.get("cost_adjustment_r"),
        "stress_cost_adjustment_r": score.get("stress_cost_adjustment_r"),
        "cost_proxy_status": score.get("cost_proxy_status"),
        "cost_proxy_symbol": score.get("cost_proxy_symbol"),
        "win_count": int(score.get("win_count") or 0),
        "loss_count": int(score.get("loss_count") or 0),
        "zero_count": int(score.get("zero_count") or 0),
        "target_first_count": int(score.get("target_first_count") or 0),
        "stop_first_count": int(score.get("stop_first_count") or 0),
        "neither_count": int(score.get("neither_count") or 0),
        "ambiguous_count": int(score.get("ambiguous_count") or 0),
        "effective_n": int(score.get("effective_n") or 0),
        "duplicate_row_count": int(score.get("duplicate_row_count") or 0),
        "effective_n_after_duplicate_collapse": int(score.get("effective_n_after_duplicate_collapse") or 0),
        "concentration_top_month_share": score.get("concentration_top_month_share"),
        "follow_inverse_default_off_avoid_class": score.get("follow_inverse_default_off_avoid_class"),
        "keep_kill_redesign_implement_decision": score.get("keep_kill_redesign_implement_decision"),
    }
    return boundary_row(row)


def noncomputable_row(
    seed_row: dict[str, Any],
    reason: str,
    sequence: int,
    source_path: str | None = None,
    source_file_sha256: str | None = None,
    market_population_row_id: str | None = None,
    missing_fields: list[str] | None = None,
) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_noncomputable_row_id": f"OHLC-GTOS-EXPANDED-MARKET-PROXY-R-NONCOMP-{sequence:06d}",
            "input_expansion_matrix_row_id": seed_row.get("market_timeframe_session_horizon_expansion_row_id"),
            "input_market_population_row_id": market_population_row_id,
            "symbol": seed_row.get("symbol"),
            "route_session": seed_row.get("route_session"),
            "horizon_id": seed_row.get("horizon_id"),
            "source_component": seed_row.get("source_component"),
            "seed_decision": seed_row.get("decision"),
            "source_path": source_path,
            "source_file_sha256": source_file_sha256,
            "source_access_status": "NOT_SCORED",
            "noncomputability_reason": reason,
            "missing_simulated_fields": missing_fields or ["scoreable_ohlc_source_or_numeric_session_horizon"],
            "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_REPLAY_IMPLEMENTATION",
        }
    )


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("seed_source_component")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def aggregate_performance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    total_effective = sum(int(row.get("effective_n") or 0) for row in rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        gross_values = [as_float(row.get("gross_simulated_r")) for row in members]
        cost_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members]
        stress_values = [as_float(row.get("stress_simulated_r")) for row in members]
        gross = [value for value in gross_values if value is not None]
        cost = [value for value in cost_values if value is not None]
        stress = [value for value in stress_values if value is not None]
        effective_n = sum(int(row.get("effective_n") or 0) for row in members)
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        dominant_decision = decisions.most_common(1)[0][0] if decisions else "REDESIGN_EXPANDED_MARKET_SIGNAL_GEOMETRY"
        record = {
            "expanded_market_aggregate_row_id": f"OHLC-GTOS-EXPANDED-MARKET-PROXY-R-AGG-{len(output) + 1:06d}",
            "symbol": key[0],
            "market_timeframe": key[1],
            "route_session": key[2],
            "horizon_id": key[3],
            "side": key[4],
            "source_component": key[5],
            "follow_inverse_default_off_avoid_class": key[6],
            "row_count": len(members),
            "source_path_count": len({row.get("source_path") for row in members}),
            "simulated_r_row_count": len(cost),
            "effective_n": effective_n,
            "duplicate_row_count": sum(int(row.get("duplicate_row_count") or 0) for row in members),
            "effective_n_after_duplicate_collapse": sum(
                int(row.get("effective_n_after_duplicate_collapse") or 0) for row in members
            ),
            "win_count": sum(int(row.get("win_count") or 0) for row in members),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
            "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
            "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
            "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "expectancy_gross_simulated_r": rounded(average(gross)),
            "expectancy_cost_adjusted_simulated_r": rounded(average(cost)),
            "expectancy_stress_simulated_r": rounded(average(stress)),
            "average_win": rounded(
                average([as_float(row.get("cost_adjusted_simulated_r")) for row in members if as_float(row.get("cost_adjusted_simulated_r")) and as_float(row.get("cost_adjusted_simulated_r")) > 0])
            ),
            "average_loss": rounded(
                average([as_float(row.get("cost_adjusted_simulated_r")) for row in members if as_float(row.get("cost_adjusted_simulated_r")) and as_float(row.get("cost_adjusted_simulated_r")) < 0])
            ),
            "path_order_counts": dict(
                sorted(
                    Counter(
                        path
                        for row in members
                        for path, count in (row.get("path_order_counts") or {}).items()
                        for _ in range(int(count))
                    ).items()
                )
            ),
            "decision_counts": dict(sorted(decisions.items())),
            "concentration_share_of_all_effective_n": rounded(effective_n / total_effective),
            "keep_kill_redesign_implement_decision": dominant_decision,
        }
        output.append(boundary_row(record))
    return output


def system_row(
    performance_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    noncomputable_rows: list[dict[str, Any]],
    seed_consumption_rows: list[dict[str, Any]],
    discovered_source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-PROXY-R-SYSTEM-0001",
            "performance_rows": len(performance_rows),
            "aggregate_rows": len(aggregate_rows),
            "noncomputable_rows": len(noncomputable_rows),
            "seed_consumption_rows": len(seed_consumption_rows),
            "discovered_ohlc_source_rows": len(discovered_source_rows),
            "source_path_count": len({row.get("source_path") for row in performance_rows}),
            "symbol_count": len({row.get("symbol") for row in performance_rows}),
            "timeframe_count": len({row.get("market_timeframe") for row in performance_rows}),
            "total_effective_n": sum(int(row.get("effective_n") or 0) for row in performance_rows),
            "decision_counts": dict(
                sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in performance_rows).items())
            ),
        }
    )
