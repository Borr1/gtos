"""Unify branch-local module, guard, market-gap, and no-fill recommendation rows."""

from __future__ import annotations

from typing import Any


UNIFIED_SYSTEM_RECOMMENDATION_SURFACE = (
    "src/research_infra/moonshot_branch_local_unified_system_recommendation_merge.py"
)


ID_FIELDS = (
    "exact_control_redesign_registry_scorer_module_row_id",
    "system_recommendation_row_id",
    "default_off_application_row_id",
    "scorer_application_row_id",
    "bundle_row_id",
    "market_gap_code_id",
    "family_synthesis_id",
    "avoid_filter_branch_id",
    "retest_redesign_branch_id",
    "source_confidence_branch_id",
    "near_miss_entry_control_offset_branch_id",
    "near_miss_entry_control_market_branch_id",
    "near_miss_entry_control_source_requirement_id",
)


def mechanical_scope_key(row: dict[str, Any]) -> str:
    existing = row.get("mechanical_scope_key")
    if existing:
        return str(existing)
    symbol = row.get("symbol")
    session = row.get("route_session") or row.get("session_bucket")
    horizon = row.get("horizon_id")
    primitive = row.get("primitive_flag")
    family_key = row.get("family_key")
    if symbol or session or horizon or primitive:
        return f"symbol={symbol}|session={session}|horizon={horizon}|primitive={primitive}"
    if family_key:
        return f"family_key={family_key}"
    return "scope_unavailable_preserve_source_row"


def source_row_id(row: dict[str, Any]) -> Any:
    for field in ID_FIELDS:
        if row.get(field):
            return row.get(field)
    return row.get("input_row_id") or row.get("event_id") or row.get("source_row_sequence")


def _common(source_component: str, row: dict[str, Any]) -> dict[str, Any]:
    return {
        "unified_system_recommendation_surface": UNIFIED_SYSTEM_RECOMMENDATION_SURFACE,
        "source_component": source_component,
        "source_row_id": source_row_id(row),
        "mechanical_scope_key": mechanical_scope_key(row),
        "symbol": row.get("symbol"),
        "route_session": row.get("route_session") or row.get("session_bucket"),
        "horizon_id": row.get("horizon_id"),
        "primitive_flag": row.get("primitive_flag"),
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "candidate_use_allowed_now": False,
        "live_effect": False,
    }


def _status_text(row: dict[str, Any]) -> str:
    keys = (
        "system_recommendation_status",
        "module_registration_status",
        "default_off_application_status",
        "scorer_application_status",
        "bundle_decision",
        "bundle_stage",
        "code_candidate_status",
        "market_gap_replay_decision",
        "evidence_class",
        "denominator_scope",
        "market_branch_join_status",
        "offset_branch_join_status",
        "source_requirement_status",
    )
    return "|".join(str(row.get(key) or "") for key in keys)


def _classify(source_component: str, row: dict[str, Any]) -> tuple[str, str, str, str]:
    text = _status_text(row)
    if source_component in {"registry_scorer_module", "registry_scorer_module_system"}:
        return (
            "IMPLEMENT_DEFAULT_OFF_MODULE_CANDIDATE",
            "KEEP_AS_BRANCH_LOCAL_DEFAULT_OFF_MODULE",
            "IMPLEMENT",
            "module_candidate_ready_default_off",
        )
    if source_component == "default_off_application":
        if "SCORE_READY" in text or "SCORE_EMITTED" in text:
            return (
                "IMPLEMENT_DEFAULT_OFF_SCORER_CANDIDATE",
                "KEEP_AS_BRANCH_LOCAL_DEFAULT_OFF_SCORER",
                "IMPLEMENT",
                "default_off_score_available_guarded",
            )
        if "CURRENT_CLAIM_REJECTED" in text:
            return (
                "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED",
                "PRESERVE_AS_AUDIT_REDESIGN_OR_AVOID_INPUT",
                "PRESERVE_AUDIT",
                "current_claim_rejected_underlying_mechanism_preserved",
            )
        if "EXACT" in text:
            return (
                "BUILD_EXACT_CONTROL_DENOMINATOR",
                "REDESIGN_BY_EXACT_CONTROL_DENOMINATOR_BUILD",
                "SOURCE_OR_CONTROL_REPAIR",
                "exact_control_required_before_runtime_score",
            )
        return (
            "RECHECK_DEFAULT_OFF_APPLICATION_ROW",
            "PRESERVE_FOR_RECHECK",
            "RECHECK",
            "default_off_application_requires_recheck",
        )
    if source_component == "default_off_scorer_application":
        return (
            "SCORE_WITH_DEFAULT_OFF_CONTROL_CONTEXT",
            "KEEP_AS_DEFAULT_OFF_SCORER_OBSERVATION",
            "SCORE_WITH_CONTROL",
            "default_off_scorer_application_observation",
        )
    if source_component == "shadow_source_guard":
        if "IMPLEMENT_ENABLE" in text or "ENABLE_" in text:
            return (
                "ENABLE_SHADOW_RULE_WITH_SOURCE_GUARD",
                "IMPLEMENT_BRANCH_LOCAL_SHADOW_RULE_DEFAULT_OFF",
                "IMPLEMENT",
                "source_guarded_shadow_rule_ready",
            )
        if "SOURCE_GUARD" in text or "SOURCE" in text:
            return (
                "SOURCE_GUARD_OR_REPAIR_REQUIRED",
                "REDESIGN_BY_SOURCE_GUARD_OR_MATERIALIZATION",
                "SOURCE_OR_CONTROL_REPAIR",
                "source_guard_required",
            )
        if "DENOMINATOR" in text:
            return (
                "DENOMINATOR_GUARD_REQUIRED",
                "KEEP_AS_DENOMINATOR_GUARD",
                "GUARD",
                "denominator_guard_required",
            )
        if "HORIZON" in text:
            return (
                "HORIZON_REPAIR_OR_REDESIGN_REQUIRED",
                "REDESIGN_BY_HORIZON_REPAIR",
                "REDESIGN",
                "horizon_repair_required",
            )
        return (
            "SCORE_WITH_CONTROL_REQUIRED",
            "KEEP_AS_SCORE_CONTROL_BUNDLE",
            "SCORE_WITH_CONTROL",
            "source_guard_bundle_control_context",
        )
    if source_component == "market_gap_code":
        if "SOURCE_MATERIALIZATION_REQUIRED" in text or "SOURCE_ACQUISITION" in text:
            return (
                "MARKET_GAP_SOURCE_MATERIALIZATION_REQUIRED",
                "REDESIGN_BY_SOURCE_MATERIALIZATION_THEN_RESCORE",
                "SOURCE_OR_CONTROL_REPAIR",
                "market_gap_source_materialization_required",
            )
        if "IMPLEMENT_ENTRY" in text:
            return (
                "MARKET_GAP_ENTRY_GEOMETRY_IMPLEMENT_CANDIDATE",
                "IMPLEMENT_MARKET_GAP_ENTRY_GEOMETRY_DEFAULT_OFF",
                "IMPLEMENT",
                "market_gap_entry_geometry_candidate",
            )
        if "IMPLEMENT_AVOID" in text:
            return (
                "MARKET_GAP_AVOID_FILTER_IMPLEMENT_CANDIDATE",
                "IMPLEMENT_MARKET_GAP_AVOID_FILTER_DEFAULT_OFF",
                "IMPLEMENT",
                "market_gap_avoid_filter_candidate",
            )
        return (
            "MARKET_GAP_SCORE_WITH_CONTROL_REQUIRED",
            "KEEP_AS_MARKET_GAP_CONTROL_SCORING_CANDIDATE",
            "SCORE_WITH_CONTROL",
            "market_gap_control_score_required",
        )
    if source_component == "nofill_far_miss_family":
        return (
            "NOFILL_FAR_MISS_FAMILY_REDESIGN_SYNTHESIS",
            "REDESIGN_OR_SPLIT_BY_NOFILL_FAMILY_CONTEXT",
            "REDESIGN",
            "nofill_family_synthesis_preserved",
        )
    if source_component == "nofill_far_miss_avoid":
        return (
            "NOFILL_FAR_MISS_AVOID_FILTER_CANDIDATE",
            "IMPLEMENT_OR_SCORE_NOFILL_AVOID_FILTER_DEFAULT_OFF",
            "REDESIGN",
            "nofill_avoid_filter_candidate",
        )
    if source_component == "nofill_far_miss_retest":
        return (
            "NOFILL_FAR_MISS_RETEST_REDESIGN_CANDIDATE",
            "REDESIGN_RETEST_ENTRY_GEOMETRY_OR_HORIZON",
            "REDESIGN",
            "nofill_retest_redesign_candidate",
        )
    if source_component == "nofill_far_miss_source_confidence":
        return (
            "NOFILL_SOURCE_CONFIDENCE_CONTEXT_CANDIDATE",
            "KEEP_AS_SOURCE_CONFIDENCE_FEATURE_OR_GUARD",
            "GUARD",
            "nofill_source_confidence_candidate",
        )
    if source_component == "nofill_near_miss_offset":
        return (
            "NOFILL_NEAR_MISS_ENTRY_OFFSET_VARIANT",
            "REDESIGN_ENTRY_OFFSET_GEOMETRY",
            "REDESIGN",
            "near_miss_offset_candidate",
        )
    if source_component == "nofill_near_miss_market_entry":
        return (
            "NOFILL_NEAR_MISS_MARKET_ENTRY_VARIANT",
            "REDESIGN_OR_SCORE_MARKET_ENTRY_PROXY",
            "REDESIGN",
            "near_miss_market_entry_candidate",
        )
    if source_component == "nofill_near_miss_source_requirement":
        return (
            "NOFILL_NEAR_MISS_SOURCE_REQUIREMENT",
            "REPAIR_SOURCE_BEFORE_ENTRY_VARIANT_DECISION",
            "SOURCE_OR_CONTROL_REPAIR",
            "near_miss_source_requirement",
        )
    return (
        "UNIFIED_SYSTEM_RECOMMENDATION_RECHECK_SOURCE_ROW",
        "PRESERVE_FOR_RECHECK",
        "RECHECK",
        "unclassified_source_row_preserved",
    )


def unified_system_candidate(
    source_component: str,
    row: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    action_class, decision, decision_group, cause = _classify(source_component, row)
    return {
        **_common(source_component, row),
        "unified_system_candidate_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-SYSTEM-CANDIDATE-{index:06d}",
        "unified_action_class": action_class,
        "unified_system_decision": decision,
        "unified_decision_group": decision_group,
        "success_or_failure_cause": cause,
        "implementation_implication": row.get("implementation_implication")
        or row.get("bundle_decision")
        or row.get("code_candidate_action")
        or row.get("system_recommendation_action")
        or row.get("default_off_application_decision_class")
        or action_class,
        "source_status": (
            row.get("system_recommendation_status")
            or row.get("module_registration_status")
            or row.get("default_off_application_status")
            or row.get("scorer_application_status")
            or row.get("bundle_decision")
            or row.get("code_candidate_status")
            or row.get("evidence_class")
        ),
        "proxy_or_module_score": row.get("proxy_score")
        or row.get("default_off_application_score")
        or row.get("default_off_scorer_score")
        or row.get("bundle_priority_score")
        or row.get("alignment_delta_mean")
        or row.get("signal_alignment_rate"),
        "source_confidence_status": row.get("source_confidence_status")
        or row.get("source_guard_requirement")
        or row.get("source_requirement_status"),
        "outside_gbpjpy_xauusd_current_branch_box": row.get("outside_gbpjpy_xauusd_current_branch_box"),
        "missed_opportunity_preserved": True,
        "current_claim_only_rejection_scope": (
            "CURRENT_CLAIM_ONLY_UNDERLYING_MECHANISM_PRESERVED"
            if action_class == "CURRENT_CLAIM_REJECTED_MECHANISM_PRESERVED"
            else None
        ),
    }


def rollup_row(group_key: tuple[Any, ...], rows: list[dict[str, Any]], index: int, rollup_type: str) -> dict[str, Any]:
    decision_groups = sorted({str(row.get("unified_decision_group")) for row in rows})
    action_classes = sorted({str(row.get("unified_action_class")) for row in rows})
    return {
        "unified_system_recommendation_surface": UNIFIED_SYSTEM_RECOMMENDATION_SURFACE,
        "unified_system_rollup_row_id": f"OHLC-GTOS-MOONSHOT-UNIFIED-SYSTEM-ROLLUP-{index:05d}",
        "rollup_type": rollup_type,
        "rollup_key": "|".join(str(part) for part in group_key),
        "candidate_rows": len(rows),
        "decision_groups": decision_groups,
        "action_classes": action_classes,
        "implement_rows": sum(1 for row in rows if row.get("unified_decision_group") == "IMPLEMENT"),
        "redesign_rows": sum(1 for row in rows if row.get("unified_decision_group") == "REDESIGN"),
        "score_with_control_rows": sum(1 for row in rows if row.get("unified_decision_group") == "SCORE_WITH_CONTROL"),
        "source_or_control_repair_rows": sum(
            1 for row in rows if row.get("unified_decision_group") == "SOURCE_OR_CONTROL_REPAIR"
        ),
        "guard_rows": sum(1 for row in rows if row.get("unified_decision_group") == "GUARD"),
        "preserve_audit_rows": sum(1 for row in rows if row.get("unified_decision_group") == "PRESERVE_AUDIT"),
        "candidate_use_allowed_now": False,
        "runtime_score_allowed": False,
        "unconditional_scalar_use_allowed": False,
        "live_effect": False,
    }
