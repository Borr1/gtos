"""Default-off Scheduler V3 admission helpers.

This module is route-local research code. It does not import MT5, mutate
configuration, place orders, or activate live scheduling behavior. The helpers
turn current Lane10/Lane10B evidence rows into explicit Scheduler V3 action
classes that a future runtime integration can consume only after a separate
production-change dossier and owner approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


RUNTIME_EFFECT_BOUNDARY = (
    "offline_scheduler_v3_package_only_no_live_broker_order_deal_position_operation_"
    "no_config_prompt_risk_execution_safety_canary_selector_scheduler_activation_"
    "no_paid_api_no_remote"
)

RESULT_USE_STATUS = (
    "scheduler_v3_uses_exact_broker_real_and_source_bound_proxy_r_only_for_offline_"
    "research_materialization_priority_and_expectancy_accounting_not_live_runtime_priority"
)

REQUIRED_MONEY_RISK_FIELDS = (
    "account_balance",
    "account_equity",
    "day_start_baseline",
    "realized_broker_or_proxy_pnl",
    "open_worst_case_sl_risk_pct",
    "pending_worst_case_sl_risk_pct",
    "new_trade_worst_case_risk_pct",
    "approved_trade_risk_pct",
    "selected_cell_risk_pct",
    "actual_sl_distance_status",
    "lot_contract_geometry_status",
    "spread_slippage_commission_swap_buffer_pct",
    "daily_overlay_limit_pct",
    "external_daily_loss_limit_pct",
    "external_total_loss_limit_pct",
    "realized_cushion_pct",
    "drawdown_compression_state",
    "portfolio_ceiling_pct",
    "correlation_cluster_ceiling_pct",
)

ACTION_CLASSES = (
    "admit",
    "admit_reduced_risk",
    "delay",
    "replace",
    "queue",
    "conflict_net",
    "require_source",
    "reject",
)


def fnum(value: Any, default: float = 0.0) -> float:
    """Return a finite float for ledger math."""
    try:
        if value in (None, ""):
            return default
        number = float(value)
    except (TypeError, ValueError):
        return default
    if number != number or number in (float("inf"), float("-inf")):
        return default
    return number


def round9(value: Any) -> float | None:
    if value is None:
        return None
    return round(fnum(value), 9)


def money(value: Any) -> float:
    return round(fnum(value), 2)


def _text(value: Any, default: str = "missing") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


@dataclass(frozen=True)
class SchedulerV3Action:
    """Concrete default-off action emitted for one Scheduler V3 evidence row."""

    decision: str
    action_class: str
    action: str
    reason: str
    recovery_status: str
    owner_approval_required_for_live_use: bool = True
    runtime_effect_now: bool = False

    def asdict(self) -> dict[str, Any]:
        return {
            "scheduler_v3_decision": self.decision,
            "scheduler_v3_action_class": self.action_class,
            "scheduler_v3_action": self.action,
            "scheduler_v3_reason": self.reason,
            "blocked_edge_recovery_status": self.recovery_status,
            "owner_approval_required_for_live_use": self.owner_approval_required_for_live_use,
            "runtime_effect_now": self.runtime_effect_now,
        }


def source_gap_action(row: dict[str, Any]) -> bool:
    reason = _text(row.get("scheduler_reason") or row.get("reason"), "")
    requested = fnum(row.get("requested_risk_pct"), 0.0)
    return (
        "risk_missing" in reason
        or "risk_missing_nonpositive" in reason
        or "source_repair_required" in reason
        or requested <= 0
    )


def classify_scheduler_v3_action(row: dict[str, Any]) -> SchedulerV3Action:
    """Map Lane10B/Lane10 evidence to the concrete Scheduler V3 action class.

    The mapping is intentionally conservative about live activation but not
    vague: repairable rows become queue/delay/replace/admit-reduced designs
    with exact prerequisites instead of remaining generic blocker labels.
    """

    scheduler_decision = _text(row.get("scheduler_decision") or row.get("decision"), "")
    scheduler_reason = _text(row.get("scheduler_reason") or row.get("reason"), "")
    same_symbol_state = _text(row.get("same_symbol_state"), "")
    same_release = _text(row.get("same_symbol_release_state"), "")
    cluster_state = _text(row.get("cluster_state"), "")
    result_r = fnum(row.get("result_r"), 0.0)
    max_money_allowed = fnum(row.get("max_money_risk_allowed_pct"), 0.0)
    max_cluster_allowed = fnum(row.get("max_safe_risk_with_cluster_pct"), 0.0)
    requested = fnum(row.get("requested_risk_pct"), 0.0)
    approved = fnum(row.get("approved_risk_pct"), 0.0)

    if source_gap_action(row):
        return SchedulerV3Action(
            decision="REQUIRE_SOURCE",
            action_class="require_source",
            action="require_selected_cell_risk_and_broker_geometry_source_before_admission",
            reason="selected_cell_or_effective_risk_missing_nonpositive",
            recovery_status="source_capture_or_read_only_export_required",
        )

    if scheduler_decision == "ACCEPTED":
        return SchedulerV3Action(
            decision="ACCEPTED",
            action_class="admit",
            action="admit_full_risk_when_money_risk_exposure_stays_inside_all_limits",
            reason="current_money_risk_authority_accepts_full_risk",
            recovery_status="already_admitted_by_lane10",
        )

    if scheduler_decision == "ACCEPTED_REDUCED_RISK" or (0.0 < approved < requested):
        return SchedulerV3Action(
            decision="ACCEPTED_REDUCED_RISK",
            action_class="admit_reduced_risk",
            action="admit_reduced_risk_to_account_or_portfolio_headroom",
            reason="lane10_reduced_risk_haircut_preserved_as_v3_authority",
            recovery_status="reduced_risk_admission",
        )

    if "opposite_side" in same_symbol_state:
        return SchedulerV3Action(
            decision="REJECTED",
            action_class="conflict_net",
            action="reject_opposite_side_same_symbol_conflict_net_without_owner_hedge_policy",
            reason="opposite_side_hedge_requires_separate_net_gross_risk_contract",
            recovery_status="not_recoverable_without_owner_approved_hedge_dossier",
        )

    if "same_side" in same_symbol_state and "all_risk_released" in same_release:
        if result_r >= 2.0:
            return SchedulerV3Action(
                decision="REPLACE",
                action_class="replace",
                action="replace_weaker_pending_or_queue_higher_priority_same_side_after_ticket_proof",
                reason="same_side_ticket_lifecycle_released_and_high_proxy_expectancy",
                recovery_status="blocked_positive_recoverable_with_ticket_bound_lifecycle",
            )
        return SchedulerV3Action(
            decision="QUEUE",
            action_class="queue",
            action="queue_same_side_ticket_bound_admission_after_release_evidence",
            reason="same_side_lifecycle_active_but_worst_case_risk_released",
            recovery_status="blocked_positive_recoverable_with_ticket_bound_lifecycle",
        )

    if "same_side" in same_symbol_state and "open_worst_case_risk_active" in same_release:
        return SchedulerV3Action(
            decision="DELAY",
            action_class="delay",
            action="delay_until_same_symbol_ticket_risk_release_or_close",
            reason="same_side_stacking_requires_risk_release_before_admission",
            recovery_status="delayed_until_lifecycle_releases_worst_case_risk",
        )

    if cluster_state == "cluster_ceiling_exceeded":
        if result_r > 0 and max_cluster_allowed >= 0.25:
            return SchedulerV3Action(
                decision="ACCEPTED_REDUCED_RISK",
                action_class="admit_reduced_risk",
                action="admit_reduced_risk_to_remaining_correlation_cluster_headroom",
                reason="cluster_headroom_supports_reduced_risk_variant",
                recovery_status="cluster_block_recoverable_as_reduced_risk",
            )
        return SchedulerV3Action(
            decision="REJECTED",
            action_class="reject",
            action="reject_unbounded_correlated_cluster_exposure",
            reason="correlation_cluster_ceiling_exceeded_without_safe_reduced_headroom",
            recovery_status="correct_reject_for_cluster_concentration",
        )

    if scheduler_reason in {
        "portfolio_total_risk_ceiling_exceeded",
        "account_daily_or_overall_limit_exceeded",
        "drawdown_compression_portfolio_budget_exceeded",
    }:
        if result_r > 0 and max_money_allowed >= 0.25:
            return SchedulerV3Action(
                decision="ACCEPTED_REDUCED_RISK",
                action_class="admit_reduced_risk",
                action="admit_reduced_risk_to_money_risk_headroom",
                reason="money_risk_headroom_supports_reduced_risk_variant",
                recovery_status="budget_block_recoverable_as_reduced_risk",
            )
        return SchedulerV3Action(
            decision="REJECTED",
            action_class="reject",
            action="reject_when_account_or_portfolio_money_risk_headroom_is_absent",
            reason=scheduler_reason,
            recovery_status="correct_reject_for_money_risk_boundary",
        )

    if result_r <= 0:
        return SchedulerV3Action(
            decision="REJECTED",
            action_class="reject",
            action="reject_no_positive_proxy_edge_after_scheduler_context",
            reason="no_positive_exact_or_proxy_result_for_current_evidence_slice",
            recovery_status="correct_reject_for_this_evidence_slice",
        )

    return SchedulerV3Action(
        decision="REJECTED",
        action_class="reject",
        action="reject_until_scheduler_v3_has_explicit_recovery_contract",
        reason=scheduler_reason or "unclassified_rejected_scheduler_row",
        recovery_status="requires_specific_future_contract_before_recovery",
    )


def build_priority_components(
    row: dict[str, Any],
    path_row: dict[str, Any] | None = None,
    whiteboard_row: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute all-row research and runtime-safe priority components.

    The offline research score may use source-bound proxy policy expectation
    fields. The runtime-safe score excludes post-outcome result fields and is
    emitted separately so future integration cannot accidentally use hindsight.
    """

    path_row = path_row or {}
    whiteboard_row = whiteboard_row or {}
    selector_decision = _text(row.get("lane09_mechanism_decision"), "")
    scheduler_decision = _text(row.get("scheduler_decision") or row.get("decision"), "")
    source_completeness = _text(
        row.get("lane09_source_completeness_state")
        or path_row.get("source_completeness_state"),
        "",
    )
    spread_bucket = _text(row.get("spread_r_bucket"), "")
    action = classify_scheduler_v3_action(row)

    selector_quality = {
        "promote": 0.30,
        "reduce": 0.12,
        "avoid": -0.35,
        "reject": -0.35,
    }.get(selector_decision.lower(), 0.0)

    max_safe = max(
        fnum(row.get("max_money_risk_allowed_pct"), 0.0),
        fnum(row.get("max_safe_risk_with_cluster_pct"), 0.0),
    )
    requested = max(fnum(row.get("requested_risk_pct"), 0.0), 0.0)
    scheduler_state = _clamp(max_safe / max(requested, 0.25), -1.0, 1.0) * 0.20
    if scheduler_decision == "ACCEPTED":
        scheduler_state += 0.10
    elif scheduler_decision == "ACCEPTED_REDUCED_RISK":
        scheduler_state += 0.05

    correlation_state = whiteboard_row.get("correlation_cluster_state") or {}
    peer_count = fnum(correlation_state.get("cluster_peer_count"), 0.0)
    risk_on_score = fnum(correlation_state.get("risk_on_proxy_score"), 0.0)
    market_context = _clamp(risk_on_score, -1.0, 1.0) * 0.05
    if peer_count > 0:
        market_context -= min(0.08, peer_count * 0.01)
    field_state = whiteboard_row.get("field_source_state") or {}
    if field_state.get("runtime_correlation_snapshot") == "missing":
        market_context -= 0.03
    if field_state.get("market_hours_state") == "missing":
        market_context -= 0.03

    policy_expectation_r = path_row.get("best_policy_cost_adjusted_median_r")
    if policy_expectation_r is None:
        policy_expectation_r = path_row.get("current_policy_cost_adjusted_median_r")
    policy_expectation_r = fnum(policy_expectation_r, 0.0)
    policy_expectation = _clamp(policy_expectation_r / 4.0, -0.50, 0.50) * 0.25

    stress_delta = fnum(path_row.get("policy_cost_stress_delta_r"), 0.0)
    cost_stress = _clamp(stress_delta, -1.0, 1.0) * 0.10
    if "missing" in spread_bucket:
        cost_stress -= 0.04
    elif "le_0_02" in spread_bucket:
        cost_stress += 0.04

    gap_count = fnum(path_row.get("source_gap_count"), 0.0)
    source_completeness_component = max(-0.25, -0.02 * gap_count)
    if source_completeness in {"complete", "complete_with_row_level_gaps"}:
        source_completeness_component += 0.05

    path_class = _text(path_row.get("path_class"), "")
    path_component = 0.0
    if "winner" in path_class or fnum(path_row.get("mfe_r"), 0.0) >= 1.0:
        path_component += 0.12
    if path_row.get("sl_before_1r") is True:
        path_component -= 0.20
    if path_row.get("stuck_no_resolution") is True:
        path_component -= 0.08

    cluster_risk = fnum(row.get("correlated_cluster_risk_pct_before"), 0.0)
    total_before = fnum(row.get("total_risk_pct_before"), 0.0)
    portfolio_marginal = max(-0.25, 0.18 - (cluster_risk * 0.025) - (total_before * 0.01))

    recovery_bonus = {
        "admit": 0.10,
        "admit_reduced_risk": 0.06,
        "queue": 0.03,
        "replace": 0.04,
        "delay": -0.03,
        "conflict_net": -0.12,
        "require_source": -0.20,
        "reject": -0.10,
    }.get(action.action_class, 0.0)

    offline_score = (
        selector_quality
        + scheduler_state
        + market_context
        + policy_expectation
        + cost_stress
        + source_completeness_component
        + path_component
        + portfolio_marginal
        + recovery_bonus
    )
    runtime_safe_score = offline_score - policy_expectation

    return {
        "selector_quality_component": round9(selector_quality),
        "scheduler_state_component": round9(scheduler_state),
        "market_context_component": round9(market_context),
        "policy_expectation_component": round9(policy_expectation),
        "policy_expectation_r": round9(policy_expectation_r),
        "cost_stress_component": round9(cost_stress),
        "source_completeness_component": round9(source_completeness_component),
        "path_anatomy_component": round9(path_component),
        "portfolio_marginal_risk_component": round9(portfolio_marginal),
        "blocked_edge_recovery_component": round9(recovery_bonus),
        "offline_research_priority_score": round9(offline_score),
        "runtime_safe_priority_score": round9(runtime_safe_score),
        "offline_score_uses_source_bound_policy_result_fields": True,
        "runtime_safe_score_excludes_post_outcome_result_fields": True,
    }


def build_money_risk_exposure(row: dict[str, Any]) -> dict[str, Any]:
    """Materialize the Scheduler V3 money-risk authority fields for one row."""

    day_start = fnum(row.get("day_start_baseline"), 100000.0)
    equity = fnum(row.get("current_equity"), day_start)
    realized = fnum(row.get("realized_proxy_pnl"), 0.0)
    requested = fnum(row.get("requested_risk_pct"), 0.0)
    approved = fnum(row.get("approved_risk_pct"), 0.0)
    open_risk = fnum(row.get("open_risk_pct_before"), 0.0)
    pending_risk = fnum(row.get("pending_risk_pct_before"), 0.0)
    total_before = fnum(row.get("total_risk_pct_before"), 0.0)
    ceiling = fnum(row.get("dynamic_portfolio_ceiling_pct"), 0.0)
    account_available = fnum(row.get("account_available_risk_pct"), 0.0)
    cost_buffer = fnum(row.get("cost_buffer_pct"), 0.0)

    drawdown_state = "drawdown_compression_active" if equity < day_start else "normal_or_cushion"
    actual_sl_status = (
        "source_gap_requires_selected_packet_entry_stop_distance_and_broker_tick_value"
        if requested <= 0
        else "risk_pct_available_sl_distance_not_authoritative_in_scheduler_v3_inputs"
    )
    geometry_status = (
        "proxy_or_missing_contract_geometry_requires_lane18_or_read_only_symbol_export"
        if "missing" in _text(row.get("cost_status"), "").lower()
        else "broker_symbol_spec_joined_or_proxy_bound"
    )

    exposure = {
        "account_balance": 100000.0,
        "account_equity": money(equity),
        "day_start_baseline": money(day_start),
        "realized_broker_or_proxy_pnl": money(realized),
        "realized_pnl_source": "broker_real_if_available_else_lane10_source_bound_proxy",
        "open_worst_case_sl_risk_pct": round9(open_risk),
        "pending_worst_case_sl_risk_pct": round9(pending_risk),
        "new_trade_worst_case_risk_pct": round9(requested),
        "approved_trade_risk_pct": round9(approved),
        "selected_cell_risk_pct": round9(row.get("requested_risk_pct")),
        "actual_sl_distance_status": actual_sl_status,
        "lot_contract_geometry_status": geometry_status,
        "spread_slippage_commission_swap_buffer_pct": round9(cost_buffer),
        "daily_overlay_limit_pct": 4.0,
        "external_daily_loss_limit_pct": 5.0,
        "external_total_loss_limit_pct": 10.0,
        "realized_cushion_pct": round9(max(0.0, (equity - day_start) / 100000.0 * 100.0)),
        "drawdown_compression_state": drawdown_state,
        "portfolio_ceiling_pct": round9(ceiling),
        "account_available_risk_pct": round9(account_available),
        "total_risk_pct_before": round9(total_before),
        "total_risk_pct_after": round9(row.get("total_risk_pct_after")),
        "correlation_cluster_ceiling_pct": 4.0,
        "same_symbol_worst_case_risk_pct": round9(row.get("same_symbol_risk_pct_before")),
        "correlated_cluster_worst_case_risk_pct": round9(
            row.get("correlated_cluster_risk_pct_before")
        ),
        "source_contract": (
            "money_risk_authority_uses_balance_equity_day_start_realized_pnl_open_pending_"
            "new_trade_risk_cost_buffer_daily_total_limits_cushion_and_drawdown_state"
        ),
    }
    missing = [field for field in REQUIRED_MONEY_RISK_FIELDS if field not in exposure]
    if missing:
        raise ValueError(f"missing Scheduler V3 money-risk fields: {missing}")
    return exposure
