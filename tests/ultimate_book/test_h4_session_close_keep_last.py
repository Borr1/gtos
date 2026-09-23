"""FRA40 Friday 17:00: keep the last closed H4 when there is no next forming bar.

Last candle is dropped as forming. At cash-index session close there is no next
forming bar, so the real last closed H4 is discarded. Friday 17:00:20Z FRA40
cash last candle is the 13:00 H4 (CAC closed ~15:30Z). Drop -> decision_bar
09:00Z, while EU50/GER40 still have a 17:00 forming candle -> drop -> 13:00Z.

H4 generation now always passes now+interval so a last candle with
time+240min <= now is kept. Recency still marks true-stale slots
stale_decision_bar. D1 is not flipped.
"""

from __future__ import annotations

from datetime import datetime, timezone

from src.components.ultimate_book.bar_provider import TF_H4, candles_to_bars, get_closed_bars


def _h4(open_iso: str) -> dict:
    return {
        "time": open_iso,
        "open": 100.0,
        "high": 101.0,
        "low": 99.0,
        "close": 100.5,
        "volume": 10.0,
    }


def test_fra40_friday_1700_keeps_the_1300_h4_under_default_drop_forming():
    """H4 candles ending 09:00 and 13:00, now=17:00:20Z — 13:00 must be kept."""
    candles = [
        _h4("2026-08-14T09:00:00+00:00"),
        _h4("2026-08-14T13:00:00+00:00"),
    ]
    now = datetime(2026, 8, 14, 17, 0, 20, tzinfo=timezone.utc)
    bars, times = candles_to_bars(
        candles, drop_forming=True, now=now, interval_minutes=240
    )
    assert len(bars) == 2
    assert times[-1] == datetime(2026, 8, 14, 13, 0, tzinfo=timezone.utc)
    # 13:00 + 240min = 17:00 <= 17:00:20
    assert (times[-1].hour, times[-1].minute) == (13, 0)


def test_get_closed_bars_keep_last_on_the_same_fra40_clock():
    class _Feed:
        def get_candles(self, symbol, timeframe, count):
            return [
                _h4("2026-08-14T09:00:00+00:00"),
                _h4("2026-08-14T13:00:00+00:00"),
            ]

    now = datetime(2026, 8, 14, 17, 0, 20, tzinfo=timezone.utc)
    bars, times = get_closed_bars(
        _Feed(), "FRA40", TF_H4, 3, now=now, interval_minutes=240
    )
    assert len(bars) == 2
    assert times[-1] == datetime(2026, 8, 14, 13, 0, tzinfo=timezone.utc)


def test_still_forming_1700_h4_is_dropped_at_1700_20():
    """If a 17:00 candle exists (EU50/GER40), it is still forming at 17:00:20."""
    candles = [
        _h4("2026-08-14T09:00:00+00:00"),
        _h4("2026-08-14T13:00:00+00:00"),
        _h4("2026-08-14T17:00:00+00:00"),
    ]
    now = datetime(2026, 8, 14, 17, 0, 20, tzinfo=timezone.utc)
    bars, times = candles_to_bars(
        candles, drop_forming=True, now=now, interval_minutes=240
    )
    assert times[-1] == datetime(2026, 8, 14, 13, 0, tzinfo=timezone.utc)
    assert len(bars) == 2
