"""Streaming numeric execution for repaired-proxy replay contracts."""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Any


REPLAY_NUMERIC_SURFACE = "src/research_infra/moonshot_repaired_proxy_replay_numeric_execution.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

TIME_COLUMNS = ("time", "timestamp", "datetime", "date")
NUMERIC_ALIASES = {
    "open": ("open", "o"),
    "high": ("high", "h"),
    "low": ("low", "l"),
    "close": ("close", "c"),
    "spread": ("spread",),
    "tick_volume": ("tick_volume", "volume", "vol"),
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
    output["replay_numeric_surface"] = REPLAY_NUMERIC_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def to_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalized_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    normalized = {normalized_header(name): name for name in fieldnames}
    resolved: dict[str, str | None] = {}
    for logical, aliases in NUMERIC_ALIASES.items():
        resolved[logical] = next((normalized[alias] for alias in aliases if alias in normalized), None)
    resolved["time"] = next((normalized[alias] for alias in TIME_COLUMNS if alias in normalized), None)
    return resolved


def safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return numerator / denominator


def round_or_none(value: float | None, places: int = 10) -> float | None:
    return round(value, places) if value is not None else None


def source_numeric_metric_row(market_or_control_row: dict[str, Any], repo_root: Path, index: int) -> dict[str, Any]:
    source_path = str(market_or_control_row.get("market_source_path") or market_or_control_row.get("source_path") or "")
    path = repo_root / source_path
    source_exists = path.exists()
    fieldnames: list[str] = []
    columns: dict[str, str | None] = {}
    rows_streamed = 0
    parsed_ohlc_rows = 0
    first_time = None
    last_time = None
    first_open = None
    first_close = None
    last_close = None
    prev_close = None
    high_max = None
    low_min = None
    range_sum = 0.0
    range_pct_sum = 0.0
    range_pct_count = 0
    max_range_pct = None
    abs_close_change_pct_sum = 0.0
    abs_close_change_pct_count = 0
    spread_sum = 0.0
    spread_count = 0
    spread_max = None
    volume_sum = 0.0
    volume_count = 0
    parse_error_rows = 0

    if source_exists:
        with open(path, "r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            fieldnames = reader.fieldnames or []
            columns = resolve_columns(fieldnames)
            for raw in reader:
                rows_streamed += 1
                open_value = to_float(raw.get(columns.get("open") or ""))
                high_value = to_float(raw.get(columns.get("high") or ""))
                low_value = to_float(raw.get(columns.get("low") or ""))
                close_value = to_float(raw.get(columns.get("close") or ""))
                if None in (open_value, high_value, low_value, close_value):
                    parse_error_rows += 1
                    continue
                parsed_ohlc_rows += 1
                row_time = raw.get(columns.get("time") or "")
                if first_time is None:
                    first_time = row_time
                    first_open = open_value
                    first_close = close_value
                last_time = row_time
                last_close = close_value
                high_max = high_value if high_max is None else max(high_max, high_value)
                low_min = low_value if low_min is None else min(low_min, low_value)
                row_range = high_value - low_value
                range_sum += row_range
                range_pct = safe_ratio(row_range, close_value)
                if range_pct is not None:
                    range_pct_sum += range_pct
                    range_pct_count += 1
                    max_range_pct = range_pct if max_range_pct is None else max(max_range_pct, range_pct)
                if prev_close not in (None, 0):
                    abs_change = abs(close_value - prev_close) / abs(prev_close)
                    abs_close_change_pct_sum += abs_change
                    abs_close_change_pct_count += 1
                prev_close = close_value
                spread_value = to_float(raw.get(columns.get("spread") or ""))
                if spread_value is not None:
                    spread_sum += spread_value
                    spread_count += 1
                    spread_max = spread_value if spread_max is None else max(spread_max, spread_value)
                volume_value = to_float(raw.get(columns.get("tick_volume") or ""))
                if volume_value is not None:
                    volume_sum += volume_value
                    volume_count += 1

    close_return_abs = None
    close_return_pct = None
    if first_open not in (None, 0) and last_close is not None:
        close_return_abs = last_close - first_open
        close_return_pct = close_return_abs / first_open
    return boundary_row(
        {
            "source_numeric_metric_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-SRC-{index:05d}",
            "input_market_population_or_control_row_id": market_or_control_row.get(
                "input_market_replay_population_row_id"
            ),
            "symbol": market_or_control_row.get("symbol"),
            "timeframe": market_or_control_row.get("market_timeframe") or market_or_control_row.get("timeframe"),
            "source_path": source_path,
            "source_exists": source_exists,
            "fieldnames": fieldnames,
            "resolved_columns": columns,
            "rows_streamed": rows_streamed,
            "parsed_ohlc_rows": parsed_ohlc_rows,
            "parse_error_rows": parse_error_rows,
            "first_time": first_time,
            "last_time": last_time,
            "first_open": round_or_none(first_open),
            "first_close": round_or_none(first_close),
            "last_close": round_or_none(last_close),
            "high_max": round_or_none(high_max),
            "low_min": round_or_none(low_min),
            "close_return_abs": round_or_none(close_return_abs),
            "close_return_pct": round_or_none(close_return_pct),
            "mean_range": round_or_none(range_sum / parsed_ohlc_rows if parsed_ohlc_rows else None),
            "mean_range_pct": round_or_none(range_pct_sum / range_pct_count if range_pct_count else None),
            "max_range_pct": round_or_none(max_range_pct),
            "mean_abs_close_change_pct": round_or_none(
                abs_close_change_pct_sum / abs_close_change_pct_count if abs_close_change_pct_count else None
            ),
            "spread_mean": round_or_none(spread_sum / spread_count if spread_count else None),
            "spread_max": round_or_none(spread_max),
            "spread_rows": spread_count,
            "tick_volume_mean": round_or_none(volume_sum / volume_count if volume_count else None),
            "tick_volume_rows": volume_count,
            "numeric_metric_status": (
                "SOURCE_NUMERIC_METRICS_READY" if source_exists and parsed_ohlc_rows else "SOURCE_NUMERIC_REPAIR_REQUIRED"
            ),
        }
    )


def replay_numeric_event_row(
    contract_row: dict[str, Any],
    metric_row: dict[str, Any],
    scope_row: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    if metric_row.get("numeric_metric_status") == "SOURCE_NUMERIC_METRICS_READY":
        status = "REPLAY_NUMERIC_EVENT_READY"
    else:
        status = "REPLAY_NUMERIC_EVENT_SOURCE_REPAIR_REQUIRED"
    return boundary_row(
        {
            "replay_numeric_event_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-EVENT-{index:06d}",
            "input_replay_scope_contract_row_id": contract_row.get("replay_scope_contract_row_id"),
            "input_registry_scope_row_id": contract_row.get("input_registry_scope_row_id"),
            "input_source_numeric_metric_row_id": metric_row.get("source_numeric_metric_row_id"),
            "registry_family": contract_row.get("registry_family"),
            "aggregate_scope_key": contract_row.get("aggregate_scope_key"),
            "symbol": contract_row.get("symbol"),
            "route_session": contract_row.get("route_session"),
            "horizon_id": contract_row.get("horizon_id"),
            "source_component": contract_row.get("source_component"),
            "market_timeframe": contract_row.get("market_timeframe"),
            "market_source_path": contract_row.get("market_source_path"),
            "replay_contract_action": contract_row.get("replay_contract_action"),
            "registry_scope_score_mean": (scope_row or {}).get("score_mean"),
            "registry_scope_score_count": (scope_row or {}).get("score_count"),
            "source_rows_streamed": metric_row.get("rows_streamed"),
            "source_parsed_ohlc_rows": metric_row.get("parsed_ohlc_rows"),
            "source_close_return_pct": metric_row.get("close_return_pct"),
            "source_mean_range_pct": metric_row.get("mean_range_pct"),
            "source_mean_abs_close_change_pct": metric_row.get("mean_abs_close_change_pct"),
            "source_spread_mean": metric_row.get("spread_mean"),
            "source_tick_volume_mean": metric_row.get("tick_volume_mean"),
            "replay_numeric_event_status": status,
            "replay_numeric_action": (
                "EXECUTE_REGISTERED_SCOPE_ON_STREAMED_SOURCE_METRICS"
                if status == "REPLAY_NUMERIC_EVENT_READY"
                else "REPAIR_SOURCE_BEFORE_SCOPE_REPLAY"
            ),
        }
    )


def control_numeric_event_row(
    control_row: dict[str, Any],
    metric_row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    if metric_row.get("numeric_metric_status") == "SOURCE_NUMERIC_METRICS_READY":
        status = "CONTROL_NUMERIC_EVENT_READY"
    else:
        status = "CONTROL_NUMERIC_EVENT_SOURCE_REPAIR_REQUIRED"
    return boundary_row(
        {
            "control_numeric_event_row_id": f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-CONTROL-{index:05d}",
            "input_control_population_contract_row_id": control_row.get("control_population_contract_row_id"),
            "input_source_numeric_metric_row_id": metric_row.get("source_numeric_metric_row_id"),
            "symbol": control_row.get("symbol"),
            "timeframe": control_row.get("timeframe"),
            "source_path": control_row.get("source_path"),
            "control_population_action": control_row.get("control_population_action"),
            "source_rows_streamed": metric_row.get("rows_streamed"),
            "source_parsed_ohlc_rows": metric_row.get("parsed_ohlc_rows"),
            "source_close_return_pct": metric_row.get("close_return_pct"),
            "source_mean_range_pct": metric_row.get("mean_range_pct"),
            "source_mean_abs_close_change_pct": metric_row.get("mean_abs_close_change_pct"),
            "source_spread_mean": metric_row.get("spread_mean"),
            "source_tick_volume_mean": metric_row.get("tick_volume_mean"),
            "control_numeric_event_status": status,
            "control_numeric_action": (
                "JOIN_AS_CROSS_MARKET_NUMERIC_CONTROL"
                if status == "CONTROL_NUMERIC_EVENT_READY"
                else "REPAIR_CONTROL_SOURCE_BEFORE_JOIN"
            ),
        }
    )


def scope_row_lookup(
    default_scope_rows: list[dict[str, Any]],
    avoid_scope_rows: list[dict[str, Any]],
    repair_scope_rows: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    lookup: dict[str, dict[str, Any]] = {}
    for row in default_scope_rows:
        lookup[str(row.get("default_off_scope_registry_row_id") or "")] = row
    for row in avoid_scope_rows:
        lookup[str(row.get("avoid_scope_registry_row_id") or "")] = row
    for row in repair_scope_rows:
        lookup[str(row.get("repair_scope_contract_source_row_id") or "")] = row
    return lookup


def metric_lookup(metric_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("source_path") or ""): row for row in metric_rows}


def symbol_summary_rows(
    replay_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    symbols = sorted(
        {
            str(row.get("symbol") or "")
            for row in [*replay_rows, *control_rows]
            if row.get("symbol")
        }
    )
    output: list[dict[str, Any]] = []
    for index, symbol in enumerate(symbols, 1):
        replay_symbol_rows = [row for row in replay_rows if row.get("symbol") == symbol]
        control_symbol_rows = [row for row in control_rows if row.get("symbol") == symbol]
        output.append(
            boundary_row(
                {
                    "replay_numeric_symbol_summary_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-SYMBOL-{index:04d}"
                    ),
                    "symbol": symbol,
                    "replay_numeric_event_rows": len(replay_symbol_rows),
                    "control_numeric_event_rows": len(control_symbol_rows),
                    "replay_status_counts": dict(
                        sorted(Counter(str(row.get("replay_numeric_event_status") or "") for row in replay_symbol_rows).items())
                    ),
                    "control_status_counts": dict(
                        sorted(Counter(str(row.get("control_numeric_event_status") or "") for row in control_symbol_rows).items())
                    ),
                }
            )
        )
    return output


def bucket_rows(
    source_metric_rows: list[dict[str, Any]],
    replay_rows: list[dict[str, Any]],
    control_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("source_metric_status", source_metric_rows, "numeric_metric_status"),
        ("replay_numeric_status", replay_rows, "replay_numeric_event_status"),
        ("replay_numeric_action", replay_rows, "replay_numeric_action"),
        ("registry_family", replay_rows, "registry_family"),
        ("control_numeric_status", control_rows, "control_numeric_event_status"),
        ("control_numeric_action", control_rows, "control_numeric_action"),
    ]
    for family, rows, field in specs:
        counter = Counter(str(row.get(field) or "") for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "replay_numeric_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-REPLAY-NUM-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
