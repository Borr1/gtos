"""Research-only execution helpers for moonshot observable/scorer specs."""

from __future__ import annotations

from typing import Any


EXECUTION_SURFACE = "src/research_infra/moonshot_observable_execution.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _score(row: dict[str, Any], bonus: float = 0.0) -> float:
    base = to_float(row.get("implementation_priority_score")) or 0.0
    return clamp01(base + bonus)


def classify_source_policy_execution(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_status") or "")
    if status == "SOURCE_POLICY_ALLOW_GUARDED_PROXY_OBSERVABLE_SCORE":
        decision = "SOURCE_EXECUTE_GUARDED_PROXY_SCORE_NOW"
        permission = "SOURCE_POLICY_PERMITS_GUARDED_SCORE"
        action = "score_proxy_under_scope_guard"
    elif status == "SOURCE_POLICY_SCORE_AMBIGUOUS_PROXY_WITH_SCOPE_GUARD":
        decision = "SOURCE_EXECUTE_AMBIGUOUS_PROXY_SCORE_WITH_CONTROL"
        permission = "SOURCE_POLICY_REQUIRES_AMBIGUITY_GUARD"
        action = "score_proxy_with_ambiguity_and_control_guard"
    elif status == "SOURCE_POLICY_BLOCK_UNTIL_EXACT_SOURCE_REPAIR":
        decision = "SOURCE_EXECUTE_EXACT_SOURCE_REPAIR_WORK_ORDER"
        permission = "SOURCE_POLICY_BLOCKS_ENABLE_UNTIL_EXACT_REPAIR"
        action = "repair_exact_source_before_observable_enable"
    elif status == "SOURCE_POLICY_FAILCLOSED_REPAIR_THEN_KILL_IF_NEGATIVE":
        decision = "SOURCE_EXECUTE_HORIZON_REPAIR_AND_KILL_CHECK"
        permission = "SOURCE_POLICY_BLOCKS_ENABLE_UNTIL_HORIZON_REPAIR"
        action = "rebuild_horizon_then_kill_if_negative_persists"
    elif status == "SOURCE_POLICY_FAILCLOSED_REPAIR_THEN_RESCORE":
        decision = "SOURCE_EXECUTE_HORIZON_REPAIR_AND_RESCORE"
        permission = "SOURCE_POLICY_BLOCKS_ENABLE_UNTIL_HORIZON_RESCORE"
        action = "rebuild_horizon_then_rescore_proxy_interval"
    else:
        decision = "SOURCE_EXECUTE_CONTEXT_ONLY"
        permission = "SOURCE_POLICY_CONTEXT_ONLY"
        action = "preserve_source_policy_context"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "SOURCE_POLICY_EXECUTION",
        "execution_decision": decision,
        "execution_permission": permission,
        "execution_action": action,
        "execution_priority_score": _score(row),
        "live_effect": False,
    }


def classify_control_execution(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_status") or "")
    if status == "CONTROL_EXPERIMENT_ENTRY_GEOMETRY_VS_STATUS_QUO":
        decision = "CONTROL_EXECUTE_ENTRY_STATUS_QUO_COMPARATOR"
        action = "score_entry_variant_against_status_quo"
    elif status == "CONTROL_EXPERIMENT_FILLABILITY_REDESIGN_BEFORE_ENABLE":
        decision = "CONTROL_EXECUTE_FILLABILITY_REDESIGN_COMPARATOR"
        action = "score_fillability_redesign_before_enable"
    elif status == "CONTROL_EXPERIMENT_MARKET_GAP_ENTRY_VS_STATUS_QUO":
        decision = "CONTROL_EXECUTE_MARKET_GAP_ENTRY_COMPARATOR"
        action = "score_market_gap_entry_against_status_quo"
    elif status == "CONTROL_EXPERIMENT_AVOID_FILTER_WITH_INVERSE_SIBLING":
        decision = "CONTROL_EXECUTE_AVOID_INVERSE_SIBLING_COMPARATOR"
        action = "score_avoid_filter_against_inverse_sibling"
    elif status == "CONTROL_EXPERIMENT_SCORER_PATCH_ABLATION":
        decision = "CONTROL_EXECUTE_SCORER_PATCH_ABLATION"
        action = "score_scorer_patch_ablation"
    else:
        decision = "CONTROL_EXECUTE_CONTEXT_PRESERVE"
        action = "preserve_control_context"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "CONTROL_EXECUTION",
        "execution_decision": decision,
        "execution_action": action,
        "control_required_before_enable": bool(row.get("control_required_before_enable", True)),
        "execution_priority_score": _score(row),
        "live_effect": False,
    }


def classify_denominator_execution(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_status") or "")
    if status == "DENOMINATOR_ENFORCE_OUTSIDE_BRANCH_SCOPE":
        decision = "DENOMINATOR_EXECUTE_OUTSIDE_BRANCH_SCOPE_GUARD"
        action = "enforce_outside_market_denominator"
    elif status == "DENOMINATOR_ENFORCE_SOURCE_ROOT_COVERAGE":
        decision = "DENOMINATOR_EXECUTE_SOURCE_ROOT_COVERAGE_GUARD"
        action = "enforce_source_root_coverage"
    elif status == "DENOMINATOR_KEEP_MECHANISM_AND_DENOMINATOR_SPLIT":
        decision = "DENOMINATOR_EXECUTE_MECHANISM_ARTIFACT_SPLIT_GUARD"
        action = "preserve_true_concentration_and_denominator_artifact_split"
    else:
        decision = "DENOMINATOR_EXECUTE_CONTEXT_COVERAGE_GUARD"
        action = "enforce_context_coverage_guard"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "DENOMINATOR_EXECUTION",
        "execution_decision": decision,
        "execution_action": action,
        "execution_priority_score": _score(row),
        "live_effect": False,
    }


def classify_horizon_repair_execution(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("implementation_status") or "")
    if status == "HORIZON_REPAIR_EXECUTE_THEN_KILL_IF_NEGATIVE_PERSISTS":
        decision = "HORIZON_WORK_ORDER_REBUILD_THEN_KILL_IF_NEGATIVE"
        action = "rebuild_targetable_horizon_then_kill_if_negative"
    elif status == "HORIZON_REPAIR_EXECUTE_THEN_ALLOW_IF_POSITIVE_PERSISTS":
        decision = "HORIZON_WORK_ORDER_REBUILD_THEN_ALLOW_IF_POSITIVE"
        action = "rebuild_targetable_horizon_then_allow_if_positive"
    else:
        decision = "HORIZON_WORK_ORDER_REBUILD_THEN_RESCORE"
        action = "rebuild_targetable_horizon_then_rescore"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "HORIZON_REPAIR_WORK_ORDER",
        "execution_decision": decision,
        "execution_action": action,
        "repair_blocking": True,
        "execution_priority_score": _score(row, 0.03),
        "live_effect": False,
    }


def classify_observable_execution(
    row: dict[str, Any],
    source_statuses: list[str],
    control_statuses: list[str],
    denominator_statuses: list[str],
) -> dict[str, Any]:
    binding = str(row.get("scorer_binding") or "")
    family = str(row.get("observable_family") or "")
    control_required = binding == "status_quo_control_required" or family in {
        "ENTRY_GEOMETRY_OBSERVABLE",
        "MARKET_ENTRY_COMPARATOR_OBSERVABLE",
        "MARKET_GAP_ENTRY_GEOMETRY_OBSERVABLE",
    }
    source_blocked = any("BLOCK" in status or "FAILCLOSED" in status for status in source_statuses)
    source_ambiguous = any("AMBIGUOUS" in status for status in source_statuses)
    denominator_guarded = bool(denominator_statuses)
    if source_blocked:
        decision = "OBSERVABLE_EXECUTE_SOURCE_REPAIR_FIRST"
        permission = "BLOCK_REGISTER_UNTIL_SOURCE_REPAIR"
    elif control_required and control_statuses:
        decision = "OBSERVABLE_EXECUTE_SCORE_WITH_CONTROL_NOW"
        permission = "REGISTER_FOR_CONTROLLED_SHADOW_SCORE"
    elif control_required:
        decision = "OBSERVABLE_EXECUTE_CONTROL_LOOKUP_REQUIRED"
        permission = "HOLD_UNTIL_CONTROL_MATCH_EXISTS"
    elif source_ambiguous:
        decision = "OBSERVABLE_EXECUTE_GUARDED_AMBIGUOUS_PROXY_SCORE"
        permission = "REGISTER_WITH_AMBIGUITY_GUARD"
    elif denominator_guarded:
        decision = "OBSERVABLE_EXECUTE_REGISTER_WITH_DENOMINATOR_GUARD"
        permission = "REGISTER_WITH_DENOMINATOR_GUARD"
    else:
        decision = "OBSERVABLE_EXECUTE_REGISTER_SHADOW_NOW"
        permission = "REGISTER_BRANCH_LOCAL_SHADOW_NOW"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "OBSERVABLE_EXECUTION",
        "execution_decision": decision,
        "execution_permission": permission,
        "source_policy_match_count": len(source_statuses),
        "control_experiment_match_count": len(control_statuses),
        "denominator_guard_match_count": len(denominator_statuses),
        "control_required": control_required,
        "source_blocked_or_repair_required": source_blocked,
        "source_ambiguous": source_ambiguous,
        "denominator_guarded": denominator_guarded,
        "execution_priority_score": _score(row, 0.02 if denominator_guarded else 0.0),
        "live_effect": False,
    }


def classify_coverage_action(row: dict[str, Any]) -> dict[str, Any]:
    statuses = row.get("covered_status_counts") or {}
    if statuses.get("COVERED_WITH_HORIZON_REPAIR_EXECUTION_PATH"):
        action = "COVERAGE_EXECUTE_HORIZON_REPAIR_PATH"
    elif statuses.get("COVERED_WITH_SOURCE_GUARD_OR_REPAIR_REQUIREMENT"):
        action = "COVERAGE_EXECUTE_SOURCE_POLICY_OR_REPAIR"
    elif statuses.get("COVERED_WITH_CONTROL_EXPERIMENT_REQUIREMENT"):
        action = "COVERAGE_EXECUTE_CONTROL_EXPERIMENT"
    elif statuses.get("COVERED_WITH_DENOMINATOR_ENFORCEMENT_GUARD"):
        action = "COVERAGE_EXECUTE_DENOMINATOR_GUARD"
    elif statuses.get("COVERED_AS_BRANCH_LOCAL_OBSERVABLE_CANDIDATE"):
        action = "COVERAGE_REGISTER_OBSERVABLE_CANDIDATE"
    else:
        action = "COVERAGE_PRESERVE_CONTEXT"
    return {
        "execution_surface": EXECUTION_SURFACE,
        "execution_stage": "PRIMITIVE_COVERAGE_EXECUTION",
        "execution_decision": action,
        "execution_action": "preserve_or_execute_coverage_status",
        "live_effect": False,
    }
