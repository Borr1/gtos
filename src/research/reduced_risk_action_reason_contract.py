"""Shared replay contract for reduced-risk selector action semantics.

These constants describe local replay/package authority only. They do not
grant broker mutation, live trading, or final-selection authority.
"""

from __future__ import annotations


RISK_BEARING_SELECTOR_ACTIONS = frozenset(
    {"trade", "reduce-risk", "open-reduced-risk"}
)

REDUCED_RISK_NEW_ENTRY_SELECTOR_ACTIONS = frozenset(
    {"reduce-risk", "open-reduced-risk"}
)

SELECTOR_REDUCE_RISK_ALLOWED_ACTION_INTENTS = frozenset(
    {
        "reduce_existing",
        "close_existing",
        "wait",
        "cancel_pending",
        "replace_pending",
    }
)

SELECTOR_OPEN_REDUCED_RISK_ALLOWED_ACTION_INTENTS = frozenset(
    {
        "new_position",
        "same_direction_scale_in",
        "close_and_reverse",
        "replace_pending",
    }
)

REDUCED_RISK_SIGNED_NEW_ENTRY_ACTION_INTENTS = frozenset(
    {
        "new_position",
        "same_direction_scale_in",
        "close_and_reverse",
        "replace_pending",
    }
)

OPEN_REDUCED_SELECTOR_REASONS = frozenset(
    {
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk",
        "ultimate_candidate_package_admission_softened_selector_cost_or_fill_floor_in_replay",
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only",
        "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
        "ultimate_candidate_package_positive_predecision_router_refusal_open_reduced_risk",
        "ultimate_candidate_package_positive_predecision_off_session_open_reduced_risk",
        "admission_quality_dynamic_router_refusal_open_reduced_risk_configured",
        "admission_quality_off_configured_session_open_reduced_risk_configured",
        "source_bound_router_refusal_open_reduced_materialized_for_replay",
        "source_bound_fill_floor_package_materialized_for_replay",
        "ultimate_candidate_package_explicit_executable_open_reduced_materialized_for_replay",
        "selected_package_bridge_open_reduced_materialized_for_replay",
    }
)

SELECTOR_REDUCE_RISK_NEW_ENTRY_BLOCK_REASONS = frozenset(
    {
        "calibrated_admission_fill_probability_below_generalized_floor",
        "numeric_confluence_structured_disagreement",
        "ultimate_candidate_package_numeric_disagreement_open_reduced_risk",
        "ultimate_candidate_package_admission_softened_selector_cost_or_fill_floor_in_replay",
        "ultimate_candidate_package_admission_softened_selector_fill_floor_in_replay",
        "ultimate_candidate_package_dynamic_router_refusal_softened_reduce_risk",
        "ultimate_candidate_package_fill_floor_bypass_reduce_risk_only",
        "ultimate_candidate_package_soft_admission:calibrated_admission_fill_probability_below_generalized_floor",
        "ultimate_candidate_package_positive_predecision_off_session_reduce_risk",
    }
)

SCHEDULER_ACTION_INTENT_ALIASES = {
    "scale": "same_direction_scale_in",
    "scale_in": "same_direction_scale_in",
    "reduce": "reduce_existing",
    "close": "close_existing",
    "reverse": "close_and_reverse",
    "cancel": "cancel_pending",
    "replace": "replace_pending",
}

SOURCE_COMPLETENESS_BLOCKED_STATUS_TOKENS = (
    "missing",
    "degraded",
    "gap",
    "source_required",
    "incomplete",
    "prospective_capture",
    "snapshot_incomplete",
)


def canonical_selector_action(action: object) -> str:
    selector_action = str(action or "").strip().lower().replace("_", "-").replace(" ", "-")
    if selector_action == "open-reduced-risk":
        return "open-reduced-risk"
    if selector_action == "reduce-risk":
        return "reduce-risk"
    return selector_action


def normalize_selector_action_for_reason(
    action: object,
    reason: object,
    action_intent: object = None,
) -> str:
    selector_action = canonical_selector_action(action)
    selector_reason = str(reason or "").strip().lower()
    if not selector_action and selector_reason in OPEN_REDUCED_SELECTOR_REASONS:
        return "open-reduced-risk"
    if (
        not selector_action
        and selector_reason
        and selector_reason in SELECTOR_REDUCE_RISK_NEW_ENTRY_BLOCK_REASONS
    ):
        return "reduce-risk"
    return selector_action
