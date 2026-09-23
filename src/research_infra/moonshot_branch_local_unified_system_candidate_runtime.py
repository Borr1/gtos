"""Branch-local executable candidate runtime for unified moonshot components."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_RUNTIME = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_runtime.py"
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


def candidate_runtime_family(role: str) -> tuple[str, str, str, str]:
    if role == "DEFAULT_OFF_POSITIVE_SCORER_COMPONENT":
        return (
            "DEFAULT_OFF_SCORER_RUNTIME_COMPONENT",
            "CANDIDATE_RUNTIME_SCORER_READY_DEFAULT_OFF",
            "score_default_off_candidate_observation",
            "EMIT_CANDIDATE_DEFAULT_OFF_SCORER_OBSERVATION",
        )
    if role == "NOFILL_POSITIVE_CHALLENGER_COMPONENT":
        return (
            "NOFILL_CHALLENGER_RUNTIME_COMPONENT",
            "CANDIDATE_RUNTIME_NOFILL_CHALLENGER_READY_DEFAULT_OFF",
            "score_nofill_challenger_candidate_observation",
            "EMIT_CANDIDATE_NOFILL_CHALLENGER_OBSERVATION",
        )
    if role == "AVOID_INVERSE_FAILURE_FILTER_COMPONENT":
        return (
            "AVOID_INVERSE_RUNTIME_COMPONENT",
            "CANDIDATE_RUNTIME_AVOID_INVERSE_FILTER_READY_DEFAULT_OFF",
            "score_avoid_inverse_candidate_observation",
            "EMIT_CANDIDATE_AVOID_INVERSE_FILTER_OBSERVATION",
        )
    if role == "NON_SCALAR_SOURCE_GUARD_OPPORTUNITY_COMPONENT":
        return (
            "NON_SCALAR_ACTION_RUNTIME_COMPONENT",
            "CANDIDATE_RUNTIME_NON_SCALAR_ACTION_READY",
            "emit_non_scalar_source_guard_opportunity_action",
            "EMIT_CANDIDATE_NON_SCALAR_ACTION_OBSERVATION",
        )
    return (
        "REPAIR_STRESS_RUNTIME_COMPONENT",
        "CANDIDATE_RUNTIME_REPAIR_STRESS_CONTEXT_REQUIRED",
        "emit_repair_stress_context_requirement",
        "EMIT_CANDIDATE_REPAIR_STRESS_CONTEXT_OBSERVATION",
    )


def candidate_runtime_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    role = str(row.get("candidate_system_role") or "")
    family, status, callable_base, emission = candidate_runtime_family(role)
    if row.get("candidate_execution_status") == "CANDIDATE_SURFACE_SELF_TEST_FAILED_REPAIR_REQUIRED":
        family, status, callable_base, emission = candidate_runtime_family("SURFACE_SELF_TEST_REPAIR_COMPONENT")
    callable_name = f"{callable_base}_{index:06d}"
    return {
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "candidate_runtime_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-{index:06d}",
        "input_candidate_execution_row_id": row.get("candidate_execution_row_id"),
        "input_runtime_surface_decision_row_id": row.get("input_runtime_surface_decision_row_id"),
        "input_executable_artifact_decision_row_id": row.get("input_executable_artifact_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "candidate_system_role": row.get("candidate_system_role"),
        "candidate_execution_status": row.get("candidate_execution_status"),
        "candidate_runtime_component_family": family,
        "candidate_runtime_status": status,
        "candidate_runtime_key": stable_key(row.get("mechanical_scope_key"), role, row.get("source_row_id")),
        "candidate_runtime_callable_name": callable_name,
        "candidate_runtime_callable_contract": (
            "scope_match_then_emit_default_off_observation_or_non_scalar_action_without_live_effect"
        ),
        "candidate_runtime_emission_class": emission,
        "default_off_observation_score": row.get("default_off_observation_score"),
        "candidate_component_consumed_in_runtime": True,
        "runtime_component_policy": "branch_local_default_off_observation_only",
        **_scope(row),
    }


def event_matches_candidate_runtime(runtime_row: dict[str, Any], event: dict[str, Any]) -> bool:
    for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "mechanical_scope_key"):
        expected = runtime_row.get(field)
        if expected not in (None, "", "ALL", "ALL_SESSIONS", "ALL_HORIZONS", "ALL_PRIMITIVES"):
            if event.get(field) != expected:
                return False
    return True


def execute_candidate_runtime(runtime_row: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_candidate_runtime(runtime_row, event)
    family = str(runtime_row.get("candidate_runtime_component_family") or "")
    if not matched:
        emission = "NO_EMIT_SCOPE_MISMATCH"
        score = None
        action = "NO_ACTION_SCOPE_MISMATCH"
    elif family in {
        "DEFAULT_OFF_SCORER_RUNTIME_COMPONENT",
        "NOFILL_CHALLENGER_RUNTIME_COMPONENT",
        "AVOID_INVERSE_RUNTIME_COMPONENT",
    }:
        emission = str(runtime_row.get("candidate_runtime_emission_class"))
        score = to_float(runtime_row.get("default_off_observation_score"))
        if score is None:
            score = to_float(runtime_row.get("computed_proxy_delta"))
        if family == "AVOID_INVERSE_RUNTIME_COMPONENT" and score is not None:
            score = abs(score)
        action = "EMIT_DEFAULT_OFF_OBSERVATION"
    elif family == "NON_SCALAR_ACTION_RUNTIME_COMPONENT":
        emission = "EMIT_CANDIDATE_NON_SCALAR_ACTION_OBSERVATION"
        score = None
        action = "EMIT_NON_SCALAR_ACTION_REQUIREMENT"
    else:
        emission = "EMIT_CANDIDATE_REPAIR_STRESS_CONTEXT_OBSERVATION"
        score = None
        action = "EMIT_REPAIR_STRESS_CONTEXT_REQUIREMENT"
    return {
        "event_matched_candidate_runtime": matched,
        "candidate_runtime_emission_class": emission,
        "candidate_runtime_action": action,
        "default_off_observation_score": score,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def candidate_runtime_self_test(row: dict[str, Any], index: int) -> dict[str, Any]:
    match_event = {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
    }
    mismatch_event = {**match_event, "mechanical_scope_key": "__mismatch__"}
    positive = execute_candidate_runtime(row, match_event)
    negative = execute_candidate_runtime(row, mismatch_event)
    return {
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "candidate_runtime_self_test_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-SELFTEST-{index:06d}",
        "input_candidate_runtime_decision_row_id": row.get("candidate_runtime_decision_row_id"),
        "input_candidate_execution_row_id": row.get("input_candidate_execution_row_id"),
        "candidate_runtime_key": row.get("candidate_runtime_key"),
        "positive_scope_match_result": positive["event_matched_candidate_runtime"],
        "negative_scope_mismatch_result": negative["event_matched_candidate_runtime"],
        "emitted_observation_class": positive["candidate_runtime_emission_class"],
        "default_off_observation_score": positive["default_off_observation_score"],
        "surface_behavior_executed": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def component_runtime_binding(row: dict[str, Any], index: int, component_type: str) -> dict[str, Any]:
    status = str(row.get("candidate_component_status") or "")
    if any(token in status for token in ("READY", "REGISTERED", "CALLABLE")):
        binding_status = "COMPONENT_RUNTIME_BINDING_READY"
    elif any(token in status for token in ("REPAIR", "HELD", "REQUIRED")):
        binding_status = "COMPONENT_RUNTIME_REPAIR_OR_CONTROL_REQUIRED"
    else:
        binding_status = "COMPONENT_RUNTIME_CONTEXT_READY"
    return {
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "component_runtime_binding_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-{component_type}-BINDING-{index:05d}",
        "component_type": component_type,
        "input_component_row_id": (
            row.get("scorer_component_row_id")
            or row.get("source_component_row_id")
            or row.get("score_control_component_row_id")
            or row.get("nofill_component_row_id")
            or row.get("guard_component_row_id")
            or row.get("opportunity_component_row_id")
            or row.get("recheck_component_row_id")
        ),
        "candidate_component_status": row.get("candidate_component_status"),
        "candidate_component_role": row.get("candidate_component_role"),
        "component_runtime_binding_status": binding_status,
        "component_execution_contract": row.get("component_execution_contract"),
        "component_runtime_binding_policy": "branch_local_default_off_or_fail_closed_research_only",
        **_scope(row),
    }


def market_runtime_binding(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("candidate_component_status") or "")
    if "REPAIR" in status:
        binding_status = "MARKET_RUNTIME_SOURCE_REPAIR_OR_PROXY_BINDING_READY"
    elif "SHADOW" in status:
        binding_status = "MARKET_RUNTIME_SHADOW_DEFAULT_OFF_BINDING_READY"
    elif "PROXY_CONTROL" in status:
        binding_status = "MARKET_RUNTIME_PROXY_CONTROL_BINDING_READY"
    elif "SYSTEM_INPUT" in status:
        binding_status = "MARKET_RUNTIME_SYSTEM_INPUT_BINDING_READY"
    elif "REJECT" in status:
        binding_status = "MARKET_RUNTIME_REJECT_CLAIM_PRESERVE_OPPORTUNITY_BINDING"
    else:
        binding_status = "MARKET_RUNTIME_REPLAY_ONLY_BINDING_READY"
    return {
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "market_runtime_binding_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-BINDING-{index:05d}",
        "input_market_component_row_id": row.get("market_component_row_id"),
        "candidate_component_status": row.get("candidate_component_status"),
        "candidate_component_role": row.get("candidate_component_role"),
        "market_runtime_binding_status": binding_status,
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


def candidate_runtime_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("candidate_runtime_status")
            or row.get("component_runtime_binding_status")
            or row.get("market_runtime_binding_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_runtime": UNIFIED_SYSTEM_CANDIDATE_RUNTIME,
        "candidate_runtime_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RUNTIME-ROLLUP-{index:05d}",
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
