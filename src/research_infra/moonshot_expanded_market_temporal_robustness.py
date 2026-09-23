"""Temporal robustness replay for expanded-market side-pair rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    event_path_result,
    horizon_bar_count,
    in_session,
    median_range,
)


EXPANDED_MARKET_TEMPORAL_ROBUSTNESS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_temporal_robustness.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
FOLD_IDS = ("FULL_REPLAY", "EARLY_HALF", "RECENT_HALF", "RECENT_QUARTER")


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
    output["expanded_market_temporal_robustness_surface"] = EXPANDED_MARKET_TEMPORAL_ROBUSTNESS_SURFACE
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


def temporal_profile_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("source_path")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("cost_adjustment_r")),
        normalized(row.get("stress_cost_adjustment_r")),
    )


def month_key(dt_value: Any) -> str:
    if isinstance(dt_value, datetime):
        return dt_value.strftime("%Y-%m")
    return "UNPARSED_TIME"


def event_rows_for_profile(
    performance_row: dict[str, Any],
    ohlc_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    horizon_bars = horizon_bar_count(normalized(performance_row.get("horizon_id")))
    if horizon_bars is None:
        return [], "HORIZON_NOT_NUMERIC"
    if len(ohlc_rows) <= horizon_bars:
        return [], "SOURCE_UNDER_HORIZON_LENGTH"
    source_range = median_range(ohlc_rows)
    if source_range is None or source_range <= 0:
        return [], "SOURCE_DENOMINATOR_RANGE_UNAVAILABLE"

    session = normalized(performance_row.get("route_session"))
    timeframe = normalized(performance_row.get("market_timeframe"))
    side = normalized(performance_row.get("side"))
    cost_r = as_float(performance_row.get("cost_adjustment_r")) or 0.0
    stress_cost_r = as_float(performance_row.get("stress_cost_adjustment_r"))
    if stress_cost_r is None:
        stress_cost_r = cost_r
    events: list[dict[str, Any]] = []
    for index in range(0, len(ohlc_rows) - horizon_bars):
        row = ohlc_rows[index]
        if not in_session(row.get("dt"), session, timeframe):
            continue
        entry = float(row["close"])
        denominator_price = max(source_range, abs(entry) * 0.000001)
        path_result, gross_r, _, _, _ = event_path_result(
            ohlc_rows,
            index,
            horizon_bars,
            side,
            denominator_price,
        )
        stress_r = gross_r - stress_cost_r
        events.append(
            {
                "time": row.get("time"),
                "dt": row.get("dt"),
                "month": month_key(row.get("dt")),
                "path_order_result": path_result,
                "gross_simulated_r": gross_r,
                "cost_adjusted_simulated_r": gross_r - cost_r,
                "stress_simulated_r": stress_r,
            }
        )
    return events, "EXPANDED_MARKET_TEMPORAL_EVENTS_REPLAYED" if events else "NO_ELIGIBLE_TEMPORAL_EVENTS"


def summarize_events(events: list[dict[str, Any]], fold_id: str) -> dict[str, Any]:
    cost_values = [float(event["cost_adjusted_simulated_r"]) for event in events]
    gross_values = [float(event["gross_simulated_r"]) for event in events]
    stress_values = [float(event["stress_simulated_r"]) for event in events]
    wins = [value for value in cost_values if value > 0]
    losses = [value for value in cost_values if value < 0]
    path_counts = Counter(event["path_order_result"] for event in events)
    months = Counter(event["month"] for event in events)
    effective_n = len(events)
    top_month = max(months.values()) if months else 0
    return {
        "fold_id": fold_id,
        "effective_n": effective_n,
        "gross_simulated_r": rounded(average(gross_values)),
        "cost_adjusted_simulated_r": rounded(average(cost_values)),
        "stress_simulated_r": rounded(average(stress_values)),
        "win_count": len(wins),
        "loss_count": len(losses),
        "zero_count": sum(1 for value in cost_values if value == 0),
        "average_win": rounded(average(wins)),
        "average_loss": rounded(average(losses)),
        "target_first_count": path_counts.get("HORIZON_CLOSE_TARGET_PROXY_RESULT", 0),
        "stop_first_count": path_counts.get("HORIZON_CLOSE_STOP_PROXY_RESULT", 0),
        "neither_count": path_counts.get("NEITHER_PROXY_TARGET_NOR_STOP_TOUCHED_CLOSE_EXIT", 0),
        "ambiguous_count": path_counts.get("AMBIGUOUS_TARGET_AND_STOP_SAME_BAR", 0),
        "path_order_counts": dict(sorted(path_counts.items())),
        "month_count": len(months),
        "concentration_top_month_share": rounded(top_month / effective_n if effective_n else 0.0),
        "first_event_time": events[0].get("time") if events else None,
        "last_event_time": events[-1].get("time") if events else None,
    }


def month_summaries(events: list[dict[str, Any]]) -> dict[str, Any]:
    by_month: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_month[str(event["month"])].append(event)
    values: list[tuple[str, float, int]] = []
    for month, members in by_month.items():
        month_value = average([float(event["cost_adjusted_simulated_r"]) for event in members])
        if month_value is not None:
            values.append((month, month_value, len(members)))
    if not values:
        return {
            "positive_month_count": 0,
            "negative_month_count": 0,
            "flat_month_count": 0,
            "worst_month": None,
            "worst_month_cost_adjusted_simulated_r": None,
            "best_month": None,
            "best_month_cost_adjusted_simulated_r": None,
        }
    worst = min(values, key=lambda item: item[1])
    best = max(values, key=lambda item: item[1])
    return {
        "positive_month_count": sum(1 for _, value, _ in values if value > 0),
        "negative_month_count": sum(1 for _, value, _ in values if value < 0),
        "flat_month_count": sum(1 for _, value, _ in values if value == 0),
        "worst_month": worst[0],
        "worst_month_cost_adjusted_simulated_r": rounded(worst[1]),
        "best_month": best[0],
        "best_month_cost_adjusted_simulated_r": rounded(best[1]),
    }


def fold_event_slices(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    if not events:
        return {fold_id: [] for fold_id in FOLD_IDS}
    effective_n = len(events)
    half = max(1, effective_n // 2)
    recent_half = events[half:] or events[-1:]
    quarter_start = min(effective_n - 1, max(0, int(effective_n * 0.75)))
    return {
        "FULL_REPLAY": events,
        "EARLY_HALF": events[:half],
        "RECENT_HALF": recent_half,
        "RECENT_QUARTER": events[quarter_start:] or events[-1:],
    }


def temporal_profile(performance_row: dict[str, Any], ohlc_rows: list[dict[str, Any]]) -> dict[str, Any]:
    events, status = event_rows_for_profile(performance_row, ohlc_rows)
    if not events:
        return {
            "profile_status": status,
            "input_performance_row_id": performance_row.get("expanded_market_performance_row_id"),
            "folds": {},
            "month_summary": month_summaries([]),
        }
    folds = {
        fold_id: summarize_events(members, fold_id)
        for fold_id, members in fold_event_slices(events).items()
    }
    return {
        "profile_status": status,
        "input_performance_row_id": performance_row.get("expanded_market_performance_row_id"),
        "folds": folds,
        "month_summary": month_summaries(events),
        "event_count": len(events),
    }


def fold_decision(
    pair_decision: str,
    fold_winner_side: str | None,
    overall_winner_side: str | None,
    winner_expectancy: float | None,
    spread: float | None,
    effective_n: int,
) -> str:
    if winner_expectancy is None or spread is None or fold_winner_side is None:
        return "REDESIGN_EXPANDED_MARKET_TEMPORAL_FOLD_INCOMPLETE"
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_TEMPORAL_FOLD_UNDERPOWERED"
    if winner_expectancy <= -0.20:
        return "KILL_EXPANDED_MARKET_TEMPORAL_FOLD"
    if "AVOID" in pair_decision and winner_expectancy < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_TEMPORAL_FOLD"
    if fold_winner_side == overall_winner_side and winner_expectancy > -0.05 and spread >= 0.05:
        return "IMPLEMENT_EXPANDED_MARKET_TEMPORAL_FOLD_CONFIRMATION"
    return "REDESIGN_EXPANDED_MARKET_TEMPORAL_FOLD_INSTABILITY"


def temporal_decision(
    pair_decision: str,
    consistency_share: float | None,
    positive_winner_fold_share: float | None,
    worst_test_fold_winner_r: float | None,
    recent_half_winner_r: float | None,
    recent_quarter_winner_r: float | None,
    min_test_effective_n: int,
) -> str:
    if consistency_share is None or positive_winner_fold_share is None:
        return "REDESIGN_EXPANDED_MARKET_TEMPORAL_INCOMPLETE"
    if min_test_effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_TEMPORAL_UNDERPOWERED"
    if worst_test_fold_winner_r is not None and worst_test_fold_winner_r <= -0.25:
        return "KILL_EXPANDED_MARKET_TEMPORAL_DECAY"
    if "AVOID" in pair_decision and positive_winner_fold_share <= 0.33:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_TEMPORAL"
    if pair_decision.startswith("IMPLEMENT"):
        recent_ok = (recent_half_winner_r or 0.0) > -0.05 and (recent_quarter_winner_r or 0.0) > -0.05
        if consistency_share >= 0.67 and positive_winner_fold_share >= 0.67 and recent_ok:
            return "IMPLEMENT_EXPANDED_MARKET_TEMPORAL_SIDE_FILTER"
        if not recent_ok:
            return "REDESIGN_EXPANDED_MARKET_TEMPORAL_RECENT_DECAY"
    if consistency_share < 0.50:
        return "REDESIGN_EXPANDED_MARKET_TEMPORAL_INSTABILITY"
    return "REDESIGN_EXPANDED_MARKET_TEMPORAL_GEOMETRY"


def pair_fold_row(
    pair_row: dict[str, Any],
    fold_id: str,
    long_fold: dict[str, Any],
    short_fold: dict[str, Any],
    row_index: int,
) -> dict[str, Any]:
    long_r = as_float(long_fold.get("cost_adjusted_simulated_r"))
    short_r = as_float(short_fold.get("cost_adjusted_simulated_r"))
    if long_r is None or short_r is None:
        fold_winner_side = None
        winner_r = None
        loser_side = None
        loser_r = None
        spread = None
    elif long_r >= short_r:
        fold_winner_side = "LONG"
        winner_r = long_r
        loser_side = "SHORT"
        loser_r = short_r
        spread = long_r - short_r
    else:
        fold_winner_side = "SHORT"
        winner_r = short_r
        loser_side = "LONG"
        loser_r = long_r
        spread = short_r - long_r
    effective_n = min(int(long_fold.get("effective_n") or 0), int(short_fold.get("effective_n") or 0))
    decision = fold_decision(
        normalized(pair_row.get("keep_kill_redesign_implement_decision")),
        fold_winner_side,
        pair_row.get("winner_side"),
        winner_r,
        spread,
        effective_n,
    )
    return boundary_row(
        {
            "temporal_fold_row_id": f"OHLC-GTOS-EXPANDED-MARKET-TEMPORAL-FOLD-{row_index:08d}",
            "input_side_pair_robustness_row_id": pair_row.get("side_pair_robustness_row_id"),
            "input_long_performance_row_id": pair_row.get("input_long_performance_row_id"),
            "input_short_performance_row_id": pair_row.get("input_short_performance_row_id"),
            "fold_id": fold_id,
            "symbol": pair_row.get("symbol"),
            "source_symbol": pair_row.get("source_symbol"),
            "market_timeframe": pair_row.get("market_timeframe"),
            "route_session": pair_row.get("route_session"),
            "horizon_id": pair_row.get("horizon_id"),
            "source_component": pair_row.get("source_component"),
            "source_path": pair_row.get("source_path"),
            "source_file_sha256": pair_row.get("source_file_sha256"),
            "overall_winner_side": pair_row.get("winner_side"),
            "fold_winner_side": fold_winner_side,
            "fold_loser_side": loser_side,
            "long_cost_adjusted_simulated_r": rounded(long_r),
            "short_cost_adjusted_simulated_r": rounded(short_r),
            "winner_cost_adjusted_simulated_r": rounded(winner_r),
            "loser_cost_adjusted_simulated_r": rounded(loser_r),
            "side_edge_spread_cost_adjusted_r": rounded(spread),
            "effective_n": effective_n,
            "long_effective_n": long_fold.get("effective_n"),
            "short_effective_n": short_fold.get("effective_n"),
            "long_win_count": long_fold.get("win_count"),
            "long_loss_count": long_fold.get("loss_count"),
            "short_win_count": short_fold.get("win_count"),
            "short_loss_count": short_fold.get("loss_count"),
            "long_path_order_counts": long_fold.get("path_order_counts") or {},
            "short_path_order_counts": short_fold.get("path_order_counts") or {},
            "fold_matches_overall_winner": fold_winner_side == pair_row.get("winner_side"),
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def temporal_pair_rows(
    side_pair_rows: list[dict[str, Any]],
    profile_by_performance_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    summary_rows: list[dict[str, Any]] = []
    fold_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []
    for pair in side_pair_rows:
        long_profile = profile_by_performance_id.get(normalized(pair.get("input_long_performance_row_id")))
        short_profile = profile_by_performance_id.get(normalized(pair.get("input_short_performance_row_id")))
        if not long_profile or not short_profile or long_profile.get("profile_status") != "EXPANDED_MARKET_TEMPORAL_EVENTS_REPLAYED" or short_profile.get("profile_status") != "EXPANDED_MARKET_TEMPORAL_EVENTS_REPLAYED":
            issue_rows.append(
                boundary_row(
                    {
                        "temporal_issue_row_id": f"OHLC-GTOS-EXPANDED-MARKET-TEMPORAL-ISSUE-{len(issue_rows) + 1:07d}",
                        "input_side_pair_robustness_row_id": pair.get("side_pair_robustness_row_id"),
                        "input_long_performance_row_id": pair.get("input_long_performance_row_id"),
                        "input_short_performance_row_id": pair.get("input_short_performance_row_id"),
                        "long_profile_status": (long_profile or {}).get("profile_status"),
                        "short_profile_status": (short_profile or {}).get("profile_status"),
                        "missing_simulated_fields": ["temporal_profile_replay_events"],
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_TEMPORAL_REPLAY_IMPLEMENTATION",
                    }
                )
            )
            continue
        pair_fold_rows: list[dict[str, Any]] = []
        for fold_id in FOLD_IDS:
            pair_fold_rows.append(
                pair_fold_row(
                    pair,
                    fold_id,
                    long_profile["folds"].get(fold_id, {}),
                    short_profile["folds"].get(fold_id, {}),
                    len(fold_rows) + len(pair_fold_rows) + 1,
                )
            )
        fold_rows.extend(pair_fold_rows)
        test_folds = [row for row in pair_fold_rows if row["fold_id"] != "FULL_REPLAY"]
        winner_side = pair.get("winner_side")
        winner_fold_values = [
            as_float(row["long_cost_adjusted_simulated_r"] if winner_side == "LONG" else row["short_cost_adjusted_simulated_r"])
            for row in test_folds
        ]
        winner_fold_values = [value for value in winner_fold_values if value is not None]
        consistency_count = sum(1 for row in test_folds if row.get("fold_winner_side") == winner_side)
        positive_count = sum(1 for value in winner_fold_values if value > 0)
        min_test_effective_n = min((int(row.get("effective_n") or 0) for row in test_folds), default=0)
        recent_half = next((row for row in test_folds if row["fold_id"] == "RECENT_HALF"), None)
        recent_quarter = next((row for row in test_folds if row["fold_id"] == "RECENT_QUARTER"), None)
        recent_half_winner_r = as_float(
            recent_half.get("long_cost_adjusted_simulated_r")
            if winner_side == "LONG" and recent_half
            else recent_half.get("short_cost_adjusted_simulated_r") if recent_half else None
        )
        recent_quarter_winner_r = as_float(
            recent_quarter.get("long_cost_adjusted_simulated_r")
            if winner_side == "LONG" and recent_quarter
            else recent_quarter.get("short_cost_adjusted_simulated_r") if recent_quarter else None
        )
        decision = temporal_decision(
            normalized(pair.get("keep_kill_redesign_implement_decision")),
            consistency_count / len(test_folds) if test_folds else None,
            positive_count / len(test_folds) if test_folds else None,
            min(winner_fold_values) if winner_fold_values else None,
            recent_half_winner_r,
            recent_quarter_winner_r,
            min_test_effective_n,
        )
        long_month = long_profile.get("month_summary") or {}
        short_month = short_profile.get("month_summary") or {}
        summary_rows.append(
            boundary_row(
                {
                    "temporal_robustness_row_id": f"OHLC-GTOS-EXPANDED-MARKET-TEMPORAL-{len(summary_rows) + 1:07d}",
                    "input_side_pair_robustness_row_id": pair.get("side_pair_robustness_row_id"),
                    "input_long_performance_row_id": pair.get("input_long_performance_row_id"),
                    "input_short_performance_row_id": pair.get("input_short_performance_row_id"),
                    "symbol": pair.get("symbol"),
                    "source_symbol": pair.get("source_symbol"),
                    "market_timeframe": pair.get("market_timeframe"),
                    "route_session": pair.get("route_session"),
                    "horizon_id": pair.get("horizon_id"),
                    "source_component": pair.get("source_component"),
                    "source_path": pair.get("source_path"),
                    "source_file_sha256": pair.get("source_file_sha256"),
                    "overall_winner_side": winner_side,
                    "overall_winner_cost_adjusted_simulated_r": pair.get("winner_cost_adjusted_simulated_r"),
                    "overall_side_edge_spread_cost_adjusted_r": pair.get("side_edge_spread_cost_adjusted_r"),
                    "temporal_fold_count": len(test_folds),
                    "consistent_winner_fold_count": consistency_count,
                    "winner_consistency_share": rounded(consistency_count / len(test_folds) if test_folds else None),
                    "positive_winner_fold_count": positive_count,
                    "positive_winner_fold_share": rounded(positive_count / len(test_folds) if test_folds else None),
                    "min_test_effective_n": min_test_effective_n,
                    "worst_test_fold_winner_cost_adjusted_simulated_r": rounded(
                        min(winner_fold_values) if winner_fold_values else None
                    ),
                    "best_test_fold_winner_cost_adjusted_simulated_r": rounded(
                        max(winner_fold_values) if winner_fold_values else None
                    ),
                    "recent_half_winner_cost_adjusted_simulated_r": rounded(recent_half_winner_r),
                    "recent_quarter_winner_cost_adjusted_simulated_r": rounded(recent_quarter_winner_r),
                    "long_positive_month_count": long_month.get("positive_month_count"),
                    "long_negative_month_count": long_month.get("negative_month_count"),
                    "long_worst_month": long_month.get("worst_month"),
                    "long_worst_month_cost_adjusted_simulated_r": long_month.get("worst_month_cost_adjusted_simulated_r"),
                    "short_positive_month_count": short_month.get("positive_month_count"),
                    "short_negative_month_count": short_month.get("negative_month_count"),
                    "short_worst_month": short_month.get("worst_month"),
                    "short_worst_month_cost_adjusted_simulated_r": short_month.get("worst_month_cost_adjusted_simulated_r"),
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
    return summary_rows, fold_rows, issue_rows


def aggregate_temporal_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("symbol")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("overall_winner_side")),
            normalized(row.get("follow_inverse_default_off_avoid_class")),
        )
        grouped[key].append(row)
    total_rows = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        output.append(
            boundary_row(
                {
                    "temporal_aggregate_row_id": f"OHLC-GTOS-EXPANDED-MARKET-TEMPORAL-AGG-{len(output) + 1:06d}",
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "overall_winner_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "average_winner_consistency_share": rounded(
                        average([as_float(row.get("winner_consistency_share")) for row in members if as_float(row.get("winner_consistency_share")) is not None])
                    ),
                    "average_positive_winner_fold_share": rounded(
                        average([as_float(row.get("positive_winner_fold_share")) for row in members if as_float(row.get("positive_winner_fold_share")) is not None])
                    ),
                    "average_recent_half_winner_cost_adjusted_simulated_r": rounded(
                        average([as_float(row.get("recent_half_winner_cost_adjusted_simulated_r")) for row in members if as_float(row.get("recent_half_winner_cost_adjusted_simulated_r")) is not None])
                    ),
                    "worst_test_fold_winner_cost_adjusted_simulated_r": rounded(
                        min(
                            as_float(row.get("worst_test_fold_winner_cost_adjusted_simulated_r")) or 0.0
                            for row in members
                        )
                    ),
                    "concentration_share_of_all_temporal_rows": rounded(len(members) / total_rows),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_temporal_rows(
    temporal_rows: list[dict[str, Any]],
    fold_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_side_pair_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "temporal_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-TEMPORAL-SYSTEM-0001",
                "input_side_pair_rows": input_side_pair_rows,
                "temporal_robustness_rows": len(temporal_rows),
                "temporal_fold_rows": len(fold_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "source_path_count": len({row.get("source_path") for row in temporal_rows}),
                "symbol_count": len({row.get("symbol") for row in temporal_rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in temporal_rows).items())
                ),
            }
        )
    ]
