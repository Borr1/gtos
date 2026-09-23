import pytest

from src.components.exit_policy_v4 import (
    ExitPolicyConfigV4,
    ExitPolicyInputV4,
    evaluate_exit_policy_v4,
)


def base_row(**overrides):
    row = {
        "ticket": 123,
        "symbol": "XAUUSD",
        "direction": "LONG",
        "entry_time_utc": "2026-06-02T10:00:00+00:00",
        "bars_elapsed": 4,
        "current_progress_r": 0.2,
        "mfe_r": 0.4,
        "mae_r": -0.1,
        "current_stop_r": -1.0,
        "partial_closed": False,
        "sl_at_breakeven": False,
        "current_volume": 0.1,
        "initial_volume": 0.1,
        "partial_close_allowed": True,
        "ticket_bound_state": True,
        "broker_position_confirmed": True,
        "path_source_status": "live_tick_current_price_source_bound",
        "clock_source_status": "current_candle.time_utc",
        "lifecycle_source_status": "broker_position_confirmed_ticket_bound",
    }
    row.update(overrides)
    return ExitPolicyInputV4(**row)


def config(**overrides):
    data = {
        "enabled": True,
        "apply_to_execution": True,
    }
    data.update(overrides)
    return ExitPolicyConfigV4(**data)


def test_source_gap_holds_fail_closed_without_inventing_action():
    decision = evaluate_exit_policy_v4(
        config(),
        base_row(ticket=None, broker_position_confirmed=False),
    )

    assert decision.action == "HOLD"
    assert decision.status == "source_gap_fail_closed"
    assert "missing_ticket" in decision.source_gaps
    assert "broker_position_not_confirmed" in decision.source_gaps


def test_partial_close_precedes_be_when_allowed_and_trigger_reached():
    decision = evaluate_exit_policy_v4(
        config(partial_trigger_r=1.0, be_trigger_r=1.0),
        base_row(current_progress_r=1.05, mfe_r=1.05, partial_close_allowed=True),
    )

    assert decision.action == "PARTIAL_CLOSE_TO_BE"
    assert decision.partial_close_ratio == 0.5


def test_partial_close_uses_mfe_trigger_not_only_terminal_progress():
    decision = evaluate_exit_policy_v4(
        config(partial_trigger_r=1.0, be_trigger_r=1.0, giveback_close_r=0.65),
        base_row(current_progress_r=0.7, mfe_r=1.1, partial_close_allowed=True),
    )

    assert decision.action == "PARTIAL_CLOSE_TO_BE"
    assert decision.reason == "partial_trigger_reached_before_full_target"


def test_move_stop_to_be_when_initial_risk_should_be_released():
    decision = evaluate_exit_policy_v4(
        config(be_trigger_r=1.0),
        base_row(
            current_progress_r=0.8,
            mfe_r=1.1,
            partial_close_allowed=False,
            sl_at_breakeven=False,
        ),
    )

    assert decision.action == "MOVE_STOP_TO_BE"
    assert decision.target_stop_r == 0.0


def test_trailing_stop_raises_only_when_it_improves_current_stop():
    decision = evaluate_exit_policy_v4(
        config(trailing_trigger_r=1.0, trailing_gap_r=0.4),
        base_row(
            partial_closed=True,
            sl_at_breakeven=True,
            current_progress_r=1.1,
            mfe_r=1.4,
            current_stop_r=0.5,
        ),
    )

    assert decision.action == "RAISE_TRAILING_STOP"
    assert decision.target_stop_r == pytest.approx(1.0)


def test_stale_thesis_closes_after_no_progress_and_adverse_path():
    decision = evaluate_exit_policy_v4(
        config(stale_thesis_bars=12, stale_min_mfe_r=0.35, stale_adverse_r=-0.25),
        base_row(
            bars_elapsed=12,
            current_progress_r=-0.1,
            mfe_r=0.2,
            mae_r=-0.4,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_STALE_THESIS"
    assert decision.close_reason == "v4_stale_thesis_no_progress"


def test_opportunity_cost_closes_stale_hold_when_source_bound():
    decision = evaluate_exit_policy_v4(
        config(opportunity_cost_close_r=1.0, opportunity_cost_min_bars=4),
        base_row(
            bars_elapsed=8,
            current_progress_r=0.1,
            mfe_r=0.3,
            mae_r=-0.1,
            partial_close_allowed=False,
            opportunity_cost_r=1.4,
            competing_candidate_ev_r=0.9,
            opportunity_cost_source_status="opportunity_cost_replay_bound",
        ),
    )

    assert decision.action == "CLOSE_STALE_THESIS"
    assert decision.reason == "opportunity_cost_or_scheduler_regret_dominates_stale_hold"
    assert decision.close_reason == "v4_stale_thesis_opportunity_cost_close"


def test_scheduler_regret_closes_stale_hold_when_source_bound():
    decision = evaluate_exit_policy_v4(
        config(scheduler_regret_close_r=0.75, opportunity_cost_min_bars=4),
        base_row(
            bars_elapsed=6,
            current_progress_r=0.2,
            mfe_r=0.25,
            mae_r=-0.2,
            partial_close_allowed=False,
            scheduler_regret_r=0.9,
            scheduler_regret_source_status="scheduler_regret_replay_bound",
        ),
    )

    assert decision.action == "CLOSE_STALE_THESIS"
    assert decision.close_reason == "v4_stale_thesis_opportunity_cost_close"


def test_opportunity_cost_without_source_proof_fails_closed():
    decision = evaluate_exit_policy_v4(
        config(opportunity_cost_close_r=1.0),
        base_row(
            bars_elapsed=8,
            current_progress_r=0.1,
            mfe_r=0.3,
            partial_close_allowed=False,
            opportunity_cost_r=1.4,
        ),
    )

    assert decision.action == "HOLD"
    assert decision.status == "source_gap_fail_closed"
    assert "opportunity_cost_source_missing" in decision.source_gaps


def test_meaningful_giveback_closes_before_time_stop():
    decision = evaluate_exit_policy_v4(
        config(giveback_trigger_r=1.0, giveback_close_r=0.5, time_stop_bars=32),
        base_row(
            bars_elapsed=40,
            current_progress_r=0.4,
            mfe_r=1.2,
            mae_r=-0.2,
            partial_closed=True,
            sl_at_breakeven=True,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_GIVEBACK"
    assert decision.close_reason == "v4_profit_giveback_exit"


def test_time_stop_closes_when_max_hold_bars_elapsed():
    decision = evaluate_exit_policy_v4(
        config(time_stop_bars=3),
        base_row(
            bars_elapsed=3,
            current_progress_r=0.45,
            mfe_r=0.5,
            mae_r=-0.1,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_TIME_STOP"
    assert decision.close_reason == "v4_time_stop"
