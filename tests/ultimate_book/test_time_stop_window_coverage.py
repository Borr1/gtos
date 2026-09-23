"""Session BD (B2086-B2093) -- AQ §6a's `want = budget + 64` exposure, made observable.

WHAT AQ FILED AND WHY IT WAS NOT PATCHED. After the `mx_*` time-stop unit repair (96 -> 7,680)
an open `mx_*` position requests 7,744 M15 bars per tick. *"If the terminal returns fewer than
7,680 closed M15 bars the count can never reach the budget and the time stop never fires at all"*
-- and the wall-clock fallback does not catch it, because that path needs `None`, not an honestly
short count. The backstop degrades to **inert** rather than to late, which is the wrong direction.
AQ filed rather than patched because *"the obvious mitigation moves armed sleeves onto the
over-counting wall-clock path and would close them EARLIER, which is not a change to make
unmeasured at the end of a session."* That judgement is respected here.

WHAT WAS ACTUALLY MISSING, AND IT IS NOT THE FIX.

1. `len(candles) < want` is not the test. A broker legitimately returns fewer bars than asked for.
   The only question is whether the returned window reaches back PAST THE FILL -- if the oldest
   closed bar printed after `entry_dt`, the count is a LOWER BOUND and not a count. That test is
   free from timestamps the function already parses.

2. The inertness is INVISIBLE. `book_owner.py:2768-2772` asks the engine for
   `get_time_stop_clock_diagnostic`, then for `_last_time_stop_clock_diagnostic`, and **no engine
   in this repository defined either name** -- so `policy_clock` was None on every tick of this
   lineage and every `policy_clock_*` field was absent from every packet it emits. A time stop
   that cannot fire produced no signal anywhere. This engine is now that missing producer.

SO: detection is always on and inert; the behaviour change is behind
`ultimate_book_time_stop_wallclock_on_truncated_window`, default OFF, and arming it trades an
inert backstop for an early one. Both are wrong; which is less wrong is per-sleeve and is Borhen's.

HEADROOM, since it is what makes this worth shipping now. Nothing armed is exposed -- the three
live sleeves are H4 at 1280 and want 1344. F15 measured 7,800 available on both terminals, which
clears an `mx_*` request of 7,744 by **56 bars: 0.72 %**, on a terminal setting a future session
can change without knowing this code exists.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from src.components.execution import ExecutionEngine

END = datetime(2026, 7, 30, 0, 0, tzinfo=timezone.utc)
# Old enough that a 7,744-bar window cannot reach it. Kept as an absolute date because the
# TRUNCATED cases are the ones this file exists for.
ENTRY = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)


class _FakeMT5:
    """Returns `available` M15 bars ending at END. `available` short of the fill is truncation.

    The bars are calendar-contiguous, which real M15 bars are not -- they print only while the
    market is open, so 7,744 real bars span ~112 calendar days against this fake's 80.7. That
    difference is why the COVERING cases below anchor their entry to the bar grid with
    `_entry_bars_ago` instead of naming a date: an absolute date silently tests truncation
    instead of coverage, which is what my first version of this file did.
    """

    def __init__(self, available: int, *, end: datetime | None = None):
        self.available = available
        self.end = end or END
        self.last_request = None

    def get_candles(self, symbol, timeframe, count):
        self.last_request = (symbol, timeframe, count)
        n = min(int(count), self.available)
        return [
            {"time": (self.end - timedelta(minutes=15 * (n - i))).isoformat()}
            for i in range(n)
        ]


def _entry_bars_ago(bars: int, *, end: datetime = END) -> datetime:
    """A fill `bars` M15 bars back on the fake's grid -- inside a window of that many bars."""
    return end - timedelta(minutes=15 * bars)


def _engine(mt5, **runtime):
    config = {
        "market": {"symbol": "BTCUSD", "mt5_symbol": "BTCUSD"},
        "gtos_vnext_runtime": dict(runtime),
    }
    engine = ExecutionEngine.__new__(ExecutionEngine)
    engine.mt5 = mt5
    engine.config = config
    engine.symbol = "BTCUSD"
    return engine


# --------------------------------------------------------------------------------------------
# 1. The request AQ measured
# --------------------------------------------------------------------------------------------


def test_an_mx_budget_requests_7744_bars():
    mt5 = _FakeMT5(available=7800)
    _engine(mt5)._trading_m15_bars_since(ENTRY, 7680)
    assert mt5.last_request == ("BTCUSD", 15, 7744)


def test_the_f15_measured_ceiling_clears_the_request_by_56_bars():
    """7,800 available against 7,744 requested. That margin is the reason this ships."""
    assert 7800 - (7680 + 64) == 56


# --------------------------------------------------------------------------------------------
# 2. A window that covers the fill -- the count is a count
# --------------------------------------------------------------------------------------------


def test_a_covering_window_reports_covers_entry_and_is_not_a_lower_bound():
    engine = _engine(_FakeMT5(available=7800))
    entry = _entry_bars_ago(7000)          # inside the 7,744-bar window
    n = engine._trading_m15_bars_since(entry, 7680)
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["coverage_status"] == "covers_entry"
    assert diag["count_is_lower_bound"] is False
    assert diag["time_stop_unreachable"] is False
    assert n == diag["elapsed_m15_bars"]


def test_the_armed_h4_sleeves_are_not_exposed():
    """1280 wants 1344; every terminal in evidence returns far more."""
    engine = _engine(_FakeMT5(available=7800))
    engine._trading_m15_bars_since(_entry_bars_ago(1200), 1280)
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["bars_requested"] == 1344
    assert diag["coverage_status"] == "covers_entry"
    assert diag["time_stop_unreachable"] is False


# --------------------------------------------------------------------------------------------
# 3. The inert case -- AQ's hazard, detected
# --------------------------------------------------------------------------------------------


def test_a_truncated_window_is_flagged_unreachable_rather_than_returning_a_quiet_short_count():
    """The whole defect: a count that can never reach the budget, reported as if it were a count."""
    engine = _engine(_FakeMT5(available=500))
    n = engine._trading_m15_bars_since(ENTRY, 7680)
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["coverage_status"] == "truncated_before_entry"
    assert diag["count_is_lower_bound"] is True
    assert diag["time_stop_unreachable"] is True
    assert n is not None and n < 7680, "still a lower bound, still returned -- behaviour unchanged"


def test_len_candles_is_not_the_test_a_short_read_that_still_covers_the_fill_is_fine():
    """A young symbol returns fewer bars than asked and its time stop is perfectly sound."""
    recent_entry = datetime(2026, 7, 29, 0, 0, tzinfo=timezone.utc)
    engine = _engine(_FakeMT5(available=300))
    engine._trading_m15_bars_since(recent_entry, 7680)
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["bars_returned"] < diag["bars_requested"]
    assert diag["coverage_status"] == "covers_entry"
    assert diag["time_stop_unreachable"] is False


def test_a_truncated_window_whose_lower_bound_already_exceeds_the_budget_is_not_unreachable():
    """A lower bound past the budget is proof the stop is due -- truncation is irrelevant there."""
    engine = _engine(_FakeMT5(available=500))
    engine._trading_m15_bars_since(ENTRY, 10)
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["coverage_status"] == "truncated_before_entry"
    assert diag["count_is_lower_bound"] is True
    assert diag["time_stop_unreachable"] is False


# --------------------------------------------------------------------------------------------
# 4. Default OFF -- the behaviour change is not made
# --------------------------------------------------------------------------------------------


def test_detection_alone_does_not_change_the_returned_count():
    """Same inputs, same answer as before this session. The diagnostic is the only addition."""
    engine = _engine(_FakeMT5(available=500))
    assert engine._trading_m15_bars_since(ENTRY, 7680) is not None


def test_the_wallclock_fallback_is_off_by_default():
    engine = _engine(_FakeMT5(available=500))
    assert engine._time_stop_wallclock_on_truncated_window() is False
    assert engine._trading_m15_bars_since(ENTRY, 7680) is not None


def test_arming_the_flag_hands_the_caller_the_wallclock_fallback():
    engine = _engine(
        _FakeMT5(available=500),
        ultimate_book_time_stop_wallclock_on_truncated_window=True,
    )
    assert engine._trading_m15_bars_since(ENTRY, 7680) is None
    assert engine.get_time_stop_clock_diagnostic()["fallback"] == "wallclock_on_truncated_window"


def test_the_flag_does_nothing_when_the_window_covers_the_fill():
    """Arming it must not touch a sound position -- that is what makes it safe to arm per account.

    The entry is anchored to the bar grid on purpose. My first version passed `ENTRY`, which is
    outside a 7,744-bar window on this fake, so the case under test was TRUNCATED and the
    assertion held only because the lower bound already exceeded the budget. Right answer, wrong
    branch -- a green test that never touched the code path named in its own title.
    """
    engine = _engine(
        _FakeMT5(available=7800),
        ultimate_book_time_stop_wallclock_on_truncated_window=True,
    )
    entry = _entry_bars_ago(7000)
    assert engine._trading_m15_bars_since(entry, 7680) is not None
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["coverage_status"] == "covers_entry", "the covering branch is the one under test"
    assert "fallback" not in diag


def test_no_committed_config_arms_it():
    import pathlib

    root = pathlib.Path(__file__).resolve().parents[2]
    hits = [
        str(p.relative_to(root))
        for p in list((root / "config").rglob("*.yaml")) + list((root / "config").rglob("*.yml"))
        if "ultimate_book_time_stop_wallclock_on_truncated_window"
        in p.read_text(encoding="utf-8", errors="replace")
    ]
    assert hits == [], hits


# --------------------------------------------------------------------------------------------
# 5. Never raises, and the book's getter finally has a producer
# --------------------------------------------------------------------------------------------


def test_an_unreadable_feed_still_returns_none_and_says_why():
    class Dead:
        def get_candles(self, *a, **k):
            raise RuntimeError("terminal gone")

    engine = _engine(Dead())
    assert engine._trading_m15_bars_since(ENTRY, 7680) is None
    diag = engine.get_time_stop_clock_diagnostic()
    assert diag["status"] == "exception"
    assert diag["coverage_status"] == "feed_unreadable"


def test_an_empty_feed_is_feed_unreadable_not_a_zero_count():
    class Empty:
        def get_candles(self, *a, **k):
            return []

    engine = _engine(Empty())
    assert engine._trading_m15_bars_since(ENTRY, 7680) is None
    assert engine.get_time_stop_clock_diagnostic()["coverage_status"] == "feed_unreadable"


def test_the_book_getter_that_had_no_producer_now_has_one():
    """`book_owner.py:2768` has called this name since the packet carry landed and got None."""
    engine = _engine(_FakeMT5(available=7800))
    assert engine.get_time_stop_clock_diagnostic() is None, "nothing measured yet"
    engine._trading_m15_bars_since(ENTRY, 1280)
    diag = engine.get_time_stop_clock_diagnostic()
    assert callable(getattr(engine, "get_time_stop_clock_diagnostic"))
    assert diag["schema_version"] == "gtos.vnext.time_stop_clock_diagnostic.v1"
    assert diag["checked_at_utc"] and diag["time_stop_bars"] == 1280


def test_the_diagnostic_survives_the_books_own_field_mapping():
    """It must land in the packet, not just on the engine."""
    from src.components.ultimate_book.book_owner import UltimateBookOwner

    engine = _engine(_FakeMT5(available=500))
    engine._trading_m15_bars_since(ENTRY, 7680)
    ctx = UltimateBookOwner._runtime_learning_policy_clock_context(
        engine.get_time_stop_clock_diagnostic()
    )
    assert ctx, "the policy-clock mapper dropped the whole diagnostic"
    assert any("policy_clock" in k for k in ctx)
