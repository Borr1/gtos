import pytest

from src.research.dynamic_execution_policy import (
    PathObservation,
    ai_target_policy,
    be_only_policy,
    early_cut_policy,
    legacy_fixed_target_policy,
    live_current_j46_j49_policy,
    momentum_exhaustion_policy,
    observation_from_ohlc,
    partial_be_policy,
    path_aware_runner_policy,
    profit_harvest_mfe_capture_v4_policy,
    required_policy_manifest,
    simulate_policy,
    time_stop_policy,
    trailing_policy,
)


def obs(index, high, low, close=None):
    return PathObservation(
        index=index,
        high_r=high,
        low_r=low,
        close_r=high if close is None else close,
        time_utc=f"2026-05-26T00:{index:02d}:00Z",
    )


def test_legacy_fixed_target_closes_at_configured_r():
    result = simulate_policy(
        legacy_fixed_target_policy(1.5),
        [obs(1, high=0.7, low=-0.2), obs(2, high=1.6, low=0.1)],
    )

    assert result.exit_reason == "final_target"
    assert result.final_r == 1.5
    assert result.exit_index == 2


def test_live_current_j46_j49_moves_to_be_then_closes_at_be():
    result = simulate_policy(
        live_current_j46_j49_policy(),
        [
            obs(1, high=3.2, low=-0.4, close=3.0),
            obs(2, high=3.4, low=-0.1, close=0.2),
        ],
    )

    assert result.exit_reason == "breakeven_stop"
    assert result.final_r == 0.0
    assert result.transitions[0]["event"] == "tp1"
    assert result.transitions[0]["stop_moved_to_r"] == 0.0


def test_live_current_j46_j49_reaches_higher_target():
    result = simulate_policy(
        live_current_j46_j49_policy(),
        [
            obs(1, high=3.1, low=-0.2, close=2.8),
            obs(2, high=6.2, low=2.4, close=6.0),
        ],
    )

    assert result.exit_reason == "final_target"
    assert result.final_r == 6.0
    assert result.remaining_fraction == 1.0


def test_live_current_j46_j49_time_stop_marks_to_market_after_twelve_bars():
    observations = [obs(i, high=2.0, low=-0.5, close=0.25) for i in range(1, 13)]

    result = simulate_policy(live_current_j46_j49_policy(), observations)

    assert result.exit_reason == "time_stop"
    assert result.exit_index == 12
    assert result.final_r == 0.25


def test_partial_be_policy_blends_partial_and_runner_r():
    result = simulate_policy(
        partial_be_policy(tp1_r=1.0, final_target_r=3.0, partial_close_ratio=0.5),
        [obs(1, high=1.2, low=-0.2), obs(2, high=3.1, low=0.4)],
    )

    assert result.exit_reason == "final_target"
    assert result.partial_realized_r == 0.5
    assert result.remaining_fraction == 0.5
    assert result.final_r == 2.0


def test_be_only_policy_turns_late_stop_into_zero_r():
    result = simulate_policy(
        be_only_policy(trigger_r=1.0, final_target_r=2.0),
        [obs(1, high=1.1, low=-0.3), obs(2, high=1.2, low=-0.05, close=0.1)],
    )

    assert result.exit_reason == "breakeven_stop"
    assert result.final_r == 0.0


def test_trailing_policy_raises_stop_and_exits_on_trail():
    result = simulate_policy(
        trailing_policy(trigger_r=2.0, gap_r=0.75, final_target_r=None),
        [obs(1, high=2.3, low=1.6, close=2.0), obs(2, high=2.4, low=1.6, close=1.6)],
    )

    assert result.exit_reason == "trailing_stop"
    assert result.final_r == 1.65
    assert result.same_bar_ambiguity is True


def test_momentum_exhaustion_closes_on_pullback_after_trigger():
    result = simulate_policy(
        momentum_exhaustion_policy(trigger_r=1.0, pullback_r=0.4, final_target_r=2.0),
        [obs(1, high=1.3, low=1.0, close=1.2), obs(2, high=1.35, low=0.8, close=0.9)],
    )

    assert result.exit_reason == "giveback_close"
    assert result.final_r == pytest.approx(0.95)
    assert result.policy_name == "momentum_exhaustion"


def test_momentum_exhaustion_keeps_final_target_cap():
    result = simulate_policy(
        momentum_exhaustion_policy(trigger_r=1.0, pullback_r=0.4, final_target_r=2.0),
        [obs(1, high=2.1, low=1.2, close=2.0)],
    )

    assert result.exit_reason == "final_target"
    assert result.final_r == 2.0


def test_time_stop_policy_can_run_without_static_target():
    result = simulate_policy(
        time_stop_policy(bars=3, final_target_r=None),
        [obs(1, high=0.1, low=-0.1, close=0.0), obs(2, 0.3, -0.2, 0.2), obs(3, 0.4, -0.2, 0.35)],
    )

    assert result.exit_reason == "time_stop"
    assert result.final_r == 0.35


def test_early_cut_policy_closes_when_path_makes_no_progress():
    result = simulate_policy(
        early_cut_policy(bars=3, min_mfe_r=0.5, final_target_r=1.5),
        [obs(1, 0.1, -0.1, 0.0), obs(2, 0.2, -0.2, 0.1), obs(3, 0.3, -0.2, -0.05)],
    )

    assert result.exit_reason == "early_cut_no_progress"
    assert result.final_r == -0.05


def test_path_aware_runner_uses_nearest_source_bound_target():
    policy = path_aware_runner_policy(
        structural_target_r=4.0,
        liquidity_target_r=2.5,
        atr_expansion_target_r=5.0,
    )

    result = simulate_policy(policy, [obs(1, 2.6, -0.2)])

    assert policy.final_target_r == 2.5
    assert result.exit_reason == "final_target"
    assert result.final_r == 2.5


def test_same_bar_policy_can_return_ambiguous_instead_of_fake_ordering():
    result = simulate_policy(
        legacy_fixed_target_policy(1.5),
        [obs(1, high=1.6, low=-1.1, close=0.0)],
        same_bar_policy="ambiguous",
    )

    assert result.replay_status == "ambiguous"
    assert result.exit_reason == "same_bar_stop_and_profit_trigger_ambiguous"
    assert result.same_bar_ambiguity is True


def test_empty_path_is_not_replayable_source_gap():
    result = simulate_policy(legacy_fixed_target_policy(1.5), [])

    assert result.replay_status == "not_replayable"
    assert result.source_gap_reason == "no_path_observations"
    assert result.final_r is None


def test_observation_from_ohlc_side_normalizes_long_and_short():
    long_obs = observation_from_ohlc(
        index=1,
        row={"open": 100.0, "high": 103.0, "low": 99.0, "close": 102.0},
        entry=100.0,
        stop=99.0,
        side="LONG",
    )
    short_obs = observation_from_ohlc(
        index=1,
        row={"open": 100.0, "high": 101.0, "low": 97.0, "close": 98.0},
        entry=100.0,
        stop=101.0,
        side="SHORT",
    )

    assert long_obs.high_r == 3.0
    assert long_obs.low_r == -1.0
    assert short_obs.high_r == 3.0
    assert short_obs.low_r == -1.0


def test_required_manifest_contains_moonshot_policy_families():
    names = {policy.name for policy in required_policy_manifest()}

    assert "live_current_j46_j49" in names
    assert "legacy_fixed_1.5r" in names
    assert "ai_target" in names
    assert "partial_be_runner" in names
    assert "be_after_trigger" in names
    assert "momentum_exhaustion" in names
    assert "trailing_runner" in names
    assert "time_stop_only" in names
    assert "early_cut_if_no_progress" in names
    assert "profit_harvest_mfe_capture_v4" in names
    assert "path_aware_runner" in names


def test_ai_target_policy_accepts_non_legacy_target_r():
    result = simulate_policy(ai_target_policy(2.25), [obs(1, 2.3, -0.2)])

    assert result.exit_reason == "final_target"
    assert result.final_r == 2.25


def test_profit_harvest_v4_micro_partial_and_runner_target():
    result = simulate_policy(
        profit_harvest_mfe_capture_v4_policy(
            min_mfe_r=0.25,
            micro_partial_trigger_r=0.5,
            micro_partial_close_ratio=0.33,
            trail_gap_r=0.75,
            giveback_close_r=1.0,
            final_target_r=2.0,
        ),
        [obs(1, high=0.55, low=-0.10), obs(2, high=2.1, low=0.40)],
    )

    assert result.exit_reason == "final_target"
    assert result.partial_realized_r == pytest.approx(0.165)
    assert result.remaining_fraction == pytest.approx(0.67)
    assert result.final_r == pytest.approx(1.505)
    assert result.transitions[0]["event"] == "tp1"


def test_profit_harvest_v4_giveback_closes_source_bound_path():
    result = simulate_policy(
        profit_harvest_mfe_capture_v4_policy(
            min_mfe_r=0.25,
            micro_partial_trigger_r=0.9,
            micro_partial_close_ratio=0.0,
            trail_gap_r=1.0,
            giveback_close_r=0.5,
            final_target_r=2.0,
        ),
        [obs(1, high=0.75, low=0.20, close=0.25)],
    )

    assert result.exit_reason == "giveback_close"
    assert result.final_r == pytest.approx(0.25)
    assert result.same_bar_ambiguity is True
    assert result.transitions[-1]["event"] == "giveback_close"


def test_profit_harvest_v4_stale_thesis_close():
    result = simulate_policy(
        profit_harvest_mfe_capture_v4_policy(
            min_mfe_r=0.25,
            micro_partial_trigger_r=0.9,
            micro_partial_close_ratio=0.0,
            trail_gap_r=1.0,
            giveback_close_r=2.0,
            stale_thesis_bars=3,
            stale_thesis_min_mfe_r=0.25,
            stale_thesis_close_below_r=0.0,
            final_target_r=2.0,
        ),
        [
            obs(1, high=0.30, low=-0.10, close=0.20),
            obs(2, high=0.25, low=-0.05, close=0.10),
            obs(3, high=0.20, low=-0.20, close=-0.05),
        ],
    )

    assert result.exit_reason == "stale_thesis_close"
    assert result.final_r == pytest.approx(-0.05)
    assert result.transitions[-1]["event"] == "stale_thesis_close"
