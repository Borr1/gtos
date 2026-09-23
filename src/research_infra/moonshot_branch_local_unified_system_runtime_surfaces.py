"""Branch-local runtime surfaces for unified moonshot executable artifacts."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_RUNTIME_SURFACE = "src/research_infra/moonshot_branch_local_unified_system_runtime_surfaces.py"


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


def _surface_family(row: dict[str, Any]) -> str:
    family = str(row.get("executable_artifact_family") or "")
    return {
        "CODE_SURFACE_ARTIFACT": "SCORER_REGISTRY_RUNTIME_SURFACE",
        "SOURCE_CONTROL_BUILDER_ARTIFACT": "SOURCE_REPLAY_RUNTIME_SURFACE",
        "SCORE_CONTROL_COMPARISON_ARTIFACT": "SCORE_CONTROL_RUNTIME_SURFACE",
        "NOFILL_COMPARATOR_ARTIFACT": "NOFILL_REPLAY_RUNTIME_SURFACE",
        "GUARD_BINDING_ARTIFACT": "GUARD_RUNTIME_SURFACE",
        "CURRENT_CLAIM_OPPORTUNITY_ARTIFACT": "OPPORTUNITY_RUNTIME_SURFACE",
        "RECHECK_ARTIFACT": "RECHECK_RUNTIME_SURFACE",
    }.get(family, "UNKNOWN_RUNTIME_SURFACE")


def runtime_surface_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    surface_family = _surface_family(row)
    status = str(row.get("executable_artifact_status") or "")
    if status in {
        "EXECUTABLE_CODE_SURFACE_READY_DEFAULT_OFF",
        "EXECUTABLE_NOFILL_POSITIVE_COMPARATOR_READY",
        "EXECUTABLE_SOURCE_CONTROL_BUILDER_READY",
        "EXECUTABLE_GUARD_BINDING_READY",
        "EXECUTABLE_OPPORTUNITY_ROUTE_READY",
        "EXECUTABLE_RECHECK_ROUTE_READY",
    }:
        runtime_status = "RUNTIME_SURFACE_IMPLEMENTATION_READY_DEFAULT_OFF"
    elif status == "EXECUTABLE_NOFILL_AVOID_INVERSE_ROUTE_READY":
        runtime_status = "RUNTIME_SURFACE_AVOID_INVERSE_IMPLEMENTATION_READY_DEFAULT_OFF"
    else:
        runtime_status = "RUNTIME_SURFACE_CONTROL_REDESIGN_OR_STRESS_REQUIRED"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "runtime_surface_decision_row_id": f"OHLC-GTOS-UNIFIED-RUNTIME-SURFACE-{index:06d}",
        "input_executable_artifact_decision_row_id": row.get("executable_artifact_decision_row_id"),
        "input_implementation_execution_decision_row_id": row.get("input_implementation_execution_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "executable_artifact_family": row.get("executable_artifact_family"),
        "executable_artifact_status": row.get("executable_artifact_status"),
        "runtime_surface_family": surface_family,
        "runtime_surface_status": runtime_status,
        "runtime_surface_key": stable_key(row.get("mechanical_scope_key"), surface_family, row.get("source_row_id")),
        "runtime_callable_contract": "branch_local_default_off_event_in_observation_out_with_guarded_scope_match",
        "executable_artifact_row_consumed_in_runtime_surface": True,
        "missed_opportunity_preserved": row.get("missed_opportunity_preserved") is not False,
        **_scope(row),
    }


def event_matches_runtime_surface(surface: dict[str, Any], event: dict[str, Any]) -> bool:
    for field in ("symbol", "route_session", "horizon_id", "primitive_flag", "mechanical_scope_key"):
        expected = surface.get(field)
        if expected not in (None, "", "ALL", "ALL_SESSIONS", "ALL_HORIZONS", "ALL_PRIMITIVES"):
            if event.get(field) != expected:
                return False
    return True


def score_runtime_surface_event(surface: dict[str, Any], event: dict[str, Any]) -> dict[str, Any]:
    matched = event_matches_runtime_surface(surface, event)
    delta = to_float(surface.get("computed_proxy_delta"))
    family = str(surface.get("runtime_surface_family") or "")
    if not matched:
        emitted = "NO_EMIT_SCOPE_MISMATCH"
        score = None
    elif family == "NOFILL_REPLAY_RUNTIME_SURFACE" and delta is not None and delta <= -0.15:
        emitted = "EMIT_AVOID_INVERSE_OR_ENTRY_FAILURE_OBSERVATION"
        score = abs(delta)
    elif family == "SCORER_REGISTRY_RUNTIME_SURFACE" and delta is not None and delta >= 0.05:
        emitted = "EMIT_DEFAULT_OFF_POSITIVE_SCORER_OBSERVATION"
        score = delta
    elif family == "NOFILL_REPLAY_RUNTIME_SURFACE" and delta is not None and delta >= 0.05:
        emitted = "EMIT_DEFAULT_OFF_NOFILL_CHALLENGER_OBSERVATION"
        score = delta
    elif family in {"SOURCE_REPLAY_RUNTIME_SURFACE", "GUARD_RUNTIME_SURFACE", "OPPORTUNITY_RUNTIME_SURFACE", "RECHECK_RUNTIME_SURFACE"}:
        emitted = "EMIT_NON_SCALAR_ACTION_OBSERVATION"
        score = None
    else:
        emitted = "EMIT_REPAIR_STRESS_OR_CONTEXT_OBSERVATION"
        score = delta
    return {
        "event_matched_runtime_surface": matched,
        "emitted_observation_class": emitted,
        "default_off_observation_score": score,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def runtime_surface_self_test(row: dict[str, Any], index: int) -> dict[str, Any]:
    match_event = {
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
    }
    mismatch_event = {**match_event, "mechanical_scope_key": "__mismatch__"}
    positive = score_runtime_surface_event(row, match_event)
    negative = score_runtime_surface_event(row, mismatch_event)
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "runtime_surface_self_test_row_id": f"OHLC-GTOS-UNIFIED-RUNTIME-SELFTEST-{index:06d}",
        "input_runtime_surface_decision_row_id": row.get("runtime_surface_decision_row_id"),
        "runtime_surface_key": row.get("runtime_surface_key"),
        "positive_scope_match_result": positive["event_matched_runtime_surface"],
        "negative_scope_mismatch_result": negative["event_matched_runtime_surface"],
        "emitted_observation_class": positive["emitted_observation_class"],
        "default_off_observation_score": positive["default_off_observation_score"],
        "surface_behavior_executed": True,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def scorer_registry_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("code_surface_status") or "")
    callable_name = str(row.get("candidate_function_name") or f"score_unified_runtime_surface_{index:05d}")
    if status in {"CODE_SURFACE_STRONG_POSITIVE_DEFAULT_OFF_READY", "CODE_SURFACE_POSITIVE_DEFAULT_OFF_READY"}:
        registry_status = "SCORER_RUNTIME_REGISTERED_DEFAULT_OFF"
    else:
        registry_status = "SCORER_RUNTIME_HELD_FOR_CONTROL_OR_REDESIGN"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "scorer_registry_surface_row_id": f"OHLC-GTOS-UNIFIED-SCORER-REGISTRY-{index:05d}",
        "input_code_surface_artifact_row_id": row.get("code_surface_artifact_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "scorer_registry_status": registry_status,
        "registered_callable_name": callable_name,
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "event_match_contract": row.get("event_match_contract"),
        "score_contract": row.get("score_contract"),
        "guard_requirements": row.get("guard_requirements", []),
        "emission_schema": ["scope_match", "default_off_observation_score", "guard_state", "control_lookup_state"],
        **_scope(row),
    }


def source_replay_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_control_builder_execution_status") or "")
    if "EXECUTABLE_FROM_CURRENT_SCOPE" in status:
        replay_status = "SOURCE_REPLAY_EXACT_CONTROL_BUILD_CALLABLE_READY"
    elif "REPLAY_ATTACHMENT" in status:
        replay_status = "SOURCE_REPLAY_ATTACHMENT_CALLABLE_READY"
    else:
        replay_status = "SOURCE_REPLAY_PROXY_OR_ACQUISITION_CALLABLE_MATERIALIZED"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "source_replay_surface_row_id": f"OHLC-GTOS-UNIFIED-SOURCE-REPLAY-{index:05d}",
        "input_source_control_builder_execution_row_id": row.get("source_control_builder_execution_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "source_replay_status": replay_status,
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "source_rows_needed_to_n20_proxy": row.get("source_rows_needed_to_n20_proxy"),
        "replay_callable_contract": "build exact control/source replay/proxy observation for same mechanical scope",
        **_scope(row),
    }


def score_control_runtime_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("score_control_comparison_status") or "")
    if status == "SCORE_CONTROL_POSITIVE_COMPARISON_READY":
        runtime_status = "SCORE_CONTROL_RUNTIME_COMPARATOR_READY_DEFAULT_OFF"
    elif status == "SCORE_CONTROL_SOURCE_OR_DENOMINATOR_REPAIR_REQUIRED":
        runtime_status = "SCORE_CONTROL_RUNTIME_SOURCE_REPAIR_REQUIRED"
    else:
        runtime_status = "SCORE_CONTROL_RUNTIME_CONTEXT_OR_REDESIGN_READY"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "score_control_runtime_surface_row_id": f"OHLC-GTOS-UNIFIED-SCORE-CONTROL-RUNTIME-{index:05d}",
        "input_score_control_comparison_artifact_row_id": row.get("score_control_comparison_artifact_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "score_control_runtime_status": runtime_status,
        "score_control_system_role": row.get("score_control_system_role"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "comparator_contract": row.get("comparator_contract"),
        **_scope(row),
    }


def nofill_replay_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("nofill_comparator_outcome_status") or "")
    if status == "NOFILL_POSITIVE_VARIANT_KEEP_FOR_STATUS_QUO_COMPARATOR":
        replay_status = "NOFILL_REPLAY_POSITIVE_CHALLENGER_SCORER_READY"
    elif status == "NOFILL_NEGATIVE_VARIANT_FORCE_AVOID_INVERSE_OR_ENTRY_FAILURE_ROLE":
        replay_status = "NOFILL_REPLAY_AVOID_INVERSE_SCORER_READY"
    elif status == "NOFILL_WEAK_VARIANT_STRESS_CONTROL_REQUIRED":
        replay_status = "NOFILL_REPLAY_STRESS_SCORER_READY"
    else:
        replay_status = "NOFILL_REPLAY_SOURCE_OR_TARGETSTOP_REPAIR_REQUIRED"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "nofill_replay_surface_row_id": f"OHLC-GTOS-UNIFIED-NOFILL-REPLAY-{index:05d}",
        "input_nofill_comparator_outcome_row_id": row.get("nofill_comparator_outcome_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "nofill_replay_status": replay_status,
        "nofill_system_role": row.get("nofill_system_role"),
        "target_stop_proxy_basis": row.get("target_stop_proxy_basis"),
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "replay_callable_contract": "score no-fill variant against status-quo control or emit avoid/inverse failure feature",
        **_scope(row),
    }


def guard_runtime_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "guard_runtime_surface_row_id": f"OHLC-GTOS-UNIFIED-GUARD-RUNTIME-{index:05d}",
        "input_guard_binding_execution_row_id": row.get("guard_binding_execution_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "guard_runtime_status": "GUARD_RUNTIME_FAIL_CLOSED_BINDING_READY",
        "guard_family": row.get("guard_family"),
        "guard_fail_closed_condition": row.get("guard_fail_closed_condition"),
        "guard_policy": row.get("guard_policy"),
        **_scope(row),
    }


def opportunity_runtime_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "opportunity_runtime_surface_row_id": f"OHLC-GTOS-UNIFIED-OPPORTUNITY-RUNTIME-{index:05d}",
        "input_current_claim_opportunity_route_row_id": row.get("current_claim_opportunity_route_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "opportunity_runtime_status": "CURRENT_CLAIM_OPPORTUNITY_RUNTIME_ROUTE_READY",
        "preserved_opportunity_roles": row.get("preserved_opportunity_roles", []),
        "missed_opportunity_preserved": True,
        **_scope(row),
    }


def recheck_runtime_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "recheck_runtime_surface_row_id": f"OHLC-GTOS-UNIFIED-RECHECK-RUNTIME-{index:05d}",
        "input_recheck_execution_artifact_row_id": row.get("recheck_execution_artifact_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "recheck_runtime_status": "RECHECK_RUNTIME_SOURCE_HORIZON_TARGETABILITY_READY",
        "missing_source_proof": row.get("missing_source_proof", []),
        **_scope(row),
    }


def market_source_runtime_surface(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_source_action_status") or "")
    if "SOURCE_REPAIR" in status:
        runtime_status = "MARKET_SOURCE_RUNTIME_REPAIR_OR_PROXY_READY"
    elif "SHADOW_CANDIDATE" in status:
        runtime_status = "MARKET_SOURCE_RUNTIME_SHADOW_DEFAULT_OFF_READY"
    elif "PROXY_CONTROL_FEATURE" in status:
        runtime_status = "MARKET_SOURCE_RUNTIME_PROXY_CONTROL_READY"
    elif "SYSTEM_INPUT" in status:
        runtime_status = "MARKET_SOURCE_RUNTIME_SYSTEM_INPUT_READY"
    elif "REJECTION" in status:
        runtime_status = "MARKET_SOURCE_RUNTIME_REJECT_CLAIM_PRESERVE_OPPORTUNITY"
    else:
        runtime_status = "MARKET_SOURCE_RUNTIME_REPLAY_ONLY_READY"
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "market_source_runtime_surface_row_id": f"OHLC-GTOS-UNIFIED-MARKET-RUNTIME-{index:05d}",
        "input_market_source_action_row_id": row.get("market_source_action_row_id"),
        "input_market_timeframe_session_horizon_expansion_row_id": row.get(
            "input_market_timeframe_session_horizon_expansion_row_id"
        ),
        "market_source_runtime_status": runtime_status,
        "market_system_role": row.get("market_system_role"),
        "market_transfer_status": row.get("market_transfer_status"),
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


def runtime_surface_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("runtime_surface_status")
            or row.get("scorer_registry_status")
            or row.get("source_replay_status")
            or row.get("nofill_replay_status")
            or row.get("guard_runtime_status")
            or row.get("score_control_runtime_status")
            or row.get("opportunity_runtime_status")
            or row.get("recheck_runtime_status")
            or row.get("market_source_runtime_status")
        )
        for row in rows
    )
    return {
        "unified_system_runtime_surface": UNIFIED_SYSTEM_RUNTIME_SURFACE,
        "runtime_surface_rollup_row_id": f"OHLC-GTOS-UNIFIED-RUNTIME-ROLLUP-{index:05d}",
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
