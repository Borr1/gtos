"""The percentile machinery must be leak-free, per-symbol, and warmup-honest.

A trailing percentile that includes the current bar in its own reference window makes every
variant look better than it is, and the defect would be invisible in the summary numbers —
it moves the level, not the shape. So the leak is tested directly, on a monotone series
where the correct answer is known by construction.
"""

from __future__ import annotations

import datetime as dt

import pytest

from src.research_infra.regime_spine import conditions as C
from src.research_infra.regime_spine.normalize import (
    DEFAULT_WINDOW,
    attach_ranks,
    fit_percentile,
    percentile_variant,
    trailing_ranks,
)
from src.research_infra.regime_spine.state import build_frame


def test_rank_is_none_until_the_window_is_full():
    r = trailing_ranks(list(range(10)), window=4)
    assert r[:4] == [None, None, None, None]
    assert all(x is not None for x in r[4:])


def test_rank_excludes_the_current_bar():
    """On a strictly increasing series every value is above ALL of its history -> 1.0.

    If the current bar were in its own window the answer would be (n-1)/n < 1.0, so this
    single assertion catches the leak exactly.
    """
    r = trailing_ranks([float(i) for i in range(50)], window=10)
    assert all(x == 1.0 for x in r[10:])


def test_rank_on_a_decreasing_series_is_zero():
    r = trailing_ranks([float(-i) for i in range(50)], window=10)
    assert all(x == 0.0 for x in r[10:])


def test_window_evicts_in_insertion_order():
    """A value that leaves the window must stop influencing the rank."""
    vals = [100.0] * 5 + [0.0] * 20
    r = trailing_ranks(vals, window=5)
    assert r[5] == 0.0                      # window is five 100s, 0 ranks below all
    assert r[-1] == 0.0                     # window is all zeros: bisect_left -> 0
    mid = trailing_ranks([100.0] * 5 + [1.0, 2.0, 3.0, 4.0, 5.0, 3.5], window=5)
    assert mid[-1] == pytest.approx(3 / 5)  # 3.5 sits above 1,2,3 of {1,2,3,4,5}


def test_nones_are_skipped_not_counted():
    r = trailing_ranks([None, None, 1.0, 2.0, 3.0, 4.0, 0.5], window=3)
    assert r[-1] == 0.0
    assert r[:4] == [None, None, None, None]


def _frame(seed=3, n=1400, start=dt.datetime(2015, 1, 1, tzinfo=dt.timezone.utc)):
    from tests.research_infra.test_regime_spine_state import _bars

    bars = _bars(n, seed=seed)
    t0 = start
    times = [t0 + dt.timedelta(hours=4 * i) for i in range(len(bars))]
    return build_frame("XAUUSD", 16388, bars, times)


def test_attach_ranks_is_per_symbol_and_keyed_by_window():
    a, b = _frame(seed=3), _frame(seed=99)
    frames = {"XAUUSD": a, "XAGUSD": b}
    attach_ranks(frames, ["vr"], window=200)
    assert "vr@200" in a.ranks and "vr@200" in b.ranks
    assert a.ranks["vr@200"] != b.ranks["vr@200"], (
        "a pooled quantile would let one symbol's distribution set another's threshold")


def test_percentile_variant_changes_exactly_one_gate():
    cond = C.SLEEVES["sub_xvol_pullback"]
    var, pname = percentile_variant(cond, "vol_xhi", window=200, p=0.9)
    assert pname == "pct_vol_xhi"
    assert var.gate_names() == cond.gate_names()
    assert var.surface == cond.surface and var.warmup_bars == cond.warmup_bars
    changed = [g.name for g, h in zip(var.gates, cond.gates) if g.test is not h.test]
    assert changed == ["vol_xhi"]
    assert var.defaults["pct_vol_xhi"] == 0.9


def test_percentile_gate_fails_closed_without_ranks():
    """No ranks attached -> the gate must refuse, not pass by default."""
    f = _frame()
    cond = C.SLEEVES["sub_xvol_pullback"]
    var, pname = percentile_variant(cond, "vol_xhi", window=200, p=0.5)
    g = next(x for x in var.gates if x.name == "vol_xhi")
    assert all(not g.test(f, i, {pname: 0.5}) for i in range(300, 400))


def test_fit_uses_only_the_fit_era():
    """A fit that could see 2024+ would be the defect this repairs, one level up."""
    # 1,400 H4 bars is ~233 days, so the fixture must START mid-2014 for a 2014/2015
    # boundary to fall inside it. (First draft cut at 2015 on a series that began
    # 2015-01-01 and both eras came back identical — the assertion caught it.)
    f = _frame(n=1400, start=dt.datetime(2014, 6, 1, tzinfo=dt.timezone.utc))
    frames = {"XAUUSD": f}
    attach_ranks(frames, ["vr"], window=200)
    cond = C.SLEEVES["sub_xvol_pullback"]
    assert {t.year for t in f.times_utc} == {2014, 2015}, "fixture must cross a year"
    early = fit_percentile(frames, cond, "vol_xhi", window=200, fit_last_year=2014)
    late = fit_percentile(frames, cond, "vol_xhi", window=200, fit_last_year=2100)
    assert early["n_eval_fit_era"] < late["n_eval_fit_era"]
    assert 0.0 <= early["fitted_p"] <= 1.0
    assert early["fit_last_year"] == 2014


def test_fitted_p_reproduces_the_production_pass_rate_within_tolerance():
    f = _frame(n=1600)
    frames = {"XAUUSD": f}
    attach_ranks(frames, ["vr"], window=DEFAULT_WINDOW // 2)
    cond = C.SLEEVES["sub_xvol_pullback"]
    fit = fit_percentile(frames, cond, "vol_xhi", window=DEFAULT_WINDOW // 2,
                         fit_last_year=2100)
    var, pname = percentile_variant(cond, "vol_xhi", window=DEFAULT_WINDOW // 2,
                                    p=fit["fitted_p"])
    g = next(x for x in var.gates if x.name == "vol_xhi")
    lo = cond.warmup_bars - 1
    rankable = [i for i in range(lo, len(f))
                if f.ranks[f"vr@{DEFAULT_WINDOW // 2}"][i] is not None]
    if not rankable:
        pytest.skip("fixture too short to produce rankable bars")
    got = sum(1 for i in rankable if g.test(f, i, {pname: fit["fitted_p"]})) / len(rankable)
    assert got == pytest.approx(fit["rankable_pass_rate_fit_era"], abs=0.02)
