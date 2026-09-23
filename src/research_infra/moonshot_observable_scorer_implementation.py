"""Research-only observable/scorer implementation helpers for moonshot rows.

These helpers translate source-guard bundle rows into branch-local observable
candidate specs, source policies, control experiments, denominator guards, and
horizon repair execution specs. They are pure functions with no live-system
side effects.
"""

from __future__ import annotations

from typing import Any


IMPLEMENTATION_SURFACE = "src/research_infra/moonshot_observable_scorer_implementation.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def implementation_score(row: dict[str, Any], bonus: float = 0.0) -> float:
    base = to_float(row.get("bundle_priority_score")) or 0.0
    outside_bonus = 0.03 if row.get("outside_gbpjpy_xauusd_current_branch_box") else 0.0
    return clamp01(base + outside_bonus + bonus)


def scope_key(row: dict[str, Any]) -> str:
    return (
        f"symbol={row.get('symbol')}|session={row.get('route_session')}|"
        f"horizon={row.get('horizon_id')}|primitive={row.get('primitive_flag')}"
    )


def _component_family(component: str, decision: str) -> tuple[str, str, str]:
    if component in {"entry_geometry", "market_gap_entry_geometry"}:
        if component == "market_gap_entry_geometry":
            return (
                "MARKET_GAP_ENTRY_GEOMETRY_OBSERVABLE",
                "REGISTER_MARKET_GAP_ENTRY_GEOMETRY_OBSERVABLE",
                "entry_path_geometry",
            )
        return ("ENTRY_GEOMETRY_OBSERVABLE", "REGISTER_ENTRY_GEOMETRY_OBSERVABLE", "entry_path_geometry")
    if component in {"avoid_filter", "market_gap_avoid_filter", "branch_failure_avoid_filter"}:
        if component == "branch_failure_avoid_filter":
            return (
                "BRANCH_FAILURE_AVOID_OBSERVABLE",
                "REGISTER_FAILURE_CAUSE_AVOID_OBSERVABLE",
                "avoid_inverse_behavior",
            )
        if component == "market_gap_avoid_filter":
            return ("MARKET_GAP_AVOID_OBSERVABLE", "REGISTER_MARKET_GAP_AVOID_OBSERVABLE", "avoid_inverse_behavior")
        return ("AVOID_FILTER_OBSERVABLE", "REGISTER_AVOID_FILTER_OBSERVABLE", "avoid_inverse_behavior")
    if component == "market_entry_comparator":
        return ("MARKET_ENTRY_COMPARATOR_OBSERVABLE", "REGISTER_MARKET_ENTRY_COMPARATOR", "execution_fillability")
    if component == "branch_proxy_scorer":
        return ("BRANCH_PROXY_SCORER_OBSERVABLE", "REGISTER_BRANCH_PROXY_SCORER", "branch_proxy_scoring")
    if "SCORER" in decision:
        return ("SCORER_PATCH_OBSERVABLE", "REGISTER_SCORER_PATCH_OBSERVABLE", "scorer_patch")
    return ("MISC_OBSERVABLE", "REGISTER_MISC_OBSERVABLE", "misc")


def observable_rule_spec(row: dict[str, Any]) -> dict[str, Any]:
    component = str(row.get("shadow_scorer_component") or "")
    decision = str(row.get("bundle_decision") or "")
    family, operation, primitive_science = _component_family(component, decision)
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "implementation_stage": "OBSERVABLE_RULE_SPEC",
        "implementation_status": "OBSERVABLE_REGISTER_BRANCH_LOCAL_SHADOW_SPEC",
        "implementation_operation": operation,
        "observable_family": family,
        "primitive_science_dimension": primitive_science,
        "observable_scope_key": scope_key(row),
        "runtime_registry": "branch_local_research_shadow_observable_registry",
        "runtime_effect": "record_and_score_only",
        "scorer_binding": (
            "status_quo_control_required"
            if "ENTRY" in decision or "COMPARATOR" in decision
            else "control_or_source_guard_as_declared"
        ),
        "required_runtime_fields": [
            "symbol",
            "route_session",
            "session_bucket",
            "horizon_id",
            "primitive_flag",
            "mechanical_scope_key",
        ],
        "implementation_priority_score": implementation_score(row, 0.01),
        "live_effect": False,
    }


def source_guard_policy_spec(row: dict[str, Any]) -> dict[str, Any]:
    permission = str(row.get("bundle_permission") or "")
    decision = str(row.get("bundle_decision") or "")
    if permission == "ALLOW_GUARDED_PROXY_SCORING":
        status = "SOURCE_POLICY_ALLOW_GUARDED_PROXY_OBSERVABLE_SCORE"
        operation = "APPLY_EXPANDED_PROXY_SCOPE_GUARD_AND_SCORE"
        action = "score_proxy_now_with_scope_guard"
    elif permission == "SCORE_WITH_GUARD_NO_UNCONDITIONAL_ENABLE":
        status = "SOURCE_POLICY_SCORE_AMBIGUOUS_PROXY_WITH_SCOPE_GUARD"
        operation = "APPLY_AMBIGUOUS_PROXY_SCOPE_GUARD_AND_SCORE_CONTROL"
        action = "score_proxy_with_ambiguity_guard_before_enable"
    elif permission == "DO_NOT_ENABLE_SOURCE_DEPENDENT_RULE":
        status = "SOURCE_POLICY_BLOCK_UNTIL_EXACT_SOURCE_REPAIR"
        operation = "REQUIRE_EXACT_SOURCE_REPAIR_BEFORE_OBSERVABLE_ENABLE"
        action = "repair_exact_source_or_keep_blocked"
    elif "KILL_IF_UNCHANGED" in permission:
        status = "SOURCE_POLICY_FAILCLOSED_REPAIR_THEN_KILL_IF_NEGATIVE"
        operation = "REBUILD_HORIZON_AND_KILL_IF_NEGATIVE_PERSISTS"
        action = "repair_horizon_then_kill_if_interval_remains_negative"
    elif "RESCORE" in permission:
        status = "SOURCE_POLICY_FAILCLOSED_REPAIR_THEN_RESCORE"
        operation = "REBUILD_HORIZON_AND_RESCORE_PROXY_INTERVAL"
        action = "repair_horizon_then_rescore_interval"
    else:
        status = "SOURCE_POLICY_REPAIR_THEN_ALLOW_IF_POSITIVE"
        operation = "REBUILD_HORIZON_AND_ALLOW_IF_POSITIVE"
        action = "repair_horizon_then_allow_guarded_positive"
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "implementation_stage": "SOURCE_GUARD_POLICY_SPEC",
        "implementation_status": status,
        "implementation_operation": operation,
        "source_policy_action": action,
        "source_policy_decision": decision,
        "source_guard_mode": row.get("source_guard_mode"),
        "source_repair_required": bool(row.get("source_repair_required")),
        "proxy_interval_lower": row.get("materialization_proxy_r_style_lower"),
        "proxy_interval_midpoint": row.get("materialization_proxy_r_style_midpoint"),
        "proxy_interval_upper": row.get("materialization_proxy_r_style_upper"),
        "proxy_interval_class": row.get("materialization_proxy_r_style_result_class"),
        "source_targetable_n": row.get("current_targetable_flagged_n"),
        "source_flagged_n": row.get("current_source_flagged_n"),
        "source_failclosed_n": row.get("current_failclosed_flagged_n"),
        "implementation_priority_score": implementation_score(row),
        "observable_scope_key": scope_key(row),
        "live_effect": False,
    }


def control_experiment_spec(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("bundle_decision") or "")
    if decision == "CONTROL_SCORE_ENTRY_GEOMETRY_AGAINST_STATUS_QUO":
        status = "CONTROL_EXPERIMENT_ENTRY_GEOMETRY_VS_STATUS_QUO"
        operation = "RUN_ENTRY_GEOMETRY_STATUS_QUO_COMPARATOR"
        family = "entry_geometry_control"
    elif decision == "CONTROL_SCORE_FILLABILITY_REDESIGN_BEFORE_ENABLE":
        status = "CONTROL_EXPERIMENT_FILLABILITY_REDESIGN_BEFORE_ENABLE"
        operation = "RUN_FILLABILITY_REDESIGN_CONTROL"
        family = "fillability_no_fill_control"
    elif decision == "CONTROL_SCORE_MARKET_GAP_ENTRY_AGAINST_STATUS_QUO":
        status = "CONTROL_EXPERIMENT_MARKET_GAP_ENTRY_VS_STATUS_QUO"
        operation = "RUN_MARKET_GAP_ENTRY_STATUS_QUO_COMPARATOR"
        family = "market_gap_entry_control"
    elif decision == "CONTROL_SCORE_AVOID_FILTER_WITH_INVERSE_CONTROL":
        status = "CONTROL_EXPERIMENT_AVOID_FILTER_WITH_INVERSE_SIBLING"
        operation = "RUN_AVOID_INVERSE_SIBLING_COMPARATOR"
        family = "avoid_inverse_control"
    elif decision == "CONTROL_SCORE_SCORER_COMPONENT_PATCH_BEFORE_ENABLE":
        status = "CONTROL_EXPERIMENT_SCORER_PATCH_ABLATION"
        operation = "RUN_SCORER_PATCH_ABLATION_CONTROL"
        family = "scorer_patch_control"
    else:
        status = "CONTROL_EXPERIMENT_CONTEXT_ONLY"
        operation = "PRESERVE_CONTROL_CONTEXT_ONLY"
        family = "context_control"
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "implementation_stage": "CONTROL_EXPERIMENT_SPEC",
        "implementation_status": status,
        "implementation_operation": operation,
        "control_experiment_family": family,
        "control_required_before_enable": True,
        "control_source_status": row.get("control_status"),
        "observable_scope_key": scope_key(row),
        "implementation_priority_score": implementation_score(row),
        "live_effect": False,
    }


def denominator_enforcement_spec(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("bundle_decision") or "")
    if decision == "DENOMINATOR_GUARD_FORCE_OUTSIDE_BRANCH_SCOPE":
        status = "DENOMINATOR_ENFORCE_OUTSIDE_BRANCH_SCOPE"
        operation = "REQUIRE_OUTSIDE_MARKET_DENOMINATOR_BEFORE_CONCENTRATION_INTERPRETATION"
    elif decision == "DENOMINATOR_GUARD_SOURCE_ROOT_COVERAGE":
        status = "DENOMINATOR_ENFORCE_SOURCE_ROOT_COVERAGE"
        operation = "REQUIRE_SOURCE_ROOT_COVERAGE_BEFORE_SCORER_INTERPRETATION"
    elif decision == "DENOMINATOR_GUARD_KEEP_MECHANISM_AND_DENOMINATOR":
        status = "DENOMINATOR_KEEP_MECHANISM_AND_DENOMINATOR_SPLIT"
        operation = "PRESERVE_TRUE_CONCENTRATION_AND_DENOMINATOR_ARTIFACT_SPLIT"
    else:
        status = "DENOMINATOR_ENFORCE_CONTEXT_COVERAGE"
        operation = "REQUIRE_CONTEXT_COVERAGE_BEFORE_BRANCH_DECISION"
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "implementation_stage": "DENOMINATOR_ENFORCEMENT_SPEC",
        "implementation_status": status,
        "implementation_operation": operation,
        "denominator_guard_status": row.get("guard_status"),
        "observable_scope_key": scope_key(row),
        "implementation_priority_score": implementation_score(row),
        "live_effect": False,
    }


def horizon_repair_execution_spec(row: dict[str, Any]) -> dict[str, Any]:
    decision = str(row.get("bundle_decision") or "")
    if decision == "HORIZON_REPAIR_REBUILD_AND_KILL_IF_NEGATIVE_PERSISTS":
        status = "HORIZON_REPAIR_EXECUTE_THEN_KILL_IF_NEGATIVE_PERSISTS"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_KILL_IF_NEGATIVE"
    elif decision == "HORIZON_REPAIR_REBUILD_AND_ALLOW_GUARDED_ENABLE":
        status = "HORIZON_REPAIR_EXECUTE_THEN_ALLOW_IF_POSITIVE_PERSISTS"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_ALLOW_IF_POSITIVE"
    else:
        status = "HORIZON_REPAIR_EXECUTE_THEN_RESCORE_INTERVAL"
        operation = "REBUILD_TARGETABLE_HORIZON_AND_RESCORE"
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "implementation_stage": "HORIZON_REPAIR_EXECUTION_SPEC",
        "implementation_status": status,
        "implementation_operation": operation,
        "repair_action": row.get("repair_action"),
        "repair_reason": row.get("repair_reason"),
        "source_bundle_row_id": row.get("source_bundle_row_id"),
        "observable_scope_key": scope_key(row),
        "implementation_priority_score": implementation_score(row, 0.02),
        "live_effect": False,
    }


def primitive_coverage_state(row: dict[str, Any]) -> dict[str, Any]:
    stage = str(row.get("implementation_stage") or row.get("bundle_stage") or "")
    status = str(row.get("implementation_status") or row.get("bundle_decision") or "")
    if stage == "OBSERVABLE_RULE_SPEC":
        coverage_status = "COVERED_AS_BRANCH_LOCAL_OBSERVABLE_CANDIDATE"
    elif stage == "SOURCE_GUARD_POLICY_SPEC":
        coverage_status = "COVERED_WITH_SOURCE_GUARD_OR_REPAIR_REQUIREMENT"
    elif stage == "CONTROL_EXPERIMENT_SPEC":
        coverage_status = "COVERED_WITH_CONTROL_EXPERIMENT_REQUIREMENT"
    elif stage == "DENOMINATOR_ENFORCEMENT_SPEC":
        coverage_status = "COVERED_WITH_DENOMINATOR_ENFORCEMENT_GUARD"
    elif stage == "HORIZON_REPAIR_EXECUTION_SPEC":
        coverage_status = "COVERED_WITH_HORIZON_REPAIR_EXECUTION_PATH"
    else:
        coverage_status = "COVERED_CONTEXT_ONLY"
    return {
        "implementation_surface": IMPLEMENTATION_SURFACE,
        "primitive_coverage_status": coverage_status,
        "primitive_coverage_detail": status,
        "observable_scope_key": scope_key(row),
        "live_effect": False,
    }
