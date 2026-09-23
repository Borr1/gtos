"""Convert executed repaired-proxy replay specs into simulated-R performance tables."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


RUNTIME_REPLAY_PERFORMANCE_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_performance.py"
)
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
    output["runtime_replay_performance_surface"] = RUNTIME_REPLAY_PERFORMANCE_SURFACE
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


def numeric_index(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("replay_numeric_event_row_id")): row for row in rows}


def positive_denominator(numeric: dict[str, Any] | None) -> tuple[str | None, float | None]:
    if not numeric:
        return (None, None)
    for field in ("source_mean_abs_close_change_pct", "source_mean_range_pct"):
        value = as_float(numeric.get(field))
        if value is not None and value > 0:
            return (field, value)
    return (None, None)


def proxy_side(source_close_return_pct: float | None) -> str:
    if source_close_return_pct is None:
        return "SIDE_PROXY_MISSING_SOURCE_RETURN"
    if source_close_return_pct > 0:
        return "LONG_PROXY_FROM_SOURCE_CLOSE_SIGN"
    if source_close_return_pct < 0:
        return "SHORT_PROXY_FROM_SOURCE_CLOSE_SIGN"
    return "FLAT_PROXY_FROM_SOURCE_CLOSE_SIGN"


def value_source(denominator_field: str | None) -> str:
    if denominator_field == "source_mean_abs_close_change_pct":
        return "PROXY_R_FROM_SOURCE_CLOSE_RETURN_OVER_MEAN_ABS_CLOSE_CHANGE"
    if denominator_field == "source_mean_range_pct":
        return "PROXY_R_FROM_SOURCE_CLOSE_RETURN_OVER_MEAN_RANGE"
    return "SIMULATED_R_UNAVAILABLE_MISSING_PROXY_DENOMINATOR"


def cost_adjustment_r(source_spread_mean: float | None, denominator: float | None) -> tuple[float, str]:
    if source_spread_mean is None:
        return (0.0, "COST_SOURCE_MISSING_ZERO_ADJUSTMENT_RECORDED")
    if denominator is None or denominator <= 0:
        return (0.0, "COST_DENOMINATOR_MISSING_ZERO_ADJUSTMENT_RECORDED")
    return (abs(source_spread_mean) / denominator, "COST_ADJUSTED_FROM_SOURCE_SPREAD_MEAN")


def exact_geometry_missing_fields(row: dict[str, Any], numeric: dict[str, Any] | None) -> list[str]:
    missing = [
        "exact_trade_side",
        "exact_event_timestamp",
        "exact_entry_price",
        "exact_stop_price",
        "exact_target_price",
        "exact_target_stop_path_order",
    ]
    if not numeric:
        missing.append("replay_numeric_event_row")
    denominator_field, _ = positive_denominator(numeric)
    if denominator_field is None:
        missing.append("proxy_denominator")
    if row.get("source_spread_mean") in (None, "") and (not numeric or numeric.get("source_spread_mean") in (None, "")):
        missing.append("source_spread_mean")
    return missing


def execution_family(kind: str) -> tuple[str, str, float]:
    if kind == "scorer":
        return ("DEFAULT_OFF_FOLLOW_PROXY", "default_off", 1.0)
    return ("AVOID_PROXY", "avoid", -1.0)


def row_result_class(value: float | None) -> str:
    if value is None:
        return "NO_FILL_OR_NO_PROXY_R"
    if value > 0:
        return "WIN"
    if value < 0:
        return "LOSS"
    return "FLAT"


def row_decision(row: dict[str, Any]) -> str:
    family = row.get("default_off_avoid_class")
    cost_r = as_float(row.get("cost_adjusted_simulated_r"))
    stress_r = as_float(row.get("stress_simulated_r"))
    if cost_r is None:
        if family == "avoid":
            return "CARRY_AS_AVOID_INTELLIGENCE_REPLAY_IMPLEMENTATION_NEEDED"
        return "NEEDS_CONCRETE_REPLAY_IMPLEMENTATION"
    if family == "avoid":
        if cost_r >= 0.10 and (stress_r is None or stress_r >= -0.05):
            return "CARRY_AS_AVOID_INTELLIGENCE"
        if cost_r < -0.10:
            return "KILL_AVOID_COMPARATOR_ROW"
        return "REDESIGN_AVOID_COMPARATOR_ROW"
    if cost_r >= 0.25 and (stress_r is None or stress_r >= 0.0):
        return "IMPLEMENT_BRANCH_LOCAL_REPLAY_PROTOTYPE"
    if cost_r > 0.0:
        return "KEEP_FOR_BRANCH_LOCAL_REPLAY_REVIEW"
    if cost_r < -0.10:
        return "KILL_BRANCH_LOCAL_DEFAULT_OFF_ROW"
    return "REDESIGN_DEFAULT_OFF_ROW"


def performance_row(
    row: dict[str, Any],
    numeric: dict[str, Any] | None,
    kind: str,
    sequence: int,
) -> dict[str, Any]:
    direction_class, default_off_avoid_class, multiplier = execution_family(kind)
    denominator_field, denominator = positive_denominator(numeric)
    source_return = as_float(row.get("source_close_return_pct"))
    if source_return is None and numeric:
        source_return = as_float(numeric.get("source_close_return_pct"))
    source_return_minus_control = as_float(row.get("source_return_minus_control"))
    source_spread = as_float(row.get("source_spread_mean"))
    if source_spread is None and numeric:
        source_spread = as_float(numeric.get("source_spread_mean"))

    follow_proxy_r = source_return / denominator if source_return is not None and denominator else None
    gross_r = follow_proxy_r * multiplier if follow_proxy_r is not None else None
    control_proxy_r = (
        source_return_minus_control / denominator
        if source_return_minus_control is not None and denominator
        else None
    )
    stress_r = control_proxy_r * multiplier if control_proxy_r is not None else gross_r
    cost_penalty, cost_status = cost_adjustment_r(source_spread, denominator)
    cost_adjusted_r = gross_r - cost_penalty if gross_r is not None else None
    result_class = row_result_class(cost_adjusted_r)
    no_proxy_r = gross_r is None

    output = {
        "performance_row_id": f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-PERF-ROW-{sequence:06d}",
        "input_execution_row_id": row.get("scorer_spec_execution_row_id")
        or row.get("comparator_spec_execution_row_id"),
        "input_replay_numeric_event_row_id": row.get("input_replay_numeric_event_row_id"),
        "input_replay_score_rerun_row_id": row.get("input_replay_score_rerun_row_id"),
        "branch": "branch_local_repaired_proxy_runtime_replay",
        "family": row.get("registry_family"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "market_timeframe": row.get("market_timeframe"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "execution_kind": kind,
        "spec_execution_class": row.get("scorer_spec_execution_class")
        or row.get("comparator_spec_execution_class"),
        "side": proxy_side(source_return),
        "side_source": "proxy_from_source_close_return_sign",
        "follow_inverse_default_off_avoid_class": direction_class,
        "default_off_avoid_class": default_off_avoid_class,
        "entry_reference": (
            f"PROXY_AGGREGATE_SOURCE:{row.get('market_source_path')}:{row.get('market_timeframe')}:"
            f"{row.get('input_replay_numeric_event_row_id')}"
        ),
        "entry_reference_type": "AGGREGATE_REPLAY_SOURCE_PROXY",
        "exact_entry_price": None,
        "exact_stop_price": None,
        "exact_target_price": None,
        "stop_target_or_proxy_denominator_field": denominator_field,
        "stop_target_or_proxy_denominator_value": rounded(denominator),
        "stop_target_source_status": (
            "EXACT_STOP_TARGET_MISSING_USING_PROXY_DENOMINATOR"
            if denominator
            else "PROXY_DENOMINATOR_MISSING"
        ),
        "path_order_result": (
            "AMBIGUOUS_PROXY_AGGREGATE_NO_EXACT_TARGET_STOP"
            if not no_proxy_r
            else "NO_PATH_ORDER_NO_PROXY_DENOMINATOR"
        ),
        "fill_status": (
            "PROXY_FILL_ASSUMED_FROM_REPLAY_SOURCE"
            if not no_proxy_r
            else "NO_FILL_PROXY_DENOMINATOR_MISSING"
        ),
        "simulation_value_source": value_source(denominator_field),
        "source_close_return_pct": rounded(source_return),
        "source_return_minus_control": rounded(source_return_minus_control),
        "source_mean_abs_close_change_pct": rounded(
            as_float(numeric.get("source_mean_abs_close_change_pct")) if numeric else None
        ),
        "source_mean_range_pct": rounded(as_float(numeric.get("source_mean_range_pct")) if numeric else None),
        "source_spread_mean": rounded(source_spread),
        "gross_simulated_r": rounded(gross_r),
        "cost_adjustment_r": rounded(cost_penalty),
        "cost_adjustment_status": cost_status,
        "cost_adjusted_simulated_r": rounded(cost_adjusted_r),
        "stress_simulated_r": rounded(stress_r),
        "result_class": result_class,
        "win_count": 1 if result_class == "WIN" else 0,
        "loss_count": 1 if result_class == "LOSS" else 0,
        "flat_count": 1 if result_class == "FLAT" else 0,
        "no_fill_count": 1 if result_class == "NO_FILL_OR_NO_PROXY_R" else 0,
        "target_first_count": 0,
        "stop_first_count": 0,
        "neither_count": 1 if result_class == "FLAT" else 0,
        "ambiguous_count": 0 if no_proxy_r else 1,
        "duplicate_key": row.get("input_replay_numeric_event_row_id"),
        "effective_n_key": row.get("input_replay_numeric_event_row_id"),
        "packet_rank": row.get("packet_rank"),
        "replay_rerun_score": row.get("replay_rerun_score"),
        "missing_simulated_fields": exact_geometry_missing_fields(row, numeric),
    }
    output["missing_simulated_field_count"] = len(output["missing_simulated_fields"])
    output["row_disposition"] = row_decision(output)
    return boundary_row(output)


def performance_rows(
    scorer_execution_rows: list[dict[str, Any]],
    comparator_execution_rows: list[dict[str, Any]],
    replay_numeric_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    index = numeric_index(replay_numeric_rows)
    output: list[dict[str, Any]] = []
    for row in scorer_execution_rows:
        output.append(performance_row(row, index.get(str(row.get("input_replay_numeric_event_row_id"))), "scorer", len(output) + 1))
    for row in comparator_execution_rows:
        output.append(
            performance_row(row, index.get(str(row.get("input_replay_numeric_event_row_id"))), "comparator", len(output) + 1)
        )
    return output


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


def aggregate_decision(row: dict[str, Any]) -> str:
    expectancy = as_float(row.get("expectancy_cost_adjusted_simulated_r"))
    stress = as_float(row.get("expectancy_stress_simulated_r"))
    effective_n = int(row.get("effective_n") or 0)
    cls = row.get("default_off_avoid_class")
    if int(row.get("simulated_r_row_count") or 0) == 0:
        if cls == "avoid":
            return "CARRY_AS_AVOID_INTELLIGENCE_REPLAY_IMPLEMENTATION_NEEDED"
        return "REDESIGN_CONCRETE_REPLAY_IMPLEMENTATION_REQUIRED"
    if cls == "avoid":
        if expectancy is not None and expectancy >= 0.10 and effective_n >= 20:
            return "CARRY_AS_AVOID_INTELLIGENCE"
        if expectancy is not None and expectancy < -0.10:
            return "KILL_AVOID_COMPARATOR_AGGREGATE"
        return "REDESIGN_AVOID_COMPARATOR_AGGREGATE"
    if expectancy is not None and expectancy >= 0.25 and (stress is None or stress >= 0.0) and effective_n >= 20:
        return "IMPLEMENT_BRANCH_LOCAL_REPLAY_PROTOTYPE"
    if expectancy is not None and expectancy > 0.0:
        return "KEEP_FOR_BRANCH_LOCAL_REPLAY_REVIEW"
    if expectancy is not None and expectancy < -0.10:
        return "KILL_BRANCH_LOCAL_DEFAULT_OFF_AGGREGATE"
    return "REDESIGN_DEFAULT_OFF_AGGREGATE"


def aggregate_performance_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(aggregate_key(row), []).append(row)
    total = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        cost_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members]
        cost_values = [value for value in cost_values if value is not None]
        gross_values = [as_float(row.get("gross_simulated_r")) for row in members]
        gross_values = [value for value in gross_values if value is not None]
        stress_values = [as_float(row.get("stress_simulated_r")) for row in members]
        stress_values = [value for value in stress_values if value is not None]
        win_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "WIN"]
        loss_values = [as_float(row.get("cost_adjusted_simulated_r")) for row in members if row.get("result_class") == "LOSS"]
        effective_keys = {normalized(row.get("effective_n_key")) for row in members if row.get("effective_n_key")}
        source_counts = Counter(normalized(row.get("source_component")) for row in members)
        source_key, source_count = source_counts.most_common(1)[0]
        record = {
            "aggregate_performance_row_id": (
                f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-PERF-AGG-{len(output) + 1:05d}"
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
            "simulated_r_row_count": len(cost_values),
            "win_count": sum(int(row.get("win_count") or 0) for row in members),
            "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
            "flat_count": sum(int(row.get("flat_count") or 0) for row in members),
            "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in members),
            "expectancy_gross_simulated_r": rounded(average(gross_values)),
            "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
            "expectancy_stress_simulated_r": rounded(average(stress_values)),
            "average_win": rounded(average([value for value in win_values if value is not None])),
            "average_loss": rounded(average([value for value in loss_values if value is not None])),
            "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
            "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
            "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
            "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
            "effective_n": len(effective_keys),
            "duplicate_row_count": len(members) - len(effective_keys),
            "duplicate_inflation_ratio": rounded(len(members) / len(effective_keys)) if effective_keys else None,
            "concentration_share_of_all_rows": rounded(len(members) / total),
            "dominant_source_component": source_key,
            "dominant_source_component_share": rounded(source_count / len(members)),
        }
        record["keep_kill_redesign_implement_decision"] = aggregate_decision(record)
        output.append(boundary_row(record))
    return output


def missing_simulated_field_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        if row.get("gross_simulated_r") is not None:
            continue
        fields = row.get("missing_simulated_fields") or []
        for field in fields:
            output.append(
                boundary_row(
                    {
                        "missing_simulated_field_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-PERF-MISSING-{len(output) + 1:06d}"
                        ),
                        "performance_row_id": row.get("performance_row_id"),
                        "input_execution_row_id": row.get("input_execution_row_id"),
                        "missing_simulated_field": field,
                        "row_disposition": row.get("row_disposition"),
                        "family": row.get("family"),
                        "symbol": row.get("symbol"),
                        "route_session": row.get("route_session"),
                        "market_timeframe": row.get("market_timeframe"),
                        "horizon_id": row.get("horizon_id"),
                    }
                )
            )
    return output


def system_performance_rows(
    row_level: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    missing_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in aggregate_rows)
    dispositions = Counter(row.get("row_disposition") for row in row_level)
    return [
        boundary_row(
            {
                "system_performance_row_id": "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-PERF-SYSTEM-00001",
                "performance_row_count": len(row_level),
                "aggregate_performance_row_count": len(aggregate_rows),
                "missing_simulated_field_row_count": len(missing_rows),
                "rows_with_proxy_r": sum(row.get("gross_simulated_r") is not None for row in row_level),
                "rows_without_proxy_r": sum(row.get("gross_simulated_r") is None for row in row_level),
                "win_count": sum(int(row.get("win_count") or 0) for row in row_level),
                "loss_count": sum(int(row.get("loss_count") or 0) for row in row_level),
                "flat_count": sum(int(row.get("flat_count") or 0) for row in row_level),
                "no_fill_count": sum(int(row.get("no_fill_count") or 0) for row in row_level),
                "target_first_count": sum(int(row.get("target_first_count") or 0) for row in row_level),
                "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in row_level),
                "neither_count": sum(int(row.get("neither_count") or 0) for row in row_level),
                "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in row_level),
                "row_disposition_counts": dict(sorted(dispositions.items())),
                "aggregate_decision_counts": dict(sorted(decisions.items())),
            }
        )
    ]
