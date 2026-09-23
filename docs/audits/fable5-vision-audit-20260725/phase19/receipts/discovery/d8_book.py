"""d8_book — THE HORIZON SWEEP NOBODY RAN: what does the family book if it simply HOLDS?

Every economic number in this estate stops at the sealed 120-M1-bar wall, which is the
pending-order expiry, not a holding contract.  This prices the same emissions as a plain
timed hold at 15 min / 1 h / 4 h / 24 h, with no stop and no target, charged the h1
broker-true four-term toll (hour-aware spread + commission + slippage + swap for the hold),
against a matched PLACEBO-SIDE arm on identical rows, instants, geometry and toll.

Reported in bps (the honest unit for a magnitude question) and in R (the estate's unit).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pbg"))
sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
import d8_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402

H = D.HORIZONS


def blockstats(v, blk, boot=2000, seed=20260806):
    v = np.asarray(v, np.float64)
    ok = np.isfinite(v)
    v, blk = v[ok], np.asarray(blk)[ok]
    if v.size == 0:
        return dict(n=0)
    ud, inv = np.unique(blk, return_inverse=True)
    nb = ud.size
    bs = np.bincount(inv, weights=v, minlength=nb)
    bn = np.bincount(inv, minlength=nb).astype(np.float64)
    rng = np.random.default_rng(seed)
    dr = rng.integers(0, nb, size=(boot, nb))
    ms = bs[dr].sum(1) / np.maximum(bn[dr].sum(1), 1)
    return dict(n=int(v.size), blocks=int(nb), mean=float(v.mean()),
                se=float(ms.std(ddof=1)), lo=float(np.percentile(ms, 2.5)),
                hi=float(np.percentile(ms, 97.5)), p_le0=float((ms <= 0).mean()),
                blocks_pos=int((bs / np.maximum(bn, 1) > 0).sum()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "d8"))
    ap.add_argument("--months", default=",".join(D.MONTHS))
    ap.add_argument("--json", default=os.path.join(HERE, "D8_HORIZON_V1.json"))
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args()
    months = [m for m in a.months.split(",")
              if os.path.isfile(os.path.join(a.out, "D8_EMIT_%s.npz" % m))]
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    acc = defaultdict(list)
    for mm in months:
        e = np.load(os.path.join(a.out, "D8_EMIT_%s.npz" % mm))
        syms = [str(x) for x in e["syms"]]
        base = D.base_dt(mm)
        n = e["i"].size
        iso = [(base + dt.timedelta(minutes=int(x))).isoformat() for x in e["i"]]
        sym = np.array([syms[i] for i in e["sym"]])
        anchor = e["anchor"]
        L = e["long"]
        flip = rng.random(n) < 0.5           # placebo side, drawn once per row
        # toll in bps of the anchor, per horizon (swap depends on the hold)
        toll = {}
        for h in H:
            t = np.full(n, np.nan)
            for i in range(n):
                if not np.isfinite(anchor[i]) or anchor[i] <= 0:
                    continue
                tot, _ = cm.cost_px(sym[i], iso[i], float(anchor[i]), bool(L[i]), hold_min=h)
                t[i] = tot / anchor[i] * 1e4
            toll[h] = t
        for h in H:
            r = e["ret_%d" % h].astype(np.float64)
            d = e["d_bps"].astype(np.float64)
            ok = np.isfinite(r) & np.isfinite(toll[h]) & np.isfinite(d) & (d > 0)
            sgn = np.where(L, 1.0, -1.0)
            gross = sgn * r
            gross_pl = np.where(flip, 1.0, -1.0) * r
            acc[(h, "gross_bps")].append(gross[ok])
            acc[(h, "pl_gross_bps")].append(gross_pl[ok])
            acc[(h, "toll_bps")].append(toll[h][ok])
            acc[(h, "net_bps")].append((gross - toll[h])[ok])
            acc[(h, "pl_net_bps")].append((gross_pl - toll[h])[ok])
            acc[(h, "gross_r")].append((gross / d)[ok])
            acc[(h, "net_r")].append(((gross - toll[h]) / d)[ok])
            acc[(h, "pl_net_r")].append(((gross_pl - toll[h]) / d)[ok])
            acc[(h, "blk")].append(np.array([mm + ":" + str(x) for x in e["day"]])[ok])
            acc[(h, "sym")].append(sym[ok])
            acc[(h, "d_bps")].append(d[ok])
        print("book", mm, flush=True)

    R = {"months": months, "cells": {}}
    for h in H:
        blk = np.concatenate(acc[(h, "blk")])
        cell = {}
        for q in ("gross_bps", "pl_gross_bps", "toll_bps", "net_bps", "pl_net_bps",
                  "gross_r", "net_r", "pl_net_r"):
            cell[q] = blockstats(np.concatenate(acc[(h, q)]), blk, a.boot)
        g = np.concatenate(acc[(h, "gross_bps")])
        p = np.concatenate(acc[(h, "pl_gross_bps")])
        cell["signal_bps"] = blockstats(g - p, blk, a.boot)
        cell["hit_rate"] = float((g > 0).mean())
        cell["pl_hit_rate"] = float((p > 0).mean())
        cell["median_d_bps"] = float(np.median(np.concatenate(acc[(h, "d_bps")])))
        # per symbol
        sy = np.concatenate(acc[(h, "sym")])
        nb = np.concatenate(acc[(h, "net_bps")])
        gb = g
        tb = np.concatenate(acc[(h, "toll_bps")])
        per = {}
        for s in np.unique(sy):
            m = sy == s
            per[str(s)] = dict(n=int(m.sum()), gross_bps=float(gb[m].mean()),
                               toll_bps=float(tb[m].mean()), net_bps=float(nb[m].mean()),
                               edge_toll=float(gb[m].mean() / tb[m].mean()))
        cell["by_symbol"] = per
        R["cells"]["h%d" % h] = cell
        print("h%d gross %.4f toll %.4f net %.4f signal %.4f" % (
            h, cell["gross_bps"]["mean"], cell["toll_bps"]["mean"],
            cell["net_bps"]["mean"], cell["signal_bps"]["mean"]), flush=True)

    with open(a.json, "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", a.json)


if __name__ == "__main__":
    main()
