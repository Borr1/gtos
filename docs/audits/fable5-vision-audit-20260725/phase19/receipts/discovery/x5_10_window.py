#!/usr/bin/env python3
"""x5_10_window - the M1 price window substrate for the CONFIRMATION-TRADE-OFF lane.

Stores the raw M1 O/H/L/C for stamps D-15 .. D+180 around every January decision, plus
every meta array the ladder needs.  Everything downstream (x5_20..x5_60) loads this once
and never re-reads a CSV.

Bar-stamp convention (validated by w0-capture, x3 and x4): an M1 bar stamped T covers
[T, T+1min); its CLOSE happens at T+1min.  A decision at M15 boundary D is made on
information whose last knowable price is the close of the bar stamped D-1min.
The TRIGGER M15 bar is the 15 M1 bars stamped D-15 .. D-1.

Entry offset k (minutes relative to D):
    entry price = close of bar stamped D+k-1   (array index sidx(k-1))
    k=0   -> the shipped contract (entry == M15 close; == pool entry_price for at-market rows)
    k=-14 -> entry at the close of the FIRST minute of the trigger bar
    k=+5  -> the estate's L7 "delay 5" rung
Forward walk scores bars stamped D+k, D+k+1, ...

usage: python3 x5_10_window.py
"""
import bisect
import csv
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

S_LO, S_HI = -15, 180
NS = S_HI - S_LO + 1
OUT = os.path.join(D, "x5_WINDOW_JAN.npz")
OUTK = os.path.join(D, "x5_WINDOW_JAN_META.json")


def sidx(s):
    return s - S_LO


def load_bars(sym):
    p = os.path.join(BARS_ROOT, BARS_DIR, "%s_M1.csv" % sym)
    if not os.path.isfile(p):
        return None
    t, o, h, l, c = [], [], [], [], []
    with open(p) as f:
        rd = csv.reader(f)
        next(rd)
        for r in rd:
            t.append(r[0])
            o.append(float(r[1]))
            h.append(float(r[2]))
            l.append(float(r[3]))
            c.append(float(r[4]))
    return {"t": t, "o": np.array(o), "h": np.array(h), "l": np.array(l), "c": np.array(c)}


def main():
    t0 = time.time()
    rows = w0_ws.load()
    n = len(rows)
    print("pool rows %d (%.1fs)" % (n, time.time() - t0), flush=True)
    syms = sorted({r["symbol"] for r in rows})
    bars = {}
    for s in syms:
        b = load_bars(s)
        if b is not None:
            bars[s] = b
    print("bar files %d/%d (%.1fs)" % (len(bars), len(syms), time.time() - t0), flush=True)

    O = np.full((n, NS), np.nan, dtype=np.float32)
    H = np.full((n, NS), np.nan, dtype=np.float32)
    L = np.full((n, NS), np.nan, dtype=np.float32)
    C = np.full((n, NS), np.nan, dtype=np.float32)
    entry0 = np.zeros(n); stop = np.zeros(n); tp1 = np.full(n, np.nan)
    sgn = np.zeros(n); d0 = np.zeros(n); anchor = np.full(n, np.nan)
    pre_contig = np.zeros(n, dtype=np.int16)
    ok = np.zeros(n, dtype=bool)
    gross_r = np.full(n, np.nan); cost_r = np.full(n, np.nan); spread_r = np.full(n, np.nan)
    tgt_r = np.full(n, np.nan); bte = np.full(n, -1, dtype=np.int16)
    firstem = np.zeros(n, dtype=bool)
    hour = np.zeros(n, dtype=np.int16)
    symi = np.zeros(n, dtype=np.int16)
    sym_list = syms
    sym_ix = {s: i for i, s in enumerate(syms)}
    fams = sorted({(r.get("origin_family") or "?") for r in rows})
    fam_ix = {s: i for i, s in enumerate(fams)}
    fami = np.zeros(n, dtype=np.int16)
    days = sorted({r["decision_time_utc"][:10] for r in rows})
    day_ix = {s: i for i, s in enumerate(days)}
    dayi = np.zeros(n, dtype=np.int16)
    keys = []

    for i, r in enumerate(rows):
        keys.append([r["candidate_id"], r["decision_time_utc"]])
        symi[i] = sym_ix[r["symbol"]]
        fami[i] = fam_ix[r.get("origin_family") or "?"]
        dayi[i] = day_ix[r["decision_time_utc"][:10]]
        hour[i] = int(r["decision_time_utc"][11:13])
        gross_r[i] = r.get("gross_r", np.nan)
        cost_r[i] = r.get("cost_r", np.nan)
        spread_r[i] = r.get("spread_r") if r.get("spread_r") is not None else np.nan
        tgt_r[i] = r.get("policy_target_r", np.nan)
        b = r.get("bars_to_entry_touch")
        bte[i] = -1 if b is None else int(b)
        firstem[i] = bool(r.get("is_first_emission"))
        bb = bars.get(r["symbol"])
        if bb is None:
            continue
        dtt = datetime.fromisoformat(r["decision_time_utc"])
        want = (dtt - timedelta(minutes=1)).isoformat()
        j = bisect.bisect_left(bb["t"], want)
        if j >= len(bb["t"]) or bb["t"][j] != want:
            continue
        e = float(r["entry_price"]); sl = float(r["stop_loss"])
        d = abs(e - sl)
        if not (d > 0):
            continue
        sg = 1.0 if r["side"] == "LONG" else -1.0
        entry0[i] = e; stop[i] = sl; sgn[i] = sg; d0[i] = d
        tv = r.get("take_profit_1")
        tp1[i] = float(tv) if tv is not None else np.nan
        anchor[i] = sg * (float(bb["c"][j]) - e) / d
        lo = max(0, j - 20); hi = min(len(bb["t"]), j + 200)
        for kx in range(lo, hi):
            off = int(round((datetime.fromisoformat(bb["t"][kx]) - dtt).total_seconds() / 60.0))
            if off < S_LO or off > S_HI:
                continue
            ii = sidx(off)
            O[i, ii] = bb["o"][kx]; H[i, ii] = bb["h"][kx]
            L[i, ii] = bb["l"][kx]; C[i, ii] = bb["c"][kx]
        cc = 0
        for s in range(-1, S_LO - 1, -1):
            if np.isnan(C[i, sidx(s)]):
                break
            cc += 1
        pre_contig[i] = cc
        ok[i] = True
        if i % 5000 == 0:
            print("  row %d %.1fs" % (i, time.time() - t0), flush=True)

    # born state, from the no-look-ahead anchor
    born = np.full(n, 4, dtype=np.int8)     # 4 = unknown
    born[ok & (np.abs(anchor) < 1e-12)] = 0                       # at_limit
    born[ok & (anchor > 1e-12)] = 1                               # resting
    born[ok & (anchor < -1e-12) & (anchor > -1.0)] = 2            # marketable
    born[ok & (anchor <= -1.0)] = 3                               # past_stop
    print("born counts at_limit/resting/marketable/past_stop/unk:",
          [(born == q).sum() for q in range(5)], flush=True)
    print("ok=%d pre15=%d (%.1fs)" % (ok.sum(), (pre_contig >= 15).sum(), time.time() - t0),
          flush=True)

    np.savez_compressed(OUT, O=O, H=H, L=L, C=C, entry0=entry0, stop=stop, tp1=tp1,
                        sgn=sgn, d0=d0, anchor=anchor, pre_contig=pre_contig, ok=ok,
                        gross_r=gross_r, cost_r=cost_r, spread_r=spread_r, tgt_r=tgt_r,
                        bte=bte, firstem=firstem, hour=hour, symi=symi, fami=fami, dayi=dayi,
                        born=born)
    with open(OUTK, "w") as f:
        json.dump({"S_LO": S_LO, "S_HI": S_HI, "symbols": sym_list, "families": fams,
                   "days": days, "keys": keys,
                   "born_labels": ["at_limit", "resting", "marketable", "past_stop", "unknown"]}, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
