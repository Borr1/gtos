"""Research-only implementation synthesis helpers for observable scorer execution rows."""

from __future__ import annotations

from typing import Any


IMPLEMENTATION_SYNTHESIS_SURFACE = "src/research_infra/moonshot_observable_implementation_synthesis.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _score_band(value: float | None) -> str:
    if value is None:
        return "SYNTHESIS_SCORE_NO_SCALAR"
    if value >= 0.75:
        return "SYNTHESIS_SCORE_HIGH"
    if value >= 0.5:
        return "SYNTHESIS_SCORE_MEDIUM"
    if value >= 0.25:
        return "SYNTHESIS_SCORE_LOW"
    return "SYNTHESIS_SCORE_WEAK"


def _first_float(row: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = to_float(row.get(key))
        if value is not None:
            return value
    return None


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "implementation_synthesis_surface": IMPLEMENTATION_SYNTHESIS_SURFACE,
        "proxy_r_style_score_delta": to_float(row.get("proxy_r_style_score_delta")),
        "expectancy_style_proxy_delta": to_float(row.get("expectancy_style_proxy_delta")),
        "source_repair_required": bool(row.get("source_repair_required") or row.get("runtime_source_repair_required")),
        "control_required": bool(row.get("control_required") or row.get("runtime_control_required")),
        "branch_local_ready": bool(row.get("executable_now")),
        "live_effect": False,
    }


def scorer_registration_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("execution_status") or "")
    if status == "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA":
        synthesis_status = "SCORER_REGISTRATION_CONTROLLED_CHALLENGER_REGISTER"
        decision = "IMPLEMENT_BRANCH_LOCAL_CONTROLLED_OBSERVABLE_SCORER"
        action = "register_controlled_observable_scorer_with_proxy_delta_and_exact_control_context"
        keep_kill = "IMPLEMENT"
        control_required = False
        success_cause = "positive proxy delta exists against matched control rows"
        score = _first_float(row, ["scorer_proxy_score", "observable_proxy_score"])
    elif status == "SOURCE_SCORER_EXECUTION_GUARDED_PROXY_SCORE":
        synthesis_status = "SCORER_REGISTRATION_SOURCE_GUARDED_PROXY_REGISTER"
        decision = "IMPLEMENT_GUARDED_SOURCE_PROXY_SCORER"
        action = "register_source_proxy_scorer_with_source_guard"
        keep_kill = "IMPLEMENT"
        control_required = False
        success_cause = "source proxy is scoreable under source guard"
        score = _first_float(row, ["source_scorer_proxy_score", "source_proxy_score"])
    elif status == "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE":
        synthesis_status = "SCORER_REGISTRATION_SOURCE_AMBIGUOUS_CONTROL_GUARD_REGISTER"
        decision = "IMPLEMENT_SOURCE_PROXY_SCORER_ONLY_WITH_AMBIGUITY_CONTROL"
        action = "register_source_proxy_scorer_with_mandatory_ambiguity_control_guard"
        keep_kill = "IMPLEMENT_WITH_CONTROL_GUARD"
        control_required = True
        success_cause = "source proxy has scalar signal but ambiguity requires control guard before interpretation"
        score = _first_float(row, ["source_scorer_proxy_score", "source_proxy_score"])
    else:
        synthesis_status = "SCORER_REGISTRATION_CONTEXT_ONLY"
        decision = "PRESERVE_SCORER_CONTEXT"
        action = "preserve_unexpected_scorer_execution_context"
        keep_kill = "PRESERVE_CONTEXT"
        control_required = bool(row.get("control_required") or row.get("runtime_control_required"))
        success_cause = "no implementation registration status matched"
        score = None
    return {
        **_base(row),
        "implementation_synthesis_stage": "SCORER_REGISTRATION_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": action,
        "keep_kill_redesign_implement_decision": keep_kill,
        "implementation_success_cause": success_cause,
        "control_required": control_required,
        "control_match_count": int(row.get("control_match_count") or 0),
        "source_scorer_execution_status": row.get("source_scorer_execution_status"),
        "scorer_registration_score": score,
        "scorer_registration_score_band": _score_band(score),
        "branch_local_ready": status in {
            "SCORER_EXECUTION_CONTROLLED_POSITIVE_DELTA",
            "SOURCE_SCORER_EXECUTION_GUARDED_PROXY_SCORE",
            "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE",
        },
        "standalone_interpretation_allowed": status != "SOURCE_SCORER_EXECUTION_AMBIGUOUS_PROXY_CONTROL_SCORE",
    }


def observable_registry_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("execution_status") or "")
    score = _first_float(row, ["scorer_proxy_score", "guard_strength_score"])
    if status == "SCORER_EXECUTION_DENOMINATOR_GUARDED_OBSERVABLE_STRONG":
        synthesis_status = "OBSERVABLE_REGISTRY_DENOMINATOR_GUARDED_REGISTER"
        decision = "IMPLEMENT_DENOMINATOR_GUARDED_OBSERVABLE_REGISTRATION"
        keep_kill = "IMPLEMENT_WITH_DENOMINATOR_GUARD"
        cause = "observable is registerable only with explicit denominator guard strength"
    else:
        synthesis_status = "OBSERVABLE_REGISTRY_CONTEXT_ONLY"
        decision = "PRESERVE_OBSERVABLE_REGISTRY_CONTEXT"
        keep_kill = "PRESERVE_CONTEXT"
        cause = "observable registry row did not carry strong denominator guard status"
    return {
        **_base(row),
        "implementation_synthesis_stage": "OBSERVABLE_REGISTRY_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": "register_observable_with_denominator_guard" if "REGISTER" in synthesis_status else "preserve_observable_context",
        "keep_kill_redesign_implement_decision": keep_kill,
        "implementation_success_cause": cause,
        "guard_strength_score": to_float(row.get("guard_strength_score")),
        "denominator_guard_match_count": int(row.get("denominator_guard_match_count") or 0),
        "observable_registry_score": score,
        "observable_registry_score_band": _score_band(score),
        "branch_local_ready": status == "SCORER_EXECUTION_DENOMINATOR_GUARDED_OBSERVABLE_STRONG",
    }


def control_scope_implementation_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("control_scope_execution_status") or row.get("execution_status") or "")
    score = to_float(row.get("control_scope_execution_score"))
    if status == "CONTROL_SCOPE_EXECUTION_PROXY_SAME_SYMBOL_SESSION":
        synthesis_status = "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_SESSION_GUARD"
        decision = "IMPLEMENT_SESSION_MATCHED_PROXY_CONTROL_GUARD"
        keep_kill = "IMPLEMENT_PROXY_CONTROL_GUARD"
        action = "register_session_matched_proxy_control_guard"
        cause = "same-symbol/session proxy control rows meet N20 proxy threshold"
        ready = True
    elif status == "CONTROL_SCOPE_EXECUTION_PROXY_SAME_SYMBOL":
        synthesis_status = "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_GUARD"
        decision = "IMPLEMENT_SYMBOL_MATCHED_PROXY_CONTROL_GUARD"
        keep_kill = "IMPLEMENT_PROXY_CONTROL_GUARD"
        action = "register_symbol_matched_proxy_control_guard"
        cause = "same-symbol proxy control rows meet N20 proxy threshold"
        ready = True
    elif status == "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED":
        synthesis_status = "CONTROL_SCOPE_IMPLEMENT_EXACT_CONTROL_BUILD_REQUIRED"
        decision = "BUILD_EXACT_OR_BETTER_PROXY_CONTROL_BEFORE_SCALAR_SCORE"
        keep_kill = "BUILD_CONTROL"
        action = "build_exact_control_scope_from_current_or_reconstructed_rows"
        cause = "only underpowered global proxy controls are available; scalar score is withheld"
        ready = False
    else:
        synthesis_status = "CONTROL_SCOPE_IMPLEMENT_CONTEXT_ONLY"
        decision = "PRESERVE_CONTROL_SCOPE_CONTEXT"
        keep_kill = "PRESERVE_CONTEXT"
        action = "preserve_control_scope_context"
        cause = "control scope status not executable"
        ready = False
    return {
        **_base(row),
        "implementation_synthesis_stage": "CONTROL_SCOPE_IMPLEMENTATION_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": action,
        "keep_kill_redesign_implement_decision": keep_kill,
        "implementation_success_cause": cause,
        "control_scope_proxy_quality": to_float(row.get("control_scope_proxy_quality")),
        "control_scope_execution_score": score,
        "control_scope_score_band": _score_band(score),
        "selected_control_count": int(row.get("selected_control_count") or 0),
        "selected_control_candidate_ids": row.get("selected_control_candidate_ids") or [],
        "selected_control_runtime_work_row_ids": row.get("selected_control_runtime_work_row_ids") or [],
        "selected_control_input_candidate_ids": row.get("selected_control_input_candidate_ids") or [],
        "desired_control_family": row.get("desired_control_family"),
        "missing_control_scope_key": row.get("missing_control_scope_key"),
        "exact_control_build_required": status == "CONTROL_SCOPE_EXECUTION_EXACT_CONTROL_BUILD_REQUIRED",
        "branch_local_ready": ready,
        "control_required": True,
    }


def exact_control_build_action(row: dict[str, Any]) -> dict[str, Any]:
    synthesis = control_scope_implementation_synthesis(row)
    return {
        **synthesis,
        "implementation_synthesis_stage": "EXACT_CONTROL_BUILD_ACTION",
        "implementation_action_status": "EXACT_CONTROL_BUILD_REQUIRED_UNDERPOWERED_GLOBAL_ONLY",
        "exact_build_source_requirement": "materialize same-scope or stronger same-resource control rows before scalar scorer interpretation",
        "current_selected_control_count": int(row.get("selected_control_count") or 0),
        "exact_control_count": int(row.get("exact_control_count") or 0),
        "same_symbol_session_control_count": int(row.get("same_symbol_session_control_count") or 0),
        "same_symbol_control_count": int(row.get("same_symbol_control_count") or 0),
        "branch_local_ready": False,
    }


def control_registry_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("control_execution_status") or row.get("execution_status") or "")
    score = to_float(row.get("control_proxy_score"))
    if status == "CONTROL_EXECUTION_COMPARATOR_REGISTERED":
        synthesis_status = "CONTROL_REGISTRY_COMPARATOR_REGISTERED"
        decision = "IMPLEMENT_CONTROL_COMPARATOR_REGISTRY_ROW"
        keep_kill = "IMPLEMENT_CONTROL"
        cause = "control comparator is available for branch-local scorer comparisons"
        ready = True
    else:
        synthesis_status = "CONTROL_REGISTRY_CONTEXT_ONLY"
        decision = "PRESERVE_CONTROL_CONTEXT_NO_COMPARATOR"
        keep_kill = "PRESERVE_CONTEXT"
        cause = "control row is context only and must not be counted as comparator"
        ready = False
    return {
        **_base(row),
        "implementation_synthesis_stage": "CONTROL_REGISTRY_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": "register_control_comparator" if ready else "preserve_control_context",
        "keep_kill_redesign_implement_decision": keep_kill,
        "implementation_success_cause": cause,
        "control_proxy_score": score,
        "control_proxy_score_band": _score_band(score),
        "branch_local_ready": ready,
    }


def denominator_guard_registry_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("denominator_execution_status") or row.get("execution_status") or "")
    score = to_float(row.get("guard_strength_score"))
    ready = status == "DENOMINATOR_EXECUTION_GUARD_REGISTERED"
    return {
        **_base(row),
        "implementation_synthesis_stage": "DENOMINATOR_GUARD_REGISTRY_SYNTHESIS",
        "implementation_synthesis_status": "DENOMINATOR_GUARD_REGISTRY_REGISTERED" if ready else "DENOMINATOR_GUARD_REGISTRY_CONTEXT_ONLY",
        "implementation_synthesis_decision": "IMPLEMENT_DENOMINATOR_GUARD_REGISTRY_ROW" if ready else "PRESERVE_DENOMINATOR_CONTEXT",
        "implementation_action": "register_denominator_guard" if ready else "preserve_denominator_context",
        "keep_kill_redesign_implement_decision": "IMPLEMENT_DENOMINATOR_GUARD" if ready else "PRESERVE_CONTEXT",
        "implementation_success_cause": "denominator guard is required for interpretation and registration" if ready else "denominator guard row is context only",
        "guard_strength_score": score,
        "guard_strength_band": _score_band(score),
        "branch_local_ready": ready,
    }


def source_repair_action_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("source_repair_execution_status") or row.get("execution_status") or "")
    score = _first_float(row, ["source_proxy_score", "horizon_proxy_score"])
    if status == "SOURCE_REPAIR_EXECUTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE":
        synthesis_status = "SOURCE_REPAIR_ACTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE"
        decision = "BUILD_OR_ACQUIRE_EXACT_SOURCE_BEFORE_SCORING"
        keep_kill = "REPAIR_SOURCE"
        action = "rebuild_or_acquire_exact_source_rows"
    elif status == "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_RESCORE":
        synthesis_status = "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_RESCORE"
        decision = "REBUILD_HORIZON_AND_RESCORE"
        keep_kill = "REPAIR_HORIZON_RESCORING"
        action = "rebuild_targetable_horizon_rows_and_rescore"
    elif status == "SOURCE_REPAIR_EXECUTION_HORIZON_REBUILD_KILL_CHECK":
        synthesis_status = "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_KILL_CHECK"
        decision = "REBUILD_HORIZON_AND_KILL_IF_NEGATIVE_PERSISTS"
        keep_kill = "REPAIR_HORIZON_THEN_KILL_CHECK"
        action = "rebuild_targetable_horizon_rows_and_keep_kill_check_if_negative_persists"
    else:
        synthesis_status = "SOURCE_REPAIR_ACTION_CONTEXT_ONLY"
        decision = "PRESERVE_SOURCE_REPAIR_CONTEXT"
        keep_kill = "PRESERVE_CONTEXT"
        action = "preserve_source_repair_context"
    return {
        **_base(row),
        "implementation_synthesis_stage": "SOURCE_REPAIR_ACTION_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": action,
        "keep_kill_redesign_implement_decision": keep_kill,
        "implementation_failure_or_repair_cause": row.get("exact_missing_geometry_or_source_reason"),
        "source_repair_score": score,
        "source_repair_score_band": _score_band(score),
        "duplicate_repair_scope_count": int(row.get("duplicate_repair_scope_count") or 0),
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists")),
        "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
        "current_source_flagged_n": row.get("current_source_flagged_n"),
        "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
        "branch_local_ready": status != "SOURCE_REPAIR_EXECUTION_CONTEXT_ONLY",
        "source_repair_required": True,
    }


def horizon_sidecar_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("horizon_repair_execution_status") or row.get("execution_status") or "")
    if status == "HORIZON_REPAIR_EXECUTION_REBUILD_KILL_CHECK":
        synthesis_status = "HORIZON_SIDECAR_REBUILD_KILL_CHECK"
        decision = "REBUILD_HORIZON_THEN_KEEP_KILL_CHECK"
    elif status == "HORIZON_REPAIR_EXECUTION_REBUILD_RESCORE":
        synthesis_status = "HORIZON_SIDECAR_REBUILD_RESCORE"
        decision = "REBUILD_HORIZON_THEN_RESCORE"
    else:
        synthesis_status = "HORIZON_SIDECAR_CONTEXT_ONLY"
        decision = "PRESERVE_HORIZON_CONTEXT"
    return {
        **_base(row),
        "implementation_synthesis_stage": "HORIZON_SIDECAR_SYNTHESIS",
        "implementation_synthesis_status": synthesis_status,
        "implementation_synthesis_decision": decision,
        "implementation_action": "preserve_horizon_sidecar_action_without_unified_denominator_inflation",
        "keep_kill_redesign_implement_decision": "REPAIR_HORIZON" if "REBUILD" in synthesis_status else "PRESERVE_CONTEXT",
        "horizon_proxy_score": to_float(row.get("horizon_proxy_score")),
        "horizon_proxy_score_band": _score_band(to_float(row.get("horizon_proxy_score"))),
        "branch_local_ready": False,
        "source_repair_required": True,
    }


def coverage_sidecar_synthesis(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("coverage_execution_status") or row.get("execution_status") or "")
    mapping = {
        "COVERAGE_EXECUTION_OBSERVABLE_CANDIDATE_ACTIVE": "COVERAGE_SIDECAR_OBSERVABLE_CANDIDATE_ACTIVE",
        "COVERAGE_EXECUTION_SOURCE_OR_REPAIR_PATH_ACTIVE": "COVERAGE_SIDECAR_SOURCE_OR_REPAIR_ACTIVE",
        "COVERAGE_EXECUTION_CONTROL_PATH_ACTIVE": "COVERAGE_SIDECAR_CONTROL_PATH_ACTIVE",
        "COVERAGE_EXECUTION_DENOMINATOR_GUARD_ACTIVE": "COVERAGE_SIDECAR_DENOMINATOR_GUARD_ACTIVE",
        "COVERAGE_EXECUTION_HORIZON_REPAIR_ACTIVE": "COVERAGE_SIDECAR_HORIZON_REPAIR_ACTIVE",
    }
    return {
        **_base(row),
        "implementation_synthesis_stage": "COVERAGE_SIDECAR_SYNTHESIS",
        "implementation_synthesis_status": mapping.get(status, "COVERAGE_SIDECAR_CONTEXT_ONLY"),
        "implementation_synthesis_decision": "PRESERVE_FULL_PRIMITIVE_COVERAGE_MAP_FOR_NEXT_SYNTHESIS",
        "implementation_action": "preserve_coverage_sidecar_without_unified_denominator_inflation",
        "keep_kill_redesign_implement_decision": "PRESERVE_COVERAGE_MAP",
        "coverage_row_count": row.get("coverage_row_count"),
        "covered_status_counts": row.get("covered_status_counts") or {},
        "implementation_stage_counts": row.get("implementation_stage_counts") or {},
        "branch_local_ready": False,
    }
