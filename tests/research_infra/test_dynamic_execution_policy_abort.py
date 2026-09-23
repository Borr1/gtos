"""Early-loss-abort primitives in the research replay policy engine.

Covers the three abort primitives added to ``PolicySpec``/``simulate_policy``:

- adverse-excursion stop-tighten (one-shot, never lowers, next-bar effect),
- no-progress close at the abort bar budget (``abort_no_progress``),
- consecutive-adverse-close close (``abort_adverse_close``),

plus a golden default-equivalence suite proving that all-``None`` abort fields
reproduce the pre-abort replay results for the existing policy factories. The
golden expectations were computed from the pre-change module on the same fixed
path before the abort primitives were added.
"""

import pytest

from src.research.dynamic_execution_policy import (
    PathObservation,
    PolicySpec,
    legacy_fixed_target_policy,
    live_current_j46_j49_policy,
    partial_be_policy,
    profit_harvest_mfe_capture_v4_policy,
    simulate_policy,
    trailing_policy,
)


def obs(index, high, low, close):
    return PathObservation(
        index=index,
        high_r=high,
        low_r=low,
        close_r=close,
        time_utc=f"2026-05-26T00:{index:02d}:00Z",
    )


def abort_spec(**overrides):
    base = {"name": "abort_probe", "final_target_r": 1.5, "stop_r": -1.0}
    base.update(overrides)
    return PolicySpec(**base)


# ---------------------------------------------------------------------------
# Golden default-equivalence: abort fields default None => byte-identical
# replay results versus the pre-abort module for the existing factories.
# Expected values below were produced by running simulate_policy from the
# PRE-CHANGE module on GOLDEN_PATH.
# ---------------------------------------------------------------------------

GOLDEN_PATH = [
    obs(1, 0.30, -0.20, 0.10),
    obs(2, 0.55, -0.05, 0.45),
    obs(3, 0.80, 0.10, 0.30),
    obs(4, 0.60, -0.15, -0.10),
    obs(5, 0.20, -0.40, -0.30),
    obs(6, 0.10, -0.60, -0.55),
]

GOLDEN_EXPECTATIONS = [
    # (factory, exit_reason, final_r, exit_index, n_transitions)
    (legacy_fixed_target_policy, "path_end_mark_to_market", -0.55, 6, 0),
    (trailing_policy, "path_end_mark_to_market", -0.55, 6, 0),
    (
        profit_harvest_mfe_capture_v4_policy,
        "trailing_stop",
        -0.04999999999999999,
        1,
        1,
    ),
    (live_current_j46_j49_policy, "path_end_mark_to_market", -0.55, 6, 0),
    (partial_be_policy, "path_end_mark_to_market", -0.55, 6, 0),
]


@pytest.mark.parametrize(
    "factory, exit_reason, final_r, exit_index, n_transitions",
    GOLDEN_EXPECTATIONS,
    ids=[entry[0].__name__ for entry in GOLDEN_EXPECTATIONS],
)
def test_defaults_none_reproduce_pre_abort_golden_results(
    factory, exit_reason, final_r, exit_index, n_transitions
):
    spec = factory()

    assert spec.abort_adverse_r is None
    assert spec.abort_adverse_max_mfe_r is None
    assert spec.abort_stop_r is None
    assert spec.abort_no_progress_bars is None
    assert spec.abort_min_mfe_r is None
    assert spec.abort_close_below_r is None
    assert spec.abort_consecutive_bars is None

    result = simulate_policy(spec, GOLDEN_PATH)

    assert result.exit_reason == exit_reason
    assert result.final_r == final_r
    assert result.exit_index == exit_index
    assert len(result.transitions) == n_transitions
    assert not any(
        str(transition.get("event", "")).startswith("abort")
        for transition in result.transitions
    )


# ---------------------------------------------------------------------------
# Adverse-excursion stop-tighten.
# ---------------------------------------------------------------------------

TIGHTEN_PATH = [
    # Bar 1: MAE -0.55 <= -0.40 with MFE 0.10 < 0.20 floor => tighten to -0.5
    # on bar close. Bar 1's own stop check ran with -1.0, so the bar-1 low
    # (-0.55 <= -0.5) does NOT exit: next-bar semantics.
    obs(1, 0.10, -0.55, -0.30),
    # Bar 2: low -0.52 <= tightened -0.5 => stop exit at -0.5.
    obs(2, 0.15, -0.52, -0.20),
    # Bar 3: would reach the 1.5R target without the abort.
    obs(3, 1.60, -0.20, 1.55),
]


def test_path_survives_to_target_without_abort_fields():
    result = simulate_policy(abort_spec(), TIGHTEN_PATH)

    assert result.exit_reason == "final_target"
    assert result.final_r == 1.5
    assert result.exit_index == 3


def test_abort_stop_tighten_stops_survivor_at_abort_stop_from_next_bar():
    spec = abort_spec(
        abort_adverse_r=0.40,
        abort_adverse_max_mfe_r=0.20,
        abort_stop_r=-0.5,
    )

    result = simulate_policy(spec, TIGHTEN_PATH)

    assert result.exit_reason == "abort_tightened_stop"
    assert result.final_r == pytest.approx(-0.5)
    # Bar 1 already traded through -0.5 but the tighten only applies from the
    # next bar, so the exit lands on bar 2.
    assert result.exit_index == 2
    assert result.stop_r_at_exit == pytest.approx(-0.5)
    tighten_events = [
        transition
        for transition in result.transitions
        if transition["event"] == "abort_stop_tighten"
    ]
    assert len(tighten_events) == 1
    assert tighten_events[0]["index"] == 1
    assert tighten_events[0]["stop_moved_to_r"] == pytest.approx(-0.5)


def test_abort_stop_tighten_requires_mfe_below_floor():
    spec = abort_spec(
        abort_adverse_r=0.40,
        abort_adverse_max_mfe_r=0.20,
        abort_stop_r=-0.5,
    )
    path = [
        # Same adverse excursion, but MFE 0.30 >= 0.20 floor: no tighten.
        obs(1, 0.30, -0.55, -0.30),
        obs(2, 0.15, -0.52, -0.20),
        obs(3, 1.60, -0.20, 1.55),
    ]

    result = simulate_policy(spec, path)

    assert result.exit_reason == "final_target"
    assert result.final_r == 1.5
    assert not any(
        transition["event"] == "abort_stop_tighten" for transition in result.transitions
    )


def test_abort_stop_tighten_is_one_shot_across_qualifying_bars():
    spec = abort_spec(
        final_target_r=None,
        abort_adverse_r=0.40,
        abort_adverse_max_mfe_r=0.20,
        abort_stop_r=-0.9,
    )
    path = [
        obs(1, 0.05, -0.45, -0.30),
        obs(2, 0.05, -0.45, -0.30),
        obs(3, 0.05, -0.45, -0.30),
    ]

    result = simulate_policy(spec, path)

    tighten_events = [
        transition
        for transition in result.transitions
        if transition["event"] == "abort_stop_tighten"
    ]
    assert len(tighten_events) == 1
    assert tighten_events[0]["index"] == 1
    assert result.exit_reason == "path_end_mark_to_market"
    assert result.final_r == pytest.approx(-0.30)
    assert result.stop_r_at_exit == pytest.approx(-0.9)


def test_abort_stop_tighten_never_lowers_existing_stop():
    spec = abort_spec(
        final_target_r=None,
        abort_adverse_r=0.40,
        abort_adverse_max_mfe_r=0.20,
        abort_stop_r=-1.5,
    )
    path = [
        obs(1, 0.05, -0.45, -0.30),
        obs(2, 0.05, -1.05, -0.90),
    ]

    result = simulate_policy(spec, path)

    # The -1.5 abort stop is below the original -1.0 stop, so the stop must
    # not move and the original stop exits the trade at -1.0.
    assert result.exit_reason == "stop_loss"
    assert result.final_r == pytest.approx(-1.0)
    assert result.stop_r_at_exit == pytest.approx(-1.0)
    assert not any(
        transition["event"] == "abort_stop_tighten" for transition in result.transitions
    )


# ---------------------------------------------------------------------------
# No-progress close at bar k.
# ---------------------------------------------------------------------------


def test_abort_no_progress_closes_at_bar_k_close():
    spec = abort_spec(
        final_target_r=2.0,
        abort_no_progress_bars=3,
        abort_min_mfe_r=0.30,
    )
    path = [
        obs(1, 0.20, -0.10, 0.05),
        obs(2, 0.25, -0.15, 0.10),
        obs(3, 0.10, -0.20, -0.12),
        obs(4, 2.50, 0.00, 2.40),
    ]

    baseline = simulate_policy(abort_spec(final_target_r=2.0), path)
    result = simulate_policy(spec, path)

    assert baseline.exit_reason == "final_target"
    assert baseline.final_r == 2.0
    assert result.exit_reason == "abort_no_progress"
    assert result.exit_index == 3
    assert result.final_r == pytest.approx(-0.12)
    assert result.transitions[-1]["event"] == "abort_no_progress"
    assert result.transitions[-1]["abort_no_progress_bars"] == 3


def test_abort_no_progress_skipped_when_mfe_floor_met():
    spec = abort_spec(
        final_target_r=2.0,
        abort_no_progress_bars=3,
        abort_min_mfe_r=0.30,
    )
    path = [
        obs(1, 0.20, -0.10, 0.05),
        obs(2, 0.35, -0.15, 0.10),
        obs(3, 0.10, -0.20, -0.12),
        obs(4, 2.50, 0.00, 2.40),
    ]

    result = simulate_policy(spec, path)

    assert result.exit_reason == "final_target"
    assert result.final_r == 2.0
    assert result.exit_index == 4


# ---------------------------------------------------------------------------
# Consecutive-adverse-close rule.
# ---------------------------------------------------------------------------


def test_abort_adverse_close_requires_n_consecutive_closes():
    spec = abort_spec(
        final_target_r=None,
        abort_close_below_r=-0.10,
        abort_consecutive_bars=2,
        abort_min_mfe_r=0.30,
    )
    path = [
        obs(1, 0.05, -0.20, -0.15),  # run = 1
        obs(2, 0.10, -0.15, 0.00),  # close above threshold => run resets
        obs(3, 0.05, -0.25, -0.20),  # run = 1
        obs(4, 0.05, -0.30, -0.25),  # run = 2 => abort
    ]

    result = simulate_policy(spec, path)

    assert result.exit_reason == "abort_adverse_close"
    assert result.exit_index == 4
    assert result.final_r == pytest.approx(-0.25)
    assert result.transitions[-1]["event"] == "abort_adverse_close"
    assert result.transitions[-1]["consecutive_adverse_closes"] == 2


def test_abort_adverse_close_never_fires_on_alternating_closes():
    spec = abort_spec(
        final_target_r=None,
        abort_close_below_r=-0.10,
        abort_consecutive_bars=2,
        abort_min_mfe_r=0.30,
    )
    path = [
        obs(1, 0.05, -0.20, -0.15),
        obs(2, 0.10, -0.15, 0.00),
        obs(3, 0.05, -0.25, -0.20),
        obs(4, 0.10, -0.15, 0.00),
    ]

    result = simulate_policy(spec, path)

    assert result.exit_reason == "path_end_mark_to_market"
    assert result.final_r == pytest.approx(0.00)
    assert not any(
        transition["event"] == "abort_adverse_close"
        for transition in result.transitions
    )


def test_abort_adverse_close_blocked_by_mfe_floor():
    spec = abort_spec(
        final_target_r=None,
        abort_close_below_r=-0.10,
        abort_consecutive_bars=2,
        abort_min_mfe_r=0.30,
    )
    path = [
        obs(1, 0.05, -0.20, -0.15),
        obs(2, 0.40, -0.15, -0.12),  # MFE 0.40 >= 0.30 floor
        obs(3, 0.05, -0.25, -0.20),
        obs(4, 0.05, -0.30, -0.25),
    ]

    result = simulate_policy(spec, path)

    assert result.exit_reason == "path_end_mark_to_market"
    assert result.final_r == pytest.approx(-0.25)
    assert not any(
        transition["event"] == "abort_adverse_close"
        for transition in result.transitions
    )
