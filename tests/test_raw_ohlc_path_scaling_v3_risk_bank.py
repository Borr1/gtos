from __future__ import annotations

from datetime import datetime, timezone

from scripts import analyze_raw_ohlc_path_scaling_v2_confluence as v2
from scripts import analyze_raw_ohlc_path_scaling_v3_exploratory as mod
from scripts.build_raw_ohlc_prefill_delivery_path import PathIndex


def _dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc)


def _bar(time: str, open_: float, high: float, low: float, close: float) -> dict:
    return {"time": _dt(time), "open": open_, "high": high, "low": low, "close": close}


def test_initial_leg_stopped_exactly_minus_one_r_is_valid_floor():
    assert mod.aggregate_worst_case_r(
        realized_closed_leg_r=-1.0,
        open_leg_stop_if_hit_rs=[],
        estimated_remaining_cost_r=0.0,
    ) == -1.0


def test_locked_profit_accepts_full_reentry_and_costs_accumulate():
    plan = mod.plan_new_leg(
        realized_closed_leg_r=0.95,
        existing_open_stop_rs=[],
        new_leg_stop_if_hit_r_per_full_size=-0.5,
        estimated_remaining_cost_r=0.05,
        requested_size=1.0,
    )

    assert plan.status == "ACCEPTED_FULL_SIZE"
    assert plan.aggregate_worst_case_after >= -1.0
    assert mod.completed_leg_cost(3, 0.05) == 0.15


def test_same_size_reentry_resizes_when_full_size_breaks_bank():
    plan = mod.plan_new_leg(
        realized_closed_leg_r=-0.8,
        existing_open_stop_rs=[],
        new_leg_stop_if_hit_r_per_full_size=-0.5,
        estimated_remaining_cost_r=0.0,
        requested_size=1.0,
    )

    assert plan.status == "ACCEPTED_RESIZED"
    assert 0.0 < plan.accepted_size < 1.0
    assert plan.aggregate_worst_case_after >= -1.0


def test_multiple_reentries_cannot_silently_exceed_risk_bank():
    first = mod.plan_new_leg(
        realized_closed_leg_r=0.0,
        existing_open_stop_rs=[],
        new_leg_stop_if_hit_r_per_full_size=-0.8,
        estimated_remaining_cost_r=0.0,
        requested_size=1.0,
    )
    second = mod.plan_new_leg(
        realized_closed_leg_r=0.0,
        existing_open_stop_rs=[-0.8 * first.accepted_size],
        new_leg_stop_if_hit_r_per_full_size=-0.8,
        estimated_remaining_cost_r=0.0,
        requested_size=1.0,
    )

    assert first.status == "ACCEPTED_FULL_SIZE"
    assert second.status == "ACCEPTED_RESIZED"
    assert second.aggregate_worst_case_after >= -1.0


def test_unfilled_pending_does_not_change_realized_r():
    assert mod.finalized_unfilled_pending(0.45) == 0.45


def test_same_bar_fill_stop_target_is_ambiguous_not_guessed():
    row = mod.classify_same_row_fill_exit(
        side="LONG",
        fill_price=101.0,
        stop_price=100.0,
        target_price=104.0,
        high=105.0,
        low=99.0,
    )

    assert row["ambiguous"] is True
    assert row["status"] == "AMBIGUOUS_FILL_EXIT_SAME_ROW"


def _lock(selector: str, time: str, floor_r: float, price: float) -> dict:
    return {
        "selector_id": selector,
        "event_type": selector.lower(),
        "confirmed_time": time,
        "source_time": time,
        "confirmed_index": 1,
        "source_index": 1,
        "floor_r": floor_r,
        "price": price,
    }


def _row(variant: str, net_r: float, *, locks: list[dict] | None = None) -> dict:
    return {
        "event_key": "XAUUSD|2026-01-01T00:00:00+00:00",
        "variant_id": variant,
        "symbol": "XAUUSD",
        "session": "ny",
        "mechanical_side": "LONG",
        "mechanical_entry": 100.0,
        "mechanical_sl": 95.0,
        "mechanical_tp": 130.0,
        "candle_close_utc": "2026-01-01T00:00:00+00:00",
        "raw_cohort_key": "XAUUSD|ny|bullish|D1",
        "role": "dominance_watchlist",
        "selected_timeframe": "M1",
        "outcome": "TIMEOUT",
        "locks_triggered": locks or [],
        "net_r_by_cost": {"0.05": net_r},
    }


def test_replay_preserves_label_separation_and_unfilled_pending():
    ob_lock = _lock("OB_PROTECTIVE_BOUNDARY", "2026-01-01T00:01:00+00:00", 0.5, 102.5)
    rows = {
        v2.BASELINE: _row(v2.BASELINE, 0.2),
        v2.SWING: _row(v2.SWING, 0.2),
        v2.FVG: _row(v2.FVG, 0.3),
        v2.OB: _row(v2.OB, 0.8, locks=[ob_lock]),
        v2.COMPOSITE: _row(v2.COMPOSITE, 0.7, locks=[ob_lock]),
    }
    indexes = {
        ("XAUUSD", "M1"): PathIndex(
            "XAUUSD",
            "M1",
            [
                _bar("2026-01-01T00:02:00+00:00", 103.0, 104.0, 103.0, 103.5),
                _bar("2026-01-01T00:03:00+00:00", 103.5, 104.5, 103.1, 104.0),
            ],
        )
    }
    variant = {"variant_id": "V3_OB_LOCK_PULLBACK_RISK_BANK", "structural_lock_source": v2.OB}

    record = mod.replay_variant_event(
        variant=variant,
        event_key="event",
        rows=rows,
        indexes=indexes,
        cost_key="0.05",
        cost_r=0.05,
        hold_bars=12,
    )

    assert record["actual_broker_r"] is None
    assert record["j46_path_synthetic_r"] == 0.2
    assert record["fill_status"] == "UNFILLED_REENTRY_PENDING"
    assert record["path_synthetic_r"] == record["initial_closed_net_r"]
    assert record["label_policy"] == "actual broker R is never overwritten by V3 path_synthetic_r"
