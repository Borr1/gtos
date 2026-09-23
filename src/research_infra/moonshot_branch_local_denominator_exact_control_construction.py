"""Construct exact-control denominators from same-resource primitive ledgers."""

from __future__ import annotations

from typing import Any


EXACT_CONTROL_CONSTRUCTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_denominator_exact_control_construction.py"
)
N20 = 20

SESSION_BUCKET_BY_ROUTE_SESSION = {
    "london_core": "london_core_0700_1030",
    "ny_core": "ny_core_1300_1700",
    "off_core_session": "off_core_session",
    "tokyo_kz": "tokyo_core_0000_0300",
}

SIERRA_SOURCE_SYMBOLS = {
    "NAS100": ("NQM26-CME", "MNQM26-CME"),
    "USDJPY": ("6JM26-CME",),
    "XAGUSD": ("SIM26-COMEX", "SILM26-COMEX"),
}

SIERRA_PRIMITIVE_TRANSLATION = {
    "ABSORPTION_PROXY_CVD_DIVERGENCE_DELTA_P75": ("price_delta_divergence_active",),
    "DELTA_IMPULSE_P95_SAME_SYMBOL_SESSION": ("abs_delta_p90",),
    "TICK_RANGE_EXPANSION_P95_SAME_SYMBOL_SESSION": ("range_p95",),
    "TICK_VELOCITY_BURST_P95_SAME_SYMBOL_SESSION": ("num_trades_p90",),
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


def route_session_to_tick_session(route_session: str | None) -> str | None:
    if route_session is None:
        return None
    return SESSION_BUCKET_BY_ROUTE_SESSION.get(route_session, route_session)


def scope_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("route_session"), row.get("horizon_id"), row.get("primitive_flag"))


def tick_control_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (row.get("symbol"), row.get("session_bucket"), row.get("horizon_id"), row.get("primitive_flag"))


def scope_to_tick_control_key(row: dict[str, Any]) -> tuple[Any, Any, Any, Any]:
    return (
        row.get("symbol"),
        route_session_to_tick_session(row.get("route_session")),
        row.get("horizon_id"),
        row.get("primitive_flag"),
    )


def primitive_flags(row: dict[str, Any]) -> set[str]:
    flags = row.get("primitive_flags")
    if isinstance(flags, list):
        return {str(flag) for flag in flags}
    if isinstance(flags, str):
        return {part.strip() for part in flags.split("|") if part.strip()}
    return set()


def tick_event_matches_scope(event_row: dict[str, Any], scope_row: dict[str, Any]) -> bool:
    return (
        event_row.get("symbol") == scope_row.get("symbol")
        and event_row.get("session_bucket") == route_session_to_tick_session(scope_row.get("route_session"))
        and event_row.get("horizon_id") == scope_row.get("horizon_id")
    )


def tick_event_has_scope_flag(event_row: dict[str, Any], scope_row: dict[str, Any]) -> bool:
    return str(scope_row.get("primitive_flag")) in primitive_flags(event_row)


def _delta(a: Any, b: Any) -> float | None:
    left = to_float(a)
    right = to_float(b)
    if left is None or right is None:
        return None
    return round(left - right, 6)


def exact_control_result_class(delta_metric: float | None, alignment_delta: float | None) -> str:
    if delta_metric is None:
        return "EXACT_CONTROL_NO_TARGET_PROXY_METRIC"
    if abs(delta_metric) < 1e-12:
        return "EXACT_CONTROL_FLAT_TARGET_DELTA_SPLIT_REQUIRED"
    alignment_nonnegative = alignment_delta is not None and alignment_delta >= 0
    if delta_metric > 0 and alignment_nonnegative:
        return "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA"
    if delta_metric > 0:
        return "EXACT_CONTROL_POSITIVE_TARGET_DELTA_ALIGNMENT_WEAKENED"
    if alignment_nonnegative:
        return "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT"
    return "EXACT_CONTROL_NEGATIVE_TARGET_AND_ALIGNMENT_DELTA_CURRENT_CLAIM_REJECTED"


def implementation_implication(result_class: str) -> str:
    if result_class == "EXACT_CONTROL_POSITIVE_TARGET_AND_ALIGNMENT_DELTA":
        return "branch_local_default_off_exact_control_score_candidate"
    if result_class == "EXACT_CONTROL_POSITIVE_TARGET_DELTA_ALIGNMENT_WEAKENED":
        return "split_alignment_before_exact_control_scalar_use"
    if result_class == "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT":
        return "preserve_as_horizon_or_directional_split_candidate"
    if result_class == "EXACT_CONTROL_NEGATIVE_TARGET_AND_ALIGNMENT_DELTA_CURRENT_CLAIM_REJECTED":
        return "reject_current_positive_claim_preserve_avoid_inverse_redesign_context"
    return "preserve_scope_for_redesign_or_source_recheck"


def exact_control_scope_construction(
    scope_row: dict[str, Any],
    tick_control_row: dict[str, Any] | None,
    denominator_event_count: int,
    flagged_event_count: int,
) -> dict[str, Any]:
    flagged_n = to_int((tick_control_row or {}).get("flagged_n"))
    control_n = to_int((tick_control_row or {}).get("control_n"))
    delta_metric = _delta(
        (tick_control_row or {}).get("flagged_mean_future_change_per_current_range"),
        (tick_control_row or {}).get("control_mean_future_change_per_current_range"),
    )
    alignment_delta = _delta(
        (tick_control_row or {}).get("flagged_delta_alignment_rate"),
        (tick_control_row or {}).get("control_delta_alignment_rate"),
    )
    if tick_control_row is None:
        status = "EXACT_CONTROL_CONSTRUCTION_TICK_M15_EXACT_SCOPE_MISSING"
    elif flagged_n >= N20:
        status = "EXACT_CONTROL_CONSTRUCTION_TICK_M15_N20_BUILT"
    elif flagged_n > 0:
        status = "EXACT_CONTROL_CONSTRUCTION_TICK_M15_UNDER_N20"
    else:
        status = "EXACT_CONTROL_CONSTRUCTION_TICK_M15_ZERO_FLAGGED"
    result_class = exact_control_result_class(delta_metric, alignment_delta)
    return {
        "exact_control_construction_surface": EXACT_CONTROL_CONSTRUCTION_SURFACE,
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "tick_session_bucket": route_session_to_tick_session(scope_row.get("route_session")),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "source_code_candidate_id": scope_row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": scope_row.get(
            "outside_gbpjpy_xauusd_current_branch_box"
        ),
        "input_scope_effective_n_row_id": scope_row.get("exact_control_scope_effective_n_row_id"),
        "input_scope_effective_n_status": scope_row.get("exact_control_scope_effective_n_status"),
        "input_effective_best_proxy_member_count": scope_row.get("effective_best_proxy_member_count"),
        "input_raw_best_proxy_member_count": scope_row.get("raw_best_proxy_member_count"),
        "input_best_available_proxy_relation": scope_row.get("best_available_proxy_relation"),
        "exact_control_construction_status": status,
        "exact_control_source": "TICK_M15_TARGET_MOVEMENT_FLAG_CONTROL_LEDGER",
        "exact_control_source_available": tick_control_row is not None,
        "exact_control_flagged_n": flagged_n,
        "exact_control_control_n": control_n,
        "exact_control_rows_needed_to_n20": rows_needed_to_n20(flagged_n),
        "denominator_event_rows_preserved": denominator_event_count,
        "flagged_event_rows_preserved": flagged_event_count,
        "event_count_matches_control_flagged_n": flagged_event_count == flagged_n,
        "control_event_count_matches_control_n": denominator_event_count == control_n,
        "flagged_mean_future_change_per_current_range": to_float(
            (tick_control_row or {}).get("flagged_mean_future_change_per_current_range")
        ),
        "control_mean_future_change_per_current_range": to_float(
            (tick_control_row or {}).get("control_mean_future_change_per_current_range")
        ),
        "exact_control_proxy_r_style_delta": delta_metric,
        "flagged_delta_alignment_rate": to_float((tick_control_row or {}).get("flagged_delta_alignment_rate")),
        "control_delta_alignment_rate": to_float((tick_control_row or {}).get("control_delta_alignment_rate")),
        "exact_control_alignment_delta": alignment_delta,
        "exact_control_result_class": result_class,
        "exact_control_implementation_implication": implementation_implication(result_class),
        "branch_local_exact_control_score_allowed": tick_control_row is not None and flagged_n >= N20,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def exact_control_blocker_construction(
    blocker_row: dict[str, Any],
    scope_construction_row: dict[str, Any] | None,
) -> dict[str, Any]:
    scope = scope_construction_row or {}
    result_class = str(scope.get("exact_control_result_class") or "EXACT_CONTROL_CONSTRUCTION_MISSING_SCOPE")
    current_claim_rejected = result_class == "EXACT_CONTROL_NEGATIVE_TARGET_AND_ALIGNMENT_DELTA_CURRENT_CLAIM_REJECTED"
    mixed_or_redesign = result_class in {
        "EXACT_CONTROL_POSITIVE_TARGET_DELTA_ALIGNMENT_WEAKENED",
        "EXACT_CONTROL_NEGATIVE_TARGET_DELTA_ALIGNMENT_POSITIVE_SPLIT",
        "EXACT_CONTROL_FLAT_TARGET_DELTA_SPLIT_REQUIRED",
    }
    return {
        "exact_control_construction_surface": EXACT_CONTROL_CONSTRUCTION_SURFACE,
        "input_exact_control_blocker_effective_n_row_id": blocker_row.get("exact_control_blocker_effective_n_row_id"),
        "input_exact_control_blocker_row_id": blocker_row.get("input_exact_control_blocker_row_id"),
        "input_default_off_implementation_row_id": blocker_row.get("input_default_off_implementation_row_id"),
        "input_detail_execution_row_id": blocker_row.get("input_detail_execution_row_id"),
        "symbol": blocker_row.get("symbol"),
        "route_session": blocker_row.get("route_session"),
        "tick_session_bucket": route_session_to_tick_session(blocker_row.get("route_session")),
        "horizon_id": blocker_row.get("horizon_id"),
        "primitive_flag": blocker_row.get("primitive_flag"),
        "source_code_candidate_id": blocker_row.get("source_code_candidate_id"),
        "outside_gbpjpy_xauusd_current_branch_box": blocker_row.get(
            "outside_gbpjpy_xauusd_current_branch_box"
        ),
        "input_effective_n_status": blocker_row.get("exact_control_effective_n_status"),
        "input_effective_best_proxy_member_count": blocker_row.get("effective_best_proxy_member_count"),
        "input_raw_best_proxy_member_count": blocker_row.get("raw_best_proxy_member_count"),
        "input_best_available_proxy_relation": blocker_row.get("best_available_proxy_relation"),
        "exact_control_construction_status": scope.get("exact_control_construction_status"),
        "exact_control_flagged_n": scope.get("exact_control_flagged_n"),
        "exact_control_control_n": scope.get("exact_control_control_n"),
        "exact_control_rows_needed_to_n20": scope.get("exact_control_rows_needed_to_n20"),
        "exact_control_proxy_r_style_delta": scope.get("exact_control_proxy_r_style_delta"),
        "exact_control_alignment_delta": scope.get("exact_control_alignment_delta"),
        "exact_control_result_class": result_class,
        "current_claim_rejected": current_claim_rejected,
        "claim_rejected_scope": (
            "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED" if current_claim_rejected else None
        ),
        "mixed_or_redesign_required": mixed_or_redesign,
        "missed_opportunity_audit": {
            "what_was_tried": "same-resource tick_m15 exact target-control denominator construction",
            "what_could_make_it_work": (
                "split by direction/session/horizon/entry geometry/source confidence or convert to avoid/inverse logic"
            ),
            "preserve_as": implementation_implication(result_class),
            "underlying_mechanism_preserved": True,
        },
        "exact_control_implementation_implication": implementation_implication(result_class),
        "branch_local_exact_control_score_allowed": scope.get("branch_local_exact_control_score_allowed", False),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def exact_control_denominator_event_row(
    scope_row: dict[str, Any],
    event_row: dict[str, Any],
    event_index: int,
) -> dict[str, Any]:
    flagged = tick_event_has_scope_flag(event_row, scope_row)
    return {
        "exact_control_construction_surface": EXACT_CONTROL_CONSTRUCTION_SURFACE,
        "source_event_index": event_index,
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "tick_session_bucket": route_session_to_tick_session(scope_row.get("route_session")),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "input_scope_effective_n_row_id": scope_row.get("exact_control_scope_effective_n_row_id"),
        "bar_open_utc": event_row.get("bar_open_utc"),
        "bar_close_utc": event_row.get("bar_close_utc"),
        "future_bar_open_utc": event_row.get("future_bar_open_utc"),
        "primitive_present": flagged,
        "future_change_per_current_range": to_float(event_row.get("future_change_per_current_range")),
        "future_change": to_float(event_row.get("future_change")),
        "future_abs_change": to_float(event_row.get("future_abs_change")),
        "delta_aligned_with_future": event_row.get("delta_aligned_with_future"),
        "price_aligned_with_future": event_row.get("price_aligned_with_future"),
        "delta_sign": event_row.get("delta_sign"),
        "future_sign": event_row.get("future_sign"),
        "source_route_id": event_row.get("route_id"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }


def sierra_translation_proxy_row(
    scope_row: dict[str, Any],
    sierra_control_row: dict[str, Any] | None,
    source_symbol: str | None,
    translated_primitive_flag: str | None,
) -> dict[str, Any]:
    if translated_primitive_flag is None:
        status = "SIERRA_TRANSLATION_NO_TAXONOMY_EQUIVALENT"
    elif sierra_control_row is None:
        status = "SIERRA_TRANSLATION_PROXY_SCOPE_MISSING"
    elif to_int(sierra_control_row.get("flagged_stats", {}).get("n")) >= N20:
        status = "SIERRA_TRANSLATION_PROXY_N20_AVAILABLE_NOT_EXACT"
    else:
        status = "SIERRA_TRANSLATION_PROXY_UNDER_N20_NOT_EXACT"
    flagged_stats = (sierra_control_row or {}).get("flagged_stats", {}) or {}
    denominator_stats = (sierra_control_row or {}).get("denominator_stats", {}) or {}
    flagged_mean = to_float(flagged_stats.get("mean_future_change_per_current_range"))
    denominator_mean = to_float(denominator_stats.get("mean_future_change_per_current_range"))
    return {
        "exact_control_construction_surface": EXACT_CONTROL_CONSTRUCTION_SURFACE,
        "symbol": scope_row.get("symbol"),
        "route_session": scope_row.get("route_session"),
        "tick_session_bucket": route_session_to_tick_session(scope_row.get("route_session")),
        "horizon_id": scope_row.get("horizon_id"),
        "primitive_flag": scope_row.get("primitive_flag"),
        "input_scope_effective_n_row_id": scope_row.get("exact_control_scope_effective_n_row_id"),
        "sierra_source_symbol": source_symbol,
        "sierra_translated_primitive_flag": translated_primitive_flag,
        "sierra_translation_status": status,
        "sierra_proxy_is_exact_control": False,
        "sierra_flagged_n": to_int(flagged_stats.get("n")),
        "sierra_denominator_n": to_int(denominator_stats.get("n")),
        "sierra_proxy_delta": _delta(flagged_mean, denominator_mean),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
