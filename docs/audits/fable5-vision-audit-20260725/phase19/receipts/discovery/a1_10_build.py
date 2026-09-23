#!/usr/bin/env python3
"""a1 step 10 - the joint-scorer substrate: an M1 window around every AT-MARKET candidate.

One npz per month.  Stamps D-15 .. D+125 (141 slots) of true-UTC M1 O/H/L/C, where D is
the decision instant.  Bar-stamp convention (validated by w0-capture, x3, x4, x5):
    a bar stamped T covers [T, T+1min) and its CLOSE happens at T+1min.
Therefore:
    * the TRIGGER M15 bar interior is stamps D-15 .. D-1
    * the decision-instant price is the CLOSE of stamp D-1
    * `c0` (x4's confirm minute) is the CLOSE of stamp D, knowable at D+1min
    * a market entry taken at D+k minutes fills at the CLOSE of stamp D+k-1

Row source: h5_SUBSTRATE_5M.jsonl.gz - the e-stack AT-MARKET (live-expressible) cohort,
69,480 rows over 2026-01..05.  Cost: h1's four-term broker-true toll where it exists
(Jan/Feb/Mar), h5's hour-true three-term + swap elsewhere.

usage: python3 a1_10_build.py <YYYYMM> [more...]
"""
from __future__ import annotations
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
BARS = ("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
        "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars")
S_LO, S_HI = -15, 125
NS = S_HI - S_LO + 1

META_KEYS = ("cid", "dt", "symbol", "side", "family", "session", "day", "month",
             "hour", "utc_hour", "ny_hour", "dow", "entry_price", "risk_distance",
             "rdp", "cost_frozen", "cost_true", "cost_true_hour", "real_comm_r",
             "real_slip_r", "real_spread_r_hour", "swap_r", "spread_bps_hour",
             "efp", "prob", "rv60_bps", "rv_rel", "rdp_rel", "n_bars",
             "K0_STOPONLY", "K5_STOPONLY", "K0_TRAIL025", "K5_TRAIL025")


def load_bars(mm, sym):
    p = os.path.join(BARS, "bridge_ftmo_m1_%s" % mm, "%s_M1.csv" % sym)
    if not os.path.isfile(p):
        return None
    t, o, h, l, c = [], [], [], [], []
    with open(p, newline="") as f:
        rd = csv.reader(f)
        hdr = next(rd)
        ix = {k: hdr.index(k) for k in ("time", "open", "high", "low", "close")}
        for r in rd:
            t.append(r[ix["time"]])
            o.append(float(r[ix["open"]]))
            h.append(float(r[ix["high"]]))
            l.append(float(r[ix["low"]]))
            c.append(float(r[ix["close"]]))
    order = sorted(range(len(t)), key=lambda i: t[i])
    return {"t": [t[i] for i in order],
            "o": np.array([o[i] for i in order], dtype=np.float64),
            "h": np.array([h[i] for i in order], dtype=np.float64),
            "l": np.array([l[i] for i in order], dtype=np.float64),
            "c": np.array([c[i] for i in order], dtype=np.float64)}


def prevmonth(mm):
    y, m = int(mm[:4]), int(mm[4:])
    return "%04d%02d" % (y - (m == 1), 12 if m == 1 else m - 1)


def nextmonth(mm):
    y, m = int(mm[:4]), int(mm[4:])
    return "%04d%02d" % (y + (m == 12), 1 if m == 12 else m + 1)


def load_bars_span(mm, sym):
    """month +- 1 so a decision near a month edge still has a full window."""
    parts = [load_bars(x, sym) for x in (prevmonth(mm), mm, nextmonth(mm))]
    parts = [p for p in parts if p is not None]
    if not parts:
        return None
    t = []
    o = []
    h = []
    l = []
    c = []
    for p in parts:
        t.extend(p["t"])
        o.append(p["o"])
        h.append(p["h"])
        l.append(p["l"])
        c.append(p["c"])
    order = sorted(range(len(t)), key=lambda i: t[i])
    o = np.concatenate(o)[order]
    h = np.concatenate(h)[order]
    l = np.concatenate(l)[order]
    c = np.concatenate(c)[order]
    return {"t": [t[i] for i in order], "o": o, "h": h, "l": l, "c": c}


def main(months):
    h1 = {}
    for ln in gzip.open(os.path.join(D, "h1_COST_ROWS_V1.jsonl.gz"), "rt"):
        r = json.loads(ln)
        h1[(r["cid"], r["dt"])] = r
    print("h1 cost rows %d" % len(h1), flush=True)

    bymonth = {}
    for ln in gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "rt"):
        r = json.loads(ln)
        bymonth.setdefault(r["month"], []).append(r)
    print("h5 months %s" % sorted((k, len(v)) for k, v in bymonth.items()), flush=True)

    for mm in months:
        t0 = time.time()
        key = "%s-%s" % (mm[:4], mm[4:])
        rows = bymonth[key]
        syms = sorted({r["symbol"] for r in rows})
        cache = {}
        for s in syms:
            b = load_bars_span(mm, s)
            if b is not None:
                cache[s] = b
        n = len(rows)
        O = np.full((n, NS), np.nan, dtype=np.float64)
        H = np.full((n, NS), np.nan, dtype=np.float64)
        L = np.full((n, NS), np.nan, dtype=np.float64)
        C = np.full((n, NS), np.nan, dtype=np.float64)
        anchor_px = np.full(n, np.nan, dtype=np.float64)
        meta = {k: [] for k in META_KEYS}
        meta["cost_h1_r"] = []
        meta["cost_h1_noswap_r"] = []
        meta["broker_hour"] = []
        meta["instrument_class"] = []
        meta["has_h1"] = []
        keep = np.zeros(n, dtype=bool)
        nofile = 0
        for i, r in enumerate(rows):
            b = cache.get(r["symbol"])
            if b is None:
                nofile += 1
                continue
            dt = r["dt"]
            d0 = datetime.fromisoformat(dt)
            lo_iso = (d0 + timedelta(minutes=S_LO)).isoformat()
            hi_iso = (d0 + timedelta(minutes=S_HI)).isoformat()
            j0 = bisect.bisect_left(b["t"], lo_iso)
            j1 = bisect.bisect_right(b["t"], hi_iso)
            if j1 <= j0:
                continue
            # the decision-instant price = close of the LAST available bar strictly
            # before D, however far back that is (e_build_atmkt.py's `anchor`)
            ja = bisect.bisect_left(b["t"], dt) - 1
            if ja >= 0:
                anchor_px[i] = b["c"][ja]
            for j in range(j0, j1):
                dtb = datetime.fromisoformat(b["t"][j])
                s = int(round((dtb - d0).total_seconds() / 60.0))
                if s < S_LO or s > S_HI:
                    continue
                k = s - S_LO
                O[i, k] = b["o"][j]
                H[i, k] = b["h"][j]
                L[i, k] = b["l"][j]
                C[i, k] = b["c"][j]
            keep[i] = True
            for kk in META_KEYS:
                meta[kk].append(r.get(kk))
            hh = h1.get((r["cid"], dt))
            meta["cost_h1_r"].append(hh["total_r"] if hh else None)
            meta["cost_h1_noswap_r"].append(hh["total_r_noswap"] if hh else None)
            meta["broker_hour"].append(hh["broker_hour"] if hh else None)
            meta["instrument_class"].append(hh["instrument_class"] if hh else None)
            meta["has_h1"].append(1 if hh else 0)

        idx = np.where(keep)[0]
        O, H, L, C = O[idx], H[idx], L[idx], C[idx]
        anchor_px = anchor_px[idx]
        # forward-fill the close so an absent minute still has a quotable price.
        # seed slot 0 with the true pre-window anchor so a candidate whose first
        # stamps are all gaps NEVER inherits a price from the FUTURE.
        Cf = C.copy()
        m0 = np.isnan(Cf[:, 0])
        Cf[m0, 0] = anchor_px[m0]
        for k in range(1, NS):
            m = np.isnan(Cf[:, k])
            Cf[m, k] = Cf[m, k - 1]

        out = os.path.join(D, "a1_WIN_%s.npz" % mm)
        np.savez_compressed(out, O=O, H=H, L=L, C=C, Cf=Cf, ANCHOR=anchor_px,
                            S_LO=np.array([S_LO]), S_HI=np.array([S_HI]))
        with open(os.path.join(D, "a1_WIN_%s_META.json" % mm), "w") as f:
            json.dump({"month": key, "n_h5": n, "n_written": int(len(idx)),
                       "no_bar_file": nofile, "S_LO": S_LO, "S_HI": S_HI,
                       "meta": meta}, f)
        print("%s  h5=%d written=%d nofile=%d  %.1fs  %s"
              % (mm, n, len(idx), nofile, time.time() - t0, out), flush=True)


if __name__ == "__main__":
    main(sys.argv[1:] or ["202601", "202602", "202603", "202604", "202605"])
