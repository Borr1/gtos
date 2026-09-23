"""Execute source-expansion acquisition proof rows against reachable local OHLC sources."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_impl_candidate_execution import normalized
from src.research_infra.moonshot_expanded_market_proxy_r_performance import (
    as_float,
    boundary_row as proxy_boundary_row,
    rounded,
    source_aliases,
    symbol_key,
)


EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_source_expansion_execution.py"
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
    output["expanded_market_source_expansion_execution_surface"] = (
        EXPANDED_MARKET_SOURCE_EXPANSION_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def stable_text_sha256(value: Any) -> str | None:
    text = normalized(value)
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def source_key(source: dict[str, Any]) -> tuple[str, str]:
    return (symbol_key(source.get("source_symbol")), normalized(source.get("source_timeframe")))


def source_index_by_alias_timeframe(sources: list[dict[str, Any]]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for source in sources:
        if source.get("source_access_status") != "OHLC_CSV_REACHABLE":
            continue
        timeframe = normalized(source.get("source_timeframe"))
        for alias in source_aliases(source.get("source_symbol")):
            index[(symbol_key(alias), timeframe)].append(source)
    return index


def alternate_sources_for_row(
    row: dict[str, Any],
    source_index: dict[tuple[str, str], list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    timeframe = normalized(row.get("market_timeframe"))
    source_path = normalized(row.get("source_path"))
    candidates: dict[str, dict[str, Any]] = {}
    for symbol_field in (row.get("symbol"), row.get("source_symbol"), row.get("symbol_family")):
        for alias in source_aliases(symbol_field):
            for source in source_index.get((symbol_key(alias), timeframe), []):
                candidate_path = normalized(source.get("source_path"))
                if candidate_path and candidate_path != source_path:
                    candidates[candidate_path] = source
    return [candidates[path] for path in sorted(candidates)]


def score_decision(score: dict[str, Any]) -> str:
    if score.get("score_status") != "EXPANDED_MARKET_PROXY_R_SCORED":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_REPLAY_IMPLEMENTATION"
    cost_r = as_float(score.get("cost_adjusted_simulated_r"))
    stress_r = as_float(score.get("stress_simulated_r"))
    effective_n = int(score.get("effective_n") or 0)
    concentration = as_float(score.get("concentration_top_month_share")) or 0.0
    if effective_n < 20:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_UNDERPOWERED"
    if concentration > 0.70:
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_CONCENTRATION"
    if cost_r is not None and cost_r >= 0.10 and (stress_r if stress_r is not None else cost_r) > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUIRED_PROXY_R"
    if cost_r is not None and cost_r <= -0.20 and (stress_r if stress_r is not None else cost_r) <= -0.20:
        return "KILL_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUIRED_PROXY_R"
    if cost_r is not None and cost_r < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_SOURCE_EXPANSION"
    return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SIGNAL_GEOMETRY"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def source_expansion_execution_row(
    evidence: dict[str, Any],
    source: dict[str, Any],
    score: dict[str, Any],
    sequence: int,
) -> dict[str, Any]:
    decision = score_decision(score)
    return boundary_row(
        {
            "expanded_market_source_expansion_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-EXEC-{sequence:07d}"
            ),
            "input_acceptance_execution_evidence_row_id": evidence.get(
                "expanded_market_repair_implementation_acceptance_evidence_execution_row_id"
            ),
            "input_source_repair_reachability_row_id": evidence.get(
                "input_source_repair_reachability_row_id"
            ),
            "input_action_class_performance_row_id": evidence.get(
                "input_action_class_performance_row_id"
            ),
            "source_expansion_execution_status": "SOURCE_EXPANSION_ALTERNATE_SOURCE_SCORED"
            if score.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED"
            else "SOURCE_EXPANSION_ALTERNATE_SOURCE_NONCOMPUTABLE",
            "source_expansion_input_source_path": evidence.get("source_path"),
            "source_expansion_input_source_path_sha256": stable_text_sha256(
                evidence.get("source_path")
            ),
            "source_expansion_input_source_file_sha256": evidence.get("source_file_sha256"),
            "source_expansion_candidate_source_path": source.get("source_path"),
            "source_expansion_candidate_source_path_sha256": stable_text_sha256(
                source.get("source_path")
            ),
            "source_expansion_candidate_source_file_sha256": source.get("source_file_sha256"),
            "source_access_status": source.get("source_access_status"),
            "source_component": evidence.get("source_component"),
            "source_record_selector": evidence.get("source_record_selector"),
            "branch_family": evidence.get("performance_source_family") or evidence.get("symbol_family"),
            "symbol_family": evidence.get("symbol_family"),
            "symbol": evidence.get("symbol"),
            "source_symbol": source.get("source_symbol"),
            "market_timeframe": evidence.get("market_timeframe"),
            "route_session": evidence.get("route_session"),
            "horizon_id": evidence.get("horizon_id"),
            "side": evidence.get("side"),
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
            "input_observed_gross_simulated_r": evidence.get("observed_gross_simulated_r"),
            "input_observed_cost_adjusted_simulated_r": evidence.get(
                "observed_cost_adjusted_simulated_r"
            ),
            "input_observed_stress_simulated_r": evidence.get("observed_stress_simulated_r"),
            "win_count": int(score.get("win_count") or 0),
            "loss_count": int(score.get("loss_count") or 0),
            "zero_count": int(score.get("zero_count") or 0),
            "target_first_count": int(score.get("target_first_count") or 0),
            "stop_first_count": int(score.get("stop_first_count") or 0),
            "neither_count": int(score.get("neither_count") or 0),
            "ambiguous_count": int(score.get("ambiguous_count") or 0),
            "effective_n": int(score.get("effective_n") or 0),
            "duplicate_row_count": int(score.get("duplicate_row_count") or 0),
            "effective_n_after_duplicate_collapse": int(
                score.get("effective_n_after_duplicate_collapse") or 0
            ),
            "concentration_top_month_share": score.get("concentration_top_month_share"),
            "cost_adjustment_r": score.get("cost_adjustment_r"),
            "stress_cost_adjustment_r": score.get("stress_cost_adjustment_r"),
            "cost_proxy_status": score.get("cost_proxy_status"),
            "cost_proxy_symbol": score.get("cost_proxy_symbol"),
            "missing_simulated_fields": []
            if score.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED"
            else ["alternate_source_simulated_r"],
            "follow_inverse_default_off_avoid_class": class_from_decision(decision),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def source_expansion_gap_row(
    evidence: dict[str, Any],
    sequence: int,
    discovered_source_count: int,
    searched_aliases: list[str] | None = None,
    searched_source_roots: list[str] | None = None,
) -> dict[str, Any]:
    return boundary_row(
        {
            "expanded_market_source_expansion_gap_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-GAP-{sequence:07d}"
            ),
            "input_acceptance_execution_evidence_row_id": evidence.get(
                "expanded_market_repair_implementation_acceptance_evidence_execution_row_id"
            ),
            "input_source_repair_reachability_row_id": evidence.get(
                "input_source_repair_reachability_row_id"
            ),
            "input_action_class_performance_row_id": evidence.get(
                "input_action_class_performance_row_id"
            ),
            "source_expansion_gap_status": "NO_ALTERNATE_LOCAL_OHLC_SOURCE_FOR_SYMBOL_TIMEFRAME",
            "branch_family": evidence.get("performance_source_family") or evidence.get("symbol_family"),
            "symbol_family": evidence.get("symbol_family"),
            "symbol": evidence.get("symbol"),
            "source_symbol": evidence.get("source_symbol"),
            "market_timeframe": evidence.get("market_timeframe"),
            "route_session": evidence.get("route_session"),
            "horizon_id": evidence.get("horizon_id"),
            "side": evidence.get("side"),
            "source_path": evidence.get("source_path"),
            "source_path_sha256": stable_text_sha256(evidence.get("source_path")),
            "source_file_sha256": evidence.get("source_file_sha256"),
            "source_component": evidence.get("source_component"),
            "source_record_selector": evidence.get("source_record_selector"),
            "discovered_local_ohlc_source_count": discovered_source_count,
            "searched_symbol_aliases": searched_aliases or [],
            "searched_source_roots": searched_source_roots or [],
            "missing_simulated_fields": ["additional_replay_source_path_hash_for_scope"],
            "follow_inverse_default_off_avoid_class": "redesign",
            "keep_kill_redesign_implement_decision": (
                "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_LOCAL_SOURCE_GAP"
            ),
        }
    )


def aggregate_key(row: dict[str, Any], row_kind: str) -> tuple[str, ...]:
    return (
        row_kind,
        normalized(row.get("symbol_family")),
        normalized(row.get("symbol")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def empty_bucket() -> dict[str, Any]:
    return {
        "row_count": 0,
        "scored_rows": 0,
        "gap_rows": 0,
        "gross_r_sum": 0.0,
        "gross_r_count": 0,
        "cost_r_sum": 0.0,
        "cost_r_count": 0,
        "stress_r_sum": 0.0,
        "stress_r_count": 0,
        "win_r_sum": 0.0,
        "win_r_count": 0,
        "loss_r_sum": 0.0,
        "loss_r_count": 0,
        "win_count": 0,
        "loss_count": 0,
        "zero_count": 0,
        "target_first_count": 0,
        "stop_first_count": 0,
        "neither_count": 0,
        "ambiguous_count": 0,
        "effective_n_sum": 0,
        "duplicate_row_count": 0,
        "effective_n_after_duplicate_collapse": 0,
        "max_concentration_top_month_share": 0.0,
        "source_paths": set(),
        "decisions": Counter(),
        "path_results": Counter(),
    }


def update_bucket(bucket: dict[str, Any], row: dict[str, Any], row_kind: str) -> None:
    bucket["row_count"] += 1
    if row_kind == "execution":
        bucket["scored_rows"] += int(row.get("score_status") == "EXPANDED_MARKET_PROXY_R_SCORED")
        gross_value = as_float(row.get("gross_simulated_r"))
        if gross_value is not None:
            bucket["gross_r_sum"] += gross_value
            bucket["gross_r_count"] += 1
        value = as_float(row.get("cost_adjusted_simulated_r"))
        if value is not None:
            bucket["cost_r_sum"] += value
            bucket["cost_r_count"] += 1
            if value > 0:
                bucket["win_r_sum"] += value
                bucket["win_r_count"] += 1
            if value < 0:
                bucket["loss_r_sum"] += value
                bucket["loss_r_count"] += 1
        stress_value = as_float(row.get("stress_simulated_r"))
        if stress_value is not None:
            bucket["stress_r_sum"] += stress_value
            bucket["stress_r_count"] += 1
        bucket["win_count"] += int(row.get("win_count") or 0)
        bucket["loss_count"] += int(row.get("loss_count") or 0)
        bucket["zero_count"] += int(row.get("zero_count") or 0)
        bucket["target_first_count"] += int(row.get("target_first_count") or 0)
        bucket["stop_first_count"] += int(row.get("stop_first_count") or 0)
        bucket["neither_count"] += int(row.get("neither_count") or 0)
        bucket["ambiguous_count"] += int(row.get("ambiguous_count") or 0)
        bucket["effective_n_sum"] += int(row.get("effective_n") or 0)
        bucket["duplicate_row_count"] += int(row.get("duplicate_row_count") or 0)
        bucket["effective_n_after_duplicate_collapse"] += int(
            row.get("effective_n_after_duplicate_collapse") or 0
        )
        bucket["max_concentration_top_month_share"] = max(
            bucket["max_concentration_top_month_share"],
            as_float(row.get("concentration_top_month_share")) or 0.0,
        )
        bucket["source_paths"].add(normalized(row.get("source_expansion_candidate_source_path")))
        bucket["path_results"][normalized(row.get("path_order_result"))] += 1
    if row_kind == "gap":
        bucket["gap_rows"] += 1
        bucket["source_paths"].add(normalized(row.get("source_path")))
    bucket["decisions"][row.get("keep_kill_redesign_implement_decision")] += 1


def aggregate_rows_from_buckets(buckets: dict[tuple[str, ...], dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in sorted(buckets):
        bucket = buckets[key]
        rows.append(
            boundary_row(
                {
                    "expanded_market_source_expansion_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-EXPANSION-EXEC-AGG-{len(rows) + 1:07d}"
                    ),
                    "row_kind": key[0],
                    "symbol_family": key[1],
                    "symbol": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": bucket["row_count"],
                    "scored_rows": bucket["scored_rows"],
                    "gap_rows": bucket["gap_rows"],
                    "expectancy_gross_simulated_r": rounded(
                        bucket["gross_r_sum"] / bucket["gross_r_count"]
                        if bucket["gross_r_count"]
                        else None
                    ),
                    "average_cost_adjusted_simulated_r": rounded(
                        bucket["cost_r_sum"] / bucket["cost_r_count"]
                        if bucket["cost_r_count"]
                        else None
                    ),
                    "expectancy_cost_adjusted_simulated_r": rounded(
                        bucket["cost_r_sum"] / bucket["cost_r_count"]
                        if bucket["cost_r_count"]
                        else None
                    ),
                    "expectancy_stress_simulated_r": rounded(
                        bucket["stress_r_sum"] / bucket["stress_r_count"]
                        if bucket["stress_r_count"]
                        else None
                    ),
                    "average_win": rounded(
                        bucket["win_r_sum"] / bucket["win_r_count"]
                        if bucket["win_r_count"]
                        else None
                    ),
                    "average_loss": rounded(
                        bucket["loss_r_sum"] / bucket["loss_r_count"]
                        if bucket["loss_r_count"]
                        else None
                    ),
                    "win_count": bucket["win_count"],
                    "loss_count": bucket["loss_count"],
                    "zero_count": bucket["zero_count"],
                    "target_first_count": bucket["target_first_count"],
                    "stop_first_count": bucket["stop_first_count"],
                    "neither_count": bucket["neither_count"],
                    "ambiguous_count": bucket["ambiguous_count"],
                    "effective_n_sum": bucket["effective_n_sum"],
                    "duplicate_row_count": bucket["duplicate_row_count"],
                    "effective_n_after_duplicate_collapse": bucket[
                        "effective_n_after_duplicate_collapse"
                    ],
                    "max_concentration_top_month_share": rounded(
                        bucket["max_concentration_top_month_share"]
                    ),
                    "path_order_result_counts": dict(sorted(bucket["path_results"].items())),
                    "source_path_count": len(bucket["source_paths"]),
                    "decision_counts": dict(sorted(bucket["decisions"].items())),
                    "keep_kill_redesign_implement_decision": bucket["decisions"].most_common(1)[0][0],
                }
            )
        )
    return rows
