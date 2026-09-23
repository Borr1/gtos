#!/usr/bin/env python3
"""x5_build - the CONFIRMATION AXIS frame.

Extends the estate's entry-offset axis BACKWARDS into the trigger M15 bar.

Bar-stamp convention (verified by w0-capture and e6): an M1 bar stamped T covers
[T, T+1min), so its CLOSE happens at T+1min.  A decision at M15 boundary D is
therefore made on information whose last knowable price is the close of the bar
stamped D-1min.  The trigger M15 bar is the 15 sub-bars stamped D-15 .. D-1.

Entry offset k (minutes relative to D):
    entry price = close of the bar stamped D+k-1        (index s = k-1)
    k = 0   -> the shipped contract (entry == M15 close == pool entry_price for at-market)
    k = -14 -> entry at the close of the FIRST minute of the trigger bar
    k = +5  -> the estate's "delay 5" rung (close of path bar 5)
Forward walk uses bars stamped D+k, D+k+1, ...

Two R denominators, both reported, because they are different trades:
    SHIFTSTOP  d = d0 = |entry_0 - stop_loss| held fixed, stop rides with the entry.
               This is the estate's convention for k>=0 (e_build_atmkt.py) - nests exactly.
    STRUCTSTOP d_k = |entry_k - stop_loss|; the STRUCTURAL stop price never moves and the
               position is resized.  This is what a fixed-fractional book actually gets.

Contracts: INC (target 2R / stop -1R, same-bar tie -> stop), TRAIL025 (no target, stop
-1R, trail 0.25R behind running MFE, a stop armed at bar i is checked from bar i+1 ONLY),
STOPONLY (stop -1R, mark at horizon).

Horizon: wall-clock, bars stamped D .. D+119 (the pool's own 2 h window) for the primary
arm; a horizon-MATCHED arm (exactly 120 bars from entry) is emitted as a control.

usage: python3 x5_build.py [OUT.npz]
"""
import bisect
import csv
import gzip
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa: E402

BARS_ROOT = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
             "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
BARS_DIR = "bridge_ftmo_m1_202601"

S_LO, S_HI = -15, 180           # bar-stamp offsets kept, inclusive
NS = S_HI - S_LO + 1            # 196
OFFS = list(range(-14, 1)) + [1, 2, 3, 5, 10, 15, 20, 30, 45, 60]
TOL = 1e-12
TGT = 2.0
STP = -1.0
TRAIL = 0.25


def sidx(s):
    return s - S_LO


def load_bars(sym):
    p = os.path.join(BARS_ROOT, BARS_DIR, "%s_M1.csv" % sym)
    if not os.path.isfile(p):
        return None
    t, h, l, c = [], [], [], []
    with open(p) as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            t.append(r[0])
            h.append(float(r[2]))
            l.append(float(r[3]))
            c.append(float(r[4]))
    return {"t": t, "h": np.array(h), "l": np.array(l), "c": np.array(c)}


def build():
    t0 = time.time()
    rows = w0_ws.load()
    print("pool rows %d  (%.1fs)" % (len(rows), time.time() - t0), flush=True)
    syms = sorted({r["symbol"] for r in rows})
    bars = {}
    for s in syms:
        b = load_bars(s)
        if b is not None:
            bars[s] = b
    print("bar files loaded: %d/%d  (%.1fs)" % (len(bars), len(syms), time.time() - t0), flush=True)

    n = len(rows)
    H = np.full((n, NS), np.nan, dtype=np.float32)
    L = np.full((n, NS), np.nan, dtype=np.float32)
    C = np.full((n, NS), np.nan, dtype=np.float32)
    entry0 = np.zeros(n)
    stop = np.zeros(n)
    sgn = np.zeros(n)
    d0 = np.zeros(n)
    anchor = np.full(n, np.nan)
    pre_contig = np.zeros(n, dtype=np.int16)   # contiguous minutes present in [-15,-1]
    ok = np.zeros(n, dtype=bool)
    keys = []

    for i, r in enumerate(rows):
        keys.append([r["candidate_id"], r["decision_time_utc"]])
        b = bars.get(r["symbol"])
        if b is None:
            continue
        dt = r["decision_time_utc"]
        dtt = datetime.fromisoformat(dt)
        # bar stamped D-1min
        j = bisect.bisect_left(b["t"], (dtt - timedelta(minutes=1)).isoformat())
        if j >= len(b["t"]) or b["t"][j] != (dtt - timedelta(minutes=1)).isoformat():
            continue
        e = float(r["entry_price"])
        sl = float(r["stop_loss"])
        d = abs(e - sl)
        if not (d > 0):
            continue
        sg = 1.0 if (r.get("side") or r.get("direction")) == "LONG" else -1.0
        entry0[i] = e
        stop[i] = sl
        sgn[i] = sg
        d0[i] = d
        anchor[i] = sg * (float(b["c"][j]) - e) / d
        # fill the stamp window by exact timestamp match, walking outwards from j
        lo = max(0, j - 20)
        hi = min(len(b["t"]), j + 200)
        for kx in range(lo, hi):
            off = int(round((datetime.fromisoformat(b["t"][kx]) - dtt).total_seconds() / 60.0))
            if off < S_LO or off > S_HI:
                continue
            ii = sidx(off)
            H[i, ii] = b["h"][kx]
            L[i, ii] = b["l"][kx]
            C[i, ii] = b["c"][kx]
        cc = 0
        for s in range(-1, S_LO - 1, -1):
            if np.isnan(C[i, sidx(s)]):
                break
            cc += 1
        pre_contig[i] = cc
        ok[i] = True
        if i % 5000 == 0:
            print("  row %d  %.1fs" % (i, time.time() - t0), flush=True)

    print("built price window: ok=%d  full-pre15=%d  (%.1fs)"
          % (ok.sum(), (pre_contig >= 15).sum(), time.time() - t0), flush=True)
    return rows, keys, H, L, C, entry0, stop, sgn, d0, anchor, pre_contig, ok


def walk(fav, adv, cls, valid, contract):
    """Vectorised first-touch walk.  fav/adv/cls are (n,L) in R; valid is (n,L) bool.
    Returns (r, reason_code, exit_bar).  reason 0=target 1=stop 2=mark 3=nopath."""
    nn, L = fav.shape
    r = np.full(nn, np.nan)
    reason = np.full(nn, 3, dtype=np.int8)
    ebar = np.full(nn, -1, dtype=np.int16)
    live = np.zeros(nn, dtype=bool)
    lastc = np.full(nn, np.nan)
    mfe = np.full(nn, -np.inf)
    slev = np.full(nn, STP)
    slev_next = np.full(nn, STP)
    for b in range(L):
        v = valid[:, b] & (reason == 3)
        if not v.any():
            continue
        live |= v
        f = fav[:, b]
        a = adv[:, b]
        if contract == "INC":
            hit_t = v & (f >= TGT - TOL)
            hit_s = v & (a <= STP + TOL)
            # tie -> stop
            st = hit_s
            tg = hit_t & ~hit_s
            r[st] = STP
            reason[st] = 1
            ebar[st] = b
            r[tg] = TGT
            reason[tg] = 0
            ebar[tg] = b
        elif contract == "STOPONLY":
            st = v & (a <= STP + TOL)
            r[st] = STP
            reason[st] = 1
            ebar[st] = b
        elif contract == "TRAIL025":
            st = v & (a <= slev_next + TOL)
            r[st] = slev_next[st]
            reason[st] = 1
            ebar[st] = b
        else:
            raise ValueError(contract)
        stillopen = v & (reason == 3)
        lastc[stillopen] = cls[stillopen, b]
        if contract == "TRAIL025":
            slev = slev_next.copy()
            m = np.where(stillopen, np.maximum(mfe, f), mfe)
            mfe = m
            # e_lib semantics: the trail ARMS only once running MFE >= trail_r
            newlev = np.where(mfe >= TRAIL, mfe - TRAIL, STP)
            slev_next = np.where(stillopen, np.maximum(slev, newlev), slev_next)
    mk = (reason == 3) & live & ~np.isnan(lastc)
    r[mk] = lastc[mk]
    reason[mk] = 2
    return r, reason, ebar


def main(out):
    rows, keys, H, L, C, entry0, stop, sgn, d0, anchor, pre_contig, ok = build()
    n = len(rows)
    res = {}
    t0 = time.time()
    for horizon in ("WALL", "MATCH"):
        for k in OFFS:
            ei = sidx(k - 1)
            ek = C[:, ei].astype(np.float64)
            dk = np.abs(ek - stop)
            good = ok & ~np.isnan(ek) & (dk > 0)
            if k < 0:
                good &= (pre_contig >= (15 + k + 1))   # need bar stamped D+k-1 .. D-1 present
            s_start = k
            s_end = 119 if horizon == "WALL" else k + 119
            s_end = min(s_end, S_HI)
            if s_end < s_start:
                continue
            cols = [sidx(s) for s in range(s_start, s_end + 1)]
            hh = H[:, cols].astype(np.float64)
            ll = L[:, cols].astype(np.float64)
            cc = C[:, cols].astype(np.float64)
            valid = ~np.isnan(cc) & good[:, None]
            for denom in ("SHIFTSTOP", "STRUCTSTOP"):
                dd = d0 if denom == "SHIFTSTOP" else dk
                dd = np.where(dd > 0, dd, np.nan)
                sg = sgn[:, None]
                e = ek[:, None]
                dv = dd[:, None]
                hi = sg * (hh - e) / dv
                lo = sg * (ll - e) / dv
                fav = np.where(hi >= lo, hi, lo)
                adv = np.where(hi >= lo, lo, hi)
                cls = sg * (cc - e) / dv
                fav = np.nan_to_num(fav, nan=-9e9)
                adv = np.nan_to_num(adv, nan=9e9)
                for contract in ("INC", "TRAIL025", "STOPONLY"):
                    rr, reason, ebar = walk(fav, adv, cls, valid, contract)
                    res["%s|%s|%s|k%+d|r" % (horizon, denom, contract, k)] = rr.astype(np.float32)
                    if horizon == "WALL" and denom == "STRUCTSTOP":
                        res["%s|%s|%s|k%+d|why" % (horizon, denom, contract, k)] = reason
            res["meta|%s|k%+d|dk" % (horizon, k)] = dk.astype(np.float32)
            res["meta|%s|k%+d|entry" % (horizon, k)] = ek.astype(np.float32)
            res["meta|%s|k%+d|good" % (horizon, k)] = good
            print("  %s k=%+d done %.1fs" % (horizon, k, time.time() - t0), flush=True)

    np.savez_compressed(
        out,
        entry0=entry0, stop=stop, sgn=sgn, d0=d0, anchor=anchor,
        pre_contig=pre_contig, ok=ok,
        **res)
    with open(out.replace(".npz", "_KEYS.json"), "w") as f:
        json.dump({"offs": OFFS, "keys": keys,
                   "symbol": [r["symbol"] for r in rows],
                   "side": [r.get("side") for r in rows],
                   "family": [r.get("origin_family") for r in rows],
                   "day": [r["decision_time_utc"][:10] for r in rows],
                   "hour": [int(r["decision_time_utc"][11:13]) for r in rows],
                   "gross_r": [r.get("gross_r") for r in rows],
                   "cost_r": [r.get("cost_r") for r in rows],
                   "bars_to_entry_touch": [r.get("bars_to_entry_touch") for r in rows],
                   "policy_target_r": [r.get("policy_target_r") for r in rows]}, f)
    print("WROTE %s  (%.1fs)" % (out, time.time() - t0), flush=True)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, "x5_FRAME_JAN.npz"))
