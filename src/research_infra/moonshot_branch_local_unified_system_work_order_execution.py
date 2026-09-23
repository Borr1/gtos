"""Convert unified recommendation rows into executable branch-local work orders."""

from __future__ import annotations

from collections import Counter
from typing import Any


UNIFIED_SYSTEM_WORK_ORDER_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_work_order_execution.py"
)


def _source_text(row: dict[str, Any]) -> str:
    keys = (
        "source_component",
        "unified_action_class",
        "unified_system_decision",
        "unified_decision_group",
        "implementation_implication",
        "source_status",
        "source_confidence_status",
        "success_or_failure_cause",
    )
    return "|".join(str(row.get(key) or "") for key in keys)


def _implementation_action(row: dict[str, Any]) -> tuple[str, str, str]:
    action = row.get("unified_action_class")
    if action == "IMPLEMENT_DEFAULT_OFF_MODULE_CANDIDATE":
        return (
            "REGISTER_DEFAULT_OFF_SCORER_MODULE_SPEC",
            "code_spec_default_off_scorer_module",
            "Materialize branch-local default-off scorer module spec with exact-scope guard and non-scalar target-delta policy.",
        )
    if action == "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE":
        return (
            "REGISTER_DEFAULT_OFF_SCORER_SPEC",
            "code_spec_default_off_scorer",
            "Materialize guarded default-off scorer spec and keep runtime/live permissions disabled.",
        )
    if action == "ENABLE_SHADOW_RULE_WITH_SOURCE_GUARD":
        return (
            "REGISTER_SOURCE_GUARDED_SHADOW_RULE_SPEC",
            "code_spec_source_guarded_shadow_rule",
            "Materialize branch-local shadow rule spec with required source guard and control lookup.",
        )
    if action == "MARKET_GAP_ENTRY_GEOMETRY_IMPLEMENT_CANDIDATE":
        return (
            "REGISTER_MARKET_GAP_ENTRY_GEOMETRY_SPEC",
            "code_spec_market_gap_entry_geometry",
            "Materialize market-gap entry geometry challenger spec and preserve outside-market scope.",
        )
    if action == "MARKET_GAP_AVOID_FILTER_IMPLEMENT_CANDIDATE":
        return (
            "REGISTER_MARKET_GAP_AVOID_FILTER_SPEC",
            "code_spec_market_gap_avoid_filter",
            "Materialize market-gap avoid/inverse filter spec and preserve source/control requirements.",
        )
    return (
        "REGISTER_IMPLEMENTATION_SPEC_RECHECK",
        "code_spec_recheck",
        "Preserve implementable row and recheck action mapping before materialization.",
    )


def _source_control_action(row: dict[str, Any]) -> tuple[str, str, str]:
    action = row.get("unified_action_class")
    text = _source_text(row)
    if action == "BUILD_EXACT_CONTROL_DENOMINATOR":
        return (
            "BUILD_EXACT_CONTROL_DENOMINATOR_AND_RESCORE",
            "source_control_exact_denominator_build",
            "Build exact same-scope control denominator from available tick/M15 evidence or record exact acquisition requirement, then rescore.",
        )
    if action == "SOURCE_GUARD_OR_REPAIR_REQUIRED":
        return (
            "MATERIALIZE_SOURCE_GUARD_AND_RESCORE",
            "source_control_guard_materialization",
            "Materialize source guard or repair source contradiction, then rerun guarded scorer/control comparison.",
        )
    if action == "MARKET_GAP_SOURCE_MATERIALIZATION_REQUIRED":
        return (
            "MATERIALIZE_MARKET_GAP_SOURCE_DENOMINATOR",
            "source_control_market_gap_materialization",
            "Acquire/reconstruct market-gap source rows from available historical roots or exact proxy, then rescore branch.",
        )
    if action == "NOFILL_NEAR_MISS_SOURCE_REQUIREMENT" and "SATISFIED" in text:
        return (
            "CONSUME_SATISFIED_NOFILL_SOURCE_IN_ENTRY_REPLAY",
            "source_control_nofill_source_satisfied",
            "Source requirement is already satisfied; attach it to near-miss offset/market-entry replay instead of blocking.",
        )
    if action == "NOFILL_NEAR_MISS_SOURCE_REQUIREMENT":
        return (
            "REPAIR_NOFILL_NEAR_MISS_SOURCE_THEN_REPLAY",
            "source_control_nofill_source_repair",
            "Repair exact first-spread/closest-touch source requirement or build strongest proxy before entry-variant decision.",
        )
    return (
        "REPAIR_SOURCE_OR_CONTROL_THEN_RESCORE",
        "source_control_general_repair",
        "Repair source/control denominator, preserve opportunity path, and rescore in the same evidence class.",
    )


def _score_action(row: dict[str, Any]) -> tuple[str, str, str]:
    action = row.get("unified_action_class")
    if action == "SCORE_WITH_DEFAULT_OFF_CONTROL_CONTEXT":
        return (
            "SCORE_DEFAULT_OFF_SCORER_AGAINST_CONTROL_CONTEXT",
            "score_with_control_default_off",
            "Score default-off observation against its exact/source-available control context without enabling runtime use.",
        )
    if action == "MARKET_GAP_SCORE_WITH_CONTROL_REQUIRED":
        return (
            "SCORE_MARKET_GAP_VARIANT_WITH_CONTROL",
            "score_with_control_market_gap",
            "Score market-gap entry/avoid candidate against same-scope control rows before implementation decision.",
        )
    return (
        "SCORE_SOURCE_GUARDED_RULE_WITH_CONTROL",
        "score_with_control_source_guarded",
        "Score source-guarded rule against control denominator and preserve proxy limitations.",
    )


def _redesign_action(row: dict[str, Any]) -> tuple[str, str, str]:
    action = row.get("unified_action_class")
    if action == "NOFILL_FAR_MISS_FAMILY_REDESIGN_SYNTHESIS":
        return (
            "SPLIT_NOFILL_FAMILY_BY_SYMBOL_SESSION_CAUSE",
            "redesign_nofill_family_split",
            "Split no-fill family synthesis into symbol/session/reason branches and route each to avoid, retest, or source-confidence action.",
        )
    if action == "NOFILL_FAR_MISS_AVOID_FILTER_CANDIDATE":
        return (
            "EXECUTE_NOFILL_AVOID_OR_INVERSE_VARIANT",
            "redesign_nofill_avoid_inverse",
            "Execute far-miss avoid/inverse variant with preserved current-claim boundary and control comparison.",
        )
    if action == "NOFILL_FAR_MISS_RETEST_REDESIGN_CANDIDATE":
        return (
            "EXECUTE_NOFILL_RETEST_ENTRY_GEOMETRY_REDESIGN",
            "redesign_nofill_retest_entry_geometry",
            "Execute retest redesign by entry geometry/horizon and preserve no-fill failure cause.",
        )
    if action == "NOFILL_NEAR_MISS_ENTRY_OFFSET_VARIANT":
        return (
            "EXECUTE_NEAR_MISS_ENTRY_OFFSET_VARIANT",
            "redesign_near_miss_offset",
            "Execute near-miss entry offset variant and compare against no-change/status-quo control.",
        )
    if action == "NOFILL_NEAR_MISS_MARKET_ENTRY_VARIANT":
        return (
            "EXECUTE_NEAR_MISS_MARKET_ENTRY_PROXY_VARIANT",
            "redesign_near_miss_market_entry",
            "Execute market-entry proxy variant with cost/spread guard and source requirement linkage.",
        )
    if action == "HORIZON_REPAIR_OR_REDESIGN_REQUIRED":
        return (
            "EXECUTE_HORIZON_REPAIR_REDESIGN_OR_KILL_CHECK",
            "redesign_horizon_repair",
            "Split horizon failure into exact repair, shorter-horizon transfer, stress-first redesign, or current-claim-only rejection.",
        )
    return (
        "EXECUTE_REDESIGN_ROW_WITH_CONTROL",
        "redesign_general",
        "Execute redesign row into a concrete variant/control comparison and preserve missed-opportunity route.",
    )


def _guard_action(row: dict[str, Any]) -> tuple[str, str, str]:
    action = row.get("unified_action_class")
    if action == "DENOMINATOR_GUARD_REQUIRED":
        return (
            "REGISTER_DENOMINATOR_GUARD",
            "guard_denominator",
            "Register denominator guard so the scope cannot be scored without required exact/control denominator.",
        )
    if action == "NOFILL_SOURCE_CONFIDENCE_CONTEXT_CANDIDATE":
        return (
            "REGISTER_NOFILL_SOURCE_CONFIDENCE_GUARD",
            "guard_nofill_source_confidence",
            "Register source-confidence guard/context feature for no-fill branches; do not convert to scalar without controls.",
        )
    return (
        "REGISTER_SOURCE_CONFIDENCE_OR_DENOMINATOR_GUARD",
        "guard_general",
        "Register guard and attach exact source/control requirement before scoring.",
    )


def _audit_action(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        "PRESERVE_CURRENT_CLAIM_REJECTION_AND_ROUTE_OPPORTUNITY",
        "audit_current_claim_only_rejection",
        "Preserve current-claim-only rejection with missed-opportunity audit; route mechanism into redesign, avoid/inverse, context feature, source-capture, or merged component.",
    )


def _recheck_action(row: dict[str, Any]) -> tuple[str, str, str]:
    return (
        "RECHECK_HORIZON_TARGETABILITY_AND_SOURCE_STATUS",
        "recheck_horizon_targetability",
        "Recheck horizon/targetability/source status and choose exact repair, proxy score, redesign, or current-claim-only rejection.",
    )


def classify_work_order(row: dict[str, Any]) -> dict[str, Any]:
    group = row.get("unified_decision_group")
    if group == "IMPLEMENT":
        family = "IMPLEMENTATION"
        action, artifact, detail = _implementation_action(row)
        ready = "EXECUTE_BRANCH_LOCAL_DEFAULT_OFF_SPEC_NOW"
    elif group == "SOURCE_OR_CONTROL_REPAIR":
        family = "SOURCE_CONTROL_REPAIR"
        action, artifact, detail = _source_control_action(row)
        ready = "EXECUTE_REPAIR_PROXY_OR_ACQUISITION_NOW"
    elif group == "SCORE_WITH_CONTROL":
        family = "SCORE_WITH_CONTROL"
        action, artifact, detail = _score_action(row)
        ready = "EXECUTE_CONTROL_SCORE_NOW"
    elif group == "REDESIGN":
        family = "REDESIGN_EXECUTION"
        action, artifact, detail = _redesign_action(row)
        ready = "EXECUTE_REDESIGN_VARIANT_NOW"
    elif group == "GUARD":
        family = "GUARD"
        action, artifact, detail = _guard_action(row)
        ready = "REGISTER_GUARD_OR_CONTEXT_FEATURE_NOW"
    elif group == "PRESERVE_AUDIT":
        family = "AUDIT_PRESERVATION"
        action, artifact, detail = _audit_action(row)
        ready = "PRESERVE_AUDIT_AND_ROUTE_MECHANISM_NOW"
    else:
        family = "RECHECK"
        action, artifact, detail = _recheck_action(row)
        ready = "RECHECK_AND_ROUTE_NOW"
    return {
        "work_order_family": family,
        "executable_next_action": action,
        "target_artifact_kind": artifact,
        "concrete_next_action_detail": detail,
        "work_order_ready_state": ready,
    }


def work_order_from_unified_candidate(row: dict[str, Any], index: int) -> dict[str, Any]:
    classified = classify_work_order(row)
    rejection = row.get("current_claim_only_rejection_scope") is not None
    return {
        "unified_system_work_order_surface": UNIFIED_SYSTEM_WORK_ORDER_SURFACE,
        "unified_system_work_order_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-WORKORDER-{index:06d}",
        "input_unified_system_candidate_row_id": row.get("unified_system_candidate_row_id"),
        "source_component": row.get("source_component"),
        "source_row_id": row.get("source_row_id"),
        "mechanical_scope_key": row.get("mechanical_scope_key"),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "unified_action_class": row.get("unified_action_class"),
        "unified_decision_group": row.get("unified_decision_group"),
        "unified_system_decision": row.get("unified_system_decision"),
        "source_status": row.get("source_status"),
        "source_confidence_status": row.get("source_confidence_status"),
        "proxy_or_module_score": row.get("proxy_or_module_score"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "success_or_failure_cause": row.get("success_or_failure_cause"),
        "implementation_implication": row.get("implementation_implication"),
        "row_consumption_status": "UNIFIED_ROW_CONSUMED_IN_BRANCH_LOCAL_WORK_ORDER",
        "same_evidence_class_next_action_required": True,
        "summary_only_terminal": False,
        "missed_opportunity_preserved": True,
        "missed_opportunity_audit_required": rejection,
        "current_claim_only_rejection_scope": row.get("current_claim_only_rejection_scope"),
        "opportunity_path_preserved_as": (
            "current_claim_rejection_audit_plus_redesign_avoid_context_source_capture_or_merged_component"
            if rejection
            else classified["target_artifact_kind"]
        ),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
        **classified,
    }


def work_order_rollup(
    group_key: tuple[Any, ...],
    rows: list[dict[str, Any]],
    index: int,
    rollup_type: str,
) -> dict[str, Any]:
    family_counts = Counter(str(row.get("work_order_family")) for row in rows)
    action_counts = Counter(str(row.get("executable_next_action")) for row in rows)
    return {
        "unified_system_work_order_surface": UNIFIED_SYSTEM_WORK_ORDER_SURFACE,
        "work_order_rollup_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-WORKORDER-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "work_order_rows": len(rows),
        "work_order_family_counts": {key: int(family_counts[key]) for key in sorted(family_counts)},
        "executable_next_action_counts": {key: int(action_counts[key]) for key in sorted(action_counts)},
        "summary_only_terminal": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }
