"""Strict predicate repair for expanded-market unified action surfaces."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_unified_action_surface_execution import (
    GEOMETRY_FIELDS,
    action_hash_matches_surface,
    as_int,
    first_missing_geometry_field,
    first_missing_simulated_field,
    normalized,
    rounded,
    scope_predicate_matches,
    weighted_average,
)


EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_strict_action_surface_repair.py"
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
    output["expanded_market_unified_strict_action_surface_repair_surface"] = (
        EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def action_id(row: dict[str, Any]) -> str:
    return normalized(row.get("unified_implementation_action_row_id"))


def geometry_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    source = row or {}
    return {field: source.get(field) for field in GEOMETRY_FIELDS}


def strict_predicate_matches(action: dict[str, Any], surface: dict[str, Any]) -> bool:
    return scope_predicate_matches(action, surface) and action_hash_matches_surface(action, surface)


def issue_by_surface(issue_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {normalized(row.get("input_unified_action_surface_row_id")): row for row in issue_rows}


def strict_expression(surface: dict[str, Any]) -> str:
    base = normalized(surface.get("action_surface_expression"))
    scope_hash = normalized(surface.get("action_surface_scope_sha256"))
    expression_hash = normalized(surface.get("action_surface_expression_sha256"))
    return (
        f"({base}) and row.get('branch_local_action_scope_sha256') == {scope_hash!r} "
        f"and row.get('branch_local_action_expression_sha256') == {expression_hash!r}"
    )


def strict_surface_rows(
    surfaces: list[dict[str, Any]],
    previous_issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    issues = issue_by_surface(previous_issues)
    output: list[dict[str, Any]] = []
    for index, surface in enumerate(sorted(surfaces, key=lambda item: normalized(item.get("unified_action_surface_row_id"))), start=1):
        surface_id = normalized(surface.get("unified_action_surface_row_id"))
        prior_issue = issues.get(surface_id)
        output.append(
            boundary_row(
                {
                    "strict_action_surface_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-SURFACE-{index:06d}"
                    ),
                    "input_unified_action_surface_row_id": surface_id,
                    "action_surface_scope_sha256": surface.get("action_surface_scope_sha256"),
                    "action_surface_expression_sha256": surface.get("action_surface_expression_sha256"),
                    "strict_action_surface_expression": strict_expression(surface),
                    "strict_action_surface_function_name": (
                        f"expanded_market_unified_strict_action_surface_"
                        f"{normalized(surface.get('action_surface_scope_sha256'))[:12]}"
                    ),
                    "strict_repair_mode": (
                        "HASH_GUARD_REPAIRED_PREDICATE_BREADTH"
                        if prior_issue
                        else "HASH_GUARDED_PREDICATE_CLEAN"
                    ),
                    "previous_predicate_extra_match_rows": (
                        prior_issue.get("predicate_extra_match_rows") if prior_issue else 0
                    ),
                    "action_surface_family": surface.get("action_surface_family"),
                    "symbol": surface.get("symbol"),
                    "source_symbol": surface.get("source_symbol"),
                    "market_timeframe": surface.get("market_timeframe"),
                    "route_session": surface.get("route_session"),
                    "horizon_id": surface.get("horizon_id"),
                    "source_component": surface.get("source_component"),
                    "selected_side": surface.get("selected_side"),
                    "member_action_rows": surface.get("member_action_rows"),
                    "average_cost_adjusted_simulated_r": surface.get("average_cost_adjusted_simulated_r"),
                    "average_stress_simulated_r": surface.get("average_stress_simulated_r"),
                    "effective_n_sum": surface.get("effective_n_sum"),
                    "target_first_count_sum": surface.get("target_first_count_sum"),
                    "stop_first_count_sum": surface.get("stop_first_count_sum"),
                    "ambiguous_count_sum": surface.get("ambiguous_count_sum"),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR"
                    ),
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )
    return output


def strict_surface_execution_rows(
    strict_surfaces: list[dict[str, Any]],
    original_surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    implementation_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    original_by_id = {normalized(row.get("unified_action_surface_row_id")): row for row in original_surfaces}
    members_by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for member in members:
        members_by_surface[normalized(member.get("input_unified_action_surface_row_id"))].append(member)

    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, strict_surface in enumerate(
        sorted(strict_surfaces, key=lambda item: normalized(item.get("strict_action_surface_row_id"))),
        start=1,
    ):
        surface_id = normalized(strict_surface.get("input_unified_action_surface_row_id"))
        original = original_by_id.get(surface_id) or {}
        expected_members = members_by_surface.get(surface_id, [])
        expected_ids = {normalized(member.get("input_unified_implementation_action_row_id")) for member in expected_members}
        strict_matches = [row for row in implementation_actions if strict_predicate_matches(row, original)]
        strict_ids = {action_id(row) for row in strict_matches}
        missing_ids = sorted(expected_ids - strict_ids)
        unexpected_ids = sorted(strict_ids - expected_ids)
        passed = not missing_ids and not unexpected_ids
        output_row = boundary_row(
            {
                "strict_action_surface_execution_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-SURFACE-EXECUTION-{index:06d}"
                ),
                "input_strict_action_surface_row_id": strict_surface.get("strict_action_surface_row_id"),
                "input_unified_action_surface_row_id": surface_id,
                "strict_repair_mode": strict_surface.get("strict_repair_mode"),
                "action_surface_family": strict_surface.get("action_surface_family"),
                "symbol": strict_surface.get("symbol"),
                "source_symbol": strict_surface.get("source_symbol"),
                "market_timeframe": strict_surface.get("market_timeframe"),
                "route_session": strict_surface.get("route_session"),
                "horizon_id": strict_surface.get("horizon_id"),
                "source_component": strict_surface.get("source_component"),
                "selected_side": strict_surface.get("selected_side"),
                "expected_member_action_rows": len(expected_members),
                "strict_execution_match_rows": len(strict_matches),
                "missing_expected_member_rows": len(missing_ids),
                "unexpected_strict_match_rows": len(unexpected_ids),
                "strict_execution_status": (
                    "STRICT_ACTION_SURFACE_EXECUTION_PASS"
                    if passed
                    else "STRICT_ACTION_SURFACE_EXECUTION_REDESIGN_REQUIRED"
                ),
                "strict_execution_issue_ids": json.dumps(
                    {"missing": missing_ids[:25], "unexpected": unexpected_ids[:25]},
                    sort_keys=True,
                ),
                "average_cost_adjusted_simulated_r": rounded(
                    weighted_average(strict_matches, "cost_adjusted_simulated_r")
                ),
                "average_stress_simulated_r": rounded(weighted_average(strict_matches, "stress_simulated_r")),
                "effective_n_sum": sum(as_int(row.get("effective_n")) for row in strict_matches),
                "target_first_count_sum": sum(as_int(row.get("target_first_count")) for row in strict_matches),
                "stop_first_count_sum": sum(as_int(row.get("stop_first_count")) for row in strict_matches),
                "neither_count_sum": sum(as_int(row.get("neither_count")) for row in strict_matches),
                "ambiguous_count_sum": sum(as_int(row.get("ambiguous_count")) for row in strict_matches),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_EXECUTION"
                    if passed
                    else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_EXECUTION"
                ),
                "follow_inverse_default_off_avoid_class": "follow" if passed else "redesign",
            }
        )
        output.append(output_row)
        if not passed:
            issues.append(
                boundary_row(
                    {
                        "strict_action_surface_repair_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-SURFACE-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_unified_action_surface_row_id": surface_id,
                        "strict_execution_issue_class": "strict_surface_membership_mismatch",
                        "missing_expected_member_rows": len(missing_ids),
                        "unexpected_strict_match_rows": len(unexpected_ids),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_EXECUTION"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def strict_member_execution_rows(
    strict_surfaces: list[dict[str, Any]],
    original_surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    actions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    strict_by_surface = {
        normalized(row.get("input_unified_action_surface_row_id")): row for row in strict_surfaces
    }
    original_by_id = {normalized(row.get("unified_action_surface_row_id")): row for row in original_surfaces}
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, member in enumerate(
        sorted(members, key=lambda item: normalized(item.get("unified_action_surface_member_row_id"))),
        start=1,
    ):
        surface_id = normalized(member.get("input_unified_action_surface_row_id"))
        source_action_id = normalized(member.get("input_unified_implementation_action_row_id"))
        strict_surface = strict_by_surface.get(surface_id)
        original = original_by_id.get(surface_id)
        action = actions_by_id.get(source_action_id)
        passed = bool(action and original and strict_predicate_matches(action, original))
        source = action or member
        row = {
            "strict_action_surface_member_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-MEMBER-EXECUTION-{index:08d}"
            ),
            "input_unified_action_surface_member_row_id": member.get("unified_action_surface_member_row_id"),
            "input_strict_action_surface_row_id": (
                strict_surface.get("strict_action_surface_row_id") if strict_surface else None
            ),
            "input_unified_action_surface_row_id": surface_id,
            "input_unified_implementation_action_row_id": source_action_id,
            "strict_repair_mode": strict_surface.get("strict_repair_mode") if strict_surface else None,
            "action_row_kind": source.get("action_row_kind"),
            "symbol": source.get("symbol"),
            "source_symbol": source.get("source_symbol"),
            "market_timeframe": source.get("market_timeframe"),
            "route_session": source.get("route_session"),
            "horizon_id": source.get("horizon_id"),
            "source_component": source.get("source_component"),
            "source_path": source.get("source_path"),
            "source_file_sha256": source.get("source_file_sha256"),
            "selected_side": source.get("selected_side"),
            "strict_member_execution_status": (
                "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS"
                if passed
                else "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_REDESIGN_REQUIRED"
            ),
            "missing_simulated_field": first_missing_simulated_field(source),
            "missing_geometry_field": first_missing_geometry_field(source),
            "source_action_decision": source.get("keep_kill_redesign_implement_decision"),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_MEMBER_EXECUTION"
                if passed
                else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_MEMBER_EXECUTION"
            ),
            "follow_inverse_default_off_avoid_class": source.get("follow_inverse_default_off_avoid_class", "follow"),
        }
        row.update(geometry_payload(source))
        output.append(boundary_row(row))
        if not passed:
            issues.append(
                boundary_row(
                    {
                        "strict_action_surface_repair_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-SURFACE-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_unified_action_surface_member_row_id": member.get(
                            "unified_action_surface_member_row_id"
                        ),
                        "input_unified_action_surface_row_id": surface_id,
                        "input_unified_implementation_action_row_id": source_action_id,
                        "strict_execution_issue_class": "strict_member_execution_mismatch",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_MEMBER_EXECUTION"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def strict_redesign_preservation_rows(redesign_execution_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, row in enumerate(
        sorted(redesign_execution_rows, key=lambda item: normalized(item.get("unified_action_surface_redesign_execution_row_id"))),
        start=1,
    ):
        payload = {
            "strict_action_surface_redesign_preservation_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-REDESIGN-PRESERVE-{index:06d}"
            ),
            "input_unified_action_surface_redesign_execution_row_id": row.get(
                "unified_action_surface_redesign_execution_row_id"
            ),
            "input_unified_implementation_action_row_id": row.get("input_unified_implementation_action_row_id"),
            "action_row_kind": row.get("action_row_kind"),
            "symbol": row.get("symbol"),
            "source_symbol": row.get("source_symbol"),
            "market_timeframe": row.get("market_timeframe"),
            "route_session": row.get("route_session"),
            "horizon_id": row.get("horizon_id"),
            "source_component": row.get("source_component"),
            "source_path": row.get("source_path"),
            "source_file_sha256": row.get("source_file_sha256"),
            "selected_side": row.get("selected_side"),
            "strict_redesign_preservation_status": "STRICT_ACTION_SURFACE_REDESIGN_NUMERIC_PROOF_PRESERVED",
            "missing_simulated_field": row.get("missing_simulated_field"),
            "missing_geometry_field": row.get("missing_geometry_field"),
            "source_action_decision": row.get("source_action_decision"),
            "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class", "redesign"),
        }
        payload.update(geometry_payload(row))
        output.append(boundary_row(payload))
    return output


def strict_repair_proof_rows(
    strict_surfaces: list[dict[str, Any]],
    strict_executions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    execution_by_surface = {
        normalized(row.get("input_unified_action_surface_row_id")): row for row in strict_executions
    }
    output: list[dict[str, Any]] = []
    for strict_surface in strict_surfaces:
        if strict_surface.get("strict_repair_mode") != "HASH_GUARD_REPAIRED_PREDICATE_BREADTH":
            continue
        surface_id = normalized(strict_surface.get("input_unified_action_surface_row_id"))
        execution = execution_by_surface.get(surface_id) or {}
        output.append(
            boundary_row(
                {
                    "strict_action_surface_repair_proof_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-REPAIR-PROOF-{len(output) + 1:06d}"
                    ),
                    "input_strict_action_surface_row_id": strict_surface.get("strict_action_surface_row_id"),
                    "input_unified_action_surface_row_id": surface_id,
                    "strict_repair_mode": strict_surface.get("strict_repair_mode"),
                    "previous_predicate_extra_match_rows": strict_surface.get("previous_predicate_extra_match_rows"),
                    "strict_execution_match_rows": execution.get("strict_execution_match_rows"),
                    "missing_expected_member_rows": execution.get("missing_expected_member_rows"),
                    "unexpected_strict_match_rows": execution.get("unexpected_strict_match_rows"),
                    "average_cost_adjusted_simulated_r": execution.get("average_cost_adjusted_simulated_r"),
                    "average_stress_simulated_r": execution.get("average_stress_simulated_r"),
                    "effective_n_sum": execution.get("effective_n_sum"),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_PROOF"
                    ),
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )
    return output


def aggregate_strict_repair_rows(
    strict_surfaces: list[dict[str, Any]],
    strict_executions: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    redesign_preservations: list[dict[str, Any]],
    repair_proofs: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for family, rows in [
        ("strict_surface", strict_surfaces),
        ("strict_surface_execution", strict_executions),
        ("strict_member_execution", member_executions),
        ("strict_redesign_preservation", redesign_preservations),
        ("strict_repair_proof", repair_proofs),
    ]:
        prepared.extend({**row, "strict_row_family": family} for row in rows)
    specs = [
        ("portfolio", []),
        ("row_family", ["strict_row_family"]),
        ("repair_mode", ["strict_repair_mode"]),
        ("symbol_timeframe_session", ["symbol", "market_timeframe", "route_session"]),
        ("decision", ["keep_kill_redesign_implement_decision"]),
    ]
    output: list[dict[str, Any]] = []
    for level, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in prepared:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, rows in sorted(groups.items(), key=lambda item: tuple(normalized(part) for part in item[0])):
            output.append(
                boundary_row(
                    {
                        "strict_action_surface_repair_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-AGG-{len(output) + 1:06d}"
                        ),
                        "aggregate_level": level,
                        "aggregate_dimensions": {field: value for field, value in zip(fields, key)},
                        "row_count": len(rows),
                        "issue_rows": len(issues) if level == "portfolio" else 0,
                        "effective_n_sum": sum(as_int(row.get("effective_n") or row.get("effective_n_sum")) for row in rows),
                        "average_cost_adjusted_simulated_r": rounded(
                            weighted_average(
                                [row for row in rows if row.get("cost_adjusted_simulated_r") is not None],
                                "cost_adjusted_simulated_r",
                            )
                        ),
                        "average_stress_simulated_r": rounded(
                            weighted_average(
                                [row for row in rows if row.get("stress_simulated_r") is not None],
                                "stress_simulated_r",
                            )
                        ),
                        "keep_kill_redesign_implement_decision": aggregate_decision(rows),
                        "follow_inverse_default_off_avoid_class": aggregate_class(rows),
                    }
                )
            )
    return output


def aggregate_decision(rows: list[dict[str, Any]]) -> str:
    decisions = {normalized(row.get("keep_kill_redesign_implement_decision")) for row in rows}
    if all(decision.startswith("IMPLEMENT_") for decision in decisions):
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_AGGREGATE"
    if all(decision.startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def unified_strict_action_surface_repair_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    redesign_execution_rows: list[dict[str, Any]],
    previous_issue_rows: list[dict[str, Any]],
    evidence_actions: list[dict[str, Any]],
    decision_actions: list[dict[str, Any]],
    terminal_actions: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    actions = evidence_actions + decision_actions + terminal_actions
    actions_by_id = {action_id(row): row for row in actions if action_id(row)}
    implementation_actions = [
        row
        for row in actions
        if normalized(row.get("keep_kill_redesign_implement_decision")).startswith("IMPLEMENT_")
    ]
    strict_surfaces = strict_surface_rows(surfaces, previous_issue_rows)
    strict_executions, surface_issues = strict_surface_execution_rows(
        strict_surfaces, surfaces, members, implementation_actions
    )
    member_executions, member_issues = strict_member_execution_rows(
        strict_surfaces, surfaces, members, actions_by_id
    )
    redesign_preservations = strict_redesign_preservation_rows(redesign_execution_rows)
    repair_proofs = strict_repair_proof_rows(strict_surfaces, strict_executions)
    issues = surface_issues + member_issues
    aggregates = aggregate_strict_repair_rows(
        strict_surfaces,
        strict_executions,
        member_executions,
        redesign_preservations,
        repair_proofs,
        issues,
    )
    return strict_surfaces, strict_executions, member_executions, redesign_preservations, repair_proofs, aggregates, issues


def system_unified_strict_action_surface_repair_rows(
    strict_surfaces: list[dict[str, Any]],
    strict_executions: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    redesign_preservations: list[dict[str, Any]],
    repair_proofs: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ACTION-SURFACE-REPAIR-SYSTEM-000001",
                "input_counts": input_counts,
                "strict_surface_rows": len(strict_surfaces),
                "strict_surface_execution_rows": len(strict_executions),
                "strict_member_execution_rows": len(member_executions),
                "strict_redesign_preservation_rows": len(redesign_preservations),
                "strict_repair_proof_rows": len(repair_proofs),
                "aggregate_rows": len(aggregates),
                "issue_rows": len(issues),
                "strict_surface_execution_pass_rows": sum(
                    1
                    for row in strict_executions
                    if row.get("strict_execution_status") == "STRICT_ACTION_SURFACE_EXECUTION_PASS"
                ),
                "strict_member_execution_pass_rows": sum(
                    1
                    for row in member_executions
                    if row.get("strict_member_execution_status")
                    == "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS"
                ),
                "hash_guard_repaired_surface_rows": sum(
                    1
                    for row in strict_surfaces
                    if row.get("strict_repair_mode") == "HASH_GUARD_REPAIRED_PREDICATE_BREADTH"
                ),
                "member_rows_with_simulated_r": sum(
                    1 for row in member_executions if first_missing_simulated_field(row) is None
                ),
                "redesign_rows_with_simulated_r": sum(
                    1 for row in redesign_preservations if first_missing_simulated_field(row) is None
                ),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ACTION_SURFACE_REPAIR_SYSTEM"
                ),
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
