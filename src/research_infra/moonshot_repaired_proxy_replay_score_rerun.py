"""Score rerun over repaired-proxy replay numeric rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


REPLAY_SCORE_RERUN_SURFACE = "src/research_infra/moonshot_repaired_proxy_replay_score_rerun.py"
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
    output["replay_score_rerun_surface"] = REPLAY_SCORE_RERUN_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def to_float(value: Any) -> float | None:
    if value is None or value == "" or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_or_none(value: float | None, places: int = 10) -> float | None:
    return round(value, places) if value is not None else None


def clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return max(lower, min(upper, value))


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = to_float(row.get(field))
        if value is not None:
            values.append(value)
    return values


def control_context_rows(control_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in control_rows:
        groups[str(row.get("timeframe") or "")].append(row)
    output: list[dict[str, Any]] = []
    for index, (timeframe, rows) in enumerate(sorted(groups.items()), 1):
        returns = numeric_values(rows, "source_close_return_pct")
        ranges = numeric_values(rows, "source_mean_range_pct")
        abs_changes = numeric_values(rows, "source_mean_abs_close_change_pct")
        spreads = numeric_values(rows, "source_spread_mean")
        output.append(
            boundary_row(
                {
                    "control_context_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-RERUN-CTRL-{index:04d}",
                    "timeframe": timeframe,
                    "control_numeric_event_rows": len(rows),
                    "control_symbol_count": len({str(row.get("symbol") or "") for row in rows}),
                    "control_return_mean": round_or_none(mean(returns) if returns else None),
                    "control_range_pct_mean": round_or_none(mean(ranges) if ranges else None),
                    "control_abs_change_pct_mean": round_or_none(mean(abs_changes) if abs_changes else None),
                    "control_spread_mean": round_or_none(mean(spreads) if spreads else None),
                }
            )
        )
    return output


def control_context_lookup(context_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("timeframe") or ""): row for row in context_rows}


def replay_context_modifier(row: dict[str, Any], control_context: dict[str, Any] | None) -> dict[str, Any]:
    source_return = to_float(row.get("source_close_return_pct")) or 0.0
    source_range = abs(to_float(row.get("source_mean_range_pct")) or 0.0)
    source_abs_change = abs(to_float(row.get("source_mean_abs_close_change_pct")) or 0.0)
    source_spread = to_float(row.get("source_spread_mean"))
    control_return = to_float((control_context or {}).get("control_return_mean")) or 0.0
    control_range = abs(to_float((control_context or {}).get("control_range_pct_mean")) or 0.0)
    control_abs_change = abs(to_float((control_context or {}).get("control_abs_change_pct_mean")) or 0.0)
    return_denom = max(source_range + source_abs_change, 1e-9)
    control_denom = max(control_range + control_abs_change, 1e-9)
    directional_component = clamp((source_return - control_return) / return_denom)
    volatility_component = clamp((source_range - control_range) / control_denom)
    friction_component = -clamp((source_spread or 0.0) / 100.0, 0.0, 1.0)
    modifier = 0.05 * directional_component + 0.03 * volatility_component + 0.02 * friction_component
    return {
        "source_return_minus_control": round_or_none(source_return - control_return),
        "directional_component": round_or_none(directional_component),
        "volatility_component": round_or_none(volatility_component),
        "friction_component": round_or_none(friction_component),
        "replay_context_modifier": round_or_none(modifier),
    }


def rerun_score_row(
    replay_row: dict[str, Any],
    control_context: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    family = str(replay_row.get("registry_family") or "")
    base_score = to_float(replay_row.get("registry_scope_score_mean"))
    modifier_fields = replay_context_modifier(replay_row, control_context)
    modifier = to_float(modifier_fields.get("replay_context_modifier")) or 0.0
    if family == "source_or_broker_geometry_repair":
        rerun_score = None
        status = "REPLAY_SCORE_RERUN_REPAIR_CONTEXT_ONLY"
        action = "PRESERVE_REPAIR_SCOPE_WITH_REPLAY_NUMERIC_CONTEXT"
    elif base_score is None:
        rerun_score = None
        status = "REPLAY_SCORE_RERUN_NO_BASE_SCOPE_SCORE"
        action = "RECHECK_SCOPE_SCORE_SOURCE_BEFORE_RERUN"
    else:
        rerun_score = round(base_score + modifier, 10)
        if family == "default_off_repaired_proxy_scorer":
            status = "REPLAY_SCORE_RERUN_DEFAULT_OFF_SCORER_EMITTED"
            action = (
                "KEEP_DEFAULT_OFF_SCORER_FOR_BRANCH_LOCAL_REPLAY"
                if rerun_score > 0
                else "RECHECK_DEFAULT_OFF_SCORER_AFTER_REPLAY_CONTEXT"
            )
        elif family == "avoid_redesign_repaired_proxy_comparator":
            status = "REPLAY_SCORE_RERUN_AVOID_COMPARATOR_EMITTED"
            action = (
                "KEEP_AVOID_REDESIGN_COMPARATOR_FOR_BRANCH_LOCAL_REPLAY"
                if rerun_score < 0
                else "RECHECK_AVOID_COMPARATOR_AFTER_REPLAY_CONTEXT"
            )
        else:
            status = "REPLAY_SCORE_RERUN_CONTEXT_SCORE_EMITTED"
            action = "KEEP_REPLAY_CONTEXT_SCORE_FOR_BRANCH_LOCAL_REVIEW"
    return boundary_row(
        {
            "replay_score_rerun_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-RERUN-{index:06d}",
            "input_replay_numeric_event_row_id": replay_row.get("replay_numeric_event_row_id"),
            "input_registry_scope_row_id": replay_row.get("input_registry_scope_row_id"),
            "input_control_context_row_id": (control_context or {}).get("control_context_row_id"),
            "registry_family": family,
            "aggregate_scope_key": replay_row.get("aggregate_scope_key"),
            "symbol": replay_row.get("symbol"),
            "route_session": replay_row.get("route_session"),
            "horizon_id": replay_row.get("horizon_id"),
            "source_component": replay_row.get("source_component"),
            "market_timeframe": replay_row.get("market_timeframe"),
            "market_source_path": replay_row.get("market_source_path"),
            "base_registry_scope_score": base_score,
            "replay_rerun_score": rerun_score,
            "replay_score_rerun_status": status,
            "replay_score_rerun_action": action,
            "source_close_return_pct": replay_row.get("source_close_return_pct"),
            "source_mean_range_pct": replay_row.get("source_mean_range_pct"),
            "source_mean_abs_close_change_pct": replay_row.get("source_mean_abs_close_change_pct"),
            "source_spread_mean": replay_row.get("source_spread_mean"),
            **modifier_fields,
        }
    )


def family_rows(score_rows: list[dict[str, Any]], family: str) -> list[dict[str, Any]]:
    return [row for row in score_rows if row.get("registry_family") == family]


def symbol_summary_rows(score_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    symbols = sorted({str(row.get("symbol") or "") for row in score_rows if row.get("symbol")})
    output: list[dict[str, Any]] = []
    for index, symbol in enumerate(symbols, 1):
        rows = [row for row in score_rows if row.get("symbol") == symbol]
        scores = numeric_values(rows, "replay_rerun_score")
        output.append(
            boundary_row(
                {
                    "replay_score_symbol_summary_row_id": f"OHLC-GTOS-REPAIRED-PROXY-SCORE-SYMBOL-{index:04d}",
                    "symbol": symbol,
                    "score_rerun_rows": len(rows),
                    "score_count": len(scores),
                    "score_mean": round_or_none(mean(scores) if scores else None),
                    "score_min": min(scores) if scores else None,
                    "score_max": max(scores) if scores else None,
                    "action_counts": dict(
                        sorted(Counter(str(row.get("replay_score_rerun_action") or "") for row in rows).items())
                    ),
                }
            )
        )
    return output


def bucket_rows(score_rows: list[dict[str, Any]], control_context_rows_input: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    specs = [
        ("rerun_status", score_rows, "replay_score_rerun_status"),
        ("rerun_action", score_rows, "replay_score_rerun_action"),
        ("registry_family", score_rows, "registry_family"),
        ("market_timeframe", score_rows, "market_timeframe"),
        ("control_context_timeframe", control_context_rows_input, "timeframe"),
    ]
    for family, rows, field in specs:
        counter = Counter(str(row.get(field) or "") for row in rows)
        for value in sorted(counter):
            output.append(
                boundary_row(
                    {
                        "replay_score_bucket_row_id": (
                            f"OHLC-GTOS-REPAIRED-PROXY-SCORE-BUCKET-{len(output) + 1:04d}"
                        ),
                        "bucket_family": family,
                        "bucket_field": field,
                        "bucket_value": value,
                        "row_count": int(counter[value]),
                    }
                )
            )
    return output
