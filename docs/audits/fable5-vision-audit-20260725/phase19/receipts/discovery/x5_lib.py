#!/usr/bin/env python3
"""x5_lib - shared machinery for the confirmation-trade-off lane."""
import json
import os

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
WIN = os.path.join(D, "x5_WINDOW_JAN.npz")
META = os.path.join(D, "x5_WINDOW_JAN_META.json")

S_LO, S_HI = -15, 180
TOL = 1e-12
STP = -1.0
TRAIL = 0.25
# rungs: every minute inside the trigger bar, the close, every minute for 15 min after,
# then a coarse tail.  k = entry offset in minutes relative to the M15 boundary D.
RUNGS = list(range(-14, 16)) + [20, 25, 30, 45, 60]


def sidx(s):
    return s - S_LO


class W:
    """Loaded window + meta."""

    def __init__(self):
        z = np.load(WIN)
        for k in ("O", "H", "L", "C"):
            setattr(self, k, z[k])
        for k in ("entry0", "stop", "tp1", "sgn", "d0", "anchor", "pre_contig", "ok",
                  "gross_r", "cost_r", "spread_r", "tgt_r", "bte", "firstem",
                  "hour", "symi", "fami", "dayi", "born"):
            setattr(self, k, z[k])
        with open(META) as f:
            m = json.load(f)
        self.symbols = m["symbols"]; self.families = m["families"]; self.days = m["days"]
        self.keys = m["keys"]; self.born_labels = m["born_labels"]
        self.n = len(self.entry0)
        # COMMON POPULATION: every rung must be priceable on exactly these rows.
        # needs the whole trigger bar (so k=-14 has an entry price) and d0>0.
        self.core = (self.ok & (self.pre_contig >= 15) & (self.d0 > 0)
                     & ~np.isnan(self.C[:, sidx(-1)]))
        # forward coverage: bar stamped 0 must exist for every rung's walk to start
        self.core &= ~np.isnan(self.C[:, sidx(0)])

    def entry_at(self, k):
        """Entry price at rung k = close of the bar stamped D+k-1."""
        return self.C[:, sidx(k - 1)].astype(np.float64)


def walk(fav, adv, cls, valid, contract, tgt=None):
    """Vectorised first-touch walk.  fav/adv/cls (n,L) in R, valid (n,L) bool.
    contract: INC (target `tgt` / stop -1R), FIXLEV (per-row target array `tgt`),
              TRAIL025 (stop -1R then trail 0.25R behind MFE), STOPONLY.
    Conservative same-bar tie -> STOP.
    Returns (r, reason, exit_bar); reason 0=target 1=stop 2=mark 3=no-path."""
    nn, L = fav.shape
    r = np.full(nn, np.nan)
    reason = np.full(nn, 3, dtype=np.int8)
    ebar = np.full(nn, -1, dtype=np.int16)
    live = np.zeros(nn, dtype=bool)
    lastc = np.full(nn, np.nan)
    mfe = np.full(nn, -np.inf)
    slev = np.full(nn, STP)
    slev_next = np.full(nn, STP)
    if tgt is not None:
        tgt = np.asarray(tgt, dtype=np.float64)
    for b in range(L):
        v = valid[:, b] & (reason == 3)
        if not v.any():
            continue
        live |= v
        f = fav[:, b]; a = adv[:, b]
        if contract in ("INC", "FIXLEV"):
            hit_s = v & (a <= STP + TOL)
            hit_t = v & (f >= tgt - TOL)
            st = hit_s
            tg = hit_t & ~hit_s
            r[st] = STP; reason[st] = 1; ebar[st] = b
            r[tg] = tgt[tg] if tgt.ndim else tgt
            reason[tg] = 0; ebar[tg] = b
        elif contract == "STOPONLY":
            st = v & (a <= STP + TOL)
            r[st] = STP; reason[st] = 1; ebar[st] = b
        elif contract == "TRAIL025":
            st = v & (a <= slev_next + TOL)
            r[st] = slev_next[st]; reason[st] = 1; ebar[st] = b
        else:
            raise ValueError(contract)
        stillopen = v & (reason == 3)
        lastc[stillopen] = cls[stillopen, b]
        if contract == "TRAIL025":
            slev = slev_next.copy()
            mfe = np.where(stillopen, np.maximum(mfe, f), mfe)
            newlev = np.where(mfe >= TRAIL, mfe - TRAIL, STP)
            slev_next = np.where(stillopen, np.maximum(slev, newlev), slev_next)
    mk = (reason == 3) & live & ~np.isnan(lastc)
    r[mk] = lastc[mk]; reason[mk] = 2
    return r, reason, ebar


def rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC",
               entry_px=None, start_stamp=None, nbars=120):
    """Price one rung.  entry_px overrides the default close-of-(k-1) entry price
    (used by the conditional ladder, where the entry minute varies per row).
    start_stamp overrides the first scored stamp (default k).
    Returns dict with r, reason, ebar, dk, entry, good."""
    n = w.n
    ek = np.asarray(entry_px, dtype=np.float64) if entry_px is not None else w.entry_at(k)
    dk = np.abs(ek - w.stop)
    good = w.core & ~np.isnan(ek) & (dk > 0)
    if start_stamp is None:
        s0 = np.full(n, k, dtype=np.int32)
    else:
        s0 = np.asarray(start_stamp, dtype=np.int32)
    lo = int(np.nanmin(np.where(good, s0, 10 ** 6)))
    if horizon == "WALL":
        hi = 119
    else:
        hi = int(np.nanmax(np.where(good, s0, -10 ** 6))) + nbars - 1
    hi = min(hi, S_HI)
    cols = list(range(sidx(lo), sidx(hi) + 1))
    hh = w.H[:, cols].astype(np.float64)
    ll = w.L[:, cols].astype(np.float64)
    cc = w.C[:, cols].astype(np.float64)
    Lc = len(cols)
    stampcol = np.arange(lo, hi + 1)[None, :]
    if horizon == "WALL":
        vmask = (stampcol >= s0[:, None]) & (stampcol <= 119)
    else:
        vmask = (stampcol >= s0[:, None]) & (stampcol <= (s0[:, None] + nbars - 1))
    dd = (w.d0 if denom == "SHIFTSTOP" else dk)
    dd = np.where(dd > 0, dd, np.nan)
    sg = w.sgn[:, None]; e = ek[:, None]; dv = dd[:, None]
    hi_r = sg * (hh - e) / dv
    lo_r = sg * (ll - e) / dv
    fav = np.where(hi_r >= lo_r, hi_r, lo_r)
    adv = np.where(hi_r >= lo_r, lo_r, hi_r)
    cls = sg * (cc - e) / dv
    valid = (~np.isnan(cc)) & vmask & good[:, None]
    fav = np.nan_to_num(fav, nan=-9e9)
    adv = np.nan_to_num(adv, nan=9e9)
    if contract == "FIXLEV":
        tgt = w.sgn * (w.tp1 - ek) / dd
        tgt = np.where(np.isnan(tgt), 2.0, tgt)
    else:
        tgt = np.full(n, 2.0)
    r, reason, ebar = walk(fav, adv, cls, valid, contract, tgt=tgt)
    r[~good] = np.nan
    return {"r": r, "reason": reason, "ebar": ebar, "dk": dk, "entry": ek, "good": good,
            "tgt": tgt, "Lc": Lc}


# ---------------------------------------------------------------- statistics
def dayblock_boot(vals, days, B=2000, seed=7):
    """Day-block bootstrap of the mean.  vals/days are 1-D aligned arrays."""
    rng = np.random.default_rng(seed)
    ud = np.unique(days)
    idx = {d: np.where(days == d)[0] for d in ud}
    means = np.empty(B)
    nd = len(ud)
    for b in range(B):
        pick = rng.integers(0, nd, nd)
        sel = np.concatenate([idx[ud[p]] for p in pick])
        means[b] = vals[sel].mean()
    return {"mean": float(vals.mean()), "lo": float(np.percentile(means, 2.5)),
            "hi": float(np.percentile(means, 97.5)),
            "p_le0": float((means <= 0).mean()), "B": B}


def paired_boot(a, b, days, B=2000, seed=11):
    """Day-block bootstrap of the paired difference a-b."""
    d = a - b
    return dayblock_boot(d, days, B=B, seed=seed)


def summ(r, good, days=None, tag=""):
    v = r[good]
    out = {"tag": tag, "n": int(good.sum()), "mean": float(np.nanmean(v)),
           "total": float(np.nansum(v)), "win": float((v > 0).mean()),
           "med": float(np.nanmedian(v))}
    return out
