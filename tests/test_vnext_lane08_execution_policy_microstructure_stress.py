from datetime import datetime, timedelta, timezone

from scripts import build_vnext_lane08_execution_policy_microstructure_stress as lane08


def test_lane08_microstructure_classification_rejects_same_bar_proxy():
    row = {
        "same_bar_ambiguity": True,
        "ordered_path_status": "same_bar_ambiguous_in_m15_replay_live_m1_tick_capture_required",
        "tick_availability_status": "local_tick_parquet_available_for_entry_date",
        "m1_availability_status": "local_m1_bar_available_for_entry_minute",
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
    }

    assert lane08.classify_microstructure(row) == (
        "same_bar_ambiguous_requires_tick_path_replay"
    )


def test_lane08_microstructure_classification_keeps_tick_cost_gap_explicit():
    row = {
        "same_bar_ambiguity": False,
        "ordered_path_status": "ordered_path_not_ambiguous_in_m15_replay",
        "tick_availability_status": "local_tick_parquet_available_for_entry_date",
        "m1_availability_status": "local_m1_bar_available_for_entry_minute",
        "cost_status": "missing_historical_live_cost_lifecycle_fields",
    }

    assert lane08.classify_microstructure(row) == (
        "strict_tick_path_available_cost_lifecycle_missing"
    )


def test_lane08_metric_tracks_drawdown_and_loss_streak():
    metric = lane08.new_metric()
    for value in (1.0, -1.0, -1.0, 0.5):
        lane08.add_metric(metric, value)

    closed = lane08.close_metric(metric)
    assert closed["rows"] == 4
    assert closed["total_r"] == -0.5
    assert closed["max_loss_streak"] == 2
    assert closed["max_drawdown_r"] == 2.0


def test_lane08_strict_tick_policy_orders_stop_before_later_target():
    start = datetime(2026, 5, 29, 12, tzinfo=timezone.utc)
    path = [
        (start, 0.2),
        (start + timedelta(seconds=1), -1.05),
        (start + timedelta(seconds=2), 2.0),
    ]

    fixed = lane08.simulate_tick_fixed(path)

    assert fixed["gross_r"] == -1.0
    assert fixed["exit_reason"] == "stop_loss"


def test_lane08_strict_tick_momentum_exits_on_ordered_pullback():
    start = datetime(2026, 5, 29, 12, tzinfo=timezone.utc)
    path = [
        (start, 0.2),
        (start + timedelta(seconds=1), 1.3),
        (start + timedelta(seconds=2), 0.85),
    ]

    momentum = lane08.simulate_tick_momentum(path)

    assert momentum["exit_reason"] == "momentum_exhaustion_pullback"
    assert momentum["gross_r"] == 0.9
