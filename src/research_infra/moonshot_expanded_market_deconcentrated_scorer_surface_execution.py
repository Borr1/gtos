"""Execute deconcentrated scorer surfaces against held selection rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from statistics import mean
from typing import Any

from src.research_infra.moonshot_expanded_market_deconcentrated_scorer_surfaces import matches_surface
from src.research_infra.moonshot_expanded_market_proxy_r_performance import as_float, rounded


EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION = (
    "src/research_infra/moonshot_expanded_market_deconcentrated_scorer_surface_execution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"
IMPLEMENT_SELECTION_DECISION = "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_CANDIDATE"
IMPLEMENT_EXECUTION_DECISION = "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION"
REDESIGN_EXECUTION_DECISION = "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION"
SCOPE_KEYS = (
    "symbol_family",
    "market_timeframe",
    "route_session",
    "horizon_id",
    "side",
    "source_path",
    "source_file_sha256",
)


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
    output["expanded_market_deconcentrated_scorer_surface_execution_surface"] = (
        EXPANDED_MARKET_DECONCENTRATED_SCORER_SURFACE_EXECUTION
    )
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def average(values: list[float]) -> float | None:
    return mean(values) if values else None


def numeric_values(rows: list[dict[str, Any]], field: str) -> list[float]:
    return [value for value in (as_float(row.get(field)) for row in rows) if value is not None]


def average_win(values: list[float]) -> float | None:
    wins = [value for value in values if value > 0]
    return average(wins)


def average_loss(values: list[float]) -> float | None:
    losses = [value for value in values if value < 0]
    return average(losses)


def selection_id(row: dict[str, Any]) -> str:
    return normalized(row.get("expanded_market_deconcentrated_selection_row_id") or row.get("input_selection_row_id"))


def decision_family(decision: str | None) -> str:
    text = normalized(decision)
    if text.startswith("IMPLEMENT"):
        return "implement"
    if "AVOID" in text:
        return "avoid"
    if text.startswith("KILL"):
        return "kill"
    if text.startswith("REDESIGN"):
        return "redesign"
    return "missing"


def class_from_decision(decision: str) -> str:
    if decision.startswith("IMPLEMENT"):
        return "follow"
    if "AVOID" in decision:
        return "avoid"
    if decision.startswith("KILL"):
        return "default-off"
    return "redesign"


def row_scope_key(row: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(row.get(key)) for key in SCOPE_KEYS)


def surface_scope_key(surface: dict[str, Any]) -> tuple[str, ...]:
    return tuple(normalized(surface.get(key)) for key in SCOPE_KEYS)


def performance_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol_family": row.get("symbol_family"),
        "symbol": row.get("symbol"),
        "source_symbol": row.get("source_symbol"),
        "market_timeframe": row.get("market_timeframe"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "side": row.get("side"),
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
        "gross_simulated_r": row.get("gross_simulated_r"),
        "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
        "stress_simulated_r": row.get("stress_simulated_r"),
        "deconcentrated_effective_n": row.get("deconcentrated_effective_n"),
        "deconcentrated_cost_adjusted_simulated_r": row.get("deconcentrated_cost_adjusted_simulated_r"),
        "deconcentrated_stress_simulated_r": row.get("deconcentrated_stress_simulated_r"),
        "numeric_priority_score": row.get("numeric_priority_score"),
        "win_count": int(row.get("win_count") or 0),
        "loss_count": int(row.get("loss_count") or 0),
        "zero_count": int(row.get("zero_count") or 0),
        "target_first_count": int(row.get("target_first_count") or 0),
        "stop_first_count": int(row.get("stop_first_count") or 0),
        "neither_count": int(row.get("neither_count") or 0),
        "ambiguous_count": int(row.get("ambiguous_count") or 0),
        "effective_n": int(row.get("effective_n") or 0),
        "source_path_deconcentration_weight": row.get("source_path_deconcentration_weight"),
        "deconcentrated_top_source_path_effective_n_share": row.get(
            "deconcentrated_top_source_path_effective_n_share"
        ),
        "missing_simulated_fields": row.get("missing_simulated_fields") or [],
        "selection_reason": row.get("selection_reason"),
        "branch_local_selection_expression": row.get("branch_local_selection_expression"),
    }


def surface_execution_decision(
    expected_member_ids: set[str],
    matched_ids: set[str],
    family_counts: Counter[str],
) -> str:
    missing_expected = expected_member_ids - matched_ids
    unexpected_matches = matched_ids - expected_member_ids
    if (
        expected_member_ids
        and not missing_expected
        and not unexpected_matches
        and int(family_counts.get("implement", 0)) == len(expected_member_ids)
    ):
        return IMPLEMENT_EXECUTION_DECISION
    return REDESIGN_EXECUTION_DECISION


def surface_execution_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    selection_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    selection_index: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    selection_by_id: dict[str, dict[str, Any]] = {}
    for row in selection_rows:
        selection_index[row_scope_key(row)].append(row)
        selection_by_id[selection_id(row)] = row

    expected_ids_by_surface: dict[str, set[str]] = defaultdict(set)
    member_row_by_selection_id: dict[str, dict[str, Any]] = {}
    for row in members:
        input_id = selection_id(row)
        expected_ids_by_surface[normalized(row.get("input_scorer_surface_row_id"))].add(input_id)
        member_row_by_selection_id[input_id] = row

    execution_rows: list[dict[str, Any]] = []
    member_execution_rows: list[dict[str, Any]] = []
    evidence_execution_rows: list[dict[str, Any]] = []
    issue_rows: list[dict[str, Any]] = []

    for surface in surfaces:
        surface_id = normalized(surface.get("expanded_market_deconcentrated_scorer_surface_row_id"))
        expected_member_ids = expected_ids_by_surface.get(surface_id, set())
        possible = selection_index.get(surface_scope_key(surface), [])
        matches = [row for row in possible if matches_surface(surface, row)]
        matched_ids = {selection_id(row) for row in matches}
        family_counts = Counter(decision_family(row.get("keep_kill_redesign_implement_decision")) for row in matches)
        decision = surface_execution_decision(expected_member_ids, matched_ids, family_counts)
        missing_expected = expected_member_ids - matched_ids
        unexpected_matches = matched_ids - expected_member_ids
        cost_values = numeric_values(matches, "cost_adjusted_simulated_r")
        decon_cost_values = numeric_values(matches, "deconcentrated_cost_adjusted_simulated_r")
        stress_values = numeric_values(matches, "stress_simulated_r")
        decon_stress_values = numeric_values(matches, "deconcentrated_stress_simulated_r")
        execution_row_id = (
            f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SURFACE-EXEC-{len(execution_rows) + 1:06d}"
        )
        execution_rows.append(
            boundary_row(
                {
                    "expanded_market_deconcentrated_scorer_surface_execution_row_id": execution_row_id,
                    "input_scorer_surface_row_id": surface_id,
                    "surface_scope_sha256": surface.get("surface_scope_sha256"),
                    "surface_function_name": surface.get("surface_function_name"),
                    "surface_expression": surface.get("surface_expression"),
                    "symbol_family": surface.get("symbol_family"),
                    "market_timeframe": surface.get("market_timeframe"),
                    "route_session": surface.get("route_session"),
                    "horizon_id": surface.get("horizon_id"),
                    "side": surface.get("side"),
                    "source_path": surface.get("source_path"),
                    "source_file_sha256": surface.get("source_file_sha256"),
                    "expected_member_rows": len(expected_member_ids),
                    "matched_selection_rows": len(matches),
                    "matched_expected_member_rows": len(matched_ids & expected_member_ids),
                    "matched_unexpected_rows": len(unexpected_matches),
                    "missing_expected_member_rows": len(missing_expected),
                    "matched_implement_rows": int(family_counts.get("implement", 0)),
                    "matched_nonimplement_rows": len(matches) - int(family_counts.get("implement", 0)),
                    "matched_avoid_rows": int(family_counts.get("avoid", 0)),
                    "matched_kill_rows": int(family_counts.get("kill", 0)),
                    "matched_redesign_rows": int(family_counts.get("redesign", 0)),
                    "execution_precision": rounded(
                        len(matched_ids & expected_member_ids) / len(matches) if matches else None
                    ),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
                    "average_win_simulated_r": rounded(average_win(cost_values)),
                    "average_loss_simulated_r": rounded(average_loss(cost_values)),
                    "average_deconcentrated_cost_adjusted_simulated_r": rounded(average(decon_cost_values)),
                    "average_stress_simulated_r": rounded(average(stress_values)),
                    "average_deconcentrated_stress_simulated_r": rounded(average(decon_stress_values)),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in matches),
                    "deconcentrated_effective_n_sum": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in matches)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in matches),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in matches),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in matches),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in matches),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in matches),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in matches),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in matches),
                    "execution_status": "DECONCENTRATED_SCORER_SURFACE_EXECUTION_PASS"
                    if decision == IMPLEMENT_EXECUTION_DECISION
                    else "DECONCENTRATED_SCORER_SURFACE_EXECUTION_REDESIGN",
                    "follow_inverse_default_off_avoid_class": class_from_decision(decision),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )
        for match in matches:
            input_id = selection_id(match)
            expected_member = input_id in expected_member_ids
            match_family = decision_family(match.get("keep_kill_redesign_implement_decision"))
            member_row = member_row_by_selection_id.get(input_id, {})
            member_decision = (
                "IMPLEMENT_EXPANDED_MARKET_DECONCENTRATED_SCORER_MEMBER_EXECUTION"
                if expected_member and match_family == "implement"
                else "REDESIGN_EXPANDED_MARKET_DECONCENTRATED_SCORER_MEMBER_EXECUTION"
            )
            member_execution_rows.append(
                boundary_row(
                    {
                        "expanded_market_deconcentrated_scorer_member_execution_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-MEMBER-EXEC-{len(member_execution_rows) + 1:07d}"
                        ),
                        "input_surface_execution_row_id": execution_row_id,
                        "input_scorer_surface_row_id": surface_id,
                        "input_scorer_member_row_id": member_row.get(
                            "expanded_market_deconcentrated_scorer_member_row_id"
                        ),
                        "input_selection_row_id": input_id,
                        "surface_scope_sha256": surface.get("surface_scope_sha256"),
                        "expected_surface_member": expected_member,
                        "matched_decision_family": match_family,
                        "member_execution_status": "EXPECTED_IMPLEMENT_MEMBER_MATCH"
                        if expected_member and match_family == "implement"
                        else "UNEXPECTED_SURFACE_MATCH",
                        **performance_fields(match),
                        "matched_selection_decision": match.get("keep_kill_redesign_implement_decision"),
                        "follow_inverse_default_off_avoid_class": class_from_decision(member_decision),
                        "keep_kill_redesign_implement_decision": member_decision,
                    }
                )
            )
        if decision != IMPLEMENT_EXECUTION_DECISION:
            issue_rows.append(
                boundary_row(
                    {
                        "expanded_market_deconcentrated_scorer_surface_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SURFACE-EXEC-ISSUE-{len(issue_rows) + 1:06d}"
                        ),
                        "input_surface_execution_row_id": execution_row_id,
                        "input_scorer_surface_row_id": surface_id,
                        "surface_scope_sha256": surface.get("surface_scope_sha256"),
                        "missing_expected_member_rows": len(missing_expected),
                        "matched_unexpected_rows": len(unexpected_matches),
                        "matched_nonimplement_rows": len(matches) - int(family_counts.get("implement", 0)),
                        "issue_status": "DECONCENTRATED_SCORER_SURFACE_EXECUTION_REDESIGN_REQUIRED",
                        "keep_kill_redesign_implement_decision": REDESIGN_EXECUTION_DECISION,
                    }
                )
            )

    for evidence_row in evidence:
        input_id = selection_id(evidence_row)
        source = selection_by_id.get(input_id, evidence_row)
        decision = normalized(source.get("keep_kill_redesign_implement_decision"))
        evidence_execution_rows.append(
            boundary_row(
                {
                    "expanded_market_deconcentrated_nonimplement_evidence_execution_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECON-NONIMPLEMENT-EVIDENCE-EXEC-{len(evidence_execution_rows) + 1:07d}"
                    ),
                    "input_nonimplement_evidence_row_id": evidence_row.get(
                        "expanded_market_deconcentrated_nonimplement_evidence_row_id"
                    ),
                    "input_selection_row_id": input_id,
                    "evidence_execution_status": "NONIMPLEMENT_NUMERIC_EVIDENCE_PRESERVED",
                    **performance_fields(source),
                    "matched_selection_decision": decision,
                    "follow_inverse_default_off_avoid_class": source.get(
                        "follow_inverse_default_off_avoid_class", class_from_decision(decision)
                    ),
                    "keep_kill_redesign_implement_decision": decision,
                }
            )
        )

    return execution_rows, member_execution_rows, evidence_execution_rows, issue_rows


def aggregate_execution_rows(
    surface_executions: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    all_rows = surface_executions + member_executions + evidence_executions
    total_rows = len(all_rows) or 1
    for family, rows in (
        ("surface_execution", surface_executions),
        ("member_execution", member_executions),
        ("nonimplement_evidence_execution", evidence_executions),
    ):
        decisions = Counter(row.get("keep_kill_redesign_implement_decision") for row in rows)
        cost_values = numeric_values(rows, "cost_adjusted_simulated_r") + numeric_values(
            rows, "expectancy_cost_adjusted_simulated_r"
        )
        decon_cost_values = numeric_values(rows, "deconcentrated_cost_adjusted_simulated_r") + numeric_values(
            rows, "average_deconcentrated_cost_adjusted_simulated_r"
        )
        source_counts = Counter(normalized(row.get("source_path")) for row in rows)
        output.append(
            boundary_row(
                {
                    "expanded_market_deconcentrated_scorer_surface_execution_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SURFACE-EXEC-AGG-{len(output) + 1:04d}"
                    ),
                    "aggregate_family": family,
                    "row_count": len(rows),
                    "share_of_all_execution_rows": rounded(len(rows) / total_rows),
                    "source_path_count": len({row.get("source_path") for row in rows}),
                    "symbol_family_count": len({row.get("symbol_family") for row in rows}),
                    "effective_n_sum": sum(int(row.get("effective_n") or 0) for row in rows),
                    "deconcentrated_effective_n_sum": rounded(
                        sum(float(row.get("deconcentrated_effective_n") or 0.0) for row in rows)
                    ),
                    "win_count": sum(int(row.get("win_count") or 0) for row in rows),
                    "loss_count": sum(int(row.get("loss_count") or 0) for row in rows),
                    "zero_count": sum(int(row.get("zero_count") or 0) for row in rows),
                    "target_first_count": sum(int(row.get("target_first_count") or 0) for row in rows),
                    "stop_first_count": sum(int(row.get("stop_first_count") or 0) for row in rows),
                    "neither_count": sum(int(row.get("neither_count") or 0) for row in rows),
                    "ambiguous_count": sum(int(row.get("ambiguous_count") or 0) for row in rows),
                    "expectancy_cost_adjusted_simulated_r": rounded(average(cost_values)),
                    "average_win_simulated_r": rounded(average_win(cost_values)),
                    "average_loss_simulated_r": rounded(average_loss(cost_values)),
                    "average_deconcentrated_cost_adjusted_simulated_r": rounded(average(decon_cost_values)),
                    "concentration_top_source_path_share": rounded(
                        (source_counts.most_common(1)[0][1] / len(rows)) if rows and source_counts else None
                    ),
                    "decision_counts": dict(sorted(decisions.items())),
                }
            )
        )
    return output


def system_execution_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    surface_executions: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    evidence_executions: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    metadata: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "expanded_market_deconcentrated_scorer_surface_execution_system_row_id": (
                    "OHLC-GTOS-EXPANDED-MARKET-DECON-SCORER-SURFACE-EXEC-SYSTEM-0001"
                ),
                "input_scorer_surface_rows": len(surfaces),
                "input_scorer_member_rows": len(members),
                "input_nonimplement_evidence_rows": len(evidence),
                "surface_execution_rows": len(surface_executions),
                "surface_execution_pass_rows": sum(
                    1
                    for row in surface_executions
                    if row.get("keep_kill_redesign_implement_decision") == IMPLEMENT_EXECUTION_DECISION
                ),
                "surface_execution_redesign_rows": sum(
                    1
                    for row in surface_executions
                    if row.get("keep_kill_redesign_implement_decision") == REDESIGN_EXECUTION_DECISION
                ),
                "member_execution_rows": len(member_executions),
                "nonimplement_evidence_execution_rows": len(evidence_executions),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "source_path_count": len({row.get("source_path") for row in member_executions + evidence_executions}),
                "symbol_family_count": len(
                    {row.get("symbol_family") for row in member_executions + evidence_executions}
                ),
                "surface_decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in surface_executions).items())
                ),
                "member_decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in member_executions).items())
                ),
                "evidence_decision_counts": dict(
                    sorted(Counter(row.get("keep_kill_redesign_implement_decision") for row in evidence_executions).items())
                ),
                "metadata": metadata,
            }
        )
    ]
