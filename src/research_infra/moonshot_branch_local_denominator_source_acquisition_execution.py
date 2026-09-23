"""Acquisition-execution helpers for denominator/source action candidates."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_acquisition_execution.py"
)
N20 = 20


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


def clamp(value: float, low: float = -1.0, high: float = 1.0) -> float:
    return round(max(low, min(high, value)), 6)


def r_interval_from_score(score: Any, uncertainty: float) -> dict[str, Any]:
    numeric = to_float(score)
    if numeric is None:
        return {
            "proxy_score": None,
            "proxy_r_style_midpoint": None,
            "proxy_r_style_lower": None,
            "proxy_r_style_upper": None,
            "proxy_r_style_result_class": "NO_PROXY_SCORE_AVAILABLE",
            "proxy_r_style_uncertainty": uncertainty,
        }
    midpoint = clamp(numeric - 0.35)
    lower = clamp(midpoint - uncertainty)
    upper = clamp(midpoint + uncertainty)
    if lower > 0:
        result_class = "PROXY_R_INTERVAL_ALL_POSITIVE"
    elif upper < 0:
        result_class = "PROXY_R_INTERVAL_ALL_NEGATIVE"
    else:
        result_class = "PROXY_R_INTERVAL_STRADDLES_ZERO"
    return {
        "proxy_score": round(numeric, 6),
        "proxy_r_style_midpoint": midpoint,
        "proxy_r_style_lower": lower,
        "proxy_r_style_upper": upper,
        "proxy_r_style_result_class": result_class,
        "proxy_r_style_uncertainty": uncertainty,
    }


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "denominator_source_acquisition_execution_surface": DENOMINATOR_SOURCE_ACQUISITION_EXECUTION_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "live_effect": False,
    }


def relation_counts(member_rows: list[dict[str, Any]]) -> dict[str, int]:
    counter = Counter(str(row.get("control_member_relation")) for row in member_rows)
    return {name: int(counter[name]) for name in sorted(counter)}


def relation_score_means(member_rows: list[dict[str, Any]]) -> dict[str, float]:
    values: dict[str, list[float]] = {}
    for row in member_rows:
        score = to_float(row.get("control_proxy_score"))
        if score is None:
            continue
        values.setdefault(str(row.get("control_member_relation")), []).append(score)
    return {name: round(mean(scores), 6) for name, scores in sorted(values.items()) if scores}


def exact_control_target_build_execution(
    action_row: dict[str, Any],
    execution_row: dict[str, Any],
    member_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    counts = relation_counts(member_rows)
    means = relation_score_means(member_rows)
    exact_count = counts.get("CONTROL_MEMBER_RELATION_EXACT_SCOPE", 0)
    best_relation = execution_row.get("best_available_proxy_relation")
    best_count = to_int(execution_row.get("best_available_proxy_member_count"))
    kept_members = [row for row in member_rows if row.get("keep_for_strongest_available_proxy")]
    kept_scores = [to_float(row.get("control_proxy_score")) for row in kept_members]
    kept_scores = [score for score in kept_scores if score is not None]
    best_score = mean(kept_scores) if kept_scores else to_float(execution_row.get("proxy_control_score"))
    interval = r_interval_from_score(best_score, 0.30 if best_count < N20 else 0.18)
    if exact_count >= N20:
        status = "DENOM_SOURCE_ACQ_EXEC_EXACT_CONTROL_TARGET_BUILT_N20"
        decision = "SCORE_EXACT_CONTROL_TARGET"
        scalar_allowed = True
    elif best_count >= N20:
        status = "DENOM_SOURCE_ACQ_EXEC_CONTROL_TARGET_PROXY_N20_EXACT_OPEN"
        decision = "USE_GUARDED_PROXY_AND_CONTINUE_EXACT_TARGET_BUILD"
        scalar_allowed = False
    else:
        status = "DENOM_SOURCE_ACQ_EXEC_CONTROL_TARGET_EXACT_UNAVAILABLE_PROXY_UNDER_N20"
        decision = "DO_NOT_SCORE_TARGET_BUILD_MORE_EXACT_OR_RELATION_CONTROL_ROWS"
        scalar_allowed = False
    return {
        **_base(action_row),
        "denominator_source_acquisition_lane": "EXACT_CONTROL_TARGET_BUILD_EXECUTION",
        "denominator_source_acquisition_status": status,
        "denominator_source_acquisition_decision": decision,
        "input_action_candidate_row_id": action_row.get("denominator_source_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": action_row.get("input_denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": action_row.get("input_denominator_source_rebuild_row_id"),
        "input_repair_execution_row_id": execution_row.get("input_repair_execution_row_id"),
        "member_rows_examined": len(member_rows),
        "control_member_relation_counts": counts,
        "control_member_relation_score_means": means,
        "exact_control_member_count": exact_count,
        "best_available_proxy_relation": best_relation,
        "best_available_proxy_member_count": best_count,
        "best_proxy_rows_needed_to_n20": max(0, N20 - best_count),
        "best_proxy_score": interval["proxy_score"],
        "best_proxy_r_style_midpoint": interval["proxy_r_style_midpoint"],
        "best_proxy_r_style_lower": interval["proxy_r_style_lower"],
        "best_proxy_r_style_upper": interval["proxy_r_style_upper"],
        "best_proxy_r_style_result_class": interval["proxy_r_style_result_class"],
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "exact_rebuild_required": not scalar_allowed,
        "keep_kill_redesign_decision": "BUILD_REQUIRED" if not scalar_allowed else "KEEP_EXACT_SCOREABLE",
        "implementation_implication": "exact_control_target_denominator_still_required_before_target_scalar_use",
    }


def exact_control_scope_build_execution(
    scope_action_row: dict[str, Any],
    target_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    built_targets = sum(
        1
        for row in target_rows
        if row.get("denominator_source_acquisition_status") == "DENOM_SOURCE_ACQ_EXEC_EXACT_CONTROL_TARGET_BUILT_N20"
    )
    proxy_n20_targets = sum(
        1
        for row in target_rows
        if row.get("denominator_source_acquisition_status") == "DENOM_SOURCE_ACQ_EXEC_CONTROL_TARGET_PROXY_N20_EXACT_OPEN"
    )
    underpowered_targets = len(target_rows) - built_targets - proxy_n20_targets
    if built_targets == len(target_rows) and target_rows:
        status = "DENOM_SOURCE_ACQ_EXEC_EXACT_CONTROL_SCOPE_BUILT"
        decision = "SCORE_EXACT_CONTROL_SCOPE"
        scalar_allowed = True
    elif scope_action_row.get("proxy_scalar_interpretation_allowed"):
        status = "DENOM_SOURCE_ACQ_EXEC_CONTROL_SCOPE_GUARDED_PROXY_CONFIRMED_BUILD_OPEN"
        decision = "KEEP_GUARDED_SCOPE_PROXY_AND_CONTINUE_EXACT_BUILD"
        scalar_allowed = True
    else:
        status = "DENOM_SOURCE_ACQ_EXEC_CONTROL_SCOPE_BUILD_OPEN_TARGETS_UNDER_N20"
        decision = "BUILD_EXACT_CONTROL_SCOPE_DENOMINATOR_BEFORE_SCALAR_USE"
        scalar_allowed = False
    return {
        **_base(scope_action_row),
        "denominator_source_acquisition_lane": "EXACT_CONTROL_SCOPE_BUILD_EXECUTION",
        "denominator_source_acquisition_status": status,
        "denominator_source_acquisition_decision": decision,
        "input_exact_control_scope_action_row_id": scope_action_row.get("exact_control_scope_action_row_id"),
        "target_action_rows": len(target_rows),
        "target_exact_built_rows": built_targets,
        "target_proxy_n20_rows": proxy_n20_targets,
        "target_underpowered_rows": underpowered_targets,
        "proxy_scalar_interpretation_allowed": scalar_allowed,
        "exact_rebuild_required": True,
        "keep_kill_redesign_decision": "KEEP_GUARDED_PROXY" if scalar_allowed else "BUILD_REQUIRED",
        "implementation_implication": "scope_proxy_guard_only_until_exact_control_targets_are_built",
    }


def source_exact_rebuild_execution(
    action_row: dict[str, Any],
    execution_row: dict[str, Any],
    rebuild_row: dict[str, Any],
    materialization_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    materialization_row = materialization_row or {}
    exact_count = to_int(rebuild_row.get("current_targetable_flagged_n"))
    gap = max(0, N20 - exact_count)
    proxy_class = execution_row.get("materialization_proxy_r_style_result_class")
    proxy_score = to_float(execution_row.get("materialization_proxy_score"))
    if exact_count >= N20 and proxy_class != "PROXY_R_INTERVAL_ALL_NEGATIVE":
        status = "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_BUILT_RECHECK_REQUIRED"
        decision = "RECHECK_EXACT_SOURCE_SCORE_AGAINST_PROXY"
        keep_kill = "RECHECK"
    elif proxy_class == "PROXY_R_INTERVAL_ALL_NEGATIVE":
        status = "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_UNDER_N20_NEGATIVE_PROXY_KILL_CONFIRMED"
        decision = "KEEP_SOURCE_PROXY_KILL_AND_CONTINUE_EXACT_REBUILD_ONLY_AS_CONTRADICTION_ROUTE"
        keep_kill = "KILL_PROXY"
    else:
        status = "DENOM_SOURCE_ACQ_EXEC_SOURCE_EXACT_UNDER_N20_PROXY_AMBIGUOUS"
        decision = "CONTINUE_EXACT_SOURCE_REBUILD_BEFORE_IMPLEMENTATION"
        keep_kill = "REDESIGN"
    return {
        **_base(action_row),
        "denominator_source_acquisition_lane": "EXACT_SOURCE_REBUILD_EXECUTION",
        "denominator_source_acquisition_status": status,
        "denominator_source_acquisition_decision": decision,
        "input_action_candidate_row_id": action_row.get("denominator_source_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": action_row.get("input_denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": action_row.get("input_denominator_source_rebuild_row_id"),
        "source_materialization_execution_id": action_row.get("source_materialization_execution_id"),
        "current_targetable_flagged_n": exact_count,
        "current_source_flagged_n": to_int(rebuild_row.get("current_source_flagged_n")),
        "current_failclosed_flagged_n": to_int(rebuild_row.get("current_failclosed_flagged_n")),
        "current_exact_gap_to_n20": gap,
        "best_expanded_targetable_field": rebuild_row.get("best_expanded_targetable_field"),
        "best_expanded_targetable_count": to_int(rebuild_row.get("best_expanded_targetable_count")),
        "materialization_proxy_scope": rebuild_row.get("materialization_proxy_scope"),
        "materialization_proxy_score": proxy_score,
        "materialization_proxy_r_style_result_class": proxy_class,
        "materialization_proxy_r_style_lower": execution_row.get("materialization_proxy_r_style_lower"),
        "materialization_proxy_r_style_midpoint": execution_row.get("materialization_proxy_r_style_midpoint"),
        "materialization_proxy_r_style_upper": execution_row.get("materialization_proxy_r_style_upper"),
        "materialization_status": materialization_row.get("source_materialization_execution_status"),
        "proxy_contradiction_found": False,
        "proxy_scalar_interpretation_allowed": False,
        "exact_rebuild_required": True,
        "keep_kill_redesign_decision": keep_kill,
        "implementation_implication": "source_proxy_remains_killed_pending_exact_source_rebuild_contradiction",
    }


def horizon_repair_rescore_execution(
    action_row: dict[str, Any],
    execution_row: dict[str, Any],
    rebuild_row: dict[str, Any],
    materialization_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    materialization_row = materialization_row or {}
    targetable = to_int(rebuild_row.get("current_targetable_flagged_n"))
    failclosed = to_int(rebuild_row.get("current_failclosed_flagged_n"))
    source_count = to_int(rebuild_row.get("current_source_flagged_n"))
    repaired_targetable_upper = targetable + failclosed
    source_proxy = to_float(execution_row.get("source_proxy_score"))
    horizon_proxy = to_float(execution_row.get("horizon_proxy_score"))
    repair_upper_interval = r_interval_from_score(source_proxy, 0.22)
    current_interval = r_interval_from_score(horizon_proxy, 0.34 if action_row.get("fail_if_negative_persists") else 0.28)
    fail_if_negative = bool(action_row.get("fail_if_negative_persists"))
    if fail_if_negative and repair_upper_interval["proxy_r_style_upper"] is not None and repair_upper_interval["proxy_r_style_upper"] < 0:
        status = "DENOM_SOURCE_ACQ_EXEC_HORIZON_KILL_CONFIRMED_BY_REPAIR_UPPER_BOUND"
        decision = "KILL_HORIZON_CANDIDATE_AFTER_REPAIR_BOUND_REMAINS_NEGATIVE"
        keep_kill = "KILL"
    elif fail_if_negative:
        status = "DENOM_SOURCE_ACQ_EXEC_HORIZON_KILL_CHECK_STILL_OPEN_AFTER_REPAIR_BOUND"
        decision = "REPAIR_HORIZON_AND_KILL_ONLY_IF_REBUILT_SCORE_REMAINS_NEGATIVE"
        keep_kill = "KILL_CHECK"
    elif action_row.get("keep_kill_redesign_decision") == "REDESIGN":
        status = "DENOM_SOURCE_ACQ_EXEC_HORIZON_REDESIGN_REPAIR_BOUND_SCOREABLE"
        decision = "REDESIGN_TARGETABILITY_AND_RESCORE_WITH_SOURCE_UPPER_BOUND"
        keep_kill = "REDESIGN"
    else:
        status = "DENOM_SOURCE_ACQ_EXEC_HORIZON_REPAIR_RESCORABLE_WITH_SOURCE_UPPER_BOUND"
        decision = "REPAIR_TARGETABILITY_AND_RESCORE_WITH_SOURCE_UPPER_BOUND"
        keep_kill = "REPAIR"
    return {
        **_base(action_row),
        "denominator_source_acquisition_lane": "HORIZON_REPAIR_RESCORE_EXECUTION",
        "denominator_source_acquisition_status": status,
        "denominator_source_acquisition_decision": decision,
        "input_action_candidate_row_id": action_row.get("denominator_source_action_candidate_row_id"),
        "input_denominator_source_execution_row_id": action_row.get("input_denominator_source_execution_row_id"),
        "input_denominator_source_rebuild_row_id": action_row.get("input_denominator_source_rebuild_row_id"),
        "input_horizon_rebuild_split_row_id": action_row.get("input_horizon_rebuild_split_row_id"),
        "source_materialization_execution_id": action_row.get("source_materialization_execution_id"),
        "current_targetable_flagged_n": targetable,
        "current_failclosed_flagged_n": failclosed,
        "current_source_flagged_n": source_count,
        "repaired_targetable_upper_bound_n": repaired_targetable_upper,
        "repaired_targetable_upper_bound_reaches_n20": repaired_targetable_upper >= N20,
        "current_targetable_gap_to_n20": max(0, N20 - targetable),
        "source_proxy_score": source_proxy,
        "horizon_proxy_score": horizon_proxy,
        "current_horizon_proxy_r_style_result_class": current_interval["proxy_r_style_result_class"],
        "repair_upper_proxy_r_style_midpoint": repair_upper_interval["proxy_r_style_midpoint"],
        "repair_upper_proxy_r_style_lower": repair_upper_interval["proxy_r_style_lower"],
        "repair_upper_proxy_r_style_upper": repair_upper_interval["proxy_r_style_upper"],
        "repair_upper_proxy_r_style_result_class": repair_upper_interval["proxy_r_style_result_class"],
        "source_minus_horizon_proxy_delta": execution_row.get("source_minus_horizon_proxy_delta"),
        "materialization_status": materialization_row.get("source_materialization_execution_status"),
        "fail_if_negative_persists": fail_if_negative,
        "proxy_scalar_interpretation_allowed": False,
        "exact_rebuild_required": True,
        "keep_kill_redesign_decision": keep_kill,
        "implementation_implication": "horizon_candidate_withheld_until_targetability_repair_and_rescore",
    }


def acquisition_requirement_execution(row: dict[str, Any], executed_row: dict[str, Any] | None) -> dict[str, Any]:
    executed_row = executed_row or {}
    return {
        **_base(row),
        "denominator_source_acquisition_lane": "ACQUISITION_REQUIREMENT_EXECUTION",
        "denominator_source_acquisition_status": executed_row.get(
            "denominator_source_acquisition_status", "DENOM_SOURCE_ACQ_EXEC_REQUIREMENT_NO_MATCH"
        ),
        "denominator_source_acquisition_decision": executed_row.get(
            "denominator_source_acquisition_decision", "RECHECK_ACQUISITION_REQUIREMENT_JOIN"
        ),
        "input_acquisition_requirement_row_id": row.get("acquisition_requirement_row_id"),
        "input_action_candidate_row_id": row.get("input_action_candidate_row_id"),
        "matched_execution_row_id": executed_row.get("denominator_source_acquisition_execution_row_id"),
        "acquisition_requirement_family": row.get("acquisition_requirement_family"),
        "acquisition_requirement_status": row.get("acquisition_requirement_status"),
        "rows_needed_to_n20": to_int(row.get("rows_needed_to_n20")),
        "proxy_scalar_interpretation_allowed": bool(executed_row.get("proxy_scalar_interpretation_allowed")),
        "exact_rebuild_required": bool(row.get("exact_rebuild_required")),
        "keep_kill_redesign_decision": executed_row.get("keep_kill_redesign_decision"),
        "implementation_implication": executed_row.get("implementation_implication"),
    }
