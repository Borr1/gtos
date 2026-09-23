"""One pass over a bar series -> every statistic the armed sleeves' gates test.

WHY A FRAME AND NOT JUST A GENERATOR CALL
------------------------------------------
`GenerationPort` answers "did this sleeve fire?" — one bit at the bottom of a funnel.
This session's question is the funnel: *which* gate stopped the other bars, and did that
gate's pass rate move over 26 years. Answering it for one threshold variant costs one
archive pass; answering it for four hundred variants costs four hundred, unless the
per-bar statistics are computed once and the thresholds applied afterwards.

So `build_frame` computes, per bar, the continuous quantities every armed-sleeve gate
reduces to a boolean, and `conditions.py` applies the cuts. A sweep then re-reads a frame
instead of re-walking bars.

THE FACTORISATION THAT MAKES IT LEGITIMATE
-------------------------------------------
Two production gates look like they resist this and do not:

* `metals.fvg_signal` returns `None` when `a < gate_k * sma100` **before** it looks for a
  gap. The gap search itself does not read `gate_k`, so
  ``fvg_signal(gate_k) == (frame.fvg if frame.vr_raw >= gate_k else None)`` — the vol gate
  factors out cleanly and `gate_k` becomes sweepable. Asserted in
  `tests/research_infra/test_regime_spine_state.py`.
* `substrate_engine.compute_state` bundles seven features; each is independent of the cell
  thresholds, which live in `cell_coords`. The frame stores the features and
  `conditions.py` re-buckets.

EXACTNESS, DELIBERATELY OVER SPEED
-----------------------------------
Every window here is summed with the builtin `sum`/`min`/`max` over a real slice, exactly
as the production functions do, rather than with an incrementally-updated accumulator. A
rolling accumulator drifts in the last bits over 40,000 bars and would make a parity test
either fail or be weakened to a tolerance — and a tolerance is how a fidelity claim rots.
Builtin `sum` over a 100-float slice is C-speed; the whole armed surface (~180k bars)
frames in well under a minute.

`autocorr` is called through `primitives`/`substrate_engine` themselves rather than
reimplemented, because the two production autocorrelations differ (`statistics.mean` vs
`sum/n`) and that difference is not ours to erase.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Any, Optional, Sequence

from src.components.ultimate_book.primitives import Bar, atr14, autocorr
from src.components.ultimate_book.sleeves import substrate_engine as _se
from src.components.ultimate_book.sleeves.metals import (
    ATR_STOP_FLOOR,
    STOP_BUF,
)

__all__ = ["BarFrame", "build_frame", "fvg_at", "htf_trend_sign"]

#: `metals.fvg_signal`'s minimum gap, as a multiple of ATR (`metals.py` gap loop).
FVG_MIN_ATR = 0.10
#: `metals.htf_trend` lookback (`metals.py:htf_trend`, lb=30).
HTF_LB = 30
#: `crypto.DON_LB` — the Donchian channel lookback.
DON_LB = 20


@dataclass
class BarFrame:
    """Per-bar statistics for one (symbol, timeframe) series.

    Every list is `len(bars)` long and index-aligned with `bars`. Entries before a
    statistic's warmup carry the production sentinel (`0.0` for `atr14`, `None` for
    `autocorr`, `1.0` for `vol_ratio`), never a silently-imputed value.
    """

    symbol: str
    timeframe: int
    bars: list[Bar]
    times_utc: list[dt.datetime]

    atr: list[float]
    #: `vol_ratio(atrs, i)` — production returns 1.0 below i=100; `vr_raw` is None there
    #: so a gate can tell "no measurement" from "measured 1.0".
    vr: list[float]
    vr_raw: list[Optional[float]]
    #: `c[i] - c[i-30]`, the raw numerator `metals.htf_trend` compares against `1.0*a`.
    d30: list[Optional[float]]
    #: substrate slopes, ATR-normalised: `(c[i] - c[i-k]) / a`.
    slope20: list[Optional[float]]
    slope50: list[Optional[float]]
    slope100: list[Optional[float]]
    rng_pos: list[Optional[float]]
    comp: list[Optional[float]]
    #: `primitives.autocorr(B, i, 60)` — metals/crypto persistence.
    ac60_prim: list[Optional[float]]
    #: `substrate_engine._ac` over the same 60 returns — the substrate persistence.
    ac60_sub: list[Optional[float]]
    #: `energy_agri.trend_slope(B, i, 30)` — normalised OLS slope over 30 closes / ATR.
    eslope30: list[float]
    #: Donchian channel over the 20 bars strictly before i (`crypto.crypto_signal`).
    don_hh: list[Optional[float]]
    don_ll: list[Optional[float]]
    #: `(direction, stop_dist, gap_bar_k)` of the FVG retest at i, ignoring the vol gate.
    fvg: list[Optional[tuple[int, float, int]]]

    #: Trailing-percentile ranks, `{stat_name: [rank_or_None per bar]}`, filled in by
    #: `normalize.attach_ranks`. Empty until a scale-free variant needs them; kept on the
    #: frame so a percentile gate reads it with the same `(frame, i, params)` signature a
    #: fixed-cut gate uses and the two are interchangeable in a sweep.
    ranks: dict = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.bars)

    def year(self, i: int) -> int:
        return self.times_utc[i].year


def htf_trend_sign(frame: BarFrame, i: int) -> int:
    """`metals.htf_trend(bars, i, 30)`, from the frame.

    The comparison is `diff > 1.0 * a` on the raw difference, not `diff / a > 1.0`, so the
    raw `d30` is what the frame stores.
    """
    a = frame.atr[i]
    d = frame.d30[i]
    if a <= 0 or d is None:
        return 0
    if d > 1.0 * a:
        return 1
    if d < -1.0 * a:
        return -1
    return 0


def fvg_at(frame: BarFrame, i: int, gate_k: float) -> Optional[tuple[int, float]]:
    """`metals.fvg_signal(B, atrs, i, gate_k)` — the vol gate applied to a stored gap.

    See the module docstring: the gap search does not read `gate_k`, so this is the
    production function and not an approximation of it.
    """
    if i < 100:
        return None
    a = frame.atr[i]
    if a <= 0:
        return None
    vr = frame.vr_raw[i]
    if vr is None:
        return None
    # production: `if sma100 <= 0 or a < gate_k * sma100`. vr_raw is a/sma100 with sma100>0,
    # and the frame stores None when sma100 <= 0, so the surviving test is a >= gate_k*sma100.
    if a < gate_k * (a / vr):
        return None
    g = frame.fvg[i]
    if g is None:
        return None
    d, sd, _k = g
    return d, sd


def _fvg_scan(B: Sequence[Bar], atr: Sequence[float], i: int,
              tr: int) -> Optional[tuple[int, float, int]]:
    """The gap loop of `metals.fvg_signal`, verbatim, minus the vol gate.

    Returns `(direction, stop_dist, gap_bar_index)` or None. `tr` is `htf_trend`'s sign.
    """
    if i < 100 or tr == 0:
        return None
    a = atr[i]
    if a <= 0:
        return None
    b = B[i]
    if tr == 1:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_top = B[k].l
            gap_bot = B[k - 2].h
            if gap_top - gap_bot < FVG_MIN_ATR * a:
                continue
            if b.l <= gap_top and b.c > gap_bot and b.c > b.o:
                sd = max((b.c - min(b.l, gap_bot)) + STOP_BUF * a, ATR_STOP_FLOOR * a)
                return 1, sd, k
    else:
        for k in range(i - 2, max(i - 9, 60), -1):
            gap_bot = B[k].h
            gap_top = B[k - 2].l
            if gap_top - gap_bot < FVG_MIN_ATR * a:
                continue
            if b.h >= gap_bot and b.c < gap_top and b.c < b.o:
                sd = max((max(b.h, gap_top) - b.c) + STOP_BUF * a, ATR_STOP_FLOOR * a)
                return -1, sd, k
    return None


def _ols_slope_over(closes: Sequence[float], lo: int, hi: int) -> float:
    """`energy_agri.trend_slope`'s inner least-squares slope, verbatim (lb=30)."""
    ys = closes[lo:hi]
    n = len(ys)
    xs = list(range(n))
    mx = (n - 1) / 2
    my = sum(ys) / n
    num = sum((xs[k] - mx) * (ys[k] - my) for k in range(n))
    den = sum((xs[k] - mx) ** 2 for k in range(n))
    if den == 0:
        return 0.0
    return num / den


def build_frame(symbol: str, timeframe: int, bars: Sequence[Bar],
                times_utc: Sequence[dt.datetime]) -> BarFrame:
    """Compute every armed-sleeve statistic over one bar series, once."""
    n = len(bars)
    B = list(bars)
    closes = [b.c for b in B]
    highs = [b.h for b in B]
    lows = [b.l for b in B]

    atr = [atr14(B, i) for i in range(n)]

    # true range, `substrate_engine._tr` / `atr14`'s inner term (identical formula).
    trv: list[float] = [0.0] * n
    for i in range(1, n):
        pc = closes[i - 1]
        trv[i] = max(highs[i] - lows[i], abs(highs[i] - pc), abs(lows[i] - pc))

    vr: list[float] = [1.0] * n
    vr_raw: list[Optional[float]] = [None] * n
    d30: list[Optional[float]] = [None] * n
    slope20: list[Optional[float]] = [None] * n
    slope50: list[Optional[float]] = [None] * n
    slope100: list[Optional[float]] = [None] * n
    rng_pos: list[Optional[float]] = [None] * n
    comp: list[Optional[float]] = [None] * n
    ac_p: list[Optional[float]] = [None] * n
    ac_s: list[Optional[float]] = [None] * n
    esl: list[float] = [0.0] * n
    don_hh: list[Optional[float]] = [None] * n
    don_ll: list[Optional[float]] = [None] * n
    fvg: list[Optional[tuple[int, float, int]]] = [None] * n

    for i in range(n):
        a = atr[i]
        if i >= 100:
            s = sum(atr[i - 99:i + 1]) / 100
            if s > 0:
                vr[i] = a / s
                vr_raw[i] = a / s
            # production `vol_ratio` returns 1.0 when the window mean is 0; vr_raw stays
            # None so "unmeasurable" is distinguishable from "measured 1.0".
        if i >= HTF_LB:
            d30[i] = closes[i] - closes[i - HTF_LB]
        if a > 0:
            if i >= 20:
                slope20[i] = (closes[i] - closes[i - 20]) / a
            if i >= 50:
                slope50[i] = (closes[i] - closes[i - 50]) / a
            if i >= 100:
                slope100[i] = (closes[i] - closes[i - 100]) / a
        if i >= 49:
            lo50 = min(lows[i - 49:i + 1])
            hi50 = max(highs[i - 49:i + 1])
            rng_pos[i] = (closes[i] - lo50) / (hi50 - lo50) if hi50 > lo50 else 0.5
        if i >= 20:
            num5 = sum(trv[i - 4:i + 1]) / 5
            den20 = sum(trv[i - 19:i + 1]) / 20 or 1
            comp[i] = num5 / den20
        if i >= 61:
            ac_p[i] = autocorr(B, i, 60)
            ac_s[i] = _se._ac([closes[k] - closes[k - 1] for k in range(i - 59, i + 1)])
        if i >= HTF_LB and a > 0:
            esl[i] = _ols_slope_over(closes, i - HTF_LB + 1, i + 1) / a
        if i >= DON_LB:
            don_hh[i] = max(highs[i - DON_LB:i])
            don_ll[i] = min(lows[i - DON_LB:i])
        fvg[i] = _fvg_scan(B, atr, i, _htf_sign(a, d30[i]))

    return BarFrame(
        symbol=symbol, timeframe=int(timeframe), bars=B, times_utc=list(times_utc),
        atr=atr, vr=vr, vr_raw=vr_raw, d30=d30,
        slope20=slope20, slope50=slope50, slope100=slope100,
        rng_pos=rng_pos, comp=comp, ac60_prim=ac_p, ac60_sub=ac_s,
        eslope30=esl, don_hh=don_hh, don_ll=don_ll, fvg=fvg,
    )


def _htf_sign(a: float, d: Optional[float]) -> int:
    if a <= 0 or d is None:
        return 0
    if d > 1.0 * a:
        return 1
    if d < -1.0 * a:
        return -1
    return 0


def frame_summary(frame: BarFrame) -> dict[str, Any]:
    """Small, JSON-safe description of a frame — for artifact provenance."""
    return {
        "symbol": frame.symbol,
        "timeframe": frame.timeframe,
        "n_bars": len(frame),
        "first_utc": frame.times_utc[0].isoformat() if frame.times_utc else None,
        "last_utc": frame.times_utc[-1].isoformat() if frame.times_utc else None,
        "n_fvg_gaps": sum(1 for g in frame.fvg if g is not None),
    }
