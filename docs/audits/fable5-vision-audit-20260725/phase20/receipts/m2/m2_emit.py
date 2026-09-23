"""m2_emit — a standalone, provable re-implementation of `structural_distance_extreme`.

Lifted line-for-line from the production generator so it can be run on bar archives the
pbg harness cannot reach (the never-read June/July 2026 tick window).  It is NOT trusted:
`m2_repro.py` proves it reproduces the frozen wave-19 roster's k=15 rows exactly before any
economic number is taken from it.

Production sources (worktree wave19-broad-forensic-20260801):
  _atr                   broader_origin_generators.py:2511-2515   mean(high-low) over `lookback` bars ending at index
  _prior_high/_prior_low               :2500-2508
  _close_position                      :2517-2525
  guards                               :641-658  (atr14>0, atr50>0, all four priors present)
  structural_distance_extreme          :884-916  (pos50 >= 0.97 -> SHORT, <= 0.03 -> LONG)
  _candidate target                    :2038     target = entry +/- target_rr * |entry-stop|
  _valid_geometry                      :2841-2846
  series length guard                  :320      len(series.bars) >= 51
"""
from __future__ import annotations

import numpy as np


def emit_sde(o, h, l, c, target_rr: float = 1.5, warmup: int = 50):
    """Vectorised emitter.  Returns (idx, is_long, entry, stop, target) numpy arrays.

    o/h/l/c are float64 arrays of the M15 series in time order.  `idx` indexes them.
    `warmup` = the index below which the generator cannot have been called with a
    >=51-bar window (production requires len(series.bars) >= 51, and the index used is
    the LAST bar, so index >= 50).
    """
    n = len(c)
    rng = h - l

    # _atr(series, index, k) = mean(high-low) over bars[max(0,index-k+1) : index+1]
    csum = np.concatenate(([0.0], np.cumsum(rng)))

    def atr(k):
        idx = np.arange(n)
        start = np.maximum(0, idx - k + 1)
        cnt = idx + 1 - start
        return (csum[idx + 1] - csum[start]) / cnt

    atr14 = atr(14)
    atr50 = atr(50)

    # _prior_high(series, index, k) = max(high) over bars[max(0,index-k):index]  (EXCLUDES index)
    # _close_position(series, index, 50) uses bars[index-49:index+1] (INCLUDES index)
    def roll_max(a, k, include_self):
        out = np.full(n, np.nan)
        # exact, O(n*k) is fine for k<=50 at these sizes; use a strided max
        for i in range(n):
            if include_self:
                s = max(0, i - k + 1)
                e = i + 1
            else:
                s = max(0, i - k)
                e = i
            if e <= s:
                continue
            out[i] = a[s:e].max()
        return out

    def roll_min(a, k, include_self):
        out = np.full(n, np.nan)
        for i in range(n):
            if include_self:
                s = max(0, i - k + 1)
                e = i + 1
            else:
                s = max(0, i - k)
                e = i
            if e <= s:
                continue
            out[i] = a[s:e].min()
        return out

    ph20 = roll_max(h, 20, False)
    pl20 = roll_min(l, 20, False)
    ph50 = roll_max(h, 50, False)
    pl50 = roll_min(l, 50, False)

    hi50 = roll_max(h, 50, True)
    lo50 = roll_min(l, 50, True)
    with np.errstate(invalid="ignore", divide="ignore"):
        pos50 = np.where(hi50 > lo50, (c - lo50) / (hi50 - lo50), np.nan)

    ok = (
        np.isfinite(atr14) & (atr14 > 0)
        & np.isfinite(atr50) & (atr50 > 0)
        & np.isfinite(ph20) & np.isfinite(pl20)
        & np.isfinite(ph50) & np.isfinite(pl50)
        & np.isfinite(pos50)
    )
    ok[:warmup] = False

    short = ok & (pos50 >= 0.97)
    long_ = ok & (pos50 <= 0.03)

    idx = np.concatenate([np.nonzero(short)[0], np.nonzero(long_)[0]])
    is_long = np.concatenate([np.zeros(short.sum(), bool), np.ones(long_.sum(), bool)])
    entry = c[idx]
    stop = np.where(is_long, l[idx] - 0.25 * atr14[idx], h[idx] + 0.25 * atr14[idx])
    risk = np.abs(entry - stop)
    target = np.where(is_long, entry + target_rr * risk, entry - target_rr * risk)

    # _valid_geometry
    good = np.where(is_long, (stop < entry) & (entry < target), (target < entry) & (entry < stop))
    order = np.argsort(idx[good], kind="stable")
    g = np.nonzero(good)[0][order]
    return idx[g], is_long[g], entry[g], stop[g], target[g], pos50[idx[g]], atr14[idx[g]]
