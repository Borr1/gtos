"""Research-only implementation-candidate helpers for observable action results."""

from __future__ import annotations

from typing import Any


IMPLEMENTATION_CANDIDATE_SURFACE = "src/research_infra/moonshot_observable_implementation_candidates.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _priority(row: dict[str, Any], bonus: float = 0.0) -> float:
    base = (
        to_float(row.get("observable_proxy_score"))
        or to_float(row.get("source_proxy_score"))
        or to_float(row.get("control_proxy_score"))
        or to_float(row.get("guard_strength_score"))
        or to_float(row.get("horizon_proxy_score"))
        or to_float(row.get("input_execution_priority_score"))
        or 0.0
    )
    return clamp01(base + bonus)


def observable_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("action_result_status") or "")
    if status == "CONTROL_SCORE_RESULT_POSITIVE_DELTA":
        candidate_status = "OBSERVABLE_IMPL_ENABLE_CONTROLLED_CHALLENGER_SCORER"
        operation = "REGISTER_CONTROLLED_OBSERVABLE_SCORER"
        work = "enable_branch_local_shadow_scoring_with_matched_control_delta"
        ready = True
        control_required = False
        repair_required = False
        priority_bonus = 0.08
    elif status == "DENOMINATOR_RESULT_STRONG_SCOPE_GUARD_REGISTER":
        candidate_status = "OBSERVABLE_IMPL_REGISTER_DENOMINATOR_GUARDED_SHADOW"
        operation = "REGISTER_DENOMINATOR_GUARDED_OBSERVABLE"
        work = "register_observable_with_denominator_guard_enforced"
        ready = True
        control_required = False
        repair_required = False
        priority_bonus = 0.03
    elif status == "CONTROL_LOOKUP_RESULT_EXACT_SCOPE_REQUIRED":
        candidate_status = "OBSERVABLE_IMPL_BUILD_CONTROL_SCOPE_BEFORE_ENABLE"
        operation = "BUILD_EXACT_CONTROL_SCOPE"
        work = "materialize_or_match_exact_control_scope_before_scoring"
        ready = False
        control_required = True
        repair_required = False
        priority_bonus = 0.0
    else:
        candidate_status = "OBSERVABLE_IMPL_CONTEXT_ONLY"
        operation = "PRESERVE_OBSERVABLE_CONTEXT"
        work = "preserve_observable_action_context"
        ready = False
        control_required = False
        repair_required = False
        priority_bonus = 0.0
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "OBSERVABLE_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": candidate_status,
        "implementation_operation": operation,
        "implementation_work": work,
        "branch_local_ready": ready,
        "control_builder_required": control_required,
        "source_repair_required": repair_required,
        "implementation_priority_score": _priority(row, priority_bonus),
        "proxy_r_style_score_delta": row.get("proxy_r_style_score_delta"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "live_effect": False,
    }


def source_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("source_action_result_family") or "")
    if family == "SOURCE_ACTION_GUARDED_PROXY_SCOREABLE":
        status = "SOURCE_IMPL_GUARDED_PROXY_SCORER"
        operation = "REGISTER_GUARDED_SOURCE_PROXY_SCORER"
        work = "score_proxy_under_source_scope_guard"
        ready = True
        control_required = False
        repair_required = False
        bonus = 0.04
    elif family == "SOURCE_ACTION_AMBIGUOUS_PROXY_CONTROL_REQUIRED":
        status = "SOURCE_IMPL_AMBIGUOUS_PROXY_CONTROL_SCORER"
        operation = "REGISTER_AMBIGUOUS_SOURCE_PROXY_WITH_CONTROL"
        work = "score_ambiguous_proxy_only_with_control_guard"
        ready = True
        control_required = True
        repair_required = False
        bonus = 0.02
    elif family == "SOURCE_ACTION_EXACT_SOURCE_REPAIR":
        status = "SOURCE_IMPL_EXACT_SOURCE_REPAIR_WORK_ORDER"
        operation = "BUILD_EXACT_SOURCE_REPAIR"
        work = "rebuild_or_acquire_exact_source_before_enable"
        ready = False
        control_required = False
        repair_required = True
        bonus = 0.0
    elif family == "SOURCE_ACTION_HORIZON_REPAIR_KILL_CHECK":
        status = "SOURCE_IMPL_HORIZON_REPAIR_KILL_CHECK"
        operation = "BUILD_HORIZON_REPAIR_KILL_CHECK"
        work = "rebuild_horizon_and_kill_if_negative_persists"
        ready = False
        control_required = False
        repair_required = True
        bonus = 0.01
    elif family == "SOURCE_ACTION_HORIZON_REPAIR_RESCORE":
        status = "SOURCE_IMPL_HORIZON_REPAIR_RESCORE"
        operation = "BUILD_HORIZON_REPAIR_RESCORE"
        work = "rebuild_horizon_and_rescore_interval"
        ready = False
        control_required = False
        repair_required = True
        bonus = 0.01
    else:
        status = "SOURCE_IMPL_CONTEXT_ONLY"
        operation = "PRESERVE_SOURCE_CONTEXT"
        work = "preserve_source_action_context"
        ready = False
        control_required = False
        repair_required = False
        bonus = 0.0
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "SOURCE_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": status,
        "implementation_operation": operation,
        "implementation_work": work,
        "branch_local_ready": ready,
        "control_builder_required": control_required,
        "source_repair_required": repair_required,
        "implementation_priority_score": _priority(row, bonus),
        "proxy_r_style_score_delta": row.get("proxy_r_style_score_delta"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "live_effect": False,
    }


def control_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("action_result_status") or "")
    ready = status == "CONTROL_RESULT_COMPARATOR_READY"
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "CONTROL_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": "CONTROL_IMPL_COMPARATOR_READY" if ready else "CONTROL_IMPL_CONTEXT_ONLY",
        "implementation_operation": "BUILD_CONTROL_COMPARATOR" if ready else "PRESERVE_CONTROL_CONTEXT",
        "implementation_work": "materialize_control_comparator_for_observable_scope" if ready else "preserve_control_context",
        "branch_local_ready": ready,
        "control_builder_required": False,
        "source_repair_required": False,
        "implementation_priority_score": _priority(row),
        "live_effect": False,
    }


def denominator_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("action_result_status") or "")
    mapping = {
        "DENOMINATOR_ACTION_RESULT_OUTSIDE_BRANCH_SCOPE_ENFORCED": (
            "DENOMINATOR_IMPL_OUTSIDE_BRANCH_SCOPE_GUARD",
            "ENFORCE_OUTSIDE_BRANCH_SCOPE_DENOMINATOR",
        ),
        "DENOMINATOR_ACTION_RESULT_SOURCE_ROOT_COVERAGE_ENFORCED": (
            "DENOMINATOR_IMPL_SOURCE_ROOT_COVERAGE_GUARD",
            "ENFORCE_SOURCE_ROOT_COVERAGE_DENOMINATOR",
        ),
        "DENOMINATOR_ACTION_RESULT_MECHANISM_ARTIFACT_SPLIT_ENFORCED": (
            "DENOMINATOR_IMPL_MECHANISM_ARTIFACT_SPLIT_GUARD",
            "ENFORCE_MECHANISM_ARTIFACT_SPLIT",
        ),
    }
    candidate_status, operation = mapping.get(
        status,
        ("DENOMINATOR_IMPL_CONTEXT_COVERAGE_GUARD", "ENFORCE_CONTEXT_COVERAGE_DENOMINATOR"),
    )
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "DENOMINATOR_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": candidate_status,
        "implementation_operation": operation,
        "implementation_work": "enforce_denominator_guard_before_interpretation",
        "branch_local_ready": True,
        "control_builder_required": False,
        "source_repair_required": False,
        "implementation_priority_score": _priority(row),
        "live_effect": False,
    }


def horizon_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("action_result_status") or "")
    if status == "HORIZON_ACTION_RESULT_REBUILD_KILL_CHECK":
        candidate_status = "HORIZON_IMPL_REBUILD_KILL_CHECK"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_KILL_CHECK"
    elif status == "HORIZON_ACTION_RESULT_REBUILD_ALLOW_IF_POSITIVE":
        candidate_status = "HORIZON_IMPL_REBUILD_ALLOW_IF_POSITIVE"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_ALLOW_IF_POSITIVE"
    else:
        candidate_status = "HORIZON_IMPL_REBUILD_RESCORE"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_RESCORE"
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "HORIZON_REPAIR_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": candidate_status,
        "implementation_operation": operation,
        "implementation_work": "execute_horizon_repair_before_source_dependent_interpretation",
        "branch_local_ready": False,
        "control_builder_required": False,
        "source_repair_required": True,
        "implementation_priority_score": _priority(row, 0.02),
        "live_effect": False,
    }


def coverage_implementation_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("action_result_status") or "")
    mapping = {
        "COVERAGE_ACTION_RESULT_OBSERVABLE_CANDIDATE_ACTIVE": "COVERAGE_IMPL_OBSERVABLE_CANDIDATE_ACTIVE",
        "COVERAGE_ACTION_RESULT_SOURCE_POLICY_ACTIVE": "COVERAGE_IMPL_SOURCE_POLICY_ACTIVE",
        "COVERAGE_ACTION_RESULT_CONTROL_EXPERIMENT_ACTIVE": "COVERAGE_IMPL_CONTROL_EXPERIMENT_ACTIVE",
        "COVERAGE_ACTION_RESULT_DENOMINATOR_GUARD_ACTIVE": "COVERAGE_IMPL_DENOMINATOR_GUARD_ACTIVE",
        "COVERAGE_ACTION_RESULT_HORIZON_REPAIR_ACTIVE": "COVERAGE_IMPL_HORIZON_REPAIR_ACTIVE",
    }
    return {
        "implementation_candidate_surface": IMPLEMENTATION_CANDIDATE_SURFACE,
        "implementation_candidate_stage": "PRIMITIVE_COVERAGE_IMPLEMENTATION_CANDIDATE",
        "implementation_candidate_status": mapping.get(status, "COVERAGE_IMPL_CONTEXT_ONLY"),
        "implementation_operation": "PRESERVE_FULL_COVERAGE_IMPLEMENTATION_MAP",
        "implementation_work": "keep_full_coverage_status_attached_to_active_lane",
        "branch_local_ready": status != "COVERAGE_ACTION_RESULT_HORIZON_REPAIR_ACTIVE",
        "control_builder_required": status == "COVERAGE_ACTION_RESULT_CONTROL_EXPERIMENT_ACTIVE",
        "source_repair_required": status == "COVERAGE_ACTION_RESULT_HORIZON_REPAIR_ACTIVE",
        "implementation_priority_score": _priority(row),
        "live_effect": False,
    }
