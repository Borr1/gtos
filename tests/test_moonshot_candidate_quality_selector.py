from src.research.moonshot_default_off_policy_router import route_moonshot_dynamic_execution


def _event(**overrides):
    event = {
        "symbol": "XAUUSD",
        "side": "LONG",
        "framework": "origin_liquidity_sweep_reclaim",
        "candidate_origin_family": "origin_liquidity_sweep_reclaim",
        "route_session": "london",
        "session_bucket": "london",
        "branch_label": "FOLLOW",
        "activated_origin_families": ["liquidity_sweep_reclaim", "displacement_continuation"],
        "broader_origin_allowed": True,
        "broker_native_eligible": True,
        "runtime_instrument_configured": True,
        "selected_cell_risk_required": True,
        "selected_cell_risk_allowed": True,
        "selected_cell_risk_pct": 0.25,
        "source_path_feature_status": "raw_data_m15_asof_complete",
        "live_generation_status": "generated_live_asof_closed_m15",
        "source_mode": "LIVE_RAW_M15",
        "source_window_complete": True,
        "ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
        "selected_policy_ordered_path_status": "ordered_path_not_ambiguous_in_live_closed_m15_generation",
        "kill_zone_position": "in_london_runtime_configured_kill_zone",
        "policy_router_mode": "condition_asof_displacement_v1",
        "condition_challenger_enabled": True,
        "primary_policy": "momentum_exhaustion",
        "partial_exception_policy": "partial_be_runner",
        "partial_exception_origin_families": ["liquidity_sweep_reclaim", "displacement_continuation"],
        "candidate_quality_selector_enabled": True,
        "candidate_quality_selector_apply_to_execution": True,
        "candidate_quality_selector_max_spread_r": 0.20,
        "spread_r_at_candidate": 0.05,
    }
    event.update(overrides)
    return event


def test_quality_selector_allows_friday_broad_positive_london_origin_subset():
    decision = route_moonshot_dynamic_execution(
        _event(),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.runtime_effect_now is True
    assert decision.candidate_use_allowed_now is True
    assert decision.source_event if hasattr(decision, "source_event") else True
    quality = decision.route_dimensions["candidate_quality_selector"]
    assert quality["classification"] == "tradeable_now"
    assert quality["matched_rule"]["rule_id"] == "friday_broad_london_liquidity_sweep_reclaim_positive_current_selected"
    assert quality["matched_rule"]["clean_friday_rows"] == 20
    assert quality["matched_rule"]["broad_selected_rows"] == 15645


def test_quality_selector_refuses_session_origin_outside_positive_weekend_subset():
    decision = route_moonshot_dynamic_execution(
        _event(
            route_session="ny",
            session_bucket="ny",
            kill_zone_position="in_ny_runtime_configured_kill_zone",
        ),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.runtime_effect_now is False
    assert "candidate_quality_session_origin_not_in_positive_weekend_subset" in decision.refusal_reasons
    assert decision.route_dimensions["candidate_quality_selector"]["classification"] == "insufficient_current_proof"


def test_quality_selector_refuses_high_spread_inside_positive_subset():
    decision = route_moonshot_dynamic_execution(
        _event(spread_r_at_candidate=0.25),
        enabled=True,
        apply_to_execution=True,
    )

    assert decision.runtime_effect_now is False
    assert "candidate_quality_spread_r_exceeds_weekend_selector_limit" in decision.refusal_reasons
    assert decision.route_dimensions["candidate_quality_selector"]["classification"] == "no_trade_by_evidence"
