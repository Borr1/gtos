"""Control/source split helpers for branch-local repair acquisition rows."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


CONTROL_SOURCE_SPLIT_SURFACE = "src/research_infra/moonshot_branch_local_control_source_split.py"
N20 = 20

RELATION_RANK = {
    "CONTROL_MEMBER_RELATION_EXACT_SCOPE": 4,
    "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION_HORIZON": 3,
    "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION": 2,
    "CONTROL_MEMBER_RELATION_SAME_SYMBOL": 1,
    "CONTROL_MEMBER_RELATION_GLOBAL_CROSS_SYMBOL": 0,
}


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


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "control_source_split_surface": CONTROL_SOURCE_SPLIT_SURFACE,
        "input_acquisition_proxy_row_id": row.get("acquisition_proxy_row_id"),
        "input_repair_execution_row_id": row.get("input_repair_execution_row_id"),
        "input_repair_execution_status": row.get("input_repair_execution_status"),
        "input_module_materialization_row_id": row.get("input_module_materialization_row_id"),
        "input_code_integration_candidate_row_id": row.get("input_code_integration_candidate_row_id"),
        "input_runtime_work_row_id": row.get("input_runtime_work_row_id"),
        "input_implementation_candidate_row_id": row.get("input_implementation_candidate_row_id"),
        "input_execution_bundle_row_id": row.get("input_execution_bundle_row_id"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "observable_scope_key": row.get("observable_scope_key"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "scope_symbol": row.get("scope_symbol"),
        "scope_session": row.get("scope_session"),
        "scope_horizon": row.get("scope_horizon"),
        "scope_primitive": row.get("scope_primitive"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def _scores(rows: list[dict[str, Any]]) -> list[float]:
    values: list[float] = []
    for row in rows:
        numeric = to_float(row.get("control_proxy_score"))
        if numeric is not None:
            values.append(numeric)
    return values


def _score_stats(rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = _scores(rows)
    if not values:
        return {
            "score_count": 0,
            "score_mean": None,
            "score_min": None,
            "score_max": None,
        }
    return {
        "score_count": len(values),
        "score_mean": round(mean(values), 6),
        "score_min": round(min(values), 6),
        "score_max": round(max(values), 6),
    }


def _best_relation(relation_counts: dict[str, int]) -> str:
    available = [relation for relation, count in relation_counts.items() if count > 0]
    if not available:
        return "CONTROL_MEMBER_RELATION_NONE"
    return max(available, key=lambda relation: RELATION_RANK.get(relation, -1))


def _relation_status(best_relation: str, best_count: int) -> str:
    if best_relation == "CONTROL_MEMBER_RELATION_EXACT_SCOPE" and best_count >= N20:
        return "CONTROL_SOURCE_SPLIT_EXACT_CONTROL_N20_READY"
    if best_relation == "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION_HORIZON":
        return "CONTROL_SOURCE_SPLIT_EXACT_REQUIRED_KEEP_SAME_SYMBOL_SESSION_HORIZON_PROXY_UNDER_N20"
    if best_relation == "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION":
        return "CONTROL_SOURCE_SPLIT_EXACT_REQUIRED_KEEP_SAME_SYMBOL_SESSION_PROXY_UNDER_N20"
    if best_relation == "CONTROL_MEMBER_RELATION_SAME_SYMBOL":
        return "CONTROL_SOURCE_SPLIT_EXACT_REQUIRED_KEEP_SAME_SYMBOL_PROXY_UNDER_N20"
    return "CONTROL_SOURCE_SPLIT_EXACT_REQUIRED_GLOBAL_PROXY_ONLY"


def exact_control_relation_split(
    row: dict[str, Any],
    member_rows: list[dict[str, Any]],
    duplicate_scope_row_count: int,
) -> dict[str, Any]:
    relation_counts = Counter(str(member.get("control_member_relation")) for member in member_rows)
    best_relation = _best_relation(dict(relation_counts))
    best_rows = [member for member in member_rows if member.get("control_member_relation") == best_relation]
    best_count = len(best_rows)
    best_stats = _score_stats(best_rows)
    all_stats = _score_stats(member_rows)
    status = _relation_status(best_relation, best_count)
    exact_count = to_int(row.get("exact_control_count"))
    return {
        **_base(row),
        "control_source_split_lane": "EXACT_CONTROL_RELATION_SPLIT",
        "control_source_split_status": status,
        "control_source_split_decision": "BUILD_EXACT_SCOPE_CONTROL_DENOMINATOR_KEEP_BEST_PROXY_RELATION",
        "exact_control_count": exact_count,
        "exact_control_rows_needed_to_n20": rows_needed_to_n20(exact_count),
        "same_symbol_session_horizon_member_count": relation_counts.get(
            "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION_HORIZON", 0
        ),
        "same_symbol_session_member_count": relation_counts.get(
            "CONTROL_MEMBER_RELATION_SAME_SYMBOL_SESSION", 0
        ),
        "same_symbol_member_count": relation_counts.get("CONTROL_MEMBER_RELATION_SAME_SYMBOL", 0),
        "global_member_count": relation_counts.get("CONTROL_MEMBER_RELATION_GLOBAL_CROSS_SYMBOL", 0),
        "selected_control_member_count": len(member_rows),
        "best_available_proxy_relation": best_relation,
        "best_available_proxy_relation_rank": RELATION_RANK.get(best_relation, -1),
        "best_available_proxy_member_count": best_count,
        "best_available_proxy_rows_needed_to_n20": rows_needed_to_n20(best_count),
        "best_available_proxy_score_mean": best_stats["score_mean"],
        "best_available_proxy_score_min": best_stats["score_min"],
        "best_available_proxy_score_max": best_stats["score_max"],
        "all_member_proxy_score_mean": all_stats["score_mean"],
        "all_member_proxy_score_min": all_stats["score_min"],
        "all_member_proxy_score_max": all_stats["score_max"],
        "duplicate_scope_row_count": duplicate_scope_row_count,
        "exact_scope_absent": exact_count == 0,
        "next_same_resource_action": (
            "materialize exact same-scope controls; if exact controls remain absent, preserve "
            "best same-symbol/session/horizon proxy separately from global proxy"
        ),
    }


def control_member_relation_split(
    member_row: dict[str, Any],
    target_split: dict[str, Any],
    relation_group_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    stats = _score_stats(relation_group_rows)
    score = to_float(member_row.get("control_proxy_score"))
    score_delta = None
    if score is not None and stats["score_mean"] is not None:
        score_delta = round(score - float(stats["score_mean"]), 6)
    relation = str(member_row.get("control_member_relation"))
    keep_for_best = relation == target_split.get("best_available_proxy_relation")
    return {
        **_base(member_row),
        "control_source_split_lane": "CONTROL_MEMBER_RELATION_SPLIT",
        "control_source_split_status": (
            "CONTROL_SOURCE_SPLIT_MEMBER_BEST_PROXY_RELATION"
            if keep_for_best
            else "CONTROL_SOURCE_SPLIT_MEMBER_CONTEXT_PROXY_RELATION"
        ),
        "control_source_split_decision": "PRESERVE_MEMBER_IN_FULL_RELATION_LEDGER",
        "input_member_acquisition_proxy_row_id": member_row.get("acquisition_proxy_row_id"),
        "member_runtime_work_row_id": member_row.get("member_runtime_work_row_id"),
        "member_input_candidate_id": member_row.get("member_input_candidate_id"),
        "member_execution_bundle_row_id": member_row.get("member_execution_bundle_row_id"),
        "member_symbol": member_row.get("member_symbol"),
        "member_route_session": member_row.get("member_route_session"),
        "member_horizon_id": member_row.get("member_horizon_id"),
        "member_primitive_flag": member_row.get("member_primitive_flag"),
        "control_member_relation": relation,
        "control_member_relation_rank": RELATION_RANK.get(relation, -1),
        "control_proxy_score": score,
        "control_proxy_score_band": member_row.get("control_proxy_score_band"),
        "target_best_available_proxy_relation": target_split.get("best_available_proxy_relation"),
        "target_best_available_proxy_member_count": target_split.get("best_available_proxy_member_count"),
        "relation_group_member_count": len(relation_group_rows),
        "relation_group_score_mean": stats["score_mean"],
        "score_delta_from_relation_mean": score_delta,
        "keep_for_strongest_available_proxy": keep_for_best,
    }


def source_acquisition_split(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("source_repair_family") or "")
    if family == "EXACT_SOURCE_REPAIR":
        status = "CONTROL_SOURCE_SPLIT_EXACT_SOURCE_REBUILD_REQUIRED"
        decision = "ACQUIRE_OR_REBUILD_EXACT_SOURCE_ROWS_BEFORE_SCALAR_USE"
    elif family == "HORIZON_REBUILD_KILL_CHECK":
        status = "CONTROL_SOURCE_SPLIT_HORIZON_REBUILD_KILL_CHECK_REQUIRED"
        decision = "REBUILD_HORIZON_TARGETABLE_ROWS_AND_KILL_IF_NEGATIVE_PERSISTS"
    elif family == "HORIZON_REBUILD_RESCORE":
        status = "CONTROL_SOURCE_SPLIT_HORIZON_REBUILD_RESCORE_REQUIRED"
        decision = "REBUILD_HORIZON_TARGETABLE_ROWS_AND_RESCORE"
    else:
        status = "CONTROL_SOURCE_SPLIT_SOURCE_CONTEXT_ONLY"
        decision = "PRESERVE_SOURCE_CONTEXT"
    return {
        **_base(row),
        "control_source_split_lane": "SOURCE_ACQUISITION_SPLIT",
        "control_source_split_status": status,
        "control_source_split_decision": decision,
        "source_repair_family": family,
        "source_proxy_score": row.get("source_proxy_score"),
        "source_proxy_score_band": row.get("source_proxy_score_band"),
        "horizon_proxy_score": row.get("horizon_proxy_score"),
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "current_source_flagged_n": row.get("current_source_flagged_n"),
        "current_targetable_flagged_n": row.get("current_targetable_flagged_n"),
        "current_failclosed_flagged_n": row.get("current_failclosed_flagged_n"),
        "current_targetable_ratio": row.get("current_targetable_ratio"),
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "targetable_rows_needed_to_n20": row.get("targetable_rows_needed_to_n20"),
        "fail_if_negative_persists": row.get("fail_if_negative_persists"),
        "acquisition_priority_score": row.get("acquisition_priority_score"),
        "next_same_resource_action": decision.lower(),
    }


def horizon_rebuild_split(row: dict[str, Any]) -> dict[str, Any]:
    if row.get("fail_if_negative_persists"):
        status = "CONTROL_SOURCE_SPLIT_HORIZON_KILL_CHECK_REBUILD_ACTIVE"
        decision = "REBUILD_HORIZON_AND_KILL_IF_REBUILT_PROXY_REMAINS_WEAK"
    else:
        status = "CONTROL_SOURCE_SPLIT_HORIZON_RESCORE_REBUILD_ACTIVE"
        decision = "REBUILD_HORIZON_AND_RESCORE_WITH_FAILCLOSED_STRESS"
    return {
        **_base(row),
        "control_source_split_lane": "HORIZON_REBUILD_SPLIT",
        "control_source_split_status": status,
        "control_source_split_decision": decision,
        "source_proxy_score": row.get("source_proxy_score"),
        "horizon_proxy_score": row.get("horizon_proxy_score"),
        "source_minus_horizon_proxy_delta": row.get("source_minus_horizon_proxy_delta"),
        "current_failclosed_ratio": row.get("current_failclosed_ratio"),
        "failclosed_stress_score": row.get("failclosed_stress_score"),
        "targetable_rows_needed_to_n20": row.get("targetable_rows_needed_to_n20"),
        "fail_if_negative_persists": row.get("fail_if_negative_persists"),
    }


def scope_acquisition_plan(
    scope_key: tuple[Any, Any, Any, Any],
    exact_rows: list[dict[str, Any]],
    source_rows: list[dict[str, Any]],
    horizon_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    symbol, route_session, horizon_id, primitive_flag = scope_key
    if exact_rows and source_rows:
        status = "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_CONTROL_AND_SOURCE_REQUIREMENTS"
        decision = "BUILD_BOTH_EXACT_CONTROL_AND_SOURCE_REPAIR"
    elif exact_rows:
        status = "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_CONTROL_ONLY"
        decision = "BUILD_EXACT_CONTROL_DENOMINATOR"
    elif horizon_rows:
        status = "CONTROL_SOURCE_SPLIT_SCOPE_HORIZON_SOURCE_ONLY"
        decision = "REBUILD_HORIZON_SOURCE_ROWS"
    else:
        status = "CONTROL_SOURCE_SPLIT_SCOPE_EXACT_SOURCE_ONLY"
        decision = "ACQUIRE_OR_REBUILD_EXACT_SOURCE_ROWS"
    return {
        "control_source_split_surface": CONTROL_SOURCE_SPLIT_SURFACE,
        "control_source_split_lane": "SCOPE_ACQUISITION_PLAN",
        "control_source_split_status": status,
        "control_source_split_decision": decision,
        "symbol": symbol,
        "route_session": route_session,
        "horizon_id": horizon_id,
        "primitive_flag": primitive_flag,
        "exact_control_row_count": len(exact_rows),
        "source_requirement_row_count": len(source_rows),
        "horizon_rebuild_row_count": len(horizon_rows),
        "scope_has_exact_control_requirement": bool(exact_rows),
        "scope_has_source_requirement": bool(source_rows),
        "scope_has_horizon_rebuild_requirement": bool(horizon_rows),
        "scope_exact_source_overlap": bool(exact_rows and source_rows),
        "live_effect": False,
    }
