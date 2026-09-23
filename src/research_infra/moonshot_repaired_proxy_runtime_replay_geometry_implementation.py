"""Materialize geometry repair decisions into branch-local implementation candidates."""

from __future__ import annotations

from collections import Counter
from typing import Any


RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION_SURFACE = (
    "src/research_infra/moonshot_repaired_proxy_runtime_replay_geometry_implementation.py"
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
    output["runtime_replay_geometry_implementation_surface"] = RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION_SURFACE
    output["research_boundary"] = research_boundary()
    return output


def normalized(value: Any) -> str:
    return "" if value is None else str(value)


def as_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def rounded(value: float | None, places: int = 9) -> float | None:
    return None if value is None else round(float(value), places)


def implementation_kind(row: dict[str, Any]) -> tuple[str, str]:
    decision = row.get("geometry_repair_decision")
    if decision == "IMPLEMENT_BRANCH_LOCAL_REPLAY_GEOMETRY_PROTOTYPE":
        return ("GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION", "IMPLEMENT_GEOMETRY_SCORER_PROTOTYPE_BRANCH_LOCAL")
    if decision == "CARRY_AS_AVOID_INTELLIGENCE_FROM_GEOMETRY":
        return ("GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION", "IMPLEMENT_GEOMETRY_AVOID_INTELLIGENCE_BRANCH_LOCAL")
    if decision == "KILL_AVOID_COMPARATOR_FROM_GEOMETRY":
        return ("GEOMETRY_AVOID_COMPARATOR_KILL_IMPLEMENTATION", "KILL_AVOID_COMPARATOR_BRANCH_LOCAL")
    if decision == "KILL_DEFAULT_OFF_FROM_GEOMETRY":
        return ("GEOMETRY_DEFAULT_OFF_KILL_IMPLEMENTATION", "KILL_DEFAULT_OFF_BRANCH_LOCAL")
    if decision == "CONCRETE_INTRABAR_PATH_REPLAY_REQUIRED":
        return ("GEOMETRY_INTRABAR_REPLAY_TASK_IMPLEMENTATION", "IMPLEMENT_INTRABAR_REPLAY_TASK_BRANCH_LOCAL")
    return ("GEOMETRY_REDESIGN_IMPLEMENTATION", "REDESIGN_GEOMETRY_BRANCH_LOCAL")


def payload_from_geometry_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "market_timeframe": row.get("market_timeframe"),
        "horizon_id": row.get("horizon_id"),
        "source_component": row.get("source_component"),
        "family": row.get("family"),
        "default_off_avoid_class": row.get("default_off_avoid_class"),
        "source_path": row.get("source_path"),
        "source_file_sha256": row.get("source_file_sha256"),
        "proxy_trade_direction": row.get("proxy_trade_direction"),
        "proxy_entry_price": row.get("proxy_entry_price"),
        "proxy_target_price": row.get("proxy_target_price"),
        "proxy_stop_price": row.get("proxy_stop_price"),
        "proxy_denominator_price": row.get("proxy_denominator_price"),
        "path_order_result": row.get("path_order_result"),
        "expected_action_adjusted_geometry_r": row.get("action_adjusted_geometry_r"),
        "expected_cost_adjusted_geometry_r": row.get("cost_adjusted_geometry_r"),
        "expected_geometry_result_class": row.get("geometry_result_class"),
        "remaining_missing_geometry_fields": row.get("remaining_missing_geometry_fields") or [],
    }


def evaluate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    path_order = payload.get("path_order_result")
    cls = payload.get("default_off_avoid_class")
    multiplier = -1.0 if cls == "avoid" else 1.0
    if path_order == "TARGET_FIRST_PROXY_PATH":
        underlying = 1.0
    elif path_order == "STOP_FIRST_PROXY_PATH":
        underlying = -1.0
    else:
        underlying = None
    action_r = underlying * multiplier if underlying is not None else None
    expected = as_float(payload.get("expected_action_adjusted_geometry_r"))
    status = (
        "GEOMETRY_IMPLEMENTATION_SELF_TEST_PASS"
        if action_r is not None and expected is not None and round(action_r, 9) == round(expected, 9)
        else "GEOMETRY_IMPLEMENTATION_SELF_TEST_NEEDS_REPAIR"
    )
    return {
        "evaluated_action_adjusted_geometry_r": rounded(action_r),
        "expected_action_adjusted_geometry_r": rounded(expected),
        "implementation_self_test_status": status,
    }


def geometry_implementation_rows(geometry_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in geometry_rows:
        kind, action = implementation_kind(row)
        payload = payload_from_geometry_row(row)
        test = evaluate_payload(payload)
        output.append(
            boundary_row(
                {
                    "geometry_implementation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-IMPL-ROW-{len(output) + 1:06d}"
                    ),
                    "input_geometry_repair_row_id": row.get("geometry_repair_row_id"),
                    "input_performance_row_id": row.get("input_performance_row_id"),
                    "implementation_kind": kind,
                    "implementation_action": action,
                    "branch_local_code_path": RUNTIME_REPLAY_GEOMETRY_IMPLEMENTATION_SURFACE,
                    "implementation_payload": payload,
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    "family": row.get("family"),
                    "default_off_avoid_class": row.get("default_off_avoid_class"),
                    "path_order_result": row.get("path_order_result"),
                    "cost_adjusted_geometry_r": row.get("cost_adjusted_geometry_r"),
                    "source_path": row.get("source_path"),
                    "source_file_sha256": row.get("source_file_sha256"),
                    "remaining_missing_geometry_field_count": row.get("remaining_missing_geometry_field_count"),
                    **test,
                }
            )
        )
    return output


def aggregate_implementation_rows(
    aggregate_geometry_rows: list[dict[str, Any]],
    implementation_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str, str, str, str], list[dict[str, Any]]] = {}
    for row in implementation_rows:
        key = (
            normalized(row.get("family")),
            normalized(row.get("symbol")),
            normalized(row.get("route_session")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("default_off_avoid_class")),
        )
        grouped.setdefault(key, []).append(row)
    aggregate_by_key = {
        (
            normalized(row.get("family")),
            normalized(row.get("symbol")),
            normalized(row.get("route_session")),
            normalized(row.get("market_timeframe")),
            normalized(row.get("horizon_id")),
            normalized(row.get("source_component")),
            normalized(row.get("default_off_avoid_class")),
        ): row
        for row in aggregate_geometry_rows
    }
    output: list[dict[str, Any]] = []
    for key in sorted(grouped):
        rows = grouped[key]
        aggregate = aggregate_by_key.get(key, {})
        kinds = Counter(row.get("implementation_kind") for row in rows)
        self_tests = Counter(row.get("implementation_self_test_status") for row in rows)
        output.append(
            boundary_row(
                {
                    "aggregate_implementation_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-IMPL-AGG-{len(output) + 1:05d}"
                    ),
                    "input_aggregate_geometry_row_id": aggregate.get("aggregate_geometry_row_id"),
                    "family": key[0],
                    "symbol": key[1],
                    "route_session": key[2],
                    "market_timeframe": key[3],
                    "horizon_id": key[4],
                    "source_component": key[5],
                    "default_off_avoid_class": key[6],
                    "row_count": len(rows),
                    "effective_n": aggregate.get("effective_n"),
                    "expectancy_cost_adjusted_geometry_r": aggregate.get("expectancy_cost_adjusted_geometry_r"),
                    "geometry_aggregate_decision": aggregate.get("geometry_keep_kill_redesign_implement_decision"),
                    "implementation_kind_counts": dict(sorted(kinds.items())),
                    "implementation_self_test_counts": dict(sorted(self_tests.items())),
                    "aggregate_implementation_action": aggregate_implementation_action(aggregate, kinds),
                }
            )
        )
    return output


def aggregate_implementation_action(aggregate: dict[str, Any], kinds: Counter) -> str:
    decision = aggregate.get("geometry_keep_kill_redesign_implement_decision")
    if decision in {"KILL_AVOID_COMPARATOR_FROM_GEOMETRY", "KILL_DEFAULT_OFF_FROM_GEOMETRY"}:
        return "APPLY_BRANCH_LOCAL_KILL_DECISION_TO_AGGREGATE"
    if decision in {"REDESIGN_AVOID_COMPARATOR_FROM_GEOMETRY", "REDESIGN_DEFAULT_OFF_FROM_GEOMETRY"}:
        return "OPEN_BRANCH_LOCAL_REDIRECTION_TASK_FOR_AGGREGATE"
    if kinds.get("GEOMETRY_SCORER_PROTOTYPE_IMPLEMENTATION"):
        return "ENABLE_BRANCH_LOCAL_GEOMETRY_SCORER_PROTOTYPE_AGGREGATE"
    if kinds.get("GEOMETRY_AVOID_INTELLIGENCE_IMPLEMENTATION"):
        return "ENABLE_BRANCH_LOCAL_AVOID_INTELLIGENCE_AGGREGATE"
    return "KEEP_BRANCH_LOCAL_IMPLEMENTATION_CONTEXT"


def implementation_self_test_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for row in rows:
        payload = row.get("implementation_payload") or {}
        test = evaluate_payload(payload)
        output.append(
            boundary_row(
                {
                    "implementation_self_test_row_id": (
                        f"OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-IMPL-TEST-{len(output) + 1:06d}"
                    ),
                    "input_geometry_implementation_row_id": row.get("geometry_implementation_row_id"),
                    "input_geometry_repair_row_id": row.get("input_geometry_repair_row_id"),
                    "implementation_kind": row.get("implementation_kind"),
                    "symbol": row.get("symbol"),
                    "route_session": row.get("route_session"),
                    "market_timeframe": row.get("market_timeframe"),
                    "horizon_id": row.get("horizon_id"),
                    "source_component": row.get("source_component"),
                    **test,
                }
            )
        )
    return output


def system_implementation_rows(
    implementation_rows: list[dict[str, Any]],
    aggregate_rows: list[dict[str, Any]],
    self_tests: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    kinds = Counter(row.get("implementation_kind") for row in implementation_rows)
    actions = Counter(row.get("implementation_action") for row in implementation_rows)
    tests = Counter(row.get("implementation_self_test_status") for row in self_tests)
    aggregate_actions = Counter(row.get("aggregate_implementation_action") for row in aggregate_rows)
    return [
        boundary_row(
            {
                "system_geometry_implementation_row_id": (
                    "OHLC-GTOS-REPAIRED-PROXY-RUNTIME-REPLAY-GEOM-IMPL-SYSTEM-00001"
                ),
                "geometry_implementation_rows": len(implementation_rows),
                "aggregate_implementation_rows": len(aggregate_rows),
                "implementation_self_test_rows": len(self_tests),
                "implementation_kind_counts": dict(sorted(kinds.items())),
                "implementation_action_counts": dict(sorted(actions.items())),
                "implementation_self_test_counts": dict(sorted(tests.items())),
                "aggregate_implementation_action_counts": dict(sorted(aggregate_actions.items())),
            }
        )
    ]
