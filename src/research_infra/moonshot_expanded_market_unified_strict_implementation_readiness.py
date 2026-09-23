"""Implementation-readiness rows for strict expanded-market action surfaces."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from src.research_infra.moonshot_expanded_market_unified_action_surface_execution import (
    GEOMETRY_FIELDS,
    as_int,
    first_missing_simulated_field,
    normalized,
    rounded,
    weighted_average,
)


EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_strict_implementation_readiness.py"
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
    output["expanded_market_unified_strict_implementation_readiness_surface"] = (
        EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def geometry_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    source = row or {}
    return {field: source.get(field) for field in GEOMETRY_FIELDS}


def strict_implementation_surface_rows(
    strict_surfaces: list[dict[str, Any]],
    strict_executions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    strict_by_id = {normalized(row.get("strict_action_surface_row_id")): row for row in strict_surfaces}
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, execution in enumerate(
        sorted(strict_executions, key=lambda item: normalized(item.get("strict_action_surface_execution_row_id"))),
        start=1,
    ):
        strict_surface = strict_by_id.get(normalized(execution.get("input_strict_action_surface_row_id"))) or {}
        ready = (
            execution.get("strict_execution_status") == "STRICT_ACTION_SURFACE_EXECUTION_PASS"
            and execution.get("average_cost_adjusted_simulated_r") is not None
            and execution.get("average_stress_simulated_r") is not None
        )
        row = boundary_row(
            {
                "strict_implementation_readiness_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-READY-{index:06d}"
                ),
                "input_strict_action_surface_row_id": execution.get("input_strict_action_surface_row_id"),
                "input_strict_action_surface_execution_row_id": execution.get(
                    "strict_action_surface_execution_row_id"
                ),
                "input_unified_action_surface_row_id": execution.get("input_unified_action_surface_row_id"),
                "strict_repair_mode": execution.get("strict_repair_mode"),
                "strict_action_surface_expression": strict_surface.get("strict_action_surface_expression"),
                "strict_action_surface_function_name": strict_surface.get("strict_action_surface_function_name"),
                "action_surface_family": execution.get("action_surface_family"),
                "symbol": execution.get("symbol"),
                "source_symbol": execution.get("source_symbol"),
                "market_timeframe": execution.get("market_timeframe"),
                "route_session": execution.get("route_session"),
                "horizon_id": execution.get("horizon_id"),
                "source_component": execution.get("source_component"),
                "selected_side": execution.get("selected_side"),
                "expected_member_action_rows": execution.get("expected_member_action_rows"),
                "strict_execution_match_rows": execution.get("strict_execution_match_rows"),
                "average_cost_adjusted_simulated_r": execution.get("average_cost_adjusted_simulated_r"),
                "average_stress_simulated_r": execution.get("average_stress_simulated_r"),
                "effective_n_sum": execution.get("effective_n_sum"),
                "target_first_count_sum": execution.get("target_first_count_sum"),
                "stop_first_count_sum": execution.get("stop_first_count_sum"),
                "neither_count_sum": execution.get("neither_count_sum"),
                "ambiguous_count_sum": execution.get("ambiguous_count_sum"),
                "implementation_readiness_status": (
                    "STRICT_IMPLEMENTATION_READY" if ready else "STRICT_IMPLEMENTATION_REDESIGN_REQUIRED"
                ),
                "missing_simulated_field": None if ready else "average_cost_adjusted_simulated_r_or_stress_simulated_r",
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_SURFACE"
                    if ready
                    else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_SURFACE"
                ),
                "follow_inverse_default_off_avoid_class": "follow" if ready else "redesign",
            }
        )
        output.append(row)
        if not ready:
            issues.append(
                boundary_row(
                    {
                        "strict_implementation_readiness_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_action_surface_execution_row_id": execution.get(
                            "strict_action_surface_execution_row_id"
                        ),
                        "readiness_issue_class": "strict_surface_missing_simulated_r_or_execution_pass",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_SURFACE"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def strict_implementation_member_rows(
    member_executions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, member in enumerate(
        sorted(member_executions, key=lambda item: normalized(item.get("strict_action_surface_member_execution_row_id"))),
        start=1,
    ):
        missing_simulated = first_missing_simulated_field(member)
        ready = (
            member.get("strict_member_execution_status") == "STRICT_ACTION_SURFACE_MEMBER_EXECUTION_PASS"
            and missing_simulated is None
        )
        row = {
            "strict_implementation_member_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-MEMBER-{index:08d}"
            ),
            "input_strict_action_surface_member_execution_row_id": member.get(
                "strict_action_surface_member_execution_row_id"
            ),
            "input_unified_implementation_action_row_id": member.get("input_unified_implementation_action_row_id"),
            "input_strict_action_surface_row_id": member.get("input_strict_action_surface_row_id"),
            "input_unified_action_surface_row_id": member.get("input_unified_action_surface_row_id"),
            "strict_repair_mode": member.get("strict_repair_mode"),
            "action_row_kind": member.get("action_row_kind"),
            "symbol": member.get("symbol"),
            "source_symbol": member.get("source_symbol"),
            "market_timeframe": member.get("market_timeframe"),
            "route_session": member.get("route_session"),
            "horizon_id": member.get("horizon_id"),
            "source_component": member.get("source_component"),
            "source_path": member.get("source_path"),
            "source_file_sha256": member.get("source_file_sha256"),
            "selected_side": member.get("selected_side"),
            "implementation_member_status": (
                "STRICT_IMPLEMENTATION_MEMBER_READY"
                if ready
                else "STRICT_IMPLEMENTATION_MEMBER_REDESIGN_REQUIRED"
            ),
            "missing_simulated_field": missing_simulated,
            "missing_geometry_field": member.get("missing_geometry_field"),
            "source_action_decision": member.get("source_action_decision"),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_MEMBER"
                if ready
                else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_MEMBER"
            ),
            "follow_inverse_default_off_avoid_class": member.get("follow_inverse_default_off_avoid_class", "follow"),
        }
        row.update(geometry_payload(member))
        output.append(boundary_row(row))
        if not ready:
            issues.append(
                boundary_row(
                    {
                        "strict_implementation_readiness_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_action_surface_member_execution_row_id": member.get(
                            "strict_action_surface_member_execution_row_id"
                        ),
                        "input_unified_implementation_action_row_id": member.get(
                            "input_unified_implementation_action_row_id"
                        ),
                        "readiness_issue_class": "strict_member_missing_simulated_r_or_execution_pass",
                        "missing_simulated_field": missing_simulated,
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_MEMBER"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def strict_implementation_redesign_rows(
    redesign_preservations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, redesign in enumerate(
        sorted(
            redesign_preservations,
            key=lambda item: normalized(item.get("strict_action_surface_redesign_preservation_row_id")),
        ),
        start=1,
    ):
        missing_simulated = first_missing_simulated_field(redesign)
        preserved = missing_simulated is None
        row = {
            "strict_implementation_redesign_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-REDESIGN-{index:06d}"
            ),
            "input_strict_action_surface_redesign_preservation_row_id": redesign.get(
                "strict_action_surface_redesign_preservation_row_id"
            ),
            "input_unified_implementation_action_row_id": redesign.get("input_unified_implementation_action_row_id"),
            "action_row_kind": redesign.get("action_row_kind"),
            "symbol": redesign.get("symbol"),
            "source_symbol": redesign.get("source_symbol"),
            "market_timeframe": redesign.get("market_timeframe"),
            "route_session": redesign.get("route_session"),
            "horizon_id": redesign.get("horizon_id"),
            "source_component": redesign.get("source_component"),
            "source_path": redesign.get("source_path"),
            "source_file_sha256": redesign.get("source_file_sha256"),
            "selected_side": redesign.get("selected_side"),
            "implementation_redesign_status": (
                "STRICT_IMPLEMENTATION_REDESIGN_EVIDENCE_PRESERVED"
                if preserved
                else "STRICT_IMPLEMENTATION_REDESIGN_REPLAY_FIELD_REQUIRED"
            ),
            "missing_simulated_field": missing_simulated,
            "missing_geometry_field": redesign.get("missing_geometry_field"),
            "source_action_decision": redesign.get("source_action_decision"),
            "keep_kill_redesign_implement_decision": redesign.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": redesign.get("follow_inverse_default_off_avoid_class", "redesign"),
        }
        row.update(geometry_payload(redesign))
        output.append(boundary_row(row))
        if not preserved:
            issues.append(
                boundary_row(
                    {
                        "strict_implementation_readiness_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_action_surface_redesign_preservation_row_id": redesign.get(
                            "strict_action_surface_redesign_preservation_row_id"
                        ),
                        "readiness_issue_class": "strict_redesign_missing_simulated_r",
                        "missing_simulated_field": missing_simulated,
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_REDRAW"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def aggregate_readiness_rows(
    surface_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for family, rows in [
        ("surface", surface_rows),
        ("member", member_rows),
        ("redesign", redesign_rows),
    ]:
        prepared.extend({**row, "readiness_row_family": family} for row in rows)
    specs = [
        ("portfolio", []),
        ("row_family", ["readiness_row_family"]),
        ("repair_mode", ["strict_repair_mode"]),
        ("action_kind", ["action_row_kind"]),
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
                        "strict_implementation_readiness_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-AGG-{len(output) + 1:06d}"
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
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_AGGREGATE"
    if all(decision.startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def unified_strict_implementation_readiness_rows(
    strict_surfaces: list[dict[str, Any]],
    strict_executions: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    redesign_preservations: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    surface_rows, surface_issues = strict_implementation_surface_rows(strict_surfaces, strict_executions)
    member_rows, member_issues = strict_implementation_member_rows(member_executions)
    redesign_rows, redesign_issues = strict_implementation_redesign_rows(redesign_preservations)
    issues = surface_issues + member_issues + redesign_issues
    aggregates = aggregate_readiness_rows(surface_rows, member_rows, redesign_rows, issues)
    return surface_rows, member_rows, redesign_rows, aggregates, issues


def system_unified_strict_implementation_readiness_rows(
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
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-IMPLEMENTATION-READINESS-SYSTEM-000001",
                "input_counts": input_counts,
                "strict_implementation_surface_rows": len(surface_rows),
                "strict_implementation_member_rows": len(member_rows),
                "strict_implementation_redesign_rows": len(redesign_rows),
                "aggregate_rows": len(aggregate_rows),
                "issue_rows": len(issue_rows),
                "implementation_ready_surface_rows": sum(
                    1
                    for row in surface_rows
                    if row.get("implementation_readiness_status") == "STRICT_IMPLEMENTATION_READY"
                ),
                "implementation_ready_member_rows": sum(
                    1
                    for row in member_rows
                    if row.get("implementation_member_status") == "STRICT_IMPLEMENTATION_MEMBER_READY"
                ),
                "redesign_evidence_preserved_rows": sum(
                    1
                    for row in redesign_rows
                    if row.get("implementation_redesign_status")
                    == "STRICT_IMPLEMENTATION_REDESIGN_EVIDENCE_PRESERVED"
                ),
                "member_rows_with_simulated_r": sum(
                    1 for row in member_rows if first_missing_simulated_field(row) is None
                ),
                "redesign_rows_with_simulated_r": sum(
                    1 for row in redesign_rows if first_missing_simulated_field(row) is None
                ),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_IMPLEMENTATION_READINESS_SYSTEM"
                ),
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
