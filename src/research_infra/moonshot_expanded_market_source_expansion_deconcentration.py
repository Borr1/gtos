"""Deconcentrate source-expansion execution rows by removing dominant month exposure."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded
from src.research_infra.moonshot_expanded_market_source_expansion_execution import stable_text_sha256
from src.research_infra.moonshot_expanded_market_temporal_robustness import (
    event_rows_for_profile,
    month_key,
    summarize_events,
)


EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_deconcentration.py"
)


def research_boundary() -> dict[str, Any]:
    return {
        "boundary_schema": "concrete_branch_local_research_boundary_v1",
        "artifact_scope": "branch_local_research",
        "production_import_path": False,
        "mutates_order_risk_prompt_safety_or_mt5": False,
        "runtime_candidate_use_permitted": False,
        "unconditional_scalar_use_permitted": False,
    }


def boundary_row(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["expanded_market_source_expansion_deconcentration_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def score_row_to_performance_like(row: dict[str, Any]) -> dict[str, Any]:
    output = dict(row)
    output["source_path"] = row.get("source_expansion_candidate_source_path")
    output["source_file_sha256"] = row.get("source_expansion_candidate_source_file_sha256")
    return output


def dominant_month(events: list[dict[str, Any]]) -> tuple[str | None, int, float]:
    counts = Counter(str(event.get("month") or month_key(event.get("dt"))) for event in events)
    if not counts:
        return None, 0, 0.0
    month, count = counts.most_common(1)[0]
    return month, count, count / len(events)


def monthly_event_groups(events: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        groups[str(event.get("month") or month_key(event.get("dt")))].append(event)
    return groups


def deconcentration_decision(
    status: str,
    deconcentrated: dict[str, Any],
    remaining_top_share: float | None,
) -> str:
    if status != "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED":
        if status == "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED":
            return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP"
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION_REPLAY_IMPLEMENTATION"
    effective_n = int(deconcentrated.get("effective_n") or 0)
    cost_r = as_float(deconcentrated.get("cost_adjusted_simulated_r"))
    stress_r = as_float(deconcentrated.get("stress_simulated_r"))
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION_UNDERPOWERED"
    if remaining_top_share is not None and remaining_top_share > 0.70:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION_RESIDUAL_CONCENTRATION"
    if cost_r is not None and cost_r >= 0.10 and (stress_r if stress_r is not None else cost_r) > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATED_PROXY_R"
    if cost_r is not None and cost_r <= -0.20 and (stress_r if stress_r is not None else cost_r) <= -0.20:
        return "KILL_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATED_PROXY_R"
    if cost_r is not None and cost_r < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATED"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_DECONCENTRATION_SIGNAL_GEOMETRY"


def scored_deconcentration_row(
    execution_row: dict[str, Any],
    ohlc_rows: list[dict[str, Any]],
    sequence: int,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profile_input = score_row_to_performance_like(execution_row)
    events, event_status = event_rows_for_profile(profile_input, ohlc_rows)
    if event_status != "EXPANDED_MARKET_TEMPORAL_EVENTS_REPLAYED":
        decision = deconcentration_decision("SOURCE_EXPANSION_DECONCENTRATION_REPLAY_NOT_COMPUTABLE", {}, None)
        return (
            boundary_row(
                {
                    "expanded_market_source_expansion_deconcentration_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-{sequence:07d}"
                    ),
                    "input_source_expansion_execution_row_id": execution_row.get(
                        "expanded_market_source_expansion_execution_row_id"
                    ),
                    "source_expansion_deconcentration_status": (
                        "SOURCE_EXPANSION_DECONCENTRATION_REPLAY_NOT_COMPUTABLE"
                    ),
                    "replay_event_status": event_status,
                    "symbol_family": execution_row.get("symbol_family"),
                    "symbol": execution_row.get("symbol"),
                    "source_symbol": execution_row.get("source_symbol"),
                    "market_timeframe": execution_row.get("market_timeframe"),
                    "route_session": execution_row.get("route_session"),
                    "horizon_id": execution_row.get("horizon_id"),
                    "side": execution_row.get("side"),
                    "source_path": execution_row.get("source_expansion_candidate_source_path"),
                    "source_file_sha256": execution_row.get(
                        "source_expansion_candidate_source_file_sha256"
                    ),
                    "missing_simulated_fields": ["deconcentrated_replay_events"],
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            ),
            [],
        )

    all_summary = summarize_events(events, "FULL_REPLAY")
    top_month, top_count, top_share = dominant_month(events)
    deconcentrated_events = [event for event in events if event.get("month") != top_month]
    deconcentrated_summary = summarize_events(deconcentrated_events, "DOMINANT_MONTH_REMOVED")
    _, _, remaining_top_share = dominant_month(deconcentrated_events)
    status = "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED"
    decision = deconcentration_decision(status, deconcentrated_summary, remaining_top_share)
    month_rows = []
    for month, members in sorted(monthly_event_groups(events).items()):
        month_summary = summarize_events(members, month)
        month_decision = deconcentration_decision(
            "SOURCE_EXPANSION_DECONCENTRATION_REPLAYED",
            month_summary,
            month_summary.get("concentration_top_month_share"),
        )
        month_rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_deconcentration_month_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-MONTH-{sequence:07d}-{len(month_rows) + 1:03d}"
                    ),
                    "input_source_expansion_execution_row_id": execution_row.get(
                        "expanded_market_source_expansion_execution_row_id"
                    ),
                    "month": month,
                    "symbol_family": execution_row.get("symbol_family"),
                    "symbol": execution_row.get("symbol"),
                    "source_symbol": execution_row.get("source_symbol"),
                    "market_timeframe": execution_row.get("market_timeframe"),
                    "route_session": execution_row.get("route_session"),
                    "horizon_id": execution_row.get("horizon_id"),
                    "side": execution_row.get("side"),
                    "source_path": execution_row.get("source_expansion_candidate_source_path"),
                    "source_path_sha256": stable_text_sha256(
                        execution_row.get("source_expansion_candidate_source_path")
                    ),
                    "source_file_sha256": execution_row.get(
                        "source_expansion_candidate_source_file_sha256"
                    ),
                    **month_summary,
                    "follow_inverse_default_off_avoid_class": class_from_decision(month_decision),
                    "keep_kill_redesign_implement_decision": month_decision,
                }
            )
        )
    return (
        boundary_row(
            {
                "expanded_market_source_expansion_deconcentration_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-{sequence:07d}"
                ),
                "input_source_expansion_execution_row_id": execution_row.get(
                    "expanded_market_source_expansion_execution_row_id"
                ),
                "source_expansion_deconcentration_status": status,
                "symbol_family": execution_row.get("symbol_family"),
                "symbol": execution_row.get("symbol"),
                "source_symbol": execution_row.get("source_symbol"),
                "market_timeframe": execution_row.get("market_timeframe"),
                "route_session": execution_row.get("route_session"),
                "horizon_id": execution_row.get("horizon_id"),
                "side": execution_row.get("side"),
                "source_path": execution_row.get("source_expansion_candidate_source_path"),
                "source_path_sha256": stable_text_sha256(
                    execution_row.get("source_expansion_candidate_source_path")
                ),
                "source_file_sha256": execution_row.get(
                    "source_expansion_candidate_source_file_sha256"
                ),
                "original_decision": execution_row.get("keep_kill_redesign_implement_decision"),
                "original_cost_adjusted_simulated_r": execution_row.get("cost_adjusted_simulated_r"),
                "original_stress_simulated_r": execution_row.get("stress_simulated_r"),
                "full_replay_effective_n": all_summary.get("effective_n"),
                "full_replay_cost_adjusted_simulated_r": all_summary.get(
                    "cost_adjusted_simulated_r"
                ),
                "full_replay_stress_simulated_r": all_summary.get("stress_simulated_r"),
                "dominant_month": top_month,
                "dominant_month_row_count": top_count,
                "dominant_month_share": rounded(top_share),
                "deconcentrated_effective_n": deconcentrated_summary.get("effective_n"),
                "deconcentrated_gross_simulated_r": deconcentrated_summary.get(
                    "gross_simulated_r"
                ),
                "deconcentrated_cost_adjusted_simulated_r": deconcentrated_summary.get(
                    "cost_adjusted_simulated_r"
                ),
                "deconcentrated_stress_simulated_r": deconcentrated_summary.get(
                    "stress_simulated_r"
                ),
                "deconcentrated_win_count": deconcentrated_summary.get("win_count"),
                "deconcentrated_loss_count": deconcentrated_summary.get("loss_count"),
                "deconcentrated_zero_count": deconcentrated_summary.get("zero_count"),
                "deconcentrated_average_win": deconcentrated_summary.get("average_win"),
                "deconcentrated_average_loss": deconcentrated_summary.get("average_loss"),
                "deconcentrated_target_first_count": deconcentrated_summary.get(
                    "target_first_count"
                ),
                "deconcentrated_stop_first_count": deconcentrated_summary.get("stop_first_count"),
                "deconcentrated_neither_count": deconcentrated_summary.get("neither_count"),
                "deconcentrated_ambiguous_count": deconcentrated_summary.get("ambiguous_count"),
                "deconcentrated_path_order_counts": deconcentrated_summary.get(
                    "path_order_counts"
                ),
                "remaining_top_month_share": rounded(remaining_top_share),
                "month_fold_count": len(month_rows),
                "missing_simulated_fields": []
                if deconcentrated_summary.get("effective_n")
                else ["deconcentrated_replay_events_after_dominant_month_removed"],
                "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                "keep_kill_redesign_implement_decision": decision,
            }
        ),
        month_rows,
    )


def preserved_noncomputable_row(source_row: dict[str, Any], sequence: int, row_kind: str) -> dict[str, Any]:
    is_gap = row_kind == "source_gap"
    decision = deconcentration_decision(
        "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED"
        if is_gap
        else "SOURCE_EXPANSION_DECONCENTRATION_REPLAY_NOT_COMPUTABLE",
        {},
        None,
    )
    return boundary_row(
        {
            "expanded_market_source_expansion_deconcentration_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-{sequence:07d}"
            ),
            "input_source_expansion_execution_row_id": source_row.get(
                "expanded_market_source_expansion_execution_row_id"
            ),
            "input_source_expansion_gap_row_id": source_row.get(
                "expanded_market_source_expansion_gap_row_id"
            ),
            "source_expansion_deconcentration_status": (
                "SOURCE_EXPANSION_DECONCENTRATION_LOCAL_SOURCE_GAP_PRESERVED"
                if is_gap
                else "SOURCE_EXPANSION_DECONCENTRATION_REPLAY_NOT_COMPUTABLE"
            ),
            "symbol_family": source_row.get("symbol_family"),
            "symbol": source_row.get("symbol"),
            "source_symbol": source_row.get("source_symbol"),
            "market_timeframe": source_row.get("market_timeframe"),
            "route_session": source_row.get("route_session"),
            "horizon_id": source_row.get("horizon_id"),
            "side": source_row.get("side"),
            "source_path": source_row.get("source_path")
            or source_row.get("source_expansion_candidate_source_path"),
            "source_path_sha256": source_row.get("source_path_sha256")
            or stable_text_sha256(source_row.get("source_expansion_candidate_source_path")),
            "source_file_sha256": source_row.get("source_file_sha256")
            or source_row.get("source_expansion_candidate_source_file_sha256"),
            "missing_simulated_fields": source_row.get("missing_simulated_fields")
            or ["deconcentrated_replay_events"],
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def aggregate_key(row: dict[str, Any]) -> tuple[str, ...]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
        normalized(row.get("follow_inverse_default_off_avoid_class")),
    )


def aggregate_deconcentration_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[aggregate_key(row)].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        values = [
            as_float(row.get("deconcentrated_cost_adjusted_simulated_r"))
            for row in members
            if as_float(row.get("deconcentrated_cost_adjusted_simulated_r")) is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_deconcentration_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-DECONC-AGG-{len(output) + 1:07d}"
                    ),
                    "symbol_family": key[0],
                    "symbol": key[1],
                    "market_timeframe": key[2],
                    "route_session": key[3],
                    "horizon_id": key[4],
                    "side": key[5],
                    "follow_inverse_default_off_avoid_class": key[6],
                    "row_count": len(members),
                    "rows_with_deconcentrated_r": len(values),
                    "average_deconcentrated_cost_adjusted_simulated_r": rounded(
                        sum(values) / len(values) if values else None
                    ),
                    "deconcentrated_effective_n_sum": sum(
                        int(row.get("deconcentrated_effective_n") or 0) for row in members
                    ),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output
