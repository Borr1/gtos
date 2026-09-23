"""Source-repair reachability over expanded-market action-class performance rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any, Iterable

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_SOURCE_REPAIR_REACHABILITY = (
    "src/research_infra/moonshot_expanded_market_source_repair_reachability.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SCOPE_KEYS = ("symbol_family", "market_timeframe", "route_session", "horizon_id", "side")


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
    output["expanded_market_source_repair_reachability_surface"] = EXPANDED_MARKET_SOURCE_REPAIR_REACHABILITY
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def scope_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(row.get(key)) for key in SCOPE_KEYS)


def is_scored_action(row: dict[str, Any]) -> bool:
    return as_float(row.get("primary_action_cost_adjusted_simulated_r")) is not None


def observed_decon_cost(row: dict[str, Any]) -> float | None:
    return as_float(row.get("observed_deconcentrated_cost_adjusted_simulated_r"))


def primary_action_cost(row: dict[str, Any]) -> float | None:
    return as_float(row.get("primary_action_cost_adjusted_simulated_r"))


def empty_scope_bucket() -> dict[str, Any]:
    return {
        "row_count": 0,
        "source_paths": set(),
        "source_hashes": set(),
        "action_class_counts": Counter(),
        "source_path_counts": Counter(),
        "scored_sum_by_source_path": defaultdict(float),
        "scored_count_by_source_path": Counter(),
        "observed_sum_by_source_path": defaultdict(float),
        "observed_count_by_source_path": Counter(),
        "scored_sum": 0.0,
        "scored_count": 0,
        "observed_sum": 0.0,
        "observed_count": 0,
    }


def scope_statistics(rows: Iterable[dict[str, Any]]) -> dict[tuple[str, ...], dict[str, Any]]:
    stats: dict[tuple[str, ...], dict[str, Any]] = defaultdict(empty_scope_bucket)
    for row in rows:
        key = scope_key(row)
        bucket = stats[key]
        source_path = normalized(row.get("source_path"))
        source_hash = normalized(row.get("source_file_sha256"))
        bucket["row_count"] += 1
        bucket["source_paths"].add(source_path)
        bucket["source_hashes"].add(source_hash)
        bucket["action_class_counts"][normalized(row.get("action_class"))] += 1
        bucket["source_path_counts"][source_path] += 1
        scored_value = primary_action_cost(row)
        if scored_value is not None:
            bucket["scored_sum_by_source_path"][source_path] += scored_value
            bucket["scored_count_by_source_path"][source_path] += 1
            bucket["scored_sum"] += scored_value
            bucket["scored_count"] += 1
        observed_value = observed_decon_cost(row)
        if observed_value is not None:
            bucket["observed_sum_by_source_path"][source_path] += observed_value
            bucket["observed_count_by_source_path"][source_path] += 1
            bucket["observed_sum"] += observed_value
            bucket["observed_count"] += 1
    return stats


def alternate_counts(bucket: dict[str, Any], source_path: str) -> dict[str, Any]:
    alternate_paths = sorted(path for path in bucket["source_paths"] if path != source_path)
    scored_sum = float(bucket["scored_sum"]) - float(bucket["scored_sum_by_source_path"].get(source_path, 0.0))
    scored_count = int(bucket["scored_count"]) - int(bucket["scored_count_by_source_path"].get(source_path, 0))
    observed_sum = float(bucket["observed_sum"]) - float(bucket["observed_sum_by_source_path"].get(source_path, 0.0))
    observed_count = int(bucket["observed_count"]) - int(bucket["observed_count_by_source_path"].get(source_path, 0))
    return {
        "alternate_source_path_count": len(alternate_paths),
        "alternate_source_paths_sample": alternate_paths[:8],
        "alternate_scored_action_rows": scored_count,
        "alternate_observed_rows": observed_count,
        "alternate_primary_action_cost_adjusted_simulated_r": rounded(scored_sum / scored_count if scored_count else None),
        "alternate_observed_deconcentrated_cost_adjusted_simulated_r": rounded(
            observed_sum / observed_count if observed_count else None
        ),
    }


def reachability_class(row: dict[str, Any], alternates: dict[str, Any]) -> str:
    action_class = normalized(row.get("action_class"))
    if action_class in {"follow", "avoid", "default-off"}:
        return "scored-action-carried-forward"
    if action_class == "redesign-source-repair":
        if int(alternates["alternate_scored_action_rows"]) > 0:
            return "source-repair-alternate-scored-action-available"
        if int(alternates["alternate_source_path_count"]) > 0:
            return "source-repair-alternate-source-unscored"
        return "source-repair-no-alternate-source"
    if action_class == "redesign-source-expansion":
        if int(alternates["alternate_source_path_count"]) > 0:
            return "source-expansion-has-current-alternate"
        return "source-expansion-new-source-required"
    return "weak-edge-preserved-for-signal-redesign"


def reachability_missing_fields(reachability: str) -> list[str]:
    if reachability in {"scored-action-carried-forward", "source-repair-alternate-scored-action-available"}:
        return []
    if reachability == "source-repair-alternate-source-unscored":
        return ["scored_alternate_replay_action_r"]
    if reachability == "source-repair-no-alternate-source":
        return ["alternate_replay_source_path_hash_for_scope"]
    if reachability == "source-expansion-new-source-required":
        return ["additional_replay_source_path_hash_for_scope"]
    if reachability == "source-expansion-has-current-alternate":
        return ["scored_action_replay_on_current_alternate_source"]
    return ["positive_action_edge_after_source_repair_or_new_signal_geometry"]


def reachability_decision(reachability: str) -> str:
    if reachability == "scored-action-carried-forward":
        return "IMPLEMENT_EXPANDED_MARKET_SOURCE_REPAIR_REACHABILITY_CARRY_SCORED_ACTION"
    if reachability == "source-repair-alternate-scored-action-available":
        return "REPAIR_EXPANDED_MARKET_SOURCE_REPAIR_WITH_ALTERNATE_SCORED_ACTION"
    if reachability == "source-repair-alternate-source-unscored":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_REPAIR_SCORE_ALTERNATE_SOURCE"
    if reachability == "source-repair-no-alternate-source":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_REPAIR_ACQUIRE_ALTERNATE_SOURCE"
    if reachability == "source-expansion-has-current-alternate":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_SCORE_CURRENT_ALTERNATE"
    if reachability == "source-expansion-new-source-required":
        return "REDESIGN_EXPANDED_MARKET_SOURCE_EXPANSION_ACQUIRE_NEW_SOURCE"
    return "REDESIGN_EXPANDED_MARKET_WEAK_EDGE_SIGNAL_GEOMETRY"


def repaired_action_value(row: dict[str, Any], reachability: str, alternates: dict[str, Any]) -> float | None:
    if reachability == "scored-action-carried-forward":
        return rounded(primary_action_cost(row))
    if reachability == "source-repair-alternate-scored-action-available":
        return alternates["alternate_primary_action_cost_adjusted_simulated_r"]
    return None


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
        "saved_cost_adjusted_simulated_r": row.get("saved_cost_adjusted_simulated_r"),
        "proxy_inverse_cost_adjusted_simulated_r": row.get("proxy_inverse_cost_adjusted_simulated_r"),
        "default_off_account_simulated_r": row.get("default_off_account_simulated_r"),
        "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
        "effective_n": int(row.get("effective_n") or 0),
        "win_count": int(row.get("win_count") or 0),
        "loss_count": int(row.get("loss_count") or 0),
        "zero_count": int(row.get("zero_count") or 0),
        "target_first_count": int(row.get("target_first_count") or 0),
        "stop_first_count": int(row.get("stop_first_count") or 0),
        "neither_count": int(row.get("neither_count") or 0),
        "ambiguous_count": int(row.get("ambiguous_count") or 0),
        "source_path_deconcentration_weight": row.get("source_path_deconcentration_weight"),
        "deconcentrated_top_source_path_effective_n_share": row.get(
            "deconcentrated_top_source_path_effective_n_share"
        ),
        "input_decision": row.get("keep_kill_redesign_implement_decision"),
    }


def source_repair_reachability_row(row: dict[str, Any], stats: dict[tuple[str, ...], dict[str, Any]], sequence: int) -> dict[str, Any]:
    bucket = stats[scope_key(row)]
    source_path = normalized(row.get("source_path"))
    alternates = alternate_counts(bucket, source_path)
    reachability = reachability_class(row, alternates)
    decision = reachability_decision(reachability)
    missing_fields = reachability_missing_fields(reachability)
    return boundary_row(
        {
            "expanded_market_source_repair_reachability_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-REPAIR-REACH-{sequence:07d}"
            ),
            "input_action_class_performance_row_id": row.get("expanded_market_action_class_performance_row_id"),
            "input_selection_row_id": row.get("input_selection_row_id"),
            **base_fields(row),
            "scope_row_count": int(bucket["row_count"]),
            "scope_source_path_count": len(bucket["source_paths"]),
            "scope_source_hash_count": len(bucket["source_hashes"]),
            "scope_scored_action_rows": int(bucket["scored_count"]),
            "scope_observed_rows": int(bucket["observed_count"]),
            "scope_action_class_counts": dict(sorted(bucket["action_class_counts"].items())),
            "alternate_source_path_count": alternates["alternate_source_path_count"],
            "alternate_source_paths_sample": alternates["alternate_source_paths_sample"],
            "alternate_scored_action_rows": alternates["alternate_scored_action_rows"],
            "alternate_observed_rows": alternates["alternate_observed_rows"],
            "alternate_primary_action_cost_adjusted_simulated_r": alternates[
                "alternate_primary_action_cost_adjusted_simulated_r"
            ],
            "alternate_observed_deconcentrated_cost_adjusted_simulated_r": alternates[
                "alternate_observed_deconcentrated_cost_adjusted_simulated_r"
            ],
            "source_repair_reachability_class": reachability,
            "repair_action_cost_adjusted_simulated_r": repaired_action_value(row, reachability, alternates),
            "repair_missing_fields": missing_fields,
            "follow_inverse_default_off_avoid_class": row.get("action_class"),
            "keep_kill_redesign_implement_decision": decision,
        }
    )


def source_repair_reachability_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    stats = scope_statistics(rows)
    output = [source_repair_reachability_row(row, stats, index) for index, row in enumerate(rows, 1)]
    return output, issue_rows(output)


def issue_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for row in rows:
        if not row.get("source_path") or not row.get("source_file_sha256"):
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_repair_reachability_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-REPAIR-REACH-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_source_repair_reachability_row_id": row.get(
                            "expanded_market_source_repair_reachability_row_id"
                        ),
                        "issue_status": "MISSING_SOURCE_PATH_OR_HASH",
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_SOURCE_REPAIR_REACHABILITY_ROW",
                    }
                )
            )
        if not row.get("repair_missing_fields") and row.get("repair_action_cost_adjusted_simulated_r") is None:
            issues.append(
                boundary_row(
                    {
                        "expanded_market_source_repair_reachability_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-REPAIR-REACH-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_source_repair_reachability_row_id": row.get(
                            "expanded_market_source_repair_reachability_row_id"
                        ),
                        "issue_status": "MISSING_REPAIR_ACTION_R_FOR_REACHABLE_ROW",
                        "keep_kill_redesign_implement_decision": "REDESIGN_EXPANDED_MARKET_SOURCE_REPAIR_REACHABILITY_ROW",
                    }
                )
            )
    return issues


def aggregate_reachability_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        key = (
            normalized(row.get("source_repair_reachability_class")),
            normalized(row.get("action_class")),
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
        repair_values = [
            value
            for value in (as_float(row.get("repair_action_cost_adjusted_simulated_r")) for row in members)
            if value is not None
        ]
        observed_values = [
            value
            for value in (as_float(row.get("observed_deconcentrated_cost_adjusted_simulated_r")) for row in members)
            if value is not None
        ]
        source_counts = Counter(normalized(row.get("source_path")) for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_source_repair_reachability_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-SOURCE-REPAIR-REACH-AGG-{len(output) + 1:06d}"
                    ),
                    "source_repair_reachability_class": key[0],
                    "action_class": key[1],
                    "symbol_family": key[2],
                    "market_timeframe": key[3],
                    "route_session": key[4],
                    "horizon_id": key[5],
                    "side": key[6],
                    "row_count": len(members),
                    "reachable_repair_rows": sum(1 for row in members if not row.get("repair_missing_fields")),
                    "missing_repair_rows": sum(1 for row in members if row.get("repair_missing_fields")),
                    "repair_action_expectancy_cost_adjusted_simulated_r": rounded(average(repair_values)),
                    "observed_deconcentrated_expectancy_cost_adjusted_simulated_r": rounded(average(observed_values)),
                    "alternate_source_path_count_max": max(int(row.get("alternate_source_path_count") or 0) for row in members),
                    "alternate_scored_action_rows_sum": sum(int(row.get("alternate_scored_action_rows") or 0) for row in members),
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
                    "source_path_count": len(source_counts),
                    "concentration_top_source_path_share": rounded(
                        (source_counts.most_common(1)[0][1] / len(members)) if members and source_counts else None
                    ),
                    "decision_counts": dict(sorted(decisions.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0],
                }
            )
        )
    return output


def system_reachability_rows(
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_source_repair_reachability_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-SOURCE-REPAIR-REACH-SYSTEM-0001"
                ),
                "source_repair_reachability_rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issues),
                "reachable_repair_rows": sum(1 for row in rows if not row.get("repair_missing_fields")),
                "missing_repair_rows": sum(1 for row in rows if row.get("repair_missing_fields")),
                "reachability_class_counts": dict(
                    sorted(Counter(row.get("source_repair_reachability_class") for row in rows).items())
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
