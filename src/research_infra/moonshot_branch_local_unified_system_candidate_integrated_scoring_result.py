"""Convert execution-integration rows into integrated branch-local scoring results."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT = (
    "src/research_infra/moonshot_branch_local_unified_system_candidate_integrated_scoring_result.py"
)


def to_float(value: Any) -> float | None:
    if isinstance(value, bool) or value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def stable_key(*parts: Any) -> str:
    payload = "|".join("" if part is None else str(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def proxy_delta_band(value: Any) -> str:
    delta = to_float(value)
    if delta is None:
        return "PROXY_DELTA_NOT_NUMERIC"
    if delta >= 0.25:
        return "PROXY_DELTA_STRONG_POSITIVE"
    if delta > 0:
        return "PROXY_DELTA_POSITIVE"
    if delta <= -0.25:
        return "PROXY_DELTA_STRONG_NEGATIVE"
    if delta < 0:
        return "PROXY_DELTA_NEGATIVE"
    return "PROXY_DELTA_ZERO"


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
        "integrated_proxy_delta_band": proxy_delta_band(row.get("computed_proxy_delta")),
        "exact_R_availability": row.get("exact_R_availability"),
        "proxy_R_availability": row.get("proxy_R_availability"),
        "fillability_no_fill_status": row.get("fillability_no_fill_status"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "summary_only_terminal": False,
    }


def integrated_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    family = str(row.get("execution_integration_family") or "")
    status = str(row.get("execution_integration_status") or "")
    delta = to_float(row.get("integration_proxy_delta", row.get("computed_proxy_delta")))
    if family == "INTEGRATE_DEFAULT_OFF_SCORER_REGISTRY_MODULE":
        decision = "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE"
        role = "default_off_scoring_component"
    elif family == "INTEGRATE_NOFILL_CHALLENGER_COMPARATOR_RESULT":
        decision = "KEEP_NOFILL_CHALLENGER_COMPARATOR_RESULT"
        role = "status_quo_vs_challenger_comparator"
    elif family == "INTEGRATE_AVOID_INVERSE_ENTRY_FAILURE_RESULT":
        decision = "KEEP_AVOID_INVERSE_ENTRY_FAILURE_FILTER"
        role = "avoid_inverse_or_entry_failure_component"
    elif family == "INTEGRATE_NON_SCALAR_GUARD_SOURCE_OR_OPPORTUNITY_RESULT":
        decision = "SOURCE_CONTROL_GUARD_OR_OPPORTUNITY_SYSTEM_INPUT"
        role = "non_scalar_guard_source_or_opportunity_component"
    elif "REPAIR" in status or "STRESS" in status:
        decision = "REDESIGN_REPAIR_OR_STRESS_CONTROL_RESULT"
        role = "repair_stress_or_context_component"
    else:
        decision = "REDESIGN_CURRENT_CLAIM_KEEP_MECHANISM"
        role = "current_claim_redesign_component"
    if delta is not None and delta < 0 and decision.startswith("KEEP_NOFILL"):
        decision = "REDESIGN_AS_AVOID_INVERSE_OR_FAILURE_FILTER"
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "integrated_scoring_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-SCORING-{index:06d}",
        "input_execution_integration_decision_row_id": row.get("execution_integration_decision_row_id"),
        "input_candidate_implementation_execution_result_row_id": row.get(
            "input_candidate_implementation_execution_result_row_id"
        ),
        "input_unified_system_computed_action_row_id": row.get("input_unified_system_computed_action_row_id"),
        "execution_integration_family": family,
        "execution_integration_status": status,
        "integrated_result_decision": decision,
        "integrated_result_role": role,
        "keep_kill_redesign_implement_decision": decision,
        "current_claim_only_rejection": decision.startswith("REDESIGN_CURRENT_CLAIM"),
        "underlying_mechanism_preserved": True,
        "integration_result_key": row.get("integration_result_key")
        or stable_key(row.get("execution_integration_decision_row_id"), family, row.get("source_row_id")),
        "integrated_proxy_delta": delta,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        "source_hash_lineage": [
            value
            for value in [row.get("upstream_source_manifest_hash"), row.get("source_manifest_hash")]
            if value
        ],
        "integration_row_consumed_in_result": True,
        **_scope(row),
    }


def default_off_module_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    ready = row.get("registry_module_status") == "REGISTRY_MODULE_DEFAULT_OFF_EVENT_MATCH_READY"
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "default_off_module_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MODULE-RESULT-{index:05d}",
        "input_registry_module_row_id": row.get("registry_module_row_id"),
        "module_result_status": "DEFAULT_OFF_MODULE_SPEC_READY" if ready else "DEFAULT_OFF_MODULE_REDESIGN_OR_CONTROL_REQUIRED",
        "module_result_decision": "IMPLEMENT_DEFAULT_OFF_MODULE_SPEC" if ready else "REDESIGN_OR_CONTROL_BEFORE_MODULE_SPEC",
        "branch_local_registry_key": row.get("branch_local_registry_key"),
        "candidate_callable_name": row.get("candidate_callable_name"),
        "event_match_policy": row.get("event_match_policy"),
        "required_guards": row.get("required_guards", []),
        "guard_binding_required": True,
        "default_off": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def source_control_builder_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("source_control_result_status") or "")
    if status == "SOURCE_CONTROL_RESULT_BUILDER_EXECUTION_READY":
        decision = "RUN_EXACT_OR_SAME_SCOPE_CONTROL_BUILDER"
    elif status == "SOURCE_CONTROL_RESULT_REPAIR_PROXY_EXECUTION_READY":
        decision = "RUN_SOURCE_REPAIR_OR_PROXY_BUILDER"
    else:
        decision = "PRESERVE_SOURCE_CONTEXT_UNTIL_REPAIR_ROUTE"
    missing = row.get("missing_source_proof", [])
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "source_control_builder_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SOURCE-BUILDER-RESULT-{index:05d}",
        "input_source_control_result_row_id": row.get("source_control_result_row_id"),
        "source_builder_result_status": status,
        "source_builder_decision": decision,
        "builder_spec": row.get("builder_spec"),
        "same_resource_execution_available": row.get("same_resource_execution_available"),
        "missing_source_proof": missing,
        "missing_source_proof_count": len(missing) if isinstance(missing, list) else 0,
        "result_rejoin_contract": row.get("result_rejoin_contract"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def score_control_result_table(row: dict[str, Any], index: int) -> dict[str, Any]:
    pass_delta = to_float(row.get("pass_control_delta_proxy"))
    exp_delta = to_float(row.get("expectancy_style_proxy_delta"))
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "score_control_result_table_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-SCORE-CONTROL-TABLE-{index:05d}",
        "input_score_control_result_row_id": row.get("score_control_result_row_id"),
        "score_control_result_status": row.get("score_control_result_status"),
        "score_control_decision": (
            "KEEP_SCORE_WITH_PASS_CONTROL_TABLE"
            if row.get("score_control_result_status") == "SCORE_CONTROL_RESULT_COMPARATOR_SCORABLE"
            else "SOURCE_REPAIR_OR_CONTEXT_BEFORE_SCORE_CONTROL"
        ),
        "pass_control_delta_proxy": pass_delta,
        "pass_control_delta_band": proxy_delta_band(pass_delta),
        "expectancy_style_proxy_delta": exp_delta,
        "expectancy_style_proxy_delta_band": proxy_delta_band(exp_delta),
        "control_denominator_required": row.get("control_denominator_required"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def nofill_comparator_result_table(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("nofill_result_status") or "")
    if status == "NOFILL_RESULT_POSITIVE_CHALLENGER_SCORABLE":
        decision = "KEEP_NOFILL_POSITIVE_CHALLENGER_COMPARATOR"
    elif status == "NOFILL_RESULT_AVOID_INVERSE_FILTER_SCORABLE":
        decision = "KEEP_NOFILL_AVOID_INVERSE_FILTER"
    elif status == "NOFILL_RESULT_SOURCE_REPAIR_REQUIRED":
        decision = "SOURCE_REPAIR_TARGET_STOP_OR_NOFILL_BEFORE_COMPARATOR"
    else:
        decision = "REDESIGN_OR_STRESS_TEST_NOFILL_COMPARATOR"
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "nofill_comparator_result_table_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-NOFILL-TABLE-{index:05d}",
        "input_nofill_result_row_id": row.get("nofill_result_row_id"),
        "nofill_result_status": status,
        "nofill_comparator_decision": decision,
        "nofill_system_role": row.get("nofill_system_role"),
        "status_quo_control_required": row.get("status_quo_control_required"),
        "opportunity_preserved_as": row.get("opportunity_preserved_as"),
        "negative_signal_preserved_as_filter": row.get("negative_signal_preserved_as_filter"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def guard_binding_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "guard_binding_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-GUARD-BINDING-RESULT-{index:05d}",
        "input_guard_bound_integration_row_id": row.get("guard_bound_integration_row_id"),
        "guard_binding_status": "GUARD_BINDING_FAIL_CLOSED_ATTACHED",
        "guard_binding_decision": "BIND_FAIL_CLOSED_GUARD_TO_RESULT_COMPONENT",
        "guard_family": row.get("guard_family"),
        "fail_closed_condition": row.get("fail_closed_condition"),
        "guard_spec": row.get("guard_spec"),
        "guard_blocks_unconditional_score_use": True,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def opportunity_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "opportunity_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-OPPORTUNITY-RESULT-{index:05d}",
        "input_opportunity_integration_row_id": row.get("opportunity_integration_row_id"),
        "opportunity_result_status": "CURRENT_CLAIM_FAILURE_INTELLIGENCE_PRESERVED",
        "opportunity_result_decision": "MERGE_FAILURE_AS_AVOID_REDESIGN_CONTEXT_OR_SOURCE_CAPTURE",
        "current_claim_failure_preserved": row.get("current_claim_failure_preserved") is not False,
        "underlying_mechanism_not_discarded": row.get("underlying_mechanism_not_discarded") is not False,
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def recheck_result(row: dict[str, Any], index: int) -> dict[str, Any]:
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "recheck_result_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-RECHECK-RESULT-{index:05d}",
        "input_recheck_integration_row_id": row.get("recheck_integration_row_id"),
        "recheck_result_status": "RECHECK_RESULT_ROUTE_READY",
        "recheck_result_decision": "EXECUTE_RECHECK_THEN_ROUTE_TO_SOURCE_CONTROL_OR_REDESIGN",
        "recheck_reason": row.get("recheck_reason"),
        "upstream_source_manifest_hash": row.get("source_manifest_hash") or row.get("upstream_source_manifest_hash"),
        **_scope(row),
    }


def market_transfer_decision(row: dict[str, Any], index: int) -> dict[str, Any]:
    status = str(row.get("market_system_integration_status") or "")
    if status == "MARKET_SYSTEM_INTEGRATION_SOURCE_REPAIR_PROXY_READY":
        decision = "MARKET_SOURCE_REPAIR_OR_PROXY_EXECUTE"
    elif status == "MARKET_SYSTEM_INTEGRATION_SHADOW_DEFAULT_OFF_READY":
        decision = "MARKET_SHADOW_DEFAULT_OFF_CANDIDATE"
    elif status == "MARKET_SYSTEM_INTEGRATION_PROXY_CONTROL_FEATURE_READY":
        decision = "MARKET_PROXY_CONTROL_FEATURE"
    elif status == "MARKET_SYSTEM_INTEGRATION_SYSTEM_INPUT_READY":
        decision = "MARKET_MERGE_AS_SYSTEM_INPUT"
    elif status == "MARKET_SYSTEM_INTEGRATION_REJECTED_CLAIM_OPPORTUNITY_READY":
        decision = "REJECT_CURRENT_CLAIM_PRESERVE_MARKET_OPPORTUNITY"
    else:
        decision = "MARKET_REPLAY_ONLY_TRANSFER_CONTEXT"
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "market_transfer_decision_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-MARKET-TRANSFER-RESULT-{index:05d}",
        "input_market_system_integration_row_id": row.get("market_system_integration_row_id"),
        "market_system_integration_status": status,
        "market_transfer_decision": decision,
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


def integrated_result_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    status_counts = Counter(
        str(
            row.get("integrated_result_decision")
            or row.get("module_result_status")
            or row.get("source_builder_decision")
            or row.get("score_control_decision")
            or row.get("nofill_comparator_decision")
            or row.get("guard_binding_status")
            or row.get("opportunity_result_status")
            or row.get("recheck_result_status")
            or row.get("market_transfer_decision")
        )
        for row in rows
    )
    return {
        "unified_system_candidate_integrated_scoring_result": UNIFIED_SYSTEM_CANDIDATE_INTEGRATED_SCORING_RESULT,
        "integrated_result_rollup_row_id": f"OHLC-GTOS-UNIFIED-CANDIDATE-INTEGRATED-RESULT-ROLLUP-{index:05d}",
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
