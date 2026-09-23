"""Materialize unified system work orders into branch-local action results."""

from __future__ import annotations

from collections import Counter
from typing import Any


UNIFIED_SYSTEM_ACTION_RESULT_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_action_results.py"
)


def _numeric_score(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def proxy_result_class(score: Any, family: str) -> str:
    numeric = _numeric_score(score)
    if numeric is None:
        if family == "SOURCE_CONTROL_REPAIR":
            return "PROXY_R_NOT_COMPUTED_SOURCE_OR_CONTROL_ACTION_FIRST"
        if family == "REDESIGN_EXECUTION":
            return "PROXY_R_NOT_COMPUTED_REDESIGN_REPLAY_REQUIRED"
        if family == "GUARD":
            return "PROXY_R_NOT_COMPUTED_GUARD_OR_CONTEXT_ONLY"
        if family == "AUDIT_PRESERVATION":
            return "PROXY_R_NOT_COMPUTED_CURRENT_CLAIM_REJECTED_AUDIT_ONLY"
        return "PROXY_R_NOT_NUMERIC_IN_INPUT_ROW"
    if numeric >= 0.60:
        return "PROXY_R_STYLE_STRONG_POSITIVE"
    if numeric > 0.50:
        return "PROXY_R_STYLE_POSITIVE"
    if numeric <= -0.10:
        return "PROXY_R_STYLE_NEGATIVE"
    if numeric < 0.40:
        return "PROXY_R_STYLE_WEAK_OR_ADVERSE"
    return "PROXY_R_STYLE_NEUTRAL_OR_CONTROL_REQUIRED"


def action_materialization(row: dict[str, Any]) -> dict[str, str]:
    family = str(row.get("work_order_family") or "RECHECK")
    action = str(row.get("executable_next_action") or "")
    if family == "IMPLEMENTATION":
        return {
            "action_result_family": "IMPLEMENTATION_RESULT",
            "action_execution_status": "BRANCH_LOCAL_DEFAULT_OFF_SPEC_MATERIALIZED",
            "materialized_artifact_kind": row.get("target_artifact_kind") or "code_spec",
            "implementation_decision": "REGISTER_DEFAULT_OFF_SHADOW_CANDIDATE_KEEP_RUNTIME_DISABLED",
            "next_concrete_builder": "write_branch_local_default_off_scorer_or_guarded_shadow_spec",
        }
    if family == "SOURCE_CONTROL_REPAIR":
        if action.startswith("BUILD_EXACT_CONTROL"):
            status = "EXACT_CONTROL_DENOMINATOR_BUILD_ACTION_MATERIALIZED"
        elif action.startswith("CONSUME_SATISFIED"):
            status = "SATISFIED_SOURCE_ATTACHED_TO_REPLAY_ACTION"
        else:
            status = "SOURCE_OR_CONTROL_REPAIR_ACTION_MATERIALIZED"
        return {
            "action_result_family": "SOURCE_CONTROL_REPAIR_RESULT",
            "action_execution_status": status,
            "materialized_artifact_kind": row.get("target_artifact_kind") or "source_control_action",
            "implementation_decision": "REPAIR_PROXY_OR_ACQUIRE_SOURCE_THEN_RESCORE_SAME_LANE",
            "next_concrete_builder": "execute_source_control_denominator_or_source_repair_rows",
        }
    if family == "SCORE_WITH_CONTROL":
        return {
            "action_result_family": "SCORE_WITH_CONTROL_RESULT",
            "action_execution_status": "CONTROL_SCORE_RESULT_ROW_MATERIALIZED",
            "materialized_artifact_kind": row.get("target_artifact_kind") or "score_with_control_result",
            "implementation_decision": "KEEP_SCORE_RESEARCH_ONLY_UNTIL_EXACT_CONTROL_ACCEPTED",
            "next_concrete_builder": "compute_score_with_control_deltas_by_scope",
        }
    if family == "REDESIGN_EXECUTION":
        return {
            "action_result_family": "REDESIGN_EXECUTION_RESULT",
            "action_execution_status": "REDESIGN_VARIANT_ACTION_RESULT_MATERIALIZED",
            "materialized_artifact_kind": row.get("target_artifact_kind") or "redesign_variant_result",
            "implementation_decision": "EXECUTE_VARIANT_WITH_CONTROL_OR_SOURCE_GUARD",
            "next_concrete_builder": "score_nofill_avoid_retest_offset_market_entry_variants",
        }
    if family == "GUARD":
        return {
            "action_result_family": "GUARD_RESULT",
            "action_execution_status": "GUARD_REGISTRATION_RESULT_MATERIALIZED",
            "materialized_artifact_kind": row.get("target_artifact_kind") or "guard_registration",
            "implementation_decision": "REGISTER_GUARD_DEFAULT_OFF_AND_BLOCK_UNCONTROLLED_SCORING",
            "next_concrete_builder": "attach_guard_to_default_off_scorer_or_source_confidence_context",
        }
    if family == "AUDIT_PRESERVATION":
        return {
            "action_result_family": "AUDIT_PRESERVATION_RESULT",
            "action_execution_status": "CURRENT_CLAIM_REJECTION_AUDIT_MATERIALIZED",
            "materialized_artifact_kind": row.get("target_artifact_kind") or "audit_preservation_result",
            "implementation_decision": "REJECT_CURRENT_CLAIM_ONLY_PRESERVE_MECHANISM_OPPORTUNITY",
            "next_concrete_builder": "route_preserved_mechanism_to_redesign_avoid_context_or_source_capture",
        }
    return {
        "action_result_family": "RECHECK_RESULT",
        "action_execution_status": "RECHECK_ACTION_RESULT_MATERIALIZED",
        "materialized_artifact_kind": row.get("target_artifact_kind") or "recheck_result",
        "implementation_decision": "RECHECK_HORIZON_SOURCE_TARGETABILITY_BEFORE_ANY_REJECTION",
        "next_concrete_builder": "execute_horizon_repair_redesign_or_current_claim_rejection_check",
    }


def action_result_from_work_order(
    row: dict[str, Any],
    index: int,
    market_expansion: dict[str, Any] | None = None,
) -> dict[str, Any]:
    materialized = action_materialization(row)
    family = str(row.get("work_order_family") or "RECHECK")
    score = _numeric_score(row.get("proxy_or_module_score"))
    return {
        "unified_system_action_result_surface": UNIFIED_SYSTEM_ACTION_RESULT_SURFACE,
        "unified_system_action_result_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-ACTION-RESULT-{index:06d}",
        "input_unified_system_work_order_row_id": row.get("unified_system_work_order_row_id"),
        "input_unified_system_candidate_row_id": row.get("input_unified_system_candidate_row_id"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "work_order_family": row.get("work_order_family"),
        "executable_next_action": row.get("executable_next_action"),
        "target_artifact_kind": row.get("target_artifact_kind"),
        "proxy_or_module_score": row.get("proxy_or_module_score"),
        "proxy_numeric_score": score,
        "proxy_r_style_result": proxy_result_class(row.get("proxy_or_module_score"), family),
        "source_status": row.get("source_status"),
        "source_confidence_status": row.get("source_confidence_status"),
        "success_or_failure_cause": row.get("success_or_failure_cause"),
        "implementation_implication": row.get("implementation_implication"),
        "current_claim_only_rejection_scope": row.get("current_claim_only_rejection_scope"),
        "missed_opportunity_preserved": row.get("missed_opportunity_preserved") is not False,
        "action_result_consumption_status": "WORK_ORDER_CONSUMED_IN_BRANCH_LOCAL_ACTION_RESULT",
        "same_lane_result_materialized": True,
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        "market_expansion_row_id": (market_expansion or {}).get(
            "market_timeframe_session_horizon_expansion_row_id"
        ),
        "market_expansion_decision": (market_expansion or {}).get("decision"),
        "tradability_status": (market_expansion or {}).get("tradability_status"),
        "available_timeframes": (market_expansion or {}).get("available_timeframes", []),
        "exact_R_availability": (market_expansion or {}).get("exact_R_availability"),
        "proxy_R_availability": (market_expansion or {}).get("proxy_R_availability"),
        "fillability_no_fill_status": (market_expansion or {}).get("fillability_no_fill_status"),
        **materialized,
    }


def action_result_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    family_counts = Counter(str(row.get("action_result_family")) for row in rows)
    status_counts = Counter(str(row.get("action_execution_status")) for row in rows)
    proxy_counts = Counter(str(row.get("proxy_r_style_result")) for row in rows)
    return {
        "unified_system_action_result_surface": UNIFIED_SYSTEM_ACTION_RESULT_SURFACE,
        "action_result_rollup_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-ACTION-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "action_result_rows": len(rows),
        "action_result_family_counts": {key: int(family_counts[key]) for key in sorted(family_counts)},
        "action_execution_status_counts": {key: int(status_counts[key]) for key in sorted(status_counts)},
        "proxy_r_style_result_counts": {key: int(proxy_counts[key]) for key in sorted(proxy_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
