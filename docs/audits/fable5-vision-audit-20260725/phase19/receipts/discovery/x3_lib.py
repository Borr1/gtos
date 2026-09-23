#!/usr/bin/env python3
"""x3_lib — vectorised entry-offset walker over the x3 M1 tape.

Everything is in R units with the candidate's OWN risk distance `d` held fixed, so an
arm at offset k is the identical geometry (stop -1R, target +tgt R) re-anchored to the
price the market was at k minutes after the decision instant.  k<0 = inside the forming
M15 bar; k=0 = the shipped contract's entry instant (the M15 close).
"""
from __future__ import annotations
import os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TAPE = os.path.join(HERE, "x3_TAPE.npz")
EPS = 1e-12


class Tape:
    def __init__(self, path=TAPE):
        z = np.load(path, allow_pickle=False)
        self.px = z["px"]                      # (n, NOFF, 4) o,h,l,c
        self.entry = z["entry"]; self.rdist = z["rdist"]
        self.is_long = z["is_long"]; self.tgt = z["tgt"]
        self.cost_r = z["cost_r"]; self.spread_r = z["spread_r"]
        self.gross_r = z["gross_r"]; self.plain = z["plain"]
        self.born = z["born"]; self.fam = z["fam"]; self.sym = z["sym"]
        self.day = z["day"]; self.cid = z["cid"]; self.dtu = z["dtu"]
        self.hour = z["hour"]; self.firstem = z["firstem"]
        self.off_lo = int(z["off_lo"][0]); self.off_hi = int(z["off_hi"][0])
        self.n, self.noff = self.px.shape[0], self.px.shape[1]
        s = np.where(self.is_long, 1.0, -1.0)[:, None]
        E = self.entry[:, None]; d = self.rdist[:, None]
        hi, lo, cl = self.px[:, :, 1], self.px[:, :, 2], self.px[:, :, 3]
        # R of each bar's extremes measured from the ORIGINAL entry (offset independent)
        self.favE = np.where(self.is_long[:, None], (hi - E), (E - lo)) / d
        self.advE = np.where(self.is_long[:, None], (lo - E), (E - hi)) / d
        self.clsE = (cl - E) * s / d
        self.valid = ~np.isnan(cl)
        # per-row entry price offset in R, for entry at instant T+k (close of bar T+k-1)
        self.mR = (cl - E) * s / d              # market R at close of each labelled bar
        # notional bps per 1.0 R
        self.bps_per_R = self.rdist / self.entry * 1e4

    def j(self, off):
        return off - self.off_lo


def walk(t: Tape, k: int, contract="pool", trail=0.25, target=None, max_bars=None,
         sub=None, stop_r=-1.0):
    """Enter at instant T+k (close of bar labelled T+k-1); walk bars T+k .. T+120.

    contract 'pool'  : target at +tgt R (per row), stop -1R, else mark-to-market at the
                       last available bar close.  Conservative tie: stop wins.
    contract 'trail' : no target, stop -1R, trailing `trail` R behind the running MFE,
                       armed-at-bar-i-checked-from-i+1.
    Returns dict of float arrays over the FULL row index; rows not tradable at this
    offset carry NaN in `r`.
    """
    n = t.n
    je = t.j(k) - 1                      # entry bar (its close is the entry price)
    js = t.j(k)                          # first walk bar
    sel = np.ones(n, bool) if sub is None else sub.copy()
    sel &= t.valid[:, je]
    m = np.where(sel, t.mR[:, je], np.nan)      # entry offset in R from original entry
    r = np.full(n, np.nan)
    reason = np.zeros(n, np.int8)               # 1 target 2 stop 3 mtm 4 no_bars
    exitbar = np.full(n, -1, np.int16)
    peak = np.full(n, -np.inf)
    stop = np.full(n, float(stop_r))
    done = ~sel
    lastcls = np.full(n, np.nan)
    lastbar = np.full(n, -1, np.int16)
    tg = t.tgt if target is None else np.full(n, float(target))
    last = t.noff if max_bars is None else min(t.noff, js + max_bars)
    for j in range(js, last):
        v = t.valid[:, j] & ~done
        if not v.any():
            continue
        fav = t.favE[:, j] - m
        adv = t.advE[:, j] - m
        cls = t.clsE[:, j] - m
        hs = v & (adv <= stop + EPS)
        if hs.any():
            r[hs] = stop[hs]; reason[hs] = 2; exitbar[hs] = j - js + 1; done |= hs
        v = v & ~hs
        if contract == "pool":
            ht = v & (fav >= tg - EPS)
            if ht.any():
                r[ht] = tg[ht]; reason[ht] = 1; exitbar[ht] = j - js + 1; done |= ht
            v = v & ~ht
        np.maximum(peak, np.where(v, fav, -np.inf), out=peak)
        if contract == "trail":
            armed = peak >= trail
            np.maximum(stop, np.where(armed, peak - trail, stop), out=stop)
        lastcls = np.where(v, cls, lastcls)
        lastbar = np.where(v, j - js + 1, lastbar)
    open_ = sel & ~done
    r[open_] = lastcls[open_]
    reason[open_] = 3
    exitbar[open_] = lastbar[open_]
    nb = sel & np.isnan(r)
    r[nb] = np.nan; reason[nb] = 4
    return {"r": r, "reason": reason, "exit_bar": exitbar, "sel": sel & ~nb,
            "entry_offset_R": m}


def summarise(t: Tape, res, mask=None, label=""):
    s = res["sel"] if mask is None else (res["sel"] & mask)
    r = res["r"][s]
    if r.size == 0:
        return {"label": label, "n": 0}
    cost = t.cost_r[s]
    bw = t.bps_per_R[s]
    reason = res["reason"][s]
    sd = r.std(ddof=1) if r.size > 1 else float("nan")
    return {
        "label": label, "n": int(r.size),
        "gross_R": float(r.mean()), "gross_sd": float(sd),
        "t": float(r.mean() / (sd / np.sqrt(r.size))) if r.size > 1 and sd > 0 else None,
        "median_R": float(np.median(r)),
        "win_rate": float((r > 0).mean()),
        "target_rate": float((reason == 1).mean()),
        "stop_rate": float((reason == 2).mean()),
        "mtm_rate": float((reason == 3).mean()),
        "net_R": float((r - cost).mean()),
        "cost_R": float(cost.mean()),
        "gross_bps": float((r * bw).mean()),
        "cost_bps": float((cost * bw).mean()),
        "net_bps": float(((r - cost) * bw).mean()),
        "mean_exit_bar": float(res["exit_bar"][s].mean()),
    }


def dayboot(day, x, reps=2000, seed=20260806):
    """Block bootstrap by calendar day on a vector of per-trade values."""
    rng = np.random.default_rng(seed)
    days, inv = np.unique(day, return_inverse=True)
    buckets = [x[inv == i] for i in range(len(days))]
    nd = len(days)
    out = np.empty(reps)
    for b in range(reps):
        pick = rng.integers(0, nd, nd)
        out[b] = np.concatenate([buckets[p] for p in pick]).mean()
    out.sort()
    return {"mean": float(x.mean()), "lo95": float(out[int(.025 * reps)]),
            "hi95": float(out[int(.975 * reps)]),
            "p_le_0": float((out <= 0).mean()), "n_days": int(nd)}
