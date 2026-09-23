"""Implementation-priority rows from expanded-market alternate-source scoring."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_IMPLEMENTATION_PRIORITY = "src/research_infra/moonshot_expanded_market_implementation_priority.py"
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
    output["expanded_market_implementation_priority_surface"] = EXPANDED_MARKET_IMPLEMENTATION_PRIORITY
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [value for value in (as_float(row.get(field)) for row in rows) if value is not None]


def priority_class(row: dict[str, Any]) -> str:
    score_class = normalized(row.get("alternate_source_scoring_class"))
    if score_class == "alternate-source-positive-repair":
        return "implementation-priority-positive-alternate-source-repair"
    if score_class == "scored-action-carried-forward":
        return "carry-forward-existing-scored-action"
    if score_class == "alternate-source-weak-positive-repair":
        return "redesign-weak-positive-alternate-source-repair"
    if score_class == "alternate-source-nonpositive-repair":
        return "kill-nonpositive-alternate-source-repair"
    if score_class == "source-expansion-new-source-required":
        return "source-expansion-acquisition-proof"
    return "weak-edge-signal-geometry-proof"


def decision_for_class(row_class: str) -> str:
    if row_class == "implementation-priority-positive-alternate-source-repair":
        return "IMPLEMENT_EXPANDED_MARKET_POSITIVE_ALTERNATE_SOURCE_REPAIR_PRIORITY"
    if row_class == "carry-forward-existing-scored-action":
        return "IMPLEMENT_EXPANDED_MARKET_CARRY_FORWARD_EXISTING_SCORED_ACTION"
    if row_class == "redesign-weak-positive-alternate-source-repair":
        return "REDESIGN_EXPANDED_MARKET_WEAK_POSITIVE_ALTERNATE_SOURCE_REPAIR"
    if row_class == "kill-nonpositive-alternate-source-repair":
        return "KILL_EXPANDED_MARKET_NONPOSITIVE_ALTERNATE_SOURCE_REPAIR"
    if row_class == "source-expansion-acquisition-proof":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUISITION_PROOF"
    return "REDESIGN_EXPANDED_MARKET_WEAK_EDGE_SIGNAL_GEOMETRY_PROOF"


def missing_fields_for_class(row_class: str) -> list[str]:
    if row_class in {
        "implementation-priority-positive-alternate-source-repair",
        "carry-forward-existing-scored-action",
        "redesign-weak-positive-alternate-source-repair",
        "kill-nonpositive-alternate-source-repair",
    }:
        return []
    if row_class == "source-expansion-acquisition-proof":
        return ["additional_replay_source_path_hash_for_scope"]
    return ["positive_action_edge_after_source_repair_or_new_signal_geometry"]


def priority_score(row: dict[str, Any], row_class: str) -> float | None:
    score_value = as_float(row.get("alternate_source_proxy_cost_adjusted_simulated_r"))
    if score_value is None:
        return None
    if row_class == "implementation-priority-positive-alternate-source-repair":
        effective_n = min(float(row.get("deconcentrated_effective_n") or 0.0), 1000.0)
        alternate_rows = min(float(row.get("alternate_observed_rows") or 0.0), 50.0)
        return rounded(score_value * (1.0 + effective_n / 1000.0) * (1.0 + alternate_rows / 50.0))
    if row_class == "carry-forward-existing-scored-action":
        return rounded(score_value)
    return rounded(score_value)


def priority_tier(row_class: str, score: float | None) -> str:
    if row_class != "implementation-priority-positive-alternate-source-repair":
        return "not-new-implementation-priority"
    if score is None:
        return "repair-priority-missing-score"
    if score >= 0.30:
        return "repair-priority-high"
    if score >= 0.15:
        return "repair-priority-medium"
    return "repair-priority-positive"


def base_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
        "action_class": row.get("action_class"),
        "source_repair_reachability_class": row.get("source_repair_reachability_class"),
        "alternate_source_scoring_class": row.get("alternate_source_scoring_class"),
        "performance_source_family": row.get("performance_source_family"),
        "source_component": row.get("source_component"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "source_record_selector": row.get("source_record_selector"),
        "entry_reference": row.get("entry_reference"),
        "entry_reference_time": row.get("entry_reference_time"),
        "proxy_entry_price": row.get("proxy_entry_price"),
        "proxy_denominator_price": row.get("proxy_denominator_price"),
        "proxy_target_price": row.get("proxy_target_price"),
        "proxy_stop_price": row.get("proxy_stop_price"),
        "path_order_result": row.get("path_order_result"),
        "fill_status": row.get("fill_status"),
        "observed_gross_simulated_r": row.get("observed_gross_simulated_r"),
        "observed_cost_adjusted_simulated_r": row.get("observed_cost_adjusted_simulated_r"),
        "observed_stress_simulated_r": row.get("observed_stress_simulated_r"),
        "observed_deconcentrated_cost_adjusted_simulated_r": row.get(
            "observed_deconcentrated_cost_adjusted_simulated_r"
        ),
        "observed_deconcentrated_stress_simulated_r": row.get("observed_deconcentrated_stress_simulated_r"),
        "primary_action_cost_adjusted_simulated_r": row.get("primary_action_cost_adjusted_simulated_r"),
        "repair_action_cost_adjusted_simulated_r": row.get("repair_action_cost_adjusted_simulated_r"),
        "alternate_source_proxy_cost_adjusted_simulated_r": row.get(
            "alternate_source_proxy_cost_adjusted_simulated_r"
        ),
        "alternate_source_path_count": row.get("alternate_source_path_count"),
        "alternate_source_paths_sample": row.get("alternate_source_paths_sample"),
        "alternate_observed_rows": row.get("alternate_observed_rows"),
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": row.get(
            "alternate_observed_deconcentrated_cost_adjusted_simulated_r"
        ),
        "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
        "effective_n": int(row.get("effective_n") or 0),
        "win_count": int(row.get("win_count") or 0),
        "loss_count": int(row.get("loss_count") or 0),
        "zero_count": int(row.get("zero_count") or 0),
        "target_first_count": int(row.get("target_first_count") or 0),
        "stop_first_count": int(row.get("stop_first_count") or 0),
        "neither_count": int(row.get("neither_count") or 0),
        "ambiguous_count": int(row.get("ambiguous_count") or 0),
        "input_alternate_source_decision": row.get("keep_kill_redesign_implement_decision"),
    }


def implementation_priority_row(row: dict[str, Any], sequence: int) -> dict[str, Any]:
    row_class = priority_class(row)
    score = priority_score(row, row_class)
    return boundary_row(
        {
            "expanded_market_implementation_priority_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-PRIORITY-{sequence:07d}"
            ),
            "input_alternate_source_scoring_row_id": row.get("expanded_market_alternate_source_scoring_row_id"),
            "input_source_repair_reachability_row_id": row.get("input_source_repair_reachability_row_id"),
            "input_action_class_performance_row_id": row.get("input_action_class_performance_row_id"),
            "input_selection_row_id": row.get("input_selection_row_id"),
            **base_fields(row),
            "implementation_priority_class": row_class,
            "implementation_priority_score": score,
            "implementation_priority_tier": priority_tier(row_class, score),
            "implementation_missing_fields": missing_fields_for_class(row_class),
            "follow_inverse_default_off_avoid_class": row.get("action_class"),
            "keep_kill_redesign_implement_decision": decision_for_class(row_class),
        }
    )


def implementation_priority_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output = [implementation_priority_row(row, index) for index, row in enumerate(rows, 1)]
    return output, issue_rows(output)


def issue_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append(
                boundary_row(
                    {
                        "expanded_market_implementation_priority_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-PRIORITY-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_implementation_priority_row_id": row.get("expanded_market_implementation_priority_row_id"),
                        "issue_status": "MISSING_SOURCE_PATH_OR_HASH",
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_PRIORITY_ROW",
                    }
                )
            )
        if row.get("implementation_priority_class") == "implementation-priority-positive-alternate-source-repair":
            if row.get("implementation_priority_score") is None or row.get("alternate_source_proxy_cost_adjusted_simulated_r") is None:
                issues.append(
                    boundary_row(
                        {
                            "expanded_market_implementation_priority_issue_row_id": (
                                f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-PRIORITY-ISSUE-{len(issues) + 1:06d}"
                            ),
                            "input_implementation_priority_row_id": row.get(
                                "expanded_market_implementation_priority_row_id"
                            ),
                            "issue_status": "MISSING_POSITIVE_REPAIR_PRIORITY_SCORE",
                            "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_IMPLEMENTATION_PRIORITY_ROW",
                        }
                    )
                )
    return issues


def aggregate_priority_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("implementation_priority_class")),
            normalized(row.get("implementation_priority_tier")),
            normalized(row.get("symbol_family")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("route_session")),
            normalized(row.get("horizon_id")),
            normalized(row.get("side")),
        )
        grouped[key].append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        priority_scores = numeric_values(members, "implementation_priority_score")
        alternate_scores = numeric_values(members, "alternate_source_proxy_cost_adjusted_simulated_r")
        output.append(
            boundary_row(
                {
                    "expanded_market_implementation_priority_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-PRIORITY-AGG-{len(output) + 1:06d}"
                    ),
                    "implementation_priority_class": key[0],
                    "implementation_priority_tier": key[1],
                    "symbol_family": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": len(members),
                    "implementation_candidate_rows": sum(
                        1
                        for row in members
                        if row.get("implementation_priority_class")
                        == "implementation-priority-positive-alternate-source-repair"
                    ),
                    "missing_rows": sum(1 for row in members if row.get("implementation_missing_fields")),
                    "average_implementation_priority_score": rounded(average(priority_scores)),
                    "average_alternate_source_proxy_cost_adjusted_simulated_r": rounded(average(alternate_scores)),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in members),
                    "deconcentrated_effective_n_sum": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in members)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_priority_rows(
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_implementation_priority_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-IMPLEMENTATION-PRIORITY-SYSTEM-0001"
                ),
                "implementation_priority_rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "implementation_candidate_rows": sum(
                    1
                    for row in rows
                    if row.get("implementation_priority_class")
                    == "implementation-priority-positive-alternate-source-repair"
                ),
                "preserved_evidence_rows": sum(
                    1
                    for row in rows
                    if row.get("implementation_priority_class")
                    != "implementation-priority-positive-alternate-source-repair"
                ),
                "priority_class_counts": dict(
                    sorted(Counter(row.get("implementation_priority_class") for row in rows).items())
                ),
                "priority_tier_counts": dict(
                    sorted(Counter(row.get("implementation_priority_tier") for row in rows).items())
                ),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in rows).items())
                ),
                "source_path_count": len({row.get("source_path") for row in rows}),
                "symbol_family_count": len({row.get("symbol_family") for row in rows}),
                "metadata": metadata,
            }
        )
    ]
