"""Detail execution helpers for guarded scorer next-action rows."""

from __future__ import annotations

from typing import Any


DETAIL_EXECUTION_SURFACE = "src/research_infra/moonshot_branch_local_denominator_detail_execution.py"


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


def normalize_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text and text.lower() not in {"none", "null"} else None


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "detail_execution_surface": DETAIL_EXECUTION_SURFACE,
        "symbol": normalize_text(row.get("symbol")),
        "route_session": normalize_text(row.get("route_session")),
        "horizon_id": normalize_text(row.get("horizon_id")),
        "primitive_flag": normalize_text(row.get("primitive_flag")),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def detail_execution_from_next_action(row: dict[str, Any], evidence_row: dict[str, Any] | None = None) -> dict[str, Any]:
    evidence = evidence_row or {}
    lane = row.get("action_execution_lane")
    rows_needed = to_int(
        row.get("rows_needed_to_n20")
        or row.get("current_exact_gap_to_n20")
        or evidence.get("best_proxy_rows_needed_to_n20")
        or evidence.get("current_exact_gap_to_n20")
        or evidence.get("current_targetable_gap_to_n20")
    )
    has_registration = bool(row.get("matched_guarded_scorer_registration_row_id"))
    proxy_class = (
        row.get("decision_proxy_r_style_result_class")
        or evidence.get("materialization_proxy_r_style_result_class")
        or evidence.get("repair_upper_proxy_r_style_result_class")
    )
    evidence_status = evidence.get("denominator_source_acquisition_status")
    if lane == "EXACT_CONTROL_TARGET_BUILD":
        status = "DETAIL_EXEC_EXACT_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20"
        decision = "BUILD_EXACT_CONTROL_TARGET_DENOMINATOR_BEFORE_SCALAR_USE"
        family = "EXACT_CONTROL"
        can_use = False
        cause = (
            "exact target denominator unavailable in current rows; "
            f"best_proxy_member_count={to_int(evidence.get('best_available_proxy_member_count'))}; "
            f"member_rows_examined={to_int(evidence.get('member_rows_examined'))}; rows_needed_to_n20={rows_needed}"
        )
    elif lane == "EXACT_CONTROL_SCOPE_BUILD" and has_registration:
        status = "DETAIL_EXEC_EXACT_CONTROL_SCOPE_GUARDED_SCORER_REGISTERED_BUILD_OPEN_TARGETS_UNDER_N20"
        decision = "USE_GUARDED_SCOPE_PROXY_RESEARCH_ONLY_AND_CONTINUE_EXACT_CONTROL_BUILD"
        family = "EXACT_CONTROL"
        can_use = True
        cause = (
            "guarded scorer registered, but exact-control scope build remains open; "
            f"target_underpowered_rows={to_int(evidence.get('target_underpowered_rows') or row.get('rows_needed_to_n20'))}"
        )
    elif lane == "EXACT_CONTROL_SCOPE_BUILD":
        status = "DETAIL_EXEC_EXACT_CONTROL_SCOPE_BUILD_OPEN_TARGETS_UNDER_N20"
        decision = "BUILD_EXACT_CONTROL_SCOPE_DENOMINATOR_BEFORE_SCALAR_USE"
        family = "EXACT_CONTROL"
        can_use = False
        cause = f"exact scope denominator underpowered; target_underpowered_rows={to_int(evidence.get('target_underpowered_rows') or row.get('rows_needed_to_n20'))}"
    elif lane == "SOURCE_CONTRADICTION_CHECK":
        if proxy_class == "PROXY_R_INTERVAL_ALL_NEGATIVE" and not evidence.get("proxy_contradiction_found"):
            status = "DETAIL_EXEC_SOURCE_CONTRADICTION_NO_CONTRADICTION_NEGATIVE_PROXY_PERSISTS"
            decision = "KEEP_SOURCE_PROXY_KILL_UNLESS_EXACT_SOURCE_CONTRADICTS"
        elif evidence.get("proxy_contradiction_found"):
            status = "DETAIL_EXEC_SOURCE_CONTRADICTION_FOUND_REPAIR_REQUIRED"
            decision = "REPAIR_SOURCE_PROXY_KILL_WITH_EXACT_SOURCE_CONTRADICTION"
        else:
            status = "DETAIL_EXEC_SOURCE_CONTRADICTION_RECHECK_PROXY_CLASS"
            decision = "RECHECK_SOURCE_PROXY_KILL_CLASS"
        family = "SOURCE_CONTRADICTION"
        can_use = False
        cause = (
            "source exact rebuild contradiction check executed from current rows; "
            f"proxy_contradiction_found={bool(evidence.get('proxy_contradiction_found'))}; "
            f"current_exact_gap_to_n20={rows_needed}"
        )
    elif lane == "HORIZON_REPAIR":
        status = "DETAIL_EXEC_HORIZON_REPAIR_RESCORABLE_WITH_SOURCE_UPPER_BOUND"
        decision = "REBUILD_TARGETABLE_HORIZON_ROWS_AND_RESCORE"
        family = "HORIZON_REPAIR"
        can_use = False
        cause = (
            "horizon repair upper bound reaches computable source count; "
            f"repaired_targetable_upper_bound_n={to_int(evidence.get('repaired_targetable_upper_bound_n'))}"
        )
    elif lane == "HORIZON_REDESIGN":
        status = "DETAIL_EXEC_HORIZON_REDESIGN_REPAIR_BOUND_SCOREABLE"
        decision = "MATERIALIZE_REDESIGNED_TARGETABILITY_DEFINITION_AND_RESCORE"
        family = "HORIZON_REDESIGN"
        can_use = False
        cause = (
            "current targetability definition produces high fail-closed pressure; "
            f"current_failclosed_flagged_n={to_int(evidence.get('current_failclosed_flagged_n'))}; "
            f"repaired_targetable_upper_bound_n={to_int(evidence.get('repaired_targetable_upper_bound_n'))}"
        )
    elif lane == "HORIZON_KILL_CHECK":
        status = "DETAIL_EXEC_HORIZON_KILL_CHECK_REPAIR_OPEN"
        decision = "REPAIR_TARGETABILITY_AND_KILL_IF_NEGATIVE_PERSISTS"
        family = "HORIZON_KILL_CHECK"
        can_use = False
        cause = (
            "negative horizon proxy requires repair before terminal kill confirmation; "
            f"fail_if_negative_persists={bool(evidence.get('fail_if_negative_persists'))}"
        )
    else:
        status = "DETAIL_EXEC_RECHECK_ACTION_LANE"
        decision = "RECHECK_ACTION_EXECUTION_LANE"
        family = "RECHECK"
        can_use = False
        cause = "unmapped action execution lane"
    return {
        **_base(row),
        "detail_execution_family": family,
        "detail_execution_status": status,
        "detail_execution_decision": decision,
        "input_next_action_carryforward_row_id": row.get("guarded_scorer_next_action_carryforward_row_id"),
        "input_action_execution_row_id": row.get("action_execution_row_id"),
        "input_resolution_row_id": row.get("input_resolution_row_id"),
        "candidate_implementation_state": row.get("candidate_implementation_state"),
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "action_execution_lane": lane,
        "action_execution_status": row.get("action_execution_status"),
        "evidence_execution_row_id": evidence.get("denominator_source_acquisition_execution_row_id")
        or evidence.get("exact_control_scope_acquisition_execution_row_id"),
        "evidence_execution_status": evidence_status,
        "evidence_execution_decision": evidence.get("denominator_source_acquisition_decision"),
        "decision_proxy_score": row.get("decision_proxy_score") or evidence.get("best_proxy_score") or evidence.get("materialization_proxy_score") or evidence.get("source_proxy_score"),
        "decision_proxy_r_style_result_class": proxy_class,
        "best_available_proxy_member_count": evidence.get("best_available_proxy_member_count"),
        "best_available_proxy_relation": evidence.get("best_available_proxy_relation"),
        "best_proxy_rows_needed_to_n20": evidence.get("best_proxy_rows_needed_to_n20"),
        "best_proxy_r_style_result_class": evidence.get("best_proxy_r_style_result_class"),
        "member_rows_examined": evidence.get("member_rows_examined"),
        "exact_control_member_count": evidence.get("exact_control_member_count"),
        "control_member_relation_counts": evidence.get("control_member_relation_counts"),
        "control_member_relation_score_means": evidence.get("control_member_relation_score_means"),
        "target_action_rows": evidence.get("target_action_rows"),
        "target_underpowered_rows": evidence.get("target_underpowered_rows"),
        "target_exact_built_rows": evidence.get("target_exact_built_rows"),
        "target_proxy_n20_rows": evidence.get("target_proxy_n20_rows"),
        "proxy_contradiction_found": evidence.get("proxy_contradiction_found"),
        "current_targetable_flagged_n": evidence.get("current_targetable_flagged_n"),
        "current_source_flagged_n": evidence.get("current_source_flagged_n"),
        "current_failclosed_flagged_n": evidence.get("current_failclosed_flagged_n"),
        "best_expanded_targetable_count": evidence.get("best_expanded_targetable_count"),
        "materialization_status": evidence.get("materialization_status"),
        "materialization_proxy_scope": evidence.get("materialization_proxy_scope"),
        "materialization_proxy_r_style_result_class": evidence.get("materialization_proxy_r_style_result_class"),
        "repaired_targetable_upper_bound_n": evidence.get("repaired_targetable_upper_bound_n"),
        "repaired_targetable_upper_bound_reaches_n20": evidence.get("repaired_targetable_upper_bound_reaches_n20"),
        "repair_upper_proxy_r_style_result_class": evidence.get("repair_upper_proxy_r_style_result_class"),
        "repair_upper_proxy_r_style_lower": evidence.get("repair_upper_proxy_r_style_lower"),
        "repair_upper_proxy_r_style_midpoint": evidence.get("repair_upper_proxy_r_style_midpoint"),
        "repair_upper_proxy_r_style_upper": evidence.get("repair_upper_proxy_r_style_upper"),
        "source_minus_horizon_proxy_delta": evidence.get("source_minus_horizon_proxy_delta"),
        "rows_needed_to_n20": rows_needed,
        "matched_guarded_scorer_registration_row_id": row.get("matched_guarded_scorer_registration_row_id"),
        "matched_guarded_scorer_key": row.get("matched_guarded_scorer_key"),
        "candidate_use_allowed_now": can_use,
        "unconditional_scalar_use_allowed": False,
        "detail_failure_or_success_cause": cause,
        "next_same_resource_action": row.get("next_same_resource_action"),
        "next_execution_step": row.get("next_execution_step"),
        "terminal_decision": bool(row.get("terminal_decision")),
    }


def terminal_detail_from_kill(row: dict[str, Any]) -> dict[str, Any]:
    status = row.get("action_execution_status")
    if status == "ACTION_EXEC_TERMINAL_SOURCE_PROXY_KILL_PRESERVED":
        family = "SOURCE_TERMINAL_KILL"
        decision = "PRESERVE_SOURCE_PROXY_KILL_AS_FAILURE_OR_AVOID_INTELLIGENCE"
    elif status == "ACTION_EXEC_TERMINAL_HORIZON_KILL_PRESERVED":
        family = "HORIZON_TERMINAL_KILL"
        decision = "PRESERVE_HORIZON_KILL_AS_TARGETABILITY_FAILURE_INTELLIGENCE"
    else:
        family = "TERMINAL_RECHECK"
        decision = "RECHECK_TERMINAL_KILL_ROW"
    return {
        **_base(row),
        "detail_execution_family": family,
        "detail_execution_status": str(status).replace("ACTION_EXEC_", "DETAIL_EXEC_"),
        "detail_execution_decision": decision,
        "input_terminal_kill_carryforward_row_id": row.get("guarded_scorer_terminal_carryforward_row_id"),
        "input_terminal_kill_row_id": row.get("input_terminal_kill_row_id"),
        "input_resolution_row_id": row.get("input_resolution_row_id"),
        "candidate_implementation_state": row.get("candidate_implementation_state"),
        "keep_kill_redesign_decision": row.get("keep_kill_redesign_decision"),
        "decision_proxy_score": row.get("decision_proxy_score"),
        "decision_proxy_r_style_result_class": row.get("decision_proxy_r_style_result_class"),
        "candidate_use_allowed_now": False,
        "unconditional_scalar_use_allowed": False,
        "terminal_decision": True,
        "detail_failure_or_success_cause": row.get("next_execution_step"),
    }


def scope_detail_rollup(scope_key: tuple[Any, Any, Any, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    symbol, route_session, horizon_id, primitive_flag = scope_key
    family_counts: dict[str, int] = {}
    for row in rows:
        key = str(row.get("detail_execution_family"))
        family_counts[key] = family_counts.get(key, 0) + 1
    registered_rows = sum(1 for row in rows if row.get("matched_guarded_scorer_registration_row_id"))
    candidate_use_rows = sum(1 for row in rows if row.get("candidate_use_allowed_now"))
    terminal_rows = sum(1 for row in rows if row.get("terminal_decision"))
    if family_counts.get("SOURCE_CONTRADICTION"):
        status = "DETAIL_SCOPE_SOURCE_CONTRADICTION_KILL_CHECK"
    elif family_counts.get("HORIZON_REDESIGN") or family_counts.get("HORIZON_REPAIR") or family_counts.get(
        "HORIZON_KILL_CHECK"
    ):
        status = "DETAIL_SCOPE_HORIZON_REPAIR_OR_REDESIGN"
    elif registered_rows:
        status = "DETAIL_SCOPE_GUARDED_SCORER_REGISTERED_EXACT_BUILD_OPEN"
    elif family_counts.get("EXACT_CONTROL"):
        status = "DETAIL_SCOPE_EXACT_CONTROL_BUILD_OPEN"
    elif terminal_rows:
        status = "DETAIL_SCOPE_TERMINAL_KILL_PRESERVED"
    else:
        status = "DETAIL_SCOPE_CONTEXT_ONLY"
    return {
        "detail_execution_surface": DETAIL_EXECUTION_SURFACE,
        "symbol": normalize_text(symbol),
        "route_session": normalize_text(route_session),
        "horizon_id": normalize_text(horizon_id),
        "primitive_flag": normalize_text(primitive_flag),
        "scope_detail_status": status,
        "scope_row_count": len(rows),
        "family_counts": family_counts,
        "registered_guarded_scorer_rows": registered_rows,
        "candidate_use_allowed_rows": candidate_use_rows,
        "terminal_decision_rows": terminal_rows,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
