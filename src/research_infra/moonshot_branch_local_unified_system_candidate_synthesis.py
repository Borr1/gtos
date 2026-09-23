"""Synthesize runtime surfaces into branch-local candidate-system execution rows."""

from __future__ import annotations

from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_synthesis.py"
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


def candidate_role_from_emission(emission: str) -> tuple[str, str]:
    if emission == "EMIT_DEFAULT_OFF_POSITIVE_SCORER_OBSERVATION":
        return "DEFAULT_OFF_POSITIVE_SCORER_COMPONENT", "CANDIDATE_SCORER_OBSERVATION_READY"
    if emission == "EMIT_DEFAULT_OFF_NOFILL_CHALLENGER_OBSERVATION":
        return "NOFILL_POSITIVE_CHALLENGER_COMPONENT", "CANDIDATE_NOFILL_CHALLENGER_READY"
    if emission == "EMIT_AVOID_INVERSE_OR_ENTRY_FAILURE_OBSERVATION":
        return "AVOID_INVERSE_FAILURE_FILTER_COMPONENT", "CANDIDATE_AVOID_INVERSE_READY"
    if emission == "EMIT_NON_SCALAR_ACTION_OBSERVATION":
        return "NON_SCALAR_SOURCE_GUARD_OPPORTUNITY_COMPONENT", "CANDIDATE_NON_SCALAR_ACTION_READY"
    return "REPAIR_STRESS_CONTEXT_COMPONENT", "CANDIDATE_REPAIR_STRESS_CONTEXT_REQUIRED"


def candidate_execution_row(
    runtime_row: dict[str, Any],
    self_test_row: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    emission = str((self_test_row or {}).get("emitted_observation_class") or "SELF_TEST_EMISSION_MISSING")
    role, status = candidate_role_from_emission(emission)
    positive_match = (self_test_row or {}).get("positive_scope_match_result") is True
    negative_mismatch = (self_test_row or {}).get("negative_scope_mismatch_result") is False
    if not positive_match or not negative_mismatch:
        status = "CANDIDATE_SURFACE_SELF_TEST_FAILED_REPAIR_REQUIRED"
        role = "SURFACE_SELF_TEST_REPAIR_COMPONENT"
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "candidate_execution_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-EXECUTION-{index:06d}",
        "input_runtime_surface_decision_row_id": runtime_row.get("runtime_surface_decision_row_id"),
        "input_executable_artifact_decision_row_id": runtime_row.get("input_executable_artifact_decision_row_id"),
        "input_unified_system_computed_action_row_id": runtime_row.get("input_unified_system_computed_action_row_id"),
        "runtime_surface_family": runtime_row.get("runtime_surface_family"),
        "runtime_surface_status": runtime_row.get("runtime_surface_status"),
        "runtime_surface_key": runtime_row.get("runtime_surface_key"),
        "self_test_row_id": (self_test_row or {}).get("runtime_surface_self_test_row_id"),
        "self_test_emission": emission,
        "positive_scope_match_result": positive_match,
        "negative_scope_mismatch_result": negative_mismatch,
        "candidate_system_role": role,
        "candidate_execution_status": status,
        "candidate_execution_policy": "default_off_branch_local_observation_only",
        "default_off_observation_score": (self_test_row or {}).get("default_off_observation_score"),
        "candidate_surface_consumed_in_system_synthesis": True,
        **_scope(runtime_row),
    }


def scorer_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "scorer_component_row_id": f"OHLC-GTOS-UNIFIED-SCORER-COMPONENT-{index:05d}",
        "input_scorer_registry_surface_row_id": row.get("scorer_registry_surface_row_id"),
        "candidate_component_status": row.get("scorer_registry_status"),
        "candidate_component_role": "default_off_scorer_registry",
        "registered_callable_name": row.get("registered_callable_name"),
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "guard_requirements": row.get("guard_requirements", []),
        "component_execution_contract": "scope_match_then_emit_default_off_scorer_observation_with_guard_state",
        **_scope(row),
    }


def source_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "source_component_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-COMPONENT-{index:05d}",
        "input_source_replay_surface_row_id": row.get("source_replay_surface_row_id"),
        "candidate_component_status": row.get("source_replay_status"),
        "candidate_component_role": "source_or_control_replay_builder",
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "source_rows_needed_to_n20_proxy": row.get("source_rows_needed_to_n20_proxy"),
        "component_execution_contract": row.get("replay_callable_contract"),
        **_scope(row),
    }


def score_control_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "score_control_component_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-COMPONENT-{index:05d}",
        "input_score_control_runtime_surface_row_id": row.get("score_control_runtime_surface_row_id"),
        "candidate_component_status": row.get("score_control_runtime_status"),
        "candidate_component_role": row.get("score_control_system_role"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "component_execution_contract": row.get("comparator_contract"),
        **_scope(row),
    }


def nofill_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "nofill_component_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-COMPONENT-{index:05d}",
        "input_nofill_replay_surface_row_id": row.get("nofill_replay_surface_row_id"),
        "candidate_component_status": row.get("nofill_replay_status"),
        "candidate_component_role": row.get("nofill_system_role"),
        "target_stop_proxy_basis": row.get("target_stop_proxy_basis"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "component_execution_contract": row.get("replay_callable_contract"),
        **_scope(row),
    }


def guard_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "guard_component_row_id": f"OHLC-GTOS-UNIFIED-GUARD-COMPONENT-{index:05d}",
        "input_guard_runtime_surface_row_id": row.get("guard_runtime_surface_row_id"),
        "candidate_component_status": row.get("guard_runtime_status"),
        "candidate_component_role": "fail_closed_guard_binding",
        "guard_family": row.get("guard_family"),
        "guard_fail_closed_condition": row.get("guard_fail_closed_condition"),
        "guard_policy": row.get("guard_policy"),
        **_scope(row),
    }


def opportunity_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "opportunity_component_row_id": f"OHLC-GTOS-UNIFIED-OPPORTUNITY-COMPONENT-{index:05d}",
        "input_opportunity_runtime_surface_row_id": row.get("opportunity_runtime_surface_row_id"),
        "candidate_component_status": row.get("opportunity_runtime_status"),
        "candidate_component_role": "current_claim_rejection_opportunity_route",
        "preserved_opportunity_roles": row.get("preserved_opportunity_roles", []),
        "missed_opportunity_preserved": True,
        **_scope(row),
    }


def recheck_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "recheck_component_row_id": f"OHLC-GTOS-UNIFIED-RECHECK-COMPONENT-{index:05d}",
        "input_recheck_runtime_surface_row_id": row.get("recheck_runtime_surface_row_id"),
        "candidate_component_status": row.get("recheck_runtime_status"),
        "candidate_component_role": "source_horizon_targetability_recheck",
        "missing_source_proof": row.get("missing_source_proof", []),
        **_scope(row),
    }


def market_component_row(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "market_component_row_id": f"OHLC-GTOS-UNIFIED-MARKET-COMPONENT-{index:05d}",
        "input_market_source_runtime_surface_row_id": row.get("market_source_runtime_surface_row_id"),
        "candidate_component_status": row.get("market_source_runtime_status"),
        "candidate_component_role": row.get("market_system_role"),
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
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def candidate_system_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("candidate_execution_status")
            or row.get("candidate_component_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_synthesis_surface": UNIFIED_SYSTEM_CANDIDATE_SYNTHESIS_SURFACE,
        "candidate_system_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-ROLLUP-{index:05d}",
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
