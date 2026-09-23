from __future__ import annotations

from build_vnext_moonshot_lane08_digital_twin_replay_engine import (
    add_metric,
    build_decision_inputs,
    build_result_payload,
    choose_result_r,
    close_metric,
    is_friday_row,
    new_metric,
    validate_decision_inputs_no_leak,
)


def test_decision_input_validator_rejects_future_result_fields():
    decision_inputs = {
        "candidate_generation": {"symbol": "XAUUSD"},
        "selector": {"source_bound_proxy_r": 1.25},
    }

    issues = validate_decision_inputs_no_leak(decision_inputs)

    assert issues
    assert issues[0]["field"] == "selector.source_bound_proxy_r"


def test_decision_input_validator_allows_source_availability_features():
    decision_inputs = {
        "source_completeness": {
            "m1_availability_status": "local_m1_bar_available_for_entry_minute",
            "tick_availability_status": "local_tick_source_date_absent_after_data_ticks_search",
            "source_use_state": "m15_ordered_path_proxy_with_m1_availability_state",
        },
        "cost_inputs": {"strict_tick_entry_spread_r": 0.012},
    }

    assert validate_decision_inputs_no_leak(decision_inputs) == []


def test_result_r_prefers_broker_real_over_proxy():
    result_r, source_field, result_class = choose_result_r(
        {
            "broker_real_net_r": -0.35,
            "source_bound_proxy_r": 1.75,
            "execution_policy_result": {"final_r": 1.25},
        }
    )

    assert result_r == -0.35
    assert source_field == "broker_real_net_r"
    assert result_class == "exact_broker_real"


def test_result_payload_keeps_label_values_out_of_decision_inputs():
    decision_inputs = build_decision_inputs(
        {
            "candidate_id": "cand1",
            "upstream_row_id": "selected1",
            "symbol": "XAUUSD",
            "feature_time_utc": "2026-01-01T00:00:00+00:00",
            "features": {
                "chosen_policy": "momentum_exhaustion",
                "framework": "ob_retest",
                "origin_family": "current_ob_retest",
                "side": "LONG",
                "source_window_complete": True,
                "m1_availability_status": "available",
                "tick_availability_status": "missing",
            },
        },
        scheduler_row={"decision": "accept"},
        strict_tick_row=None,
        spec_row={"trade_stops_level": 0, "trade_freeze_level": 0},
    )
    result_payload, result_r, source_field, result_class = build_result_payload(
        {
            "evidence_class": "m15_proxy_replay_label",
            "label_values": {
                "source_bound_proxy_r": 1.2,
                "execution_policy_result": {"final_r": 1.2, "exit_reason": "target"},
            },
        },
        scheduler_row={"decision": "accept"},
        strict_tick_row=None,
        chosen_policy="momentum_exhaustion",
    )

    assert validate_decision_inputs_no_leak(decision_inputs) == []
    assert result_payload["label_values"]["source_bound_proxy_r"] == 1.2
    assert result_r == 1.2
    assert source_field == "source_bound_proxy_r"
    assert result_class == "source_bound_proxy"


def test_metric_tracks_drawdown_profit_factor_and_loss_streak():
    metric = new_metric()
    for value in (1.0, -1.0, -1.0, 2.0, 0.0):
        add_metric(metric, value)

    closed = close_metric(metric)

    assert closed["rows"] == 5
    assert closed["known_r_rows"] == 5
    assert closed["total_r"] == 1.0
    assert closed["max_drawdown_r"] == 2.0
    assert closed["max_loss_streak"] == 2
    assert closed["profit_factor"] == 1.5


def test_friday_depth_requires_friday_microscope_source_not_calendar_friday():
    calendar_friday_feature = {
        "features": {"time_is_friday": True},
        "source_family": "lane04_microscope_timeline",
        "source_use_state": "m15_ordered_path_proxy_with_m1_availability_state",
    }
    microscope_feature = {
        "source_family": "friday_microscope_tick_bid_ask",
        "source_use_state": "friday_tick_bid_ask_exact_path_capped_at_friday_close",
    }

    assert is_friday_row(calendar_friday_feature, None) is False
    assert is_friday_row(microscope_feature, None) is True
