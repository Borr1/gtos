"""d8_lib — substrate for the d8 lane (WHAT HAVE WE NOT LOOKED AT).

The estate has measured this family exclusively in R units, where R is the generator's
own stop distance.  R is volatility-scaled, so any information the family carries about
the SIZE of the coming move is divided out by construction.  This module measures the
family in PRICE space (bps) against a fully-enumerated control: every one of the 96
M15 decision windows on the same symbol and the same UTC day.

Nothing is sampled.  The control is the whole grid.
"""
from __future__ import annotations

import csv
import glob
import gzip
import json
import os
from datetime import datetime, timedelta, timezone

import numpy as np

BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")

ROSTER_DIR = {
    "202510": "/tmp/f2_close_202510",
    "202511": "/tmp/f2_close_202511",
    "202512": "/tmp/f2_close_202512",
    "202601": "/tmp/pbg_full_jan",
    "202602": "/tmp/pbg_full_feb",
    "202603": "/tmp/pbg_full_mar",
    "202604": "/tmp/f2_close_202604",
    "202605": "/tmp/f2_close_202605",
}
MONTHS = tuple(sorted(ROSTER_DIR))

AT_MARKET = ("displacement_continuation", "liquidity_sweep_reclaim",
             "structural_distance_extreme", "volatility_compression_expansion",
             "session_open_range_break", "regime_transition_break",
             "cross_asset_lead_lag")
POI = ("current_fvg_fill", "current_ob_retest", "current_breaker_re_entry")

HORIZONS = (15, 60, 240, 1440)   # M1 bars: 15 min, 1 h, 4 h, 24 h
NEG = np.float64(-1e18)
POS = np.float64(1e18)


def month_symbols(mm):
    d = os.path.join(BARS, "bridge_ftmo_m1_%s" % mm)
    return sorted(p[len(d) + 1:-len("_M1.csv")] for p in glob.glob(os.path.join(d, "*_M1.csv")))


def next_month(mm):
    y, m = int(mm[:4]), int(mm[4:])
    return "%04d%02d" % ((y + 1, 1) if m == 12 else (y, m + 1))


def base_dt(mm):
    return datetime(int(mm[:4]), int(mm[4:]), 1, tzinfo=timezone.utc)


class Tape:
    """Dense per-minute OHLC grid for one month plus the following month's overhang."""

    def __init__(self, mm, symbols=None, overhang_days=3):
        self.mm = mm
        self.base = base_dt(mm)
        nm = next_month(mm)
        end = base_dt(nm) + timedelta(days=overhang_days)
        self.n = int((end - self.base).total_seconds() // 60)
        self.symbols = symbols or month_symbols(mm)
        self.O, self.H, self.L, self.C, self.V = {}, {}, {}, {}, {}
        for sym in self.symbols:
            o = np.full(self.n, np.nan)
            h = np.full(self.n, np.nan)
            l = np.full(self.n, np.nan)
            c = np.full(self.n, np.nan)
            v = np.zeros(self.n, dtype=bool)
            for m in (mm, nm):
                p = os.path.join(BARS, "bridge_ftmo_m1_%s" % m, "%s_M1.csv" % sym)
                if not os.path.isfile(p):
                    continue
                with open(p) as fh:
                    rd = csv.reader(fh)
                    next(rd)
                    for r in rd:
                        t = datetime.fromisoformat(r[0])
                        i = int((t - self.base).total_seconds() // 60)
                        if 0 <= i < self.n:
                            o[i] = float(r[1]); h[i] = float(r[2])
                            l[i] = float(r[3]); c[i] = float(r[4]); v[i] = True
            self.O[sym], self.H[sym], self.L[sym], self.C[sym], self.V[sym] = o, h, l, c, v

    def idx(self, iso):
        return int((datetime.fromisoformat(iso) - self.base).total_seconds() // 60)


def ffill(a):
    """forward-fill NaN with the last valid value."""
    idx = np.where(np.isfinite(a), np.arange(a.size), 0)
    np.maximum.accumulate(idx, out=idx)
    out = a[idx]
    # leading NaNs stay NaN
    first = np.argmax(np.isfinite(a)) if np.isfinite(a).any() else a.size
    out[:first] = np.nan
    return out


def block_max(a, h):
    """max over the forward window [i, i+h) for every i, O(n).  a must be finite-filled."""
    n = a.size
    pad = (-n) % h
    b = np.concatenate([a, np.full(pad, NEG)])
    m = b.reshape(-1, h)
    pre = np.maximum.accumulate(m, axis=1).ravel()          # max of block start..j
    suf = np.maximum.accumulate(m[:, ::-1], axis=1)[:, ::-1].ravel()  # max of j..block end
    out = np.full(n + pad, NEG)
    # window [i, i+h-1] spans at most two blocks: suffix from i, prefix up to i+h-1
    hi = np.arange(n + pad) + h - 1
    ok = hi < (n + pad)
    out[ok] = np.maximum(suf[np.arange(n + pad)[ok]], pre[hi[ok]])
    return out[:n]


def block_min(a, h):
    return -block_max(-a, h)


def forward_stats(tape, sym, horizons=HORIZONS):
    """Return dict h -> (ret_long_bps, hi_bps, lo_bps, valid) evaluated AT instant-minute i.

    Convention (PB's, and f2's): the decision instant t sits at minute i; the anchor price
    is the last M1 close strictly before t, i.e. C[i-1].  The forward window is the bars
    opening at i .. i+h-1.
    """
    C, H, L, V = tape.C[sym], tape.H[sym], tape.L[sym], tape.V[sym]
    n = C.size
    Cff = ffill(C)
    Hf = np.where(np.isfinite(H), H, NEG)
    Lf = np.where(np.isfinite(L), L, POS)
    vcum = np.concatenate([[0], np.cumsum(V.astype(np.int64))])
    anchor = np.full(n, np.nan)
    anchor[1:] = C[:-1]                      # real close of the bar ending at t
    out = {}
    for h in horizons:
        hi = block_max(Hf, h)
        lo = block_min(Lf, h)
        j = np.minimum(np.arange(n) + h - 1, n - 1)
        endc = Cff[j]
        cnt = vcum[np.minimum(np.arange(n) + h, n)] - vcum[np.arange(n)]
        valid = (np.isfinite(anchor) & np.isfinite(endc)
                 & (cnt >= max(1, int(0.2 * h)))
                 & (hi > NEG / 2) & (lo < POS / 2)
                 & ((np.arange(n) + h) <= n))
        a = np.where(valid, anchor, np.nan)
        ret = (endc - a) / a * 1e4
        hib = (hi - a) / a * 1e4
        lob = (a - lo) / a * 1e4
        out[h] = (ret.astype(np.float32), hib.astype(np.float32),
                  lob.astype(np.float32), valid)
    out["anchor"] = anchor
    return out


def setup_key(r):
    if r["f"].startswith("current_"):
        return (r["s"], r["f"], r["d"], r["b"], r["cid"])
    return (r["s"], r["f"], r["d"], r["b"])


def load_roster(mm, families=None):
    """One row per setup key, close-only (k=15) — PB's BOOK_close_only population."""
    seen = {}
    for p in sorted(glob.glob(os.path.join(ROSTER_DIR[mm], "pbg_*.jsonl.gz"))):
        with gzip.open(p, "rt") as fh:
            for line in fh:
                r = json.loads(line)
                if r.get("k") != 15:
                    continue
                if families is not None and r["f"] not in families:
                    continue
                k = setup_key(r)
                if k not in seen:
                    seen[k] = r
    return list(seen.values())


def grid_instants(mm, tape):
    """Every one of the 96 M15 decision windows on every UTC day of the month."""
    days = []
    d = base_dt(mm)
    while d.month == int(mm[4:]):
        days.append(d.strftime("%Y-%m-%d"))
        d += timedelta(days=1)
    out = []
    for day in days:
        i0 = int((datetime.fromisoformat(day + "T00:00:00+00:00") - tape.base).total_seconds() // 60)
        for w in range(96):
            out.append((day, w, i0 + 15 * w))
    return out
