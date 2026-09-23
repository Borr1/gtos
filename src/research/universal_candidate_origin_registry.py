"""Research-only candidate-origin registry for moonshot discovery.

This module is deliberately declarative and default-off. It prevents future
candidate discovery work from treating the current OB/FVG/breaker generator as
the full opportunity horizon.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateOriginFamily:
    name: str
    category: str
    source_requirements: tuple[str, ...]
    candidate_clock: str
    asof_controls: tuple[str, ...]
    current_gtos_status: str
    boxes_out_if_missing: str
    next_replay_action: str


def required_origin_families() -> list[CandidateOriginFamily]:
    """Return the full seed registry for non-boxed discovery.

    The list is not a ranking and is not an exhaustive claim about all possible
    market science. It is the minimum route-local registry required before
    Stage05 can say candidate-origin boxing has been repaired structurally.
    """

    return [
        CandidateOriginFamily(
            name="ob_retest",
            category="current_gtos_framework",
            source_requirements=("M15/H1/H4/D1 OHLC", "market_state_order_blocks"),
            candidate_clock="m15_close",
            asof_controls=("market_state_asof", "no_future_structure"),
            current_gtos_status="active_baseline",
            boxes_out_if_missing="baseline edge mechanism cannot be compared",
            next_replay_action="keep_as_baseline_comparator",
        ),
        CandidateOriginFamily(
            name="fvg_fill",
            category="current_gtos_framework",
            source_requirements=("M15/H1/H4/D1 OHLC", "fair_value_gap_registry"),
            candidate_clock="m15_close",
            asof_controls=("market_state_asof", "gap_birth_before_candidate"),
            current_gtos_status="active_baseline",
            boxes_out_if_missing="existing multi-framework path cannot be reproduced",
            next_replay_action="keep_as_baseline_comparator",
        ),
        CandidateOriginFamily(
            name="breaker_re_entry",
            category="current_gtos_framework",
            source_requirements=("M15/H1/H4/D1 OHLC", "breaker_block_registry"),
            candidate_clock="m15_close",
            asof_controls=("market_state_asof", "breaker_birth_before_candidate"),
            current_gtos_status="active_baseline",
            boxes_out_if_missing="existing multi-framework path cannot be reproduced",
            next_replay_action="keep_as_baseline_comparator",
        ),
        CandidateOriginFamily(
            name="liquidity_sweep_reclaim",
            category="liquidity_and_stop_cascade",
            source_requirements=("M1/M5/M15 OHLC", "swing_high_low_liquidity_levels"),
            candidate_clock="event_time_or_bar_close",
            asof_controls=("sweep_level_known_before_break", "no_future_swing_confirmation"),
            current_gtos_status="shadow_or_partial_diagnostic",
            boxes_out_if_missing="stop-cascade reversals outside static POIs are invisible",
            next_replay_action="build_sweep_reclaim_candidate_generator",
        ),
        CandidateOriginFamily(
            name="displacement_continuation",
            category="impulse_path_geometry",
            source_requirements=("M1/M5/M15 OHLC", "range_normalized_displacement"),
            candidate_clock="event_time_or_bar_close",
            asof_controls=("displacement_measured_at_close", "no_future_retrace"),
            current_gtos_status="shadow_diagnostic",
            boxes_out_if_missing="non-POI impulse continuation opportunities are invisible",
            next_replay_action="build_displacement_continuation_generator",
        ),
        CandidateOriginFamily(
            name="continuation_no_retrace",
            category="impulse_path_geometry",
            source_requirements=("M1/M5/M15 OHLC", "path_follow_without_entry_touch"),
            candidate_clock="event_time_or_bar_close",
            asof_controls=("entry_miss_known_before_follow", "no_future_target_touch"),
            current_gtos_status="shadow_diagnostic",
            boxes_out_if_missing="no-fill winners remain only post-hoc failure anatomy",
            next_replay_action="convert_cnr_shadow_to_candidate_generator",
        ),
        CandidateOriginFamily(
            name="nofill_reprice_reentry",
            category="pending_lifecycle",
            source_requirements=("pending_lifecycle_logs", "M1/M5/M15 OHLC"),
            candidate_clock="pending_lifecycle_event",
            asof_controls=("pending_intent_logged", "no_synthetic_historical_intent"),
            current_gtos_status="repair_needed",
            boxes_out_if_missing="missed fillability improvement cannot become an opportunity",
            next_replay_action="build_forward_capture_then_replay_reprice_rules",
        ),
        CandidateOriginFamily(
            name="volatility_compression_expansion",
            category="volatility_state",
            source_requirements=("M1/M5/M15 OHLC", "atr_or_realized_volatility"),
            candidate_clock="bar_close",
            asof_controls=("vol_window_past_only", "purged_regime_split"),
            current_gtos_status="not_first_class_candidate_origin",
            boxes_out_if_missing="volatility-release setups are only context fields",
            next_replay_action="build_volatility_state_origin_generator",
        ),
        CandidateOriginFamily(
            name="session_open_range_break",
            category="session_clock",
            source_requirements=("M1/M5/M15 OHLC", "session_calendar"),
            candidate_clock="session_event_time",
            asof_controls=("session_window_known", "range_closed_before_break"),
            current_gtos_status="not_first_class_candidate_origin",
            boxes_out_if_missing="session-specific opening-range behavior cannot generate candidates",
            next_replay_action="build_session_open_range_generator",
        ),
        CandidateOriginFamily(
            name="regime_transition_break",
            category="regime_state",
            source_requirements=("H1/H4/D1 OHLC", "regime_classifier_state"),
            candidate_clock="bar_close",
            asof_controls=("regime_state_past_only", "no_outcome_conditioned_regime"),
            current_gtos_status="shadow_context",
            boxes_out_if_missing="trend/range transition becomes passive context only",
            next_replay_action="build_regime_transition_origin_generator",
        ),
        CandidateOriginFamily(
            name="orderflow_depth_imbalance_proxy",
            category="microstructure_orderflow",
            source_requirements=("tick_or_sierra_depth_proxy", "spread_state"),
            candidate_clock="event_time",
            asof_controls=("quote_depth_before_decision", "no_future_fill_or_result"),
            current_gtos_status="source_limited_shadow",
            boxes_out_if_missing="orderflow/depth pressure cannot originate opportunities",
            next_replay_action="build_proxy_packet_then_candidate_generator",
        ),
        CandidateOriginFamily(
            name="spread_liquidity_state_shift",
            category="execution_microstructure",
            source_requirements=("tick_bid_ask", "spread_state"),
            candidate_clock="event_time",
            asof_controls=("spread_known_before_entry", "no_broker_result_field"),
            current_gtos_status="not_first_class_candidate_origin",
            boxes_out_if_missing="execution-quality edge remains only a gate/cost field",
            next_replay_action="build_spread_state_origin_or_filter_comparator",
        ),
        CandidateOriginFamily(
            name="news_volatility_reprice",
            category="calendar_macro",
            source_requirements=("economic_calendar", "M1/M5/M15 OHLC"),
            candidate_clock="calendar_event_time",
            asof_controls=("calendar_known_before_event", "no_future_surprise_data_without_source"),
            current_gtos_status="filter_context",
            boxes_out_if_missing="news/context can only block, not discover asymmetric opportunity",
            next_replay_action="build_calendar_window_origin_generator",
        ),
        CandidateOriginFamily(
            name="cross_asset_lead_lag",
            category="cross_market_context",
            source_requirements=("synchronized_multi_symbol_ohlc", "correlation_state"),
            candidate_clock="event_time_or_bar_close",
            asof_controls=("leader_move_known_before_lag_candidate", "purged_cross_symbol_time"),
            current_gtos_status="risk_gate_context",
            boxes_out_if_missing="cross-asset context can only size/block, not originate candidates",
            next_replay_action="build_lead_lag_origin_generator",
        ),
        CandidateOriginFamily(
            name="path_hazard_early_failure",
            category="survival_hazard",
            source_requirements=("ordered_path_observations", "dynamic_policy_replay_rows"),
            candidate_clock="post_entry_management_clock",
            asof_controls=("hazard_inputs_before_exit_decision", "no_future_mfe_mae_label"),
            current_gtos_status="not_first_class_entry_or_exit_origin",
            boxes_out_if_missing="path survival cannot change entry timing or dynamic exit",
            next_replay_action="build_hazard_state_exit_and_entry_comparator",
        ),
        CandidateOriginFamily(
            name="structural_distance_extreme",
            category="geometry_topology",
            source_requirements=("swing_structure", "distance_to_liquidity_or_equilibrium"),
            candidate_clock="bar_close",
            asof_controls=("structure_known_before_candidate", "no_future_swing_confirm"),
            current_gtos_status="passive_feature_or_prompt_context",
            boxes_out_if_missing="geometry extremes remain prompt context instead of candidate origins",
            next_replay_action="build_structural_distance_origin_generator",
        ),
    ]


def family_names() -> list[str]:
    return [family.name for family in required_origin_families()]
