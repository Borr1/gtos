"""Execute integrated scoring/result tables into branch-local dispatch outputs."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_integrated_result_execution.py"
)


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
        "integrated_proxy_delta_band": row.get("integrated_proxy_delta_band"),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def integrated_result_execution(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("integrated_result_decision") or "")
    if decision == "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE":
        family = "EXECUTE_SCORER_REGISTRY_CODE"
        status = "INTEGRATED_RESULT_EXECUTION_SCORER_REGISTRY_READY"
        action = "emit_branch_local_default_off_registry_code"
    elif decision == "KEEP_NOFILL_CHALLENGER_COMPARATOR_RESULT":
        family = "EXECUTE_NOFILL_STATUS_QUO_COMPARATOR_SCORING"
        status = "INTEGRATED_RESULT_EXECUTION_NOFILL_COMPARATOR_READY"
        action = "score_status_quo_vs_nofill_challenger_proxy_result"
    elif decision == "KEEP_AVOID_INVERSE_ENTRY_FAILURE_FILTER":
        family = "EXECUTE_AVOID_INVERSE_FEATURE_EMISSION"
        status = "INTEGRATED_RESULT_EXECUTION_AVOID_INVERSE_FEATURE_READY"
        action = "emit_avoid_inverse_or_entry_failure_feature"
    elif decision == "SOURCE_CONTROL_GUARD_OR_OPPORTUNITY_SYSTEM_INPUT":
        family = "EXECUTE_SOURCE_CONTROL_GUARD_OR_OPPORTUNITY_DISPATCH"
        status = "INTEGRATED_RESULT_EXECUTION_NON_SCALAR_DISPATCH_READY"
        action = "dispatch_source_control_guard_or_opportunity_result"
    else:
        family = "EXECUTE_REDESIGN_REPAIR_STRESS_DISPATCH"
        status = "INTEGRATED_RESULT_EXECUTION_REDESIGN_STRESS_READY"
        action = "dispatch_redesign_repair_or_stress_control_result"
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "integrated_result_execution_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-{index:06d}",
        "input_integrated_scoring_decision_row_id": row.get("integrated_scoring_decision_row_id"),
        "input_execution_integration_decision_row_id": row.get("input_execution_integration_decision_row_id"),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "integrated_result_decision": decision,
        "integrated_result_execution_family": family,
        "integrated_result_execution_status": status,
        "integrated_result_execution_action": action,
        "integrated_result_execution_key": stable_key(
            row.get("integration_result_key"),
            row.get("integrated_result_decision"),
            row.get("source_row_id"),
        ),
        "current_claim_only_rejection": row.get("current_claim_only_rejection") is True,
        "underlying_mechanism_preserved": row.get("underlying_mechanism_preserved") is not False,
        "integration_row_consumed_in_execution": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def scorer_registry_dispatch(row: dict[str, Any], index: int) -> dict[str, Any]:
    ready = row.get("module_result_decision") == "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC"
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "scorer_registry_dispatch_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORER-REGISTRY-DISPATCH-{index:05d}",
        "input_default_off_module_result_row_id": row.get("default_off_module_result_row_id"),
        "scorer_registry_dispatch_status": "SCORER_REGISTRY_CODE_EMITTED_DEFAULT_OFF" if ready else "SCORER_REGISTRY_HELD_FOR_CONTROL_OR_REDESIGN",
        "scorer_registry_dispatch_action": "register_default_off_scope_matcher" if ready else "hold_registry_until_control_or_redesign",
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "candidate_callable_name": row.get("candidate_callable_name"),
        "event_match_policy": row.get("event_match_policy"),
        "required_guards": row.get("required_guards", []),
        "default_off": True,
        "guard_binding_required": row.get("guard_binding_required") is not False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def source_control_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("source_builder_decision") or "")
    if decision == "RUN_EXACT_OR_SAME_SCOPE_CONTROL_BUILDER":
        status = "SOURCE_CONTROL_EXECUTION_EXACT_BUILDER_OUTPUT_READY"
    elif decision == "RUN_SOURCE_REPAIR_OR_PROXY_BUILDER":
        status = "SOURCE_CONTROL_EXECUTION_REPAIR_PROXY_OUTPUT_READY"
    else:
        status = "SOURCE_CONTROL_EXECUTION_CONTEXT_ONLY"
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "source_control_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SOURCE-EXEC-OUTPUT-{index:05d}",
        "input_source_control_builder_result_row_id": row.get("source_control_builder_result_row_id"),
        "source_control_execution_status": status,
        "source_control_execution_action": decision,
        "builder_spec": row.get("builder_spec"),
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": row.get("missing_source_proof", []),
        "missing_source_proof_count": row.get("missing_source_proof_count", 0),
        "result_rejoin_contract": row.get("result_rejoin_contract"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def score_control_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("score_control_decision") or "")
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "score_control_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORE-CONTROL-EXEC-{index:05d}",
        "input_score_control_result_table_row_id": row.get("score_control_result_table_row_id"),
        "score_control_execution_status": (
            "SCORE_CONTROL_EXECUTION_TABLE_SCORABLE" if decision == "KEEP_SCORE_WITH_PASS_CONTROL_TABLE" else "SCORE_CONTROL_EXECUTION_REPAIR_OR_CONTEXT"
        ),
        "score_control_execution_action": decision,
        "pass_control_delta_proxy": row.get("pass_control_delta_proxy"),
        "pass_control_delta_band": row.get("pass_control_delta_band"),
        "expectancy_style_proxy_delta": row.get("expectancy_style_proxy_delta"),
        "expectancy_style_proxy_delta_band": row.get("expectancy_style_proxy_delta_band"),
        "control_denominator_required": row.get("control_denominator_required"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def nofill_comparator_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("nofill_comparator_decision") or "")
    avoid = decision == "KEEP_NOFILL_AVOID_INVERSE_FILTER"
    challenger = decision == "KEEP_NOFILL_POSITIVE_CHALLENGER_COMPARATOR"
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "nofill_comparator_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-NOFILL-EXEC-OUTPUT-{index:05d}",
        "input_nofill_comparator_result_table_row_id": row.get("nofill_comparator_result_table_row_id"),
        "nofill_comparator_execution_status": (
            "NOFILL_EXECUTION_STATUS_QUO_CHALLENGER_SCORING_READY"
            if challenger
            else "NOFILL_EXECUTION_AVOID_INVERSE_FEATURE_EMITTED"
            if avoid
            else "NOFILL_EXECUTION_REPAIR_OR_STRESS_READY"
        ),
        "nofill_comparator_execution_action": decision,
        "status_quo_comparator_scoring_ready": challenger,
        "avoid_inverse_feature_emitted": avoid,
        "nofill_system_role": row.get("nofill_system_role"),
        "status_quo_control_required": row.get("status_quo_control_required"),
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        "negative_signal_preserved_as_filter": row.get("negative_signal_preserved_as_filter"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def guard_dispatch_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "guard_dispatch_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-GUARD-DISPATCH-{index:05d}",
        "input_guard_binding_result_row_id": row.get("guard_binding_result_row_id"),
        "guard_dispatch_status": "GUARD_DISPATCH_FAIL_CLOSED_ACTIVE_IN_BRANCH_LOCAL_RESULT",
        "guard_dispatch_action": row.get("guard_binding_decision"),
        "guard_family": row.get("guard_family"),
        "fail_closed_condition": row.get("fail_closed_condition"),
        "guard_spec": row.get("guard_spec"),
        "guard_blocks_unconditional_score_use": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def opportunity_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "opportunity_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-OPPORTUNITY-EXEC-{index:05d}",
        "input_opportunity_result_row_id": row.get("opportunity_result_row_id"),
        "opportunity_execution_status": "OPPORTUNITY_EXECUTION_FAILURE_INTELLIGENCE_EMITTED",
        "opportunity_execution_action": row.get("opportunity_result_decision"),
        "current_claim_failure_preserved": row.get("current_claim_failure_preserved") is not False,
        "underlying_mechanism_not_discarded": row.get("underlying_mechanism_not_discarded") is not False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def recheck_execution_output(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "recheck_execution_output_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RECHECK-EXEC-{index:05d}",
        "input_recheck_result_row_id": row.get("recheck_result_row_id"),
        "recheck_execution_status": "RECHECK_EXECUTION_ROUTE_EMITTED",
        "recheck_execution_action": row.get("recheck_result_decision"),
        "recheck_reason": row.get("recheck_reason"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def market_transfer_dispatch(row: dict[str, Any], index: int) -> dict[str, Any]:
    decision = str(row.get("market_transfer_decision") or "")
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "market_transfer_dispatch_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-DISPATCH-{index:05d}",
        "input_market_transfer_decision_row_id": row.get("market_transfer_decision_row_id"),
        "market_transfer_dispatch_status": f"{decision}_DISPATCHED",
        "market_transfer_dispatch_action": decision,
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
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def integrated_result_execution_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("integrated_result_execution_status")
            or row.get("scorer_registry_dispatch_status")
            or row.get("source_control_execution_status")
            or row.get("score_control_execution_status")
            or row.get("nofill_comparator_execution_status")
            or row.get("guard_dispatch_status")
            or row.get("opportunity_execution_status")
            or row.get("recheck_execution_status")
            or row.get("market_transfer_dispatch_status")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_integrated_result_execution": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_RESULT_EXECUTION,
        "integrated_result_execution_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-EXEC-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "row_count": len(rows),
        "status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
