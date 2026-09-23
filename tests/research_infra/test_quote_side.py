"""Behavioural tests for the quote-side correction.

Every expected number here is computed BY HAND in the test body from the geometry, never
copied from a run of the code under test. Several of them are the number the OLD
convention gets wrong — those are marked and they are the proof the repair is real.
"""

from __future__ import annotations

import datetime as dt
import json

import pytest

from src.components.ultimate_book.primitives import Bar
from src.research_infra.walkforward.exits import ExitPolicy, replay
from src.research_infra.walkforward.quote_side import (
    BarQuote,
    LevelAnchor,
    ObservedBookBars,
    OrderedQuoteTicks,
    SpreadUnavailable,
    entry_trigger_level_on_tape,
    exit_quote_offset,
    first_resting_limit_touch,
    resolve_post_submission_m1_lifecycle,
    resolve_post_submission_quote_lifecycle,
    replay_ticks,
    replay_anchor,
    spread_for,
    transacted_entry_price,
    walk,
    walk_observed_book,
)


def flat(px: float) -> Bar:
    return Bar(px, px, px, px)


def bar(o, h, l, c) -> Bar:
    return Bar(o, h, l, c)


# --------------------------------------------------------------- quote geometry


def test_transacted_entry_matches_the_live_engine_sides():
    """execution.py:3247 — LONG pays the ask, SHORT receives the bid."""
    # bid tape at 100, spread 1 -> bid 100, ask 101
    assert transacted_entry_price(100.0, 1, 1.0, BarQuote.BID) == 101.0
    assert transacted_entry_price(100.0, -1, 1.0, BarQuote.BID) == 100.0
    # mid tape at 100, spread 1 -> bid 99.5, ask 100.5
    assert transacted_entry_price(100.0, 1, 1.0, BarQuote.MID) == 100.5
    assert transacted_entry_price(100.0, -1, 1.0, BarQuote.MID) == 99.5
    # ask tape at 100, spread 1 -> bid 99, ask 100
    assert transacted_entry_price(100.0, 1, 1.0, BarQuote.ASK) == 100.0
    assert transacted_entry_price(100.0, -1, 1.0, BarQuote.ASK) == 99.0


def test_exit_trigger_sides_match_the_live_engine():
    """execution.py:6953 — a LONG's exits watch the bid, a SHORT's watch the ask."""
    assert exit_quote_offset(1, BarQuote.BID, 1.0) == 0.0     # bid tape IS the bid
    assert exit_quote_offset(-1, BarQuote.BID, 1.0) == 1.0    # ask sits one spread up
    assert exit_quote_offset(1, BarQuote.ASK, 1.0) == -1.0
    assert exit_quote_offset(-1, BarQuote.ASK, 1.0) == 0.0


def test_anchor_is_bar_quote_invariant():
    """The correction is NOT 'bid vs mid' — a mid tape is exactly as optimistic.

    What is missing from the old walk is that the round trip crosses the spread at all,
    and the crossing costs one full spread from whichever side the tape is quoted.
    """
    for q in (BarQuote.BID, BarQuote.MID, BarQuote.ASK):
        assert replay_anchor(100.0, 1, 1.0, q) == pytest.approx(101.0)
        assert replay_anchor(100.0, -1, 1.0, q) == pytest.approx(99.0)


def test_pending_entry_trigger_displacement():
    """execution.py:6197 — a BUY level is watched on the ask, a SELL level on the bid."""
    # bid tape: a buy limit at 100 fires when the bid is at 99 (ask == 100)
    assert entry_trigger_level_on_tape(100.0, 1, 1.0, BarQuote.BID) == 99.0
    # a sell limit at 100 fires when the bid is at 100 — exactly on the tape
    assert entry_trigger_level_on_tape(100.0, -1, 1.0, BarQuote.BID) == 100.0


# ----------------------------------------------------- the walk, by hand, both sides


def test_long_stop_is_one_spread_nearer_and_the_old_walk_survives_it():
    """THE PROOF TEST — this FAILS under the old unshifted convention.

    Bid tape. Entry bar closes at 100.00; spread 0.20; stop distance 1.00.
    Live: buy at the ask 100.20, stop at 100.20 - 1.00 = 99.20, which triggers on the BID.
    The old walk puts the stop at 100.00 - 1.00 = 99.00, one spread FURTHER away.
    The next bar's low is 99.10: it reaches the true stop at 99.20 and never reaches the
    old one at 99.00. The bar then closes back at 100.00.

    Old convention: never stopped, R = (100.00 - 100.00)/1 = 0.0.
    Truth:          stopped, R = -1.0.
    """
    bars = [flat(100.0), bar(100.0, 100.1, 99.10, 100.0), flat(100.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=2)

    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "maxbars"
    assert old.r_gross == pytest.approx(0.0)

    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "stop"
    assert t.corrected.r_gross == pytest.approx(-1.0)
    assert t.exit_reason_changed is True
    assert t.delta_r == pytest.approx(-1.0)


def test_short_stop_is_one_spread_nearer():
    """Mirror of the above on the other side of the market, hand-computed.

    Bid tape. Close 100.00; spread 0.20; stop distance 1.00.
    Live: sell at the bid 100.00, stop at 101.00 watched on the ASK, i.e. the bid only
    has to reach 100.80. The next bar's high is 100.85 — past 100.80 and short of 101.00.
    """
    bars = [flat(100.0), bar(100.0, 100.85, 99.9, 100.0), flat(100.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=2)

    old = replay(bars, 0, -1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "maxbars"
    assert old.r_gross == pytest.approx(0.0)

    t = walk(bars, 0, -1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "stop"
    assert t.corrected.r_gross == pytest.approx(-1.0)


def test_long_target_is_one_spread_further():
    """A target the old walk books at +2R is not reached. Hand-computed.

    Close 100, spread 0.20, stop 1.00, target 2.00 away.
    Old target level 102.00; true target level 100.20 + 2.00 = 102.20.
    Next bar's high 102.10: reaches the old one, misses the true one, closes at 101.00.
    True R at the close = (101.00 - 100.20)/1.00 = +0.80.
    """
    bars = [flat(100.0), bar(100.0, 102.10, 99.9, 101.0), flat(101.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=1)

    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "target"
    assert old.r_gross == pytest.approx(2.0)

    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "maxbars"
    assert t.corrected.r_gross == pytest.approx(0.80)
    assert t.delta_r == pytest.approx(-1.20)


def test_short_target_is_one_spread_further():
    """Close 100, spread 0.20, stop 1.00, target 2.00.

    Old target 98.00; true target is watched on the ASK at 98.00, i.e. bid 97.80.
    Next bar's low 97.90 takes the old one and misses the true one; it closes at 99.00,
    where the short buys back at the ask 99.20, so R = (100.00 - 99.20)/1.00 = +0.80.
    """
    bars = [flat(100.0), bar(100.0, 100.1, 97.90, 99.0), flat(99.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=1)

    old = replay(bars, 0, -1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "target"
    assert old.r_gross == pytest.approx(2.0)

    t = walk(bars, 0, -1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "maxbars"
    assert t.corrected.r_gross == pytest.approx(0.80)


def test_close_based_exits_are_charged_exactly_one_spread():
    """A time stop, a maxbars close and a rollover flat all transact on the wrong side.

    Nothing is touched; the trade runs to its bar ceiling. The whole correction on such a
    path is s/d, and it is the same on both sides.
    """
    bars = [flat(100.0), flat(100.5), flat(100.5)]
    pol = ExitPolicy(maxbars=2)
    for d, expect_old in ((1, 0.5), (-1, -0.5)):
        old = replay(bars, 0, d, stop_dist=1.0, policy=pol)
        assert old.r_gross == pytest.approx(expect_old)
        t = walk(bars, 0, d, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
        assert t.corrected.exit_reason == "maxbars"
        assert t.delta_r == pytest.approx(-0.20)  # exactly s/d, both directions

    ts = ExitPolicy(maxbars=8, time_stop_bars=1)
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=ts)
    assert t.corrected.exit_reason == "time_stop"
    assert t.delta_r == pytest.approx(-0.20)


# ------------------------------------------------------------- boundary cases


def test_touch_exactly_at_the_true_level():
    """Exact equality must trigger, on both conventions, at the level each believes in."""
    # true long stop at 99.20 (close 100 + spread .2 - stop 1.0); bar low is exactly that
    bars = [flat(100.0), bar(100.0, 100.1, 99.20, 100.0)]
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID,
             policy=ExitPolicy(maxbars=1))
    assert t.corrected.exit_reason == "stop"
    # one tick above it must NOT trigger
    bars2 = [flat(100.0), bar(100.0, 100.1, 99.2000001, 100.0)]
    t2 = walk(bars2, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID,
              policy=ExitPolicy(maxbars=1))
    assert t2.corrected.exit_reason == "maxbars"


def test_gap_through_still_books_the_level_not_the_gap():
    """A bar that opens beyond the stop books -1R, not the gap. Both conventions agree
    on the R; they disagree on WHICH trades gap through."""
    bars = [flat(100.0), bar(95.0, 95.5, 94.0, 95.0)]
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID,
             policy=ExitPolicy(maxbars=1))
    assert t.corrected.exit_reason == "stop"
    assert t.corrected.r_gross == pytest.approx(-1.0)
    assert t.uncorrected.r_gross == pytest.approx(-1.0)
    assert t.delta_r == pytest.approx(0.0)


def test_same_bar_stop_and_target_keeps_the_pessimistic_tie():
    """The estate's tie rule (stop wins) is preserved under the correction."""
    bars = [flat(100.0), bar(100.0, 103.0, 98.0, 100.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=1)
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.uncorrected.exit_reason == "stop"
    assert t.corrected.exit_reason == "stop"
    assert t.corrected.r_gross == pytest.approx(-1.0)


def test_zero_spread_reproduces_the_old_walk_exactly():
    """The correction is a pure function of the spread — at zero it is the identity.

    This is what makes the A/B exact: the uncorrected arm is not a re-implementation.
    """
    bars = [flat(100.0), bar(100.0, 101.5, 99.4, 100.7), bar(100.7, 102.4, 100.0, 101.1)]
    for d in (1, -1):
        for pol in (
            ExitPolicy(target_dist=2.0, maxbars=2),
            ExitPolicy(trail_arm=0.5, trail_gap=0.4, maxbars=2),
            ExitPolicy(partial_at_r=1.0, target_dist=3.0, maxbars=2),
            ExitPolicy(time_stop_bars=1, maxbars=2),
        ):
            t = walk(bars, 0, d, stop_dist=1.0, spread=0.0,
                     bar_quote=BarQuote.BID, policy=pol)
            assert t.corrected.r_gross == t.uncorrected.r_gross
            assert t.corrected.exit_reason == t.uncorrected.exit_reason
            assert t.corrected.exit_index == t.uncorrected.exit_index
            assert t.corrected.mfe_r == t.uncorrected.mfe_r
            assert t.corrected.mae_r == t.uncorrected.mae_r


def test_default_replay_is_unchanged_by_the_new_argument():
    """`entry_price=None` must be byte-identical to the pre-r1 walker."""
    bars = [flat(100.0), bar(100.0, 101.5, 99.4, 100.7), bar(100.7, 102.4, 100.0, 101.1)]
    pol = ExitPolicy(target_dist=2.0, maxbars=2)
    a = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    b = replay(bars, 0, 1, stop_dist=1.0, policy=pol, entry_price=None)
    c = replay(bars, 0, 1, stop_dist=1.0, policy=pol, entry_price=bars[0].c)
    d = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=pol,
        entry_price=None,
        exit_bars=None,
        first_tradable_fills=False,
    )
    assert a.as_dict() == b.as_dict() == c.as_dict() == d.as_dict()


# ---------------------------------------------- ordered BID/ASK execution truth


def test_ordered_ticks_fail_closed_on_reordering_crossing_and_naive_time():
    with pytest.raises(ValueError, match="not ordered"):
        OrderedQuoteTicks([2, 1], [100, 100], [101, 101])
    with pytest.raises(ValueError, match="crossed"):
        OrderedQuoteTicks([1], [101], [100])
    with pytest.raises(ValueError, match="naive"):
        OrderedQuoteTicks([dt.datetime(2026, 1, 1)], [100], [101])
    with pytest.raises(ValueError, match="strings are forbidden"):
        OrderedQuoteTicks(["10", "2"], [100, 100], [101, 101])


def test_equal_numeric_instants_keep_capture_order_after_type_validation():
    ticks = OrderedQuoteTicks([10, 10.0, 11], [100, 99, 98], [101, 100, 99])
    touch = first_resting_limit_touch(ticks, 1, 100.0)
    assert touch is not None and touch.index == 1


def test_equal_timestamp_ticks_retain_capture_sequence_for_first_touch():
    ticks = OrderedQuoteTicks(
        [1, 1, 2],
        [100.0, 99.0, 98.0],
        [101.0, 100.0, 99.0],
    )
    # Both first two rows share a timestamp. Their captured sequence, not a price sort,
    # decides that the second row is the first BUY-LIMIT ASK touch.
    touch = first_resting_limit_touch(ticks, 1, 100.0)
    assert touch is not None
    assert touch.index == 1 and touch.at == 1 and touch.ask == pytest.approx(100.0)


def test_resting_limits_touch_on_correct_side_without_claiming_queue_fill():
    ticks = OrderedQuoteTicks(
        [0, 1, 2, 3],
        [100.2, 100.0, 99.8, 100.4],
        [100.5, 100.3, 100.0, 100.7],
    )
    # A BUY LIMIT at 100 is not touch-eligible when BID first touches 100 (tick 1);
    # ASK reaches 100 at tick 2. No queue/order event is inferred from that quote.
    buy = first_resting_limit_touch(ticks, 1, 100.0)
    assert buy is not None
    assert buy.index == 2 and buy.price == pytest.approx(100.0)
    # A SELL LIMIT reads BID, and the first quote is already better than its level.
    sell = first_resting_limit_touch(ticks, -1, 100.1)
    assert sell is not None
    assert sell.index == 0 and sell.price == pytest.approx(100.2)
    # The activation boundary is explicit: excluding tick 0 cannot back-fill from it.
    sell_late = first_resting_limit_touch(ticks, -1, 100.5, start=1)
    assert sell_late is None


def test_tick_replay_short_uses_time_varying_ask_and_first_crossing_quote():
    ticks = OrderedQuoteTicks(
        [1, 2, 3],
        [100.4, 100.6, 100.7],
        [100.6, 100.9, 101.2],
    )
    got = replay_ticks(
        ticks,
        0,
        -1,
        entry_price=100.0,
        stop_dist=1.0,
        policy=ExitPolicy(target_dist=2.0),
    )
    assert got.exit_reason == "stop"
    assert got.exit_index == 2
    assert got.exit_price == pytest.approx(101.2)
    assert got.r_gross == pytest.approx(-1.2)
    assert "level_geometry" not in got.detail


@pytest.mark.parametrize("direction,quote", [(1, 104.0), (-1, 96.0)])
def test_tick_gap_broker_resting_target_precedes_client_partial(direction, quote):
    ticks = OrderedQuoteTicks([1, 2], [quote, quote], [quote, quote])
    got = replay_ticks(
        ticks,
        0,
        direction,
        entry_price=100.0,
        stop_dist=1.0,
        policy=ExitPolicy(target_dist=3.0, partial_at_r=1.0),
    )
    assert got.exit_reason == "target"
    assert got.r_gross == pytest.approx(4.0)
    assert "partial_banked_r" not in got.detail
    assert got.detail["partial_vs_target_priority"] == (
        "broker_resting_final_target_first_on_same_quote"
    )
    assert got.detail["partial_order_event_authority"].startswith("NOT_AVAILABLE")


def _quote_lifecycle(
    ticks: OrderedQuoteTicks,
    *,
    direction: int = 1,
    order_type: str = "LIMIT",
    entry: float = 100.0,
    stop: float = 99.0,
    target: float = 102.0,
    risk: float = 1.0,
    source_end: dt.datetime = dt.datetime(
        2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc
    ),
    coverage_verified: bool = True,
    policy: ExitPolicy = ExitPolicy(),
):
    return resolve_post_submission_quote_lifecycle(
        ticks,
        direction=direction,
        post_scheduler_order_type=order_type,
        submission_or_ack_time_utc=dt.datetime(
            2026, 1, 1, 8, 0, tzinfo=dt.timezone.utc
        ),
        required_horizon_utc=dt.datetime(
            2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc
        ),
        source_start_utc=dt.datetime(
            2026, 1, 1, 7, 59, tzinfo=dt.timezone.utc
        ),
        source_end_utc=source_end,
        source_coverage_verified=coverage_verified,
        approved_entry_price=entry,
        approved_stop_price=stop,
        approved_target_price=target,
        approved_risk_distance=risk,
        policy=policy,
    )


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target", "entry_px", "terminal_r"),
    [
        (1, [98.0, 100.4, 102.4, 102.4], [98.1, 100.5, 102.5, 102.5], 99.0, 102.0, 100.5, 1.9),
        (-1, [102.0, 99.5, 97.5, 97.5], [102.1, 99.6, 97.6, 97.6], 101.0, 98.0, 99.5, 1.9),
    ],
)
def test_market_uses_first_strictly_causal_far_side_without_limit_bound(
    direction, bids, asks, stop, target, entry_px, terminal_r
):
    times = [
        dt.datetime(2026, 1, 1, 8, 0, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        order_type="MARKET",
        stop=stop,
        target=target,
    )

    assert got.measurement_status == "EVALUATED"
    assert got.first_causal_quote_index == 1  # the equal submission tick is excluded
    assert got.activation_class == "MARKET_FIRST_STRICTLY_CAUSAL_FAR_SIDE_QUOTE"
    assert got.modelled_entry_price == pytest.approx(entry_px)
    assert got.correct_side_touch_eligible is None
    assert got.terminal_outcome == "target"
    assert got.terminal_r == pytest.approx(terminal_r)
    assert got.broker_fill_status == "NOT_EVALUABLE"
    assert got.broker_fill_claimed is False


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target", "entry_px"),
    [
        (1, [99.4, 102.4, 102.4], [99.5, 102.5, 102.5], 99.0, 102.0, 99.5),
        (-1, [100.5, 97.5, 97.5], [100.6, 97.6, 97.6], 101.0, 98.0, 100.5),
    ],
)
def test_marketable_limit_preserves_approved_risk_after_price_improvement(
    direction, bids, asks, stop, target, entry_px
):
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        stop=stop,
        target=target,
    )

    assert got.activation_class == "MARKETABLE_LIMIT_AT_FIRST_STRICTLY_CAUSAL_QUOTE"
    assert got.correct_side_touch_eligible is True
    assert got.modelled_entry_price == pytest.approx(entry_px)
    assert got.approved_risk_distance == 1.0
    assert got.stop_r == pytest.approx(-0.5)
    assert got.target_r == pytest.approx(2.5)
    assert got.terminal_outcome == "target"
    assert got.terminal_r == pytest.approx(2.9)
    assert got.detail["ordered_exit_path"]["detail"]["level_geometry"] == (
        "explicit_absolute_stop_target"
    )
    assert got.claim_class.endswith("NOT_BROKER_ORDER_QUEUE_DEAL_OR_POSITION_TRUTH")


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target"),
    [
        (1, [99.4, 99.0, 99.0], [99.5, 99.1, 99.1], 99.0, 102.0),
        (-1, [100.5, 100.9, 100.9], [100.6, 101.0, 101.0], 101.0, 98.0),
    ],
)
def test_price_improved_limit_stop_stays_on_approved_risk_basis(
    direction, bids, asks, stop, target
):
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        stop=stop,
        target=target,
    )

    assert got.stop_r == pytest.approx(-0.5)
    assert got.terminal_outcome == "stop"
    assert got.terminal_r == pytest.approx(-0.5)


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target"),
    [
        (1, [99.4, 100.5], [99.5, 100.6], 99.0, 102.0),
        (-1, [100.5, 99.4], [100.6, 99.5], 101.0, 98.0),
    ],
)
def test_price_improved_horizon_close_uses_fill_anchor_and_approved_risk(
    direction, bids, asks, stop, target
):
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 59, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        stop=stop,
        target=target,
    )

    assert got.terminal_outcome == "required_horizon"
    assert got.terminal_r == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target", "close_r"),
    [
        (1, [99.9, 100.5, 103.0], [100.0, 100.6, 103.1], 99.0, 102.0, 0.5),
        (-1, [100.0, 99.4, 97.0], [100.1, 99.5, 97.1], 101.0, 98.0, 0.5),
    ],
)
def test_post_horizon_protection_quote_cannot_rewrite_horizon_close(
    direction, bids, asks, stop, target, close_r
):
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 59, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 1, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        order_type="MARKET",
        stop=stop,
        target=target,
        source_end=times[-1],
    )

    assert got.terminal_outcome == "required_horizon"
    assert got.terminal_at == times[1].isoformat()
    assert got.terminal_r == pytest.approx(close_r)


@pytest.mark.parametrize(
    ("direction", "bids", "asks", "stop", "target"),
    [
        (1, [99.9, 103.0], [100.0, 103.1], 99.0, 102.0),
        (-1, [100.0, 97.0], [100.1, 97.1], 101.0, 98.0),
    ],
)
def test_post_horizon_only_quote_leaves_lifecycle_not_evaluable(
    direction, bids, asks, stop, target
):
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 1, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, bids, asks),
        direction=direction,
        order_type="MARKET",
        stop=stop,
        target=target,
        source_end=times[-1],
    )

    assert got.measurement_status == "NOT_EVALUABLE"
    assert got.terminal_outcome is None


def test_resting_limit_uses_correct_side_and_preserves_equal_timestamp_order():
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(
            times,
            [99.5, 100.0, 97.8, 97.8],
            [99.6, 100.1, 97.9, 97.9],
        ),
        direction=-1,
        stop=101.0,
        target=98.0,
    )

    assert got.activation_class == "RESTING_LIMIT_AFTER_FIRST_STRICTLY_CAUSAL_QUOTE"
    assert got.first_causal_quote_index == 0
    assert got.correct_side_touch_index == 1
    assert got.correct_side_touch_at == got.first_causal_quote_at
    assert got.modelled_entry_price == 100.0
    assert got.terminal_outcome == "target"


@pytest.mark.parametrize("terminal_observed", [False, True])
def test_partial_capture_never_fabricates_horizon_but_retains_observed_terminal(
    terminal_observed,
):
    final_bid = 102.2 if terminal_observed else 100.2
    final_ask = 102.3 if terminal_observed else 100.3
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, [99.4, final_bid], [99.5, final_ask]),
        source_end=times[-1],
    )

    if terminal_observed:
        assert got.measurement_status == "EVALUATED"
        assert got.coverage_status == "VERIFIED_PREFIX_THROUGH_OBSERVED_TERMINAL"
        assert got.terminal_outcome == "target"
    else:
        assert got.measurement_status == "NOT_EVALUABLE"
        assert got.coverage_status == "PARTIAL_HORIZON_CAPTURE"
        assert got.terminal_outcome is None
        assert got.terminal_r is None
        assert got.detail["partial_capture_path_diagnostic"]["exit_reason"] == "capture_end"


def test_no_limit_touch_requires_full_horizon_coverage():
    t1 = dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc)
    horizon = dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc)
    full = _quote_lifecycle(
        OrderedQuoteTicks([t1, horizon], [100.5, 100.4], [100.6, 100.5])
    )
    partial = _quote_lifecycle(
        OrderedQuoteTicks([t1, t1 + dt.timedelta(minutes=1)], [100.5, 100.4], [100.6, 100.5]),
        source_end=t1 + dt.timedelta(minutes=1),
    )

    assert full.measurement_status == "EVALUATED"
    assert full.correct_side_touch_eligible is False
    assert full.modelled_lifecycle_status == "NO_CORRECT_SIDE_LIMIT_TOUCH_BEFORE_HORIZON"
    assert partial.measurement_status == "NOT_EVALUABLE"
    assert partial.correct_side_touch_eligible is None
    assert "required_horizon_not_covered" in partial.source_gaps[0]


def test_limit_touch_at_or_after_expiry_is_not_admitted():
    before = dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc)
    after = dt.datetime(2026, 1, 1, 9, 1, tzinfo=dt.timezone.utc)
    got = _quote_lifecycle(
        OrderedQuoteTicks([before, after], [100.5, 99.4], [100.6, 99.5]),
        source_end=after,
    )

    assert got.measurement_status == "EVALUATED"
    assert got.correct_side_touch_eligible is False
    assert got.modelled_entry_price is None


def test_unverified_source_prefix_and_conflicting_approved_risk_fail_closed():
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    ticks = OrderedQuoteTicks(times, [99.4, 102.0], [99.5, 102.1])
    unverified = _quote_lifecycle(ticks, coverage_verified=False)
    assert unverified.measurement_status == "NOT_EVALUABLE"
    assert unverified.modelled_entry_price is None
    with pytest.raises(ValueError, match="approved_risk_distance conflicts"):
        _quote_lifecycle(ticks, risk=0.5)


def test_entry_quote_already_through_stop_requires_order_event_sequence():
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, [98.9, 100.0], [99.5, 100.1])
    )

    assert got.measurement_status == "NOT_EVALUABLE"
    assert got.modelled_lifecycle_status == (
        "FIRST_TRADABLE_ENTRY_QUOTE_PAST_PROTECTION_GEOMETRY"
    )
    assert got.terminal_outcome is None
    assert "order_or_deal_evidence" in got.source_gaps[0]


def test_gap_target_precedes_modelled_client_partial_in_lifecycle_wrapper():
    times = [
        dt.datetime(2026, 1, 1, 8, 1, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 8, 2, tzinfo=dt.timezone.utc),
        dt.datetime(2026, 1, 1, 9, 0, tzinfo=dt.timezone.utc),
    ]
    got = _quote_lifecycle(
        OrderedQuoteTicks(times, [99.4, 104.0, 104.0], [99.5, 104.1, 104.1]),
        policy=ExitPolicy(partial_at_r=1.0),
    )

    path = got.detail["ordered_exit_path"]
    assert got.terminal_outcome == "target"
    assert got.terminal_price == 104.0
    assert "partial_banked_r" not in path["detail"]
    assert path["detail"]["partial_vs_target_priority"] == (
        "broker_resting_final_target_first_on_same_quote"
    )


_M1_BASE = dt.datetime(2026, 1, 1, 8, 0, tzinfo=dt.timezone.utc)
_M1_AUTHORITY_HASH = "a" * 64


def _m1_lifecycle(
    bars,
    *,
    times=None,
    direction=1,
    order_type="MARKET",
    submission=_M1_BASE + dt.timedelta(seconds=30),
    expiry=_M1_BASE + dt.timedelta(minutes=3),
    horizon=_M1_BASE + dt.timedelta(minutes=3),
    entry=100.0,
    stop=99.0,
    target=102.0,
    risk=1.0,
    price_basis=BarQuote.BID,
    spreads=None,
    source_verified=True,
    spec_hash=_M1_AUTHORITY_HASH,
    spread_hash=_M1_AUTHORITY_HASH,
):
    if times is None:
        times = [_M1_BASE + dt.timedelta(minutes=index) for index in range(len(bars))]
    if spreads is None:
        spreads = [0.2] * len(bars)
    return resolve_post_submission_m1_lifecycle(
        bars,
        m1_open_times_utc=times,
        direction=direction,
        proposed_order_type=order_type,
        submission_or_ack_time_utc=submission,
        expiry_utc=expiry,
        required_horizon_utc=horizon,
        approved_entry_price=entry,
        approved_stop_price=stop,
        approved_target_price=target,
        approved_risk_distance=risk,
        m1_price_basis=price_basis,
        spread_by_bar=spreads,
        source_interval_verified=source_verified,
        symbol_spec_hash_sha256=spec_hash,
        spread_source_hash_sha256=spread_hash,
    )


@pytest.mark.parametrize(
    ("direction", "successor", "stop", "target", "fill", "terminal_r"),
    [
        (1, bar(100.0, 102.2, 99.8, 101.5), 99.0, 102.0, 100.2, 1.8),
        (-1, bar(100.0, 100.5, 97.7, 98.5), 101.0, 98.0, 100.0, 2.0),
    ],
)
def test_m1_market_fills_first_complete_successor_open_on_correct_side(
    direction, successor, stop, target, fill, terminal_r
):
    # The submission bar deliberately spans both boundaries. MARKET ignores it.
    got = _m1_lifecycle(
        [bar(100.0, 103.0, 98.0, 100.0), successor, flat(100.0), flat(100.0)],
        direction=direction,
        stop=stop,
        target=target,
    )

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TARGET"
    assert got.modelled_fill_bar_index == 1
    assert got.modelled_fill_time_utc == (_M1_BASE + dt.timedelta(minutes=1)).isoformat()
    assert got.modelled_fill_price == pytest.approx(fill)
    assert got.terminal_state == "TARGET"
    assert got.terminal_gross_r == pytest.approx(terminal_r)
    assert got.evidence_class == "ALL24_M1_MODELLED_LIFECYCLE_NOT_BROKER_FILL"
    assert got.broker_fill_status == "NOT_EVALUABLE"
    assert got.broker_fill_claimed is False


def test_m1_limit_submission_bar_touch_is_censored_before_successor_scan():
    got = _m1_lifecycle(
        [bar(100.5, 100.6, 99.7, 100.5), flat(101.0), flat(101.0), flat(101.0)],
        order_type="LIMIT",
    )

    assert got.lifecycle_label_status == (
        "CENSORED_SUBMISSION_BAR_LIMIT_TOUCH_ORDERING"
    )
    assert got.modelled_fill_price is None
    assert got.censor_reason == "submission_bar_limit_touch_order_unresolved"


def test_m1_limit_favorable_successor_open_can_resolve_one_later_terminal_touch():
    got = _m1_lifecycle(
        [flat(101.0), bar(99.5, 102.2, 99.5, 101.8), flat(101.8), flat(101.8)],
        order_type="LIMIT",
    )

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TARGET"
    assert got.modelled_fill_price == pytest.approx(99.7)  # BID + source-bound spread
    assert got.terminal_price == pytest.approx(102.0)
    assert got.terminal_gross_r == pytest.approx(2.3)
    assert got.detail["fill_time_semantics"] == (
        "FAVORABLE_EXECUTABLE_SIDE_M1_OPEN_THROUGH_LIMIT"
    )
    # The proposed geometry and denominator are echoed unchanged after improvement.
    assert got.detail["order_contract"] == {
        "direction": 1,
        "submission_or_ack_time_utc": (
            _M1_BASE + dt.timedelta(seconds=30)
        ).isoformat(),
        "expiry_utc": (_M1_BASE + dt.timedelta(minutes=3)).isoformat(),
        "required_horizon_utc": (_M1_BASE + dt.timedelta(minutes=3)).isoformat(),
        "approved_entry_price": 100.0,
        "approved_stop_price": 99.0,
        "approved_target_price": 102.0,
        "approved_risk_distance": 1.0,
    }


def test_m1_intrabar_limit_fill_plus_terminal_touch_same_bar_is_censored():
    got = _m1_lifecycle(
        [flat(101.0), bar(100.8, 102.2, 99.7, 101.5), flat(101.5), flat(101.5)],
        order_type="LIMIT",
    )

    assert got.modelled_fill_price == 100.0
    assert got.lifecycle_label_status == "CENSORED_ORDERING_AMBIGUITY"
    assert got.censor_reason == "intrabar_limit_fill_and_terminal_touch_same_m1_bar"


def test_m1_both_terminal_boundaries_in_one_post_fill_bar_are_censored():
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), bar(100.0, 102.2, 98.8, 100.0), flat(100.0)]
    )

    assert got.lifecycle_label_status == "CENSORED_ORDERING_AMBIGUITY"
    assert got.censor_reason == "stop_and_target_touch_same_m1_bar"
    assert got.terminal_state is None


def test_m1_limit_full_expiry_path_without_touch_is_resolved_no_fill():
    got = _m1_lifecycle(
        [flat(100.5), flat(100.5), flat(100.5), flat(100.5)],
        order_type="LIMIT",
    )

    assert got.lifecycle_label_status == "RESOLVED_NO_FILL"
    assert got.terminal_state == "NO_FILL"
    assert got.terminal_time_utc == (_M1_BASE + dt.timedelta(minutes=3)).isoformat()
    assert got.modelled_fill_price is None
    assert got.terminal_gross_r is None


def test_m1_limit_open_fill_before_intrabar_expiry_is_causally_resolved():
    got = _m1_lifecycle(
        [flat(101.0), bar(99.5, 102.2, 99.5, 101.8), flat(101.8), flat(101.8)],
        order_type="LIMIT",
        expiry=_M1_BASE + dt.timedelta(minutes=1, seconds=30),
    )

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TARGET"
    assert got.modelled_fill_time_utc == (_M1_BASE + dt.timedelta(minutes=1)).isoformat()


def test_m1_no_fill_needs_no_row_opening_at_exact_expiry_boundary():
    got = _m1_lifecycle(
        [flat(100.5), flat(100.5), flat(100.5)],
        order_type="LIMIT",
    )

    assert got.lifecycle_label_status == "RESOLVED_NO_FILL"
    assert got.terminal_time_utc == (_M1_BASE + dt.timedelta(minutes=3)).isoformat()


def test_m1_missing_complete_successor_interval_is_censored_as_source_gap():
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), flat(100.0)],
        times=[
            _M1_BASE,
            _M1_BASE + dt.timedelta(minutes=2),
            _M1_BASE + dt.timedelta(minutes=3),
        ],
    )

    assert got.lifecycle_label_status == "CENSORED_SOURCE_INTERVAL_GAP"
    assert got.censor_reason == "m1_interval_gap_before_first_complete_successor"


@pytest.mark.parametrize(
    ("overrides", "reason"),
    [
        ({"price_basis": None}, "m1_price_basis_spread_or_symbol_spec_authority_missing"),
        ({"spec_hash": None}, "m1_price_basis_spread_or_symbol_spec_authority_missing"),
        ({"spreads": [0.2, None, 0.2, 0.2]}, "m1_spread_missing"),
    ],
)
def test_m1_missing_price_basis_spec_or_used_spread_is_censored(overrides, reason):
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), flat(100.0), flat(100.0)],
        **overrides,
    )

    assert got.lifecycle_label_status == "CENSORED_SPREAD_OR_SPEC_AUTHORITY"
    assert got.censor_reason == reason


@pytest.mark.parametrize("successor_open", [98.5, 102.1])
def test_m1_first_market_entry_quote_gap_through_stop_or_target_is_censored(
    successor_open,
):
    got = _m1_lifecycle(
        [flat(100.0), flat(successor_open), flat(successor_open), flat(successor_open)]
    )

    assert got.lifecycle_label_status == "CENSORED_INVALID_GAP_THROUGH_SL_OR_TP"
    assert got.terminal_state is None
    assert got.censor_reason == (
        "first_modelled_executable_entry_quote_through_stop_or_target"
    )


@pytest.mark.parametrize(
    ("direction", "bars", "stop", "target", "fill", "close", "expected_r"),
    [
        (
            1,
            [flat(100.0), flat(100.0), flat(100.6), flat(100.6)],
            99.0,
            102.0,
            100.2,
            100.6,
            0.4,
        ),
        (
            -1,
            [flat(100.0), flat(100.0), flat(99.4), flat(99.4)],
            101.0,
            98.0,
            100.0,
            99.6,
            0.4,
        ),
    ],
)
def test_m1_time_stop_preserves_signed_r_and_correct_exit_quote_side(
    direction, bars, stop, target, fill, close, expected_r
):
    got = _m1_lifecycle(bars, direction=direction, stop=stop, target=target)

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TIME_STOP"
    assert got.terminal_state == "TIME_STOP"
    assert got.modelled_fill_price == pytest.approx(fill)
    assert got.terminal_price == pytest.approx(close)
    assert got.terminal_gross_r == pytest.approx(expected_r)
    assert got.detail["time_stop_rule"] == (
        "LAST_COMPLETE_PRE_HORIZON_EXECUTABLE_EXIT_SIDE_CLOSE"
    )


def test_m1_known_open_gap_before_partial_horizon_resolves_before_ohlc_censor():
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), flat(102.1)],
        expiry=_M1_BASE + dt.timedelta(minutes=2),
        horizon=_M1_BASE + dt.timedelta(minutes=2, seconds=30),
    )

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TARGET"
    assert got.terminal_time_utc == (_M1_BASE + dt.timedelta(minutes=2)).isoformat()
    assert got.terminal_price == pytest.approx(102.1)


def test_m1_irrelevant_missing_later_spread_cannot_erase_prior_terminal_label():
    got = _m1_lifecycle(
        [flat(100.0), bar(100.0, 102.2, 99.8, 101.5), flat(101.5), flat(101.5)],
        spreads=[0.2, 0.2, None, None],
    )

    assert got.lifecycle_label_status == "RESOLVED_FILLED_TARGET"
    assert got.terminal_gross_r == pytest.approx(1.8)


def test_m1_conflicting_approved_risk_is_censored_as_geometry():
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), flat(100.0), flat(100.0)],
        risk=0.5,
    )

    assert got.lifecycle_label_status == "CENSORED_GEOMETRY"
    assert got.censor_reason == "approved_risk_distance_conflicts_with_geometry"


def test_m1_high_price_tight_stop_rejects_material_r_denominator_mismatch():
    got = _m1_lifecycle(
        [flat(100000.0), flat(100000.0), flat(100000.0), flat(100000.0)],
        entry=100000.0,
        stop=99999.9999,
        target=100000.0002,
        risk=0.00015,
        spreads=[0.0, 0.0, 0.0, 0.0],
    )

    assert got.lifecycle_label_status == "CENSORED_GEOMETRY"
    assert got.censor_reason == "approved_risk_distance_conflicts_with_geometry"


def test_m1_invalid_geometry_censor_is_strict_json_safe():
    got = _m1_lifecycle(
        [flat(100.0), flat(100.0), flat(100.0), flat(100.0)],
        entry=None,
    )

    assert got.lifecycle_label_status == "CENSORED_GEOMETRY"
    assert got.detail["order_contract"]["approved_entry_price"] is None
    json.dumps(got.as_dict(), allow_nan=False)


def test_observed_ask_bars_close_the_scalar_short_spread_residual():
    bid = [flat(100.0), bar(100.0, 100.6, 99.8, 100.1), flat(100.1)]
    ask = [flat(100.2), bar(100.3, 101.1, 100.1, 100.5), flat(100.5)]
    got = walk_observed_book(
        ObservedBookBars(bid, ask),
        0,
        -1,
        stop_dist=1.0,
        policy=ExitPolicy(target_dist=2.0, maxbars=2),
    )
    assert got.entry_price == pytest.approx(100.0)  # short sells at BID
    assert got.entry_spread == pytest.approx(0.2)
    assert got.observed.exit_reason == "stop"       # ASK high 101.1 crossed 101.0
    assert got.observed.r_gross == pytest.approx(-1.0)
    assert got.scalar.exit_reason == "maxbars"      # constant .2 spread misses it
    assert got.observed_vs_scalar_reason_changed is True


@pytest.mark.parametrize(
    "direction,opening,expected_r",
    [(1, 95.0, -5.0), (-1, 105.0, -5.0)],
)
def test_opening_gap_stop_fills_at_first_tradable_quote(direction, opening, expected_r):
    bars = [flat(100.0), flat(opening)]
    old = replay(bars, 0, direction, stop_dist=1.0, policy=ExitPolicy(maxbars=1))
    new = replay(
        bars,
        0,
        direction,
        stop_dist=1.0,
        policy=ExitPolicy(maxbars=1),
        first_tradable_fills=True,
    )
    assert old.r_gross == pytest.approx(-1.0)
    assert new.exit_reason == "stop"
    assert new.r_gross == pytest.approx(expected_r)
    # The bar ended after the opening fill, so later OHLC cannot enter excursion.
    assert new.mfe_r == pytest.approx(0.0)
    assert new.mae_r == pytest.approx(expected_r)


def test_opening_gap_target_uses_only_observed_price_improvement():
    bars = [flat(100.0), flat(103.0)]
    got = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=ExitPolicy(target_dist=2.0, maxbars=1),
        first_tradable_fills=True,
    )
    assert got.exit_reason == "target"
    assert got.r_gross == pytest.approx(3.0)


@pytest.mark.parametrize(
    "direction,opening,bar_high,bar_low",
    [
        (1, 102.0, 102.2, 99.8),
        (-1, 98.0, 100.2, 97.8),
    ],
)
def test_opening_gap_partial_transacts_at_first_quote_then_updates_be(
    direction, opening, bar_high, bar_low
):
    bars = [flat(100.0), bar(opening, bar_high, bar_low, 100.0)]
    got = replay(
        bars,
        0,
        direction,
        stop_dist=1.0,
        policy=ExitPolicy(
            target_dist=3.0,
            partial_at_r=1.0,
            partial_frac=0.5,
            maxbars=1,
        ),
        first_tradable_fills=True,
    )
    # The opening quote is +2R and crosses the partial before the +3R target.
    # Half banks at the actually tradable +2R quote (1R banked), then the updated
    # breakeven stop wins the remaining same-bar ambiguity.
    assert got.exit_reason == "stop"
    assert got.r_gross == pytest.approx(1.0)
    assert got.detail["partial_banked_r"] == pytest.approx(1.0)
    assert got.detail["partial_fill_price"] == pytest.approx(opening)
    assert got.detail["partial_fill_convention"] == (
        "modelled_client_partial_first_quote_no_order_event"
    )
    assert got.detail["partial_order_event_authority"].startswith("NOT_AVAILABLE")


@pytest.mark.parametrize("direction,opening", [(1, 104.0), (-1, 96.0)])
def test_opening_gap_broker_target_prevents_double_client_partial(direction, opening):
    bars = [flat(100.0), flat(opening)]
    got = replay(
        bars,
        0,
        direction,
        stop_dist=1.0,
        policy=ExitPolicy(target_dist=3.0, partial_at_r=1.0, maxbars=1),
        first_tradable_fills=True,
    )
    assert got.exit_reason == "target"
    assert got.r_gross == pytest.approx(4.0)
    assert "partial_banked_r" not in got.detail
    assert "partial_fill_price" not in got.detail
    assert got.detail["partial_vs_target_priority"] == (
        "broker_resting_final_target_first_on_same_quote"
    )


def test_partial_path_is_exactly_unchanged_when_first_tradable_input_is_absent():
    bars = [flat(100.0), bar(100.0, 102.0, 99.8, 101.5), flat(100.0)]
    policy = ExitPolicy(target_dist=3.0, partial_at_r=1.0, maxbars=2)
    legacy = replay(bars, 0, 1, stop_dist=1.0, policy=policy)
    explicit_off = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=policy,
        first_tradable_fills=False,
    )
    assert legacy.as_dict() == explicit_off.as_dict()


def test_partial_without_target_still_declares_missing_order_event_authority():
    bars = [flat(100.0), flat(102.0)]
    got = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=ExitPolicy(partial_at_r=1.0, maxbars=1),
        first_tradable_fills=True,
    )
    assert got.detail["partial_order_event_authority"] == (
        "NOT_AVAILABLE_MODELLED_CLIENT_ACTION"
    )


def test_same_bar_trail_formation_never_inherits_the_bar_open_as_a_gap_fill():
    bars = [flat(100.0), bar(100.0, 108.0, 99.6, 100.1)]
    got = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=ExitPolicy(trail_arm=0.5, trail_gap=0.5, maxbars=1),
        first_tradable_fills=True,
    )
    assert got.exit_reason == "trail"
    assert got.r_gross == pytest.approx(7.5)


def test_preexisting_trail_gap_fills_at_the_next_bar_open():
    bars = [
        flat(100.0),
        bar(100.0, 104.0, 103.8, 103.9),  # leaves a 103.5 trail standing
        bar(100.1, 100.3, 99.9, 100.0),
    ]
    got = replay(
        bars,
        0,
        1,
        stop_dist=1.0,
        policy=ExitPolicy(trail_arm=0.5, trail_gap=0.5, maxbars=2),
        first_tradable_fills=True,
    )
    assert got.exit_reason == "trail"
    assert got.exit_index == 2
    assert got.r_gross == pytest.approx(0.1)


# ------------------------------------------------- trail and scale-out variants


def test_trail_arms_one_spread_later_and_fills_on_the_exit_side():
    """`trailing_runner` is the live contract of `asian_fade` / `metal_session_reversion`.

    Close 100, spread 0.20, stop 1.00, arm at +0.50, gap 0.40.
    Old: arms when the tape reaches 100.50, running max 100.90 -> fills at 100.50,
         R = (100.50 - 100.00)/1.00 = +0.50.
    True: the long paid 100.20, so it arms at 100.70 (still armed by the 100.90 high) and
         fills at 100.90 - 0.40 = 100.50 on the BID, R = (100.50 - 100.20)/1.00 = +0.30.
    """
    bars = [flat(100.0), bar(100.0, 100.90, 100.0, 100.4), flat(100.4)]
    pol = ExitPolicy(trail_arm=0.50, trail_gap=0.40, maxbars=2)
    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "trail"
    assert old.r_gross == pytest.approx(0.50)
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "trail"
    assert t.corrected.r_gross == pytest.approx(0.30)


def test_trail_that_no_longer_arms():
    """One spread of arming displacement can remove the trail exit entirely."""
    bars = [flat(100.0), bar(100.0, 100.60, 100.0, 100.1), flat(100.1)]
    pol = ExitPolicy(trail_arm=0.50, trail_gap=0.40, maxbars=2)
    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "trail"
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    # arm level is 100.70; the bar's high of 100.60 never reaches it
    assert t.corrected.exit_reason == "maxbars"
    assert t.corrected.r_gross == pytest.approx((100.1 - 100.2) / 1.0)


def test_partial_be_runner_scale_out_moves_with_the_anchor():
    """`partial_be_runner` is the live contract of `energy_agri` and `metals_core`.

    Close 100, spread 0.20, stop 1.00, scale out half at +1R, breakeven after.
    Old: partial level 101.00, banked 0.5 * 1.0 = 0.5, BE stop at 100.00.
    True: partial level 101.20, banked 0.5, BE stop at 100.20.
    Bar 1: high 101.30 (takes both partial levels), low 100.5, close 101.0.
    Bar 2: low 100.10 -> hits the TRUE BE stop at 100.20, not the old one at 100.00.
    """
    bars = [flat(100.0), bar(100.0, 101.30, 100.5, 101.0),
            bar(101.0, 101.1, 100.10, 100.9), flat(100.9)]
    pol = ExitPolicy(partial_at_r=1.0, partial_frac=0.5, maxbars=3)
    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "maxbars"
    # banked 0.5 + half of (100.9 - 100.0)/1.0 = 0.5 + 0.45
    assert old.r_gross == pytest.approx(0.95)
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "stop"
    # banked 0.5 + half of (100.20 - 100.20)/1.0 = 0.5
    assert t.corrected.r_gross == pytest.approx(0.50)


# ------------------------------------------------------------ level anchoring


def test_level_anchored_short_shifts_and_long_does_not():
    """A generator that rests a pending order at an absolute structural level.

    A LONG's exits are bid-quoted, so on a bid tape its levels resolve unshifted and the
    displacement lands on the ENTRY trigger instead. A SHORT's exits are ask-quoted and
    take the full shift.
    """
    bars = [flat(100.0), bar(100.0, 100.1, 99.05, 100.0), flat(100.0)]
    pol = ExitPolicy(target_dist=2.0, maxbars=2)
    lt = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID,
              policy=pol, anchor=LevelAnchor.LEVEL, entry_level=100.0)
    assert lt.anchor == pytest.approx(100.0)          # no shift for a long
    assert lt.corrected.r_gross == lt.uncorrected.r_gross
    st = walk(bars, 0, -1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID,
              policy=pol, anchor=LevelAnchor.LEVEL, entry_level=100.0)
    assert st.anchor == pytest.approx(99.80)          # full shift for a short


def test_level_anchor_argument_hygiene():
    bars = [flat(100.0), flat(100.0)]
    with pytest.raises(ValueError):
        walk(bars, 0, 1, stop_dist=1.0, spread=0.1, bar_quote=BarQuote.BID,
             anchor=LevelAnchor.LEVEL)
    with pytest.raises(ValueError):
        walk(bars, 0, 1, stop_dist=1.0, spread=0.1, bar_quote=BarQuote.BID,
             entry_level=100.0)
    with pytest.raises(ValueError):
        replay_anchor(100.0, 0, 0.1, BarQuote.BID)
    with pytest.raises(ValueError):
        replay_anchor(100.0, 1, -0.1, BarQuote.BID)


# ------------------------------------------------------------------ fail closed


def test_spread_for_fails_closed_on_an_unknown_symbol():
    with pytest.raises(SpreadUnavailable):
        spread_for("NOT_A_SYMBOL_XYZ", dt.datetime(2026, 1, 15, tzinfo=dt.timezone.utc))


def test_spread_for_returns_a_positive_price_for_a_measured_symbol():
    s = spread_for("XAUUSD", dt.datetime(2026, 1, 15, 12, tzinfo=dt.timezone.utc))
    assert s > 0
    # sanity: gold quotes in the tenths, not the hundreds
    assert 0.001 < s < 50.0


def _sweep(pol, n=3000, seed=20260807):
    import random

    rng = random.Random(seed)
    out = []
    for _ in range(n):
        px = 100.0
        bars = [flat(px)]
        for _k in range(12):
            o = px
            hi = o + rng.uniform(0, 1.5)
            lo = o - rng.uniform(0, 1.5)
            c = rng.uniform(lo, hi)
            bars.append(bar(o, hi, lo, c))
            px = c
        d = rng.choice((1, -1))
        out.append(walk(bars, 0, d, stop_dist=1.0, spread=rng.uniform(0.01, 0.3),
                        bar_quote=BarQuote.BID, policy=pol))
    return out


@pytest.mark.parametrize("pol", [
    ExitPolicy(target_dist=2.0, maxbars=12),
    ExitPolicy(maxbars=12, time_stop_bars=6),
    ExitPolicy(maxbars=12),
])
def test_stop_target_time_policies_are_monotone_per_trade(pol):
    """For stop / target / clock exits the correction can NEVER help a single trade.

    Provable, and worth stating because it is what licenses reading a pooled delta on
    those sleeves as a bound: the stop only ever moves nearer, the target only ever moves
    further, and an exit at the true target books exactly +T. A path that misses the true
    target and later exceeds it would have exited at it, so no maxbars close can beat +T.
    """
    for t in _sweep(pol):
        assert t.delta_r <= 1e-12, t.as_dict()


@pytest.mark.parametrize("pol,label", [
    (ExitPolicy(trail_arm=0.5, trail_gap=0.4, maxbars=12), "trailing_runner"),
    (ExitPolicy(partial_at_r=1.0, target_dist=3.0, maxbars=12), "partial_be_runner"),
])
def test_path_dependent_policies_are_not_monotone_but_are_negative_pooled(pol, label):
    """`trailing_runner` and `partial_be_runner` CAN gain on an individual trade.

    A trail that arms one spread later can exit later and better; a scale-out that is not
    taken leaves full size in a winner. This is not a defect in the correction, it is a
    property of path-dependent exits, and it means **a per-trade bound does not exist for
    the four `partial_be_runner` sleeves or the two `trailing_runner` sleeves** — only a
    pooled one. `energy_agri` and `metals_core` are armed and are `partial_be_runner`.
    """
    rs = _sweep(pol)
    deltas = [t.delta_r for t in rs]
    pos = [x for x in deltas if x > 1e-12]
    assert pos, f"{label} was expected to be non-monotone on at least one path"
    assert sum(deltas) / len(deltas) < 0.0


def test_trail_can_gain_from_arming_later():
    """The non-monotonicity, hand-built, so the mechanism is legible.

    Close 100, spread 0.20, stop 1.00, arm +0.50, gap 0.40.
    Bar 1 high 100.55, low 100.0: the OLD walk arms at 100.50 and, with the running max
    at 100.55, its trail level is 100.15 — which bar 2's low of 100.10 takes out, booking
    +0.15 R. The corrected walk needs 100.70 to arm, so it is still unarmed on bar 2 and
    rides bar 3's high to 102.00, arming and trailing out at 101.60 for +1.40 R.
    """
    bars = [flat(100.0),
            bar(100.0, 100.55, 100.00, 100.5),
            bar(100.5, 100.6, 100.10, 100.2),
            bar(100.2, 102.00, 100.2, 101.0),
            flat(101.0)]
    pol = ExitPolicy(trail_arm=0.50, trail_gap=0.40, maxbars=4)
    old = replay(bars, 0, 1, stop_dist=1.0, policy=pol)
    assert old.exit_reason == "trail"
    assert old.r_gross == pytest.approx(0.15)
    t = walk(bars, 0, 1, stop_dist=1.0, spread=0.20, bar_quote=BarQuote.BID, policy=pol)
    assert t.corrected.exit_reason == "trail"
    assert t.corrected.r_gross == pytest.approx(101.60 - 100.20)
    assert t.delta_r > 0
