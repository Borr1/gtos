"""Compute branch-local result rows from unified system action results."""

from __future__ import annotations

from collections import Counter
from typing import Any


UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_computed_actions.py"
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int(value: Any) -> int:
    numeric = to_float(value)
    return int(numeric) if numeric is not None else 0


def clamp(value: float, lower: float = -1.0, upper: float = 1.0) -> float:
    return round(max(lower, min(upper, value)), 6)


def _first_numeric(row: dict[str, Any], keys: tuple[str, ...]) -> tuple[float | None, str | None]:
    for key in keys:
        value = to_float(row.get(key))
        if value is not None:
            return value, key
    return None, None


def _sidecar_score(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> tuple[float | None, str]:
    side = sidecar or {}
    component = str(action_row.get("source_component") or "")
    if component == "default_off_scorer_application":
        score, key = _first_numeric(side, ("default_off_scorer_event_score", "default_off_application_score"))
        return score, key or "default_off_scorer_event_score_missing"
    if component == "market_gap_code":
        score, key = _first_numeric(side, ("proxy_score", "candidate_score_proxy", "market_gap_decision_score"))
        return score, key or "market_gap_proxy_score_missing"
    if component == "shadow_source_guard":
        score, key = _first_numeric(side, ("bundle_priority_score", "shadow_scorer_score", "materialization_proxy_score"))
        return score, key or "shadow_source_guard_priority_score_missing"
    score, key = _first_numeric(
        side,
        (
            "proxy_score",
            "candidate_score_proxy",
            "bundle_priority_score",
            "shadow_scorer_score",
            "default_off_scorer_event_score",
        ),
    )
    if score is not None:
        return score, key or "sidecar_score"
    score = to_float(action_row.get("proxy_numeric_score"))
    if score is not None:
        return score, "action_proxy_numeric_score"
    return None, "no_numeric_proxy_available"


def _score_delta_from_score(score: float | None, basis: str) -> float | None:
    if score is None:
        return None
    # Default-off event scores are already signed scorer deltas; most other sidecar scores are 0..1 priorities.
    if basis in {"default_off_scorer_event_score", "default_off_application_score"}:
        return clamp(score)
    if 0.0 <= score <= 1.0:
        return clamp(score - 0.5)
    return clamp(score)


def _delta_class(delta: float | None, source_required: bool = False) -> str:
    if delta is None:
        return "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED" if source_required else "COMPUTED_DELTA_NOT_AVAILABLE"
    if delta >= 0.15:
        return "COMPUTED_PROXY_DELTA_STRONG_POSITIVE"
    if delta >= 0.05:
        return "COMPUTED_PROXY_DELTA_POSITIVE"
    if delta > -0.05:
        return "COMPUTED_PROXY_DELTA_NEUTRAL"
    if delta > -0.15:
        return "COMPUTED_PROXY_DELTA_WEAK_NEGATIVE"
    return "COMPUTED_PROXY_DELTA_STRONG_NEGATIVE"


def _target_stop_score_from_status(status: str) -> tuple[float | None, str]:
    text = status.upper()
    if "TARGET_TOUCH_FIRST" in text or "TARGET_FIRST" in text:
        return 0.65, "TARGET_FIRST_PROXY"
    if "STOP_TOUCH_FIRST" in text or "STOP_FIRST" in text:
        return -0.65, "STOP_FIRST_PROXY"
    if "NO_TARGET_OR_STOP_TOUCH" in text or "NO_TOUCH" in text:
        return 0.05, "NO_TOUCH_PROXY"
    if "AMBIG" in text or "UNRESOLVED" in text:
        return None, "TARGET_STOP_ORDER_AMBIGUOUS"
    return None, "TARGET_STOP_STATUS_NOT_AVAILABLE"


def _status_count_delta(counts: Any) -> tuple[float | None, str]:
    if not isinstance(counts, dict) or not counts:
        return None, "NO_TARGET_STOP_COUNT_DICT"
    target = 0
    stop = 0
    ambiguous = 0
    for key, value in counts.items():
        count = to_int(value)
        text = str(key).upper()
        if "TARGET" in text and "STOP" not in text:
            target += count
        elif "STOP" in text and "TARGET" not in text:
            stop += count
        elif "TARGET" in text and "STOP" in text:
            ambiguous += count
    denom = target + stop + ambiguous
    if denom <= 0:
        return None, "NO_TARGET_STOP_TOUCH_COUNTS"
    return clamp((target - stop) / denom), "TARGET_STOP_COUNT_DELTA_PROXY"


def _nofill_sidecar_score(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> tuple[float | None, str]:
    side = sidecar or {}
    component = str(action_row.get("source_component") or "")
    if component == "nofill_near_miss_market_entry":
        score, basis = _target_stop_score_from_status(str(side.get("market_first_touch_status") or ""))
        return score, basis
    if component == "nofill_near_miss_offset":
        score, basis = _target_stop_score_from_status(str(side.get("first_touch_status_offset_proxy") or ""))
        return score, basis
    count_score, count_basis = _status_count_delta(side.get("m1_spread_adjusted_first_touch_status_counts"))
    if count_score is not None:
        if component == "nofill_far_miss_avoid":
            return clamp(-count_score), "AVOID_FILTER_INVERTED_" + count_basis
        return count_score, count_basis
    distance = to_float(side.get("miss_distance_to_zero_over_rolling_median_range"))
    miss_class = str(side.get("confirmed_nofill_miss_class") or side.get("confirmed_nofill_miss_class_counts") or "")
    if component == "nofill_far_miss_avoid":
        if distance is not None and distance >= 1.0:
            return 0.35, "FAR_MISS_DISTANCE_AVOID_PROXY"
        if "SOURCE_ALIGNMENT_CONFLICT" in miss_class:
            return 0.25, "SOURCE_ALIGNMENT_CONFLICT_AVOID_PROXY"
        return 0.10, "AVOID_CONTEXT_PROXY"
    if component == "nofill_far_miss_retest":
        if distance is not None and distance >= 1.0:
            return -0.25, "FAR_MISS_RETEST_WEAK_PROXY"
        return 0.05, "RETEST_REDESIGN_CONTEXT_PROXY"
    if component == "nofill_far_miss_family":
        confirmed = to_int(side.get("friction_family_confirmed_nofill_signature_rows"))
        nonconfirmed = to_int(side.get("friction_family_nonconfirmed_signature_rows"))
        denom = confirmed + nonconfirmed
        if denom:
            return clamp(0.5 - (confirmed / denom)), "FAMILY_CONFIRMED_NOFILL_SHARE_INVERTED_PROXY"
    if component == "nofill_far_miss_source_confidence":
        if "TICK_ABSENT" in str(side.get("source_confidence_branch_status") or ""):
            return None, "SOURCE_CONFIDENCE_TICK_ABSENT_REPAIR_REQUIRED"
    return None, "NOFILL_PROXY_NOT_COMPUTABLE_FROM_CURRENT_SIDECAR"


def _implementation_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    score, basis = _sidecar_score(action_row, sidecar)
    delta = _score_delta_from_score(score, basis)
    return {
        "computed_action_family": "DEFAULT_OFF_CODE_CANDIDATE",
        "computed_action_status": (
            "DEFAULT_OFF_CODE_CANDIDATE_PROXY_DELTA_COMPUTED"
            if delta is not None
            else "DEFAULT_OFF_CODE_CANDIDATE_SPEC_ONLY_SOURCE_CONTEXT"
        ),
        "computed_decision": (
            "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD"
            if delta is not None and delta >= 0.05
            else "KEEP_DEFAULT_OFF_CODE_CANDIDATE_CONTROL_OR_REDESIGN_REQUIRED"
        ),
        "computed_proxy_score": score,
        "computed_proxy_score_basis": basis,
        "computed_proxy_delta": delta,
        "computed_proxy_delta_class": _delta_class(delta),
        "pass_control_delta_proxy": delta,
        "expectancy_style_proxy_delta": delta,
        "computed_next_action": "materialize_default_off_code_spec_with_guard_and_control_lookup",
    }


def _score_with_control_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    score, basis = _sidecar_score(action_row, sidecar)
    delta = _score_delta_from_score(score, basis)
    return {
        "computed_action_family": "SCORE_WITH_CONTROL",
        "computed_action_status": (
            "CONTROL_SCORE_DELTA_COMPUTED_FROM_SOURCE_SIDECAR"
            if delta is not None
            else "CONTROL_SCORE_DELTA_REQUIRES_EXACT_CONTROL_OR_SOURCE_REPAIR"
        ),
        "computed_decision": (
            "KEEP_SCORE_ROW_FOR_CONTROLLED_RESEARCH_COMPARISON"
            if delta is not None and delta >= -0.05
            else "REPAIR_OR_REDESIGN_BEFORE_SCORE_ROW_CAN_INFORM_SYSTEM"
        ),
        "computed_proxy_score": score,
        "computed_proxy_score_basis": basis,
        "computed_proxy_delta": delta,
        "computed_proxy_delta_class": _delta_class(delta, source_required=delta is None),
        "pass_control_delta_proxy": delta,
        "expectancy_style_proxy_delta": delta,
        "computed_next_action": "compare_score_delta_against_same_scope_control_and_guard_exact_denominator",
    }


def _source_repair_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    side = sidecar or {}
    score, basis = _sidecar_score(action_row, sidecar)
    delta = _score_delta_from_score(score, basis)
    rows_needed = max(
        to_int(side.get("best_proxy_rows_needed_to_n20")),
        to_int(side.get("additional_flagged_rows_needed_for_n20")),
        to_int(side.get("source_rows_needed_to_n20")),
    )
    status = str(action_row.get("action_execution_status") or "")
    if status == "EXACT_CONTROL_DENOMINATOR_BUILD_ACTION_MATERIALIZED":
        computed_status = "EXACT_CONTROL_DENOMINATOR_BUILD_RESULT_ROW"
        decision = "BUILD_OR_RECONSTRUCT_EXACT_CONTROL_DENOMINATOR_THEN_RESCORE"
    elif status == "SATISFIED_SOURCE_ATTACHED_TO_REPLAY_ACTION":
        computed_status = "SATISFIED_SOURCE_ATTACHED_TO_REPLAY_RESULT_ROW"
        decision = "ATTACH_SATISFIED_SOURCE_TO_ENTRY_REPLAY_AND_SCORE_VARIANT"
    else:
        computed_status = "SOURCE_OR_CONTROL_REPAIR_RESULT_ROW"
        decision = "MATERIALIZE_SOURCE_OR_PROXY_CONTROL_THEN_RESCORE"
    return {
        "computed_action_family": "SOURCE_CONTROL_REPAIR",
        "computed_action_status": computed_status,
        "computed_decision": decision,
        "computed_proxy_score": score,
        "computed_proxy_score_basis": basis,
        "computed_proxy_delta": delta,
        "computed_proxy_delta_class": _delta_class(delta, source_required=delta is None),
        "pass_control_delta_proxy": delta,
        "expectancy_style_proxy_delta": delta,
        "source_rows_needed_to_n20_proxy": rows_needed,
        "source_repair_required": computed_status != "SATISFIED_SOURCE_ATTACHED_TO_REPLAY_RESULT_ROW",
        "computed_next_action": "execute_source_control_denominator_build_or_replay_attachment",
    }


def _redesign_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    score, basis = _nofill_sidecar_score(action_row, sidecar)
    delta = _score_delta_from_score(score, basis)
    component = str(action_row.get("source_component") or "")
    if component == "nofill_far_miss_avoid":
        status = "NOFILL_AVOID_OR_INVERSE_VARIANT_PROXY_SCORED"
        decision = "SCORE_AVOID_INVERSE_VARIANT_WITH_SIBLING_CONTROL"
    elif component == "nofill_far_miss_retest":
        status = "NOFILL_RETEST_REDESIGN_PROXY_SCORED"
        decision = "REDESIGN_RETEST_ENTRY_OR_TRANSFER_TO_AVOID_MARKET_ENTRY"
    elif component == "nofill_near_miss_offset":
        status = "NEAR_MISS_OFFSET_TARGET_STOP_PROXY_SCORED"
        decision = "COMPARE_OFFSET_ENTRY_VARIANT_TO_STATUS_QUO_CONTROL"
    elif component == "nofill_near_miss_market_entry":
        status = "NEAR_MISS_MARKET_ENTRY_TARGET_STOP_PROXY_SCORED"
        decision = "COMPARE_MARKET_ENTRY_PROXY_TO_RETEST_LIMIT_CONTROL"
    elif component == "nofill_far_miss_family":
        status = "NOFILL_FAMILY_SPLIT_PROXY_SCORED"
        decision = "SPLIT_FAMILY_BY_SYMBOL_SESSION_MISS_CAUSE_AND_SOURCE_CONFIDENCE"
    else:
        status = "NOFILL_REDESIGN_CONTEXT_PROXY_PRESERVED"
        decision = "PRESERVE_SOURCE_CONFIDENCE_OR_CONTEXT_GUARD"
    return {
        "computed_action_family": "NOFILL_REDESIGN_SCORING",
        "computed_action_status": status,
        "computed_decision": decision,
        "computed_proxy_score": score,
        "computed_proxy_score_basis": basis,
        "computed_proxy_delta": delta,
        "computed_proxy_delta_class": _delta_class(delta, source_required=delta is None),
        "pass_control_delta_proxy": delta,
        "expectancy_style_proxy_delta": delta,
        "computed_next_action": "score_variant_with_target_stop_source_cost_and_status_quo_or_inverse_control",
    }


def _guard_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    score, basis = _sidecar_score(action_row, sidecar)
    delta = _score_delta_from_score(score, basis)
    guard_type = str(action_row.get("materialized_artifact_kind") or "guard_general")
    return {
        "computed_action_family": "GUARD_REGISTRY_SPEC",
        "computed_action_status": "GUARD_REGISTRY_SPEC_COMPUTED",
        "computed_decision": (
            "REGISTER_DENOMINATOR_OR_SOURCE_CONFIDENCE_GUARD_DEFAULT_OFF"
            if guard_type != "guard_nofill_source_confidence"
            else "REGISTER_NOFILL_SOURCE_CONFIDENCE_CONTEXT_GUARD_DEFAULT_OFF"
        ),
        "computed_proxy_score": score,
        "computed_proxy_score_basis": basis,
        "computed_proxy_delta": delta,
        "computed_proxy_delta_class": _delta_class(delta),
        "pass_control_delta_proxy": None,
        "expectancy_style_proxy_delta": None,
        "guard_strength_proxy": score,
        "computed_next_action": "attach_guard_to_default_off_or_nofill_variant_before_any_scoring",
    }


def _audit_status(action_row: dict[str, Any], sidecar: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "computed_action_family": "CURRENT_CLAIM_OPPORTUNITY_AUDIT",
        "computed_action_status": "CURRENT_CLAIM_REJECTION_OPPORTUNITY_ROUTE_COMPUTED",
        "computed_decision": "REJECT_CURRENT_CLAIM_ONLY_ROUTE_MECHANISM_TO_REDESIGN_AVOID_CONTEXT_SOURCE_CAPTURE_OR_MERGE",
        "computed_proxy_score": None,
        "computed_proxy_score_basis": "audit_preservation_no_scalar",
        "computed_proxy_delta": None,
        "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_AUDIT_ONLY",
        "pass_control_delta_proxy": None,
        "expectancy_style_proxy_delta": None,
        "computed_next_action": "merge_preserved_mechanism_into_redesign_or_failure_intelligence",
    }


def computed_action_result(
    action_row: dict[str, Any],
    index: int,
    sidecar: dict[str, Any] | None = None,
) -> dict[str, Any]:
    family = str(action_row.get("action_result_family") or "")
    if family == "IMPLEMENTATION_RESULT":
        computed = _implementation_status(action_row, sidecar)
    elif family == "SCORE_WITH_CONTROL_RESULT":
        computed = _score_with_control_status(action_row, sidecar)
    elif family == "SOURCE_CONTROL_REPAIR_RESULT":
        computed = _source_repair_status(action_row, sidecar)
    elif family == "REDESIGN_EXECUTION_RESULT":
        computed = _redesign_status(action_row, sidecar)
    elif family == "GUARD_RESULT":
        computed = _guard_status(action_row, sidecar)
    elif family == "AUDIT_PRESERVATION_RESULT":
        computed = _audit_status(action_row, sidecar)
    else:
        computed = {
            "computed_action_family": "RECHECK",
            "computed_action_status": "RECHECK_REPAIR_ROUTE_COMPUTED",
            "computed_decision": "RECHECK_HORIZON_SOURCE_TARGETABILITY_AND_ROUTE_TO_REPAIR_OR_REDESIGN",
            "computed_proxy_score": None,
            "computed_proxy_score_basis": "recheck_no_scalar",
            "computed_proxy_delta": None,
            "computed_proxy_delta_class": "COMPUTED_DELTA_NOT_AVAILABLE_RECHECK_ONLY",
            "pass_control_delta_proxy": None,
            "expectancy_style_proxy_delta": None,
            "computed_next_action": "execute_recheck_repair_redesign_or_current_claim_audit",
        }
    return {
        "unified_system_computed_action_surface": UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE,
        "unified_system_computed_action_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-COMPUTED-ACTION-{index:06d}",
        "input_unified_system_action_result_row_id": action_row.get("unified_system_action_result_row_id"),
        "input_unified_system_work_order_row_id": action_row.get("input_unified_system_work_order_row_id"),
        "source_component": action_row.get("source_component"),
        "source_row_id": action_row.get("source_row_id"),
        "source_sidecar_joined": bool(sidecar),
        "source_sidecar_row_id": _sidecar_id(sidecar or {}),
        "symbol": action_row.get("symbol"),
        "route_session": action_row.get("route_session"),
        "horizon_id": action_row.get("horizon_id"),
        "primitive_flag": action_row.get("primitive_flag"),
        "mechanical_scope_key": action_row.get("mechanical_scope_key"),
        "action_result_family": action_row.get("action_result_family"),
        "action_execution_status": action_row.get("action_execution_status"),
        "target_artifact_kind": action_row.get("target_artifact_kind"),
        "market_expansion_row_id": action_row.get("market_expansion_row_id"),
        "market_expansion_decision": action_row.get("market_expansion_decision"),
        "tradability_status": action_row.get("tradability_status"),
        "available_timeframes": action_row.get("available_timeframes", []),
        "exact_R_availability": action_row.get("exact_R_availability"),
        "proxy_R_availability": action_row.get("proxy_R_availability"),
        "fillability_no_fill_status": action_row.get("fillability_no_fill_status"),
        "source_status": action_row.get("source_status"),
        "source_confidence_status": action_row.get("source_confidence_status"),
        "success_or_failure_cause": action_row.get("success_or_failure_cause"),
        "implementation_implication": action_row.get("implementation_implication"),
        "current_claim_only_rejection_scope": action_row.get("current_claim_only_rejection_scope"),
        "missed_opportunity_preserved": action_row.get("missed_opportunity_preserved") is not False,
        "action_result_consumed_in_computed_layer": True,
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        **computed,
    }


def _sidecar_id(row: dict[str, Any]) -> Any:
    for key in (
        "default_off_application_row_id",
        "scorer_application_row_id",
        "market_gap_code_id",
        "bundle_row_id",
        "family_synthesis_id",
        "avoid_filter_branch_id",
        "retest_redesign_branch_id",
        "source_confidence_branch_id",
        "near_miss_entry_control_offset_branch_id",
        "near_miss_entry_control_market_branch_id",
        "near_miss_entry_control_source_requirement_id",
    ):
        if row.get(key):
            return row.get(key)
    return row.get("source_row_id") or row.get("input_row_id")


def computed_action_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    family_counts = Counter(str(row.get("computed_action_family")) for row in rows)
    status_counts = Counter(str(row.get("computed_action_status")) for row in rows)
    delta_counts = Counter(str(row.get("computed_proxy_delta_class")) for row in rows)
    joined = sum(1 for row in rows if row.get("source_sidecar_joined"))
    delta_rows = sum(1 for row in rows if row.get("computed_proxy_delta") is not None)
    return {
        "unified_system_computed_action_surface": UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE,
        "computed_action_rollup_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-COMPUTED-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "computed_action_rows": len(rows),
        "source_sidecar_joined_rows": joined,
        "computed_delta_rows": delta_rows,
        "computed_action_family_counts": {key: int(family_counts[key]) for key in sorted(family_counts)},
        "computed_action_status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "computed_proxy_delta_class_counts": {key: int(delta_counts[key]) for key in sorted(delta_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def computed_market_timeframe_expansion_row(
    base_row: dict[str, Any],
    computed_rows: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    family_counts = Counter(str(row.get("computed_action_family")) for row in computed_rows)
    status_counts = Counter(str(row.get("computed_action_status")) for row in computed_rows)
    delta_counts = Counter(str(row.get("computed_proxy_delta_class")) for row in computed_rows)
    component_counts = Counter(str(row.get("source_component")) for row in computed_rows)
    missing_evidence = list(base_row.get("missing_evidence") or [])
    if not computed_rows:
        missing_evidence.append("no_current_computed_action_row_for_inventory_or_unconsumed_scope")
    replay_counts = dict(base_row.get("replay_result_row_counts") or {})
    replay_counts.update(
        {
            "computed_action_rows": len(computed_rows),
            "computed_delta_rows": sum(1 for row in computed_rows if row.get("computed_proxy_delta") is not None),
            "computed_source_sidecar_joined_rows": sum(1 for row in computed_rows if row.get("source_sidecar_joined")),
            "computed_action_family_counts": {key: int(family_counts[key]) for key in sorted(family_counts)},
            "computed_action_status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
            "computed_proxy_delta_class_counts": {key: int(delta_counts[key]) for key in sorted(delta_counts)},
            "computed_source_component_counts": {key: int(component_counts[key]) for key in sorted(component_counts)},
        }
    )
    return {
        "unified_system_computed_action_surface": UNIFIED_SYSTEM_COMPUTED_ACTION_SURFACE,
        "market_timeframe_session_horizon_expansion_row_id": (
            f"OHLC-GTOS-UNIFIED-COMPUTED-MARKET-EXPANSION-{index:06d}"
        ),
        "input_market_timeframe_session_horizon_expansion_row_id": base_row.get(
            "market_timeframe_session_horizon_expansion_row_id"
        ),
        "coverage_source": base_row.get("coverage_source"),
        "symbol": base_row.get("symbol"),
        "broker_proxy_mapping": base_row.get("broker_proxy_mapping"),
        "tradability_status": base_row.get("tradability_status"),
        "data_source": base_row.get("data_source", []),
        "source_files": base_row.get("source_files", []),
        "available_timeframes": base_row.get("available_timeframes", []),
        "session_kz_offkz_coverage": base_row.get("session_kz_offkz_coverage", []),
        "route_session": base_row.get("route_session"),
        "horizon_id": base_row.get("horizon_id"),
        "primitive_flag": base_row.get("primitive_flag"),
        "source_component": base_row.get("source_component"),
        "spread_cost_source": base_row.get("spread_cost_source"),
        "replay_result_row_counts": replay_counts,
        "exact_R_availability": base_row.get("exact_R_availability"),
        "proxy_R_availability": base_row.get("proxy_R_availability"),
        "fillability_no_fill_status": base_row.get("fillability_no_fill_status"),
        "missing_evidence": missing_evidence,
        "decision": base_row.get("decision"),
        "computed_action_rows": len(computed_rows),
        "computed_delta_rows": replay_counts["computed_delta_rows"],
        "computed_source_sidecar_joined_rows": replay_counts["computed_source_sidecar_joined_rows"],
        "computed_action_family_counts": replay_counts["computed_action_family_counts"],
        "computed_action_status_counts": replay_counts["computed_action_status_counts"],
        "computed_proxy_delta_class_counts": replay_counts["computed_proxy_delta_class_counts"],
        "computed_source_component_counts": replay_counts["computed_source_component_counts"],
        "current_output_path_coverage": (
            "CURRENT_COMPUTED_ACTION_ROWS_CONSUMED_FOR_MARKET_SCOPE"
            if computed_rows
            else "MARKET_SCOPE_PRESERVED_WITHOUT_CURRENT_COMPUTED_ACTION_ROWS"
        ),
        "all_material_scope_rows_preserved": True,
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
