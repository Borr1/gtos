"""Two live-risk defects the VPS merge (46c526bfe) brought in with it.

1. `_normalize_future_bar_times` chose its broker offset by scanning for the
   first value that made the bar look fresh *relative to now*. `times[-1]`
   becomes `decision_bar_iso`, which is the placement-ledger idempotency key
   (`placement_ledger.py:1,88`), so the same bar acquired a new key as the wall
   clock advanced. Within a day the one-unit-per-(sleeve,symbol,day) cap
   (`book_owner.py:1601-1606`) absorbs that; across a UTC date boundary the
   derived decision *day* changes too and nothing does.

2. The merge swapped `bool()` for `config_bool_value(..., default)` everywhere.
   That is correct for an authority gate — unknown means no authority — but on
   the two operator SAFETY flags it inverted the fail direction: an unrecognised
   value silently DISARMED the circuit breaker and DISABLED breach-flatten,
   where the pre-merge `bool("maybe")` armed them.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components.ultimate_book.book_engine import UltimateBookLiveEngine
from src.components.ultimate_book.bridge import config_bool_value, config_safety_flag

H4_MINUTES = 240


class _OffsetMT5:
    """Only the surface the repair touches."""

    def __init__(self, offset_seconds=0):
        self._offset = offset_seconds

    def get_broker_offset_seconds(self):
        return self._offset


def _engine(mt5) -> UltimateBookLiveEngine:
    engine = UltimateBookLiveEngine.__new__(UltimateBookLiveEngine)
    engine.config = {}
    engine._mt5 = mt5
    return engine


def _series(last_close_utc: datetime, n=5, minutes=H4_MINUTES) -> list[datetime]:
    """Aligned bar-OPEN times whose last bar closes at `last_close_utc`."""

    last_open = last_close_utc - timedelta(minutes=minutes)
    return [last_open - timedelta(minutes=minutes * i) for i in range(n - 1, -1, -1)]


# --------------------------------------------------------------------------
# 1. The decision-bar stamp must not move with the wall clock
# --------------------------------------------------------------------------


def test_the_repaired_decision_bar_does_not_drift_with_the_wall_clock():
    """THE regression test. A drifting stamp is a duplicate live position."""

    engine = _engine(_OffsetMT5(offset_seconds=0))
    # A broker-local (leaked) series: mid-day so no date boundary is involved.
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    times = _series(now + timedelta(hours=2))       # closes 2h in the "future"

    stamps = set()
    for minutes_later in (0, 30, 60, 90, 120, 180):
        repaired, offset = engine._normalize_future_bar_times(
            list(times),
            now=now + timedelta(minutes=minutes_later),
            interval_minutes=H4_MINUTES,
            cache_key=("XAUUSD", 16388, 260),
        )
        stamps.add(repaired[-1].isoformat())

    assert len(stamps) == 1, (
        f"the decision-bar stamp moved with the wall clock: {sorted(stamps)}. "
        "That is the placement-ledger idempotency key."
    )


def test_the_stamp_survives_a_restart(tmp_path):
    """The case an in-process memo cannot cover, and the reason the memo is
    persisted rather than the repair being refused.

    A restart inside the same bar rebuilds the memo. If it re-derived the offset
    from a new `now`, the same bar would get a new `decision_bar_iso` -- and if
    that shifted across midnight, a new `decision_day` too, which is the one
    thing the per-day placement cap cannot absorb.

    An earlier version of this fix bought that guarantee by REFUSING any repair
    that changed the UTC day. It worked and it dropped 12.5 % of M15 and H1 bars
    per day in the leaked-offset state. Persisting the memo gives the same
    guarantee for free.
    """

    state = tmp_path / "pipeline_state" / "ultimate_book" / "ftmo" / "bar_time_repair.json"
    now = datetime(2026, 7, 20, 0, 30, tzinfo=timezone.utc)
    times = _series(datetime(2026, 7, 20, 2, 0, tzinfo=timezone.utc))

    first = _engine(_OffsetMT5(offset_seconds=0))
    first._bar_offset_state_path = str(state)
    a, off_a = first._normalize_future_bar_times(
        list(times), now=now, interval_minutes=H4_MINUTES, cache_key=("BTCUSD", 16388, 260)
    )
    assert state.is_file(), "the memo was not persisted, so a restart cannot reuse it"

    # A restart three hours later: fresh process, fresh memo, same bar.
    second = _engine(_OffsetMT5(offset_seconds=0))
    second._bar_offset_state_path = str(state)
    second._bar_offset_latch = second._load_bar_offset_latch()
    b, off_b = second._normalize_future_bar_times(
        list(times), now=now + timedelta(hours=3), interval_minutes=H4_MINUTES,
        cache_key=("BTCUSD", 16388, 260),
    )

    assert off_a == off_b
    assert a[-1] == b[-1], "the same bar got a different stamp after a restart"
    assert a[-1].date() == b[-1].date(), "the decision DAY moved across a restart"


def test_the_repair_no_longer_drops_bars_to_stay_stable():
    """Regression on the fix's own cost. The date-boundary refusal it replaced
    dropped 12.5 % of M15 and H1 bars per day in the leaked-offset state."""

    unrepaired = 0
    for slot in range(96):                       # a full day of M15 bars
        engine = _engine(_OffsetMT5(offset_seconds=0))
        true_close = datetime(2026, 7, 20, tzinfo=timezone.utc) + timedelta(minutes=15 * (slot + 1))
        times = _series(true_close + timedelta(hours=3), minutes=15)
        _, offset = engine._normalize_future_bar_times(
            list(times), now=true_close + timedelta(seconds=30), interval_minutes=15,
            cache_key=("USDJPY", 15, 260),
        )
        if not offset:
            unrepaired += 1
    assert unrepaired == 0, f"{unrepaired}/96 M15 bars still dropped by the repair"


def test_the_adapter_offset_is_preferred_over_a_search():
    """The broker offset is a property of the broker. `RealMT5` already detects
    it; the engine should not re-derive it from bar times and a clock."""

    engine = _engine(_OffsetMT5(offset_seconds=3 * 3600))
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    times = _series(now + timedelta(hours=3))

    repaired, offset = engine._normalize_future_bar_times(
        list(times), now=now, interval_minutes=H4_MINUTES, cache_key=("EURUSD", 16388, 260)
    )

    assert offset == 3 * 3600
    assert repaired[-1] == times[-1] - timedelta(hours=3)


def test_a_healthy_series_is_returned_untouched():
    """In the normal case `mt5_real.get_candles` has already corrected the
    offset, so this must be a no-op — including no latch entry."""

    engine = _engine(_OffsetMT5(offset_seconds=3 * 3600))
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    times = _series(now - timedelta(minutes=5))

    repaired, offset = engine._normalize_future_bar_times(
        list(times), now=now, interval_minutes=H4_MINUTES, cache_key=("XAUUSD", 16388, 260)
    )

    assert offset is None
    assert repaired == times


def test_healthy_positive_adapter_clears_colliding_fallback_memo():
    """A raw ISO repaired under a poisoned offset can later be the true UTC bar.

    Once the adapter has a positive offset and presents a healthy series, the old
    fallback must not shift that same ISO a second time.
    """

    engine = _engine(_OffsetMT5(offset_seconds=3 * 3600))
    now = datetime(2026, 8, 12, 23, 0, 34, tzinfo=timezone.utc)
    times = _series(datetime(2026, 8, 12, 23, 0, tzinfo=timezone.utc), minutes=15)
    cache_key = ("EURUSD", 15, 260)
    memo_key = (cache_key, times[-1].isoformat())
    engine._bar_offset_latch = {memo_key: 3600}

    repaired, offset = engine._normalize_future_bar_times(
        list(times), now=now, interval_minutes=15, cache_key=cache_key
    )

    assert offset is None
    assert repaired == times
    assert engine._bar_offset_latch[memo_key] is None


def test_an_unrepairable_skew_leaves_the_fail_safe_to_skip_the_bar():
    engine = _engine(_OffsetMT5(offset_seconds=0))
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    times = _series(now + timedelta(hours=40))      # far outside any broker offset

    repaired, offset = engine._normalize_future_bar_times(
        list(times), now=now, interval_minutes=H4_MINUTES, cache_key=("US30_cash", 16388, 260)
    )

    assert offset is None
    assert repaired == times                        # still future -> caller skips it


def test_the_latch_is_per_symbol_timeframe():
    """One symbol's repair must not stamp another symbol's bars."""

    engine = _engine(_OffsetMT5(offset_seconds=0))
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

    a, off_a = engine._normalize_future_bar_times(
        _series(now + timedelta(hours=2)), now=now, interval_minutes=H4_MINUTES,
        cache_key=("XAUUSD", 16388, 260),
    )
    b, off_b = engine._normalize_future_bar_times(
        _series(now + timedelta(hours=4)), now=now, interval_minutes=H4_MINUTES,
        cache_key=("BTCUSD", 16388, 260),
    )

    keys = list(engine._bar_offset_latch)
    assert {k[0] for k in keys} == {("XAUUSD", 16388, 260), ("BTCUSD", 16388, 260)}
    assert off_a and off_b


# --------------------------------------------------------------------------
# 2. Safety flags must fail toward protection
# --------------------------------------------------------------------------


@pytest.mark.parametrize("garbage", ["maybe", "ARMED?", "tru", "", "  ", "2026-07-26"])
def test_an_unparseable_safety_flag_arms_rather_than_disarms(garbage):
    assert config_safety_flag({"k": garbage}, "k", default_when_absent=False) is True
    # ...where the general-purpose parser resolves the same value to the default,
    # which is right for an authority gate and wrong here.
    assert config_bool_value(garbage, False) is False


def test_an_absent_safety_flag_keeps_its_documented_default():
    assert config_safety_flag({}, "ultimate_book_flatten_on_breach", default_when_absent=False) is False
    assert config_safety_flag({}, "x", default_when_absent=True) is True
    assert config_safety_flag({"x": None}, "x", default_when_absent=False) is False


@pytest.mark.parametrize(
    "value,expected",
    [(True, True), (False, False), ("true", True), ("false", False), ("ON", True),
     ("off", False), ("disabled", False), ("enabled", True), (1, True), (0, False)],
)
def test_recognised_safety_flag_values_are_unchanged(value, expected):
    assert config_safety_flag({"k": value}, "k", default_when_absent=False) is expected


def test_the_two_operator_safety_flags_use_the_fail_safe_resolver():
    """A census: if a future edit swaps one back to `config_bool_value`, the
    fail direction silently inverts again and no behavioural test would notice
    (the values in every committed config parse cleanly)."""

    import pathlib

    source = pathlib.Path(
        __file__
    ).resolve().parents[2].joinpath("src/components/ultimate_book/book_engine.py").read_text()

    for flag in ("ultimate_book_operator_circuit_breaker", "ultimate_book_flatten_on_breach"):
        for line in source.splitlines():
            if flag in line and "config_bool_value" in line:
                pytest.fail(f"{flag} resolved with config_bool_value; it must fail toward protection")
        assert f'"{flag}"' in source
