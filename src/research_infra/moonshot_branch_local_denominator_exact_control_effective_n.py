"""Effective-N consumption for exact-control denominator blockers."""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any


EXACT_CONTROL_EFFECTIVE_N_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_effective_n.py"
)
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
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def rows_needed_to_n20(value: Any) -> int:
    return max(0, N20 - to_int(value))


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def member_effective_identity(row: dict[str, Any]) -> str:
    parts = (
        row.get("member_execution_bundle_row_id"),
        row.get("member_runtime_work_row_id"),
        row.get("member_symbol"),
        row.get("member_route_session"),
        row.get("member_horizon_id"),
        row.get("member_primitive_flag"),
    )
    return "|".join(str(part or "") for part in parts)


def best_relation(member_rows: list[dict[str, Any]]) -> str | None:
    counts = Counter(str(row.get("control_member_relation")) for row in member_rows)
    available = [relation for relation, count in counts.items() if count > 0]
    if not available:
        return None
    return max(available, key=lambda relation: RELATION_RANK.get(relation, -1))


def score_stats(member_rows: list[dict[str, Any]]) -> dict[str, Any]:
    values = [to_float(row.get("control_proxy_score")) for row in member_rows]
    numeric = [value for value in values if value is not None]
    if not numeric:
        return {"score_count": 0, "score_mean": None, "score_min": None, "score_max": None}
    return {
        "score_count": len(numeric),
        "score_mean": round(mean(numeric), 6),
        "score_min": round(min(numeric), 6),
        "score_max": round(max(numeric), 6),
    }


def effective_n_stats(member_rows: list[dict[str, Any]], relation: str | None = None) -> dict[str, Any]:
    scoped = [row for row in member_rows if relation is None or row.get("control_member_relation") == relation]
    identities = [member_effective_identity(row) for row in scoped]
    duplicate_counts = Counter(identities)
    stats = score_stats(scoped)
    return {
        "raw_member_count": len(scoped),
        "effective_member_count": len(duplicate_counts),
        "effective_rows_needed_to_n20": rows_needed_to_n20(len(duplicate_counts)),
        "duplicate_member_rows": max(0, len(scoped) - len(duplicate_counts)),
        "max_duplicate_identity_count": max(duplicate_counts.values()) if duplicate_counts else 0,
        "score_mean": stats["score_mean"],
        "score_min": stats["score_min"],
        "score_max": stats["score_max"],
    }


def _base(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "exact_control_effective_n_surface": EXACT_CONTROL_EFFECTIVE_N_SURFACE,
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "source_code_candidate_id": row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "live_effect": False,
    }


def exact_control_blocker_effective_n_decision(
    blocker_row: dict[str, Any],
    execution_row: dict[str, Any] | None,
    member_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    execution = execution_row or {}
    relation = execution.get("best_available_proxy_relation") or best_relation(member_rows)
    best_stats = effective_n_stats(member_rows, relation)
    all_stats = effective_n_stats(member_rows)
    exact_count = to_int(blocker_row.get("exact_control_member_count") or execution.get("exact_control_count"))
    raw_best_count = to_int(
        blocker_row.get("best_available_proxy_member_count")
        or execution.get("best_available_proxy_member_count")
        or execution.get("best_proxy_member_count")
    )
    effective_count = best_stats["effective_member_count"]
    if exact_count >= N20:
        status = "EXACT_CONTROL_EFFECTIVE_N_EXACT_N20_READY"
        decision = "score_exact_control_after_recount"
    elif effective_count >= N20:
        status = "EXACT_CONTROL_EFFECTIVE_N_PROXY_N20_GUARD_AVAILABLE_EXACT_BUILD_OPEN"
        decision = "keep_proxy_guard_default_off_and_build_exact_control_denominator"
    elif raw_best_count >= N20 and effective_count < N20:
        status = "EXACT_CONTROL_EFFECTIVE_N_RAW_N20_DUPLICATE_INFLATED_BUILD_REQUIRED"
        decision = "deduplicate_proxy_members_and_build_exact_control_denominator"
    elif effective_count > 0:
        status = "EXACT_CONTROL_EFFECTIVE_N_PROXY_UNDER_N20_BUILD_REQUIRED"
        decision = "build_exact_control_denominator_no_runtime_scalar"
    else:
        status = "EXACT_CONTROL_EFFECTIVE_N_NO_PROXY_MEMBERS_BUILD_REQUIRED"
        decision = "build_exact_control_denominator_from_source"
    return {
        **_base(blocker_row),
        "input_exact_control_blocker_row_id": blocker_row.get("exact_control_blocker_row_id"),
        "input_default_off_implementation_row_id": blocker_row.get("input_default_off_implementation_row_id"),
        "input_detail_execution_row_id": blocker_row.get("input_detail_execution_row_id"),
        "input_denominator_source_execution_row_id": execution.get("denominator_source_execution_row_id")
        or execution.get("exact_control_scope_execution_row_id"),
        "exact_control_effective_n_status": status,
        "exact_control_effective_n_decision": decision,
        "exact_control_application_blocker_status": blocker_row.get("exact_control_application_blocker_status"),
        "denominator_source_execution_status": execution.get("denominator_source_execution_status"),
        "exact_control_member_count": exact_count,
        "best_available_proxy_relation": relation,
        "raw_best_proxy_member_count": raw_best_count,
        "effective_best_proxy_member_count": effective_count,
        "effective_best_proxy_rows_needed_to_n20": best_stats["effective_rows_needed_to_n20"],
        "duplicate_best_proxy_member_rows": best_stats["duplicate_member_rows"],
        "all_relation_raw_member_count": all_stats["raw_member_count"],
        "all_relation_effective_member_count": all_stats["effective_member_count"],
        "best_proxy_score_mean": best_stats["score_mean"],
        "best_proxy_score_min": best_stats["score_min"],
        "best_proxy_score_max": best_stats["score_max"],
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "implementation_implication": (
            "effective_n_confirms_exact_control_build_required"
            if effective_count < N20
            else "proxy_guard_available_but_exact_control_build_still_required"
        ),
    }


def exact_control_scope_effective_n_decision(
    scope_seed_row: dict[str, Any],
    blocker_rows: list[dict[str, Any]],
    member_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    relation = best_relation(member_rows)
    best_stats = effective_n_stats(member_rows, relation)
    all_stats = effective_n_stats(member_rows)
    raw_best = best_stats["raw_member_count"]
    effective_best = best_stats["effective_member_count"]
    if effective_best >= N20:
        status = "EXACT_CONTROL_SCOPE_EFFECTIVE_N_PROXY_N20_GUARD_AVAILABLE"
    elif raw_best >= N20:
        status = "EXACT_CONTROL_SCOPE_EFFECTIVE_N_RAW_N20_DUPLICATE_INFLATED"
    elif effective_best > 0:
        status = "EXACT_CONTROL_SCOPE_EFFECTIVE_N_UNDER_N20_BUILD_REQUIRED"
    else:
        status = "EXACT_CONTROL_SCOPE_EFFECTIVE_N_NO_PROXY_MEMBERS_BUILD_REQUIRED"
    return {
        **_base(scope_seed_row),
        "exact_control_scope_effective_n_status": status,
        "exact_control_scope_effective_n_decision": "build_exact_control_denominator_preserve_deduped_proxy_context",
        "scope_blocker_row_count": len(blocker_rows),
        "best_available_proxy_relation": relation,
        "raw_best_proxy_member_count": raw_best,
        "effective_best_proxy_member_count": effective_best,
        "effective_best_proxy_rows_needed_to_n20": best_stats["effective_rows_needed_to_n20"],
        "duplicate_best_proxy_member_rows": best_stats["duplicate_member_rows"],
        "all_relation_raw_member_count": all_stats["raw_member_count"],
        "all_relation_effective_member_count": all_stats["effective_member_count"],
        "best_proxy_score_mean": best_stats["score_mean"],
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
    }


def control_member_effective_n_row(
    member_row: dict[str, Any],
    identity_first_seen: bool,
    identity_duplicate_count: int,
) -> dict[str, Any]:
    identity = member_effective_identity(member_row)
    return {
        **_base(member_row),
        "input_control_member_relation_split_row_id": member_row.get("control_member_relation_split_row_id"),
        "input_member_acquisition_proxy_row_id": member_row.get("input_member_acquisition_proxy_row_id"),
        "input_repair_execution_row_id": member_row.get("input_repair_execution_row_id"),
        "member_effective_identity": identity,
        "member_effective_identity_first_seen": identity_first_seen,
        "member_effective_identity_duplicate_count": identity_duplicate_count,
        "control_member_relation": member_row.get("control_member_relation"),
        "control_member_relation_rank": member_row.get("control_member_relation_rank"),
        "control_proxy_score": member_row.get("control_proxy_score"),
        "control_proxy_score_band": member_row.get("control_proxy_score_band"),
        "keep_for_strongest_available_proxy": bool(member_row.get("keep_for_strongest_available_proxy")),
        "target_best_available_proxy_relation": member_row.get("target_best_available_proxy_relation"),
        "target_best_available_proxy_member_count": member_row.get("target_best_available_proxy_member_count"),
        "member_symbol": member_row.get("member_symbol"),
        "member_route_session": member_row.get("member_route_session"),
        "member_horizon_id": member_row.get("member_horizon_id"),
        "member_primitive_flag": member_row.get("member_primitive_flag"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
    }
