"""The pre-gap bar: `candles_to_bars` must keep a last candle it can prove is closed.

Session AB measured that the live book cannot reach the last closed bar before any session
gap (`phase6/receipts/AB_PORT_PARITY_V1.json`: 29 fires across five H4 sleeves, 29 of 29
immediately before a gap of >= 2 intervals). The mechanism is here — `rows = candles[:-1]`
unconditionally — and the fix is a proof obligation, not a heuristic: keep the last candle
only when `time + interval <= now`.

The first test is the one that matters most: **the default must not move.** A capability
that silently changed live generation on a funded account would be the wrong kind of
repair.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from src.components.ultimate_book.bar_provider import TF_H4, candles_to_bars


def _candles(n: int, start: datetime, interval_h: int = 4) -> list[dict]:
    return [{"time": (start + timedelta(hours=interval_h * i)).isoformat(),
             "open": 100.0 + i, "high": 101.0 + i, "low": 99.0 + i,
             "close": 100.5 + i, "volume": 10.0}
            for i in range(n)]


T0 = datetime(2026, 1, 5, 0, 0, tzinfo=timezone.utc)


def test_default_behaviour_is_byte_identical_without_now():
    """No `now`, no change. Every existing caller keeps exactly what it had."""
    c = _candles(5, T0)
    bars, times = candles_to_bars(c)
    assert len(bars) == 4
    assert times[-1] == T0 + timedelta(hours=12)
    # explicit `now` but no interval is still the old path
    bars2, times2 = candles_to_bars(c, now=T0 + timedelta(hours=99))
    assert (len(bars2), times2) == (len(bars), times)


def test_last_candle_is_kept_when_its_interval_has_elapsed():
    """A session close: the last candle's interval is over, so it is closed, not forming."""
    c = _candles(5, T0)
    last_open = T0 + timedelta(hours=16)
    bars, times = candles_to_bars(c, now=last_open + timedelta(hours=4),
                                  interval_minutes=240)
    assert len(bars) == 5, "the freshly-closed pre-gap bar must survive"
    assert times[-1] == last_open


def test_last_candle_is_still_dropped_while_it_is_forming():
    """Mid-session: the last candle's interval has NOT elapsed, so it is forming."""
    c = _candles(5, T0)
    last_open = T0 + timedelta(hours=16)
    bars, _times = candles_to_bars(c, now=last_open + timedelta(hours=1),
                                   interval_minutes=240)
    assert len(bars) == 4


def test_a_stale_feed_two_intervals_behind_still_keeps_its_last_closed_bar():
    """Monday morning, Friday's last bar: still closed, so still kept."""
    c = _candles(5, T0)
    last_open = T0 + timedelta(hours=16)
    bars, times = candles_to_bars(c, now=last_open + timedelta(days=3),
                                  interval_minutes=240)
    assert len(bars) == 5 and times[-1] == last_open


def test_naive_now_is_treated_as_utc_not_rejected():
    c = _candles(3, T0)
    last_open = T0 + timedelta(hours=8)
    bars, _t = candles_to_bars(c, now=(last_open + timedelta(hours=4)).replace(tzinfo=None),
                               interval_minutes=240)
    assert len(bars) == 3


def test_drop_forming_false_still_wins():
    c = _candles(4, T0)
    bars, _t = candles_to_bars(c, drop_forming=False, now=T0, interval_minutes=240)
    assert len(bars) == 4


def test_unparseable_last_timestamp_falls_back_to_dropping():
    """Fail closed: if the proof is unavailable, keep the conservative behaviour."""
    c = _candles(4, T0)
    c[-1]["time"] = "not-a-timestamp"
    bars, _t = candles_to_bars(c, now=T0 + timedelta(days=9), interval_minutes=240)
    assert len(bars) == 3


def test_get_closed_bars_threads_the_arguments_through():
    class _Feed:
        def get_candles(self, symbol, timeframe, count):
            return _candles(5, T0)

    from src.components.ultimate_book.bar_provider import get_closed_bars

    bars, _t = get_closed_bars(_Feed(), "XAUUSD", TF_H4, 5,
                               now=T0 + timedelta(hours=20), interval_minutes=240)
    assert len(bars) == 5
    bars2, _t2 = get_closed_bars(_Feed(), "XAUUSD", TF_H4, 5)
    assert len(bars2) == 4, "the default must not move"
