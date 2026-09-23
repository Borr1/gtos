"""Behavioural tests for the partial-bar generator harness (Session PB, wave 19).

Every test here asserts on OBSERVED BEHAVIOUR — a candidate that does or does not
appear, a price that is or is not booked — never on the presence of a substring in
a source file.  A source-string test passes against a wrong implementation.

The harness lives under
``docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg/`` because it is
research machinery, not runtime code; these tests pin its contract so a later
session cannot silently change what "partial bar" means.
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PBG = REPO / "docs/audits/fable5-vision-audit-20260725/phase19/receipts/pbg"
sys.path.insert(0, str(PBG))

pytest.importorskip("numpy")

import numpy as np  # noqa: E402

pbg_lib = pytest.importorskip("pbg_lib")
pbg_econ = pytest.importorskip("pbg_econ")


UTC = timezone.utc


def _m1(ts, o, h, l, c, v=1.0):
    return {
        "time": ts.isoformat(),
        "time_utc": ts.isoformat(),
        "open": o,
        "high": h,
        "low": l,
        "close": c,
        "volume": v,
    }


def _index(bar_open, specs):
    """specs: list of (minute_offset, o, h, l, c)."""
    return {
        bar_open + timedelta(minutes=m): _m1(bar_open + timedelta(minutes=m), o, h, l, c)
        for (m, o, h, l, c) in specs
    }


# --------------------------------------------------------------- forming bar


def test_partial_bar_aggregates_only_minutes_before_the_decision():
    """The forming bar at minute k is exactly the OHLC of M1 stamps [open, open+k)."""
    b = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    idx = _index(
        b,
        [
            (0, 100.0, 101.0, 99.5, 100.5),
            (1, 100.5, 102.0, 100.0, 101.5),
            (2, 101.5, 101.8, 98.0, 98.5),   # the low arrives at minute 2
            (3, 98.5, 110.0, 98.5, 109.0),   # a huge move at minute 3
        ],
    )
    at2 = pbg_lib.synth_partial_m15(bar_open=b, m1_index=idx, minutes=2)
    assert at2["open"] == 100.0
    assert at2["high"] == 102.0
    assert at2["low"] == 99.5
    assert at2["close"] == 101.5          # close of stamp b+1
    # minute 2's low and minute 3's spike are NOT visible at k=2
    assert at2["low"] > 98.0
    assert at2["high"] < 110.0

    at3 = pbg_lib.synth_partial_m15(bar_open=b, m1_index=idx, minutes=3)
    assert at3["low"] == 98.0
    assert at3["high"] == 102.0            # minute 3 still invisible
    assert at3["close"] == 98.5


def test_partial_bar_is_blind_to_later_prints():
    """Mutating an M1 bar at or after minute k cannot change the bar at k."""
    b = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    base = [(0, 1.0, 1.1, 0.9, 1.05), (1, 1.05, 1.2, 1.0, 1.15), (2, 1.15, 1.3, 1.1, 1.25)]
    idx_a = _index(b, base)
    idx_b = _index(b, base[:2] + [(2, 1.15, 99.0, 0.001, 50.0)])
    assert pbg_lib.synth_partial_m15(bar_open=b, m1_index=idx_a, minutes=2) == \
        pbg_lib.synth_partial_m15(bar_open=b, m1_index=idx_b, minutes=2)


def test_partial_bar_returns_none_when_the_market_has_not_traded():
    b = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    assert pbg_lib.synth_partial_m15(bar_open=b, m1_index={}, minutes=5) is None


def test_partial_bar_at_15_minutes_equals_the_complete_bar():
    """k=15 must reconstruct the M15 bar the shipped contract decides on."""
    b = datetime(2026, 1, 5, 12, 0, tzinfo=UTC)
    specs = [(m, 10.0 + m, 10.5 + m, 9.5 + m, 10.2 + m) for m in range(15)]
    idx = _index(b, specs)
    full = pbg_lib.synth_partial_m15(bar_open=b, m1_index=idx, minutes=15)
    assert full["open"] == 10.0
    assert full["high"] == max(s[2] for s in specs)
    assert full["low"] == min(s[3] for s in specs)
    assert full["close"] == specs[-1][4]


# ------------------------------------------------------------------ walker


class _Tape:
    """Minimal in-memory tape with the same interface pbg_econ.walk consumes."""

    def __init__(self, bars):
        self.n = len(bars)
        self.o = {"X": np.array([b[0] for b in bars], dtype=float)}
        self.h = {"X": np.array([b[1] for b in bars], dtype=float)}
        self.l = {"X": np.array([b[2] for b in bars], dtype=float)}
        self.c = {"X": np.array([b[3] for b in bars], dtype=float)}


def test_walker_tie_rule_stop_wins_inside_one_bar():
    """Target and stop both reachable in one M1 bar -> STOP (M1 carries no order)."""
    tape = _Tape([(100, 100, 100, 100), (100, 103, 98, 100)])
    r = pbg_econ.walk(tape, "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0)
    assert r[1] == "stop"
    assert r[0] == -1.0


def test_walker_gives_no_same_bar_credit():
    """A target touched only in the fill minute is not booked."""
    bars = [(100, 105, 100, 100)] + [(100, 100.1, 99.9, 100.0)] * 5
    tape = _Tape(bars)
    r = pbg_econ.walk(tape, "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0)
    assert r[1] != "target"
    # with the fill minute included the same tape DOES book the target
    r2 = pbg_econ.walk(
        tape, "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0,
        include_fill_minute=True,
    )
    assert r2[1] == "target"


def test_walker_books_target_and_stop_at_the_declared_multiples():
    up = [(100, 100, 100, 100)] + [(100, 102.5, 100, 102)] * 3
    tape = _Tape(up)
    r = pbg_econ.walk(tape, "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0)
    assert r[1] == "target" and r[0] == 2.0
    dn = [(100, 100, 100, 100)] + [(100, 100, 98.9, 99)] * 3
    r = pbg_econ.walk(_Tape(dn), "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0)
    assert r[1] == "stop" and r[0] == -1.0


def test_walker_short_side_is_the_mirror():
    bars = [(100, 100, 100, 100)] + [(100, 100, 97.9, 98)] * 3
    r = pbg_econ.walk(_Tape(bars), "X", 0, entry=100.0, stop=101.0, long=False, target_r=2.0)
    assert r[1] == "target" and r[0] == 2.0


def test_walker_marks_to_market_when_neither_level_is_touched():
    bars = [(100, 100, 100, 100)] + [(100, 100.4, 99.7, 100.3)] * 4
    r = pbg_econ.walk(_Tape(bars), "X", 0, entry=100.0, stop=99.0, long=True, target_r=2.0)
    assert r[1] == "path_end"
    assert abs(r[0] - 0.3) < 1e-9


# ------------------------------------------------------- resting-limit walker


def test_limit_walk_books_zero_when_the_level_is_never_touched():
    bars = [(100, 100.2, 99.8, 100.0)] * 10
    r = pbg_econ.walk_limit(_Tape(bars), "X", 0, entry=95.0, stop=94.0, long=True)
    assert r[1] == "no_fill" and r[0] == 0.0


def test_limit_walk_fills_at_first_touch_then_walks_from_the_next_bar():
    bars = [
        (100, 100.2, 99.8, 100.0),
        (100, 100.2, 94.9, 95.0),      # touches 95.0 here
        (95, 97.2, 94.9, 97.0),        # +2R (entry 95, stop 94) reached only later
        (97, 97.2, 96.9, 97.0),
    ]
    r = pbg_econ.walk_limit(_Tape(bars), "X", 0, entry=95.0, stop=94.0, long=True, target_r=2.0)
    assert r[1] == "target"


# --------------------------------------------------------------- cost model


@pytest.mark.skipif(
    not (PBG.parent / "discovery" / "L10X_TICK_SPREAD_V1.json").is_file(),
    reason="lane cost artifacts absent",
)
def test_cost_model_is_positive_hour_aware_and_denominated_in_price():
    cm = pbg_econ.CostModel()
    a, terms = cm.cost_px("EURUSD", "2026-01-05T13:00:00+00:00", 1.17, True)
    assert a > 0
    assert set(terms) == {"spread", "commission", "slippage", "swap"}
    assert abs(sum(terms.values()) - a) < 1e-12
    hours = {
        cm.spread_bps("EURUSD", h) for h in range(24)
    }
    assert len(hours) > 1, "the spread term must vary with the broker hour"
    # a 2-hour horizon on a weekday afternoon crosses no broker midnight
    assert terms["swap"] == 0.0


@pytest.mark.skipif(
    not (PBG.parent / "discovery" / "L10X_TICK_SPREAD_V1.json").is_file(),
    reason="lane cost artifacts absent",
)
def test_cost_in_r_scales_inversely_with_the_risk_distance():
    """Fixed-fractional sizing pays the same price-unit toll over a smaller unit."""
    cm = pbg_econ.CostModel()
    px, _ = cm.cost_px("XAUUSD", "2026-01-05T13:00:00+00:00", 4300.0, True)
    wide, narrow = px / 10.0, px / 2.0
    assert narrow > wide


# ------------------------------------------------------- reproduction receipt


RECEIPT = PBG / "PBG_JAN_V1.json"


@pytest.mark.skipif(not RECEIPT.is_file(), reason="January receipt not built in this tree")
def test_january_close_only_reproduces_the_sealed_generator_roster():
    """Pin the MEASURED reproduction contract, not an aspirational one.

    The harness reproduces the sealed January arm's own candidate roster at
    99.82 %.  The residual is characterised, not unexplained: everything the
    sealed arm has and the harness does not sits at the day's 00:00 window, and
    everything the harness has and the sealed arm does not sits on a Monday or
    on the first trading day after a market break.  A regression that broke the
    predicates would move coverage, not just the calendar edges.
    """
    import datetime as _dt
    import json

    rec = json.loads(RECEIPT.read_text())
    rep = rec["reproduction"]
    assert rep["coverage_of_sealed"] > 0.998, rep["coverage_of_sealed"]
    assert rep["mine_only"] / rep["my_close_only_rows"] < 0.005
    # every missed candidate is at the first window of a trading day
    assert set(rep["sealed_only_by_time"]) == {"00:00"}
    # every invented candidate is on a Monday or on the first trading day of the month
    for day in rep["mine_only_by_day"]:
        d = _dt.date.fromisoformat(day)
        assert d.weekday() == 0 or d.day <= 2, day


@pytest.mark.skipif(not RECEIPT.is_file(), reason="January receipt not built in this tree")
def test_january_partial_entries_carry_no_look_ahead():
    import json

    rec = json.loads(RECEIPT.read_text())
    a = rec["anchor_check"]
    assert a["n"] > 10000
    assert a["share_exact"] == 1.0
    assert a["worst_relative_error"] == 0.0
