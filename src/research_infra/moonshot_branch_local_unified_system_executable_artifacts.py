"""Materialize implementation-execution rows into executable branch-local artifacts."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_executable_artifacts.py"
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


def _artifact_family(row: dict[str, Any]) -> str:
    family = str(row.get("computed_action_family") or "")
    return {
        "DEFAULT_OFF_CODE_CANDIDATE": "CODE_SURFACE_ARTIFACT",
        "SOURCE_CONTROL_REPAIR": "SOURCE_CONTROL_BUILDER_ARTIFACT",
        "SCORE_WITH_CONTROL": "SCORE_CONTROL_COMPARISON_ARTIFACT",
        "NOFILL_REDESIGN_SCORING": "NOFILL_COMPARATOR_ARTIFACT",
        "GUARD_REGISTRY_SPEC": "GUARD_BINDING_ARTIFACT",
        "CURRENT_CLAIM_OPPORTUNITY_AUDIT": "CURRENT_CLAIM_OPPORTUNITY_ARTIFACT",
    }.get(family, "RECHECK_ARTIFACT")


def executable_artifact_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    artifact_family = _artifact_family(row)
    decision_class = str(row.get("execution_decision_class") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if artifact_family == "CODE_SURFACE_ARTIFACT" and delta is not None and delta >= 0.05:
        artifact_status = "EXECUTABLE_CODE_SURFACE_READY_DEFAULT_OFF"
    elif artifact_family == "NOFILL_COMPARATOR_ARTIFACT" and decision_class == "NOFILL_VARIANT_POSITIVE_PROXY":
        artifact_status = "EXECUTABLE_NOFILL_POSITIVE_COMPARATOR_READY"
    elif artifact_family == "NOFILL_COMPARATOR_ARTIFACT" and decision_class == "NOFILL_VARIANT_NEGATIVE_PROXY":
        artifact_status = "EXECUTABLE_NOFILL_AVOID_INVERSE_ROUTE_READY"
    elif artifact_family == "SOURCE_CONTROL_BUILDER_ARTIFACT":
        artifact_status = "EXECUTABLE_SOURCE_CONTROL_BUILDER_READY"
    elif artifact_family == "GUARD_BINDING_ARTIFACT":
        artifact_status = "EXECUTABLE_GUARD_BINDING_READY"
    elif artifact_family == "CURRENT_CLAIM_OPPORTUNITY_ARTIFACT":
        artifact_status = "EXECUTABLE_OPPORTUNITY_ROUTE_READY"
    elif artifact_family == "RECHECK_ARTIFACT":
        artifact_status = "EXECUTABLE_RECHECK_ROUTE_READY"
    else:
        artifact_status = "EXECUTABLE_ARTIFACT_REQUIRES_CONTROL_REDESIGN_OR_STRESS"
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "executable_artifact_decision_row_id": f"OHLC-GTOS-UNIFIED-EXECUTABLE-ARTIFACT-{index:06d}",
        "input_implementation_execution_decision_row_id": row.get("implementation_execution_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "computed_action_family": row.get("computed_action_family"),
        "execution_action_class": row.get("execution_action_class"),
        "execution_decision_class": row.get("execution_decision_class"),
        "execution_priority_tier": row.get("execution_priority_tier"),
        "executable_artifact_family": artifact_family,
        "executable_artifact_status": artifact_status,
        "artifact_registry_key": stable_key(row.get("mechanical_scope_key"), artifact_family, row.get("source_row_id")),
        "implementation_row_consumed_in_executable_artifact": True,
        "missed_opportunity_preserved": row.get("missed_opportunity_preserved") is not False,
        **_scope(row),
    }


def code_surface_artifact(row: dict[str, Any], index: int) -> dict[str, Any]:
    delta = to_float(row.get("computed_proxy_delta"))
    module_family = str(row.get("module_family") or "branch_local_default_off_module")
    if delta is not None and delta >= 0.15:
        status = "CODE_SURFACE_STRONG_POSITIVE_DEFAULT_OFF_READY"
    elif delta is not None and delta >= 0.05:
        status = "CODE_SURFACE_POSITIVE_DEFAULT_OFF_READY"
    else:
        status = "CODE_SURFACE_CONTROL_OR_REDESIGN_REQUIRED"
    registry_key = stable_key(row.get("mechanical_scope_key"), module_family, row.get("source_row_id"))
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "code_surface_artifact_row_id": f"OHLC-GTOS-UNIFIED-CODE-SURFACE-{index:05d}",
        "input_default_off_module_spec_row_id": row.get("default_off_module_spec_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "code_surface_status": status,
        "module_family": module_family,
        "candidate_function_name": row.get("candidate_function_name"),
        "branch_local_registry_key": registry_key,
        "proposed_module_path": "src/research_infra/moonshot_branch_local_unified_system_executable_artifacts.py",
        "event_match_contract": "match symbol/session/horizon/primitive/mechanical_scope_key before emitting observation",
        "score_contract": "emit default-off research observation only after source and control guards pass",
        "guard_requirements": row.get("guard_requirements", []),
        "required_runtime_fields": row.get("required_runtime_fields", []),
        "exact_executable_spec": (
            "default_off_module(event)->observation when event scope matches and guard lookup is satisfied; "
            "otherwise no-op with source/control repair reason"
        ),
        **_scope(row),
    }


def source_control_builder_execution(row: dict[str, Any], index: int) -> dict[str, Any]:
    action = str(row.get("source_builder_action_class") or "")
    needed = to_int(row.get("source_rows_needed_to_n20_proxy"))
    if action == "BUILD_EXACT_CONTROL_DENOMINATOR" and needed <= 0:
        status = "EXACT_CONTROL_DENOMINATOR_BUILDER_EXECUTABLE_FROM_CURRENT_SCOPE"
        same_resource = True
        missing_source_proof: list[str] = []
    elif action == "BUILD_EXACT_CONTROL_DENOMINATOR":
        status = "EXACT_CONTROL_DENOMINATOR_BUILDER_NEEDS_SOURCE_ROWS"
        same_resource = False
        missing_source_proof = [f"source_rows_needed_to_n20_proxy={needed}"]
    elif action == "ATTACH_SATISFIED_SOURCE_TO_REPLAY":
        status = "SATISFIED_SOURCE_REPLAY_ATTACHMENT_BUILDER_EXECUTABLE"
        same_resource = True
        missing_source_proof = []
    else:
        status = "SOURCE_OR_PROXY_REPAIR_BUILDER_SPEC_MATERIALIZED"
        same_resource = False
        missing_source_proof = [
            "exact_source_or_control_not_satisfied_in_current_row",
            str(row.get("exact_R_availability") or "exact_R_availability_unknown"),
        ]
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "source_control_builder_execution_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-CONTROL-EXEC-{index:05d}",
        "input_source_builder_spec_row_id": row.get("source_builder_spec_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "source_control_builder_execution_status": status,
        "source_builder_action_class": action,
        "same_resource_execution_available": same_resource,
        "source_rows_needed_to_n20_proxy": needed,
        "missing_source_proof": missing_source_proof,
        "builder_output_contract": row.get("builder_output_contract"),
        "executable_builder_spec": "build denominator/source attachment/proxy row, then rescore same mechanical scope",
        **_scope(row),
    }


def score_control_comparison_artifact(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("score_control_status") or "")
    delta = to_float(row.get("computed_proxy_delta"))
    if status == "SCORE_CONTROL_POSITIVE":
        comparison_status = "SCORE_CONTROL_POSITIVE_COMPARISON_READY"
        role = "candidate_score_with_control"
    elif status == "SCORE_CONTROL_REPAIR_REQUIRED":
        comparison_status = "SCORE_CONTROL_SOURCE_OR_DENOMINATOR_REPAIR_REQUIRED"
        role = "source_control_builder_input"
    else:
        comparison_status = "SCORE_CONTROL_WEAK_NEGATIVE_CONTEXT_OR_REDESIGN"
        role = "context_feature_or_redesign_input"
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "score_control_comparison_artifact_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-COMP-{index:05d}",
        "input_score_control_execution_row_id": row.get("score_control_execution_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "score_control_comparison_status": comparison_status,
        "score_control_system_role": role,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "control_denominator_required": row.get("control_denominator_required") or delta is None,
        "comparator_contract": "compare signed proxy delta only against same-scope control with denominator guard",
        **_scope(row),
    }


def nofill_comparator_outcome(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("variant_comparator_status") or "")
    if status == "NOFILL_VARIANT_POSITIVE_PROXY":
        outcome_status = "NOFILL_POSITIVE_VARIANT_KEEP_FOR_STATUS_QUO_COMPARATOR"
        role = "positive_challenger_or_market_entry_variant"
    elif status == "NOFILL_VARIANT_NEGATIVE_PROXY":
        outcome_status = "NOFILL_NEGATIVE_VARIANT_FORCE_AVOID_INVERSE_OR_ENTRY_FAILURE_ROLE"
        role = "avoid_inverse_filter_or_failure_feature"
    elif status == "NOFILL_VARIANT_WEAK_PROXY":
        outcome_status = "NOFILL_WEAK_VARIANT_STRESS_CONTROL_REQUIRED"
        role = "stress_test_cost_source_target_stop_controls"
    else:
        outcome_status = "NOFILL_VARIANT_REPLAY_OR_SOURCE_REPAIR_REQUIRED"
        role = "source_repair_or_target_stop_replay_input"
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "nofill_comparator_outcome_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-OUTCOME-{index:05d}",
        "input_nofill_variant_comparator_row_id": row.get("nofill_variant_comparator_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "nofill_comparator_outcome_status": outcome_status,
        "nofill_system_role": role,
        "variant_action_class": row.get("variant_action_class"),
        "variant_next_action": row.get("variant_next_action"),
        "target_stop_proxy_basis": row.get("target_stop_proxy_basis"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "status_quo_control_required": True,
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        **_scope(row),
    }


def guard_binding_execution(row: dict[str, Any], index: int) -> dict[str, Any]:
    guard_family = str(row.get("guard_family") or "")
    if guard_family == "nofill_source_confidence_guard":
        fail_closed = "fail_closed_when_no_fill_source_confidence_or_cost_source_missing"
    else:
        fail_closed = "fail_closed_when_denominator_or_source_guard_missing"
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "guard_binding_execution_row_id": f"OHLC-GTOS-UNIFIED-GUARD-EXEC-{index:05d}",
        "input_guard_binding_spec_row_id": row.get("guard_binding_spec_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "guard_binding_execution_status": "GUARD_BINDING_ATTACHED_TO_DEFAULT_OFF_ARTIFACT",
        "guard_family": guard_family,
        "guard_fail_closed_condition": fail_closed,
        "guard_policy": row.get("guard_policy"),
        "attached_to_family": row.get("attached_to_family"),
        "guard_strength_proxy": row.get("guard_strength_proxy"),
        **_scope(row),
    }


def current_claim_opportunity_route(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "current_claim_opportunity_route_row_id": f"OHLC-GTOS-UNIFIED-OPPORTUNITY-ROUTE-{index:05d}",
        "input_current_claim_audit_route_row_id": row.get("current_claim_audit_route_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "opportunity_route_status": "CURRENT_CLAIM_REJECTED_OPPORTUNITY_ROUTE_EXECUTABLE",
        "current_claim_only_rejection_scope": row.get("current_claim_only_rejection_scope"),
        "preserved_opportunity_roles": [
            "avoid_inverse_filter",
            "context_feature",
            "redesign_input",
            "source_capture_requirement",
            "merge_as_system_component",
        ],
        "missed_opportunity_preserved": True,
        **_scope(row),
    }


def recheck_execution_artifact(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "recheck_execution_artifact_row_id": f"OHLC-GTOS-UNIFIED-RECHECK-EXEC-{index:05d}",
        "input_implementation_execution_decision_row_id": row.get("implementation_execution_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "recheck_execution_status": "RECHECK_SOURCE_HORIZON_TARGETABILITY_ROUTE_MATERIALIZED",
        "recheck_action": row.get("execution_next_action"),
        "missing_source_proof": ["computed_action_family_not_routed_by_current_known_split"],
        **_scope(row),
    }


def market_source_action(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_transfer_status") or "")
    if "SOURCE_REPAIR" in status:
        action_status = "MARKET_SOURCE_REPAIR_OR_PROXY_ACTION_MATERIALIZED"
        role = "source_acquisition_or_proxy_control"
    elif "SHADOW_CANDIDATE" in status:
        action_status = "MARKET_SHADOW_CANDIDATE_DEFAULT_OFF_ACTION_MATERIALIZED"
        role = "shadow_candidate_default_off"
    elif "PROXY_CONTROL_FEATURE" in status:
        action_status = "MARKET_PROXY_CONTROL_FEATURE_ACTION_MATERIALIZED"
        role = "proxy_control_feature"
    elif "MERGE_AS_SYSTEM_INPUT" in status:
        action_status = "MARKET_SYSTEM_INPUT_MERGE_ACTION_MATERIALIZED"
        role = "system_context_input"
    elif "REJECT_CURRENT_CLAIM" in status:
        action_status = "MARKET_CURRENT_CLAIM_REJECTION_OPPORTUNITY_PRESERVED"
        role = "reject_claim_preserve_market_opportunity"
    else:
        action_status = "MARKET_REPLAY_ONLY_ACTION_MATERIALIZED"
        role = "replay_only_or_comparator_scope"
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "market_source_action_row_id": f"OHLC-GTOS-UNIFIED-MARKET-SOURCE-ACTION-{index:05d}",
        "input_market_transfer_decision_row_id": row.get("market_transfer_decision_row_id"),
        "input_market_timeframe_session_horizon_expansion_row_id": row.get(
            "input_market_timeframe_session_horizon_expansion_row_id"
        ),
        "market_source_action_status": action_status,
        "market_system_role": role,
        "market_transfer_status": row.get("market_transfer_status"),
        "market_transfer_action": row.get("market_transfer_action"),
        "symbol": row.get("symbol"),
        "broker_proxy_mapping": row.get("broker_proxy_mapping"),
        "tradability_status": row.get("tradability_status"),
        "data_source": row.get("data_source", []),
        "available_timeframes": row.get("available_timeframes", []),
        "session_kz_offkz_coverage": row.get("session_kz_offkz_coverage", []),
        "spread_cost_source": row.get("spread_cost_source"),
        "decision": row.get("decision"),
        "coverage_source": row.get("coverage_source"),
        "computed_action_rows": row.get("computed_action_rows"),
        "computed_delta_rows": row.get("computed_delta_rows"),
        "replay_result_row_counts": row.get("replay_result_row_counts", {}),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "missing_evidence": row.get("missing_evidence", []),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def executable_artifact_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("executable_artifact_status")
            or row.get("code_surface_status")
            or row.get("source_control_builder_execution_status")
            or row.get("nofill_comparator_outcome_status")
            or row.get("guard_binding_execution_status")
            or row.get("score_control_comparison_status")
            or row.get("opportunity_route_status")
            or row.get("market_source_action_status")
            or row.get("recheck_execution_status")
        )
        for row in rows
    )
    return {
        "unified_system_executable_artifact_surface": UNIFIED_SYSTEM_EXECUTABLE_ARTIFACT_SURFACE,
        "executable_artifact_rollup_row_id": f"OHLC-GTOS-UNIFIED-EXECUTABLE-ROLLUP-{index:05d}",
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
