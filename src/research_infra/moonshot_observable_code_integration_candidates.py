"""Research-only code integration candidates for observable implementation synthesis rows."""

from __future__ import annotations

from typing import Any


CODE_INTEGRATION_SURFACE = "src/research_infra/moonshot_observable_code_integration_candidates.py"
BRANCH_LOCAL_REGISTRY_TARGET = "src/research_infra/moonshot_branch_local_observable_registry.py"
BRANCH_LOCAL_SCORER_TARGET = "src/research_infra/moonshot_branch_local_observable_scorers.py"
BRANCH_LOCAL_REPAIR_TARGET = "src/research_infra/moonshot_branch_local_source_repair_work.py"


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
    for key in [
        "scorer_registration_score",
        "observable_registry_score",
        "control_scope_execution_score",
        "control_proxy_score",
        "guard_strength_score",
        "source_repair_score",
        "horizon_proxy_score",
    ]:
        value = to_float(row.get(key))
        if value is not None:
            return clamp01(value + bonus)
    return clamp01(bonus)


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "code_integration_surface": CODE_INTEGRATION_SURFACE,
        "input_implementation_synthesis_status": row.get("implementation_synthesis_status"),
        "input_keep_kill_redesign_implement_decision": row.get("keep_kill_redesign_implement_decision"),
        "runtime_effect": "branch_local_research_only_record_and_score",
        "source_repair_required": bool(row.get("source_repair_required")),
        "control_required": bool(row.get("control_required")),
        "branch_local_ready": bool(row.get("branch_local_ready")),
        "live_effect": False,
    }


def scorer_code_integration_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_synthesis_status") or "")
    if status == "SCORER_REGISTRATION_CONTROLLED_CHALLENGER_REGISTER":
        candidate_status = "CODE_INTEGRATION_CONTROLLED_OBSERVABLE_SCORER_PATCH"
        action = "ADD_CONTROLLED_OBSERVABLE_SCORER_SPEC"
        target = BRANCH_LOCAL_SCORER_TARGET
        decision = "IMPLEMENT_BRANCH_LOCAL_SCORER_PATCH"
        standalone = True
        bonus = 0.08
    elif status == "SCORER_REGISTRATION_SOURCE_GUARDED_PROXY_REGISTER":
        candidate_status = "CODE_INTEGRATION_GUARDED_SOURCE_PROXY_SCORER_PATCH"
        action = "ADD_GUARDED_SOURCE_PROXY_SCORER_SPEC"
        target = BRANCH_LOCAL_SCORER_TARGET
        decision = "IMPLEMENT_BRANCH_LOCAL_SOURCE_SCORER_PATCH"
        standalone = True
        bonus = 0.05
    elif status == "SCORER_REGISTRATION_SOURCE_AMBIGUOUS_CONTROL_GUARD_REGISTER":
        candidate_status = "CODE_INTEGRATION_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SCORER_PATCH"
        action = "ADD_AMBIGUOUS_SOURCE_PROXY_CONTROL_GUARD_SPEC"
        target = BRANCH_LOCAL_SCORER_TARGET
        decision = "IMPLEMENT_BRANCH_LOCAL_SOURCE_SCORER_WITH_CONTROL_GUARD"
        standalone = False
        bonus = 0.03
    else:
        candidate_status = "CODE_INTEGRATION_SCORER_CONTEXT_ONLY"
        action = "PRESERVE_SCORER_CONTEXT"
        target = BRANCH_LOCAL_SCORER_TARGET
        decision = "PRESERVE_CONTEXT"
        standalone = False
        bonus = 0.0
    return {
        **_base(row),
        "code_integration_stage": "SCORER_CODE_INTEGRATION_CANDIDATE",
        "code_integration_status": candidate_status,
        "code_integration_decision": decision,
        "code_integration_action": action,
        "target_file_hint": target,
        "candidate_function_hint": action.lower(),
        "standalone_interpretation_allowed": standalone,
        "control_guard_required": not standalone,
        "integration_priority_score": _priority(row, bonus),
    }


def observable_registry_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    ready = row.get("implementation_synthesis_status") == "OBSERVABLE_REGISTRY_DENOMINATOR_GUARDED_REGISTER"
    return {
        **_base(row),
        "code_integration_stage": "OBSERVABLE_REGISTRY_CODE_INTEGRATION_CANDIDATE",
        "code_integration_status": (
            "CODE_INTEGRATION_DENOMINATOR_GUARDED_OBSERVABLE_REGISTRY_PATCH"
            if ready
            else "CODE_INTEGRATION_OBSERVABLE_CONTEXT_ONLY"
        ),
        "code_integration_decision": (
            "IMPLEMENT_BRANCH_LOCAL_OBSERVABLE_REGISTRY_PATCH" if ready else "PRESERVE_OBSERVABLE_CONTEXT"
        ),
        "code_integration_action": "ADD_DENOMINATOR_GUARDED_OBSERVABLE_SPEC" if ready else "PRESERVE_OBSERVABLE_CONTEXT",
        "target_file_hint": BRANCH_LOCAL_REGISTRY_TARGET,
        "candidate_function_hint": "add_denominator_guarded_observable_spec",
        "denominator_guard_required": ready,
        "integration_priority_score": _priority(row, 0.04 if ready else 0.0),
    }


def control_scope_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_synthesis_status") or "")
    if status == "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_SESSION_GUARD":
        candidate_status = "CODE_INTEGRATION_SESSION_PROXY_CONTROL_GUARD_PATCH"
        action = "ADD_SESSION_MATCHED_PROXY_CONTROL_GUARD"
        decision = "IMPLEMENT_PROXY_CONTROL_GUARD_PATCH"
        ready = True
        exact = False
    elif status == "CONTROL_SCOPE_IMPLEMENT_PROXY_SAME_SYMBOL_GUARD":
        candidate_status = "CODE_INTEGRATION_SYMBOL_PROXY_CONTROL_GUARD_PATCH"
        action = "ADD_SYMBOL_MATCHED_PROXY_CONTROL_GUARD"
        decision = "IMPLEMENT_PROXY_CONTROL_GUARD_PATCH"
        ready = True
        exact = False
    elif status == "CONTROL_SCOPE_IMPLEMENT_EXACT_CONTROL_BUILD_REQUIRED":
        candidate_status = "CODE_INTEGRATION_EXACT_CONTROL_BUILDER_WORK_ORDER"
        action = "BUILD_EXACT_CONTROL_SCOPE_ROWS"
        decision = "BUILD_EXACT_CONTROL_SCOPE_BEFORE_SCALAR_INTEGRATION"
        ready = False
        exact = True
    else:
        candidate_status = "CODE_INTEGRATION_CONTROL_SCOPE_CONTEXT_ONLY"
        action = "PRESERVE_CONTROL_SCOPE_CONTEXT"
        decision = "PRESERVE_CONTEXT"
        ready = False
        exact = False
    return {
        **_base(row),
        "code_integration_stage": "CONTROL_SCOPE_CODE_INTEGRATION_CANDIDATE",
        "code_integration_status": candidate_status,
        "code_integration_decision": decision,
        "code_integration_action": action,
        "target_file_hint": BRANCH_LOCAL_REGISTRY_TARGET,
        "candidate_function_hint": action.lower(),
        "exact_control_build_required": exact,
        "control_builder_required": exact,
        "branch_local_ready": ready,
        "selected_control_count": int(row.get("selected_control_count") or 0),
        "integration_priority_score": _priority(row, 0.02 if ready else 0.0),
    }


def exact_control_builder_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **control_scope_code_candidate(row),
        "code_integration_stage": "EXACT_CONTROL_BUILDER_CODE_ACTION",
        "code_integration_status": "CODE_INTEGRATION_EXACT_CONTROL_BUILDER_WORK_ORDER",
        "code_integration_decision": "BUILD_EXACT_CONTROL_SCOPE_BEFORE_SCALAR_INTEGRATION",
        "code_integration_action": "BUILD_EXACT_CONTROL_SCOPE_ROWS",
        "target_file_hint": BRANCH_LOCAL_REPAIR_TARGET,
        "exact_build_source_requirement": row.get("exact_build_source_requirement"),
        "branch_local_ready": False,
    }


def control_registry_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    ready = row.get("implementation_synthesis_status") == "CONTROL_REGISTRY_COMPARATOR_REGISTERED"
    return {
        **_base(row),
        "code_integration_stage": "CONTROL_REGISTRY_CODE_INTEGRATION_CANDIDATE",
        "code_integration_status": (
            "CODE_INTEGRATION_CONTROL_COMPARATOR_REGISTRY_PATCH"
            if ready
            else "CODE_INTEGRATION_CONTROL_CONTEXT_ONLY"
        ),
        "code_integration_decision": "IMPLEMENT_CONTROL_COMPARATOR_REGISTRY_PATCH" if ready else "PRESERVE_CONTROL_CONTEXT",
        "code_integration_action": "ADD_CONTROL_COMPARATOR_SPEC" if ready else "PRESERVE_CONTROL_CONTEXT",
        "target_file_hint": BRANCH_LOCAL_REGISTRY_TARGET,
        "candidate_function_hint": "add_control_comparator_spec",
        "branch_local_ready": ready,
        "integration_priority_score": _priority(row, 0.02 if ready else 0.0),
    }


def denominator_guard_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    ready = row.get("implementation_synthesis_status") == "DENOMINATOR_GUARD_REGISTRY_REGISTERED"
    return {
        **_base(row),
        "code_integration_stage": "DENOMINATOR_GUARD_CODE_INTEGRATION_CANDIDATE",
        "code_integration_status": (
            "CODE_INTEGRATION_DENOMINATOR_GUARD_PATCH" if ready else "CODE_INTEGRATION_DENOMINATOR_CONTEXT_ONLY"
        ),
        "code_integration_decision": "IMPLEMENT_DENOMINATOR_GUARD_PATCH" if ready else "PRESERVE_DENOMINATOR_CONTEXT",
        "code_integration_action": "ADD_DENOMINATOR_GUARD_SPEC" if ready else "PRESERVE_DENOMINATOR_CONTEXT",
        "target_file_hint": BRANCH_LOCAL_REGISTRY_TARGET,
        "candidate_function_hint": "add_denominator_guard_spec",
        "branch_local_ready": ready,
        "integration_priority_score": _priority(row, 0.02 if ready else 0.0),
    }


def source_repair_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_synthesis_status") or "")
    if status == "SOURCE_REPAIR_ACTION_EXACT_SOURCE_REBUILD_OR_ACQUIRE":
        candidate_status = "CODE_INTEGRATION_EXACT_SOURCE_REPAIR_WORK_ORDER"
        action = "BUILD_OR_ACQUIRE_EXACT_SOURCE_ROWS"
    elif status == "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_RESCORE":
        candidate_status = "CODE_INTEGRATION_HORIZON_REBUILD_RESCORE_WORK_ORDER"
        action = "REBUILD_HORIZON_ROWS_AND_RESCORE"
    elif status == "SOURCE_REPAIR_ACTION_HORIZON_REBUILD_KILL_CHECK":
        candidate_status = "CODE_INTEGRATION_HORIZON_REBUILD_KILL_CHECK_WORK_ORDER"
        action = "REBUILD_HORIZON_ROWS_AND_KILL_CHECK"
    else:
        candidate_status = "CODE_INTEGRATION_SOURCE_REPAIR_CONTEXT_ONLY"
        action = "PRESERVE_SOURCE_REPAIR_CONTEXT"
    return {
        **_base(row),
        "code_integration_stage": "SOURCE_REPAIR_CODE_ACTION",
        "code_integration_status": candidate_status,
        "code_integration_decision": "EXECUTE_SOURCE_OR_HORIZON_REPAIR_WORK_ORDER",
        "code_integration_action": action,
        "target_file_hint": BRANCH_LOCAL_REPAIR_TARGET,
        "candidate_function_hint": action.lower(),
        "source_repair_required": True,
        "branch_local_ready": False,
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists")),
        "integration_priority_score": _priority(row, 0.01),
    }


def horizon_sidecar_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "code_integration_stage": "HORIZON_SIDECAR_CODE_ACTION",
        "code_integration_status": str(row.get("implementation_synthesis_status") or "HORIZON_SIDECAR_CONTEXT_ONLY").replace(
            "HORIZON_SIDECAR", "CODE_INTEGRATION_HORIZON_SIDECAR"
        ),
        "code_integration_decision": "PRESERVE_HORIZON_SIDECAR_REPAIR_CONTEXT",
        "code_integration_action": "PRESERVE_HORIZON_REPAIR_SIDECAR",
        "target_file_hint": BRANCH_LOCAL_REPAIR_TARGET,
        "branch_local_ready": False,
        "source_repair_required": True,
        "integration_priority_score": _priority(row),
    }


def coverage_sidecar_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **_base(row),
        "code_integration_stage": "COVERAGE_SIDECAR_CODE_ACTION",
        "code_integration_status": str(row.get("implementation_synthesis_status") or "COVERAGE_SIDECAR_CONTEXT_ONLY").replace(
            "COVERAGE_SIDECAR", "CODE_INTEGRATION_COVERAGE_SIDECAR"
        ),
        "code_integration_decision": "PRESERVE_FULL_PRIMITIVE_COVERAGE_MAP",
        "code_integration_action": "PRESERVE_COVERAGE_SIDECAR",
        "target_file_hint": BRANCH_LOCAL_REGISTRY_TARGET,
        "branch_local_ready": False,
        "integration_priority_score": _priority(row),
    }
