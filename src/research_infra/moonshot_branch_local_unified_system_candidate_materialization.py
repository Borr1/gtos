"""Materialize candidate dispatch rows into executable branch-local action surfaces."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_materialization.py"
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


def candidate_materialization_family(dispatch_family: str) -> tuple[str, str, str]:
    if dispatch_family == "SCORER_REGISTRY_MATERIALIZATION_DISPATCH":
        return (
            "SCORER_CODE_SURFACE_MATERIALIZATION",
            "MATERIALIZE_SCORER_CODE_SURFACE_READY_DEFAULT_OFF",
            "write_branch_local_default_off_scorer_registration",
        )
    if dispatch_family == "NOFILL_CHALLENGER_MODULE_DISPATCH":
        return (
            "NOFILL_CHALLENGER_COMPARATOR_MATERIALIZATION",
            "MATERIALIZE_NOFILL_CHALLENGER_COMPARATOR_READY",
            "write_status_quo_vs_nofill_challenger_comparator",
        )
    if dispatch_family == "AVOID_INVERSE_FILTER_MODULE_DISPATCH":
        return (
            "AVOID_INVERSE_FILTER_MATERIALIZATION",
            "MATERIALIZE_AVOID_INVERSE_FILTER_READY",
            "write_avoid_inverse_or_entry_failure_filter",
        )
    if dispatch_family == "SOURCE_GUARD_OPPORTUNITY_ACTION_DISPATCH":
        return (
            "NON_SCALAR_SOURCE_GUARD_ACTION_MATERIALIZATION",
            "MATERIALIZE_NON_SCALAR_SOURCE_GUARD_ACTION_READY",
            "write_source_guard_opportunity_or_claim_audit_action",
        )
    return (
        "REPAIR_STRESS_CONTEXT_MATERIALIZATION",
        "MATERIALIZE_REPAIR_STRESS_CONTEXT_REQUIRED",
        "write_repair_stress_context_action_before_score_use",
    )


def candidate_materialization_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    family, status, action = candidate_materialization_family(str(row.get("candidate_dispatch_family") or ""))
    score = to_float(row.get("default_off_observation_score"))
    if score is None:
        score = to_float(row.get("computed_proxy_delta"))
    if family == "AVOID_INVERSE_FILTER_MATERIALIZATION" and score is not None:
        score = abs(score)
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "candidate_materialization_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MATERIALIZATION-{index:06d}",
        "input_candidate_dispatch_decision_row_id": row.get("candidate_dispatch_decision_row_id"),
        "input_candidate_runtime_decision_row_id": row.get("input_candidate_runtime_decision_row_id"),
        "input_candidate_execution_row_id": row.get("input_candidate_execution_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "candidate_dispatch_family": row.get("candidate_dispatch_family"),
        "candidate_dispatch_status": row.get("candidate_dispatch_status"),
        "candidate_dispatch_action_class": row.get("candidate_dispatch_action_class"),
        "candidate_materialization_family": family,
        "candidate_materialization_status": status,
        "candidate_materialization_action": action,
        "candidate_materialization_key": stable_key(row.get("candidate_dispatch_key"), family, row.get("source_row_id")),
        "default_off_observation_score": score,
        "materialization_output_contract": "branch_local_code_surface_builder_guard_or_market_action_row",
        "dispatch_row_consumed_in_materialization": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def scorer_code_surface_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("component_dispatch_plan_status") or "")
    ready = status == "COMPONENT_DISPATCH_PLAN_READY"
    registry_key = stable_key(row.get("mechanical_scope_key"), row.get("candidate_component_role"), row.get("source_row_id"))
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "scorer_code_surface_materialization_row_id": f"OHLC-GTOS-UNIFIED-SCORER-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "scorer_materialization_status": (
            "SCORER_CODE_SURFACE_READY_DEFAULT_OFF_WITH_GUARD"
            if ready
            else "SCORER_CODE_SURFACE_HELD_FOR_CONTROL_OR_REDESIGN"
        ),
        "branch_local_registry_key": registry_key,
        "candidate_callable_name": f"score_candidate_dispatch_default_off_{index:05d}",
        "required_guards": ["source_confidence_guard", "same_scope_control_lookup", "default_off_disabled_until_enabled"],
        "materialized_spec": "if event scope matches and guards pass, emit default-off research observation; else no-op with reason",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def source_control_builder_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("component_dispatch_plan_status") or "")
    action = str(row.get("component_dispatch_action") or "")
    if status == "COMPONENT_DISPATCH_PLAN_READY":
        materialized_status = "SOURCE_CONTROL_BUILDER_EXECUTABLE"
        same_resource = True
        missing_source_proof: list[str] = []
    elif status == "COMPONENT_DISPATCH_REPAIR_OR_CONTROL_REQUIRED":
        materialized_status = "SOURCE_CONTROL_BUILDER_REPAIR_OR_PROXY_REQUIRED"
        same_resource = False
        missing_source_proof = ["component_runtime_binding_requires_repair_or_control"]
    else:
        materialized_status = "SOURCE_CONTROL_BUILDER_CONTEXT_ONLY"
        same_resource = False
        missing_source_proof = ["component_runtime_binding_context_only"]
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "source_control_builder_materialization_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-CONTROL-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "source_control_materialization_status": materialized_status,
        "source_control_materialization_action": action,
        "same_resource_execution_available": same_resource,
        "missing_source_proof": missing_source_proof,
        "builder_spec": "build exact/source/proxy/control observation for same mechanical scope and rejoin to candidate score",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def score_control_comparator_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    delta = to_float(row.get("computed_proxy_delta"))
    if row.get("component_dispatch_plan_status") == "COMPONENT_DISPATCH_PLAN_READY" and delta is not None and delta >= 0.05:
        status = "SCORE_CONTROL_COMPARATOR_POSITIVE_READY"
        role = "score_with_control_candidate"
    elif row.get("component_dispatch_plan_status") == "COMPONENT_DISPATCH_REPAIR_OR_CONTROL_REQUIRED":
        status = "SCORE_CONTROL_COMPARATOR_REPAIR_REQUIRED"
        role = "source_control_repair_input"
    else:
        status = "SCORE_CONTROL_COMPARATOR_CONTEXT_OR_REDESIGN"
        role = "context_or_redesign_input"
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "score_control_comparator_materialization_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "score_control_materialization_status": status,
        "score_control_system_role": role,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": status != "SCORE_CONTROL_COMPARATOR_POSITIVE_READY",
        "comparator_spec": "compare candidate proxy only against same-scope pass/control denominator with guard",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def nofill_comparator_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    role = str(row.get("candidate_component_role") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if "positive_challenger" in role or (delta is not None and delta >= 0.05):
        status = "NOFILL_MATERIALIZE_POSITIVE_CHALLENGER_COMPARATOR"
        action = "run_status_quo_vs_nofill_challenger_comparator"
        system_role = "positive_nofill_challenger"
    elif "avoid_inverse" in role or (delta is not None and delta <= -0.15):
        status = "NOFILL_MATERIALIZE_AVOID_INVERSE_FILTER"
        action = "run_avoid_inverse_or_entry_failure_filter"
        system_role = "avoid_inverse_or_failure_feature"
    elif row.get("component_dispatch_plan_status") == "COMPONENT_DISPATCH_REPAIR_OR_CONTROL_REQUIRED":
        status = "NOFILL_MATERIALIZE_SOURCE_REPAIR_REQUIRED"
        action = "repair_targetstop_source_or_no_fill_denominator"
        system_role = "source_repair_or_targetstop_replay_input"
    else:
        status = "NOFILL_MATERIALIZE_STRESS_CONTROL"
        action = "stress_cost_source_target_stop_and_status_quo_control"
        system_role = "stress_control_or_context"
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "nofill_comparator_materialization_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "nofill_materialization_status": status,
        "nofill_materialization_action": action,
        "nofill_system_role": system_role,
        "target_stop_proxy_basis": row.get("target_stop_proxy_basis"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "status_quo_control_required": True,
        "opportunity_preserved_as": "positive_challenger_avoid_inverse_retest_source_or_entry_redesign_intelligence",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def guard_enforcement_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "guard_enforcement_materialization_row_id": f"OHLC-GTOS-UNIFIED-GUARD-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "guard_enforcement_status": "GUARD_ENFORCEMENT_REGISTERED_FAIL_CLOSED",
        "guard_enforcement_action": "block_candidate_score_or_variant_until_source_control_guard_satisfied",
        "guard_family": row.get("guard_family") or "source_control_or_denominator_guard",
        "fail_closed_condition": "missing_source_confidence_control_denominator_or_market_transfer_evidence",
        "guard_spec": "fail closed for score use while preserving row as source/control repair input",
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def opportunity_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "opportunity_materialization_row_id": f"OHLC-GTOS-UNIFIED-OPPORTUNITY-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "opportunity_materialization_status": "CURRENT_CLAIM_OPPORTUNITY_PRESERVED_IN_SYSTEM_INPUTS",
        "opportunity_materialization_action": "route_claim_failure_to_avoid_inverse_context_redesign_source_capture_or_merge",
        "missed_opportunity_preserved": True,
        "preserved_roles": ["avoid_inverse_filter", "context_feature", "redesign_input", "source_capture_requirement", "system_component"],
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def recheck_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "recheck_materialization_row_id": f"OHLC-GTOS-UNIFIED-RECHECK-MATERIALIZATION-{index:05d}",
        "input_component_dispatch_plan_row_id": row.get("component_dispatch_plan_row_id"),
        "input_component_runtime_binding_row_id": row.get("input_component_runtime_binding_row_id"),
        "recheck_materialization_status": "RECHECK_SOURCE_HORIZON_TARGETABILITY_MATERIALIZED",
        "recheck_materialization_action": "recheck_source_horizon_targetability_then_route_to_builder_or_kill_current_claim_only",
        "missing_source_proof": row.get("missing_source_proof", []),
        "upstream_source_manifest_hash": row.get("source_manifest_hash"),
        **_scope(row),
    }


def market_action_materialization(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_transfer_dispatch_status") or "")
    if "SOURCE_REPAIR_OR_PROXY" in status:
        action_status = "MARKET_ACTION_SOURCE_REPAIR_OR_PROXY_MATERIALIZED"
        role = "source_acquisition_or_proxy_control"
    elif "SHADOW_DEFAULT_OFF" in status:
        action_status = "MARKET_ACTION_SHADOW_DEFAULT_OFF_CANDIDATE_MATERIALIZED"
        role = "shadow_candidate_default_off"
    elif "PROXY_CONTROL" in status:
        action_status = "MARKET_ACTION_PROXY_CONTROL_FEATURE_MATERIALIZED"
        role = "proxy_control_feature"
    elif "SYSTEM_INPUT" in status:
        action_status = "MARKET_ACTION_SYSTEM_INPUT_MERGE_MATERIALIZED"
        role = "system_context_input"
    elif "REJECT_CLAIM" in status:
        action_status = "MARKET_ACTION_CURRENT_CLAIM_REJECTION_OPPORTUNITY_PRESERVED"
        role = "reject_current_claim_preserve_market_opportunity"
    else:
        action_status = "MARKET_ACTION_REPLAY_ONLY_MATERIALIZED"
        role = "replay_only_or_comparator_scope"
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "market_action_materialization_row_id": f"OHLC-GTOS-UNIFIED-MARKET-MATERIALIZATION-{index:05d}",
        "input_market_transfer_dispatch_row_id": row.get("market_transfer_dispatch_row_id"),
        "input_market_runtime_binding_row_id": row.get("input_market_runtime_binding_row_id"),
        "market_action_materialization_status": action_status,
        "market_action_materialization_role": role,
        "market_action_materialization_action": row.get("market_transfer_dispatch_action"),
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


def candidate_materialization_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("candidate_materialization_status")
            or row.get("scorer_materialization_status")
            or row.get("source_control_materialization_status")
            or row.get("score_control_materialization_status")
            or row.get("nofill_materialization_status")
            or row.get("guard_enforcement_status")
            or row.get("opportunity_materialization_status")
            or row.get("recheck_materialization_status")
            or row.get("market_action_materialization_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_materialization": UNIFIED_SYSTEM_CANDIDATE_MATERIALIZATION,
        "candidate_materialization_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MATERIALIZATION-ROLLUP-{index:05d}",
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
