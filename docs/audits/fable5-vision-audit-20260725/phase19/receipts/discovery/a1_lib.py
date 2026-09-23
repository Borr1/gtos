#!/usr/bin/env python3
"""a1 shared library - the joint scorer, its walker, and its statistics.

Stamp convention (see a1_10_build.py):  a bar stamped T covers [T, T+1min); its CLOSE
happens at T+1min.  D = decision instant.
    * decision-instant price          = close of stamp D-1                (sidx(-1))
    * trigger M15 bar interior        = stamps D-15 .. D-1
    * x4's confirm minute c0          = close of stamp D, known at D+1min  (sidx(0))
    * a MARKET order sent at D+k min  fills at the close of stamp D+k-1
    * the walk after that fill scores stamps D+k .. D+120

R frame.  Everything is denominated by the candidate's OWN declared risk distance
d = |entry_price - stop_loss|, which is NEVER changed by any arm here, so cost_r is
invariant across arms and R is comparable trade to trade (fixed-fractional sizing).
The re-anchored stop sits at fill - 1R.
"""
from __future__ import annotations
import json
import os

import numpy as np

D_ = os.path.dirname(os.path.abspath(__file__))
S_LO, S_HI = -15, 125
NS = S_HI - S_LO + 1
BELL = 120          # last walk stamp = D+120 (that bar closes at D+121min; see note)
TOL = 1e-12


def sidx(s):
    return s - S_LO


class Month:
    def __init__(self, mm):
        z = np.load(os.path.join(D_, "a1_WIN_%s.npz" % mm))
        self.mm = mm
        self.O = z["O"].astype(np.float64)
        self.H = z["H"].astype(np.float64)
        self.L = z["L"].astype(np.float64)
        self.C = z["C"].astype(np.float64)
        self.Cf = z["Cf"].astype(np.float64)
        self.anchor_px = z["ANCHOR"].astype(np.float64)
        m = json.load(open(os.path.join(D_, "a1_WIN_%s_META.json" % mm)))
        self.meta = m["meta"]
        self.n = self.O.shape[0]
        self.entry = np.array(self.meta["entry_price"], dtype=np.float64)
        self.d = np.array(self.meta["risk_distance"], dtype=np.float64)
        self.sgn = np.array([1.0 if s == "LONG" else -1.0 for s in self.meta["side"]])
        self.symbol = np.array(self.meta["symbol"])
        self.family = np.array(self.meta["family"])
        self.day = np.array(self.meta["day"])
        self.rdp = np.array(self.meta["rdp"], dtype=np.float64)
        self.hour = np.array(self.meta["utc_hour"], dtype=np.float64)
        bh = self.meta["broker_hour"]
        self.broker_hour = np.array([-1 if v is None else v for v in bh], dtype=np.int64)
        # ---- cost bases, all in R units of the (unchanged) risk distance
        self.cost_frozen = np.array(self.meta["cost_frozen"], dtype=np.float64)
        self.cost_true = np.array(self.meta["cost_true"], dtype=np.float64)
        self.cost_hour3 = np.array(self.meta["cost_true_hour"], dtype=np.float64)
        self.swap_r = np.array(self.meta["swap_r"], dtype=np.float64)
        h1 = self.meta["cost_h1_r"]
        self.has_h1 = np.array(self.meta["has_h1"], dtype=bool)
        self.cost_h1 = np.array([np.nan if v is None else v for v in h1])
        # four-term basis that exists in every month: hour-true three-term + swap
        self.cost_hour4 = self.cost_hour3 + self.swap_r
        # the headline basis: h1 four-term where it exists, else hour4
        self.cost = np.where(self.has_h1, np.nan_to_num(self.cost_h1), self.cost_hour4)
        # ---- signed-R views of the window
        self.RH = self.sgn[:, None] * (self.H - self.entry[:, None]) / self.d[:, None]
        self.RL = self.sgn[:, None] * (self.L - self.entry[:, None]) / self.d[:, None]
        self.RC = self.sgn[:, None] * (self.Cf - self.entry[:, None]) / self.d[:, None]
        self.FAV = np.fmax(self.RH, self.RL)     # NaN-safe max (NaN where no bar)
        self.ADV = np.fmin(self.RH, self.RL)
        # ---- pre-decision features
        tb = slice(sidx(-15), sidx(0))
        with np.errstate(invalid="ignore"):
            hi = np.nanmax(self.H[:, tb], axis=1)
            lo = np.nanmin(self.L[:, tb], axis=1)
        self.trig_range = hi - lo
        with np.errstate(invalid="ignore", divide="ignore"):
            self.geo = np.where(self.trig_range > 0, self.d / self.trig_range, np.nan)
        # ---- the confirm minute
        self.c0 = self.RC[:, sidx(0)]
        self.anchor = self.RC[:, sidx(-1)]     # must be ~0 for the at-market cohort
        self.anchor_true = self.sgn * (self.anchor_px - self.entry) / self.d
        self.has_trigger = np.isfinite(self.trig_range) & (self.trig_range > 0)

    # ------------------------------------------------------------------ walker
    def walk(self, k, target=None, stop=-1.0, bell=BELL, trail=None):
        """Market entry at D+k min (fill = close of stamp D+k-1); walk stamps D+k..D+bell.

        Returns (r, reason_code, exit_stamp) where reason_code 0=stop 1=target 2=bell.
        R is in the FILL frame with the risk distance unchanged.
        """
        ei = sidx(k - 1)
        s0, s1 = sidx(k), sidx(bell) + 1
        ck = self.RC[:, ei]
        fav = self.FAV[:, s0:s1] - ck[:, None]
        adv = self.ADV[:, s0:s1] - ck[:, None]
        cls = self.RC[:, s0:s1] - ck[:, None]
        n, w = fav.shape
        BIG = w + 10
        if trail is None:
            hs = adv <= (stop + TOL)
            i_stop = np.where(hs.any(axis=1), hs.argmax(axis=1), BIG)
            if target is None:
                i_tgt = np.full(n, BIG)
            else:
                ht = fav >= (target - TOL)
                i_tgt = np.where(ht.any(axis=1), ht.argmax(axis=1), BIG)
            r = np.where(np.isnan(cls[:, -1]), 0.0, cls[:, -1])
            reason = np.full(n, 2)
            stopped = i_stop <= i_tgt
            hit_t = (i_tgt < i_stop) & (i_tgt < BIG)
            r = np.where((i_stop < BIG) & stopped, stop, r)
            reason = np.where((i_stop < BIG) & stopped, 0, reason)
            if target is not None:
                r = np.where(hit_t, target, r)
                reason = np.where(hit_t, 1, reason)
            ex = np.where((i_stop < BIG) & stopped, i_stop,
                          np.where(hit_t, i_tgt, w - 1))
            return r, reason, ex + k
        # trailing arm (loop; only used for ablation cross-checks)
        r = np.zeros(n)
        reason = np.full(n, 2)
        ex = np.full(n, w - 1)
        for i in range(n):
            st = stop
            peak = -1e18
            done = False
            for j in range(w):
                a, f = adv[i, j], fav[i, j]
                if not np.isnan(a) and a <= st + TOL:
                    r[i] = st
                    reason[i] = 0
                    ex[i] = j
                    done = True
                    break
                if target is not None and not np.isnan(f) and f >= target - TOL:
                    r[i] = target
                    reason[i] = 1
                    ex[i] = j
                    done = True
                    break
                if not np.isnan(f) and f > peak:
                    peak = f
                if peak >= trail:
                    st = max(st, peak - trail)
            if not done:
                v = cls[i, -1]
                r[i] = 0.0 if np.isnan(v) else v
        return r, reason, ex + k

    def stopgone(self, k):
        """Original stop already traded through in [D, D+k) - the 'already dead' refusal."""
        if k <= 0:
            return np.zeros(self.n, dtype=bool)
        seg = self.ADV[:, sidx(0):sidx(k)]
        return np.nanmin(np.where(np.isnan(seg), np.inf, seg), axis=1) <= -1.0 + TOL


# ----------------------------------------------------------------- statistics
def day_blocks(day):
    u = sorted(set(day.tolist()))
    idx = {d: i for i, d in enumerate(u)}
    return np.array([idx[d] for d in day]), len(u)


def dayboot(x, day, B=4000, seed=17):
    """Paired day-block bootstrap of the mean. Returns (mean, lo, hi, p_le0)."""
    if len(x) == 0:
        return (float("nan"),) * 4
    g, nd = day_blocks(day)
    order = np.argsort(g, kind="stable")
    xs = x[order]
    gs = g[order]
    starts = np.searchsorted(gs, np.arange(nd), side="left")
    ends = np.searchsorted(gs, np.arange(nd), side="right")
    sums = np.add.reduceat(xs, starts) if len(xs) else np.zeros(nd)
    cnts = (ends - starts).astype(float)
    rng = np.random.default_rng(seed)
    pick = rng.integers(0, nd, size=(B, nd))
    S = sums[pick].sum(axis=1)
    N = cnts[pick].sum(axis=1)
    m = S / np.maximum(N, 1)
    return (float(x.mean()), float(np.percentile(m, 2.5)),
            float(np.percentile(m, 97.5)), float((m <= 0).mean()))


def tday(x, day):
    """Day-clustered t of the mean (cluster-robust, days as clusters)."""
    if len(x) < 2:
        return float("nan")
    g, nd = day_blocks(day)
    if nd < 2:
        return float("nan")
    n = len(x)
    mu = x.mean()
    res = x - mu
    s = np.zeros(nd)
    np.add.at(s, g, res)
    var = (s ** 2).sum() * nd / max(nd - 1, 1) / (n ** 2)
    return float(mu / np.sqrt(var)) if var > 0 else float("nan")


def ttrade(x):
    if len(x) < 2:
        return float("nan")
    return float(x.mean() / (x.std(ddof=1) / np.sqrt(len(x))))


def spearman(a, b):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ra = np.argsort(np.argsort(a)).astype(float)
    rb = np.argsort(np.argsort(b)).astype(float)
    ra -= ra.mean()
    rb -= rb.mean()
    den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
    return float((ra * rb).sum() / den) if den > 0 else float("nan")


def summarize(gross, cost, day, rdp, reason=None, label="", B=2000):
    net = gross - cost
    m, lo, hi, p = dayboot(net, day, B=B)
    out = {
        "label": label, "n": int(len(net)),
        "days": int(len(set(day.tolist()))) if len(day) else 0,
        "gross_R": float(gross.mean()) if len(gross) else float("nan"),
        "cost_R": float(cost.mean()) if len(cost) else float("nan"),
        "net_R": float(net.mean()) if len(net) else float("nan"),
        "gross_bps": float((gross * rdp * 1e4).mean()) if len(gross) else float("nan"),
        "cost_bps": float((cost * rdp * 1e4).mean()) if len(cost) else float("nan"),
        "net_bps": float((net * rdp * 1e4).mean()) if len(net) else float("nan"),
        "edge_toll": float(gross.mean() / cost.mean()) if len(cost) and cost.mean() else float("nan"),
        "win_rate_net": float((net > 0).mean()) if len(net) else float("nan"),
        "win_rate_gross": float((gross > 0).mean()) if len(gross) else float("nan"),
        "t_trade": ttrade(net), "t_day": tday(net, day),
        "boot_lo": lo, "boot_hi": hi, "p_net_le0": p,
        "total_R": float(net.sum()),
    }
    if len(day):
        u = sorted(set(day.tolist()))
        per = np.array([net[day == d].sum() for d in u])
        out["days_positive"] = int((per > 0).sum())
        out["days_total"] = len(u)
        out["R_per_day_mean"] = float(per.mean())
        out["R_per_day_sd"] = float(per.std(ddof=1)) if len(per) > 1 else float("nan")
        eq = np.cumsum(per)
        out["max_drawdown_R"] = float((np.maximum.accumulate(eq) - eq).max())
        out["equity_by_day"] = [round(float(v), 4) for v in eq]
    if reason is not None and len(reason):
        out["share_stop"] = float((reason == 0).mean())
        out["share_target"] = float((reason == 1).mean())
        out["share_bell"] = float((reason == 2).mean())
    return out
