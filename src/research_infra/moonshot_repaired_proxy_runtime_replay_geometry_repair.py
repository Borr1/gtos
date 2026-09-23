"""Repair proxy replay geometry for executed repaired-proxy performance rows."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Any


RUNTIME_REPLAY_GEOMETRY_REPAIR_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_repair.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

TIME_COLUMNS = ("time", "timestamp", "datetime", "date")
NUMERIC_ALIASES = {
    "open": ("open", "o"),
    "high": ("high", "h"),
    "low": ("low", "l"),
    "close": ("close", "c"),
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
    output["runtime_replay_geometry_repair_surface"] = RUNTIME_REPLAY_GEOMETRY_REPAIR_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def normalized_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def resolve_columns(fieldnames: list[str]) -> dict[str, str | None]:
    normalized = {normalized_header(name): name for name in fieldnames}
    resolved: dict[str, str | None] = {}
    for logical, aliases in NUMERIC_ALIASES.items():
        resolved[logical] = next((normalized[alias] for alias in aliases if alias in normalized), None)
    resolved["time"] = next((normalized[alias] for alias in TIME_COLUMNS if alias in normalized), None)
    return resolved


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def index_by(rows: list[dict[str, Any]], field: str) -> dict[str, dict[str, Any]]:
    return {str(row.get(field)): row for row in rows}


def direction_from_side(side: Any) -> str | None:
    text = str(side or "")
    if text.startswith("LONG"):
        return "LONG"
    if text.startswith("SHORT"):
        return "SHORT"
    return None


def action_multiplier(row: dict[str, Any]) -> float:
    return -1.0 if row.get("default_off_avoid_class") == "avoid" else 1.0


def proxy_levels(entry_price: float | None, denominator_pct: float | None, direction: str | None) -> dict[str, Any]:
    if entry_price is None or denominator_pct is None or denominator_pct <= 0 or direction is None:
        return {
            "proxy_entry_price": entry_price,
            "proxy_denominator_pct": denominator_pct,
            "proxy_denominator_price": None,
            "proxy_target_price": None,
            "proxy_stop_price": None,
            "geometry_level_status": "GEOMETRY_LEVELS_MISSING_INPUT",
        }
    denominator_price = abs(entry_price) * denominator_pct
    if direction == "LONG":
        target = entry_price + denominator_price
        stop = entry_price - denominator_price
    else:
        target = entry_price - denominator_price
        stop = entry_price + denominator_price
    return {
        "proxy_entry_price": rounded(entry_price),
        "proxy_denominator_pct": rounded(denominator_pct),
        "proxy_denominator_price": rounded(denominator_price),
        "proxy_target_price": rounded(target),
        "proxy_stop_price": rounded(stop),
        "geometry_level_status": "PROXY_TARGET_STOP_LEVELS_DERIVED",
    }


def path_scan_key(source_path: str, direction: str | None, entry: float | None, target: float | None, stop: float | None) -> tuple[str, str, str, str, str]:
    return (
        source_path,
        normalized(direction),
        normalized(rounded(entry)),
        normalized(rounded(target)),
        normalized(rounded(stop)),
    )


def scan_proxy_path(
    repo_root: Path,
    source_path: str,
    direction: str | None,
    entry_price: float | None,
    target_price: float | None,
    stop_price: float | None,
) -> dict[str, Any]:
    path = repo_root / source_path
    source_exists = path.exists()
    if not source_exists:
        return {
            "source_path": source_path,
            "source_exists": False,
            "source_file_sha256": None,
            "path_scan_status": "SOURCE_FILE_MISSING",
            "path_order_result": "NO_PATH_ORDER_SOURCE_MISSING",
            "fill_status": "NO_FILL_SOURCE_MISSING",
            "first_touch_time": None,
            "first_touch_bar_index": None,
            "rows_streamed": 0,
            "parsed_ohlc_rows": 0,
        }
    if direction is None or entry_price is None or target_price is None or stop_price is None:
        return {
            "source_path": source_path,
            "source_exists": True,
            "source_file_sha256": sha256_file(path),
            "path_scan_status": "PROXY_LEVEL_INPUT_MISSING",
            "path_order_result": "NO_PATH_ORDER_PROXY_LEVEL_INPUT_MISSING",
            "fill_status": "NO_FILL_PROXY_LEVEL_INPUT_MISSING",
            "first_touch_time": None,
            "first_touch_bar_index": None,
            "rows_streamed": 0,
            "parsed_ohlc_rows": 0,
        }

    rows_streamed = 0
    parsed_ohlc_rows = 0
    first_touch_time = None
    first_touch_bar_index = None
    path_order_result = "NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT"
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = resolve_columns(reader.fieldnames or [])
        required_columns = (columns.get("high"), columns.get("low"), columns.get("close"))
        if None in required_columns:
            return {
                "source_path": source_path,
                "source_exists": True,
                "source_file_sha256": sha256_file(path),
                "path_scan_status": "SOURCE_OHLC_COLUMNS_MISSING",
                "path_order_result": "NO_PATH_ORDER_SOURCE_OHLC_COLUMNS_MISSING",
                "fill_status": "NO_FILL_SOURCE_OHLC_COLUMNS_MISSING",
                "first_touch_time": None,
                "first_touch_bar_index": None,
                "rows_streamed": 0,
                "parsed_ohlc_rows": 0,
            }
        for raw in reader:
            rows_streamed += 1
            high_value = as_float(raw.get(columns.get("high") or ""))
            low_value = as_float(raw.get(columns.get("low") or ""))
            close_value = as_float(raw.get(columns.get("close") or ""))
            if None in (high_value, low_value, close_value):
                continue
            parsed_ohlc_rows += 1
            row_time = raw.get(columns.get("time") or "")
            if direction == "LONG":
                target_touched = high_value >= target_price
                stop_touched = low_value <= stop_price
            else:
                target_touched = low_value <= target_price
                stop_touched = high_value >= stop_price
            if target_touched and stop_touched:
                path_order_result = "BOTH_PROXY_TARGET_AND_STOP_TOUCHED_SAME_BAR"
                first_touch_time = row_time
                first_touch_bar_index = parsed_ohlc_rows
                break
            if target_touched:
                path_order_result = "TARGET_FIRST_PROXY_PATH"
                first_touch_time = row_time
                first_touch_bar_index = parsed_ohlc_rows
                break
            if stop_touched:
                path_order_result = "STOP_FIRST_PROXY_PATH"
                first_touch_time = row_time
                first_touch_bar_index = parsed_ohlc_rows
                break

    return {
        "source_path": source_path,
        "source_exists": True,
        "source_file_sha256": sha256_file(path),
        "path_scan_status": "PROXY_PATH_SCAN_COMPLETE" if parsed_ohlc_rows else "SOURCE_HAS_NO_PARSED_OHLC_ROWS",
        "path_order_result": path_order_result if parsed_ohlc_rows else "NO_PATH_ORDER_SOURCE_HAS_NO_PARSED_OHLC_ROWS",
        "fill_status": "PROXY_FILLED_FROM_SOURCE_FIRST_OPEN" if parsed_ohlc_rows else "NO_FILL_SOURCE_HAS_NO_PARSED_OHLC_ROWS",
        "first_touch_time": first_touch_time,
        "first_touch_bar_index": first_touch_bar_index,
        "rows_streamed": rows_streamed,
        "parsed_ohlc_rows": parsed_ohlc_rows,
    }


def underlying_path_r(
    path_order_result: str,
    direction: str | None,
    entry_price: float | None,
    last_close: float | None,
    denominator_price: float | None,
) -> float | None:
    if path_order_result == "TARGET_FIRST_PROXY_PATH":
        return 1.0
    if path_order_result == "STOP_FIRST_PROXY_PATH":
        return -1.0
    if path_order_result == "BOTH_PROXY_TARGET_AND_STOP_TOUCHED_SAME_BAR":
        return None
    if (
        path_order_result == "NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT"
        and direction
        and entry_price is not None
        and last_close is not None
        and denominator_price
    ):
        raw = (last_close - entry_price) / denominator_price
        return raw if direction == "LONG" else -raw
    return None


def row_result_class(value: float | None, ambiguous: bool, no_fill: bool) -> str:
    if no_fill:
        return "NO_FILL"
    if ambiguous or value is None:
        return "AMBIGUOUS"
    if value > 0:
        return "WIN"
    if value < 0:
        return "LOSS"
    return "FLAT"


def remaining_missing_fields(
    perf_row: dict[str, Any],
    path_result: str,
    action_adjusted_r: float | None,
) -> list[str]:
    fields = list(perf_row.get("missing_simulated_fields") or [])
    if path_result == "BOTH_PROXY_TARGET_AND_STOP_TOUCHED_SAME_BAR":
        fields.append("intrabar_target_stop_order")
    if action_adjusted_r is None:
        fields.append("deterministic_geometry_simulated_r")
    return sorted(set(fields))


def geometry_repair_row(
    perf_row: dict[str, Any],
    numeric_row: dict[str, Any] | None,
    metric_row: dict[str, Any] | None,
    path_scan: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    direction = direction_from_side(perf_row.get("side"))
    entry_price = as_float(metric_row.get("first_open")) if metric_row else None
    last_close = as_float(metric_row.get("last_close")) if metric_row else None
    levels = proxy_levels(entry_price, as_float(perf_row.get("stop_target_or_proxy_denominator_value")), direction)
    underlying_r = underlying_path_r(
        path_scan.get("path_order_result"),
        direction,
        entry_price,
        last_close,
        as_float(levels.get("proxy_denominator_price")),
    )
    multiplier = action_multiplier(perf_row)
    action_r = underlying_r * multiplier if underlying_r is not None else None
    cost_penalty = as_float(perf_row.get("cost_adjustment_r")) or 0.0
    cost_adjusted = action_r - cost_penalty if action_r is not None else None
    ambiguous = path_scan.get("path_order_result") == "BOTH_PROXY_TARGET_AND_STOP_TOUCHED_SAME_BAR"
    no_fill = str(path_scan.get("fill_status") or "").startswith("NO_FILL")
    stress = -1.0 - cost_penalty if ambiguous and not no_fill else cost_adjusted
    result_class = row_result_class(cost_adjusted, ambiguous, no_fill)
    missing_fields = remaining_missing_fields(perf_row, str(path_scan.get("path_order_result")), action_r)

    row = {
        "geometry_repair_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-ROW-{sequence:06d}",
        "input_performance_row_id": perf_row.get("performance_row_id"),
        "input_replay_numeric_event_row_id": perf_row.get("input_replay_numeric_event_row_id"),
        "input_source_numeric_metric_row_id": numeric_row.get("input_source_numeric_metric_row_id") if numeric_row else None,
        "branch": perf_row.get("branch"),
        "family": perf_row.get("family"),
        "symbol": perf_row.get("symbol"),
        "route_session": perf_row.get("route_session"),
        "market_timeframe": perf_row.get("market_timeframe"),
        "horizon_id": perf_row.get("horizon_id"),
        "source_component": perf_row.get("source_component"),
        "follow_inverse_default_off_avoid_class": perf_row.get("follow_inverse_default_off_avoid_class"),
        "default_off_avoid_class": perf_row.get("default_off_avoid_class"),
        "proxy_trade_direction": direction,
        "source_path": path_scan.get("source_path"),
        "source_file_sha256": path_scan.get("source_file_sha256"),
        "source_first_time": metric_row.get("first_time") if metric_row else None,
        "source_last_time": metric_row.get("last_time") if metric_row else None,
        "source_parsed_ohlc_rows": metric_row.get("parsed_ohlc_rows") if metric_row else None,
        "proxy_entry_price": levels.get("proxy_entry_price"),
        "proxy_stop_price": levels.get("proxy_stop_price"),
        "proxy_target_price": levels.get("proxy_target_price"),
        "proxy_denominator_pct": levels.get("proxy_denominator_pct"),
        "proxy_denominator_price": levels.get("proxy_denominator_price"),
        "geometry_level_status": levels.get("geometry_level_status"),
        "path_scan_status": path_scan.get("path_scan_status"),
        "path_order_result": path_scan.get("path_order_result"),
        "fill_status": path_scan.get("fill_status"),
        "first_touch_time": path_scan.get("first_touch_time"),
        "first_touch_bar_index": path_scan.get("first_touch_bar_index"),
        "underlying_proxy_path_r": rounded(underlying_r),
        "action_adjusted_geometry_r": rounded(action_r),
        "cost_adjustment_r": rounded(cost_penalty),
        "cost_adjusted_geometry_r": rounded(cost_adjusted),
        "stress_geometry_r": rounded(stress),
        "geometry_result_class": result_class,
        "win_count": 1 if result_class == "WIN" else 0,
        "loss_count": 1 if result_class == "LOSS" else 0,
        "flat_count": 1 if result_class == "FLAT" else 0,
        "no_fill_count": 1 if result_class == "NO_FILL" else 0,
        "ambiguous_count": 1 if result_class == "AMBIGUOUS" else 0,
        "target_first_count": 1 if path_scan.get("path_order_result") == "TARGET_FIRST_PROXY_PATH" else 0,
        "stop_first_count": 1 if path_scan.get("path_order_result") == "STOP_FIRST_PROXY_PATH" else 0,
        "neither_count": 1 if path_scan.get("path_order_result") == "NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT" else 0,
        "remaining_missing_geometry_fields": missing_fields,
        "remaining_missing_geometry_field_count": len(missing_fields),
    }
    row["geometry_repair_decision"] = geometry_repair_decision(row)
    return boundary_row(row)


def geometry_repair_decision(row: dict[str, Any]) -> str:
    result_class = row.get("geometry_result_class")
    value = as_float(row.get("cost_adjusted_geometry_r"))
    cls = row.get("default_off_avoid_class")
    if result_class == "NO_FILL":
        return "CONCRETE_REPLAY_SOURCE_REPAIR_REQUIRED"
    if result_class == "AMBIGUOUS":
        return "CONCRETE_INTRABAR_PATH_REPLAY_REQUIRED"
    if cls == "avoid":
        if value is not None and value > 0:
            return "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY"
        if value is not None and value < 0:
            return "KILL_AVOID_COMPARATOR_FROM_GEOMETRY"
        return "REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY"
    if value is not None and value >= 0.25:
        return "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE"
    if value is not None and value < -0.10:
        return "KILL_DEFAULT_OFF_FROM_GEOMETRY"
    return "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY"


def path_scan_rows(scan_cache: dict[tuple[str, str, str, str, str], dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for key, scan in sorted(scan_cache.items()):
        row = dict(scan)
        row.update(
            {
                "path_scan_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-SCAN-{len(output) + 1:05d}",
                "path_scan_cache_key": "|".join(key),
            }
        )
        output.append(boundary_row(row))
    return output


def geometry_repair_rows(
    perf_rows: list[dict[str, Any]],
    replay_numeric_rows: list[dict[str, Any]],
    source_metric_rows: list[dict[str, Any]],
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    numeric_by_id = index_by(replay_numeric_rows, "replay_numeric_event_row_id")
    metric_by_id = index_by(source_metric_rows, "source_numeric_metric_row_id")
    scan_cache: dict[tuple[str, str, str, str, str], dict[str, Any]] = {}
    output: list[dict[str, Any]] = []
    for perf in perf_rows:
        numeric = numeric_by_id.get(str(perf.get("input_replay_numeric_event_row_id")))
        metric = metric_by_id.get(str(numeric.get("input_source_numeric_metric_row_id"))) if numeric else None
        direction = direction_from_side(perf.get("side"))
        entry = as_float(metric.get("first_open")) if metric else None
        levels = proxy_levels(entry, as_float(perf.get("stop_target_or_proxy_denominator_value")), direction)
        source_path = str(numeric.get("market_source_path") if numeric else "")
        key = path_scan_key(
            source_path,
            direction,
            entry,
            as_float(levels.get("proxy_target_price")),
            as_float(levels.get("proxy_stop_price")),
        )
        if key not in scan_cache:
            scan_cache[key] = scan_proxy_path(
                repo_root,
                source_path,
                direction,
                entry,
                as_float(levels.get("proxy_target_price")),
                as_float(levels.get("proxy_stop_price")),
            )
        output.append(geometry_repair_row(perf, numeric, metric, scan_cache[key], len(output) + 1))
    return output, path_scan_rows(scan_cache)


def aggregate_key(row: dict[str, Any]) -> tuple[str, str, str, str, str, str, str, str]:
    return (
        normalized(row.get("branch")),
        normalized(row.get("family")),
        normalized(row.get("symbol")),
        normalized(row.get("route_session")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def aggregate_decision(record: dict[str, Any]) -> str:
    expectancy = as_float(record.get("expectancy_cost_adjusted_geometry_r"))
    deterministic = int(record.get("deterministic_geometry_r_rows") or 0)
    effective_n = int(record.get("effective_n") or 0)
    ambiguous = int(record.get("ambiguous_count") or 0)
    cls = record.get("default_off_avoid_class")
    if deterministic == 0:
        return "CONCRETE_INTRABAR_PATH_REPLAY_REQUIRED"
    if ambiguous > deterministic:
        return "REDESIGN_INTRABAR_PATH_ORDER_BEFORE_IMPLEMENTATION"
    if cls == "avoid":
        if expectancy is not None and expectancy > 0 and effective_n >= 20:
            return "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY"
        if expectancy is not None and expectancy < 0:
            return "KILL_AVOID_COMPARATOR_FROM_GEOMETRY"
        return "REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY"
    if expectancy is not None and expectancy >= 0.25 and effective_n >= 20:
        return "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE"
    if expectancy is not None and expectancy < -0.10:
        return "KILL_DEFAULT_OFF_FROM_GEOMETRY"
    return "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY"


def aggregate_geometry_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    total = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        values = [as_float(row.get("cost_adjusted_geometry_r")) for row in members]
        values = [value for value in values if value is not None]
        stress_values = [as_float(row.get("stress_geometry_r")) for row in members]
        stress_values = [value for value in stress_values if value is not None]
        win_values = [as_float(row.get("cost_adjusted_geometry_r")) for row in members if row.get("geometry_result_class") == "WIN"]
        loss_values = [as_float(row.get("cost_adjusted_geometry_r")) for row in members if row.get("geometry_result_class") == "LOSS"]
        effective_keys = {normalized(row.get("input_replay_numeric_event_row_id")) for row in members}
        path_counts = Counter(row.get("path_order_result") for row in members)
        record = {
            "aggregate_geometry_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-AGG-{len(output) + 1:05d}"
            ),
            "branch": key[0],
            "family": key[1],
            "symbol": key[2],
            "route_session": key[3],
            "market_timeframe": key[4],
            "horizon_id": key[5],
            "source_component": key[6],
            "follow_inverse_default_off_avoid_class": key[7],
            "default_off_avoid_class": members[0].get("default_off_avoid_class"),
            "row_count": len(members),
            "deterministic_geometry_r_rows": len(values),
            "win_count": sum(int(row.get("win_count") or 0) for row in members),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
            "flat_count": sum(int(row.get("flat_count") or 0) for row in members),
            "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in members),
            "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
            "expectancy_cost_adjusted_geometry_r": rounded(average(values)),
            "expectancy_stress_geometry_r": rounded(average(stress_values)),
            "average_win": rounded(average([value for value in win_values if value is not None])),
            "average_loss": rounded(average([value for value in loss_values if value is not None])),
            "effective_n": len(effective_keys),
            "duplicate_row_count": len(members) - len(effective_keys),
            "duplicate_inflation_ratio": rounded(len(members) / len(effective_keys)) if effective_keys else None,
            "concentration_share_of_all_rows": rounded(len(members) / total),
            "path_order_counts": dict(sorted(path_counts.items())),
        }
        record["geometry_keep_kill_redesign_implement_decision"] = aggregate_decision(record)
        output.append(boundary_row(record))
    return output


def missing_geometry_field_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        for field in row.get("remaining_missing_geometry_fields") or []:
            output.append(
                boundary_row(
                    {
                        "missing_geometry_field_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-MISSING-{len(output) + 1:06d}"
                        ),
                        "geometry_repair_row_id": row.get("geometry_repair_row_id"),
                        "input_performance_row_id": row.get("input_performance_row_id"),
                        "missing_geometry_field": field,
                        "geometry_repair_decision": row.get("geometry_repair_decision"),
                        "source_path": row.get("source_path"),
                        "source_file_sha256": row.get("source_file_sha256"),
                        "symbol": row.get("symbol"),
                        "route_session": row.get("route_session"),
                        "market_timeframe": row.get("market_timeframe"),
                        "horizon_id": row.get("horizon_id"),
                    }
                )
            )
    return output


def system_geometry_rows(
    rows: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    path_scans: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("geometry_keep_kill_redesign_implement_decision") for row in aggregates)
    row_decisions = Counter(row.get("geometry_repair_decision") for row in rows)
    return [
        boundary_row(
            {
                "system_geometry_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-SYSTEM-00001",
                "geometry_repair_rows": len(rows),
                "aggregate_geometry_rows": len(aggregates),
                "path_scan_rows": len(path_scans),
                "missing_geometry_field_rows": len(missing_rows),
                "deterministic_geometry_r_rows": sum(row.get("action_adjusted_geometry_r") is not None for row in rows),
                "ambiguous_rows": sum(int(row.get("ambiguous_count") or 0) for row in rows),
                "no_fill_rows": sum(int(row.get("no_fill_count") or 0) for row in rows),
                "target_first_rows": sum(int(row.get("target_first_count") or 0) for row in rows),
                "stop_first_rows": sum(int(row.get("stop_first_count") or 0) for row in rows),
                "neither_rows": sum(int(row.get("neither_count") or 0) for row in rows),
                "geometry_repair_decision_counts": dict(sorted(row_decisions.items())),
                "aggregate_decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
