"""Apply default-off denominator scorers to implementation decision rows."""

from __future__ import annotations

from typing import Any

from src.research_infra.moonshot_branch_local_denominator_default_off_scorers import score_default_off_event


DEFAULT_OFF_APPLICATION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_default_off_application.py"
)


def _to_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "default_off_application_surface": DEFAULT_OFF_APPLICATION_SURFACE,
        "input_default_off_implementation_row_id": row.get("default_off_implementation_row_id"),
        "input_detail_execution_row_id": row.get("input_detail_execution_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "detail_execution_family": row.get("detail_execution_family"),
        "detail_execution_status": row.get("detail_execution_status"),
        "source_default_off_implementation_status": row.get("default_off_implementation_status"),
        "source_default_off_decision_result": row.get("decision_result"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "candidate_use_allowed_now": bool(row.get("candidate_use_allowed_now")),
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def _event_from(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
    }


def default_off_application_decision(
    implementation_row: dict[str, Any],
    registration_row: dict[str, Any] | None = None,
    exact_row: dict[str, Any] | None = None,
    source_row: dict[str, Any] | None = None,
    horizon_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the concrete application decision for one implementation row."""

    registration = registration_row or {}
    exact = exact_row or {}
    source = source_row or {}
    horizon = horizon_row or {}
    status = implementation_row.get("default_off_implementation_status")
    event_score = score_default_off_event(_event_from(implementation_row), registration) if registration else {}
    score = event_score.get("default_off_scorer_event_score")

    application_status = "DEFAULT_OFF_APPLICATION_RECHECK"
    application_decision_class = "RECHECK"
    no_runtime_score_reason = "RECHECK_APPLICATION_INPUTS"
    scorer_surface_consumed = False
    exact_control_build_still_required = False
    repair_or_redesign_required = False
    current_claim_rejection_audit_required = False
    missed_opportunity_audit_status = "NOT_REQUIRED"
    implementation_implication = "recheck_before_any_branch_local_candidate"
    next_same_resource_action = implementation_row.get("next_same_resource_action")
    current_claim_rejection_basis = None
    underlying_mechanism_preserved_as = None
    could_make_current_claim_work = None

    if status == "DEFAULT_OFF_BLOCKED_EXACT_CONTROL_BUILD_REQUIRED":
        exact_status = exact.get("exact_control_expansion_status")
        if exact_status == "EXACT_CONTROL_EXPANSION_TARGET_EXACT_UNAVAILABLE_BUILD_REQUIRED":
            application_status = "DEFAULT_OFF_APPLICATION_EXACT_TARGET_CONTROL_BUILD_REQUIRED_NO_RUNTIME_SCORE"
            no_runtime_score_reason = "exact_target_control_denominator_not_built_to_n20"
        else:
            application_status = "DEFAULT_OFF_APPLICATION_EXACT_SCOPE_CONTROL_BUILD_REQUIRED_NO_RUNTIME_SCORE"
            no_runtime_score_reason = "exact_scope_control_denominator_not_built_to_n20"
        application_decision_class = "EXACT_CONTROL_BUILD_REQUIRED"
        exact_control_build_still_required = True
        implementation_implication = "withhold_scalar_and_build_exact_control_denominator"
        next_same_resource_action = exact.get("exact_control_expansion_action") or implementation_row.get(
            "default_off_implementation_action"
        )
    elif status == "DEFAULT_OFF_GUARDED_SCOPE_SCORER_CANDIDATE":
        application_status = "DEFAULT_OFF_APPLICATION_GUARDED_SCOPE_SCORE_READY_EXACT_BUILD_OPEN"
        application_decision_class = "DEFAULT_OFF_SCORE_READY_RESEARCH_ONLY"
        no_runtime_score_reason = None
        scorer_surface_consumed = True
        exact_control_build_still_required = True
        implementation_implication = "branch_local_default_off_guarded_scope_scorer_candidate_exact_build_open"
        next_same_resource_action = "score_matching_scope_default_off_and_continue_exact_scope_denominator_build"
    elif status == "DEFAULT_OFF_HORIZON_REPAIR_RESCORER_CANDIDATE":
        application_status = "DEFAULT_OFF_APPLICATION_HORIZON_REPAIR_SCORE_READY"
        application_decision_class = "DEFAULT_OFF_SCORE_READY_RESEARCH_ONLY"
        no_runtime_score_reason = None
        scorer_surface_consumed = True
        repair_or_redesign_required = True
        implementation_implication = "branch_local_default_off_horizon_repair_rescorer_candidate"
        next_same_resource_action = "score_repaired_horizon_targetability_definition_and_preserve_repair_limits"
    elif status == "DEFAULT_OFF_HORIZON_REDESIGN_CANDIDATE":
        application_status = "DEFAULT_OFF_APPLICATION_HORIZON_REDESIGN_SCORE_READY"
        application_decision_class = "DEFAULT_OFF_SCORE_READY_RESEARCH_ONLY"
        no_runtime_score_reason = None
        scorer_surface_consumed = True
        repair_or_redesign_required = True
        implementation_implication = "branch_local_default_off_horizon_targetability_redesign_candidate"
        next_same_resource_action = "score_redesigned_horizon_targetability_definition_and_preserve_repair_limits"
    elif status == "DEFAULT_OFF_HORIZON_KILL_CHECK_REPAIR_OPEN":
        application_status = "DEFAULT_OFF_APPLICATION_HORIZON_REPAIR_GATE_HELD_NO_RUNTIME_SCORE"
        application_decision_class = "REPAIR_GATE_HELD"
        no_runtime_score_reason = "horizon_targetability_repair_check_open"
        scorer_surface_consumed = True
        repair_or_redesign_required = True
        missed_opportunity_audit_status = "REPAIR_GATE_HELD_AUDIT_REQUIRED_BEFORE_CURRENT_CLAIM_REJECTION"
        implementation_implication = "repair_horizon_targetability_before_rejecting_current_claim"
        next_same_resource_action = "repair_targetability_then_retest_current_horizon_claim"
    elif status == "DEFAULT_OFF_KILLED_SOURCE_PROXY_NEGATIVE_NO_CONTRADICTION":
        application_status = "DEFAULT_OFF_APPLICATION_SOURCE_PROXY_CURRENT_CLAIM_REJECTED_AUDIT_PRESERVED"
        application_decision_class = "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED"
        no_runtime_score_reason = "negative_source_proxy_without_current_exact_contradiction"
        current_claim_rejection_audit_required = True
        missed_opportunity_audit_status = "SOURCE_PROXY_REJECTION_AUDIT_PRESERVED"
        current_claim_rejection_basis = source.get("source_completeness_status") or "terminal_source_proxy_negative"
        underlying_mechanism_preserved_as = (
            "avoid_filter_candidate_or_source_confidence_context_or_market_session_redesign_input"
        )
        could_make_current_claim_work = (
            "exact_source_contradiction_repair_positive_proxy_split_market_session_isolation_or_inverse_use_case"
        )
        implementation_implication = "do_not_use_current_source_proxy_claim_as_scorer_preserve_avoid_redesign_intelligence"
        next_same_resource_action = "preserve_audit_and_reopen_only_if_exact_source_or_proxy_split_contradicts_current_rejection"
    elif status == "DEFAULT_OFF_TERMINAL_HORIZON_KILL_PRESERVED":
        application_status = "DEFAULT_OFF_APPLICATION_HORIZON_CURRENT_CLAIM_REJECTED_AUDIT_PRESERVED"
        application_decision_class = "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED"
        no_runtime_score_reason = "terminal_horizon_targetability_failure_under_current_repair_evidence"
        current_claim_rejection_audit_required = True
        missed_opportunity_audit_status = "HORIZON_REJECTION_AUDIT_PRESERVED"
        current_claim_rejection_basis = horizon.get("horizon_detail_status") or "terminal_horizon_targetability_failure"
        underlying_mechanism_preserved_as = "horizon_selector_negative_context_or_targetability_redesign_input"
        could_make_current_claim_work = "different_horizon_target_family_market_session_split_or_repaired_targetability_source"
        implementation_implication = "do_not_use_current_horizon_claim_as_scorer_preserve_targetability_failure_intelligence"
        next_same_resource_action = "preserve_audit_and_convert_to_horizon_selector_or_redesign_context"

    return {
        **_base(implementation_row),
        "input_default_off_scorer_registration_row_id": registration.get("default_off_scorer_registration_row_id"),
        "matched_default_off_scorer_kind": registration.get("default_off_scorer_kind"),
        "matched_default_off_scorer_score": registration.get("default_off_scorer_score"),
        "default_off_scorer_event_status": event_score.get("default_off_scorer_event_status"),
        "default_off_application_status": application_status,
        "default_off_application_decision_class": application_decision_class,
        "default_off_application_score": score,
        "scorer_surface_consumed": scorer_surface_consumed,
        "exact_control_build_still_required": exact_control_build_still_required,
        "repair_or_redesign_required": repair_or_redesign_required,
        "current_claim_rejection_audit_required": current_claim_rejection_audit_required,
        "missed_opportunity_audit_status": missed_opportunity_audit_status,
        "no_runtime_score_reason": no_runtime_score_reason,
        "current_claim_rejection_basis": current_claim_rejection_basis,
        "underlying_mechanism_preserved_as": underlying_mechanism_preserved_as,
        "could_make_current_claim_work": could_make_current_claim_work,
        "implementation_implication": implementation_implication,
        "next_same_resource_action": next_same_resource_action,
        "exact_control_expansion_status": exact.get("exact_control_expansion_status"),
        "source_completeness_status": source.get("source_completeness_status"),
        "horizon_detail_status": horizon.get("horizon_detail_status"),
    }


def exact_control_blocker_decision(
    implementation_row: dict[str, Any],
    exact_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Preserve exact-control blocker details for rows with no allowed scalar."""

    exact = exact_row or {}
    exact_status = exact.get("exact_control_expansion_status")
    if exact_status == "EXACT_CONTROL_EXPANSION_TARGET_EXACT_UNAVAILABLE_BUILD_REQUIRED":
        blocker_status = "EXACT_CONTROL_APPLICATION_TARGET_BUILD_REQUIRED_NO_RUNTIME_SCORE"
    else:
        blocker_status = "EXACT_CONTROL_APPLICATION_SCOPE_BUILD_REQUIRED_NO_RUNTIME_SCORE"
    return {
        **_base(implementation_row),
        "exact_control_application_blocker_status": blocker_status,
        "exact_control_expansion_status": exact_status,
        "exact_control_expansion_action": exact.get("exact_control_expansion_action"),
        "exact_control_member_count": _to_int(exact.get("exact_control_member_count")),
        "best_available_proxy_relation": exact.get("best_available_proxy_relation"),
        "best_available_proxy_member_count": _to_int(exact.get("best_available_proxy_member_count")),
        "best_proxy_rows_needed_to_n20": _to_int(exact.get("best_proxy_rows_needed_to_n20")),
        "target_action_rows": _to_int(exact.get("target_action_rows")),
        "target_underpowered_rows": _to_int(exact.get("target_underpowered_rows")),
        "default_off_permission": exact.get("default_off_permission"),
        "runtime_score_allowed": False,
        "blocker_consumption_decision": "build_exact_control_denominator_before_runtime_scalar_use",
    }


def scorer_application_decision(
    implementation_row: dict[str, Any],
    registration_row: dict[str, Any],
) -> dict[str, Any]:
    scored = score_default_off_event(_event_from(implementation_row), registration_row)
    if scored.get("default_off_scorer_event_status") == "DEFAULT_OFF_SCORER_EVENT_SCORE_EMITTED":
        status = "SCORER_APPLICATION_SCORE_EMITTED_DEFAULT_OFF"
    else:
        status = "SCORER_APPLICATION_GATE_HELD_NO_SCORE"
    return {
        **_base(implementation_row),
        "input_default_off_scorer_registration_row_id": registration_row.get("default_off_scorer_registration_row_id"),
        "default_off_scorer_kind": registration_row.get("default_off_scorer_kind"),
        "scorer_application_status": status,
        "default_off_scorer_event_status": scored.get("default_off_scorer_event_status"),
        "default_off_scorer_event_score": scored.get("default_off_scorer_event_score"),
        "runtime_score_allowed": False,
        "branch_local_default_off_score_available": scored.get("default_off_scorer_event_score") is not None,
    }


def current_claim_rejection_audit(
    implementation_row: dict[str, Any],
    source_row: dict[str, Any] | None = None,
    horizon_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit a rejected current claim while preserving mechanism intelligence."""

    source = source_row or {}
    horizon = horizon_row or {}
    family = implementation_row.get("detail_execution_family")
    if family in {"SOURCE_CONTRADICTION", "SOURCE_TERMINAL_KILL"}:
        status = "SOURCE_PROXY_CURRENT_CLAIM_REJECTED_NEGATIVE_PROXY_NO_CURRENT_EXACT_CONTRADICTION"
        tried = source.get("source_completeness_decision") or "source_proxy_negative_terminal_context_preserved"
        could_work = "exact_source_contradiction_repair_positive_proxy_split_market_session_isolation_or_inverse_use_case"
        preserve_as = "avoid_filter_candidate_source_confidence_context_redesign_input_or_source_capture_requirement"
        next_action = "deduplicate_or_merge_with_source_guard_and_reopen_only_on_exact_source_or_proxy_split_contradiction"
    else:
        status = "HORIZON_CURRENT_CLAIM_REJECTED_TARGETABILITY_FAILURE_CONTEXT_PRESERVED"
        tried = horizon.get("horizon_detail_decision") or "terminal_horizon_targetability_context_preserved"
        could_work = "different_horizon_target_family_market_session_split_or_repaired_targetability_source"
        preserve_as = "horizon_selector_negative_context_targetability_redesign_input_or_avoid_context_feature"
        next_action = "merge_into_horizon_selector_context_or_redesign_family_without_using_current_claim_as_scalar"
    return {
        **_base(implementation_row),
        "current_claim_rejection_audit_status": status,
        "claim_rejected_scope": "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED",
        "what_was_tried": tried,
        "what_could_make_it_work": could_work,
        "mechanism_or_intelligence_preserved_as": preserve_as,
        "redesign_inverse_avoid_or_merge_route": next_action,
        "source_completeness_status": source.get("source_completeness_status"),
        "horizon_detail_status": horizon.get("horizon_detail_status"),
        "proxy_contradiction_found": bool(source.get("proxy_contradiction_found")),
        "decision_proxy_r_style_result_class": source.get("decision_proxy_r_style_result_class"),
        "repair_upper_proxy_r_style_result_class": horizon.get("repair_upper_proxy_r_style_result_class"),
        "runtime_score_allowed": False,
    }
