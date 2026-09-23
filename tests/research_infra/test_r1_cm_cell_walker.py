"""Behavioural pins for the `stop_mult` extension of the r1 frontier-surface walker.

Wave 21 (`wave21/cm-cell-pricing`): `r1_frontier_surface_sweep.walk()` gained a
`stop_mult` parameter so the CM cell (`crypto @ stop_1p5x_target_scale`,
`execution_packets.py:213-217`) could be priced on the corrected-quote machinery
(`R1_CM_CELL_PRICING_V1.json`). These tests hold, on synthetic bars that run anywhere,
the two properties the receipt's controls established on the real substrate:

  1. DEFAULT IDENTITY — `stop_mult` omitted or 1.0 is the pre-change walker exactly
     (the receipt's C2 held this against the committed surface, 18/18 cells);
  2. THE SCALED CONTRACT — the R unit, the target and every derived distance follow the
     scaled stop, matching AD's `stop_width` family (`ad_exit_sweep.py:318,324,336-337`)
     and the live application (`execution_packets.py:530-535,564-569`).

The corrected-convention arm is deliberately not exercised here: it differs only in the
entry anchor (spread model — machine-local substrate), and the receipt's C2/C3 pinned it
on the real data. Everything below walks the published arm, where the geometry lives.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
R1 = REPO / "docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1"

from src.components.ultimate_book.bar_provider import TF_H4  # noqa: E402
from src.components.ultimate_book.primitives import Bar  # noqa: E402


@pytest.fixture(scope="module")
def sweep():
    spec = importlib.util.spec_from_file_location(
        "r1_frontier_surface_sweep_under_test", R1 / "r1_frontier_surface_sweep.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # the script inserts its own dir + repo root on sys.path
    return mod


def mk_series(bars_ohlc, symbol="SYNTH", tf=TF_H4, start=dt.datetime(2026, 1, 5)):
    bars = [Bar(o, h, l, c, 0.0) for (o, h, l, c) in bars_ohlc]
    times = [start + dt.timedelta(hours=4 * k) for k in range(len(bars))]
    series = {(symbol, tf): (bars, times)}
    index = {(symbol, tf): {ts: k for k, ts in enumerate(times)}}
    return series, index, times


def mk_trade(times, i=0, sd=1.0, symbol="SYNTH", tf=TF_H4, direction=1,
             sleeve="synthetic_sleeve_not_in_profiles", day=None):
    # The sleeve name resolves to DEFAULT_EXIT_PROFILE (policy "time_stop"), so
    # `_trail_policy` contributes no trail — the CM cell's own shape.
    return {
        "timeframe": tf, "symbol": symbol,
        "decision_bar_iso": times[i].isoformat(),
        "direction": direction, "sl_distance_price": sd,
        "sleeve": sleeve,
        "decision_day": day or times[i].date().isoformat(),
    }


# --------------------------------------------------------------------------------------
# 2. the scaled contract, CM-shaped: stop x1.5 survives what stops the native contract,
#    the target sits at 6x the native distance, and R denominates on the scaled stop.


def test_wider_stop_survives_and_pays_in_the_scaled_unit(sweep):
    """Drawdown of 1.3x native sd: the native contract stops at -1R; the CM contract
    (stop x1.5) survives it and fills its 4R-of-the-scaled-unit target at entry + 6.0x
    native sd, booking exactly +4.0R in the scaled unit."""
    series, index, times = mk_series([
        (100.0, 100.5, 99.6, 100.0),   # entry bar: entry = close = 100
        (100.0, 100.5, 98.7, 99.2),    # low 98.7: through 99.0 (1.0x stop), above 98.5 (1.5x)
        (99.2, 106.2, 99.1, 105.0),    # high 106.2: through 106.0 = entry + 4R x 1.5 x sd
    ])
    trades = [mk_trade(times, i=0, sd=1.0)]

    vals, by_day, reasons, unp, skips = sweep.walk(
        trades, series, index, 4.0, 80, "mid", False, stop_mult=1.0)
    assert vals == [-1.0]
    assert dict(reasons) == {"stop": 1}

    vals, by_day, reasons, unp, skips = sweep.walk(
        trades, series, index, 4.0, 80, "mid", False, stop_mult=1.5)
    assert vals == [4.0], "target must pay 4R OF THE SCALED UNIT (6x native sd in price)"
    assert dict(reasons) == {"target": 1}
    assert dict(by_day) == {times[0].date().isoformat(): [4.0]}
    assert unp == 0 and not skips


def test_cm_target_sits_at_six_native_sd_not_four(sweep):
    """A path that tags entry + 5.9x native sd fills the native 4R target but NOT the CM
    target (which needs 6.0x); the CM contract runs to its horizon instead, and its
    maxbars R is denominated on the 1.5x stop."""
    series, index, times = mk_series([
        (100.0, 100.5, 99.6, 100.0),
        (100.0, 105.9, 99.8, 105.5),   # high 105.9 >= 104.0 (native 4R), < 106.0 (CM 4R)
        (105.5, 105.9, 99.5, 101.5),   # never reaches 106.0, never touches 98.5
    ])
    trades = [mk_trade(times, i=0, sd=1.0)]

    vals, _, reasons, _, _ = sweep.walk(
        trades, series, index, 4.0, 2, "mid", False, stop_mult=1.0)
    assert vals == [4.0]
    assert dict(reasons) == {"target": 1}

    vals, _, reasons, _, _ = sweep.walk(
        trades, series, index, 4.0, 2, "mid", False, stop_mult=1.5)
    assert dict(reasons) == {"maxbars": 1}
    assert vals == [(101.5 - 100.0) / 1.5], "horizon close, in the scaled R unit"


def test_short_side_scales_symmetrically(sweep):
    """Same contract, direction -1: adverse excursion of 1.3x native sd stops the native
    contract at -1R; the CM contract survives and fills at entry - 6x native sd."""
    series, index, times = mk_series([
        (100.0, 100.4, 99.6, 100.0),
        (100.0, 101.3, 99.5, 100.8),   # high 101.3: through 101.0 (1.0x stop), below 101.5
        (100.8, 100.9, 93.8, 95.0),    # low 93.8: through 94.0 = entry - 6x sd
    ])
    trades = [mk_trade(times, i=0, sd=1.0, direction=-1)]

    vals, _, reasons, _, _ = sweep.walk(
        trades, series, index, 4.0, 80, "mid", False, stop_mult=1.0)
    assert vals == [-1.0]
    assert dict(reasons) == {"stop": 1}

    vals, _, reasons, _, _ = sweep.walk(
        trades, series, index, 4.0, 80, "mid", False, stop_mult=1.5)
    assert vals == [4.0]
    assert dict(reasons) == {"target": 1}


# --------------------------------------------------------------------------------------
# 1. default identity: omitted == 1.0 == the pre-change walker (hand-computed oracle).


def test_default_and_explicit_one_are_identical_and_match_the_oracle(sweep):
    """Three trades covering stop, target and maxbars exits. `stop_mult` omitted and 1.0
    must agree on every output object, and both must match the hand-computed pre-change
    semantics (entry at decision close, target at tm x sd, stop at -1R, maxbars close)."""
    series, index, times = mk_series([
        (100.0, 100.5, 99.6, 100.0),   # t0 entry (trade A, sd 1.0)
        (100.0, 104.1, 99.7, 103.0),   # A: high 104.1 >= 104.0 -> target +4R
        (103.0, 103.5, 102.0, 102.5),  # t2 entry (trade B, sd 2.0)
        (102.5, 103.0, 100.4, 101.0),  # B: low 100.4 <= 100.5 = 102.5 - 2.0 -> stop -1R
        (101.0, 101.5, 100.6, 101.2),  # t4 entry (trade C, sd 1.0)
        (101.2, 101.9, 100.9, 101.5),  # C: nothing hit
        (101.5, 102.0, 101.0, 101.8),  # C: maxbars=2 -> close 101.8 -> +0.6R
    ])
    trades = [
        mk_trade(times, i=0, sd=1.0, day="2026-01-05"),
        mk_trade(times, i=2, sd=2.0, day="2026-01-06"),
        mk_trade(times, i=4, sd=1.0, day="2026-01-07"),
    ]

    out_default = sweep.walk(trades, series, index, 4.0, 2, "mid", False)
    out_one = sweep.walk(trades, series, index, 4.0, 2, "mid", False, stop_mult=1.0)

    for a, b in zip(out_default, out_one):
        assert (dict(a) if hasattr(a, "keys") else a) == (dict(b) if hasattr(b, "keys") else b)

    vals, by_day, reasons, unp, skips = out_default
    assert vals[0] == 4.0                          # A: target
    assert vals[1] == -1.0                         # B: stop
    assert vals[2] == pytest.approx((101.8 - 101.2) / 1.0)  # C: maxbars close
    assert dict(reasons) == {"target": 1, "stop": 1, "maxbars": 1}
    assert set(by_day) == {"2026-01-05", "2026-01-06", "2026-01-07"}


# --------------------------------------------------------------------------------------
# 2b. every derived distance follows the scaled stop — including the trail branch, which
#     the CM cell does not use but the changed line also feeds.


def test_scaling_equivalence_covers_the_trail_branch(sweep):
    """walk(sd, stop_mult=k) must equal walk(k*sd, stop_mult=1.0) bit-for-bit — the
    single-scaling-point property. Run on a trailing_runner sleeve so the trail arm/gap
    distances (also derived from sd) are exercised, and assert the trail actually fired
    so the equivalence is not vacuous."""
    sleeve = "asian_fade"  # trailing_runner, trigger_r=0.5, trail_gap_r=0.5 (:102)
    trig, gap = sweep.R._trail_policy(sleeve)
    if trig is None:
        pytest.skip(f"{sleeve} is no longer a trailing_runner sleeve in this tree")

    k, sd = 2.0, 1.0
    sd_eff = sd * k
    arm_px = 100.0 + float(trig) * sd_eff          # trail arms here
    peak = arm_px + float(gap) * sd_eff + 1.0      # extreme well past arm + gap
    series, index, times = mk_series([
        (100.0, 100.2, 99.8, 100.0),
        (100.0, peak, 99.9, peak - 0.5),           # arms and (same-bar rule) can fill
        (peak - 0.5, peak - 0.4, 99.9, 100.5),
    ])
    t_scaled = [mk_trade(times, i=0, sd=sd, sleeve=sleeve)]
    t_pre = [mk_trade(times, i=0, sd=sd_eff, sleeve=sleeve)]

    out_scaled = sweep.walk(t_scaled, series, index, None, 80, "mid", False, stop_mult=k)
    out_pre = sweep.walk(t_pre, series, index, None, 80, "mid", False, stop_mult=1.0)

    for a, b in zip(out_scaled, out_pre):
        assert (dict(a) if hasattr(a, "keys") else a) == (dict(b) if hasattr(b, "keys") else b)
    assert dict(out_scaled[2]).get("trail", 0) == 1, "scenario must actually fire the trail"


def test_cm_target_constructions_agree_bitwise():
    """The walker builds the CM target as tm * (stop_mult * sd); the live wiring builds
    TP = final_target_r * risk_distance and AD's family builds target_dist * stop_mult
    (equal when target_dist == 4 * sd, which C1 held on all 181 rows). The two float
    orderings must agree bit-for-bit on awkward mantissas, or the receipt's C3 identity
    would rest on luck."""
    for sd in (0.1, 0.3, 1.0 / 3.0, 7.3e-5, 123.456789, 2.0 ** -30 * 1.1):
        assert 4.0 * (1.5 * sd) == (4.0 * sd) * 1.5


def test_nonpositive_stop_mult_refuses(sweep):
    series, index, times = mk_series([
        (100.0, 100.5, 99.6, 100.0),
        (100.0, 100.5, 99.7, 100.1),
        (100.1, 100.5, 99.8, 100.2),
    ])
    trades = [mk_trade(times, i=0, sd=1.0)]
    for bad in (0.0, -1.5):
        with pytest.raises(ValueError):
            sweep.walk(trades, series, index, 4.0, 80, "mid", False, stop_mult=bad)
