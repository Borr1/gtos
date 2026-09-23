"""Branch-local artifact execution for strict expanded-market readiness rows."""

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


EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_expanded_market_unified_strict_artifact_execution.py"
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
    output["expanded_market_unified_strict_artifact_execution_surface"] = (
        EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION_SURFACE
    )
    output["research_boundary"] = research_boundary()
    return output


def geometry_payload(row: dict[str, Any] | None) -> dict[str, Any]:
    source = row or {}
    return {field: source.get(field) for field in GEOMETRY_FIELDS}


def artifact_matches_member(artifact: dict[str, Any], member: dict[str, Any]) -> bool:
    return (
        normalized(artifact.get("input_strict_action_surface_row_id"))
        == normalized(member.get("input_strict_action_surface_row_id"))
        and member.get("implementation_member_status") == "STRICT_IMPLEMENTATION_MEMBER_READY"
        and first_missing_simulated_field(member) is None
    )


def strict_artifact_rows(
    surface_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    members_by_surface: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for member in member_rows:
        members_by_surface[normalized(member.get("input_strict_action_surface_row_id"))].append(member)
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, surface in enumerate(
        sorted(surface_rows, key=lambda item: normalized(item.get("strict_implementation_readiness_row_id"))),
        start=1,
    ):
        surface_id = normalized(surface.get("input_strict_action_surface_row_id"))
        members = members_by_surface.get(surface_id, [])
        missing_simulated = [member for member in members if first_missing_simulated_field(member) is not None]
        ready = (
            surface.get("implementation_readiness_status") == "STRICT_IMPLEMENTATION_READY"
            and bool(members)
            and not missing_simulated
        )
        row = boundary_row(
            {
                "strict_implementation_artifact_row_id": (
                    f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-{index:06d}"
                ),
                "input_strict_implementation_readiness_row_id": surface.get(
                    "strict_implementation_readiness_row_id"
                ),
                "input_strict_action_surface_row_id": surface.get("input_strict_action_surface_row_id"),
                "input_unified_action_surface_row_id": surface.get("input_unified_action_surface_row_id"),
                "artifact_family": "expanded_market_unified_strict_surface",
                "artifact_function_name": surface.get("strict_action_surface_function_name"),
                "artifact_expression": surface.get("strict_action_surface_expression"),
                "strict_repair_mode": surface.get("strict_repair_mode"),
                "action_surface_family": surface.get("action_surface_family"),
                "symbol": surface.get("symbol"),
                "source_symbol": surface.get("source_symbol"),
                "market_timeframe": surface.get("market_timeframe"),
                "route_session": surface.get("route_session"),
                "horizon_id": surface.get("horizon_id"),
                "source_component": surface.get("source_component"),
                "selected_side": surface.get("selected_side"),
                "artifact_member_rows": len(members),
                "source_path_count": len({member.get("source_path") for member in members if member.get("source_path")}),
                "source_hash_count": len(
                    {member.get("source_file_sha256") for member in members if member.get("source_file_sha256")}
                ),
                "missing_geometry_member_rows": sum(
                    1 for member in members if member.get("missing_geometry_field")
                ),
                "missing_simulated_member_rows": len(missing_simulated),
                "average_cost_adjusted_simulated_r": surface.get("average_cost_adjusted_simulated_r"),
                "average_stress_simulated_r": surface.get("average_stress_simulated_r"),
                "effective_n_sum": surface.get("effective_n_sum"),
                "target_first_count_sum": surface.get("target_first_count_sum"),
                "stop_first_count_sum": surface.get("stop_first_count_sum"),
                "neither_count_sum": surface.get("neither_count_sum"),
                "ambiguous_count_sum": surface.get("ambiguous_count_sum"),
                "artifact_execution_status": (
                    "STRICT_IMPLEMENTATION_ARTIFACT_READY"
                    if ready
                    else "STRICT_IMPLEMENTATION_ARTIFACT_REDESIGN_REQUIRED"
                ),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT"
                    if ready
                    else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT"
                ),
                "follow_inverse_default_off_avoid_class": "follow" if ready else "redesign",
            }
        )
        output.append(row)
        if not ready:
            issues.append(
                boundary_row(
                    {
                        "strict_artifact_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_implementation_readiness_row_id": surface.get(
                            "strict_implementation_readiness_row_id"
                        ),
                        "input_strict_action_surface_row_id": surface.get("input_strict_action_surface_row_id"),
                        "artifact_issue_class": "strict_artifact_missing_members_or_simulated_r",
                        "artifact_member_rows": len(members),
                        "missing_simulated_member_rows": len(missing_simulated),
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def artifact_member_execution_rows(
    artifacts: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    artifact_by_surface = {
        normalized(row.get("input_strict_action_surface_row_id")): row for row in artifacts
    }
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, member in enumerate(
        sorted(member_rows, key=lambda item: normalized(item.get("strict_implementation_member_row_id"))),
        start=1,
    ):
        artifact = artifact_by_surface.get(normalized(member.get("input_strict_action_surface_row_id")))
        matched = bool(artifact) and artifact_matches_member(artifact, member)
        row = {
            "strict_artifact_member_execution_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-MEMBER-{index:08d}"
            ),
            "input_strict_implementation_artifact_row_id": (
                artifact.get("strict_implementation_artifact_row_id") if artifact else None
            ),
            "input_strict_implementation_member_row_id": member.get("strict_implementation_member_row_id"),
            "input_strict_action_surface_row_id": member.get("input_strict_action_surface_row_id"),
            "input_unified_implementation_action_row_id": member.get("input_unified_implementation_action_row_id"),
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
            "artifact_member_match": matched,
            "artifact_member_execution_status": (
                "STRICT_ARTIFACT_MEMBER_EXECUTION_PASS"
                if matched
                else "STRICT_ARTIFACT_MEMBER_EXECUTION_REDESIGN_REQUIRED"
            ),
            "missing_simulated_field": member.get("missing_simulated_field"),
            "missing_geometry_field": member.get("missing_geometry_field"),
            "source_action_decision": member.get("source_action_decision"),
            "keep_kill_redesign_implement_decision": (
                "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_MEMBER_EXECUTION"
                if matched
                else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_MEMBER_EXECUTION"
            ),
            "follow_inverse_default_off_avoid_class": member.get("follow_inverse_default_off_avoid_class", "follow"),
        }
        row.update(geometry_payload(member))
        output.append(boundary_row(row))
        if not matched:
            issues.append(
                boundary_row(
                    {
                        "strict_artifact_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_implementation_member_row_id": member.get(
                            "strict_implementation_member_row_id"
                        ),
                        "artifact_issue_class": "strict_artifact_member_execution_mismatch",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_MEMBER_EXECUTION"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def artifact_control_rows(
    artifacts: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    first_member_by_surface: dict[str, dict[str, Any]] = {}
    for member in member_rows:
        first_member_by_surface.setdefault(normalized(member.get("input_strict_action_surface_row_id")), member)
    output: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for index, artifact in enumerate(
        sorted(artifacts, key=lambda item: normalized(item.get("strict_implementation_artifact_row_id"))),
        start=1,
    ):
        member = dict(first_member_by_surface.get(normalized(artifact.get("input_strict_action_surface_row_id")), {}))
        positive_match = bool(member) and artifact_matches_member(artifact, member)
        member["input_strict_action_surface_row_id"] = "mismatch"
        negative_rejected = not artifact_matches_member(artifact, member)
        passed = positive_match and negative_rejected
        output.append(
            boundary_row(
                {
                    "strict_artifact_control_row_id": (
                        f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-CONTROL-{index:06d}"
                    ),
                    "input_strict_implementation_artifact_row_id": artifact.get(
                        "strict_implementation_artifact_row_id"
                    ),
                    "input_strict_action_surface_row_id": artifact.get("input_strict_action_surface_row_id"),
                    "positive_member_match": positive_match,
                    "negative_surface_mismatch_rejected": negative_rejected,
                    "artifact_control_status": (
                        "STRICT_ARTIFACT_CONTROL_PASS"
                        if passed
                        else "STRICT_ARTIFACT_CONTROL_REDESIGN_REQUIRED"
                    ),
                    "keep_kill_redesign_implement_decision": (
                        "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_CONTROL"
                        if passed
                        else "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_CONTROL"
                    ),
                    "follow_inverse_default_off_avoid_class": "follow" if passed else "redesign",
                }
            )
        )
        if not passed:
            issues.append(
                boundary_row(
                    {
                        "strict_artifact_execution_issue_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-ISSUE-{len(issues) + 1:06d}"
                        ),
                        "input_strict_implementation_artifact_row_id": artifact.get(
                            "strict_implementation_artifact_row_id"
                        ),
                        "artifact_issue_class": "strict_artifact_control_failure",
                        "keep_kill_redesign_implement_decision": (
                            "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_CONTROL"
                        ),
                        "follow_inverse_default_off_avoid_class": "redesign",
                    }
                )
            )
    return output, issues


def artifact_redesign_rows(redesign_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, redesign in enumerate(
        sorted(redesign_rows, key=lambda item: normalized(item.get("strict_implementation_redesign_row_id"))),
        start=1,
    ):
        row = {
            "strict_artifact_redesign_row_id": (
                f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-REDESIGN-{index:06d}"
            ),
            "input_strict_implementation_redesign_row_id": redesign.get("strict_implementation_redesign_row_id"),
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
            "artifact_redesign_status": "STRICT_ARTIFACT_REDESIGN_EVIDENCE_PRESERVED",
            "missing_simulated_field": redesign.get("missing_simulated_field"),
            "missing_geometry_field": redesign.get("missing_geometry_field"),
            "source_action_decision": redesign.get("source_action_decision"),
            "keep_kill_redesign_implement_decision": redesign.get("keep_kill_redesign_implement_decision"),
            "follow_inverse_default_off_avoid_class": redesign.get("follow_inverse_default_off_avoid_class", "redesign"),
        }
        row.update(geometry_payload(redesign))
        output.append(boundary_row(row))
    return output


def aggregate_artifact_rows(
    artifacts: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    redesigns: list[dict[str, Any]],
    issues: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prepared: list[dict[str, Any]] = []
    for family, rows in [
        ("artifact", artifacts),
        ("member_execution", member_executions),
        ("control", controls),
        ("redesign", redesigns),
    ]:
        prepared.extend({**row, "artifact_row_family": family} for row in rows)
    specs = [
        ("portfolio", []),
        ("row_family", ["artifact_row_family"]),
        ("artifact_status", ["artifact_execution_status"]),
        ("member_status", ["artifact_member_execution_status"]),
        ("control_status", ["artifact_control_status"]),
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
                        "strict_artifact_execution_aggregate_row_id": (
                            f"OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-AGG-{len(output) + 1:06d}"
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
        return "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_AGGREGATE"
    if all(decision.startswith("REDESIGN_") for decision in decisions):
        return "REDESIGN_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_AGGREGATE"
    return "CARRY_AS_AVOID_INTELLIGENCE_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_AGGREGATE"


def aggregate_class(rows: list[dict[str, Any]]) -> str:
    classes = {normalized(row.get("follow_inverse_default_off_avoid_class")) for row in rows}
    classes.discard("")
    return next(iter(classes)) if len(classes) == 1 else "mixed"


def unified_strict_artifact_execution_rows(
    surface_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
    redesign_rows: list[dict[str, Any]],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    artifacts, artifact_issues = strict_artifact_rows(surface_rows, member_rows)
    member_executions, member_issues = artifact_member_execution_rows(artifacts, member_rows)
    controls, control_issues = artifact_control_rows(artifacts, member_rows)
    redesigns = artifact_redesign_rows(redesign_rows)
    issues = artifact_issues + member_issues + control_issues
    aggregates = aggregate_artifact_rows(artifacts, member_executions, controls, redesigns, issues)
    return artifacts, member_executions, controls, redesigns, aggregates, issues


def system_unified_strict_artifact_execution_rows(
    artifacts: list[dict[str, Any]],
    member_executions: list[dict[str, Any]],
    controls: list[dict[str, Any]],
    redesigns: list[dict[str, Any]],
    aggregates: list[dict[str, Any]],
    issues: list[dict[str, Any]],
    input_counts: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        boundary_row(
            {
                "system_row_id": "OHLC-GTOS-EXPANDED-MARKET-UNIFIED-STRICT-ARTIFACT-EXECUTION-SYSTEM-000001",
                "input_counts": input_counts,
                "strict_artifact_rows": len(artifacts),
                "strict_artifact_member_execution_rows": len(member_executions),
                "strict_artifact_control_rows": len(controls),
                "strict_artifact_redesign_rows": len(redesigns),
                "aggregate_rows": len(aggregates),
                "issue_rows": len(issues),
                "artifact_ready_rows": sum(
                    1
                    for row in artifacts
                    if row.get("artifact_execution_status") == "STRICT_IMPLEMENTATION_ARTIFACT_READY"
                ),
                "artifact_member_execution_pass_rows": sum(
                    1
                    for row in member_executions
                    if row.get("artifact_member_execution_status") == "STRICT_ARTIFACT_MEMBER_EXECUTION_PASS"
                ),
                "artifact_control_pass_rows": sum(
                    1 for row in controls if row.get("artifact_control_status") == "STRICT_ARTIFACT_CONTROL_PASS"
                ),
                "artifact_redesign_preserved_rows": sum(
                    1
                    for row in redesigns
                    if row.get("artifact_redesign_status") == "STRICT_ARTIFACT_REDESIGN_EVIDENCE_PRESERVED"
                ),
                "member_rows_with_simulated_r": sum(
                    1 for row in member_executions if first_missing_simulated_field(row) is None
                ),
                "redesign_rows_with_simulated_r": sum(
                    1 for row in redesigns if first_missing_simulated_field(row) is None
                ),
                "keep_kill_redesign_implement_decision": (
                    "IMPLEMENT_EXPANDED_MARKET_UNIFIED_STRICT_ARTIFACT_EXECUTION_SYSTEM"
                ),
                "follow_inverse_default_off_avoid_class": "mixed",
            }
        )
    ]
