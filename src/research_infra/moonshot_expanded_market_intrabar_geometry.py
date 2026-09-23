"""Intrabar high-low geometry replay for expanded-market proxy-R rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    horizon_bar_count,
    in_session,
    median_range,
)


EXPANDED_MARKET_INTRABAR_GEOMETRY_SURFACE = "src/research_infra/moonshot_expanded_market_intrabar_geometry.py"
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"


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
    output["expanded_market_intrabar_geometry_surface"] = EXPANDED_MARKET_INTRABAR_GEOMETRY_SURFACE
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


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def profile_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("source_path")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("cost_adjustment_r")),
        normalized(row.get("stress_cost_adjustment_r")),
    )


def intrabar_path_result(
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
    for forward_index in range(index + 1, end_index + 1):
        high = float(rows[forward_index]["high"])
        low = float(rows[forward_index]["low"])
        if side == "LONG":
            target_hit = high >= target
            stop_hit = low <= stop
        else:
            target_hit = low <= target
            stop_hit = high >= stop
        if target_hit and stop_hit:
            return "AMBIGUOUS_TARGET_AND_STOP_SAME_BAR", 0.0, target, stop, forward_index - index
        if target_hit:
            return "TARGET_FIRST_INTRABAR_PATH", 1.0, target, stop, forward_index - index
        if stop_hit:
            return "STOP_FIRST_INTRABAR_PATH", -1.0, target, stop, forward_index - index
    exit_close = float(rows[end_index]["close"])
    raw = (exit_close - entry) / denominator_price
    if side == "SHORT":
        raw = -raw
    return "NEITHER_INTRABAR_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT", raw, target, stop, None


def month_key(dt_value: Any) -> str:
    if isinstance(dt_value, datetime):
        return dt_value.strftime("%Y-%m")
    return "UNPARSED_TIME"


def intrabar_profile(row: dict[str, Any], ohlc_rows: list[dict[str, Any]]) -> dict[str, Any]:
    horizon_bars = horizon_bar_count(normalized(row.get("horizon_id")))
    if horizon_bars is None:
        return {"profile_status": "HORIZON_NOT_NUMERIC", "effective_n": 0}
    if len(ohlc_rows) <= horizon_bars:
        return {"profile_status": "SOURCE_UNDER_HORIZON_LENGTH", "effective_n": 0}
    source_range = median_range(ohlc_rows)
    if source_range is None or source_range <= 0:
        return {"profile_status": "SOURCE_DENOMINATOR_RANGE_UNAVAILABLE", "effective_n": 0}

    session = normalized(row.get("route_session"))
    timeframe = normalized(row.get("market_timeframe"))
    side = normalized(row.get("side"))
    cost_r = as_float(row.get("cost_adjustment_r")) or 0.0
    stress_cost_r = as_float(row.get("stress_cost_adjustment_r"))
    if stress_cost_r is None:
        stress_cost_r = cost_r

    gross_values: list[float] = []
    cost_values: list[float] = []
    stress_values: list[float] = []
    wins: list[float] = []
    losses: list[float] = []
    path_counts: Counter[str] = Counter()
    month_counts: Counter[str] = Counter()
    timestamp_counts: Counter[str] = Counter()
    first_event: dict[str, Any] | None = None
    first_touch_values: list[int] = []

    for index in range(0, len(ohlc_rows) - horizon_bars):
        source_row = ohlc_rows[index]
        if not in_session(source_row.get("dt"), session, timeframe):
            continue
        entry = float(source_row["close"])
        denominator = max(source_range, abs(entry) * 0.000001)
        path_result, gross_r, target, stop, first_touch_bars = intrabar_path_result(
            ohlc_rows,
            index,
            horizon_bars,
            side,
            denominator,
        )
        cost_adjusted = gross_r - cost_r
        stress_r = (-1.0 - stress_cost_r) if path_result == "AMBIGUOUS_TARGET_AND_STOP_SAME_BAR" else gross_r - stress_cost_r
        gross_values.append(gross_r)
        cost_values.append(cost_adjusted)
        stress_values.append(stress_r)
        if cost_adjusted > 0:
            wins.append(cost_adjusted)
        elif cost_adjusted < 0:
            losses.append(cost_adjusted)
        path_counts[path_result] += 1
        month_counts[month_key(source_row.get("dt"))] += 1
        timestamp_counts[normalized(source_row.get("time"))] += 1
        if first_touch_bars is not None:
            first_touch_values.append(first_touch_bars)
        if first_event is None:
            first_event = {
                "entry_reference": "source_bar_close_then_intrabar_high_low_path",
                "entry_reference_time": source_row.get("time"),
                "proxy_entry_price": rounded(entry),
                "proxy_denominator_price": rounded(denominator),
                "proxy_target_price": rounded(target),
                "proxy_stop_price": rounded(stop),
                "first_touch_bars": first_touch_bars,
            }

    effective_n = len(cost_values)
    if effective_n == 0:
        return {
            "profile_status": "NO_ELIGIBLE_INTRABAR_SESSION_HORIZON_ENTRIES",
            "effective_n": 0,
            "horizon_bars": horizon_bars,
        }
    top_month = max(month_counts.values()) if month_counts else 0
    duplicate_count = sum(count - 1 for count in timestamp_counts.values() if count > 1)
    dominant_path = path_counts.most_common(1)[0][0] if path_counts else "NO_INTRABAR_PATH_RESULT"
    expectancy = average(cost_values)
    stress_expectancy = average(stress_values)
    decision = intrabar_decision(expectancy, stress_expectancy, effective_n, top_month / effective_n)
    first_event = first_event or {}
    return {
        "profile_status": "EXPANDED_MARKET_INTRABAR_GEOMETRY_REPLAYED",
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
        "gross_simulated_r": rounded(average(gross_values)),
        "cost_adjusted_simulated_r": rounded(expectancy),
        "stress_simulated_r": rounded(stress_expectancy),
        "win_count": len(wins),
        "loss_count": len(losses),
        "zero_count": sum(1 for value in cost_values if value == 0),
        "average_win": rounded(average(wins)),
        "average_loss": rounded(average(losses)),
        "target_first_count": path_counts.get("TARGET_FIRST_INTRABAR_PATH", 0),
        "stop_first_count": path_counts.get("STOP_FIRST_INTRABAR_PATH", 0),
        "neither_count": path_counts.get("NEITHER_INTRABAR_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT", 0),
        "ambiguous_count": path_counts.get("AMBIGUOUS_TARGET_AND_STOP_SAME_BAR", 0),
        "effective_n": effective_n,
        "duplicate_row_count": duplicate_count,
        "effective_n_after_duplicate_collapse": effective_n - duplicate_count,
        "concentration_top_month_share": rounded(top_month / effective_n),
        "first_touch_bars": first_event.get("first_touch_bars"),
        "average_first_touch_bars": rounded(average([float(value) for value in first_touch_values])),
        "cost_adjustment_r": rounded(cost_r),
        "stress_cost_adjustment_r": rounded(stress_cost_r),
        "follow_inverse_default_off_avoid_class": class_from_decision(decision),
        "keep_kill_redesign_implement_decision": decision,
    }


def intrabar_decision(
    expectancy: float | None,
    stress_expectancy: float | None,
    effective_n: int,
    concentration_share: float,
) -> str:
    if expectancy is None:
        return "REDESIGN_EXPANDED_MARKET_INTRABAR_REPLAY_IMPLEMENTATION"
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_INTRABAR_UNDERPOWERED"
    if concentration_share > 0.70:
        return "REDESIGN_EXPANDED_MARKET_INTRABAR_CONCENTRATION"
    if expectancy >= 0.10 and (stress_expectancy or expectancy) > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_INTRABAR_SCORER"
    if expectancy <= -0.20 and (stress_expectancy or expectancy) <= -0.20:
        return "KILL_EXPANDED_MARKET_INTRABAR_BRANCH"
    if expectancy < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_INTRABAR"
    return "REDESIGN_EXPANDED_MARKET_INTRABAR_GEOMETRY"


def geometry_row_from_profile(
    performance_row: dict[str, Any],
    profile: dict[str, Any],
    row_index: int,
) -> dict[str, Any]:
    proxy_r = as_float(performance_row.get("cost_adjusted_simulated_r"))
    intrabar_r = as_float(profile.get("cost_adjusted_simulated_r"))
    delta = intrabar_r - proxy_r if intrabar_r is not None and proxy_r is not None else None
    row = {
        "intrabar_geometry_row_id": f"OHLC-GTOS-EXPANDED-MARKET-INTRABAR-{row_index:08d}",
        "input_expanded_market_performance_row_id": performance_row.get("expanded_market_performance_row_id"),
        "input_expansion_matrix_row_id": performance_row.get("input_expansion_matrix_row_id"),
        "input_market_population_row_id": performance_row.get("input_market_population_row_id"),
        "symbol": performance_row.get("symbol"),
        "source_symbol": performance_row.get("source_symbol"),
        "market_timeframe": performance_row.get("market_timeframe"),
        "route_session": performance_row.get("route_session"),
        "horizon_id": performance_row.get("horizon_id"),
        "side": performance_row.get("side"),
        "source_component": performance_row.get("seed_source_component"),
        "source_path": performance_row.get("source_path"),
        "source_file_sha256": performance_row.get("source_file_sha256"),
        "entry_reference": profile.get("entry_reference"),
        "entry_reference_time": profile.get("entry_reference_time"),
        "proxy_entry_price": profile.get("proxy_entry_price"),
        "proxy_denominator_price": profile.get("proxy_denominator_price"),
        "proxy_target_price": profile.get("proxy_target_price"),
        "proxy_stop_price": profile.get("proxy_stop_price"),
        "path_order_result": profile.get("path_order_result"),
        "path_order_counts": profile.get("path_order_counts") or {},
        "fill_status": profile.get("fill_status"),
        "gross_simulated_r": profile.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": profile.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": profile.get("stress_simulated_r"),
        "horizon_close_proxy_cost_adjusted_simulated_r": performance_row.get("cost_adjusted_simulated_r"),
        "intrabar_minus_horizon_close_cost_adjusted_r": rounded(delta),
        "win_count": profile.get("win_count"),
        "loss_count": profile.get("loss_count"),
        "zero_count": profile.get("zero_count"),
        "average_win": profile.get("average_win"),
        "average_loss": profile.get("average_loss"),
        "target_first_count": profile.get("target_first_count"),
        "stop_first_count": profile.get("stop_first_count"),
        "neither_count": profile.get("neither_count"),
        "ambiguous_count": profile.get("ambiguous_count"),
        "effective_n": profile.get("effective_n"),
        "duplicate_row_count": profile.get("duplicate_row_count"),
        "effective_n_after_duplicate_collapse": profile.get("effective_n_after_duplicate_collapse"),
        "concentration_top_month_share": profile.get("concentration_top_month_share"),
        "first_touch_bars": profile.get("first_touch_bars"),
        "average_first_touch_bars": profile.get("average_first_touch_bars"),
        "profile_status": profile.get("profile_status"),
        "follow_inverse_default_off_avoid_class": profile.get("follow_inverse_default_off_avoid_class"),
        "keep_kill_redesign_implement_decision": profile.get("keep_kill_redesign_implement_decision"),
    }
    return boundary_row(row)


def noncomputable_row(performance_row: dict[str, Any], profile: dict[str, Any], row_index: int) -> dict[str, Any]:
    return boundary_row(
        {
            "intrabar_noncomputable_row_id": f"OHLC-GTOS-EXPANDED-MARKET-INTRABAR-PROOF-{row_index:07d}",
            "input_expanded_market_performance_row_id": performance_row.get("expanded_market_performance_row_id"),
            "symbol": performance_row.get("symbol"),
            "source_path": performance_row.get("source_path"),
            "source_file_sha256": performance_row.get("source_file_sha256"),
            "market_timeframe": performance_row.get("market_timeframe"),
            "route_session": performance_row.get("route_session"),
            "horizon_id": performance_row.get("horizon_id"),
            "side": performance_row.get("side"),
            "profile_status": profile.get("profile_status"),
            "missing_simulated_fields": ["intrabar_high_low_target_stop_path"],
            "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_INTRABAR_REPLAY_IMPLEMENTATION",
        }
    )


def aggregate_intrabar_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
        )
        grouped[key].append(row)
    total_rows = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members]
        values = [value for value in values if value is not None]
        deltas = [as_float(row.get("intrabar_minus_horizon_close_cost_adjusted_r")) for row in members]
        deltas = [value for value in deltas if value is not None]
        path_counts: Counter[str] = Counter()
        for row in members:
            path_counts.update(row.get("path_order_counts") or {})
        output.append(
            boundary_row(
                {
                    "intrabar_aggregate_row_id": f"OHLC-GTOS-EXPANDED-MARKET-INTRABAR-AGG-{len(output) + 1:06d}",
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(values)),
                    "average_intrabar_minus_horizon_close_cost_adjusted_r": rounded(average(deltas)),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "path_order_counts": dict(sorted(path_counts.items())),
                    "concentration_share_of_all_intrabar_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_intrabar_rows(
    geometry_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    proof_rows: list[dict[str, Any]],
    input_performance_rows: int,
    unique_profile_keys: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "intrabar_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-INTRABAR-SYSTEM-0001",
                "input_performance_rows": input_performance_rows,
                "intrabar_geometry_rows": len(geometry_rows),
                "aggregate_rows": len(aggregate_rows),
                "source_access_proof_rows": len(proof_rows),
                "unique_intrabar_profile_keys": unique_profile_keys,
                "source_path_count": len({row.get("source_path") for row in geometry_rows}),
                "symbol_count": len({row.get("symbol") for row in geometry_rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in geometry_rows).items())
                ),
            }
        )
    ]
