"""Exit Policy V4 early-loss-abort actions.

Covers the TIGHTEN_STOP_LOSS_ABORT / CLOSE_EARLY_LOSS_ABORT ladder slot
(after stale-thesis/giveback closes, before any profit-protection action),
the default-disabled abort config fields, runtime-key parsing, and the
``from_policy_params`` per-trade overlay for the future per-segment table.
"""

import pytest

from src.components.exit_policy_v4 import (
    ExitPolicyConfigV4,
    ExitPolicyInputV4,
    evaluate_exit_policy_v4,
)

ABORT_ACTIONS = {"TIGHTEN_STOP_LOSS_ABORT", "CLOSE_EARLY_LOSS_ABORT"}


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


# ---------------------------------------------------------------------------
# Default-off behavior.
# ---------------------------------------------------------------------------


def test_default_config_has_all_abort_fields_disabled():
    cfg = ExitPolicyConfigV4()

    assert cfg.abort_adverse_r is None
    assert cfg.abort_adverse_max_mfe_r is None
    assert cfg.abort_stop_r is None
    assert cfg.abort_no_progress_bars is None
    assert cfg.abort_min_mfe_r is None
    assert cfg.abort_close_below_r is None
    assert cfg.abort_consecutive_bars is None


def test_from_runtime_config_defaults_abort_fields_to_none():
    cfg = ExitPolicyConfigV4.from_runtime_config({})

    assert cfg.abort_adverse_r is None
    assert cfg.abort_adverse_max_mfe_r is None
    assert cfg.abort_stop_r is None
    assert cfg.abort_no_progress_bars is None
    assert cfg.abort_min_mfe_r is None
    assert cfg.abort_close_below_r is None
    assert cfg.abort_consecutive_bars is None


def test_disabled_abort_config_emits_no_abort_actions_on_deep_adverse_row():
    decision = evaluate_exit_policy_v4(
        config(),
        base_row(
            bars_elapsed=8,
            current_progress_r=-0.5,
            mfe_r=0.05,
            mae_r=-0.6,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "HOLD"
    assert decision.action not in ABORT_ACTIONS


# ---------------------------------------------------------------------------
# TIGHTEN_STOP_LOSS_ABORT.
# ---------------------------------------------------------------------------


def test_tighten_stop_loss_abort_fires_on_adverse_excursion_without_progress():
    decision = evaluate_exit_policy_v4(
        config(abort_adverse_r=0.4, abort_adverse_max_mfe_r=0.25, abort_stop_r=-0.5),
        base_row(
            current_progress_r=-0.3,
            mfe_r=0.1,
            mae_r=-0.45,
            current_stop_r=-1.0,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "TIGHTEN_STOP_LOSS_ABORT"
    assert decision.status == "actionable"
    assert decision.target_stop_r == pytest.approx(-0.5)


def test_tighten_skipped_when_stop_already_at_or_above_abort_stop():
    decision = evaluate_exit_policy_v4(
        config(abort_adverse_r=0.4, abort_adverse_max_mfe_r=0.25, abort_stop_r=-0.5),
        base_row(
            current_progress_r=-0.3,
            mfe_r=0.1,
            mae_r=-0.45,
            current_stop_r=-0.5,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "HOLD"


def test_tighten_skipped_when_mfe_above_floor():
    decision = evaluate_exit_policy_v4(
        config(abort_adverse_r=0.4, abort_adverse_max_mfe_r=0.25, abort_stop_r=-0.5),
        base_row(
            current_progress_r=-0.3,
            mfe_r=0.3,
            mae_r=-0.45,
            current_stop_r=-1.0,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "HOLD"


# ---------------------------------------------------------------------------
# CLOSE_EARLY_LOSS_ABORT.
# ---------------------------------------------------------------------------


def test_close_early_loss_abort_no_progress_branch():
    decision = evaluate_exit_policy_v4(
        config(abort_no_progress_bars=6, abort_min_mfe_r=0.3),
        base_row(
            bars_elapsed=6,
            current_progress_r=-0.1,
            mfe_r=0.2,
            mae_r=-0.2,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_EARLY_LOSS_ABORT"
    assert decision.close_reason == "v4_abort_no_progress"


def test_close_early_loss_abort_not_before_bar_budget():
    decision = evaluate_exit_policy_v4(
        config(abort_no_progress_bars=6, abort_min_mfe_r=0.3),
        base_row(
            bars_elapsed=5,
            current_progress_r=-0.1,
            mfe_r=0.2,
            mae_r=-0.2,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "HOLD"


def test_close_early_loss_abort_adverse_close_requires_consecutive_counter():
    # Armed rule with NO caller-maintained counter -> fail closed, never
    # approximate with bars_elapsed (replay-parity contract).
    decision = evaluate_exit_policy_v4(
        config(abort_close_below_r=-0.1, abort_consecutive_bars=4, abort_min_mfe_r=0.3),
        base_row(
            bars_elapsed=12,
            current_progress_r=-0.2,
            mfe_r=0.1,
            mae_r=-0.3,
            partial_close_allowed=False,
        ),
    )
    assert decision.action == "HOLD"
    assert decision.status == "source_gap_fail_closed"
    assert "consecutive_closes_below_abort_r_counter_required" in decision.source_gaps


def test_close_early_loss_abort_adverse_close_fires_on_consecutive_counter():
    decision = evaluate_exit_policy_v4(
        config(abort_close_below_r=-0.1, abort_consecutive_bars=4, abort_min_mfe_r=0.3),
        base_row(
            bars_elapsed=5,
            current_progress_r=-0.2,
            mfe_r=0.1,
            mae_r=-0.3,
            partial_close_allowed=False,
            consecutive_closes_below_abort_r=4,
        ),
    )
    assert decision.action == "CLOSE_EARLY_LOSS_ABORT"
    assert decision.close_reason == "v4_abort_adverse_close"


def test_close_early_loss_abort_adverse_close_counter_below_budget_holds():
    decision = evaluate_exit_policy_v4(
        config(abort_close_below_r=-0.1, abort_consecutive_bars=4, abort_min_mfe_r=0.3),
        base_row(
            bars_elapsed=5,
            current_progress_r=-0.2,
            mfe_r=0.1,
            mae_r=-0.3,
            partial_close_allowed=False,
            consecutive_closes_below_abort_r=3,
        ),
    )
    assert decision.action == "HOLD"


def test_adverse_close_rule_disabled_without_explicit_min_mfe():
    # abort_min_mfe_r must be armed explicitly: without it the adverse-close
    # rule is fully disabled (no silent 0.0 default) and no counter gap fires.
    decision = evaluate_exit_policy_v4(
        config(abort_close_below_r=-0.1, abort_consecutive_bars=4),
        base_row(
            bars_elapsed=5,
            current_progress_r=-0.2,
            mfe_r=-0.05,
            mae_r=-0.3,
            partial_close_allowed=False,
            consecutive_closes_below_abort_r=10,
        ),
    )
    assert decision.action == "HOLD"
    assert decision.status != "source_gap_fail_closed"


# ---------------------------------------------------------------------------
# Ladder priority.
# ---------------------------------------------------------------------------


def test_giveback_still_wins_when_giveback_and_abort_both_fire():
    decision = evaluate_exit_policy_v4(
        config(
            giveback_trigger_r=1.0,
            giveback_close_r=0.5,
            abort_no_progress_bars=4,
            abort_min_mfe_r=2.0,
        ),
        base_row(
            bars_elapsed=8,
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


def test_abort_close_precedes_move_stop_to_be():
    decision = evaluate_exit_policy_v4(
        config(be_trigger_r=1.0, abort_no_progress_bars=4, abort_min_mfe_r=2.0),
        base_row(
            bars_elapsed=6,
            current_progress_r=0.9,
            mfe_r=1.1,
            mae_r=-0.2,
            sl_at_breakeven=False,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_EARLY_LOSS_ABORT"
    assert decision.action != "MOVE_STOP_TO_BE"


def test_abort_with_source_gap_fails_closed():
    decision = evaluate_exit_policy_v4(
        config(abort_no_progress_bars=4, abort_min_mfe_r=0.3),
        base_row(mfe_r=None),
    )

    assert decision.action == "HOLD"
    assert decision.status == "source_gap_fail_closed"
    assert "missing_mfe_r" in decision.source_gaps


def test_globally_disabled_policy_stays_disabled_even_with_abort_thresholds():
    decision = evaluate_exit_policy_v4(
        config(
            enabled=False,
            abort_no_progress_bars=4,
            abort_min_mfe_r=0.3,
        ),
        base_row(
            bars_elapsed=8,
            current_progress_r=-0.3,
            mfe_r=0.1,
            mae_r=-0.5,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "HOLD"
    assert decision.status == "disabled"


# ---------------------------------------------------------------------------
# Runtime-key parsing.
# ---------------------------------------------------------------------------


def test_from_runtime_config_parses_abort_keys():
    cfg = ExitPolicyConfigV4.from_runtime_config(
        {
            "moonshot_exit_policy_v4_abort_adverse_r": "0.4",
            "moonshot_exit_policy_v4_abort_adverse_max_mfe_r": 0.25,
            "moonshot_exit_policy_v4_abort_stop_r": "-0.5",
            "moonshot_exit_policy_v4_abort_no_progress_bars": "6",
            "moonshot_exit_policy_v4_abort_min_mfe_r": 0.3,
            "moonshot_exit_policy_v4_abort_close_below_r": -0.1,
            "moonshot_exit_policy_v4_abort_consecutive_bars": 4,
        }
    )

    assert cfg.abort_adverse_r == pytest.approx(0.4)
    assert cfg.abort_adverse_max_mfe_r == pytest.approx(0.25)
    assert cfg.abort_stop_r == pytest.approx(-0.5)
    assert cfg.abort_no_progress_bars == 6
    assert cfg.abort_min_mfe_r == pytest.approx(0.3)
    assert cfg.abort_close_below_r == pytest.approx(-0.1)
    assert cfg.abort_consecutive_bars == 4


def test_from_runtime_config_unparseable_abort_values_stay_disabled():
    cfg = ExitPolicyConfigV4.from_runtime_config(
        {
            "moonshot_exit_policy_v4_abort_adverse_r": "garbage",
            "moonshot_exit_policy_v4_abort_no_progress_bars": "not_an_int",
        }
    )

    assert cfg.abort_adverse_r is None
    assert cfg.abort_no_progress_bars is None


# ---------------------------------------------------------------------------
# from_policy_params overlay.
# ---------------------------------------------------------------------------


def test_from_policy_params_overlay_precedence_over_base():
    base = config(abort_adverse_r=0.4, abort_stop_r=-0.6)

    overlaid = ExitPolicyConfigV4.from_policy_params(
        {
            "abort_stop_r": -0.5,
            "moonshot_exit_policy_v4_abort_min_mfe_r": "0.3",
            "unknown_key": 99,
            "abort_adverse_max_mfe_r": "garbage",
        },
        base,
    )

    assert overlaid.abort_stop_r == pytest.approx(-0.5)
    assert overlaid.abort_min_mfe_r == pytest.approx(0.3)
    # Untouched base values keep precedence.
    assert overlaid.abort_adverse_r == pytest.approx(0.4)
    # Unparseable values degrade to the base value (still disabled).
    assert overlaid.abort_adverse_max_mfe_r is None
    # Base config object itself is not mutated.
    assert base.abort_stop_r == pytest.approx(-0.6)
    assert base.abort_min_mfe_r is None


def test_from_policy_params_empty_or_none_returns_base():
    base = config(abort_adverse_r=0.4)

    assert ExitPolicyConfigV4.from_policy_params(None, base) is base
    assert ExitPolicyConfigV4.from_policy_params({}, base) is base
    assert (
        ExitPolicyConfigV4.from_policy_params({"unknown_key": 1.0}, base) is base
    )


def test_from_policy_params_explicit_none_disables_field():
    base = config(abort_adverse_r=0.4, abort_adverse_max_mfe_r=0.25, abort_stop_r=-0.5)

    overlaid = ExitPolicyConfigV4.from_policy_params({"abort_adverse_r": None}, base)

    assert overlaid.abort_adverse_r is None
    assert overlaid.abort_adverse_max_mfe_r == pytest.approx(0.25)


def test_from_policy_params_cannot_flip_activation_flags():
    base = ExitPolicyConfigV4(enabled=False, apply_to_execution=False)

    overlaid = ExitPolicyConfigV4.from_policy_params(
        {
            "enabled": True,
            "apply_to_execution": True,
            "moonshot_exit_policy_v4_enabled": True,
            "abort_min_mfe_r": 0.3,
        },
        base,
    )

    assert overlaid.enabled is False
    assert overlaid.apply_to_execution is False
    assert overlaid.abort_min_mfe_r == pytest.approx(0.3)


def test_from_policy_params_overlaid_config_drives_abort_decision():
    base = config()
    overlaid = ExitPolicyConfigV4.from_policy_params(
        {"abort_no_progress_bars": 4, "abort_min_mfe_r": 0.3},
        base,
    )

    decision = evaluate_exit_policy_v4(
        overlaid,
        base_row(
            bars_elapsed=5,
            current_progress_r=-0.1,
            mfe_r=0.2,
            mae_r=-0.2,
            partial_close_allowed=False,
        ),
    )

    assert decision.action == "CLOSE_EARLY_LOSS_ABORT"
    assert decision.close_reason == "v4_abort_no_progress"
