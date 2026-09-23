"""Canonical predecision blocker precedence for scheduler and replay ledgers."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


ORDER_BLOCKER_RESOLUTION_SCHEMA = "gtos.order_blocker_resolution.v1"

CANONICAL_ORDER_BLOCKER_FAMILIES = frozenset(
    {
        "source_or_signature_authority",
        "cost_authority",
        "poi_lifecycle_terminal",
        "session_authority",
        "execution_fillability",
        "risk_safety",
        "order_lifecycle",
        "scheduler_selection",
    }
)

GENERIC_SELECTOR_BLOCKER_TOKENS = (
    "selector_reduce_risk_new_entry_not_order_authority",
    "selector_reduce_risk_new_entry_not_trade_authority",
    "selector_reduced_risk_new_position_signed_authority_missing",
)

NON_BLOCKING_DIAGNOSTIC_REASONS = frozenset(
    {
        "risk_authority_bound_and_headroom_available",
        "package_candidate_and_signed_new_entry_authority_executable",
        "broker_cost_and_scheduler_action_executable",
        "scheduler_approved_risk_below_selected_cell_risk_preserved",
        "approved_risk_pct_below_selected_cell_risk_pct",
        "selector_open_reduced_risk_origin_preserved",
        "selector_open_reduced_risk_origin_preserved_after_runtime_risk_reduction",
        "selector_open_reduced_risk_origin_preserved_after_scheduler_risk_cap",
        "selector_reduce_risk_origin_preserved",
        "selector_open_reduced_risk_package_fill_floor_risk_cap_released_bounded",
        "selector_reduce_risk_package_fill_floor_risk_cap_released_bounded",
        "signed_package_full_risk_expression_authorized",
        "poi_scheduler_readiness_passed",
    }
)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _lower(value: Any) -> str:
    return _text(value).lower().replace("-", "_").replace(" ", "_")


def order_blocker_is_generic_selector_alias(reason: Any) -> bool:
    text = _lower(reason)
    return any(token in text for token in GENERIC_SELECTOR_BLOCKER_TOKENS)


def order_blocker_is_nonblocking_diagnostic(reason: Any) -> bool:
    text = _lower(reason)
    return bool(
        text in NON_BLOCKING_DIAGNOSTIC_REASONS
        or "risk_cap_released_bounded" in text
        or "predecision_stop_hazard_guard_risk_cap_applied" in text
        or "predecision_stop_hazard_guard_risk_capped" in text
        or text.endswith("predecision_stop_hazard_guard_capped")
        or text.endswith("_origin_preserved")
        or "origin_preserved_after_scheduler_risk_cap" in text
        or "origin_preserved_after_runtime_risk_reduction" in text
    )


def order_blocker_family(reason: Any) -> str:
    text = _lower(reason)
    if not text:
        return "unknown"
    if any(
        token in text
        for token in (
            "signature",
            "signed_new_entry_authority_invalid",
            "authority_hash",
            "tamper",
            "source_gap",
            "source_required",
            "source_completeness",
        )
    ):
        return "source_or_signature_authority"
    if any(
        token in text
        for token in (
            "broker_cost",
            "cost_refused",
            "cost_authority",
            "spread_r_exceeds",
            "commission_r_exceeds",
            "slippage_r_exceeds",
            "swap_r_exceeds",
            "total_cost_r_exceeds",
            "untradeable_cost_floor",
            "candidate_cost_r_fallback",
        )
    ):
        return "cost_authority"
    if any(
        token in text
        for token in (
            "poi_invalidated",
            "poi_filled",
            "terminal_poi",
            "poi_state_contract",
            "poi_lifecycle_hash",
            "lifecycle_invalid",
        )
    ):
        return "poi_lifecycle_terminal"
    if any(
        token in text
        for token in (
            "off_configured_session",
            "off_session",
            "session_authority",
        )
    ):
        return "session_authority"
    if any(
        token in text
        for token in (
            "execution_fillability",
            "execution_fill_probability",
            "fill_probability_below",
            "selected_policy_executable_quality",
            "package_fill_floor_quality",
            "dynamic_budget_quality_floor",
            "poi_scheduler_readiness_floor",
        )
    ):
        return "execution_fillability"
    if any(
        token in text
        for token in (
            "daily_loss",
            "daily_lockout",
            "headroom",
            "portfolio_risk",
            "cluster_risk",
            "risk_basis",
            "selected_cell_or_requested_risk",
            "stop_hazard",
        )
    ):
        return "risk_safety"
    if any(
        token in text
        for token in (
            "scheduler",
            "not_selected",
            "displacement",
            "selector_materialization",
            "not_scheduler_materialized",
        )
    ):
        return "scheduler_selection"
    if order_blocker_is_generic_selector_alias(text):
        return "generic_selector_alias"
    if any(token in text for token in ("expiry", "expired", "cancel_replace")):
        return "order_lifecycle"
    return "other"


def order_blocker_precedence(reason: Any) -> int:
    family = order_blocker_family(reason)
    return {
        "source_or_signature_authority": 0,
        "cost_authority": 1,
        "poi_lifecycle_terminal": 2,
        "session_authority": 3,
        "execution_fillability": 4,
        "risk_safety": 5,
        "order_lifecycle": 6,
        "scheduler_selection": 7,
        "other": 8,
        "generic_selector_alias": 9,
        "unknown": 10,
    }.get(family, 10)


def _flatten_reason_items(values: Iterable[Any]) -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    observed: set[str] = set()

    def add(value: Any, source: str) -> None:
        if isinstance(value, Mapping):
            for key in (
                "primary_reason",
                "final_blocker_reason",
                "blocker_reason",
                "risk_decision_reason",
                "primary_runtime_ineligible_reason",
                "scheduler_option_primary_runtime_ineligible_reason",
                "risk_finalizer_scheduler_option_primary_runtime_ineligible_reason",
                "hard_block_reason",
                "failure_reason",
                "reason",
                "terminal_vetoes",
                "vetoes",
                "tier_causes",
                "reasons",
                "quality_failures",
                "raw_failures",
                "resolved_failures",
                "order_blocker_resolution",
            ):
                if key in value:
                    add(value.get(key), f"{source}.{key}")
            for key, nested in value.items():
                key_text = str(key)
                if key_text.endswith("causal_poi_lifecycle"):
                    add(nested, f"{source}.{key_text}")
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                add(item, source)
            return
        reason = _text(value)
        if (
            reason
            and not order_blocker_is_nonblocking_diagnostic(reason)
            and reason not in observed
        ):
            observed.add(reason)
            items.append((reason, source))

    for index, value in enumerate(values):
        add(value, f"reason_surface[{index}]")
    return items


def resolve_order_blockers(
    *reason_surfaces: Any,
    signed_order_proposal_allowed: bool = False,
    source_boundary: str = "predecision_order_blocker_precedence_no_outcome_fields",
) -> dict[str, Any]:
    """Resolve one primary cause while retaining all co-blockers and aliases."""

    observed_items = _flatten_reason_items(reason_surfaces)
    observed = [reason for reason, _source in observed_items]
    source_by_reason = {
        reason: source for reason, source in observed_items
    }
    generic_aliases = [
        reason
        for reason in observed
        if order_blocker_is_generic_selector_alias(reason)
    ]
    concrete = [
        reason
        for reason in observed
        if reason not in generic_aliases
    ]
    superseded_aliases = (
        generic_aliases if signed_order_proposal_allowed and concrete else []
    )
    active = [
        reason for reason in observed if reason not in superseded_aliases
    ]
    active.sort(
        key=lambda reason: (
            order_blocker_precedence(reason),
            observed.index(reason),
        )
    )
    primary = active[0] if active else ""
    primary_family = order_blocker_family(primary) if primary else ""
    return {
        "schema_version": ORDER_BLOCKER_RESOLUTION_SCHEMA,
        "primary_reason": primary or None,
        "primary_family": primary_family or None,
        "primary_source": source_by_reason.get(primary) if primary else None,
        "co_blockers": [reason for reason in active if reason != primary],
        "co_blocker_sources": [
            {
                "reason": reason,
                "source": source_by_reason.get(reason),
            }
            for reason in active
            if reason != primary
        ],
        "superseded_aliases": superseded_aliases,
        "all_observed_reasons": observed,
        "all_observed_reason_sources": [
            {"reason": reason, "source": source}
            for reason, source in observed_items
        ],
        "signed_order_proposal_allowed": bool(signed_order_proposal_allowed),
        "specific_primary_selected": bool(
            primary and not order_blocker_is_generic_selector_alias(primary)
        ),
        "source_boundary": source_boundary,
        "uses_outcome_fields": False,
    }
