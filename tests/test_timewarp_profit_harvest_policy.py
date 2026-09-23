from __future__ import annotations

from src.research_infra import v4_timewarp_simulated_live_research_loop as timewarp


def test_profit_harvest_min_hold_defers_early_stop_raise_and_preserves_original_path() -> None:
    candidate = {
        "side": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "dynamic_geometry_policy": "momentum_exhaustion",
    }
    oracle = {
        "fill_status": "filled",
        "fill_time_utc": "2025-06-11T08:15:00+00:00",
        "source": "m1",
        "target_r": 2.0,
    }
    rows = [
        {"time_utc": "2025-06-11T08:20:00+00:00", "high": 100.65, "low": 100.42, "close": 100.52},
        {"time_utc": "2025-06-11T08:25:00+00:00", "high": 100.66, "low": 100.20, "close": 100.35},
        {"time_utc": "2025-06-11T08:30:00+00:00", "high": 100.70, "low": 100.22, "close": 100.51},
    ]
    config = {
        "gtos_vnext_runtime": {
            "profit_harvest_mfe_capture_v4_enabled": True,
            "profit_harvest_mfe_capture_v4_require_vnext_dynamic_policy": True,
            "profit_harvest_mfe_capture_v4_min_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_stop_activation_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_target_activation_fraction": 0.25,
            "profit_harvest_mfe_capture_v4_trail_gap_r": 0.35,
            "profit_harvest_mfe_capture_v4_protect_floor_r": 0.0,
            "profit_harvest_mfe_capture_v4_close_on_giveback_r": 0.50,
            "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise": 30,
        }
    }

    final_r, close_reason, target_r, replay_exit = timewarp.apply_profit_harvest_replay_exit(
        oracle=oracle,
        rows=rows,
        candidate=candidate,
        config=config,
        packets={"geometry_contract": {"selected_policy": "momentum_exhaustion"}, "cost_r": 0.05},
        final_r=0.51,
        close_reason="time_stop_close_mark_from_m1",
        target_r=2.0,
    )

    assert replay_exit is None
    assert final_r == 0.51
    assert close_reason == "time_stop_close_mark_from_m1"
    assert target_r == 2.0
    assert "profit_harvest_mfe_capture_replay_exit" not in oracle


def test_profit_harvest_records_original_exit_opportunity_cost_when_replay_overrides() -> None:
    candidate = {
        "side": "LONG",
        "entry_price": 100.0,
        "stop_loss": 99.0,
        "dynamic_geometry_policy": "momentum_exhaustion",
    }
    oracle = {
        "fill_status": "filled",
        "fill_time_utc": "2025-06-11T08:15:00+00:00",
        "source": "tick",
        "ordered_tick_truth_satisfied": True,
        "target_r": 2.0,
    }
    rows = [
        {"time_utc": "2025-06-11T08:50:00+00:00", "bid": 100.70, "ask": 100.90},
        {"time_utc": "2025-06-11T08:55:00+00:00", "bid": 100.20, "ask": 100.40},
    ]
    config = {
        "gtos_vnext_runtime": {
            "profit_harvest_mfe_capture_v4_enabled": True,
            "profit_harvest_mfe_capture_v4_require_vnext_dynamic_policy": True,
            "profit_harvest_mfe_capture_v4_min_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_stop_activation_mfe_r": 0.50,
            "profit_harvest_mfe_capture_v4_target_activation_fraction": 0.25,
            "profit_harvest_mfe_capture_v4_trail_gap_r": 0.35,
            "profit_harvest_mfe_capture_v4_protect_floor_r": 0.0,
            "profit_harvest_mfe_capture_v4_close_on_giveback_r": 0.50,
            "profit_harvest_mfe_capture_v4_min_hold_minutes_before_stop_raise": 30,
        }
    }

    final_r, close_reason, _, replay_exit = timewarp.apply_profit_harvest_replay_exit(
        oracle=oracle,
        rows=rows,
        candidate=candidate,
        config=config,
        packets={"geometry_contract": {"selected_policy": "momentum_exhaustion"}, "cost_r": 0.05},
        final_r=0.60,
        close_reason="time_stop_close_mark_from_m1",
        target_r=2.0,
    )

    assert replay_exit is not None
    assert close_reason == "profit_harvest_mfe_capture_v4_replay_protective_stop"
    assert final_r == 0.35
    assert replay_exit["final_r_authority"] is True
    assert replay_exit["final_r_authority_status"] == "ordered_tick_truth_final_r_authority"
    assert replay_exit["original_final_r"] == 0.60
    assert replay_exit["original_net_r"] == 0.55
    assert replay_exit["lost_original_exit_net_r"] == 0.25
    assert oracle["profit_harvest_lost_original_exit_net_r"] == 0.25
