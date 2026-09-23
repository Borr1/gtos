"""Convert computed unified-system rows into concrete branch-local execution decisions."""

from __future__ import annotations

from collections import Counter
from typing import Any


UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_implementation_execution.py"
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


def _scope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "market_expansion_row_id": row.get("market_expansion_row_id"),
        "market_expansion_decision": row.get("market_expansion_decision"),
        "tradability_status": row.get("tradability_status"),
        "available_timeframes": row.get("available_timeframes", []),
        "computed_proxy_delta": row.get("computed_proxy_delta"),
        "computed_proxy_delta_class": row.get("computed_proxy_delta_class"),
        "computed_proxy_score_basis": row.get("computed_proxy_score_basis"),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def _delta_tier(delta: float | None) -> str:
    if delta is None:
        return "NO_NUMERIC_DELTA"
    if delta >= 0.15:
        return "STRONG_POSITIVE_DELTA"
    if delta >= 0.05:
        return "POSITIVE_DELTA"
    if delta > -0.05:
        return "NEUTRAL_DELTA"
    if delta > -0.15:
        return "WEAK_NEGATIVE_DELTA"
    return "STRONG_NEGATIVE_DELTA"


def _decision_for_computed(row: dict[str, Any]) -> tuple[str, str, str]:
    family = str(row.get("computed_action_family") or "")
    status = str(row.get("computed_action_status") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if family == "DEFAULT_OFF_CODE_CANDIDATE":
        if delta is not None and delta >= 0.05:
            return (
                "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC_WITH_GUARD",
                "write_default_off_module_spec_attach_guard_and_control_lookup",
                "IMPLEMENTATION_SPEC_READY_DEFAULT_OFF",
            )
        return (
            "HOLD_DEFAULT_OFF_MODULE_SPEC_FOR_CONTROL_OR_REDESIGN",
            "write_spec_but_require_control_repair_before_scoring",
            "IMPLEMENTATION_SPEC_REQUIRES_REPAIR",
        )
    if family == "SOURCE_CONTROL_REPAIR":
        if status == "EXACT_CONTROL_DENOMINATOR_BUILD_RESULT_ROW":
            return (
                "BUILD_EXACT_CONTROL_DENOMINATOR",
                "build_or_reconstruct_exact_control_then_rescore",
                "SOURCE_BUILDER_EXACT_CONTROL",
            )
        if status == "SATISFIED_SOURCE_ATTACHED_TO_REPLAY_RESULT_ROW":
            return (
                "ATTACH_SATISFIED_SOURCE_TO_REPLAY",
                "attach_source_to_entry_replay_and_score_variant",
                "SOURCE_BUILDER_ATTACH_AND_REPLAY",
            )
        return (
            "REPAIR_SOURCE_OR_PROXY_CONTROL",
            "materialize_source_or_proxy_control_then_rescore",
            "SOURCE_BUILDER_REPAIR_OR_PROXY",
        )
    if family == "SCORE_WITH_CONTROL":
        if delta is None:
            return (
                "BUILD_CONTROL_OR_SOURCE_BEFORE_SCORE_USE",
                "repair_exact_control_or_source_before_score_comparison",
                "SCORE_CONTROL_REPAIR_REQUIRED",
            )
        if delta >= 0.05:
            return (
                "KEEP_SCORE_WITH_CONTROL_COMPARISON",
                "compare_positive_delta_against_same_scope_control",
                "SCORE_CONTROL_POSITIVE",
            )
        return (
            "REDESIGN_OR_CONTEXTUALIZE_SCORE_WITH_CONTROL",
            "preserve_score_as_context_or_redesign_input",
            "SCORE_CONTROL_WEAK_OR_NEGATIVE",
        )
    if family == "NOFILL_REDESIGN_SCORING":
        if delta is None:
            return (
                "REPLAY_OR_SOURCE_REPAIR_BEFORE_NOFILL_DECISION",
                "run_target_stop_or_source_repair_before_variant_decision",
                "NOFILL_VARIANT_REPLAY_REQUIRED",
            )
        if delta >= 0.05:
            return (
                "KEEP_NOFILL_VARIANT_FOR_COMPARATOR",
                "compare_variant_against_status_quo_and_sibling_control",
                "NOFILL_VARIANT_POSITIVE_PROXY",
            )
        if delta <= -0.15:
            return (
                "ROUTE_NOFILL_VARIANT_TO_AVOID_OR_INVERSE",
                "preserve_negative_variant_as_avoid_inverse_or_entry_failure_intelligence",
                "NOFILL_VARIANT_NEGATIVE_PROXY",
            )
        return (
            "STRESS_NOFILL_VARIANT_WITH_CONTROL",
            "stress_variant_cost_source_and_target_stop_controls",
            "NOFILL_VARIANT_WEAK_PROXY",
        )
    if family == "GUARD_REGISTRY_SPEC":
        return (
            "REGISTER_GUARD_BINDING_DEFAULT_OFF",
            "attach_guard_before_any_score_or_variant_use",
            "GUARD_BINDING_SPEC",
        )
    if family == "CURRENT_CLAIM_OPPORTUNITY_AUDIT":
        return (
            "PRESERVE_CURRENT_CLAIM_REJECTION_OPPORTUNITY",
            "route_mechanism_to_redesign_avoid_context_source_capture_or_merge",
            "CURRENT_CLAIM_AUDIT_ROUTE",
        )
    return (
        "RECHECK_AND_ROUTE_COMPUTED_ROW",
        "recheck_horizon_source_targetability_then_route",
        "RECHECK_ROUTE",
    )


def implementation_execution_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    action_class, next_action, decision_class = _decision_for_computed(row)
    delta = to_float(row.get("computed_proxy_delta"))
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "implementation_execution_decision_row_id": (
            f"OHLC-GTOS-UNIFIED-IMPLEMENTATION-EXECUTION-{index:06d}"
        ),
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "input_unified_system_action_result_row_id": row.get("input_unified_system_action_result_row_id"),
        "computed_action_family": row.get("computed_action_family"),
        "computed_action_status": row.get("computed_action_status"),
        "execution_action_class": action_class,
        "execution_next_action": next_action,
        "execution_decision_class": decision_class,
        "execution_priority_tier": _delta_tier(delta),
        "computed_row_consumed_in_implementation_execution": True,
        "missed_opportunity_preserved": row.get("missed_opportunity_preserved") is not False,
        **_scope(row),
    }


def default_off_module_spec(row: dict[str, Any], index: int) -> dict[str, Any]:
    component = str(row.get("source_component") or "")
    if component == "registry_scorer_module":
        module_family = "exact_control_redesign_registry_module"
    elif component == "shadow_source_guard":
        module_family = "source_guarded_shadow_rule_module"
    elif component == "market_gap_code":
        module_family = "market_gap_entry_or_avoid_module"
    elif component == "default_off_scorer_application":
        module_family = "default_off_scorer_application_module"
    else:
        module_family = "branch_local_default_off_module"
    delta = to_float(row.get("computed_proxy_delta"))
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "default_off_module_spec_row_id": f"OHLC-GTOS-UNIFIED-DEFAULT-OFF-MODULE-SPEC-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "module_spec_status": (
            "DEFAULT_OFF_MODULE_SPEC_READY_WITH_POSITIVE_PROXY"
            if delta is not None and delta >= 0.05
            else "DEFAULT_OFF_MODULE_SPEC_CONTROL_OR_REDESIGN_REQUIRED"
        ),
        "module_family": module_family,
        "candidate_function_name": f"score_{module_family}_{index:05d}",
        "mechanical_rule_expression": (
            "match symbol/session/horizon/primitive and emit branch-local research-only module observation; "
            "attach required guard and control lookup before any score use"
        ),
        "required_runtime_fields": ["symbol", "route_session", "horizon_id", "primitive_flag"],
        "guard_requirements": ["source_confidence_guard", "same_scope_control_lookup", "default_off_runtime_disabled"],
        "score_policy": "default_off_proxy_delta_only_no_unconditional_scalar_use",
        "default_off": True,
        **_scope(row),
    }


def source_builder_spec(row: dict[str, Any], index: int) -> dict[str, Any]:
    action_class, next_action, decision_class = _decision_for_computed(row)
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "source_builder_spec_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-BUILDER-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "source_builder_status": decision_class,
        "source_builder_action_class": action_class,
        "source_builder_next_action": next_action,
        "source_rows_needed_to_n20_proxy": row.get("source_rows_needed_to_n20_proxy"),
        "source_repair_required": row.get("source_repair_required"),
        "builder_output_contract": "exact_control_or_source_proxy_result_then_rescore_same_scope",
        **_scope(row),
    }


def nofill_variant_comparator(row: dict[str, Any], index: int) -> dict[str, Any]:
    action_class, next_action, decision_class = _decision_for_computed(row)
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "nofill_variant_comparator_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-COMPARATOR-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "variant_comparator_status": decision_class,
        "variant_action_class": action_class,
        "variant_next_action": next_action,
        "target_stop_proxy_basis": row.get("computed_proxy_score_basis"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "status_quo_control_required": True,
        "opportunity_preserved_as": (
            "positive_variant_candidate"
            if to_float(row.get("computed_proxy_delta")) is not None
            and to_float(row.get("computed_proxy_delta")) >= 0.05
            else "avoid_inverse_retest_source_or_entry_redesign_intelligence"
        ),
        **_scope(row),
    }


def guard_binding_spec(row: dict[str, Any], index: int) -> dict[str, Any]:
    component = str(row.get("source_component") or "")
    guard_family = "nofill_source_confidence_guard" if component == "nofill_far_miss_source_confidence" else "denominator_or_source_guard"
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "guard_binding_spec_row_id": f"OHLC-GTOS-UNIFIED-GUARD-BINDING-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "guard_binding_status": "GUARD_BINDING_SPEC_REGISTERED_DEFAULT_OFF",
        "guard_family": guard_family,
        "guard_strength_proxy": row.get("guard_strength_proxy"),
        "guard_policy": "block_uncontrolled_score_or_variant_use_until_required_source_control_available",
        "attached_to_family": row.get("action_result_family"),
        **_scope(row),
    }


def score_control_execution(row: dict[str, Any], index: int) -> dict[str, Any]:
    action_class, next_action, decision_class = _decision_for_computed(row)
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "score_control_execution_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "score_control_status": decision_class,
        "score_control_action_class": action_class,
        "score_control_next_action": next_action,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": row.get("computed_proxy_delta") is None,
        **_scope(row),
    }


def current_claim_audit_route(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "current_claim_audit_route_row_id": f"OHLC-GTOS-UNIFIED-CURRENT-CLAIM-AUDIT-{index:05d}",
        "input_unified_system_computed_action_row_id": row.get("unified_system_computed_action_row_id"),
        "audit_route_status": "CURRENT_CLAIM_REJECTED_MECHANISM_AND_OPPORTUNITY_PRESERVED",
        "audit_route_action": "route_to_redesign_avoid_context_source_capture_or_merge",
        "current_claim_only_rejection_scope": row.get("current_claim_only_rejection_scope"),
        "missed_opportunity_preserved": True,
        **_scope(row),
    }


def market_transfer_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("decision") or "")
    computed_rows = int(row.get("computed_action_rows") or 0)
    if decision == "source-repair":
        status = "MARKET_SCOPE_SOURCE_REPAIR_OR_PROXY_REQUIRED"
        action = "execute_source_repair_or_proxy_for_market_scope"
    elif decision == "shadow-candidate":
        status = "MARKET_SCOPE_SHADOW_CANDIDATE_DEFAULT_OFF"
        action = "keep_shadow_candidate_default_off_with_guard"
    elif decision == "proxy/control feature":
        status = "MARKET_SCOPE_PROXY_CONTROL_FEATURE"
        action = "merge_as_control_feature_or_guarded_context"
    elif decision == "merge-as-system-input":
        status = "MARKET_SCOPE_MERGE_AS_SYSTEM_INPUT"
        action = "merge_as_system_context_input"
    elif decision == "reject-current-claim-with-opportunity-preserved":
        status = "MARKET_SCOPE_REJECT_CURRENT_CLAIM_ONLY"
        action = "preserve_opportunity_path_for_redesign_or_context"
    else:
        status = "MARKET_SCOPE_REPLAY_ONLY"
        action = "keep_replay_only_or_variant_comparator_scope"
    if computed_rows == 0:
        status = status + "_NO_CURRENT_COMPUTED_ACTION_ROWS"
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "market_transfer_decision_row_id": f"OHLC-GTOS-UNIFIED-MARKET-TRANSFER-{index:05d}",
        "input_market_timeframe_session_horizon_expansion_row_id": row.get(
            "market_timeframe_session_horizon_expansion_row_id"
        ),
        "market_transfer_status": status,
        "market_transfer_action": action,
        "symbol": row.get("symbol"),
        "broker_proxy_mapping": row.get("broker_proxy_mapping"),
        "tradability_status": row.get("tradability_status"),
        "data_source": row.get("data_source", []),
        "available_timeframes": row.get("available_timeframes", []),
        "session_kz_offkz_coverage": row.get("session_kz_offkz_coverage", []),
        "spread_cost_source": row.get("spread_cost_source"),
        "decision": row.get("decision"),
        "coverage_source": row.get("coverage_source"),
        "computed_action_rows": computed_rows,
        "computed_delta_rows": row.get("computed_delta_rows"),
        "computed_action_family_counts": row.get("computed_action_family_counts", {}),
        "computed_proxy_delta_class_counts": row.get("computed_proxy_delta_class_counts", {}),
        "replay_result_row_counts": row.get("replay_result_row_counts", {}),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "missing_evidence": row.get("missing_evidence", []),
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def implementation_execution_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(str(row.get("execution_action_class") or row.get("market_transfer_status")) for row in rows)
    decision_counts = Counter(str(row.get("execution_decision_class") or row.get("decision")) for row in rows)
    return {
        "unified_system_implementation_execution_surface": UNIFIED_SYSTEM_IMPLEMENTATION_EXECUTION_SURFACE,
        "implementation_execution_rollup_row_id": f"OHLC-GTOS-UNIFIED-IMPLEMENTATION-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "decision_counts": {key: int(decision_counts[key]) for key in sorted(decision_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
