"""`exits.replay` must be the same program as `primitives.simulate_detail`.

Everything downstream — MFE/MAE aggregates, the exit prescriptions, the trail sweeps wave
7 runs — is only about the estate if the replay reproduces the labeller exactly. This
fuzzes it rather than asserting it: random OHLC series, both directions, with and without
targets and trails, compared with `==` on R and on the exit index.
"""

from __future__ import annotations

import random

import pytest

from src.components.ultimate_book.primitives import Bar, simulate_detail
from src.research_infra.walkforward.exits import ExitPolicy, replay


def _series(rng: random.Random, n: int, start: float = 100.0) -> list[Bar]:
    bars = []
    px = start
    for _ in range(n):
        o = px
        drift = rng.gauss(0.0, 1.0)
        c = max(0.5, o + drift)
        hi = max(o, c) + abs(rng.gauss(0.0, 0.6))
        lo = max(0.1, min(o, c) - abs(rng.gauss(0.0, 0.6)))
        bars.append(Bar(o, hi, lo, c, 1.0))
        px = c
    return bars


@pytest.mark.parametrize("seed_block", range(8))
def test_replay_matches_simulate_detail_exactly(seed_block: int) -> None:
    rng = random.Random(20260729 + seed_block)
    checked = 0
    for _ in range(500):
        n = rng.randint(6, 90)
        bars = _series(rng, n)
        i = rng.randint(0, max(0, n - 3))
        direction = rng.choice((1, -1))
        stop = max(0.05, abs(rng.gauss(1.5, 0.8)))
        target = rng.choice((None, stop * rng.uniform(0.5, 4.0)))
        if rng.random() < 0.5:
            arm = stop * rng.uniform(0.3, 2.5)
            gap = stop * rng.uniform(0.2, 1.5)
        else:
            arm = gap = None
        maxbars = rng.randint(1, 80)

        r_ref, xi_ref = simulate_detail(
            bars, i, direction, stop_dist=stop, target_dist=target,
            trail_arm=arm, trail_gap=gap, maxbars=maxbars, cost=0.0,
        )
        got = replay(
            bars, i, direction, stop_dist=stop,
            policy=ExitPolicy(target_dist=target, trail_arm=arm, trail_gap=gap,
                              maxbars=maxbars),
        )
        assert got.r_gross == r_ref, (
            f"R differs at seed_block={seed_block} i={i} dir={direction}: "
            f"{got.r_gross!r} != {r_ref!r}"
        )
        assert got.exit_index == xi_ref
        checked += 1
    assert checked == 500


def test_excursions_bound_the_realised_r() -> None:
    """MAE <= R <= MFE on every stop/target/maxbars exit.

    A trail exit can realise BELOW its own MFE (that is what a trail is) but never above
    it, and no exit can realise below the MAE, because both are bar extremes over the
    same held window.
    """
    rng = random.Random(4242)
    for _ in range(2000):
        bars = _series(rng, rng.randint(6, 60))
        i = rng.randint(0, max(0, len(bars) - 3))
        direction = rng.choice((1, -1))
        stop = max(0.05, abs(rng.gauss(1.5, 0.8)))
        got = replay(bars, i, direction, stop_dist=stop,
                     policy=ExitPolicy(target_dist=stop * 2, maxbars=rng.randint(1, 40)))
        assert got.mae_r <= got.r_gross + 1e-9 <= got.mfe_r + 1e-9 or got.mfe_r == 0.0
        assert got.mae_r <= 0.0
        assert got.mfe_r >= 0.0


def test_time_stop_closes_at_the_bar_close_and_never_beyond_maxbars() -> None:
    bars = [Bar(100, 100.5, 99.5, 100.0)] * 40
    bars = [Bar(100 + k * 0.01, 100.5 + k * 0.01, 99.9 + k * 0.01, 100.2 + k * 0.01)
            for k in range(40)]
    got = replay(bars, 0, 1, stop_dist=50.0,
                 policy=ExitPolicy(maxbars=30, time_stop_bars=5))
    assert got.exit_reason == "time_stop"
    assert got.exit_index == 5
    assert got.bars_held == 5
    # The time stop is a policy, maxbars is the harness ceiling; tightening one must not
    # move the other.
    loose = replay(bars, 0, 1, stop_dist=50.0, policy=ExitPolicy(maxbars=30))
    assert loose.exit_reason == "maxbars"
    assert loose.exit_index == 30


def test_stop_wins_the_same_bar_tie_against_a_scheduled_exit() -> None:
    """A stop that hit on the time-stop bar hit before the clock ran out on it."""
    bars = [Bar(100, 101, 99, 100)] + [Bar(100, 101, 90, 95)] * 5
    got = replay(bars, 0, 1, stop_dist=5.0, policy=ExitPolicy(time_stop_bars=1))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(-1.0)


def test_trail_and_gap_must_be_given_together() -> None:
    with pytest.raises(ValueError, match="together"):
        ExitPolicy(trail_arm=1.0)
    with pytest.raises(ValueError, match="together"):
        ExitPolicy(trail_gap=1.0)


def test_rollover_flat_fails_closed_without_a_server() -> None:
    """No server named means no rollover rule, not a guessed +3h one."""
    bars = [Bar(100 + k * 0.01, 100.5, 99.9, 100.2) for k in range(40)]
    got = replay(bars, 0, 1, stop_dist=50.0,
                 policy=ExitPolicy(maxbars=20, flat_before_rollover_local_hour=23))
    assert got.exit_reason == "maxbars"


def test_trail_lag_extremes_forbids_the_same_bar_arm_and_fill():
    """The intrabar honesty switch (B613).

    One bar that opens at entry, spikes to +8R and closes back near entry. The production
    trail arms and fills inside it, at high - gap. With lagged extremes it cannot: the
    running extreme is still `entry` when that bar is checked, so nothing fills, and the
    trade continues to whatever the later bars do.
    """
    bars = [Bar(100, 100.5, 99.5, 100.0)]          # entry bar, entry = 100.0
    bars.append(Bar(100.0, 108.0, 99.6, 100.1))    # the spike bar
    bars += [Bar(100.1, 100.3, 99.9, 100.0)] * 5

    pol = dict(trail_arm=0.5, trail_gap=0.5, maxbars=6)
    prod = replay(bars, 0, 1, stop_dist=1.0, policy=ExitPolicy(**pol))
    lagged = replay(bars, 0, 1, stop_dist=1.0,
                    policy=ExitPolicy(**pol, trail_lag_extremes=True))

    assert prod.exit_reason == "trail" and prod.exit_index == 1
    assert prod.r_gross == pytest.approx(7.5)      # 108.0 - 0.5 gap, in R
    # The lagged variant cannot fill on the bar that set the high, and when the next bar
    # opens far below the trail level it fills at that OPEN — not at a price the bar
    # never traded.
    assert lagged.exit_index > 1
    assert lagged.r_gross == pytest.approx(0.1)    # bar 2 open 100.1, entry 100.0
    assert lagged.r_gross < prod.r_gross


def test_trail_lag_extremes_still_trails_from_the_next_bar():
    """It must not disable the trail — only delay its reference by one bar."""
    bars = [Bar(100, 100.5, 99.5, 100.0)]
    bars.append(Bar(100.0, 104.0, 99.9, 103.9))    # arms, sets the high
    bars.append(Bar(103.9, 104.0, 101.0, 101.2))   # retraces past high - gap
    bars += [Bar(101.2, 101.4, 101.0, 101.1)] * 3
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(trail_arm=0.5, trail_gap=0.5, maxbars=6,
                                   trail_lag_extremes=True))
    assert got.exit_reason == "trail"
    assert got.exit_index == 2
    # bar 2 opens at 103.9, above the 103.5 trail level, so the level is the fill
    assert got.r_gross == pytest.approx(3.5)       # 104.0 - 0.5, in R


def test_lagged_trail_never_fills_below_entry_on_the_arming_bar():
    """`prev_mx` is `entry` on the arming bar; a fill at entry - gap would be nonsense."""
    bars = [Bar(100, 100.5, 99.5, 100.0)]
    bars.append(Bar(100.0, 101.0, 99.6, 99.7))     # arms at +0.5R, low dips below entry
    bars += [Bar(99.7, 99.9, 99.5, 99.8)] * 4
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(trail_arm=0.5, trail_gap=0.5, maxbars=5,
                                   trail_lag_extremes=True))
    assert got.exit_index > 1 or got.exit_reason != "trail"
    assert got.r_gross > -1.0 or got.exit_reason == "stop"


# ===================================================================================
# B751 — the pre-rollover flat lands one bar late, and one bar is a whole swap night.
# Session AD. `fx_jpy_ny`'s §3.2 repair is "exit 23:45 broker time: caps swap at
# structurally zero", and it did not, because the cutoff was compared against each bar's
# OPEN. On an M15 grid `hour=0` therefore selected the bar OPENING at 23:45, whose CLOSE is
# exactly the broker midnight — and `costs.model.rollover_nights` charges a night at every
# midnight `day <= end`, so that exit is charged one. These tests hold the corrected
# semantics AND the arithmetic that makes it matter, so neither can regress silently.


def _ny_bars(n: int = 40):
    return [Bar(100 + k * 0.001, 100.02, 99.98, 100 + k * 0.001) for k in range(n)]


def test_rollover_flat_exits_on_the_bar_that_CLOSES_before_the_cutoff() -> None:
    """The corrected semantics, on a real broker clock and a real M15 grid."""
    import datetime as dt

    from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

    rule = resolve_rule("FTMO-Server3")
    # bar opens 16:00 broker; entry is its close. Then 32 M15 bars, so the grid spans the
    # 23:45 bar and beyond.
    opens = [broker_naive_to_utc(dt.datetime(2026, 7, 6, 16, 0) + dt.timedelta(minutes=15 * k),
                                 rule) for k in range(40)]
    bars = _ny_bars(40)
    got = replay(bars, 0, 1, stop_dist=50.0, times=opens, server="FTMO-Server3",
                 bar_minutes=15,
                 policy=ExitPolicy(maxbars=39, flat_before_rollover_local_hour=0))
    assert got.exit_reason == "rollover_flat"
    # the exit bar must CLOSE strictly before broker midnight
    exit_close_utc = opens[got.exit_index] + dt.timedelta(minutes=15)
    midnight_utc = broker_naive_to_utc(dt.datetime(2026, 7, 7, 0, 0), rule)
    assert exit_close_utc < midnight_utc
    # ...and it must be the LAST such bar: one bar later closes at or after midnight
    assert opens[got.exit_index + 1] + dt.timedelta(minutes=15) >= midnight_utc


def test_the_corrected_rollover_flat_is_what_makes_swap_structurally_zero() -> None:
    """The arithmetic B751 is about, asserted against the cost model itself.

    The bar the OLD (open-compared) rule picked closes exactly on the rollover and is
    charged a night; the bar the corrected rule picks is not. If this ever fails, the
    "structurally carry-free" claim for `fx_jpy_ny` has quietly stopped being true.
    """
    import datetime as dt

    from src.costs.model import rollover_nights
    from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

    rule = resolve_rule("FTMO-Server3")
    entry_utc = broker_naive_to_utc(dt.datetime(2026, 7, 6, 16, 15), rule)
    on_the_rollover, _ = rollover_nights(entry_utc, 7.75, server="FTMO-Server3",
                                         rollover3days_weekday=3)   # exit 00:00 broker
    before_it, _ = rollover_nights(entry_utc, 7.50, server="FTMO-Server3",
                                   rollover3days_weekday=3)         # exit 23:45 broker
    assert on_the_rollover == 1.0
    assert before_it == 0.0


def test_rollover_flat_fails_closed_without_bar_minutes() -> None:
    """No bar width named means no rollover rule, not an off-by-one-bar one."""
    import datetime as dt

    from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

    rule = resolve_rule("FTMO-Server3")
    opens = [broker_naive_to_utc(dt.datetime(2026, 7, 6, 16, 0) + dt.timedelta(minutes=15 * k),
                                 rule) for k in range(40)]
    got = replay(_ny_bars(40), 0, 1, stop_dist=50.0, times=opens, server="FTMO-Server3",
                 policy=ExitPolicy(maxbars=39, flat_before_rollover_local_hour=0))
    assert got.exit_reason == "maxbars"


def test_flat_before_utc_is_the_general_form_and_the_earlier_cutoff_binds() -> None:
    """`flat_before_utc` closes before a caller-priced instant; earliest scheduled flat wins."""
    import datetime as dt

    from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

    rule = resolve_rule("FTMO-Server3")
    opens = [broker_naive_to_utc(dt.datetime(2026, 7, 6, 16, 0) + dt.timedelta(minutes=15 * k),
                                 rule) for k in range(40)]
    bars = _ny_bars(40)
    cut = broker_naive_to_utc(dt.datetime(2026, 7, 6, 20, 0), rule)

    alone = replay(bars, 0, 1, stop_dist=50.0, times=opens, server="FTMO-Server3",
                   bar_minutes=15, flat_before_utc=cut,
                   policy=ExitPolicy(maxbars=39))
    assert alone.exit_reason == "rollover_flat"
    assert opens[alone.exit_index] + dt.timedelta(minutes=15) < cut
    assert opens[alone.exit_index + 1] + dt.timedelta(minutes=15) >= cut

    # with BOTH rules armed the 20:00 cutoff is earlier than midnight, so it binds
    both = replay(bars, 0, 1, stop_dist=50.0, times=opens, server="FTMO-Server3",
                  bar_minutes=15, flat_before_utc=cut,
                  policy=ExitPolicy(maxbars=39, flat_before_rollover_local_hour=0))
    assert both.exit_index == alone.exit_index

    # ...and it is ignored without the grid, same fail-closed doctrine
    no_grid = replay(bars, 0, 1, stop_dist=50.0, times=opens, server="FTMO-Server3",
                     flat_before_utc=cut, policy=ExitPolicy(maxbars=39))
    assert no_grid.exit_reason == "maxbars"


def test_a_scheduled_flat_never_beats_a_price_trigger_on_the_same_bar() -> None:
    """The pessimistic ordering, extended to `flat_before_utc`: the stop hit first."""
    import datetime as dt

    from src.utils.broker_clock import broker_naive_to_utc, resolve_rule

    rule = resolve_rule("FTMO-Server3")
    opens = [broker_naive_to_utc(dt.datetime(2026, 7, 6, 16, 0) + dt.timedelta(minutes=15 * k),
                                 rule) for k in range(10)]
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 100.1, 98.0, 99.0))     # bar 1 takes out a 1-point stop
    bars += [Bar(99.0, 99.1, 98.9, 99.0)] * 8
    got = replay(bars, 0, 1, stop_dist=1.0, times=opens, server="FTMO-Server3",
                 bar_minutes=15,
                 flat_before_utc=opens[1] + dt.timedelta(minutes=15),
                 policy=ExitPolicy(maxbars=9))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(-1.0)


# ===================================================================================
# B752 — `partial_be_runner`, the LIVE contract of four W7 sleeves that no walk simulated.
# `execution_packets.py:44-51`. Two of the four are armed and trading real money, and AA
# labelled all four under plain stop/target/maxbars — so `metals_core`'s measured capture
# ratio of 0.114 is a number about a contract the live book does not run.


def test_partial_banks_its_half_and_the_breakeven_stop_protects_the_rest() -> None:
    """+2R, scale 50%, then all the way back to entry: 0.5*2 + 0.5*0 = 1.0 R, not 0."""
    bars = [Bar(100, 100.1, 99.9, 100.0)]          # entry 100.0, stop_dist 1.0
    bars.append(Bar(100.0, 102.5, 99.9, 102.0))    # reaches +2.5R -> partial at +2R
    bars.append(Bar(102.0, 102.1, 99.0, 99.5))     # comes back through entry -> BE stop
    bars += [Bar(99.5, 99.6, 99.4, 99.5)] * 3
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, partial_at_r=2.0, partial_frac=0.5))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(1.0)
    assert got.detail["partial_banked_r"] == pytest.approx(1.0)
    assert got.detail["raw_remainder_r"] == pytest.approx(0.0)

    # without the partial the same path is a full -1R... no: the BE move is what saves it.
    plain = replay(bars, 0, 1, stop_dist=1.0, policy=ExitPolicy(maxbars=5))
    assert plain.exit_reason == "stop"
    assert plain.r_gross == pytest.approx(-1.0)


def test_partial_then_target_adds_the_two_pieces() -> None:
    """Scale 50% at +2R, runner to a +4R target: 0.5*2 + 0.5*4 = 3.0 R."""
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 102.5, 99.9, 102.0))    # partial at +2R
    bars.append(Bar(102.0, 104.5, 101.9, 104.0))   # target at +4R
    bars += [Bar(104.0, 104.1, 103.9, 104.0)] * 3
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, target_dist=4.0, partial_at_r=2.0))
    assert got.exit_reason == "target"
    assert got.r_gross == pytest.approx(3.0)


def test_a_target_at_or_below_the_partial_closes_the_whole_position() -> None:
    """The target is checked first, so it takes the position and no partial happens."""
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 102.5, 99.9, 102.0))
    bars += [Bar(102.0, 102.1, 101.9, 102.0)] * 4
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, target_dist=2.0, partial_at_r=2.0))
    assert got.exit_reason == "target"
    assert got.r_gross == pytest.approx(2.0)
    assert "partial_banked_r" not in got.detail


def test_stop_wins_the_same_bar_tie_against_the_partial() -> None:
    """The pessimistic ordering extends to the scale-out: a bar that stopped out did so first."""
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 102.5, 98.5, 99.0))     # touches BOTH +2R and the -1R stop
    bars += [Bar(99.0, 99.1, 98.9, 99.0)] * 4
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, partial_at_r=2.0))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(-1.0)


def test_partial_works_short_symmetrically() -> None:
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 100.1, 97.5, 98.0))     # -2.5R favourable for a short
    bars.append(Bar(98.0, 101.0, 97.9, 100.5))     # back through entry -> BE stop
    bars += [Bar(100.5, 100.6, 100.4, 100.5)] * 3
    got = replay(bars, 0, -1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, partial_at_r=2.0))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(1.0)


def test_be_stop_after_partial_can_be_turned_off() -> None:
    """With the BE move off, the original stop still governs the remainder."""
    bars = [Bar(100, 100.1, 99.9, 100.0)]
    bars.append(Bar(100.0, 102.5, 99.9, 102.0))
    bars.append(Bar(102.0, 102.1, 98.5, 99.0))     # takes the ORIGINAL -1R stop
    bars += [Bar(99.0, 99.1, 98.9, 99.0)] * 3
    got = replay(bars, 0, 1, stop_dist=1.0,
                 policy=ExitPolicy(maxbars=5, partial_at_r=2.0,
                                   be_stop_after_partial=False))
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(0.5)       # 0.5*2 + 0.5*(-1)


@pytest.mark.parametrize("frac", [0.0, 1.0, -0.1, 1.5])
def test_partial_frac_must_be_strictly_inside_zero_and_one(frac: float) -> None:
    with pytest.raises(ValueError, match="partial_frac"):
        ExitPolicy(partial_at_r=2.0, partial_frac=frac)


def test_partial_at_r_must_be_positive() -> None:
    with pytest.raises(ValueError, match="partial_at_r"):
        ExitPolicy(partial_at_r=0.0)
