"""Dispatch executable candidate runtime bindings into branch-local work surfaces."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_DISPATCH = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_dispatch.py"
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


def stable_key(*parts: Any) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _scope(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
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


def candidate_dispatch_family(runtime_family: str) -> tuple[str, str, str, str]:
    if runtime_family == "DEFAULT_OFF_SCORER_RUNTIME_COMPONENT":
        return (
            "SCORER_REGISTRY_MATERIALIZATION_DISPATCH",
            "CANDIDATE_DISPATCH_SCORER_REGISTRY_READY_DEFAULT_OFF",
            "materialize_default_off_scorer_registry",
            "DISPATCH_DEFAULT_OFF_SCORER_REGISTRATION",
        )
    if runtime_family == "NOFILL_CHALLENGER_RUNTIME_COMPONENT":
        return (
            "NOFILL_CHALLENGER_MODULE_DISPATCH",
            "CANDIDATE_DISPATCH_NOFILL_CHALLENGER_READY_DEFAULT_OFF",
            "materialize_nofill_challenger_comparator",
            "DISPATCH_NOFILL_CHALLENGER_MODULE",
        )
    if runtime_family == "AVOID_INVERSE_RUNTIME_COMPONENT":
        return (
            "AVOID_INVERSE_FILTER_MODULE_DISPATCH",
            "CANDIDATE_DISPATCH_AVOID_INVERSE_READY_DEFAULT_OFF",
            "materialize_avoid_inverse_filter_module",
            "DISPATCH_AVOID_INVERSE_FILTER_MODULE",
        )
    if runtime_family == "NON_SCALAR_ACTION_RUNTIME_COMPONENT":
        return (
            "SOURCE_GUARD_OPPORTUNITY_ACTION_DISPATCH",
            "CANDIDATE_DISPATCH_NON_SCALAR_ACTION_READY",
            "materialize_source_guard_opportunity_action",
            "DISPATCH_NON_SCALAR_SOURCE_GUARD_OPPORTUNITY_ACTION",
        )
    return (
        "REPAIR_STRESS_CONTEXT_ACTION_DISPATCH",
        "CANDIDATE_DISPATCH_REPAIR_STRESS_CONTEXT_REQUIRED",
        "materialize_repair_stress_context_action",
        "DISPATCH_REPAIR_STRESS_CONTEXT_ACTION",
    )


def candidate_dispatch_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    runtime_family = str(row.get("candidate_runtime_component_family") or "")
    dispatch_family, dispatch_status, callable_base, dispatch_class = candidate_dispatch_family(runtime_family)
    callable_name = f"{callable_base}_{index:06d}"
    return {
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "candidate_dispatch_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-{index:06d}",
        "input_candidate_runtime_decision_row_id": row.get("candidate_runtime_decision_row_id"),
        "input_candidate_execution_row_id": row.get("input_candidate_execution_row_id"),
        "input_runtime_surface_decision_row_id": row.get("input_runtime_surface_decision_row_id"),
        "input_executable_artifact_decision_row_id": row.get("input_executable_artifact_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "candidate_runtime_component_family": runtime_family,
        "candidate_runtime_status": row.get("candidate_runtime_status"),
        "candidate_runtime_emission_class": row.get("candidate_runtime_emission_class"),
        "candidate_dispatch_family": dispatch_family,
        "candidate_dispatch_status": dispatch_status,
        "candidate_dispatch_action_class": dispatch_class,
        "candidate_dispatch_callable_name": callable_name,
        "candidate_dispatch_key": stable_key(row.get("candidate_runtime_key"), dispatch_family, row.get("source_row_id")),
        "dispatch_contract": (
            "scope_match_then_materialize_branch_local_scorer_source_control_nofill_guard_or_market_action"
        ),
        "default_off_observation_score": row.get("default_off_observation_score"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        "runtime_binding_consumed_in_dispatch": True,
        **_scope(row),
    }


def event_matches_candidate_dispatch(dispatch_row: dict[str, Any], event: dict[str, Any]) -> bool:
    for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "mechanical_scope_key"):
        expected = dispatch_row.get(field)
        if expected not in (None, "", "ALL", "ALL_SESSIONS", "ALL_HORIZONS", "ALL_PRIMITIVES"):
            if event.get(field) != expected:
                return False
    return True


def execute_candidate_dispatch(dispatch_row: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_candidate_dispatch(dispatch_row, event)
    family = str(dispatch_row.get("candidate_dispatch_family") or "")
    if not matched:
        action = "NO_DISPATCH_SCOPE_MISMATCH"
        dispatch_class = "NO_DISPATCH_SCOPE_MISMATCH"
        score = None
        next_action = "no_action_scope_mismatch"
    elif family == "SCORER_REGISTRY_MATERIALIZATION_DISPATCH":
        action = "MATERIALIZE_DEFAULT_OFF_SCORER_REGISTRY"
        dispatch_class = "DISPATCH_DEFAULT_OFF_SCORER_REGISTRATION"
        score = to_float(dispatch_row.get("default_off_observation_score"))
        if score is None:
            score = to_float(dispatch_row.get("computed_proxy_delta"))
        next_action = "register_branch_local_default_off_scorer_with_source_and_control_guards"
    elif family == "NOFILL_CHALLENGER_MODULE_DISPATCH":
        action = "MATERIALIZE_NOFILL_CHALLENGER_COMPARATOR"
        dispatch_class = "DISPATCH_NOFILL_CHALLENGER_MODULE"
        score = to_float(dispatch_row.get("default_off_observation_score"))
        if score is None:
            score = to_float(dispatch_row.get("computed_proxy_delta"))
        next_action = "instantiate_status_quo_control_and_nofill_challenger_comparator"
    elif family == "AVOID_INVERSE_FILTER_MODULE_DISPATCH":
        action = "MATERIALIZE_AVOID_INVERSE_FILTER_MODULE"
        dispatch_class = "DISPATCH_AVOID_INVERSE_FILTER_MODULE"
        score = to_float(dispatch_row.get("default_off_observation_score"))
        if score is None:
            score = to_float(dispatch_row.get("computed_proxy_delta"))
        if score is not None:
            score = abs(score)
        next_action = "instantiate_avoid_inverse_or_entry_failure_filter_module"
    elif family == "SOURCE_GUARD_OPPORTUNITY_ACTION_DISPATCH":
        action = "MATERIALIZE_NON_SCALAR_SOURCE_GUARD_OPPORTUNITY_ACTION"
        dispatch_class = "DISPATCH_NON_SCALAR_SOURCE_GUARD_OPPORTUNITY_ACTION"
        score = None
        next_action = "run_source_guard_opportunity_or_current_claim_preservation_action"
    else:
        action = "MATERIALIZE_REPAIR_STRESS_CONTEXT_ACTION"
        dispatch_class = "DISPATCH_REPAIR_STRESS_CONTEXT_ACTION"
        score = None
        next_action = "run_repair_stress_control_or_context_action_before_score_use"
    return {
        "event_matched_candidate_dispatch": matched,
        "candidate_dispatch_execution_class": dispatch_class,
        "candidate_dispatch_execution_action": action,
        "candidate_dispatch_next_action": next_action,
        "default_off_observation_score": score,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def candidate_dispatch_self_test(row: dict[str, Any], index: int) -> dict[str, Any]:
    match_event = {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
    }
    mismatch_event = {**match_event, "mechanical_scope_key": "__mismatch__"}
    positive = execute_candidate_dispatch(row, match_event)
    negative = execute_candidate_dispatch(row, mismatch_event)
    return {
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "candidate_dispatch_self_test_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-SELFTEST-{index:06d}",
        "input_candidate_dispatch_decision_row_id": row.get("candidate_dispatch_decision_row_id"),
        "input_candidate_runtime_decision_row_id": row.get("input_candidate_runtime_decision_row_id"),
        "candidate_dispatch_key": row.get("candidate_dispatch_key"),
        "positive_scope_match_result": positive["event_matched_candidate_dispatch"],
        "negative_scope_mismatch_result": negative["event_matched_candidate_dispatch"],
        "executed_dispatch_class": positive["candidate_dispatch_execution_class"],
        "executed_dispatch_action": positive["candidate_dispatch_execution_action"],
        "default_off_observation_score": positive["default_off_observation_score"],
        "dispatch_behavior_executed": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def component_dispatch_plan(row: dict[str, Any], index: int, component_type: str) -> dict[str, Any]:
    binding_status = str(row.get("component_runtime_binding_status") or "")
    if binding_status == "COMPONENT_RUNTIME_BINDING_READY":
        plan_status = "COMPONENT_DISPATCH_PLAN_READY"
        action = {
            "SCORER": "materialize_default_off_scorer_registry",
            "SOURCE": "run_source_control_builder_or_attach_replay",
            "SCORE_CONTROL": "run_score_with_control_comparator",
            "NOFILL": "instantiate_nofill_variant_comparator_or_avoid_filter",
            "GUARD": "bind_fail_closed_guard_registry",
            "OPPORTUNITY": "preserve_current_claim_opportunity_route",
            "RECHECK": "run_source_horizon_targetability_recheck",
        }.get(component_type, "materialize_component_dispatch_plan")
    elif binding_status == "COMPONENT_RUNTIME_REPAIR_OR_CONTROL_REQUIRED":
        plan_status = "COMPONENT_DISPATCH_REPAIR_OR_CONTROL_REQUIRED"
        action = "build_source_control_repair_or_redesign_before_score_use"
    else:
        plan_status = "COMPONENT_DISPATCH_CONTEXT_READY"
        action = "preserve_non_scalar_context_feature_or_requirement"
    return {
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "component_dispatch_plan_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-{component_type}-DISPATCH-{index:05d}",
        "component_type": component_type,
        "input_component_runtime_binding_row_id": row.get("component_runtime_binding_row_id"),
        "input_component_row_id": row.get("input_component_row_id"),
        "candidate_component_status": row.get("candidate_component_status"),
        "candidate_component_role": row.get("candidate_component_role"),
        "component_runtime_binding_status": row.get("component_runtime_binding_status"),
        "component_dispatch_plan_status": plan_status,
        "component_dispatch_action": action,
        "component_execution_contract": row.get("component_execution_contract"),
        "component_dispatch_output_contract": (
            "branch_local_materialized_scorer_source_control_nofill_guard_opportunity_or_recheck_action"
        ),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def market_transfer_dispatch(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_runtime_binding_status") or "")
    if "SOURCE_REPAIR_OR_PROXY" in status:
        dispatch_status = "MARKET_DISPATCH_SOURCE_REPAIR_OR_PROXY_ACTION_READY"
        action = "execute_source_repair_or_proxy_for_market_scope"
    elif "SHADOW_DEFAULT_OFF" in status:
        dispatch_status = "MARKET_DISPATCH_SHADOW_DEFAULT_OFF_CANDIDATE_READY"
        action = "materialize_shadow_default_off_market_candidate"
    elif "PROXY_CONTROL" in status:
        dispatch_status = "MARKET_DISPATCH_PROXY_CONTROL_FEATURE_READY"
        action = "materialize_proxy_control_feature"
    elif "SYSTEM_INPUT" in status:
        dispatch_status = "MARKET_DISPATCH_SYSTEM_INPUT_MERGE_READY"
        action = "merge_market_scope_as_system_input"
    elif "REJECT_CLAIM" in status:
        dispatch_status = "MARKET_DISPATCH_REJECT_CLAIM_PRESERVE_OPPORTUNITY"
        action = "reject_current_claim_only_preserve_market_opportunity"
    else:
        dispatch_status = "MARKET_DISPATCH_REPLAY_ONLY_ACTION_READY"
        action = "preserve_replay_only_market_scope_for_comparator_or_context"
    return {
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "market_transfer_dispatch_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-DISPATCH-{index:05d}",
        "input_market_runtime_binding_row_id": row.get("market_runtime_binding_row_id"),
        "input_market_component_row_id": row.get("input_market_component_row_id"),
        "candidate_component_status": row.get("candidate_component_status"),
        "candidate_component_role": row.get("candidate_component_role"),
        "market_runtime_binding_status": row.get("market_runtime_binding_status"),
        "market_transfer_dispatch_status": dispatch_status,
        "market_transfer_dispatch_action": action,
        "symbol": row.get("symbol"),
        "broker_proxy_mapping": row.get("broker_proxy_mapping"),
        "tradability_status": row.get("tradability_status"),
        "data_source": row.get("data_source", []),
        "available_timeframes": row.get("available_timeframes", []),
        "session_kz_offkz_coverage": row.get("session_kz_offkz_coverage", []),
        "spread_cost_source": row.get("spread_cost_source"),
        "computed_action_rows": row.get("computed_action_rows"),
        "computed_delta_rows": row.get("computed_delta_rows"),
        "missing_evidence": row.get("missing_evidence", []),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def candidate_dispatch_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("candidate_dispatch_status")
            or row.get("component_dispatch_plan_status")
            or row.get("market_transfer_dispatch_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_dispatch": UNIFIED_SYSTEM_CANDIDATE_DISPATCH,
        "candidate_dispatch_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-DISPATCH-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }
