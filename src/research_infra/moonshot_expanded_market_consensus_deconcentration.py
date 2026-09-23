"""Deconcentrated performance over expanded-market source-consensus rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_CONSENSUS_DECONCENTRATION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_consensus_deconcentration.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
SOURCE_PATH_CAP_SHARE = 0.35


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
    output["expanded_market_consensus_deconcentration_surface"] = (
        EXPANDED_MARKET_CONSENSUS_DECONCENTRATION_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def group_key(row: dict[str, Any]) -> tuple[str, str, str, str, str]:
    return (
        normalized(row.get("symbol_family")),
        normalized(row.get("market_timeframe")),
        normalized(row.get("route_session")),
        normalized(row.get("horizon_id")),
        normalized(row.get("side")),
    )


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def group_profile(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total_effective = sum(int(row.get("effective_n") or 0) for row in rows)
    source_effective = Counter()
    source_family_effective = Counter()
    for row in rows:
        effective_n = int(row.get("effective_n") or 0)
        source_effective[normalized(row.get("source_path"))] += effective_n
        source_family_effective[normalized(row.get("performance_source_family"))] += effective_n

    source_cap = total_effective * SOURCE_PATH_CAP_SHARE if total_effective else 0.0
    source_weight_factor: dict[str, float] = {}
    weighted_source_effective: Counter[str] = Counter()
    for source_path, effective in source_effective.items():
        if effective <= 0 or source_cap <= 0:
            factor = 0.0
        else:
            factor = min(1.0, source_cap / effective)
        source_weight_factor[source_path] = factor
        weighted_source_effective[source_path] = effective * factor

    weighted_values: list[tuple[float, float, float, float]] = []
    missing_rows = 0
    for row in rows:
        weight = int(row.get("effective_n") or 0) * source_weight_factor.get(normalized(row.get("source_path")), 0.0)
        gross = as_float(row.get("gross_simulated_r"))
        cost = as_float(row.get("cost_adjusted_simulated_r"))
        stress = as_float(row.get("stress_simulated_r"))
        if weight <= 0 or gross is None or cost is None or stress is None:
            missing_rows += 1 if gross is None or cost is None or stress is None else 0
            continue
        weighted_values.append((weight, gross, cost, stress))

    weighted_effective = sum(weight for weight, _, _, _ in weighted_values)
    top_weighted = max(weighted_source_effective.values()) if weighted_source_effective else 0.0
    top_raw = max(source_effective.values()) if source_effective else 0

    def weighted_average(index: int) -> float | None:
        if weighted_effective <= 0:
            return None
        return sum(weight * values[index] for weight, *values in weighted_values) / weighted_effective

    gross_mean = weighted_average(0)
    cost_mean = weighted_average(1)
    stress_mean = weighted_average(2)
    weighted_source_share = (top_weighted / weighted_effective) if weighted_effective else 1.0
    raw_source_share = (top_raw / total_effective) if total_effective else 1.0
    decision = deconcentration_decision(
        cost_mean,
        stress_mean,
        weighted_effective,
        len(source_effective),
        weighted_source_share,
        missing_rows,
    )
    return {
        "row_count": len(rows),
        "source_path_count": len(source_effective),
        "source_family_count": len(source_family_effective),
        "raw_effective_n_sum": total_effective,
        "deconcentrated_effective_n_sum": rounded(weighted_effective),
        "raw_top_source_path_effective_n_share": rounded(raw_source_share),
        "deconcentrated_top_source_path_effective_n_share": rounded(weighted_source_share),
        "source_path_cap_share": SOURCE_PATH_CAP_SHARE,
        "source_path_effective_n": dict(sorted(source_effective.items())),
        "weighted_source_path_effective_n": {
            key: rounded(value) for key, value in sorted(weighted_source_effective.items())
        },
        "source_path_weight_factor": {key: rounded(value) for key, value in sorted(source_weight_factor.items())},
        "deconcentrated_gross_simulated_r": rounded(gross_mean),
        "deconcentrated_cost_adjusted_simulated_r": rounded(cost_mean),
        "deconcentrated_stress_simulated_r": rounded(stress_mean),
        "missing_simulated_row_count": missing_rows,
        "keep_kill_redesign_implement_decision": decision,
        "follow_inverse_default_off_avoid_class": class_from_decision(decision),
    }


def deconcentration_decision(
    cost_mean: float | None,
    stress_mean: float | None,
    weighted_effective: float,
    source_path_count: int,
    weighted_source_share: float,
    missing_rows: int,
) -> str:
    if missing_rows:
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_MISSING_SIMULATED_R"
    if source_path_count < 2:
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_SINGLE_SOURCE"
    if weighted_effective < 20:
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_UNDERPOWERED"
    if weighted_source_share > 0.70:
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_RESIDUAL_CONCENTRATION"
    if cost_mean is None or stress_mean is None:
        return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_MISSING_SIMULATED_R"
    if cost_mean >= 0.10 and stress_mean > -0.05:
        return "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_PERFORMANCE"
    if cost_mean <= -0.20 and stress_mean <= -0.20:
        return "KILL_EXPANDED_MARKET_DECONCENTRATED_BRANCH"
    if cost_mean < -0.05:
        return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_DECONCENTRATION"
    return "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_WEAK_EDGE"


def deconcentration_rows(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(group_key(row), []).append(row)
    profiles = {key: group_profile(members) for key, members in grouped.items()}

    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for row in rows:
        key = group_key(row)
        profile = profiles[key]
        source_path = normalized(row.get("source_path"))
        source_effective_n = (profile.get("source_path_effective_n") or {}).get(source_path, 0)
        weighted_source_effective_n = (profile.get("weighted_source_path_effective_n") or {}).get(source_path, 0.0)
        source_factor = (profile.get("source_path_weight_factor") or {}).get(source_path, 0.0)
        row_effective_n = int(row.get("effective_n") or 0)
        decon_row_effective_n = row_effective_n * float(source_factor or 0.0)
        missing = list(row.get("missing_simulated_fields") or [])
        if row.get("gross_simulated_r") is None:
            missing.append("gross_simulated_r")
        if row.get("cost_adjusted_simulated_r") is None:
            missing.append("cost_adjusted_simulated_r")
        if row.get("stress_simulated_r") is None:
            missing.append("stress_simulated_r")
        decon_row = boundary_row(
            {
                "expanded_market_deconcentration_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-DECON-{len(output) + 1:07d}"
                ),
                "input_source_consensus_row_id": row.get("expanded_market_source_consensus_row_id"),
                "input_supplemental_performance_row_id": row.get("input_supplemental_performance_row_id"),
                "performance_source_family": row.get("performance_source_family"),
                "symbol_family": row.get("symbol_family"),
                "symbol": row.get("symbol"),
                "source_symbol": row.get("source_symbol"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "side": row.get("side"),
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
                "gross_simulated_r": row.get("gross_simulated_r"),
                "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                "stress_simulated_r": row.get("stress_simulated_r"),
                "win_count": int(row.get("win_count") or 0),
                "loss_count": int(row.get("loss_count") or 0),
                "zero_count": int(row.get("zero_count") or 0),
                "target_first_count": int(row.get("target_first_count") or 0),
                "stop_first_count": int(row.get("stop_first_count") or 0),
                "neither_count": int(row.get("neither_count") or 0),
                "ambiguous_count": int(row.get("ambiguous_count") or 0),
                "effective_n": row_effective_n,
                "deconcentrated_effective_n": rounded(decon_row_effective_n),
                "duplicate_row_count": int(row.get("duplicate_row_count") or 0),
                "effective_n_after_duplicate_collapse": int(row.get("effective_n_after_duplicate_collapse") or 0),
                "missing_simulated_fields": sorted(set(missing)),
                "source_path_effective_n": source_effective_n,
                "source_path_deconcentrated_effective_n": weighted_source_effective_n,
                "source_path_deconcentration_weight": source_factor,
                "raw_top_source_path_effective_n_share": profile.get("raw_top_source_path_effective_n_share"),
                "deconcentrated_top_source_path_effective_n_share": profile.get(
                    "deconcentrated_top_source_path_effective_n_share"
                ),
                "source_path_count": profile.get("source_path_count"),
                "source_family_count": profile.get("source_family_count"),
                "raw_effective_n_sum": profile.get("raw_effective_n_sum"),
                "deconcentrated_effective_n_sum": profile.get("deconcentrated_effective_n_sum"),
                "deconcentrated_gross_simulated_r": profile.get("deconcentrated_gross_simulated_r"),
                "deconcentrated_cost_adjusted_simulated_r": profile.get(
                    "deconcentrated_cost_adjusted_simulated_r"
                ),
                "deconcentrated_stress_simulated_r": profile.get("deconcentrated_stress_simulated_r"),
                "source_consensus_decision": row.get("keep_kill_redesign_implement_decision"),
                "keep_kill_redesign_implement_decision": profile.get("keep_kill_redesign_implement_decision"),
                "follow_inverse_default_off_avoid_class": profile.get("follow_inverse_default_off_avoid_class"),
            }
        )
        output.append(decon_row)
        if missing:
            issues.append(
                boundary_row(
                    {
                        "expanded_market_deconcentration_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECON-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_deconcentration_row_id": decon_row["expanded_market_deconcentration_row_id"],
                        "input_source_consensus_row_id": row.get("expanded_market_source_consensus_row_id"),
                        "symbol_family": row.get("symbol_family"),
                        "symbol": row.get("symbol"),
                        "market_timeframe": row.get("market_timeframe"),
                        "route_session": row.get("route_session"),
                        "horizon_id": row.get("horizon_id"),
                        "side": row.get("side"),
                        "source_path": row.get("source_path"),
                        "source_file_sha256": row.get("source_file_sha256"),
                        "missing_simulated_fields": sorted(set(missing)),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_DECONCENTRATION_MISSING_SIMULATED_R"
                        ),
                    }
                )
            )
    return output, issues


def aggregate_deconcentration_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(group_key(row), []).append(row)
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        members = grouped[key]
        cost_values = [
            value for value in (as_float(row.get("cost_adjusted_simulated_r")) for row in members) if value is not None
        ]
        stress_values = [
            value for value in (as_float(row.get("stress_simulated_r")) for row in members) if value is not None
        ]
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in members)
        classes = Counter(row.get("follow_inverse_default_off_avoid_class") for row in members)
        output.append(
            boundary_row(
                {
                    "expanded_market_deconcentration_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECON-AGG-{len(output) + 1:06d}"
                    ),
                    "symbol_family": key[0],
                    "market_timeframe": key[1],
                    "route_session": key[2],
                    "horizon_id": key[3],
                    "side": key[4],
                    "row_count": len(members),
                    "source_path_count": len({row.get("source_path") for row in members}),
                    "source_family_count": len({row.get("performance_source_family") for row in members}),
                    "simulated_r_row_count": len(cost_values),
                    "missing_simulated_row_count": sum(1 for row in members if row.get("missing_simulated_fields")),
                    "effective_n": sum(int(row.get("effective_n") or 0) for row in members),
                    "deconcentrated_effective_n": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in members)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in members),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in members),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in members),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in members),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in members),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in members),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in members),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
                    "expectancy_stress_simulated_r": rounded(average(stress_values)),
                    "deconcentrated_cost_adjusted_simulated_r": members[0].get(
                        "deconcentrated_cost_adjusted_simulated_r"
                    ),
                    "deconcentrated_stress_simulated_r": members[0].get("deconcentrated_stress_simulated_r"),
                    "raw_top_source_path_effective_n_share": members[0].get(
                        "raw_top_source_path_effective_n_share"
                    ),
                    "deconcentrated_top_source_path_effective_n_share": members[0].get(
                        "deconcentrated_top_source_path_effective_n_share"
                    ),
                    "average_win": rounded(average([value for value in cost_values if value > 0])),
                    "average_loss": rounded(average([value for value in cost_values if value < 0])),
                    "decision_counts": dict(sorted(decisions.items())),
                    "class_counts": dict(sorted(classes.items())),
                    "keep_kill_redesign_implement_decision": decisions.most_common(1)[0][0] if decisions else None,
                }
            )
        )
    return output


def system_deconcentration_rows(
    rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_deconcentration_system_row_id": "OHLC-GTOS-EXPANDED-MARKET-DECON-SYSTEM-0001",
                "deconcentration_rows": len(rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "rows_with_simulated_r": sum(1 for row in rows if not row.get("missing_simulated_fields")),
                "symbol_family_count": len({row.get("symbol_family") for row in rows}),
                "source_path_count": len({row.get("source_path") for row in rows}),
                "source_family_count": len({row.get("performance_source_family") for row in rows}),
                "decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in rows).items())
                ),
                "class_counts": dict(sorted(Counter(row.get("follow_inverse_default_off_avoid_class") for row in rows).items())),
                "source_path_cap_share": SOURCE_PATH_CAP_SHARE,
                "metadata": metadata,
            }
        )
    ]
