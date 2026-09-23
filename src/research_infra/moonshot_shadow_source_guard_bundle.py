"""Research-only source-guard bundle helpers for moonshot shadow rules.

The helpers assemble branch-local shadow enables, source materialization
guards, score-with-control rows, and denominator guards into executable
research decisions. They are pure functions with no live-system side effects.
"""

from __future__ import annotations

from typing import Any


BUNDLE_SURFACE = "src/research_infra/moonshot_shadow_source_guard_bundle.py"


def to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def bundle_score(row: dict[str, Any], base_key: str = "shadow_scorer_score") -> float:
    base = to_float(row.get(base_key))
    if base is None:
        base = to_float(row.get("materialization_proxy_score")) or 0.0
    outside_bonus = 0.02 if row.get("outside_gbpjpy_xauusd_current_branch_box") else 0.0
    return clamp01(base + outside_bonus)


def classify_enable_bundle(row: dict[str, Any]) -> dict[str, Any]:
    component = str(row.get("shadow_scorer_component") or "unknown")
    action_by_component = {
        "entry_geometry": "ENABLE_ENTRY_GEOMETRY_SHADOW_RULE",
        "avoid_filter": "ENABLE_AVOID_FILTER_SHADOW_RULE",
        "market_gap_entry_geometry": "ENABLE_MARKET_GAP_ENTRY_GEOMETRY_SHADOW_RULE",
        "market_gap_avoid_filter": "ENABLE_MARKET_GAP_AVOID_FILTER_SHADOW_RULE",
        "market_entry_comparator": "ENABLE_MARKET_ENTRY_COMPARATOR_SHADOW_RULE",
        "branch_proxy_scorer": "ENABLE_BRANCH_PROXY_SCORER_SHADOW_RULE",
        "branch_failure_avoid_filter": "ENABLE_BRANCH_FAILURE_AVOID_FILTER_SHADOW_RULE",
    }
    action = action_by_component.get(component, "ENABLE_MISC_SHADOW_RULE")
    return {
        "bundle_surface": BUNDLE_SURFACE,
        "bundle_stage": "IMPLEMENT_ENABLE",
        "bundle_decision": action,
        "bundle_permission": "ENABLE_IN_BRANCH_LOCAL_SHADOW_BUNDLE",
        "source_guard_requirement": (
            "USE_GLOBAL_SOURCE_GUARD_AND_DENOMINATOR_SCOPE"
            if row.get("outside_gbpjpy_xauusd_current_branch_box")
            else "USE_COMPONENT_SCOPE_GUARD"
        ),
        "bundle_priority_score": bundle_score(row),
        "live_effect": False,
    }


def classify_source_guard(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("source_materialization_execution_status") or "")
    result_class = str(row.get("materialization_proxy_r_style_result_class") or "")
    if status == "SOURCE_MATERIALIZATION_CURRENT_SOURCE_N20_HORIZON_FAILCLOSED":
        if result_class == "PROXY_R_INTERVAL_ALL_NEGATIVE":
            decision = "SOURCE_GUARD_FAILCLOSED_REPAIR_THEN_KILL_IF_NEGATIVE_PERSISTS"
            permission = "BLOCK_SOURCE_ENABLE_REPAIR_THEN_KILL_IF_UNCHANGED"
        elif result_class == "PROXY_R_INTERVAL_ALL_POSITIVE":
            decision = "SOURCE_GUARD_FAILCLOSED_REPAIR_THEN_ALLOW_GUARDED_ENABLE"
            permission = "BLOCK_SOURCE_ENABLE_UNTIL_HORIZON_REPAIR"
        else:
            decision = "SOURCE_GUARD_FAILCLOSED_REPAIR_THEN_RESCORE_INTERVAL"
            permission = "BLOCK_SOURCE_ENABLE_REPAIR_THEN_RESCORE"
        guard_mode = "FAILCLOSED_HORIZON_GUARD"
        repair_required = True
    elif result_class == "PROXY_R_INTERVAL_ALL_POSITIVE":
        decision = "SOURCE_GUARD_ALLOW_PROXY_SCORE_WITH_SCOPE_GUARD"
        permission = "ALLOW_GUARDED_PROXY_SCORING"
        guard_mode = "EXPANDED_PROXY_SCOPE_GUARD"
        repair_required = False
    elif result_class == "PROXY_R_INTERVAL_ALL_NEGATIVE":
        decision = "SOURCE_GUARD_REJECT_PROXY_UNTIL_EXACT_SOURCE_REPAIR"
        permission = "DO_NOT_ENABLE_SOURCE_DEPENDENT_RULE"
        guard_mode = "NEGATIVE_PROXY_SOURCE_GUARD"
        repair_required = True
    else:
        decision = "SOURCE_GUARD_SCORE_PROXY_WITH_SCOPE_GUARD"
        permission = "SCORE_WITH_GUARD_NO_UNCONDITIONAL_ENABLE"
        guard_mode = "AMBIGUOUS_PROXY_SCOPE_GUARD"
        repair_required = False

    return {
        "bundle_surface": BUNDLE_SURFACE,
        "bundle_stage": "SOURCE_GUARD",
        "bundle_decision": decision,
        "bundle_permission": permission,
        "source_guard_mode": guard_mode,
        "source_repair_required": repair_required,
        "bundle_priority_score": bundle_score(row, "materialization_proxy_score"),
        "live_effect": False,
    }


def classify_score_control(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("code_candidate_status") or "")
    if status == "ENTRY_CODE_SCORE_WITH_STATUS_QUO_CONTROL":
        decision = "CONTROL_SCORE_ENTRY_GEOMETRY_AGAINST_STATUS_QUO"
    elif status in {"BRANCH_CODE_REDESIGN_FILLABILITY_THEN_SPEC", "BRANCH_CODE_REDESIGN_RETEST_BEFORE_KEEP"}:
        decision = "CONTROL_SCORE_FILLABILITY_REDESIGN_BEFORE_ENABLE"
    elif status == "MARKET_GAP_CODE_SCORE_ENTRY_WITH_CONTROL":
        decision = "CONTROL_SCORE_MARKET_GAP_ENTRY_AGAINST_STATUS_QUO"
    elif status in {"AVOID_CODE_SCORE_FILTER_WITH_INVERSE_CONTROL", "MARKET_GAP_CODE_SCORE_AVOID_INVERSE_WITH_CONTROL"}:
        decision = "CONTROL_SCORE_AVOID_FILTER_WITH_INVERSE_CONTROL"
    elif status.startswith("SCORER_CODE_ADD"):
        decision = "CONTROL_SCORE_SCORER_COMPONENT_PATCH_BEFORE_ENABLE"
    else:
        decision = "CONTROL_PRESERVE_SCORER_CONTEXT_ONLY"
    return {
        "bundle_surface": BUNDLE_SURFACE,
        "bundle_stage": "SCORE_WITH_CONTROL",
        "bundle_decision": decision,
        "bundle_permission": "CONTROL_REQUIRED_BEFORE_ENABLE",
        "control_status": status,
        "bundle_priority_score": bundle_score(row),
        "live_effect": False,
    }


def classify_denominator_guard(row: dict[str, Any]) -> dict[str, Any]:
    status = str(row.get("code_candidate_status") or "")
    if status == "CONCENTRATION_CODE_FORCE_OUTSIDE_BRANCH_DENOMINATOR_GUARD":
        decision = "DENOMINATOR_GUARD_FORCE_OUTSIDE_BRANCH_SCOPE"
    elif status == "CONCENTRATION_CODE_SOURCE_ROOT_COVERAGE_GUARD":
        decision = "DENOMINATOR_GUARD_SOURCE_ROOT_COVERAGE"
    elif status == "CONCENTRATION_CODE_KEEP_MECHANISM_AND_DENOMINATOR_GUARD":
        decision = "DENOMINATOR_GUARD_KEEP_MECHANISM_AND_DENOMINATOR"
    else:
        decision = "DENOMINATOR_GUARD_CONTEXT_COVERAGE"
    return {
        "bundle_surface": BUNDLE_SURFACE,
        "bundle_stage": "DENOMINATOR_GUARD",
        "bundle_decision": decision,
        "bundle_permission": "DENOMINATOR_GUARD_REQUIRED",
        "guard_status": status,
        "bundle_priority_score": bundle_score(row),
        "live_effect": False,
    }


def classify_horizon_repair_action(row: dict[str, Any]) -> dict[str, Any]:
    result_class = str(row.get("materialization_proxy_r_style_result_class") or "")
    failclosed_n = to_int(row.get("current_failclosed_flagged_n"))
    targetable_n = to_int(row.get("current_targetable_flagged_n"))
    source_n = to_int(row.get("current_source_flagged_n"))
    if result_class == "PROXY_R_INTERVAL_ALL_NEGATIVE":
        action = "HORIZON_REPAIR_REBUILD_AND_KILL_IF_NEGATIVE_PERSISTS"
        permission = "REPAIR_THEN_KILL_IF_INTERVAL_REMAINS_NEGATIVE"
    elif result_class == "PROXY_R_INTERVAL_ALL_POSITIVE":
        action = "HORIZON_REPAIR_REBUILD_AND_ALLOW_GUARDED_ENABLE"
        permission = "REPAIR_THEN_ALLOW_IF_INTERVAL_REMAINS_POSITIVE"
    else:
        action = "HORIZON_REPAIR_REBUILD_AND_RESCORE_INTERVAL"
        permission = "REPAIR_THEN_RESCORE_AMBIGUOUS_INTERVAL"
    priority = clamp01(0.40 + min(0.30, failclosed_n / 100.0) + min(0.20, max(0, source_n - targetable_n) / 100.0))
    return {
        "bundle_surface": BUNDLE_SURFACE,
        "bundle_stage": "HORIZON_FAILCLOSED_REPAIR_ACTION",
        "bundle_decision": action,
        "bundle_permission": permission,
        "repair_action": "REBUILD_TARGETABLE_HORIZON_EVENTS_FROM_CURRENT_SOURCE_FLAGS",
        "repair_reason": row.get("materialization_exact_missing_reason"),
        "repair_priority_score": priority,
        "live_effect": False,
    }
