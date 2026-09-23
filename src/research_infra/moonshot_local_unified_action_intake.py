"""Normalize moonshot branch-local computed actions for main integration.

This module is intentionally research/tooling-only. It converts the moonshot
computed-action bundle into compact main-side decision rows without changing
live behavior or claiming broker-realized R.
"""

from __future__ import annotations

import math
from collections import Counter
from typing import Any


MAIN_DECISION_BY_FAMILY = {
    "DEFAULT_OFF_CODE_CANDIDATE": "IMPLEMENT_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD_NO_LIVE_EFFECT",
    "GUARD_REGISTRY_SPEC": "REGISTER_DEFAULT_OFF_GUARD_SPEC_FOR_SOURCE_CONFIDENCE_OR_DENOMINATOR",
    "NOFILL_REDESIGN_SCORING": "MATERIALIZE_NOFILL_REDESIGN_SCORE_FOR_REPLAY_OR_DEFAULT_OFF_VARIANT",
    "SOURCE_CONTROL_REPAIR": "BUILD_SOURCE_OR_CONTROL_DENOMINATOR_BEFORE_SCORING",
    "SCORE_WITH_CONTROL": "KEEP_CONTROLLED_SCORE_DELTA_FOR_RESEARCH_COMPARISON",
    "CURRENT_CLAIM_OPPORTUNITY_AUDIT": "REJECT_CURRENT_CLAIM_ONLY_PRESERVE_OPPORTUNITY",
    "RECHECK": "RECHECK_HORIZON_SOURCE_TARGETABILITY_BEFORE_DECISION",
}

MAIN_ACTION_CLASS_BY_FAMILY = {
    "DEFAULT_OFF_CODE_CANDIDATE": "IMPLEMENTATION_CANDIDATE",
    "GUARD_REGISTRY_SPEC": "GUARD_SPEC",
    "NOFILL_REDESIGN_SCORING": "REDESIGN_SCORE",
    "SOURCE_CONTROL_REPAIR": "SOURCE_REPAIR",
    "SCORE_WITH_CONTROL": "CONTROL_SCORE",
    "CURRENT_CLAIM_OPPORTUNITY_AUDIT": "CURRENT_CLAIM_REJECTION",
    "RECHECK": "RECHECK",
}


def safe_float(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def main_decision_for_row(row: dict[str, Any]) -> dict[str, Any]:
    family = str(row.get("computed_action_family") or "")
    decision = MAIN_DECISION_BY_FAMILY.get(family, "UNCLASSIFIED_COMPUTED_ACTION_FAMILY")
    action_class = MAIN_ACTION_CLASS_BY_FAMILY.get(family, "UNCLASSIFIED")
    proxy_delta = safe_float(row.get("computed_proxy_delta"))
    candidate_allowed_now = row.get("candidate_use_allowed_now") is True
    live_effect = row.get("live_effect") is True
    if candidate_allowed_now or live_effect:
        safety_state = "UNEXPECTED_LIVE_OR_RUNTIME_USE_FLAG_REVIEW_REQUIRED"
    else:
        safety_state = "RESEARCH_ONLY_DEFAULT_OFF_NO_LIVE_EFFECT"

    if family == "DEFAULT_OFF_CODE_CANDIDATE":
        downstream = [
            "default-off implementation candidate",
            "source guard",
            "control lookup",
            "forward shadow",
        ]
    elif family == "GUARD_REGISTRY_SPEC":
        downstream = ["guard registry", "source confidence", "denominator control"]
    elif family == "NOFILL_REDESIGN_SCORING":
        downstream = ["entry redesign", "avoid/inverse", "retest scoring", "forward shadow"]
    elif family == "SOURCE_CONTROL_REPAIR":
        downstream = ["source repair", "exact control denominator", "rescore"]
    elif family == "SCORE_WITH_CONTROL":
        downstream = ["control comparison", "denominator guard", "source repair if missing"]
    elif family == "CURRENT_CLAIM_OPPORTUNITY_AUDIT":
        downstream = ["current claim rejection", "missed opportunity preservation", "redesign"]
    elif family == "RECHECK":
        downstream = ["source recheck", "targetability repair", "redesign"]
    else:
        downstream = ["manual review"]

    return {
        "main_action_class": action_class,
        "main_decision": decision,
        "main_safety_state": safety_state,
        "proxy_delta_numeric": proxy_delta,
        "proxy_delta_counted_as_r": False,
        "downstream_paths": downstream,
    }


def compact_intake_row(
    row: dict[str, Any],
    *,
    intake_row_id: str,
    source_artifact: str,
    source_line_no: int,
    source_sha256: str,
) -> dict[str, Any]:
    decision = main_decision_for_row(row)
    keys = [
        "computed_action_family",
        "computed_action_status",
        "computed_decision",
        "computed_next_action",
        "computed_proxy_delta",
        "computed_proxy_delta_class",
        "computed_proxy_score",
        "computed_proxy_score_basis",
        "expectancy_style_proxy_delta",
        "pass_control_delta_proxy",
        "source_component",
        "action_result_family",
        "action_execution_status",
        "implementation_implication",
        "market_expansion_decision",
        "mechanical_scope_key",
        "symbol",
        "route_session",
        "horizon_id",
        "primitive_flag",
        "target_stop_result",
        "entry_variant",
        "fillability_no_fill_status",
        "candidate_use_allowed_now",
        "runtime_score_allowed",
        "live_effect",
        "input_unified_system_action_result_row_id",
        "input_unified_system_work_order_row_id",
        "market_expansion_row_id",
        "missed_opportunity_preserved",
        "not_completion",
    ]
    compact = {key: row.get(key) for key in keys if key in row}
    compact.update(decision)
    compact["intake_row_id"] = intake_row_id
    compact["source_artifact"] = source_artifact
    compact["source_line_no"] = source_line_no
    compact["source_sha256"] = source_sha256
    compact["safe_flags"] = {
        "NO_PROMOTION_VERDICT": True,
        "validation_safe": False,
        "outcome_review_opened": False,
        "live_effect": False,
    }
    compact["no_live_behavior"] = True
    compact["no_shadow_log_append"] = True
    return compact


def summarize_intake(rows: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_deltas = [
        value for row in rows if (value := safe_float(row.get("computed_proxy_delta"))) is not None
    ]
    default_off = [row for row in rows if row.get("computed_action_family") == "DEFAULT_OFF_CODE_CANDIDATE"]
    return {
        "rows": len(rows),
        "main_action_class_counts": dict(sorted(Counter(str(row.get("main_action_class")) for row in rows).items())),
        "main_decision_counts": dict(sorted(Counter(str(row.get("main_decision")) for row in rows).items())),
        "computed_action_family_counts": dict(
            sorted(Counter(str(row.get("computed_action_family")) for row in rows).items())
        ),
        "computed_action_status_counts": dict(
            sorted(Counter(str(row.get("computed_action_status")) for row in rows).items())
        ),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "market_expansion_decision_counts": dict(
            sorted(Counter(str(row.get("market_expansion_decision")) for row in rows).items())
        ),
        "numeric_proxy_delta_rows": len(numeric_deltas),
        "numeric_proxy_delta_sum_not_r": round(sum(numeric_deltas), 8),
        "default_off_code_candidate_rows": len(default_off),
        "default_off_proxy_delta_class_counts": dict(
            sorted(Counter(str(row.get("computed_proxy_delta_class")) for row in default_off).items())
        ),
        "candidate_use_allowed_now_true_rows": sum(row.get("candidate_use_allowed_now") is True for row in rows),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "proxy_delta_counted_as_r_rows": sum(row.get("proxy_delta_counted_as_r") is True for row in rows),
    }


def implementation_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a generic moonshot implementation candidate into an actionable route."""
    source_component = str(row.get("source_component") or "")
    computed_decision = str(row.get("computed_decision") or "")
    implication = str(row.get("implementation_implication") or "")
    proxy_delta = safe_float(row.get("computed_proxy_delta"))

    if source_component == "shadow_source_guard" and computed_decision == "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD":
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        selection_decision = "IMPLEMENT_DEFAULT_OFF_SHADOW_SOURCE_GUARD_RULE"
        downstream = "shadow_source_guard_rule"
        reason = "Source-guarded shadow rule candidate with positive proxy-delta evidence."
    elif source_component == "market_gap_code" and computed_decision == "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD":
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        if "avoid" in implication.lower() or "inverse" in implication.lower():
            selection_decision = "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_AVOID_OR_INVERSE_SPEC"
            downstream = "avoid_inverse"
        else:
            selection_decision = "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_ENTRY_GEOMETRY_SPEC"
            downstream = "entry_geometry"
        reason = "Market-gap entry/avoid spec already carries source rows and positive proxy-delta evidence."
    elif (
        source_component == "registry_scorer_module"
        and computed_decision == "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD"
        and (proxy_delta or 0.0) > 0.0
    ):
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        selection_decision = "IMPLEMENT_DEFAULT_OFF_REGISTRY_SCORER_MODULE"
        downstream = "scorer_module"
        reason = "Registry scorer module has source guard and positive proxy-delta evidence."
    elif source_component == "default_off_application" and computed_decision == "KEEP_DEFAULT_OFF_CODE_CANDIDATE_WITH_SOURCE_GUARD":
        selection_class = "SOURCE_REPAIR"
        selection_decision = "SOURCE_REPAIR_BEFORE_DEFAULT_OFF_APPLICATION_SCORER"
        downstream = "source_requirement"
        reason = "Positive application candidate still names an exact-build/source-control boundary before scoring."
    elif source_component == "registry_scorer_module_system":
        selection_class = "REDESIGN"
        selection_decision = "REDESIGN_SYSTEM_MODULE_SCALAR_CLAIM_PRESERVE_CONTEXT"
        downstream = "context_feature"
        reason = "Negative system-module scalar evidence rejects only the current scalar claim; module family remains context."
    elif source_component == "registry_scorer_module":
        selection_class = "REDESIGN"
        selection_decision = "REDESIGN_REGISTRY_SCORER_MODULE_CONTROL_OR_SCOPE"
        downstream = "redesign"
        reason = "Neutral/weak registry scorer evidence needs control or scope repair before implementation."
    elif source_component == "default_off_application":
        selection_class = "REDESIGN"
        selection_decision = "REDESIGN_DEFAULT_OFF_APPLICATION_TARGET_OR_HORIZON"
        downstream = "tighter_target_or_shorter_horizon"
        reason = "Default-off application evidence is neutral/negative; preserve mechanism as target/horizon redesign."
    else:
        selection_class = "UNCLASSIFIED"
        selection_decision = "UNCLASSIFIED_MOONSHOT_IMPLEMENTATION_CANDIDATE"
        downstream = "manual_review"
        reason = "No executable selection rule matched this candidate."

    return {
        "selection_class": selection_class,
        "selection_decision": selection_decision,
        "selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_implementation_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(implementation_selection_for_row(row))
    return selected


def summarize_implementation_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "selection_class_counts": dict(sorted(Counter(str(row.get("selection_class")) for row in rows).items())),
        "selection_decision_counts": dict(sorted(Counter(str(row.get("selection_decision")) for row in rows).items())),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "implementation_implication_counts": dict(
            sorted(Counter(str(row.get("implementation_implication")) for row in rows).items())
        ),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }


def guard_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a generic guard spec into an explicit source-completeness action."""
    source_component = str(row.get("source_component") or "")
    market_decision = str(row.get("market_expansion_decision") or "")
    proxy_delta = safe_float(row.get("proxy_delta_numeric", row.get("computed_proxy_delta")))

    if source_component == "nofill_far_miss_source_confidence":
        guard_class = "SOURCE_CONFIDENCE_GUARD"
        guard_decision = "REGISTER_NOFILL_FAR_MISS_SOURCE_CONFIDENCE_GUARD_DEFAULT_OFF"
        downstream = "nofill_source_confidence_guard"
        reason = "No-fill far-miss rows require a source-confidence guard before any retest/avoid scoring."
    elif source_component == "shadow_source_guard" and market_decision == "source-repair":
        guard_class = "SOURCE_REPAIR"
        guard_decision = "REPAIR_SCOPE_BEFORE_DENOMINATOR_OR_SOURCE_CONFIDENCE_GUARD"
        downstream = "source_requirement"
        reason = "Scope is unavailable; repair source ownership before registering the guard."
    elif source_component == "shadow_source_guard" and (proxy_delta or 0.0) < 0.0:
        guard_class = "DENOMINATOR_GUARD_ADVERSE_CONTEXT"
        guard_decision = "REGISTER_DENOMINATOR_GUARD_ADVERSE_CONTEXT_DEFAULT_OFF"
        downstream = "avoid_or_context_guard"
        reason = "Negative proxy context becomes an adverse-context guard, not a mechanism kill."
    elif source_component == "shadow_source_guard":
        guard_class = "DENOMINATOR_GUARD"
        guard_decision = "REGISTER_DENOMINATOR_GUARD_POSITIVE_CONTEXT_DEFAULT_OFF"
        downstream = "denominator_guard"
        reason = "Positive proxy context becomes a default-off denominator/source guard."
    else:
        guard_class = "UNCLASSIFIED"
        guard_decision = "UNCLASSIFIED_MOONSHOT_GUARD_SPEC"
        downstream = "manual_review"
        reason = "No executable guard-selection rule matched this spec."

    return {
        "guard_selection_class": guard_class,
        "guard_selection_decision": guard_decision,
        "guard_selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "source_completeness_action": True,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_guard_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(guard_selection_for_row(row))
    return selected


def summarize_guard_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "guard_selection_class_counts": dict(
            sorted(Counter(str(row.get("guard_selection_class")) for row in rows).items())
        ),
        "guard_selection_decision_counts": dict(
            sorted(Counter(str(row.get("guard_selection_decision")) for row in rows).items())
        ),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "source_completeness_action_rows": sum(row.get("source_completeness_action") is True for row in rows),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }


def nofill_redesign_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert no-fill redesign proxy scores into implementation/redesign actions."""
    source_component = str(row.get("source_component") or "")
    proxy_class = str(row.get("computed_proxy_delta_class") or "")
    proxy_delta = safe_float(row.get("proxy_delta_numeric", row.get("computed_proxy_delta")))

    if proxy_class == "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED":
        selection_class = "SOURCE_REPAIR"
        if source_component == "nofill_near_miss_market_entry":
            selection_decision = "SOURCE_REPAIR_NEAR_MISS_MARKET_ENTRY_CONTROL_REQUIRED"
            downstream = "source_requirement"
        elif source_component == "nofill_near_miss_offset":
            selection_decision = "SOURCE_REPAIR_NEAR_MISS_OFFSET_CONTROL_REQUIRED"
            downstream = "source_requirement"
        else:
            selection_decision = "SOURCE_REPAIR_NOFILL_REDESIGN_CONTROL_REQUIRED"
            downstream = "source_requirement"
        reason = "Proxy delta is unavailable; source/control denominator must be repaired before scoring."
    elif proxy_class == "COMPUTED_PROXY_DELTA_STRONG_POSITIVE":
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        if source_component == "nofill_far_miss_retest":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_FAR_MISS_RETEST_REDESIGN_VARIANT"
            downstream = "retest_redesign"
        elif source_component == "nofill_far_miss_family":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_NOFILL_FAMILY_SPLIT_VARIANT"
            downstream = "family_split"
        elif source_component == "nofill_near_miss_market_entry":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_NEAR_MISS_MARKET_ENTRY_VARIANT"
            downstream = "market_entry_variant"
        elif source_component == "nofill_near_miss_offset":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_NEAR_MISS_OFFSET_ENTRY_VARIANT"
            downstream = "offset_entry_variant"
        else:
            selection_decision = "IMPLEMENT_DEFAULT_OFF_NOFILL_REDESIGN_VARIANT"
            downstream = "entry_redesign"
        reason = "Strong-positive proxy delta supports a default-off no-fill redesign candidate."
    else:
        selection_class = "REDESIGN"
        if source_component == "nofill_far_miss_avoid":
            selection_decision = "REDESIGN_AVOID_INVERSE_VARIANT_CURRENT_PROXY_NEGATIVE"
            downstream = "avoid_inverse_redesign"
            reason = "Current avoid/inverse variant proxy is negative; preserve the failure-control mechanism for redesign."
        elif source_component == "nofill_far_miss_retest":
            selection_decision = "REDESIGN_FAR_MISS_RETEST_VARIANT_PROXY_NOT_POSITIVE"
            downstream = "retest_redesign"
            reason = "Current far-miss retest variant is neutral or adverse; preserve as retest redesign/control evidence."
        elif source_component == "nofill_far_miss_family":
            selection_decision = "REDESIGN_NOFILL_FAMILY_SPLIT_SCOPE_OR_SOURCE_CONFIDENCE"
            downstream = "family_split_redesign"
            reason = "Family split evidence is neutral/adverse; preserve symbol/session/miss-cause intelligence."
        elif source_component == "nofill_near_miss_market_entry":
            selection_decision = "REDESIGN_NEAR_MISS_MARKET_ENTRY_VARIANT_PROXY_NEGATIVE"
            downstream = "market_entry_redesign"
            reason = "Near-miss market-entry proxy is adverse; preserve for tighter target, context, or avoid control."
        elif source_component == "nofill_near_miss_offset":
            selection_decision = "REDESIGN_NEAR_MISS_OFFSET_ENTRY_VARIANT_PROXY_NEGATIVE"
            downstream = "offset_entry_redesign"
            reason = "Near-miss offset-entry proxy is adverse; preserve for tighter target or shorter-horizon redesign."
        else:
            selection_decision = "REDESIGN_NOFILL_VARIANT_PROXY_NOT_POSITIVE"
            downstream = "entry_redesign"
            reason = "Current no-fill redesign proxy is not positive; preserve mechanism for redesign."

    return {
        "nofill_selection_class": selection_class,
        "nofill_selection_decision": selection_decision,
        "nofill_selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_nofill_redesign_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(nofill_redesign_selection_for_row(row))
    return selected


def summarize_nofill_redesign_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "nofill_selection_class_counts": dict(
            sorted(Counter(str(row.get("nofill_selection_class")) for row in rows).items())
        ),
        "nofill_selection_decision_counts": dict(
            sorted(Counter(str(row.get("nofill_selection_decision")) for row in rows).items())
        ),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(str(row.get("route_session")) for row in rows).items())),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }


def source_control_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Route source/control repair rows into concrete source, implementation, or redesign actions."""
    source_component = str(row.get("source_component") or "")
    proxy_class = str(row.get("computed_proxy_delta_class") or "")
    proxy_delta = safe_float(row.get("proxy_delta_numeric", row.get("computed_proxy_delta")))

    if proxy_class == "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED":
        selection_class = "SOURCE_REPAIR"
        if source_component == "default_off_application":
            selection_decision = "SOURCE_REPAIR_DEFAULT_OFF_APPLICATION_EXACT_CONTROL_DENOMINATOR"
            downstream = "exact_control_denominator"
            reason = "Default-off application row has no computable proxy delta until exact control denominator exists."
        elif source_component == "nofill_near_miss_source_requirement":
            selection_decision = "SOURCE_REPAIR_NOFILL_NEAR_MISS_ATTACH_SATISFIED_SOURCE"
            downstream = "entry_replay_source_attachment"
            reason = "Near-miss no-fill row needs satisfied source/control attachment before the entry variant can be scored."
        else:
            selection_decision = "SOURCE_REPAIR_CONTROL_DENOMINATOR_REQUIRED"
            downstream = "source_control_repair"
            reason = "Source/control denominator is unavailable and must be repaired before scoring."
    elif proxy_class in {"COMPUTED_PROXY_DELTA_POSITIVE", "COMPUTED_PROXY_DELTA_STRONG_POSITIVE"}:
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        if source_component == "shadow_source_guard":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_SHADOW_SOURCE_GUARD_SCOPE_PROXY"
            downstream = "source_guard_scope_candidate"
        elif source_component == "market_gap_code":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_MARKET_GAP_CODE_CONTROL_PROXY"
            downstream = "market_gap_control_candidate"
        else:
            selection_decision = "IMPLEMENT_DEFAULT_OFF_SOURCE_CONTROL_PROXY"
            downstream = "source_control_candidate"
        reason = "Positive branch proxy supports a default-off source/control candidate with scope guard."
    else:
        selection_class = "REDESIGN"
        if source_component == "shadow_source_guard" and proxy_class == "COMPUTED_PROXY_DELTA_NEUTRAL":
            selection_decision = "REDESIGN_SHADOW_SOURCE_GUARD_NEUTRAL_SOURCE_SCOPE"
            downstream = "source_guard_scope_redesign"
            reason = "Neutral source-guard proxy is not independently countable; preserve scope information for redesign."
        elif source_component == "market_gap_code" and proxy_class == "COMPUTED_PROXY_DELTA_NEUTRAL":
            selection_decision = "REDESIGN_MARKET_GAP_CODE_NEUTRAL_CONTROL_SCOPE"
            downstream = "market_gap_control_redesign"
            reason = "Neutral market-gap proxy is not independently countable; preserve control-scope information."
        elif source_component == "shadow_source_guard":
            selection_decision = "REDESIGN_SHADOW_SOURCE_GUARD_ADVERSE_AVOID_CONTEXT"
            downstream = "source_guard_avoid_context"
            reason = "Adverse source-guard proxy rejects only the current scalar claim and preserves avoid/context intelligence."
        elif source_component == "market_gap_code":
            selection_decision = "REDESIGN_MARKET_GAP_CODE_ADVERSE_AVOID_CONTEXT"
            downstream = "market_gap_avoid_context"
            reason = "Adverse market-gap proxy rejects only the current scalar claim and preserves avoid/context intelligence."
        else:
            selection_decision = "REDESIGN_SOURCE_CONTROL_PROXY_NOT_POSITIVE"
            downstream = "source_control_redesign"
            reason = "Current source/control proxy is not positive; preserve mechanism for redesign."

    return {
        "source_control_selection_class": selection_class,
        "source_control_selection_decision": selection_decision,
        "source_control_selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_source_control_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(source_control_selection_for_row(row))
    return selected


def summarize_source_control_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "source_control_selection_class_counts": dict(
            sorted(Counter(str(row.get("source_control_selection_class")) for row in rows).items())
        ),
        "source_control_selection_decision_counts": dict(
            sorted(Counter(str(row.get("source_control_selection_decision")) for row in rows).items())
        ),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(str(row.get("route_session")) for row in rows).items())),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }


def control_score_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Route controlled score deltas into candidates, redesigns, or exact-denominator repairs."""
    source_component = str(row.get("source_component") or "")
    proxy_class = str(row.get("computed_proxy_delta_class") or "")
    proxy_delta = safe_float(row.get("proxy_delta_numeric", row.get("computed_proxy_delta")))

    if proxy_class == "COMPUTED_DELTA_NOT_AVAILABLE_SOURCE_OR_CONTROL_REQUIRED":
        selection_class = "SOURCE_REPAIR"
        selection_decision = "SOURCE_REPAIR_CONTROL_SCORE_EXACT_DENOMINATOR_REQUIRED"
        downstream = "exact_control_denominator"
        reason = "Controlled score delta is unavailable until exact source/control denominator is reconstructed."
    elif proxy_class in {"COMPUTED_PROXY_DELTA_POSITIVE", "COMPUTED_PROXY_DELTA_STRONG_POSITIVE"}:
        selection_class = "IMPLEMENT_DEFAULT_OFF"
        if source_component == "default_off_scorer_application":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_SCORER_APPLICATION"
            downstream = "default_off_scorer_application_candidate"
        elif source_component == "market_gap_code":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_MARKET_GAP"
            downstream = "market_gap_control_candidate"
        elif source_component == "shadow_source_guard":
            selection_decision = "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_SOURCE_GUARD"
            downstream = "source_guard_control_candidate"
        else:
            selection_decision = "IMPLEMENT_DEFAULT_OFF_CONTROL_SCORE_VARIANT"
            downstream = "control_score_candidate"
        reason = "Positive controlled score delta supports a default-off candidate with exact-scope guard."
    else:
        selection_class = "REDESIGN"
        if source_component == "default_off_scorer_application":
            selection_decision = "REDESIGN_CONTROL_SCORE_SCORER_APPLICATION_NOT_POSITIVE"
            downstream = "scorer_application_redesign"
        elif source_component == "market_gap_code":
            selection_decision = "REDESIGN_CONTROL_SCORE_MARKET_GAP_NOT_POSITIVE"
            downstream = "market_gap_context_redesign"
        elif source_component == "shadow_source_guard":
            selection_decision = "REDESIGN_CONTROL_SCORE_SOURCE_GUARD_NOT_POSITIVE"
            downstream = "source_guard_context_redesign"
        else:
            selection_decision = "REDESIGN_CONTROL_SCORE_NOT_POSITIVE"
            downstream = "control_score_redesign"
        reason = "Controlled score delta is neutral or adverse; preserve comparison as context/redesign evidence."

    return {
        "control_score_selection_class": selection_class,
        "control_score_selection_decision": selection_decision,
        "control_score_selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_control_score_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(control_score_selection_for_row(row))
    return selected


def summarize_control_score_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "control_score_selection_class_counts": dict(
            sorted(Counter(str(row.get("control_score_selection_class")) for row in rows).items())
        ),
        "control_score_selection_decision_counts": dict(
            sorted(Counter(str(row.get("control_score_selection_decision")) for row in rows).items())
        ),
        "source_component_counts": dict(sorted(Counter(str(row.get("source_component")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(str(row.get("route_session")) for row in rows).items())),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }


def claim_audit_selection_for_row(row: dict[str, Any]) -> dict[str, Any]:
    """Preserve current-claim rejection and recheck rows as explicit branch decisions."""
    main_action_class = str(row.get("main_action_class") or "")
    implication = str(row.get("implementation_implication") or "")
    proxy_delta = safe_float(row.get("proxy_delta_numeric", row.get("computed_proxy_delta")))

    if main_action_class == "RECHECK":
        selection_class = "SOURCE_REPAIR"
        selection_decision = "RECHECK_REPAIR_HORIZON_TARGETABILITY_BEFORE_DECISION"
        downstream = "horizon_targetability_source_recheck"
        reason = "Horizon targetability must be repaired before the current claim can be accepted or rejected."
    elif "horizon_claim" in implication:
        selection_class = "REDESIGN"
        selection_decision = "REJECT_CURRENT_HORIZON_CLAIM_PRESERVE_TARGETABILITY_FAILURE_INTELLIGENCE"
        downstream = "horizon_targetability_redesign"
        reason = "Reject only the unsupported horizon claim and preserve targetability failure intelligence."
    else:
        selection_class = "REDESIGN"
        selection_decision = "REJECT_CURRENT_SOURCE_PROXY_CLAIM_PRESERVE_AVOID_REDESIGN_INTELLIGENCE"
        downstream = "avoid_redesign_context_or_source_capture"
        reason = "Reject only the unsupported source-proxy claim and preserve avoid/redesign/source-capture intelligence."

    return {
        "claim_audit_selection_class": selection_class,
        "claim_audit_selection_decision": selection_decision,
        "claim_audit_selection_reason": reason,
        "downstream_path": downstream,
        "proxy_delta_reference": proxy_delta,
        "proxy_delta_reference_counted_as_r": False,
        "opportunity_preserved": True,
        "underlying_intelligence_preserved": True,
        "no_live_behavior": True,
    }


def apply_claim_audit_selection(row: dict[str, Any]) -> dict[str, Any]:
    selected = dict(row)
    selected.update(claim_audit_selection_for_row(row))
    return selected


def summarize_claim_audit_selection(rows: list[dict[str, Any]]) -> dict[str, Any]:
    proxy_refs = [
        value for row in rows if (value := safe_float(row.get("proxy_delta_reference"))) is not None
    ]
    return {
        "rows": len(rows),
        "claim_audit_selection_class_counts": dict(
            sorted(Counter(str(row.get("claim_audit_selection_class")) for row in rows).items())
        ),
        "claim_audit_selection_decision_counts": dict(
            sorted(Counter(str(row.get("claim_audit_selection_decision")) for row in rows).items())
        ),
        "main_action_class_counts": dict(sorted(Counter(str(row.get("main_action_class")) for row in rows).items())),
        "symbol_counts": dict(sorted(Counter(str(row.get("symbol")) for row in rows).items())),
        "route_session_counts": dict(sorted(Counter(str(row.get("route_session")) for row in rows).items())),
        "proxy_delta_reference_rows": len(proxy_refs),
        "proxy_delta_reference_sum_not_r": round(sum(proxy_refs), 8),
        "proxy_delta_reference_counted_as_r_rows": sum(
            row.get("proxy_delta_reference_counted_as_r") is True for row in rows
        ),
        "opportunity_preserved_rows": sum(row.get("opportunity_preserved") is True for row in rows),
        "underlying_intelligence_preserved_rows": sum(
            row.get("underlying_intelligence_preserved") is True for row in rows
        ),
        "live_effect_true_rows": sum(row.get("live_effect") is True for row in rows),
        "no_live_behavior_false_rows": sum(row.get("no_live_behavior") is not True for row in rows),
    }
