"""The generation funnel's two SILENT drops, made countable — and proof they still drop.

`book_engine._generate_intents` used to lose a (sleeve, symbol) slot at two places with no
counter and no skip row:

    :601   if not bars or not enough(bars, spec.cluster): continue      insufficient bars
    :633   if (now - bar_close) > 2*ivl:                  continue      stale decision bar

Both are FEED conditions. In every log they were indistinguishable from the third, far more
common drop — the generator looked and there was no setup — which is not a rejection at all.
A sleeve starved of bars, or one whose symbol stopped printing, therefore read exactly like a
quiet market for as long as it lasted. Measured on the live F5 book 2026-08-12 02:16Z: 2 of 136
slots were being dropped stale (EU50_cash and FRA40_cash on `sub_xvol_pullback`, H4 bars 556.4
minutes old against a 480-minute limit) with nothing recorded anywhere.

This file asserts the properties that make counting them safe:

  1. Each drop is COUNTED and the slot is still DROPPED. The gate's decision does not move.
  2. The sample list is bounded while the count stays exact, so a weekend — when every slot is
     stale — costs a fixed number of rows and still reports the true total.
  3. The funnel closes arithmetically, which is the only reason the numbers are worth reading.
  4. **A bug in this telemetry cannot open a gate.** Every counter update is exception-guarded;
     if the guard were dropped, an exception inside the stale branch would skip its own
     `continue` and the book would act on a frozen bar. That is asserted directly, by making
     the telemetry raise.

Harness pattern (recorder in place of `get_closed_bars`, engine over `tmp_path`) is reused from
`test_pre_gap_bar_wiring.py` rather than reinvented.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.components.ultimate_book import book_engine as BE
from src.components.ultimate_book import bar_provider as BP


UTC = dt.timezone.utc
NOW = dt.datetime(2026, 8, 12, 2, 16, tzinfo=UTC)


class _Feed:
    """Stands in for `get_closed_bars`, timeframe-aware.

    `age_intervals` is how many bar-intervals OLD the newest bar's close is at `NOW`:
      0  -> closes exactly at NOW (fresh)
      10 -> ten intervals stale, past the 2-interval limit for every timeframe
    Spacing follows the REQUESTED timeframe, so one feed can serve M15, H4 and D1 slots in the
    same cycle without any of them landing in the future-bar branch by accident.
    """

    def __init__(self, *, n_bars: int | None, age_intervals: float = 0.0):
        self.n_bars = n_bars
        self.age_intervals = age_intervals
        self.calls = 0

    def __call__(self, mt5, symbol, timeframe, count, **kw):
        self.calls += 1
        if self.n_bars == 0:
            return [], []
        ivl = BE._TF_MINUTES.get(timeframe) or 15
        n = count if self.n_bars is None else self.n_bars
        last_close = NOW - dt.timedelta(minutes=ivl * self.age_intervals)
        last_open = last_close - dt.timedelta(minutes=ivl)
        candles = []
        for i in range(n):
            t = last_open - dt.timedelta(minutes=ivl * (n - 1 - i))
            candles.append({"time": t.isoformat(), "open": 100.0, "high": 101.0,
                            "low": 99.0, "close": 100.0, "volume": 10})
        # `now` is deliberately NOT passed: the default path drops the forming bar, so the last
        # candle here is consumed as the newest CLOSED bar exactly as it is live.
        bars, times = BP.candles_to_bars(candles, drop_forming=False)
        return bars, times


def _run(monkeypatch, tmp_path, feed):
    monkeypatch.setattr(BE, "get_closed_bars", feed)
    eng = BE.UltimateBookLiveEngine({}, object(), str(tmp_path), namespace="test_funnel_ns")
    intents, _meta = eng._generate_intents(now=NOW)
    return intents, dict(eng._last_generation_telemetry)


# ---------------------------------------------------------------------------------
# 1. Counted, and still dropped
# ---------------------------------------------------------------------------------
def test_insufficient_bars_is_counted_and_the_slot_is_still_dropped(monkeypatch, tmp_path):
    intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=0))
    supported = gen["profile_supported_symbol_slot_count"]
    assert supported >= 20, "harness sanity: the default surface should present many slots"
    assert gen["insufficient_bars_symbol_slot_count"] == supported, (
        "every slot got an empty feed, so every slot must be counted here")
    assert intents == [], "an empty feed must never produce an intent"
    assert gen["generator_evaluated_symbol_slot_count"] == 0


def test_the_insufficient_bars_sample_names_the_shortfall(monkeypatch, tmp_path):
    _intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=0))
    rows = gen["insufficient_bars_skips"]
    assert rows, "a count with no sample cannot be acted on"
    r = rows[0]
    assert r["reason"] == "insufficient_bars"
    assert r["bars_returned"] == 0
    # The two numbers that make the row diagnosable rather than merely present.
    assert r["warmup_required"] == BP.WARMUP.get(r["cluster"], 200)
    assert r["bars_requested"] >= r["warmup_required"]


def test_a_slot_one_bar_short_of_warmup_is_counted(monkeypatch, tmp_path):
    """The boundary, not just the empty feed: `enough()` is a >= test on the CLUSTER warmup."""
    _intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=99))
    assert gen["insufficient_bars_symbol_slot_count"] >= 1
    for r in gen["insufficient_bars_skips"]:
        assert r["bars_returned"] < r["warmup_required"]


def test_stale_decision_bar_is_counted_and_the_slot_is_still_dropped(monkeypatch, tmp_path):
    intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=None, age_intervals=10))
    supported = gen["profile_supported_symbol_slot_count"]
    assert gen["stale_decision_bar_symbol_slot_count"] == supported, (
        "every slot's newest bar closed ten intervals ago; every slot must be counted stale")
    assert intents == [], "a frozen bar must never produce an intent"
    assert gen["generator_evaluated_symbol_slot_count"] == 0
    r = gen["stale_decision_bar_skips"][0]
    assert r["reason"] == "stale_decision_bar"
    assert r["age_minutes"] > r["stale_limit_minutes"], (
        "the row must show WHY it was stale, in the gate's own units")


def test_a_bar_inside_the_recency_limit_reaches_the_generator(monkeypatch, tmp_path):
    """The control: without this, every test above would pass on a book that never generates."""
    _intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=None, age_intervals=0))
    assert gen["stale_decision_bar_symbol_slot_count"] == 0
    assert gen["insufficient_bars_symbol_slot_count"] == 0
    assert gen["generator_evaluated_symbol_slot_count"] == \
        gen["profile_supported_symbol_slot_count"]


# ---------------------------------------------------------------------------------
# 2. The count is exact while the sample is bounded
# ---------------------------------------------------------------------------------
def test_sample_is_capped_but_the_count_is_not(monkeypatch, tmp_path):
    _intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=0))
    n = gen["insufficient_bars_symbol_slot_count"]
    rows = gen["insufficient_bars_skips"]
    assert len(rows) <= BE._SKIP_SAMPLE_CAP
    if n > BE._SKIP_SAMPLE_CAP:
        assert len(rows) == BE._SKIP_SAMPLE_CAP, (
            "the sample must fill to the cap, not stop early")
    assert n >= len(rows), "the count is the total; the sample is only a window onto it"


# ---------------------------------------------------------------------------------
# 3. The funnel closes arithmetically
# ---------------------------------------------------------------------------------
@pytest.mark.parametrize("feed", [
    _Feed(n_bars=0),
    _Feed(n_bars=None, age_intervals=10),
    _Feed(n_bars=None, age_intervals=0),
])
def test_the_funnel_closes(monkeypatch, tmp_path, feed):
    """slots - unsupported - insufficient - stale - future == evaluated, in every regime.

    This identity is the whole reason the counters are worth reading: it proves no slot leaves
    the loop through an unnamed exit.
    """
    _intents, gen = _run(monkeypatch, tmp_path, feed)
    lhs = (gen["active_symbol_slot_count"]
           - gen["broker_unsupported_symbol_slot_count"]
           - gen["insufficient_bars_symbol_slot_count"]
           - gen["stale_decision_bar_symbol_slot_count"]
           - gen["future_decision_bar_symbol_slot_count"])
    assert lhs == gen["generator_evaluated_symbol_slot_count"], (
        f"the funnel leaks: {gen}")


# ---------------------------------------------------------------------------------
# 4. THE SAFETY PROPERTY — telemetry cannot open a gate
# ---------------------------------------------------------------------------------
def test_a_raising_sample_helper_still_drops_the_stale_slot(monkeypatch, tmp_path):
    """The stale branch lives inside a `try/except Exception: pass`. Without its own guard, an
    exception in the telemetry would skip the branch's `continue` and the book would go on to
    generate on a frozen bar. Assert the drop survives a hostile telemetry helper."""
    def _boom(*_a, **_k):
        raise RuntimeError("telemetry exploded")

    monkeypatch.setattr(BE, "_sample_skip", _boom)
    intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=None, age_intervals=10))
    assert intents == [], (
        "a stale bar produced an intent because the telemetry raised — the guard is missing")
    assert gen["generator_evaluated_symbol_slot_count"] == 0


def test_a_raising_sample_helper_still_drops_the_starved_slot(monkeypatch, tmp_path):
    def _boom(*_a, **_k):
        raise RuntimeError("telemetry exploded")

    monkeypatch.setattr(BE, "_sample_skip", _boom)
    intents, gen = _run(monkeypatch, tmp_path, _Feed(n_bars=0))
    assert intents == []
    assert gen["generator_evaluated_symbol_slot_count"] == 0
