"""Execution rows for expanded-market unified action surfaces."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Any


EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_action_surface_execution.py"
)
BOUNDARY_SCHEMA = "concrete_branch_local_research_boundary_v1"

GEOMETRY_FIELDS = [
    "entry_reference",
    "proxy_entry_price",
    "proxy_stop_price",
    "proxy_target_price",
    "proxy_denominator_price",
    "path_order_result",
    "fill_status",
    "gross_simulated_r",
    "cost_adjusted_simulated_r",
    "stress_simulated_r",
    "win_count",
    "loss_count",
    "flat_count",
    "zero_count",
    "no_fill_count",
    "average_win",
    "average_loss",
    "target_first_count",
    "stop_first_count",
    "neither_count",
    "ambiguous_count",
    "effective_n",
    "effective_n_after_duplicate_collapse",
    "duplicate_row_count",
    "target_first_share",
    "stop_first_share",
    "target_stop_edge_share",
    "ambiguous_share",
    "concentration_top_month_share",
]


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
    output["expanded_market_unified_action_surface_execution_surface"] = (
        EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_SURFACE
    )
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


def as_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def is_implementation_action(row: dict[str, Any]) -> bool:
    return normalized(row.get("keep_kill_redesign_implement_decision")).startswith("IMPLEMENT_")


def action_id(row: dict[str, Any]) -> str:
    return normalized(row.get("unified_implementation_action_row_id"))


def weighted_average(rows: list[dict[str, Any]], field: str) -> float | None:
    numerator = 0.0
    denominator = 0.0
    for row in rows:
        value = as_float(row.get(field))
        weight = as_float(row.get("effective_n"))
        if value is None or weight is None or weight <= 0:
            continue
        numerator += value * weight
        denominator += weight
    return None if denominator == 0 else numerator / denominator


def scope_predicate_matches(action: dict[str, Any], surface: dict[str, Any]) -> bool:
    scope = surface.get("action_surface_scope") or {}
    equality_fields = [
        "symbol",
        "source_symbol",
        "market_timeframe",
        "route_session",
        "horizon_id",
        "source_component",
        "selected_side",
        "source_path",
        "source_file_sha256",
    ]
    for field in equality_fields:
        if normalized(action.get(field)) != normalized(scope.get(field)):
            return False

    minimums = [
        ("cost_adjusted_simulated_r", "minimum_cost_adjusted_simulated_r"),
        ("stress_simulated_r", "minimum_stress_simulated_r"),
        ("effective_n", "minimum_effective_n"),
        ("target_stop_edge_share", "minimum_target_stop_edge_share"),
    ]
    for row_field, scope_field in minimums:
        threshold = as_float(scope.get(scope_field))
        if threshold is None:
            continue
        value = as_float(action.get(row_field))
        if value is None or value < threshold:
            return False

    maximums = [
        ("ambiguous_share", "maximum_ambiguous_share"),
        ("concentration_top_month_share", "maximum_concentration_top_month_share"),
    ]
    for row_field, scope_field in maximums:
        threshold = as_float(scope.get(scope_field))
        if threshold is None:
            continue
        value = as_float(action.get(row_field))
        if value is None or value > threshold:
            return False
    return True


def action_hash_matches_surface(action: dict[str, Any], surface: dict[str, Any]) -> bool:
    return (
        action.get("branch_local_action_scope_sha256") == surface.get("action_surface_scope_sha256")
        and action.get("branch_local_action_expression_sha256")
        == surface.get("action_surface_expression_sha256")
        and is_implementation_action(action)
    )


def action_executes_surface(action: dict[str, Any], surface: dict[str, Any]) -> bool:
    return scope_predicate_matches(action, surface) and action_hash_matches_surface(action, surface)


def first_missing_simulated_field(row: dict[str, Any]) -> str | None:
    for field in ["gross_simulated_r", "cost_adjusted_simulated_r", "stress_simulated_r"]:
        if as_float(row.get(field)) is None:
            return field
    return None


def first_missing_geometry_field(row: dict[str, Any]) -> str | None:
    for field in [
        "entry_reference",
        "proxy_entry_price",
        "proxy_stop_price",
        "proxy_target_price",
        "proxy_denominator_price",
        "path_order_result",
        "fill_status",
    ]:
        if row.get(field) in (None, ""):
            return field
    return None


def geometry_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    source = row or {}
    return {field: source.get(field) for field in GEOMETRY_FIELDS}


def surface_execution_rows(
    surfaces: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    implementation_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    members_by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for member in member_rows:
        members_by_surface[normalized(member.get("input_unified_action_surface_row_id"))].append(member)

    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, surface in enumerate(sorted(surfaces, key=lambda item: normalized(item.get("unified_action_surface_row_id"))), start=1):
        surface_id = normalized(surface.get("unified_action_surface_row_id"))
        expected_members = members_by_surface.get(surface_id, [])
        expected_ids = {normalized(member.get("input_unified_implementation_action_row_id")) for member in expected_members}
        predicate_matches = [row for row in implementation_actions if scope_predicate_matches(row, surface)]
        hash_matches = [row for row in implementation_actions if action_hash_matches_surface(row, surface)]
        execution_matches = [row for row in implementation_actions if action_executes_surface(row, surface)]
        execution_ids = {action_id(row) for row in execution_matches}
        missing_ids = sorted(expected_ids - execution_ids)
        unexpected_ids = sorted(execution_ids - expected_ids)
        predicate_extra_ids = sorted({action_id(row) for row in predicate_matches} - expected_ids)
        passed = not missing_ids and not unexpected_ids and not predicate_extra_ids
        status = (
            "ACTION_SURFACE_EXECUTION_PASS"
            if passed
            else "ACTION_SURFACE_EXECUTION_REDESIGN_REQUIRED"
        )
        decision = (
            "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION"
            if passed
            else "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_MISMATCH"
        )
        row = boundary_row(
            {
                "unified_action_surface_execution_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-{index:06d}"
                ),
                "input_unified_action_surface_row_id": surface_id,
                "action_surface_scope_sha256": surface.get("action_surface_scope_sha256"),
                "action_surface_expression_sha256": surface.get("action_surface_expression_sha256"),
                "action_surface_function_name": surface.get("action_surface_function_name"),
                "action_surface_family": surface.get("action_surface_family"),
                "symbol": surface.get("symbol"),
                "source_symbol": surface.get("source_symbol"),
                "market_timeframe": surface.get("market_timeframe"),
                "route_session": surface.get("route_session"),
                "horizon_id": surface.get("horizon_id"),
                "source_component": surface.get("source_component"),
                "selected_side": surface.get("selected_side"),
                "expected_member_action_rows": len(expected_members),
                "predicate_match_rows": len(predicate_matches),
                "hash_match_rows": len(hash_matches),
                "execution_match_rows": len(execution_matches),
                "missing_expected_member_rows": len(missing_ids),
                "unexpected_execution_match_rows": len(unexpected_ids),
                "predicate_extra_match_rows": len(predicate_extra_ids),
                "execution_status": status,
                "execution_issue_ids": json.dumps(
                    {
                        "missing": missing_ids[:25],
                        "unexpected": unexpected_ids[:25],
                        "predicate_extra": predicate_extra_ids[:25],
                    },
                    sort_keys=True,
                ),
                "average_cost_adjusted_simulated_r": rounded(
                    weighted_average(execution_matches, "cost_adjusted_simulated_r")
                ),
                "average_stress_simulated_r": rounded(weighted_average(execution_matches, "stress_simulated_r")),
                "effective_n_sum": sum(as_int(row.get("effective_n")) for row in execution_matches),
                "target_first_count_sum": sum(as_int(row.get("target_first_count")) for row in execution_matches),
                "stop_first_count_sum": sum(as_int(row.get("stop_first_count")) for row in execution_matches),
                "neither_count_sum": sum(as_int(row.get("neither_count")) for row in execution_matches),
                "ambiguous_count_sum": sum(as_int(row.get("ambiguous_count")) for row in execution_matches),
                "source_path_count": len({row.get("source_path") for row in execution_matches if row.get("source_path")}),
                "source_hash_count": len(
                    {row.get("source_file_sha256") for row in execution_matches if row.get("source_file_sha256")}
                ),
                "keep_kill_redesign_implement_decision": decision,
                "follow_inverse_default_off_avoid_class": "follow" if passed else "redesign",
            }
        )
        output.append(row)
        if not passed:
            issues.append(
                boundary_row(
                    {
                        "unified_action_surface_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_unified_action_surface_row_id": surface_id,
                        "execution_issue_class": "surface_execution_membership_mismatch",
                        "action_surface_family": surface.get("action_surface_family"),
                        "symbol": surface.get("symbol"),
                        "source_symbol": surface.get("source_symbol"),
                        "market_timeframe": surface.get("market_timeframe"),
                        "route_session": surface.get("route_session"),
                        "horizon_id": surface.get("horizon_id"),
                        "source_component": surface.get("source_component"),
                        "selected_side": surface.get("selected_side"),
                        "expected_member_action_rows": len(expected_members),
                        "predicate_match_rows": len(predicate_matches),
                        "hash_match_rows": len(hash_matches),
                        "execution_match_rows": len(execution_matches),
                        "missing_expected_member_rows": len(missing_ids),
                        "unexpected_execution_match_rows": len(unexpected_ids),
                        "predicate_extra_match_rows": len(predicate_extra_ids),
                        "predicate_extra_action_ids": json.dumps(predicate_extra_ids[:25], sort_keys=True),
                        "average_cost_adjusted_simulated_r": row.get("average_cost_adjusted_simulated_r"),
                        "average_stress_simulated_r": row.get("average_stress_simulated_r"),
                        "effective_n_sum": row.get("effective_n_sum"),
                        "target_first_count_sum": row.get("target_first_count_sum"),
                        "stop_first_count_sum": row.get("stop_first_count_sum"),
                        "neither_count_sum": row.get("neither_count_sum"),
                        "ambiguous_count_sum": row.get("ambiguous_count_sum"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_MISMATCH"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def member_execution_rows(
    member_rows: list[dict[str, Any]],
    surfaces: list[dict[str, Any]],
    actions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    surfaces_by_id = {normalized(row.get("unified_action_surface_row_id")): row for row in surfaces}
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, member in enumerate(
        sorted(member_rows, key=lambda item: normalized(item.get("unified_action_surface_member_row_id"))),
        start=1,
    ):
        member_id = normalized(member.get("unified_action_surface_member_row_id"))
        surface_id = normalized(member.get("input_unified_action_surface_row_id"))
        source_action_id = normalized(member.get("input_unified_implementation_action_row_id"))
        surface = surfaces_by_id.get(surface_id)
        action = actions_by_id.get(source_action_id)
        predicate_match = bool(action and surface and scope_predicate_matches(action, surface))
        hash_match = bool(action and surface and action_hash_matches_surface(action, surface))
        source_present = action is not None
        surface_present = surface is not None
        passed = (
            source_present
            and surface_present
            and predicate_match
            and hash_match
            and member.get("surface_member_match") is True
        )
        status = "ACTION_SURFACE_MEMBER_EXECUTION_PASS" if passed else "ACTION_SURFACE_MEMBER_EXECUTION_REDESIGN_REQUIRED"
        source = action or member
        row = {
            "unified_action_surface_member_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-MEMBER-EXECUTION-{index:08d}"
            ),
            "input_unified_action_surface_member_row_id": member_id,
            "input_unified_action_surface_row_id": surface_id,
            "input_unified_implementation_action_row_id": source_action_id,
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
            "source_action_present": source_present,
            "surface_present": surface_present,
            "scope_predicate_match": predicate_match,
            "hash_match": hash_match,
            "surface_member_match": member.get("surface_member_match"),
            "execution_status": status,
            "missing_simulated_field": first_missing_simulated_field(source),
            "missing_geometry_field": first_missing_geometry_field(source),
            "source_action_decision": source.get("keep_kill_redesign_implement_decision"),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_MEMBER_EXECUTION"
                if passed
                else "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_MEMBER_EXECUTION"
            ),
            "follow_inverse_default_off_avoid_class": source.get("follow_inverse_default_off_avoid_class", "follow"),
        }
        row.update(geometry_payload(source))
        output.append(boundary_row(row))
        if not passed:
            issues.append(
                boundary_row(
                    {
                        "unified_action_surface_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_unified_action_surface_member_row_id": member_id,
                        "input_unified_action_surface_row_id": surface_id,
                        "input_unified_implementation_action_row_id": source_action_id,
                        "execution_issue_class": "surface_member_execution_mismatch",
                        "source_action_present": source_present,
                        "surface_present": surface_present,
                        "scope_predicate_match": predicate_match,
                        "hash_match": hash_match,
                        "surface_member_match": member.get("surface_member_match"),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_MEMBER_EXECUTION"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def redesign_execution_rows(
    redesign_rows: list[dict[str, Any]],
    actions_by_id: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, redesign in enumerate(
        sorted(redesign_rows, key=lambda item: normalized(item.get("unified_action_surface_redesign_row_id"))),
        start=1,
    ):
        source_action_id = normalized(redesign.get("input_unified_implementation_action_row_id"))
        action = actions_by_id.get(source_action_id)
        source = action or redesign
        missing_simulated = first_missing_simulated_field(source)
        status = (
            "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF"
            if action is not None and missing_simulated is None
            else "REDESIGN_ACTION_EXECUTION_REQUIRES_REPLAY_FIELD"
        )
        row = {
            "unified_action_surface_redesign_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-REDESIGN-EXECUTION-{index:06d}"
            ),
            "input_unified_action_surface_redesign_row_id": redesign.get("unified_action_surface_redesign_row_id"),
            "input_unified_redesign_action_row_id": redesign.get("input_unified_redesign_action_row_id"),
            "input_unified_implementation_action_row_id": source_action_id,
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
            "source_action_present": action is not None,
            "execution_status": status,
            "stress_blocking_reason": source.get("stress_blocking_reason"),
            "branch_local_action_status": source.get("branch_local_action_status"),
            "missing_simulated_field": missing_simulated,
            "missing_geometry_field": first_missing_geometry_field(source),
            "source_action_decision": source.get("keep_kill_redesign_implement_decision"),
            "keep_kill_redesign_implement_decision": source.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": source.get("follow_inverse_default_off_avoid_class", "redesign"),
        }
        row.update(geometry_payload(source))
        output.append(boundary_row(row))
        if status != "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF":
            issues.append(
                boundary_row(
                    {
                        "unified_action_surface_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_unified_action_surface_redesign_row_id": redesign.get("unified_action_surface_redesign_row_id"),
                        "input_unified_implementation_action_row_id": source_action_id,
                        "execution_issue_class": "redesign_execution_missing_numeric_source",
                        "missing_simulated_field": missing_simulated,
                        "source_action_present": action is not None,
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_REDESIGN_EXECUTION"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def aggregate_execution_rows(
    surface_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    combined = surface_rows + member_rows + redesign_rows
    specs = [
        ("portfolio", []),
        ("row_family", ["execution_row_family"]),
        ("execution_status", ["execution_status"]),
        ("action_kind", ["action_row_kind"]),
        ("decision", ["keep_kill_redesign_implement_decision"]),
        ("symbol_timeframe_session", ["symbol", "market_timeframe", "route_session"]),
    ]
    prepared: list[dict[str, Any]] = []
    for row in surface_rows:
        prepared.append({**row, "execution_row_family": "surface"})
    for row in member_rows:
        prepared.append({**row, "execution_row_family": "member"})
    for row in redesign_rows:
        prepared.append({**row, "execution_row_family": "redesign"})

    output: list[dict[str, Any]] = []
    for level, fields in specs:
        groups: dict[tuple[Any, ...], list[dict[str, Any]]] = defaultdict(list)
        for row in prepared:
            groups[tuple(row.get(field) for field in fields)].append(row)
        for key, rows in sorted(groups.items(), key=lambda item: tuple(normalized(part) for part in item[0])):
            output.append(
                boundary_row(
                    {
                        "unified_action_surface_execution_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-AGG-{len(output) + 1:06d}"
                        ),
                        "aggregate_level": level,
                        "aggregate_dimensions": {field: value for field, value in zip(fields, key)},
                        "row_count": len(rows),
                        "execution_pass_rows": sum(1 for row in rows if normalized(row.get("execution_status")).endswith("_PASS")),
                        "redesign_preserved_rows": sum(
                            1
                            for row in rows
                            if row.get("execution_status") == "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF"
                        ),
                        "issue_rows": len(issue_rows) if level == "portfolio" else 0,
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
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_AGGREGATE"
    if all(decision.startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def unified_action_surface_execution_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    surface_redesigns: list[dict[str, Any]],
    evidence_actions: list[dict[str, Any]],
    decision_actions: list[dict[str, Any]],
    terminal_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    all_actions = evidence_actions + decision_actions + terminal_actions
    actions_by_id = {action_id(row): row for row in all_actions if action_id(row)}
    implementation_actions = [row for row in all_actions if is_implementation_action(row)]

    surfaces_out, surface_issues = surface_execution_rows(surfaces, members, implementation_actions)
    members_out, member_issues = member_execution_rows(members, surfaces, actions_by_id)
    redesigns_out, redesign_issues = redesign_execution_rows(surface_redesigns, actions_by_id)
    issues = surface_issues + member_issues + redesign_issues
    aggregates = aggregate_execution_rows(surfaces_out, members_out, redesigns_out, issues)
    return surfaces_out, members_out, redesigns_out, aggregates, issues


def system_unified_action_surface_execution_rows(
    surface_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    issue_rows: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-EXECUTION-SYSTEM-000001",
                "input_counts": input_counts,
                "surface_execution_rows": len(surface_rows),
                "member_execution_rows": len(member_rows),
                "redesign_execution_rows": len(redesign_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "surface_execution_pass_rows": sum(
                    1 for row in surface_rows if row.get("execution_status") == "ACTION_SURFACE_EXECUTION_PASS"
                ),
                "member_execution_pass_rows": sum(
                    1 for row in member_rows if row.get("execution_status") == "ACTION_SURFACE_MEMBER_EXECUTION_PASS"
                ),
                "redesign_execution_preserved_rows": sum(
                    1
                    for row in redesign_rows
                    if row.get("execution_status") == "REDESIGN_ACTION_EXECUTION_PRESERVED_WITH_NUMERIC_PROOF"
                ),
                "member_rows_with_simulated_r": sum(
                    1 for row in member_rows if first_missing_simulated_field(row) is None
                ),
                "redesign_rows_with_simulated_r": sum(
                    1 for row in redesign_rows if first_missing_simulated_field(row) is None
                ),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_SYSTEM"
                    if not issue_rows
                    else "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_EXECUTION_SYSTEM"
                ),
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
