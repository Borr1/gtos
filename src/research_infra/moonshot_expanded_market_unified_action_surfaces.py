"""Callable branch-local surfaces for expanded-market unified implementation actions."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any


EXPANDED_MARKET_UNIFIED_ACTION_SURFACES_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_action_surfaces.py"
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
    output["expanded_market_unified_action_surfaces_surface"] = (
        EXPANDED_MARKET_UNIFIED_ACTION_SURFACES_SURFACE
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


def sha_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def is_implementation_action(row: dict[str, Any]) -> bool:
    return normalized(row.get("keep_kill_redesign_implement_decision")).startswith("IMPLEMENT_")


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


def action_matches_surface(action: dict[str, Any], surface: dict[str, Any]) -> bool:
    return (
        action.get("branch_local_action_scope_sha256") == surface.get("action_surface_scope_sha256")
        and action.get("branch_local_action_expression_sha256") == surface.get("action_surface_expression_sha256")
        and is_implementation_action(action)
    )


def surface_row(scope_sha: str, members: list[dict[str, Any]], index: int) -> dict[str, Any]:
    first = members[0]
    expression = first.get("branch_local_action_expression")
    scope = first.get("branch_local_action_scope") or {}
    row = {
        "unified_action_surface_row_id": f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-{index:06d}",
        "action_surface_scope_sha256": scope_sha,
        "action_surface_expression_sha256": first.get("branch_local_action_expression_sha256"),
        "action_surface_expression": expression,
        "action_surface_scope": scope,
        "action_surface_function_name": f"expanded_market_unified_action_surface_{scope_sha[:12]}",
        "action_surface_family": first.get("branch_local_action_family"),
        "action_surface_status": "ACTION_SURFACE_READY",
        "member_action_rows": len(members),
        "symbol": first.get("symbol"),
        "source_symbol": first.get("source_symbol"),
        "market_timeframe": first.get("market_timeframe"),
        "route_session": first.get("route_session"),
        "horizon_id": first.get("horizon_id"),
        "source_component": first.get("source_component"),
        "source_path_count": len({member.get("source_path") for member in members if member.get("source_path")}),
        "source_hash_count": len({member.get("source_file_sha256") for member in members if member.get("source_file_sha256")}),
        "selected_side": first.get("selected_side"),
        "average_cost_adjusted_simulated_r": rounded(weighted_average(members, "cost_adjusted_simulated_r")),
        "average_stress_simulated_r": rounded(weighted_average(members, "stress_simulated_r")),
        "effective_n_sum": sum(as_int(member.get("effective_n")) for member in members),
        "target_first_count_sum": sum(as_int(member.get("target_first_count")) for member in members),
        "stop_first_count_sum": sum(as_int(member.get("stop_first_count")) for member in members),
        "ambiguous_count_sum": sum(as_int(member.get("ambiguous_count")) for member in members),
        "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE",
        "follow_inverse_default_off_avoid_class": "follow",
    }
    return boundary_row(row)


def unified_action_surface_rows(
    evidence_actions: list[dict[str, Any]],
    decision_actions: list[dict[str, Any]],
    redesign_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    implementation_actions = [row for row in evidence_actions + decision_actions if is_implementation_action(row)]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in implementation_actions:
        grouped[normalized(row.get("branch_local_action_scope_sha256"))].append(row)

    surfaces = [
        surface_row(scope_sha, sorted(members, key=lambda item: normalized(item.get("unified_implementation_action_row_id"))), index)
        for index, (scope_sha, members) in enumerate(sorted(grouped.items()), start=1)
    ]
    surface_by_scope = {surface["action_surface_scope_sha256"]: surface for surface in surfaces}
    member_rows: list[dict[str, Any]] = []
    for action in sorted(implementation_actions, key=lambda item: normalized(item.get("unified_implementation_action_row_id"))):
        surface = surface_by_scope.get(action.get("branch_local_action_scope_sha256"))
        member_rows.append(
            boundary_row(
                {
                    "unified_action_surface_member_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-MEMBER-{len(member_rows) + 1:08d}"
                    ),
                    "input_unified_action_surface_row_id": surface.get("unified_action_surface_row_id") if surface else None,
                    "input_unified_implementation_action_row_id": action.get("unified_implementation_action_row_id"),
                    "action_row_kind": action.get("action_row_kind"),
                    "symbol": action.get("symbol"),
                    "market_timeframe": action.get("market_timeframe"),
                    "route_session": action.get("route_session"),
                    "horizon_id": action.get("horizon_id"),
                    "source_component": action.get("source_component"),
                    "source_path": action.get("source_path"),
                    "source_file_sha256": action.get("source_file_sha256"),
                    "selected_side": action.get("selected_side"),
                    "cost_adjusted_simulated_r": action.get("cost_adjusted_simulated_r"),
                    "stress_simulated_r": action.get("stress_simulated_r"),
                    "effective_n": action.get("effective_n"),
                    "surface_member_match": bool(surface and action_matches_surface(action, surface)),
                    "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_MEMBER",
                    "follow_inverse_default_off_avoid_class": "follow",
                }
            )
        )

    self_tests = [
        boundary_row(
            {
                "unified_action_surface_self_test_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-SELF-TEST-{index:06d}"
                ),
                "input_unified_action_surface_row_id": surface.get("unified_action_surface_row_id"),
                "positive_scope_match": any(
                    action_matches_surface(action, surface)
                    for action in implementation_actions
                    if action.get("branch_local_action_scope_sha256") == surface.get("action_surface_scope_sha256")
                ),
                "negative_scope_mismatch_rejected": not action_matches_surface(
                    {
                        "branch_local_action_scope_sha256": "mismatch",
                        "branch_local_action_expression_sha256": surface.get("action_surface_expression_sha256"),
                        "keep_kill_redesign_implement_decision": "IMPLEMENT_TEST",
                    },
                    surface,
                ),
                "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_SELF_TEST",
                "follow_inverse_default_off_avoid_class": "follow",
            }
        )
        for index, surface in enumerate(surfaces, start=1)
    ]
    redesign_surface_rows = [
        boundary_row(
            {
                "unified_action_surface_redesign_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-REDESIGN-{index:06d}"
                ),
                "input_unified_redesign_action_row_id": row.get("unified_redesign_action_row_id"),
                "input_unified_implementation_action_row_id": row.get("input_unified_implementation_action_row_id"),
                "action_row_kind": row.get("action_row_kind"),
                "symbol": row.get("symbol"),
                "market_timeframe": row.get("market_timeframe"),
                "route_session": row.get("route_session"),
                "horizon_id": row.get("horizon_id"),
                "source_component": row.get("source_component"),
                "source_path": row.get("source_path"),
                "source_file_sha256": row.get("source_file_sha256"),
                "selected_side": row.get("selected_side"),
                "stress_blocking_reason": row.get("stress_blocking_reason"),
                "cost_adjusted_simulated_r": row.get("cost_adjusted_simulated_r"),
                "stress_simulated_r": row.get("stress_simulated_r"),
                "effective_n": row.get("effective_n"),
                "keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
                "follow_inverse_default_off_avoid_class": row.get("follow_inverse_default_off_avoid_class"),
            }
        )
        for index, row in enumerate(sorted(redesign_actions, key=lambda item: normalized(item.get("unified_redesign_action_row_id"))), start=1)
    ]
    aggregates = aggregate_surface_rows(surfaces, member_rows, redesign_surface_rows)
    return surfaces, member_rows, self_tests, redesign_surface_rows, aggregates


def aggregate_surface_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for label, rows in [
        ("surface_portfolio", surfaces),
        ("member_portfolio", members),
        ("redesign_portfolio", redesign_rows),
    ]:
        output.append(
            boundary_row(
                {
                    "unified_action_surface_aggregate_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-AGG-{len(output) + 1:06d}"
                    ),
                    "aggregate_level": label,
                    "row_count": len(rows),
                    "symbol_count": len({row.get("symbol") for row in rows if row.get("symbol")}),
                    "source_path_count": len({row.get("source_path") for row in rows if row.get("source_path")}),
                    "effective_n_sum": sum(as_int(row.get("effective_n") or row.get("effective_n_sum")) for row in rows),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_AGGREGATE"
                        if not label.startswith("redesign")
                        else "REDESIGN_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_AGGREGATE"
                    ),
                    "follow_inverse_default_off_avoid_class": "follow" if not label.startswith("redesign") else "redesign",
                }
            )
        )
    return output


def system_unified_action_surface_rows(
    surfaces: list[dict[str, Any]],
    members: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-ACTION-SURFACE-SYSTEM-000001",
                "input_counts": input_counts,
                "action_surface_rows": len(surfaces),
                "action_surface_member_rows": len(members),
                "action_surface_self_test_rows": len(self_tests),
                "action_surface_redesign_rows": len(redesign_rows),
                "aggregate_rows": len(aggregates),
                "surface_member_match_rows": sum(1 for row in members if row.get("surface_member_match")),
                "self_test_pass_rows": sum(
                    1
                    for row in self_tests
                    if row.get("positive_scope_match") is True and row.get("negative_scope_mismatch_rejected") is True
                ),
                "keep_kill_redesign_implement_decision": "IMPLEMENT_EXPANDED_MARKET_UNIFIED_ACTION_SURFACE_SYSTEM",
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
