#!/usr/bin/env python3
"""l11 — vectorised exit-contract engine on the fill-aligned R paths.

One numpy pass over 120 bars evaluates ANY parametrised contract for all 24k paths at once
(~15 ms), so a 10,000-cell contract search is seconds, not hours.

Contract parameters (all optional, all in R on the ORIGINAL risk distance):
  target        take-profit level                     (None = no target)
  stop          initial stop, positive number         (None = no stop)
  be_at         move stop to 0 once peak >= be_at
  trail_arm     arm the trail once peak >= trail_arm
  trail_gap     trail the stop this far behind peak
  partial_at    book partial_frac of the unit at this favourable level
  partial_frac  fraction booked at partial_at (remainder rides the rest of the contract)
  max_bars      time stop: mark at the close of this bar (bars since FILL, 1-based)
  scratch_bar / scratch_below : at bar `scratch_bar`, exit at close if r < scratch_below

TIE RULE inside a bar: the STOP is taken (conservative, same as w0/l1).
Unfilled candidates book exactly 0.0 R and are counted in the denominator.
"""
from __future__ import annotations

import os

import numpy as np

import l11_lib

HERE = os.path.dirname(os.path.abspath(__file__))
ALIGNED = os.path.join(HERE, "l11_ALIGNED_V1.npz")
T = 120


def aligned(s, mode="real"):
    """Fill-aligned (N,120) fav/adv/cls with NaN past the end of the path."""
    path = ALIGNED if mode == "real" else ALIGNED.replace("_V1", "_STRICT_V1")
    fillix = s.fill if mode == "real" else s.fill_strict
    if os.path.exists(path):
        z = np.load(path)
        return z["F"], z["D"], z["A"], z["rem"]
    N = s.N
    F = np.full((N, T), np.nan, np.float32)
    D = np.full((N, T), np.nan, np.float32)
    A = np.full((N, T), np.nan, np.float32)
    rem = np.zeros(N, np.int32)
    for i in range(N):
        f = int(fillix[i])
        if f < 0:
            continue
        k = int(s.nb[i]) - f
        if k <= 0:
            continue
        rem[i] = k
        F[i, :k] = s.fav[i, f:f + k]
        D[i, :k] = s.adv[i, f:f + k]
        A[i, :k] = s.cls[i, f:f + k]
    np.savez_compressed(path, F=F, D=D, A=A, rem=rem)
    return F, D, A, rem


class Engine:
    def __init__(self, s=None, fill_mode="real"):
        self.s = s if s is not None else l11_lib.load()
        self.fill_mode = fill_mode
        self.F, self.D, self.A, self.rem = aligned(self.s, fill_mode)
        self.alive0 = self.rem > 0

    def run(self, target=2.0, stop=1.0, be_at=None, trail_arm=None, trail_gap=None,
            partial_at=None, partial_frac=0.5, max_bars=None,
            scratch_bar=None, scratch_below=None, rows=None,
            arm_bar=None, target_arm_bar=None, stop_arm_bar=None, late_stop=None,
            late_stop_bar=None, stop_slip_r=0.0, trail_same_bar=False):
        """Returns (r, reason_code, exit_bar). reason: 0 no_fill 1 stop 2 target
        3 time/path_end.

        arm_bar          neither stop nor target can fire before this 1-based bar (grace)
        target_arm_bar   target alone is dormant before this bar
        stop_arm_bar     stop alone is dormant before this bar
        late_stop /
        late_stop_bar    from late_stop_bar onward the stop tightens to -late_stop
        """
        if arm_bar is not None:
            target_arm_bar = arm_bar if target_arm_bar is None else target_arm_bar
            stop_arm_bar = arm_bar if stop_arm_bar is None else stop_arm_bar
        F, D, A, rem = self.F, self.D, self.A, self.rem
        if rows is not None:
            F, D, A, rem = F[rows], D[rows], A[rows], rem[rows]
        n = len(rem)
        r = np.zeros(n, np.float64)
        reason = np.zeros(n, np.int8)
        ebar = np.full(n, -1, np.int32)
        open_ = rem > 0
        stoplvl = np.full(n, -stop if stop is not None else -1e18, np.float64)
        peak = np.full(n, -1e18, np.float64)
        booked = np.zeros(n, np.float64)
        remfrac = np.ones(n, np.float64)
        last = rem if max_bars is None else np.minimum(rem, max_bars)
        mark_prev = np.full(n, np.nan, np.float64)   # close of the previous bar
        for t in range(T):
            act = open_ & (t < last)
            if not act.any():
                break
            f = F[:, t]
            d = D[:, t]
            stop_live = (stop_arm_bar is None) or (t + 1 >= stop_arm_bar)
            tgt_live = (target_arm_bar is None) or (t + 1 >= target_arm_bar)
            if late_stop is not None and late_stop_bar is not None and t + 1 == late_stop_bar:
                stoplvl = np.maximum(stoplvl, -late_stop)
            # --- NO TIME TRAVEL: a stop that is armed or tightened onto a price the market
            # has ALREADY passed is a market order, and it fills at the last knowable price
            # (the previous close), not at the stop level.  For a continuously-live stop
            # this branch is unreachable (d[t-1] <= cls[t-1] would already have fired), so
            # it changes nothing for ordinary contracts and everything for late-armed ones.
            if stop_live:
                already = act & ~np.isnan(mark_prev) & (mark_prev <= stoplvl + 1e-12)
                if already.any():
                    r[already] = (booked[already]
                                  + remfrac[already] * (mark_prev[already] - stop_slip_r))
                    reason[already] = 1
                    ebar[already] = t + 1
                    open_ &= ~already
                    act &= ~already
            # --- stop first (conservative tie)
            hit = act & (d <= stoplvl + 1e-12) if stop_live else np.zeros(n, bool)
            if hit.any():
                r[hit] = booked[hit] + remfrac[hit] * (stoplvl[hit] - stop_slip_r)
                reason[hit] = 1
                ebar[hit] = t + 1
                open_ &= ~hit
                act &= ~hit
            # --- partial scale-out
            if partial_at is not None:
                p = act & (remfrac > partial_frac + 1e-12) & (f >= partial_at - 1e-12)
                if p.any():
                    booked[p] += partial_frac * partial_at
                    remfrac[p] -= partial_frac
            # --- target
            if target is not None and tgt_live:
                tg = act & (f >= target - 1e-12)
                if tg.any():
                    r[tg] = booked[tg] + remfrac[tg] * target
                    reason[tg] = 2
                    ebar[tg] = t + 1
                    open_ &= ~tg
                    act &= ~tg
            # --- update peak / BE / trail for the survivors
            np.maximum(peak, np.where(act, f, -1e18), out=peak)
            if be_at is not None:
                b = act & (peak >= be_at - 1e-12) & (stoplvl < 0.0)
                stoplvl[b] = 0.0
            if trail_arm is not None and trail_gap is not None:
                tr = act & (peak >= trail_arm - 1e-12)
                if tr.any():
                    stoplvl[tr] = np.maximum(stoplvl[tr], peak[tr] - trail_gap)
                if trail_same_bar:
                    # OPTIMISTIC convention (primitives.simulate / trail_lag_extremes=False):
                    # the trail arms off THIS bar's high and fills off THIS bar's low, at the
                    # level. exits.py:395-406 documents it; B613 measured 95.8% of asian_fade's
                    # trail exits landing on the first bar after entry under it.
                    sb = tr & (d <= stoplvl + 1e-12)
                    if sb.any():
                        r[sb] = booked[sb] + remfrac[sb] * stoplvl[sb]
                        reason[sb] = 1
                        ebar[sb] = t + 1
                        open_ &= ~sb
                        act &= ~sb
            # --- conditional scratch at a named bar
            if scratch_bar is not None and t + 1 == scratch_bar:
                sc = act & (A[:, t] < scratch_below)
                if sc.any():
                    r[sc] = booked[sc] + remfrac[sc] * A[:, t][sc]
                    reason[sc] = 3
                    ebar[sc] = t + 1
                    open_ &= ~sc
            mark_prev = A[:, t].astype(np.float64)
        # --- everyone still open marks at the close of their last allowed bar
        still = open_ & (rem > 0)
        if still.any():
            j = (last[still] - 1).astype(int)
            r[still] = booked[still] + remfrac[still] * A[still, j]
            reason[still] = 3
            ebar[still] = last[still]
        nf = rem <= 0
        r[nf] = 0.0
        reason[nf] = 0
        return r, reason, ebar


def summarize(r, reason, cost=None, n_denom=None):
    n = len(r) if n_denom is None else n_denom
    out = {"n": int(n), "gross": round(float(r.sum() / n), 6),
           "win_rate": round(float((r > 1e-9).sum() / max((reason != 0).sum(), 1)), 5),
           "no_fill": int((reason == 0).sum()),
           "stop": int((reason == 1).sum()), "target": int((reason == 2).sum()),
           "mark": int((reason == 3).sum())}
    if cost is not None:
        out["net"] = round(float((r - np.where(reason == 0, 0.0, cost)).sum() / n), 6)
    return out


if __name__ == "__main__":
    import json
    e = Engine()
    s = e.s
    m = s.takeable
    r, rs, eb = e.run(target=2.0, stop=1.0, rows=m)
    print("T2/S1 TAKEABLE:", json.dumps(summarize(r, rs)))
    r2, rs2, _ = e.run(target=None, stop=None, rows=m)
    print("hold-to-wall  :", json.dumps(summarize(r2, rs2)))
