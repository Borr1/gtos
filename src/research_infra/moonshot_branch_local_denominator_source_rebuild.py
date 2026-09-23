"""Denominator/source rebuild helpers for branch-local repair split rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


DENOMINATOR_SOURCE_REBUILD_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_source_rebuild.py"
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
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def rows_needed_to_n20(value: Any) -> int:
    return max(0, N20 - to_int(value))


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "denominator_source_rebuild_surface": DENOMINATOR_SOURCE_REBUILD_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "observable_scope_key": row.get("observable_scope_key"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def _score_stats(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    values = [to_float(row.get(key)) for row in rows]
    numeric = [value for value in values if value is not None]
    if not numeric:
        return {"score_count": 0, "score_mean": None, "score_min": None, "score_max": None}
    return {
        "score_count": len(numeric),
        "score_mean": round(mean(numeric), 6),
        "score_min": round(min(numeric), 6),
        "score_max": round(max(numeric), 6),
    }


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts = Counter(str(row.get(key)) for row in rows)
    return {name: int(counts[name]) for name in sorted(counts)}


def best_expanded_count(row: dict[str, Any], suffix: str) -> tuple[str | None, int]:
    fields = [
        f"same_symbol_all_sessions_{suffix}_flagged_n",
        f"same_session_all_symbols_{suffix}_flagged_n",
        f"all_market_primitive_{suffix}_flagged_n",
        f"same_symbol_session_all_primitives_{suffix}_flagged_n",
    ]
    best_field: str | None = None
    best_value = 0
    for field in fields:
        value = to_int(row.get(field))
        if value > best_value:
            best_field = field
            best_value = value
    return best_field, best_value


def exact_control_target_rebuild(
    row: dict[str, Any],
    shadow_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
    control_execution_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    materialization_count = len(materialization_rows)
    control_count = len(control_execution_rows)
    shadow_count = len(shadow_rows)
    if materialization_count or control_count:
        status = "DENOM_SOURCE_REBUILD_EXACT_CONTROL_CURRENT_ROWS_PRESENT_RECOUNT_REQUIRED"
        decision = "RECOUNT_CURRENT_EXACT_CONTROL_DENOMINATOR_BEFORE_SCALAR_USE"
    elif shadow_count:
        status = "DENOM_SOURCE_REBUILD_EXACT_CONTROL_GUARD_ONLY_TARGET_BUILD_REQUIRED"
        decision = "BUILD_EXACT_CONTROL_DENOMINATOR_FROM_SCOPE_REPLAY_KEEP_SHADOW_GUARD"
    else:
        status = "DENOM_SOURCE_REBUILD_EXACT_CONTROL_NO_CURRENT_SURFACE_BUILD_REQUIRED"
        decision = "BUILD_EXACT_CONTROL_DENOMINATOR_AND_SOURCE_GUARD"
    return {
        **_base(row),
        "denominator_source_rebuild_lane": "EXACT_CONTROL_TARGET_DENOMINATOR_ACQUISITION",
        "denominator_source_rebuild_status": status,
        "denominator_source_rebuild_decision": decision,
        "input_control_source_split_row_id": row.get("control_source_split_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "input_acquisition_proxy_row_id": row.get("input_acquisition_proxy_row_id"),
        "exact_control_count": to_int(row.get("exact_control_count")),
        "exact_control_rows_needed_to_n20": rows_needed_to_n20(row.get("exact_control_count")),
        "selected_control_member_count": to_int(row.get("selected_control_member_count")),
        "best_available_proxy_relation": row.get("best_available_proxy_relation"),
        "best_available_proxy_member_count": to_int(row.get("best_available_proxy_member_count")),
        "best_available_proxy_rows_needed_to_n20": rows_needed_to_n20(
            row.get("best_available_proxy_member_count")
        ),
        "best_available_proxy_score_mean": row.get("best_available_proxy_score_mean"),
        "same_symbol_session_horizon_member_count": to_int(row.get("same_symbol_session_horizon_member_count")),
        "same_symbol_session_member_count": to_int(row.get("same_symbol_session_member_count")),
        "same_symbol_member_count": to_int(row.get("same_symbol_member_count")),
        "global_member_count": to_int(row.get("global_member_count")),
        "duplicate_scope_row_count": to_int(row.get("duplicate_scope_row_count")),
        "current_materialization_row_count": materialization_count,
        "current_control_execution_row_count": control_count,
        "current_shadow_guard_row_count": shadow_count,
        "shadow_bundle_stage_counts": _count_by(shadow_rows, "bundle_stage"),
        "shadow_bundle_permission_counts": _count_by(shadow_rows, "bundle_permission"),
        "exact_denominator_acquisition_open": True,
        "proxy_scalar_interpretation_allowed": False,
        "next_same_resource_action": decision.lower(),
    }


def exact_control_scope_denominator_rebuild(
    scope_row: dict[str, Any],
    exact_rows: list[dict[str, Any]],
    shadow_rows: list[dict[str, Any]],
    materialization_rows: list[dict[str, Any]],
    control_execution_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    best_member_rows = [row for row in member_rows if row.get("keep_for_strongest_available_proxy")]
    best_stats = _score_stats(best_member_rows, "control_proxy_score")
    all_stats = _score_stats(member_rows, "control_proxy_score")
    if materialization_rows or control_execution_rows:
        status = "DENOM_SOURCE_REBUILD_SCOPE_EXACT_CONTROL_CURRENT_ROWS_PRESENT_RECOUNT_REQUIRED"
    elif shadow_rows:
        status = "DENOM_SOURCE_REBUILD_SCOPE_EXACT_CONTROL_GUARD_ONLY_BUILD_REQUIRED"
    else:
        status = "DENOM_SOURCE_REBUILD_SCOPE_EXACT_CONTROL_NO_CURRENT_SURFACE_BUILD_REQUIRED"
    return {
        "denominator_source_rebuild_surface": DENOMINATOR_SOURCE_REBUILD_SURFACE,
        "denominator_source_rebuild_lane": "EXACT_CONTROL_SCOPE_DENOMINATOR_ACQUISITION",
        "denominator_source_rebuild_status": status,
        "denominator_source_rebuild_decision": "BUILD_EXACT_SCOPE_CONTROL_DENOMINATOR_TO_N20",
        "input_scope_acquisition_plan_row_id": scope_row.get("scope_acquisition_plan_row_id"),
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "exact_control_target_row_count": len(exact_rows),
        "unique_scope_exact_control_rows_needed_to_n20": N20,
        "target_row_exact_control_rows_needed_sum": sum(
            to_int(row.get("exact_control_rows_needed_to_n20")) for row in exact_rows
        ),
        "selected_control_member_count": len(member_rows),
        "best_proxy_member_count": len(best_member_rows),
        "best_proxy_relation_counts": _count_by(exact_rows, "best_available_proxy_relation"),
        "best_proxy_score_mean": best_stats["score_mean"],
        "all_member_proxy_score_mean": all_stats["score_mean"],
        "current_materialization_row_count": len(materialization_rows),
        "current_control_execution_row_count": len(control_execution_rows),
        "current_shadow_guard_row_count": len(shadow_rows),
        "shadow_bundle_permission_counts": _count_by(shadow_rows, "bundle_permission"),
        "exact_denominator_acquisition_open": True,
        "proxy_scalar_interpretation_allowed": False,
        "outside_gbpjpy_xauusd_current_branch_box": all(
            bool(row.get("outside_gbpjpy_xauusd_current_branch_box")) for row in exact_rows
        ),
        "live_effect": False,
    }


def control_member_denominator_evidence(
    row: dict[str, Any],
    target_row: dict[str, Any],
) -> dict[str, Any]:
    keep = bool(row.get("keep_for_strongest_available_proxy"))
    return {
        **_base(row),
        "denominator_source_rebuild_lane": "CONTROL_MEMBER_DENOMINATOR_PROXY_EVIDENCE",
        "denominator_source_rebuild_status": (
            "DENOM_SOURCE_REBUILD_MEMBER_BEST_PROXY_EVIDENCE"
            if keep
            else "DENOM_SOURCE_REBUILD_MEMBER_CONTEXT_PROXY_EVIDENCE"
        ),
        "denominator_source_rebuild_decision": "PRESERVE_MEMBER_FOR_EXACT_CONTROL_DENOMINATOR_COMPARISON",
        "input_control_member_relation_split_row_id": row.get("control_member_relation_split_row_id"),
        "input_member_acquisition_proxy_row_id": row.get("input_member_acquisition_proxy_row_id"),
        "target_control_source_split_row_id": target_row.get("control_source_split_row_id"),
        "target_input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "member_runtime_work_row_id": row.get("member_runtime_work_row_id"),
        "member_execution_bundle_row_id": row.get("member_execution_bundle_row_id"),
        "member_symbol": row.get("member_symbol"),
        "member_route_session": row.get("member_route_session"),
        "member_horizon_id": row.get("member_horizon_id"),
        "member_primitive_flag": row.get("member_primitive_flag"),
        "control_member_relation": row.get("control_member_relation"),
        "control_proxy_score": row.get("control_proxy_score"),
        "control_proxy_score_band": row.get("control_proxy_score_band"),
        "keep_for_strongest_available_proxy": keep,
        "target_best_available_proxy_relation": row.get("target_best_available_proxy_relation"),
        "target_best_available_proxy_member_count": row.get("target_best_available_proxy_member_count"),
    }


def source_materialization_rebuild(
    row: dict[str, Any],
    materialization_row: dict[str, Any] | None,
) -> dict[str, Any]:
    materialization_row = materialization_row or {}
    targetable_n = to_int(materialization_row.get("current_targetable_flagged_n"))
    source_n = to_int(materialization_row.get("current_source_flagged_n"))
    best_targetable_field, best_targetable_count = best_expanded_count(materialization_row, "targetable")
    best_source_field, best_source_count = best_expanded_count(materialization_row, "source")
    if not materialization_row:
        status = "DENOM_SOURCE_REBUILD_EXACT_SOURCE_MATERIALIZATION_MISSING"
        decision = "ACQUIRE_OR_REBUILD_EXACT_SOURCE_ROWS"
    elif targetable_n >= N20:
        status = "DENOM_SOURCE_REBUILD_EXACT_SOURCE_CURRENT_TARGETABLE_N20_RECOUNT"
        decision = "RECOUNT_CURRENT_EXACT_SOURCE_ROWS_WITH_CONTROL_GUARD"
    elif best_targetable_count >= N20 or best_source_count >= N20:
        status = "DENOM_SOURCE_REBUILD_EXACT_SOURCE_UNDER_N20_EXPANDED_PROXY_AVAILABLE"
        decision = "REBUILD_EXACT_SOURCE_TO_N20_KEEP_EXPANDED_PROXY_GUARD"
    else:
        status = "DENOM_SOURCE_REBUILD_EXACT_SOURCE_UNDER_N20_ACQUIRE_ROWS"
        decision = "ACQUIRE_OR_REBUILD_EXACT_SOURCE_ROWS"
    return {
        **_base(row),
        "denominator_source_rebuild_lane": "EXACT_SOURCE_MATERIALIZATION_REBUILD",
        "denominator_source_rebuild_status": status,
        "denominator_source_rebuild_decision": decision,
        "input_control_source_split_row_id": row.get("control_source_split_row_id"),
        "input_acquisition_proxy_row_id": row.get("input_acquisition_proxy_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "source_repair_family": row.get("source_repair_family"),
        "source_proxy_score": row.get("source_proxy_score"),
        "source_proxy_score_band": row.get("source_proxy_score_band"),
        "materialization_present": bool(materialization_row),
        "source_materialization_execution_id": materialization_row.get("source_materialization_execution_id"),
        "source_materialization_execution_status": materialization_row.get("source_materialization_execution_status"),
        "source_materialization_decision": materialization_row.get("source_materialization_decision"),
        "current_source_flagged_n": source_n,
        "current_targetable_flagged_n": targetable_n,
        "current_failclosed_flagged_n": to_int(materialization_row.get("current_failclosed_flagged_n")),
        "current_exact_gap_to_n20": rows_needed_to_n20(targetable_n),
        "materialization_current_exact_gap_to_n20": materialization_row.get("current_exact_gap_to_n20"),
        "best_expanded_targetable_field": best_targetable_field,
        "best_expanded_targetable_count": best_targetable_count,
        "best_expanded_source_field": best_source_field,
        "best_expanded_source_count": best_source_count,
        "materialization_proxy_scope": materialization_row.get("materialization_proxy_scope"),
        "materialization_proxy_score": materialization_row.get("materialization_proxy_score"),
        "materialization_proxy_r_style_result_class": materialization_row.get(
            "materialization_proxy_r_style_result_class"
        ),
        "materialization_exact_missing_reason": materialization_row.get("materialization_exact_missing_reason"),
        "proxy_scalar_interpretation_allowed": False,
        "next_same_resource_action": decision.lower(),
    }


def horizon_materialization_rebuild(
    row: dict[str, Any],
    horizon_row: dict[str, Any] | None,
    materialization_row: dict[str, Any] | None,
) -> dict[str, Any]:
    horizon_row = horizon_row or {}
    materialization_row = materialization_row or {}
    failclosed_ratio = to_float(row.get("current_failclosed_ratio"))
    targetable_n = to_int(materialization_row.get("current_targetable_flagged_n") or row.get("current_targetable_flagged_n"))
    if row.get("fail_if_negative_persists") or horizon_row.get("fail_if_negative_persists"):
        status = "DENOM_SOURCE_REBUILD_HORIZON_KILL_CHECK_EXACT_REPAIR_PATH"
        decision = "REBUILD_TARGETABLE_HORIZON_ROWS_AND_KILL_IF_NEGATIVE_PERSISTS"
    elif failclosed_ratio is not None and failclosed_ratio >= 0.75:
        status = "DENOM_SOURCE_REBUILD_HORIZON_HIGH_FAILCLOSED_RESCORE_PATH"
        decision = "REBUILD_TARGETABLE_HORIZON_ROWS_AND_RESCORE_HIGH_FAILCLOSED_SCOPE"
    else:
        status = "DENOM_SOURCE_REBUILD_HORIZON_RESCORE_EXACT_REPAIR_PATH"
        decision = "REBUILD_TARGETABLE_HORIZON_ROWS_AND_RESCORE"
    return {
        **_base(row),
        "denominator_source_rebuild_lane": "HORIZON_MATERIALIZATION_REBUILD",
        "denominator_source_rebuild_status": status,
        "denominator_source_rebuild_decision": decision,
        "input_control_source_split_row_id": row.get("control_source_split_row_id"),
        "input_horizon_rebuild_split_row_id": horizon_row.get("horizon_rebuild_split_row_id"),
        "input_acquisition_proxy_row_id": row.get("input_acquisition_proxy_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "source_repair_family": row.get("source_repair_family"),
        "source_proxy_score": row.get("source_proxy_score"),
        "horizon_proxy_score": row.get("horizon_proxy_score"),
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "current_source_flagged_n": to_int(materialization_row.get("current_source_flagged_n") or row.get("current_source_flagged_n")),
        "current_targetable_flagged_n": targetable_n,
        "current_failclosed_flagged_n": to_int(
            materialization_row.get("current_failclosed_flagged_n") or row.get("current_failclosed_flagged_n")
        ),
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "current_targetable_gap_to_n20": rows_needed_to_n20(targetable_n),
        "failclosed_stress_score": horizon_row.get("failclosed_stress_score"),
        "fail_if_negative_persists": bool(row.get("fail_if_negative_persists") or horizon_row.get("fail_if_negative_persists")),
        "source_materialization_execution_id": materialization_row.get("source_materialization_execution_id"),
        "source_materialization_execution_status": materialization_row.get("source_materialization_execution_status"),
        "materialization_exact_missing_reason": materialization_row.get("materialization_exact_missing_reason"),
        "proxy_scalar_interpretation_allowed": False,
        "next_same_resource_action": decision.lower(),
    }


def scope_rebuild_action(
    scope_row: dict[str, Any],
    exact_scope_row: dict[str, Any] | None,
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    exact_scope_row = exact_scope_row or {}
    if exact_scope_row:
        status = exact_scope_row.get("denominator_source_rebuild_status")
        decision = "EXECUTE_EXACT_CONTROL_DENOMINATOR_ACQUISITION"
    elif horizon_rows:
        status = "DENOM_SOURCE_REBUILD_SCOPE_HORIZON_SOURCE_REBUILD_ACTIVE"
        decision = "EXECUTE_HORIZON_MATERIALIZATION_REBUILD"
    elif source_rows:
        status = "DENOM_SOURCE_REBUILD_SCOPE_EXACT_SOURCE_REBUILD_ACTIVE"
        decision = "EXECUTE_EXACT_SOURCE_MATERIALIZATION_REBUILD"
    else:
        status = "DENOM_SOURCE_REBUILD_SCOPE_NO_ACTION_ROWS_FOUND"
        decision = "RECHECK_SCOPE_JOIN_INPUTS"
    return {
        "denominator_source_rebuild_surface": DENOMINATOR_SOURCE_REBUILD_SURFACE,
        "denominator_source_rebuild_lane": "SCOPE_REBUILD_ACTION",
        "denominator_source_rebuild_status": status,
        "denominator_source_rebuild_decision": decision,
        "input_scope_acquisition_plan_row_id": scope_row.get("scope_acquisition_plan_row_id"),
        "input_control_source_split_status": scope_row.get("control_source_split_status"),
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "exact_control_scope_action_count": 1 if exact_scope_row else 0,
        "source_rebuild_action_count": len(source_rows),
        "horizon_rebuild_action_count": len(horizon_rows),
        "current_materialization_row_count": (
            to_int(exact_scope_row.get("current_materialization_row_count"))
            if exact_scope_row
            else sum(1 for row in [*source_rows, *horizon_rows] if row.get("materialization_present") is not False)
        ),
        "current_control_execution_row_count": to_int(exact_scope_row.get("current_control_execution_row_count")),
        "current_shadow_guard_row_count": to_int(exact_scope_row.get("current_shadow_guard_row_count")),
        "exact_denominator_acquisition_open": bool(exact_scope_row),
        "source_or_horizon_rebuild_open": bool(source_rows or horizon_rows),
        "live_effect": False,
    }
