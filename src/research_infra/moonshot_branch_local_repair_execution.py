"""Branch-local repair execution helpers for moonshot observable work orders.

The helpers are research-only. They consume module-materialized repair work
orders plus the prior scorer-execution rows and produce explicit same-resource
execution outcomes without touching live trading logic.
"""

from __future__ import annotations

from typing import Any


REPAIR_EXECUTION_SURFACE = "src/research_infra/moonshot_branch_local_repair_execution.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def proxy_score_class(score: Any) -> str:
    numeric = to_float(score)
    if numeric is None:
        return "PROXY_SCORE_MISSING"
    if numeric >= 0.5:
        return "PROXY_SCORE_HIGH"
    if numeric >= 0.25:
        return "PROXY_SCORE_MID"
    if numeric > 0:
        return "PROXY_SCORE_LOW"
    return "PROXY_SCORE_ZERO_OR_NEGATIVE"


def _base(module_row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_execution_surface": REPAIR_EXECUTION_SURFACE,
        "input_module_materialization_row_id": module_row.get("module_materialization_row_id"),
        "input_module_materialization_status": module_row.get("module_materialization_status"),
        "input_module_materialization_decision": module_row.get("module_materialization_decision"),
        "input_code_integration_candidate_row_id": module_row.get("input_code_integration_candidate_row_id"),
        "input_runtime_work_row_id": module_row.get("input_runtime_work_row_id"),
        "input_implementation_candidate_row_id": module_row.get("input_implementation_candidate_row_id"),
        "input_execution_bundle_row_id": module_row.get("input_execution_bundle_row_id"),
        "source_code_candidate_id": module_row.get("source_code_candidate_id"),
        "observable_scope_key": module_row.get("observable_scope_key"),
        "symbol": module_row.get("symbol"),
        "route_session": module_row.get("route_session"),
        "horizon_id": module_row.get("horizon_id"),
        "primitive_flag": module_row.get("primitive_flag"),
        "scope_symbol": module_row.get("scope_symbol"),
        "scope_session": module_row.get("scope_session"),
        "scope_horizon": module_row.get("scope_horizon"),
        "scope_primitive": module_row.get("scope_primitive"),
        "outside_gbpjpy_xauusd_current_branch_box": module_row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def exact_control_repair_execution(
    module_row: dict[str, Any],
    control_execution_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    control_execution_row = control_execution_row or {}
    exact_count = to_int(control_execution_row.get("exact_control_count"))
    same_symbol_session_count = to_int(control_execution_row.get("same_symbol_session_control_count"))
    same_symbol_count = to_int(control_execution_row.get("same_symbol_control_count"))
    selected_count = to_int(control_execution_row.get("selected_control_count"))
    proxy_quality = to_float(control_execution_row.get("control_scope_proxy_quality"))
    execution_score = to_float(control_execution_row.get("control_scope_execution_score"))
    proxy_score = None
    if execution_score is not None and proxy_quality is not None:
        proxy_score = round(execution_score * proxy_quality, 6)
    elif execution_score is not None:
        proxy_score = execution_score

    if exact_count >= 20:
        status = "REPAIR_EXECUTION_EXACT_CONTROL_REPAIRED_EXACT_N20"
        decision = "SCORE_WITH_EXACT_CONTROL_DENOMINATOR"
        can_score = True
        requirement_open = False
        cause = "exact same-scope control denominator reached n20 from current rows"
    elif same_symbol_session_count >= 20:
        status = "REPAIR_EXECUTION_EXACT_CONTROL_REPAIRED_SESSION_PROXY_N20"
        decision = "SCORE_WITH_SESSION_PROXY_CONTROL_GUARD"
        can_score = True
        requirement_open = True
        cause = "same-symbol/session proxy control denominator reached n20 but exact same-scope denominator remains open"
    elif same_symbol_count >= 20:
        status = "REPAIR_EXECUTION_EXACT_CONTROL_REPAIRED_SYMBOL_PROXY_N20"
        decision = "SCORE_WITH_SYMBOL_PROXY_CONTROL_GUARD"
        can_score = True
        requirement_open = True
        cause = "same-symbol proxy control denominator reached n20 but exact same-scope denominator remains open"
    elif selected_count >= 20:
        status = "REPAIR_EXECUTION_EXACT_CONTROL_GLOBAL_PROXY_ONLY_SCORE_WITHHELD"
        decision = "PRESERVE_GLOBAL_CONTROL_PROXY_AND_BUILD_EXACT_SCOPE"
        can_score = False
        requirement_open = True
        cause = "only global selected controls reached n20; same-symbol/session/exact controls are underpowered"
    else:
        status = "REPAIR_EXECUTION_EXACT_CONTROL_NO_CURRENT_CONTROL_DENOMINATOR"
        decision = "BUILD_EXACT_CONTROL_SCOPE_FROM_ADDITIONAL_CURRENT_OR_RECONSTRUCTED_ROWS"
        can_score = False
        requirement_open = True
        cause = "no current same-resource control denominator reached n20"

    return {
        **_base(module_row),
        "repair_execution_lane": "EXACT_CONTROL_REPAIR_EXECUTION",
        "repair_execution_status": status,
        "repair_execution_decision": decision,
        "repair_execution_result_class": proxy_score_class(proxy_score),
        "control_proxy_score_lower_bound": proxy_score,
        "control_scope_execution_score": execution_score,
        "control_scope_proxy_quality": proxy_quality,
        "exact_control_count": exact_count,
        "same_symbol_session_control_count": same_symbol_session_count,
        "same_symbol_control_count": same_symbol_count,
        "selected_control_count": selected_count,
        "selected_control_runtime_work_row_ids": control_execution_row.get("selected_control_runtime_work_row_ids") or [],
        "selected_control_input_candidate_ids": control_execution_row.get("selected_control_input_candidate_ids") or [],
        "selected_control_scope_keys": control_execution_row.get("selected_control_scope_keys") or [],
        "can_score_now": can_score,
        "exact_control_requirement_open": requirement_open,
        "exact_failure_or_success_cause": cause,
        "exact_build_source_requirement": module_row.get("exact_build_source_requirement"),
        "source_repair_required": False,
        "control_required": True,
        "work_order_executed_from_available_rows": True,
    }


def source_repair_work_execution(
    module_row: dict[str, Any],
    source_execution_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_execution_row = source_execution_row or {}
    family = str(module_row.get("repair_family") or "")
    source_proxy_score = to_float(source_execution_row.get("source_proxy_score"))
    horizon_proxy_score = to_float(source_execution_row.get("horizon_proxy_score"))
    current_source_n = to_int(source_execution_row.get("current_source_flagged_n"))
    current_targetable_n = to_int(source_execution_row.get("current_targetable_flagged_n"))
    current_failclosed_n = to_int(source_execution_row.get("current_failclosed_flagged_n"))
    targetable_ratio = round(current_targetable_n / current_source_n, 6) if current_source_n else None
    failclosed_ratio = round(current_failclosed_n / current_source_n, 6) if current_source_n else None
    proxy_delta = None
    if source_proxy_score is not None and horizon_proxy_score is not None:
        proxy_delta = round(source_proxy_score - horizon_proxy_score, 6)

    if family == "EXACT_SOURCE_REPAIR":
        status = "REPAIR_EXECUTION_EXACT_SOURCE_PROXY_REGISTERED_EXACT_SOURCE_REQUIRED"
        decision = "PRESERVE_PROXY_SCORE_WITH_EXACT_SOURCE_REPAIR_REQUIRED"
        can_score = False
        requirement_open = True
        cause = (
            source_execution_row.get("exact_missing_geometry_or_source_reason")
            or "exact source rows are required before scalar interpretation"
        )
    elif family == "HORIZON_REBUILD_KILL_CHECK":
        status = "REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK_PROXY_SCORED"
        decision = "REBUILD_HORIZON_AND_KILL_IF_NEGATIVE_PERSISTS"
        can_score = False
        requirement_open = True
        cause = (
            source_execution_row.get("exact_missing_geometry_or_source_reason")
            or "horizon targetability must be rebuilt before kill decision is final"
        )
    elif family == "HORIZON_REBUILD_RESCORE":
        status = "REPAIR_EXECUTION_HORIZON_REBUILD_RESCORE_PROXY_SCORED"
        decision = "REBUILD_HORIZON_AND_RESCORE_WITH_FAILCLOSED_PROXY_CONTEXT"
        can_score = False
        requirement_open = True
        cause = (
            source_execution_row.get("exact_missing_geometry_or_source_reason")
            or "horizon targetability must be rebuilt before scalar score is final"
        )
    else:
        status = "REPAIR_EXECUTION_SOURCE_REPAIR_CONTEXT_ONLY"
        decision = "PRESERVE_SOURCE_REPAIR_CONTEXT"
        can_score = False
        requirement_open = False
        cause = "source repair row did not match an executable repair family"

    return {
        **_base(module_row),
        "repair_execution_lane": "SOURCE_REPAIR_WORK_EXECUTION",
        "repair_execution_status": status,
        "repair_execution_decision": decision,
        "repair_execution_result_class": proxy_score_class(source_proxy_score),
        "source_repair_family": family,
        "source_proxy_score": source_proxy_score,
        "horizon_proxy_score": horizon_proxy_score,
        "source_minus_horizon_proxy_delta": proxy_delta,
        "current_source_flagged_n": current_source_n if current_source_n else None,
        "current_targetable_flagged_n": current_targetable_n if current_source_n else None,
        "current_failclosed_flagged_n": current_failclosed_n if current_source_n else None,
        "current_targetable_ratio": targetable_ratio,
        "current_failclosed_ratio": failclosed_ratio,
        "duplicate_repair_scope_count": to_int(source_execution_row.get("duplicate_repair_scope_count")),
        "fail_if_negative_persists": bool(module_row.get("fail_if_negative_persists") or source_execution_row.get("fail_if_negative_persists")),
        "can_score_now": can_score,
        "source_repair_requirement_open": requirement_open,
        "exact_failure_or_success_cause": cause,
        "source_repair_required": True,
        "control_required": False,
        "work_order_executed_from_available_rows": True,
    }


def horizon_sidecar_repair_execution(
    module_row: dict[str, Any],
    linked_source_repair_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    linked_source_repair_rows = linked_source_repair_rows or []
    linked_statuses = sorted(
        {
            str(row.get("repair_execution_status"))
            for row in linked_source_repair_rows
            if row.get("repair_execution_status")
        }
    )
    linked_scores = [
        to_float(row.get("source_proxy_score"))
        for row in linked_source_repair_rows
        if to_float(row.get("source_proxy_score")) is not None
    ]
    linked_score = round(sum(linked_scores) / len(linked_scores), 6) if linked_scores else None
    if linked_source_repair_rows:
        status = "REPAIR_EXECUTION_HORIZON_SIDECAR_LINKED_TO_SOURCE_REPAIR_SCOPE"
        decision = "PRESERVE_HORIZON_SIDECAR_WITH_LINKED_SOURCE_REPAIR_EXECUTION"
        cause = "horizon sidecar scope has matching source-repair execution rows"
    else:
        status = "REPAIR_EXECUTION_HORIZON_SIDECAR_SCOPE_ONLY"
        decision = "PRESERVE_HORIZON_SIDECAR_SCOPE_REQUIREMENT"
        cause = "horizon sidecar scope has no matching source-repair execution row in current bundle"

    return {
        **_base(module_row),
        "repair_execution_lane": "HORIZON_REPAIR_SIDECAR_EXECUTION",
        "repair_execution_status": status,
        "repair_execution_decision": decision,
        "repair_execution_result_class": proxy_score_class(linked_score),
        "linked_source_repair_execution_count": len(linked_source_repair_rows),
        "linked_source_repair_execution_statuses": linked_statuses,
        "linked_source_proxy_score_mean": linked_score,
        "sidecar_only": True,
        "can_score_now": False,
        "source_repair_required": bool(module_row.get("source_repair_required")),
        "control_required": False,
        "exact_failure_or_success_cause": cause,
        "work_order_executed_from_available_rows": True,
    }


def coverage_carryforward_execution(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "repair_execution_surface": REPAIR_EXECUTION_SURFACE,
        "input_module_materialization_row_id": row.get("module_materialization_row_id"),
        "input_code_integration_candidate_row_id": row.get("input_code_integration_candidate_row_id"),
        "observable_scope_key": row.get("observable_scope_key"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "repair_execution_lane": "PRIMITIVE_COVERAGE_CARRYFORWARD",
        "repair_execution_status": str(row.get("module_materialization_status") or "COVERAGE_CONTEXT_ONLY").replace(
            "REGISTRY_MODULE_", "REPAIR_EXECUTION_"
        ),
        "repair_execution_decision": "PRESERVE_FOR_FULL_PRIMITIVE_COVERAGE_MAP",
        "sidecar_only": True,
        "can_score_now": False,
        "live_effect": False,
        "work_order_executed_from_available_rows": False,
    }
