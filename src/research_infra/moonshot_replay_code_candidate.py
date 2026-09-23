"""Research-only code/spec candidate helpers for moonshot replay rows.

These helpers translate replay/acquisition result rows into mechanical
branch-local rule specs. They do not place orders, read broker state, mutate
live config, or assert validation/live-readiness.
"""

from __future__ import annotations

from typing import Any


CODE_SURFACE = "src/research_infra/moonshot_replay_code_candidate.py"
SHADOW_ONLY_BOUNDARY = (
    "branch_local_research_shadow_spec_only_no_live_behavior_change_no_validation_or_promotion_claim"
)


def to_float(value: Any) -> float | None:
    """Convert loose numeric values to float without raising."""

    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _score_band(value: float | None) -> str:
    if value is None:
        return "CODE_SCORE_NO_SCALAR"
    if value >= 0.55:
        return "CODE_SCORE_HIGH"
    if value >= 0.25:
        return "CODE_SCORE_MODERATE"
    if value >= 0.0:
        return "CODE_SCORE_REPAIRABLE"
    return "CODE_SCORE_WEAK"


def _interval_gate(result_class: str | None) -> str:
    text = str(result_class or "")
    if "ALL_POSITIVE" in text:
        return "PROXY_INTERVAL_POSITIVE"
    if "ALL_NEGATIVE" in text:
        return "PROXY_INTERVAL_NEGATIVE"
    if "CONTROL_NEUTRAL" in text:
        return "PROXY_INTERVAL_CONTROL"
    if "STRADDLES_ZERO" in text:
        return "PROXY_INTERVAL_AMBIGUOUS"
    return "PROXY_INTERVAL_NO_SCALAR"


def _mechanical_scope(row: dict[str, Any]) -> str:
    return (
        f"symbol={row.get('symbol')}|session={row.get('route_session')}|"
        f"horizon={row.get('horizon_id')}|primitive={row.get('primitive_flag')}"
    )


def _common(kind: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "code_candidate_kind": kind,
        "code_surface": CODE_SURFACE,
        "claim_boundary": SHADOW_ONLY_BOUNDARY,
        "mechanical_scope_key": _mechanical_scope(row),
        "required_feature_fields": [
            "symbol",
            "route_session",
            "horizon_id",
            "primitive_flag",
            "session_bucket",
        ],
    }


def entry_variant_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one entry replay row into a branch-local entry spec decision."""

    decision = str(row.get("entry_replay_decision") or "")
    interval_gate = _interval_gate(row.get("entry_proxy_r_style_result_class"))
    score = to_float(row.get("entry_replay_proxy_score"))
    variant = str(row.get("entry_variant") or "")
    if decision == "ENTRY_REPLAY_ACCEPT_CHALLENGER" and interval_gate == "PROXY_INTERVAL_POSITIVE":
        status = "ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC"
        action = "emit_entry_variant_shadow_rule"
        runtime_effect = "shadow_entry_geometry_candidate"
    elif decision == "ENTRY_REPLAY_SCORE_CHALLENGER_WITH_CONTROL":
        status = "ENTRY_CODE_SCORE_WITH_STATUS_QUO_CONTROL"
        action = "emit_entry_variant_shadow_rule_and_control"
        runtime_effect = "shadow_score_only_with_status_quo_control"
    elif decision == "ENTRY_REPLAY_CONTROL_ONLY" or variant == "STATUS_QUO_NO_BRANCH_CONTROL":
        status = "ENTRY_CODE_CONTROL_ONLY"
        action = "preserve_status_quo_control_row"
        runtime_effect = "control_only"
    else:
        status = "ENTRY_CODE_REPAIR_OR_STRESS_BEFORE_SPEC"
        action = "repair_entry_geometry_or_source_before_shadow_rule"
        runtime_effect = "no_rule_until_repaired"
    return {
        **_common("ENTRY_VARIANT_RULE", row),
        "entry_variant": variant,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "shadow_runtime_effect": runtime_effect,
        "proxy_interval_gate": interval_gate,
        "proxy_score": score,
        "proxy_score_band": _score_band(score),
        "mechanical_rule_expression": (
            f"when {_mechanical_scope(row)} is active, evaluate entry_variant={variant} "
            "against status_quo_control before any live effect"
        ),
        "acceptance_condition": (
            "positive_proxy_interval_and_replay_accept_decision"
            if status == "ENTRY_CODE_IMPLEMENT_SHADOW_RULE_SPEC"
            else "control_or_score_with_control_required"
        ),
    }


def avoid_policy_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one avoid/inverse replay row into a rule/control spec."""

    decision = str(row.get("policy_variant_replay_decision") or "")
    variant_type = str(row.get("policy_variant_type") or "")
    interval_gate = _interval_gate(row.get("policy_proxy_r_style_result_class"))
    score = to_float(row.get("policy_variant_proxy_score"))
    if decision == "AVOID_POLICY_REPLAY_ACCEPT_FILTER" and interval_gate == "PROXY_INTERVAL_POSITIVE":
        status = "AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC"
        action = "emit_no_trade_veto_shadow_filter"
        runtime_effect = "shadow_no_trade_veto_candidate"
    elif decision == "AVOID_POLICY_REPLAY_SCORE_FILTER_WITH_INVERSE_CONTROL":
        status = "AVOID_CODE_SCORE_FILTER_WITH_INVERSE_CONTROL"
        action = "emit_avoid_filter_with_inverse_sibling_control"
        runtime_effect = "shadow_filter_score_only"
    elif decision == "INVERSE_POLICY_REPLAY_SCORE_FADE_CONTROL":
        status = "INVERSE_CODE_CONTROL_ONLY"
        action = "preserve_inverse_or_fade_control"
        runtime_effect = "control_only"
    else:
        status = "AVOID_CODE_REPAIR_OR_REJECT"
        action = "repair_policy_source_or_reject_policy_variant"
        runtime_effect = "no_rule_until_repaired"
    return {
        **_common("AVOID_INVERSE_POLICY_RULE", row),
        "policy_variant_type": variant_type,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "shadow_runtime_effect": runtime_effect,
        "proxy_interval_gate": interval_gate,
        "proxy_score": score,
        "proxy_score_band": _score_band(score),
        "sibling_avoid_filter_score": row.get("sibling_avoid_filter_score"),
        "sibling_inverse_or_fade_score": row.get("sibling_inverse_or_fade_score"),
        "mechanical_rule_expression": (
            f"when {_mechanical_scope(row)} is active, evaluate policy_variant={variant_type} "
            "as avoid/inverse shadow control before any live effect"
        ),
        "acceptance_condition": (
            "accepted_avoid_filter_positive_proxy_interval"
            if status == "AVOID_CODE_IMPLEMENT_SHADOW_FILTER_SPEC"
            else "sibling_control_required_or_control_only"
        ),
    }


def market_gap_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one market-gap replay/acquisition row into an implementation spec."""

    decision = str(row.get("market_gap_replay_decision") or "")
    interval_gate = _interval_gate(row.get("market_gap_proxy_r_style_result_class"))
    score = to_float(row.get("market_gap_decision_score"))
    if decision == "IMPLEMENT_ENTRY_GEOMETRY_CHALLENGER_CANDIDATE":
        status = "MARKET_GAP_CODE_IMPLEMENT_ENTRY_GEOMETRY_SPEC"
        action = "emit_market_gap_entry_geometry_shadow_spec"
    elif decision == "IMPLEMENT_AVOID_FILTER_CANDIDATE":
        status = "MARKET_GAP_CODE_IMPLEMENT_AVOID_FILTER_SPEC"
        action = "emit_market_gap_avoid_filter_shadow_spec"
    elif decision == "SCORE_ENTRY_GEOMETRY_WITH_CONTROL_BEFORE_IMPLEMENT":
        status = "MARKET_GAP_CODE_SCORE_ENTRY_WITH_CONTROL"
        action = "emit_entry_geometry_shadow_spec_with_control"
    elif decision == "SCORE_AVOID_INVERSE_POLICY_WITH_CONTROL":
        status = "MARKET_GAP_CODE_SCORE_AVOID_INVERSE_WITH_CONTROL"
        action = "emit_avoid_inverse_shadow_spec_with_control"
    else:
        status = "MARKET_GAP_CODE_SOURCE_MATERIALIZATION_REQUIRED"
        action = "materialize_or_reconstruct_source_denominator_then_rescore"
    return {
        **_common("MARKET_GAP_RULE", row),
        "market_gap_replay_decision": decision,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "proxy_interval_gate": interval_gate,
        "proxy_score": score,
        "proxy_score_band": _score_band(score),
        "outside_gbpjpy_xauusd_current_branch_box": bool(row.get("outside_gbpjpy_xauusd_current_branch_box")),
        "mechanical_rule_expression": (
            f"market_gap_combo={row.get('market_gap_combo_id')} maps {_mechanical_scope(row)} "
            f"to {action}"
        ),
    }


def source_materialization_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one source-acquisition row into an active materialization spec."""

    status_text = str(row.get("source_acquisition_status") or "")
    needed = int(to_float(row.get("source_rows_needed_to_n20")) or 0)
    if "HIGH_PRIORITY" in status_text or "NEAR_N20" in status_text:
        status = "SOURCE_CODE_MATERIALIZE_HIGH_PRIORITY"
        action = "search_reconstruct_or_extract_rows_to_n20_now"
    elif "OUTSIDE_BRANCH" in status_text:
        status = "SOURCE_CODE_MATERIALIZE_OUTSIDE_BRANCH_DENOMINATOR"
        action = "expand_outside_branch_symbol_session_horizon_source"
    elif "CURRENT_CONCENTRATION" in status_text:
        status = "SOURCE_CODE_MATERIALIZE_CURRENT_CONCENTRATION_CONTROL"
        action = "materialize_current_branch_control_denominator"
    else:
        status = "SOURCE_CODE_REPLAY_READY_OR_CONTEXT"
        action = "preserve_replay_ready_source_context"
    return {
        **_common("SOURCE_MATERIALIZATION_RULE", row),
        "code_candidate_status": status,
        "code_candidate_action": action,
        "source_rows_needed_to_n20": needed,
        "proxy_interval_gate": _interval_gate(row.get("source_acquisition_proxy_r_style_result_class")),
        "proxy_score": to_float(row.get("source_replay_priority_score")),
        "proxy_score_band": _score_band(to_float(row.get("source_replay_priority_score"))),
        "mechanical_rule_expression": (
            f"for {_mechanical_scope(row)}, acquire_or_reconstruct {needed} additional flagged rows "
            "from owned/current/free historical routes before branch implementation"
        ),
    }


def branch_decision_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one branch keep/kill/redesign row into system-transfer code action."""

    decision = str(row.get("keep_kill_redesign_implement_replay_decision") or "")
    midpoint = to_float(row.get("rstyle_midpoint_mean"))
    if decision == "IMPLEMENT_MARKET_ENTRY_CHALLENGER_BRANCH_CANDIDATE":
        status = "BRANCH_CODE_IMPLEMENT_MARKET_ENTRY_COMPARATOR_SPEC"
        action = "emit_market_entry_comparator_shadow_spec"
    elif decision == "KEEP_PROXY_CHALLENGER_FOR_BRANCH_LOCAL_SCORER":
        status = "BRANCH_CODE_KEEP_PROXY_SCORER_SPEC"
        action = "emit_branch_local_proxy_scorer_spec"
    elif decision == "REDESIGN_FILLABILITY_THEN_IMPLEMENT_CHALLENGER_CANDIDATE":
        status = "BRANCH_CODE_REDESIGN_FILLABILITY_THEN_SPEC"
        action = "emit_fillability_redesign_shadow_spec"
    elif decision == "REDESIGN_FILLABILITY_OR_RETEST_BEFORE_KEEP":
        status = "BRANCH_CODE_REDESIGN_RETEST_BEFORE_KEEP"
        action = "emit_retest_redesign_control_spec"
    elif decision == "KILL_OR_IMPLEMENT_AVOID_FILTER_FROM_FAILURE_CAUSE":
        status = "BRANCH_CODE_IMPLEMENT_AVOID_FROM_FAILURE_CAUSE"
        action = "emit_failure_cause_avoid_filter_spec"
    elif decision == "KILL_LOW_PRIORITY_OR_REPAIR_BEFORE_KEEP":
        status = "BRANCH_CODE_REPAIR_OR_KILL_LOW_PRIORITY"
        action = "repair_source_or_preserve_kill_reason"
    else:
        status = "BRANCH_CODE_PRESERVE_PROVENANCE_ONLY"
        action = "exclude_from_scalar_implementation_and_preserve_binding"
    return {
        **_common("BRANCH_SYSTEM_RULE", row),
        "branch_queue_id": row.get("branch_queue_id"),
        "target_stop_contract_id": row.get("target_stop_contract_id"),
        "branch_replay_decision": decision,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "proxy_score": midpoint,
        "proxy_score_band": _score_band(midpoint),
        "target_stop_result": row.get("target_stop_result"),
        "mechanical_rule_expression": (
            f"branch={row.get('branch_queue_id')} target_stop={row.get('target_stop_contract_id')} "
            f"maps replay_decision={decision} to {action}"
        ),
    }


def scorer_patch_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one scorer-spec row into a code patch candidate."""

    decision = str(row.get("scorer_spec_replay_decision") or "")
    candidate_type = str(row.get("implementation_candidate_type") or "")
    if decision == "IMPLEMENT_BRANCH_LOCAL_SCORER_SPEC_CANDIDATE":
        status = "SCORER_CODE_ADD_RULE_COMPONENT"
        action = "add_branch_local_replay_rule_component"
    elif decision == "IMPLEMENT_AVOID_OR_INVERSE_SCORER_SPEC_CANDIDATE":
        status = "SCORER_CODE_ADD_AVOID_INVERSE_COMPONENT"
        action = "add_avoid_inverse_rule_component"
    elif decision == "IMPLEMENT_SCORER_SPEC_WITH_SOURCE_OR_FILLABILITY_REPAIR_GUARD":
        status = "SCORER_CODE_ADD_REPAIR_GUARDED_COMPONENT"
        action = "add_component_with_source_or_fillability_guard"
    elif decision == "KEEP_CONCENTRATION_TEST_IN_SCORER_AND_FORCE_OUTSIDE_BRANCH_DENOMINATOR_CHECK":
        status = "SCORER_CODE_ADD_CONCENTRATION_DENOMINATOR_GUARD"
        action = "add_outside_branch_denominator_guard"
    else:
        status = "SCORER_CODE_PRESERVE_CONTEXT_ONLY"
        action = "preserve_context_without_scorer_component"
    return {
        "code_candidate_kind": "SCORER_PATCH_SPEC",
        "code_surface": CODE_SURFACE,
        "claim_boundary": SHADOW_ONLY_BOUNDARY,
        "implementation_candidate_type": candidate_type,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "implementation_rows_for_type": row.get("implementation_rows_for_type"),
        "implementation_score_mean_for_type": row.get("implementation_score_mean_for_type"),
        "required_controls": row.get("required_controls"),
        "mechanical_rule_expression": (
            f"candidate_type={candidate_type} maps scorer_replay_decision={decision} to {action}"
        ),
    }


def concentration_guard_code_candidate(row: dict[str, Any]) -> dict[str, Any]:
    """Translate one concentration replay row into a denominator guard action."""

    decision = str(row.get("concentration_replay_decision") or "")
    if decision == "CONCENTRATION_REPLAY_DENOMINATOR_ARTIFACT_CONFIRMED":
        status = "CONCENTRATION_CODE_FORCE_OUTSIDE_BRANCH_DENOMINATOR_GUARD"
        action = "require_outside_branch_market_gap_rows_before_concentration_claim"
    elif decision == "CONCENTRATION_REPLAY_REAL_MECHANISM_AND_ARTIFACT_BOTH_TRUE":
        status = "CONCENTRATION_CODE_KEEP_MECHANISM_AND_DENOMINATOR_GUARD"
        action = "keep_current_concentration_but_force_counterdenominator"
    elif decision == "CONCENTRATION_REPLAY_SOURCE_ROOT_COVERAGE_TESTED":
        status = "CONCENTRATION_CODE_SOURCE_ROOT_COVERAGE_GUARD"
        action = "preserve_source_root_coverage_check"
    else:
        status = "CONCENTRATION_CODE_CONTEXT_GUARD"
        action = "preserve_current_branch_coverage_context"
    return {
        **_common("CONCENTRATION_DENOMINATOR_GUARD", row),
        "concentration_replay_decision": decision,
        "code_candidate_status": status,
        "code_candidate_action": action,
        "current_branch_rows": row.get("current_branch_rows"),
        "market_gap_combo_rows": row.get("market_gap_combo_rows"),
        "full_tick_transfer_rows": row.get("full_tick_transfer_rows"),
        "mechanical_rule_expression": (
            f"axis={row.get('test_axis')} symbol={row.get('symbol')} session={row.get('route_session')} "
            f"horizon={row.get('horizon_id')} requires {action}"
        ),
    }
