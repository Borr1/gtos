from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from scripts import build_vnext_weekend_execution_policy_tournament as mod


def _tick_frame(rows):
    return pd.DataFrame(
        [
            {
                "ts_utc": pd.Timestamp(ts),
                "ts_msc": int(pd.Timestamp(ts).timestamp() * 1000),
                "bid": bid,
                "ask": ask,
            }
            for ts, bid, ask in rows
        ]
    )


def _candidate(side="LONG", entry=100.0, stop=99.0):
    return {
        "candidate_id": "c1",
        "trade_id": "t1",
        "symbol": "XAUUSD",
        "broker_symbol": "XAUUSD",
        "side": side,
        "route_session": "ny",
        "origin_family": "displacement_continuation",
        "framework": "origin_displacement_continuation",
        "candle_time_utc": "2026-05-28T00:00:00+00:00",
        "final_outcome": "SKIPPED_GTOS_VNEXT_BROADER_ORIGIN_DYNAMIC",
        "selected_policy": "partial_be_runner",
        "execution_policy_id": "vnext_exec_partial_50_at_1r_be_runner_to_3r",
        "repaired_entry": entry,
        "repaired_stop_loss": stop,
        "risk_distance": abs(entry - stop),
        "broker_spec_snapshot": {
            "point": 0.01,
            "trade_stops_level": 0,
            "trade_freeze_level": 0,
            "broker_min_stop_distance": 0.0,
        },
        "_ledger_source_path": "ledger.jsonl",
        "_ledger_source_line": 1,
    }


def test_long_limit_fill_uses_ask_and_exit_uses_bid():
    row = _candidate("LONG", 100.0, 99.0)
    ticks = _tick_frame(
        [
            ("2026-05-28T00:00:01+00:00", 100.20, 100.40),
            ("2026-05-28T00:00:02+00:00", 99.90, 100.00),
            ("2026-05-28T00:00:03+00:00", 101.55, 101.75),
        ]
    )
    out = mod.simulate_tick_policy(row, ticks, mod.policy_by_name("fixed_1_5r_comparator"))
    assert out["entry_touch_utc"] == "2026-05-28T00:00:02+00:00"
    assert out["execution_result"] == "fixed_target_hit"
    assert out["gross_r"] == 1.5


def test_short_limit_fill_uses_bid_and_exit_uses_ask():
    row = _candidate("SHORT", 100.0, 101.0)
    ticks = _tick_frame(
        [
            ("2026-05-28T00:00:01+00:00", 99.80, 100.00),
            ("2026-05-28T00:00:02+00:00", 100.00, 100.20),
            ("2026-05-28T00:00:03+00:00", 98.30, 98.50),
        ]
    )
    out = mod.simulate_tick_policy(row, ticks, mod.policy_by_name("fixed_1_5r_comparator"))
    assert out["entry_touch_utc"] == "2026-05-28T00:00:02+00:00"
    assert out["execution_result"] == "fixed_target_hit"
    assert out["gross_r"] == 1.5


def test_trailing_moves_stop_and_exits_on_tick_order():
    row = _candidate("LONG", 100.0, 99.0)
    ticks = _tick_frame(
        [
            ("2026-05-28T00:00:01+00:00", 99.95, 100.00),
            ("2026-05-28T00:00:02+00:00", 101.20, 101.30),
            ("2026-05-28T00:00:03+00:00", 100.60, 100.70),
        ]
    )
    out = mod.simulate_tick_policy(row, ticks, mod.policy_by_name("trailing_1r_gap_0_5_no_cap"))
    assert out["execution_result"] == "stop_hit"
    assert round(out["gross_r"], 6) == 0.7
    assert out["stop_modify_attempts"] >= 1


def test_broker_stop_distance_reject_keeps_previous_stop():
    row = _candidate("LONG", 100.0, 99.0)
    row["broker_spec_snapshot"]["broker_min_stop_distance"] = 10.0
    ticks = _tick_frame(
        [
            ("2026-05-28T00:00:01+00:00", 99.95, 100.00),
            ("2026-05-28T00:00:02+00:00", 101.20, 101.30),
            ("2026-05-28T00:00:03+00:00", 99.50, 99.60),
            ("2026-05-28T00:00:04+00:00", 98.90, 99.00),
        ]
    )
    out = mod.simulate_tick_policy(row, ticks, mod.policy_by_name("trailing_1r_gap_0_5_no_cap"))
    assert out["stop_modify_rejections"] >= 1
    assert out["execution_result"] == "stop_hit"
    assert out["gross_r"] == -1.0


def test_m1_same_bar_ambiguity_is_flagged_conservative():
    row = _candidate("LONG", 100.0, 99.0)
    bars = [
        mod.anatomy.Bar(
            time_utc=datetime(2026, 5, 28, 0, 0, tzinfo=timezone.utc),
            open=100.0,
            high=101.5,
            low=98.8,
            close=100.5,
        )
    ]
    out = mod.simulate_m1_policy(row, bars, mod.policy_by_name("be_after_trigger_comparator"))
    assert out["price_source"] == "m1_ohlc"
    assert out["m1_same_bar_ambiguity"] is True
    assert out["execution_result"] == "stop_hit_conservative_m1"
    assert out["gross_r"] == -1.0


def test_quality_bucket_marks_london_positive_subset_tradeable():
    row = _candidate("LONG", 100.0, 99.0)
    row.update(
        {
            "route_session": "london",
            "origin_family": "liquidity_sweep_reclaim",
            "final_outcome": "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN",
            "spread_r_at_candidate": 0.05,
            "mfe_r": 2.0,
            "mae_r": -0.2,
            "time_to_mfe_seconds": 600,
            "time_to_mae_seconds": 1200,
            "price_source": "tick_bid_ask",
        }
    )
    policy_rows = [
        {
            "comparison_policy": "current_selected_policy",
            "gross_r": 1.0,
            "execution_result": "partial_then_final_target",
            "price_source": "tick_bid_ask",
        },
        {"comparison_policy": "trailing_1r_gap_0_5_cap_3r", "gross_r": 0.5},
    ]

    quality = mod.quality_bucket(row, policy_rows)

    assert quality["quality_classification"] == "tradeable_now"
    assert "weekend_london_liquidity_sweep_reclaim_positive_current_selected" in quality["quality_reasons"]
    assert quality["mfe_before_mae"] is True


def test_quality_bucket_blocks_high_spread_even_in_positive_subset():
    row = _candidate("LONG", 100.0, 99.0)
    row.update(
        {
            "route_session": "london",
            "origin_family": "liquidity_sweep_reclaim",
            "final_outcome": "LIMIT_PLACED_GTOS_VNEXT_BROADER_ORIGIN",
            "spread_r_at_candidate": 0.35,
            "price_source": "tick_bid_ask",
        }
    )
    quality = mod.quality_bucket(
        row,
        [
            {"comparison_policy": "current_selected_policy", "gross_r": 1.0, "execution_result": "partial_then_final_target"},
            {"comparison_policy": "trailing_1r_gap_0_5_cap_3r", "gross_r": 0.5},
        ],
    )

    assert quality["quality_classification"] == "no_trade_by_evidence"
    assert "spread_r_at_candidate_ge_0_30" in quality["quality_reasons"]
