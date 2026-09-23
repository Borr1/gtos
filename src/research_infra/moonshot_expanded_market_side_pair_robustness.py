"""Side-pair robustness comparisons for expanded-market proxy-R rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any


EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_side_pair_robustness.py"
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
    output["expanded_market_side_pair_robustness_surface"] = EXPANDED_MARKET_SIDE_PAIR_ROBUSTNESS_SURFACE
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


def pair_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("input_expansion_matrix_row_id")),
        normalized(row.get("input_market_population_row_id")),
        normalized(row.get("source_path")),
        normalized(row.get("symbol")),
        normalized(row.get("source_symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("seed_source_component")),
    )


def pair_decision(
    winner_expectancy: float | None,
    loser_expectancy: float | None,
    spread: float | None,
    effective_n: int,
    concentration: float | None,
) -> str:
    if winner_expectancy is None or loser_expectancy is None or spread is None:
        return "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_INCOMPLETE"
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_UNDERPOWERED"
    if concentration is not None and concentration > 0.70:
        return "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_CONCENTRATION"
    if winner_expectancy >= 0.10 and spread >= 0.15 and loser_expectancy <= -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_SIDE_FILTER"
    if winner_expectancy <= -0.10 and loser_expectancy <= -0.10:
        return "KILL_EXPANDED_MARKET_SIDE_PAIR_SCOPE"
    if loser_expectancy <= -0.20 and spread >= 0.10:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SIDE_PAIR"
    return "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_GEOMETRY"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def side_pair_rows(performance_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, ...], dict[str, list[dict[str, Any]]]] = defaultdict(lambda: {"LONG": [], "SHORT": []})
    for row in performance_rows:
        side = normalized(row.get("side"))
        if side in {"LONG", "SHORT"}:
            grouped[pair_key(row)][side].append(row)

    pairs: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for key in sorted(grouped):
        sides = grouped[key]
        long_rows = sorted(sides.get("LONG", []), key=lambda row: normalized(row.get("expanded_market_performance_row_id")))
        short_rows = sorted(sides.get("SHORT", []), key=lambda row: normalized(row.get("expanded_market_performance_row_id")))
        for member_index in range(max(len(long_rows), len(short_rows))):
            if member_index >= len(long_rows) or member_index >= len(short_rows):
                present_side = "LONG" if member_index < len(long_rows) else "SHORT"
                present_row = long_rows[member_index] if present_side == "LONG" else short_rows[member_index]
                missing_side = "SHORT" if present_side == "LONG" else "LONG"
                issues.append(
                    boundary_row(
                        {
                            "side_pair_issue_row_id": f"OHLC-GTOS-EXPANDED-MARKET-SIDE-PAIR-ISSUE-{len(issues) + 1:06d}",
                            "pair_key": "|".join(key),
                            "pair_member_index": member_index + 1,
                            "input_performance_row_id": present_row.get("expanded_market_performance_row_id"),
                            "present_side": present_side,
                            "missing_side": missing_side,
                            "issue_status": "SIDE_PAIR_INCOMPLETE",
                        }
                    )
                )
                continue
            long_row = long_rows[member_index]
            short_row = short_rows[member_index]
            long_expectancy = as_float(long_row.get("cost_adjusted_simulated_r"))
            short_expectancy = as_float(short_row.get("cost_adjusted_simulated_r"))
            if long_expectancy is None or short_expectancy is None:
                winner_side = None
                winner_expectancy = None
                loser_side = None
                loser_expectancy = None
                spread = None
            elif long_expectancy >= short_expectancy:
                winner_side = "LONG"
                winner_expectancy = long_expectancy
                loser_side = "SHORT"
                loser_expectancy = short_expectancy
                spread = long_expectancy - short_expectancy
            else:
                winner_side = "SHORT"
                winner_expectancy = short_expectancy
                loser_side = "LONG"
                loser_expectancy = long_expectancy
                spread = short_expectancy - long_expectancy
            effective_n = min(int(long_row.get("effective_n") or 0), int(short_row.get("effective_n") or 0))
            concentration = max(
                as_float(long_row.get("concentration_top_month_share")) or 0.0,
                as_float(short_row.get("concentration_top_month_share")) or 0.0,
            )
            decision = pair_decision(winner_expectancy, loser_expectancy, spread, effective_n, concentration)
            pairs.append(
                boundary_row(
                    {
                        "side_pair_robustness_row_id": f"OHLC-GTOS-EXPANDED-MARKET-SIDE-PAIR-{len(pairs) + 1:07d}",
                        "pair_member_index": member_index + 1,
                        "input_long_performance_row_id": long_row.get("expanded_market_performance_row_id"),
                        "input_short_performance_row_id": short_row.get("expanded_market_performance_row_id"),
                        "input_expansion_matrix_row_id": long_row.get("input_expansion_matrix_row_id"),
                        "input_market_population_row_id": long_row.get("input_market_population_row_id"),
                        "symbol": long_row.get("symbol"),
                        "source_symbol": long_row.get("source_symbol"),
                        "market_timeframe": long_row.get("market_timeframe"),
                        "route_session": long_row.get("route_session"),
                        "horizon_id": long_row.get("horizon_id"),
                        "source_component": long_row.get("seed_source_component"),
                        "source_path": long_row.get("source_path"),
                        "source_file_sha256": long_row.get("source_file_sha256"),
                        "long_cost_adjusted_simulated_r": rounded(long_expectancy),
                        "short_cost_adjusted_simulated_r": rounded(short_expectancy),
                        "long_gross_simulated_r": long_row.get("gross_simulated_r"),
                        "short_gross_simulated_r": short_row.get("gross_simulated_r"),
                        "long_stress_simulated_r": long_row.get("stress_simulated_r"),
                        "short_stress_simulated_r": short_row.get("stress_simulated_r"),
                        "winner_side": winner_side,
                        "winner_cost_adjusted_simulated_r": rounded(winner_expectancy),
                        "loser_side": loser_side,
                        "loser_cost_adjusted_simulated_r": rounded(loser_expectancy),
                        "side_edge_spread_cost_adjusted_r": rounded(spread),
                        "neutral_pair_expectancy_cost_adjusted_r": rounded(
                            average([value for value in (long_expectancy, short_expectancy) if value is not None])
                        ),
                        "effective_n": effective_n,
                        "long_effective_n": long_row.get("effective_n"),
                        "short_effective_n": short_row.get("effective_n"),
                        "duplicate_row_count": int(long_row.get("duplicate_row_count") or 0)
                        + int(short_row.get("duplicate_row_count") or 0),
                        "concentration_top_month_share": rounded(concentration),
                        "long_path_order_counts": long_row.get("path_order_counts") or {},
                        "short_path_order_counts": short_row.get("path_order_counts") or {},
                        "long_win_count": long_row.get("win_count"),
                        "long_loss_count": long_row.get("loss_count"),
                        "long_zero_count": long_row.get("zero_count"),
                        "short_win_count": short_row.get("win_count"),
                        "short_loss_count": short_row.get("loss_count"),
                        "short_zero_count": short_row.get("zero_count"),
                        "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                        "keep_kill_redesign_implement_decision": decision,
                    }
                )
            )
    return pairs, issues


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("source_component")),
        normalized(row.get("winner_side")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def aggregate_side_pair_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[aggregate_key(row)].append(row)
    total_pairs = len(rows) or 1
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        winner_values = [as_float(row.get("winner_cost_adjusted_simulated_r")) for row in members]
        loser_values = [as_float(row.get("loser_cost_adjusted_simulated_r")) for row in members]
        spread_values = [as_float(row.get("side_edge_spread_cost_adjusted_r")) for row in members]
        neutral_values = [as_float(row.get("neutral_pair_expectancy_cost_adjusted_r")) for row in members]
        winner_values = [value for value in winner_values if value is not None]
        loser_values = [value for value in loser_values if value is not None]
        spread_values = [value for value in spread_values if value is not None]
        neutral_values = [value for value in neutral_values if value is not None]
        decisions = Counter(normalized(row.get("keep_kill_redesign_implement_decision")) for row in members)
        dominant_decision = decisions.most_common(1)[0][0] if decisions else "REDESIGN_EXPANDED_MARKET_SIDE_PAIR_GEOMETRY"
        output.append(
            boundary_row(
                {
                    "side_pair_aggregate_row_id": f"OHLC-GTOS-EXPANDED-MARKET-SIDE-PAIR-AGG-{len(output) + 1:06d}",
                    "symbol": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "source_component": key[4],
                    "winner_side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "duplicate_row_count": sum(int(row.get("duplicate_row_count") or 0) for row in members),
                    "average_winner_cost_adjusted_simulated_r": rounded(average(winner_values)),
                    "average_loser_cost_adjusted_simulated_r": rounded(average(loser_values)),
                    "average_side_edge_spread_cost_adjusted_r": rounded(average(spread_values)),
                    "average_neutral_pair_expectancy_cost_adjusted_r": rounded(average(neutral_values)),
                    "max_concentration_top_month_share": rounded(
                        max(as_float(row.get("concentration_top_month_share")) or 0.0 for row in members)
                    ),
                    "concentration_share_of_all_pairs": rounded(len(members) / total_pairs),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": dominant_decision,
                }
            )
        )
    return output


def system_side_pair_rows(
    pair_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_performance_rows: int,
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "side_pair_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-SIDE-PAIR-SYSTEM-0001",
                "input_performance_rows": input_performance_rows,
                "side_pair_rows": len(pair_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "source_path_count": len({row.get("source_path") for row in pair_rows}),
                "symbol_count": len({row.get("symbol") for row in pair_rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in pair_rows).items())
                ),
            }
        )
    ]
