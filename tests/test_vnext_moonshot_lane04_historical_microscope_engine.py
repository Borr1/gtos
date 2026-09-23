from __future__ import annotations

from scripts import build_vnext_moonshot_lane04_historical_microscope_engine as lane04


def test_lane04_m15_timeline_records_missing_tick_and_cost_proof():
    row = {
        "candidate_id": "cand_test",
        "selected_row_id": "stage04_order_test",
        "symbol": "XAUUSD",
        "side": "LONG",
        "framework": "ob_retest",
        "origin_family": "current_ob_retest",
        "session_bucket": "london_broad",
        "chosen_policy": "partial_be_runner",
        "source_time_utc": "2026-01-01T09:00:00+00:00",
        "entry_time_utc": "2026-01-01T09:15:00+00:00",
        "exit_time_utc": "2026-01-01T09:45:00+00:00",
        "exit_reason": "stop_loss",
        "fill_status": "filled_in_replay",
        "final_r": -1.0,
        "mfe_r": 0.25,
        "mae_r": -1.2,
        "cost_r": None,
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
        "tick_availability_status": "local_tick_source_date_absent_after_data_ticks_search",
        "m1_availability_status": "local_m1_bar_available_for_entry_minute",
    }

    timeline = lane04.m15_timeline(row)

    assert timeline["path_class"] == "loss_sl_or_stop_policy_exit"
    assert timeline["source_use_state"] == "m15_ordered_path_proxy_with_m1_availability_state"
    assert timeline["time_to_sl_seconds"] == 1800.0
    assert any(gap["field_family"] == "ordered_bid_ask_tick_timeline" for gap in timeline["missing_field_proof"])
    assert any(event["event_type"] == "sl_touch" and event["r"] == -1.0 for event in timeline["ordered_events"])


def test_lane04_friday_timeline_preserves_tick_event_fields():
    row = {
        "candidate_id": "cand_friday",
        "trade_id": "XAUUSD_2026-05-29_london_0800",
        "symbol": "XAUUSD",
        "side": "LONG",
        "origin_family": "liquidity_sweep_reclaim",
        "framework": "ob_retest",
        "session_bucket": "london",
        "selected_policy": "partial_be_runner",
        "candle_time_utc": "2026-05-29T08:00:00+00:00",
        "entry_touch_utc": "2026-05-29T08:01:00+00:00",
        "threshold_times_utc": {"1_0r": "2026-05-29T08:10:00+00:00", "3_0r": "2026-05-29T09:00:00+00:00"},
        "threshold_seconds_from_entry": {"1_0r": 540.0},
        "partial_trigger_utc": "2026-05-29T08:10:00+00:00",
        "path_end_utc": "2026-05-29T21:00:00+00:00",
        "terminal_path_class": "winner_partial_then_dynamic_final",
        "proxy_gross_r": 3.0,
        "mfe_r_normalized": 3.1,
        "mae_r_normalized": -0.2,
        "spread_r_at_candidate": 0.04,
        "price_source": "tick_bid_ask",
        "tick_rows": 100,
    }

    timeline = lane04.friday_timeline(row)

    assert timeline["source_use_state"] == "friday_tick_bid_ask_exact_path_capped_at_friday_close"
    assert timeline["time_to_1r_seconds"] == 540.0
    assert timeline["spread_r_bucket"] == "spread_r_lt_0_05"
    assert any(event["event_type"] == "dynamic_final_3r" for event in timeline["ordered_events"])


