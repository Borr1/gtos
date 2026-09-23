"""d8_kill — adversarial interrogation of the ONE positive cell d8 found.

`k=6 distinct families firing on the same symbol at the same instant, held 4 h` books
+1.578 bps net at p 0.0015 with train +0.830 -> test +6.671.  Three months this week produced
three headline results with exactly that shape and all three were artifacts.  This script
tries to kill it, on: concentration (symbols / days / months), executability (POI limit rows
the live engine cannot place), and the k>=5 aggregate.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter, defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "pbg"))
sys.path.insert(0, "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801")
import d8_lib as D  # noqa: E402
import pbg_econ as E  # noqa: E402

AT_MARKET = set(D.AT_MARKET)
TRAIN = ("202510", "202511", "202512", "202601")
TEST = ("202602", "202603", "202604", "202605")


def bs(v, blk, boot=4000, seed=1):
    v = np.asarray(v, np.float64); blk = np.asarray(blk)
    ok = np.isfinite(v); v, blk = v[ok], blk[ok]
    if v.size == 0:
        return dict(n=0)
    ud, inv = np.unique(blk, return_inverse=True); nb = ud.size
    s = np.bincount(inv, weights=v, minlength=nb); c = np.bincount(inv, minlength=nb).astype(float)
    r = np.random.default_rng(seed); dr = r.integers(0, nb, size=(boot, nb))
    ms = s[dr].sum(1) / np.maximum(c[dr].sum(1), 1)
    return dict(n=int(v.size), blocks=int(nb), mean=float(v.mean()),
                lo=float(np.percentile(ms, 2.5)), hi=float(np.percentile(ms, 97.5)),
                p_le0=float((ms <= 0).mean()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(HERE, "d8"))
    ap.add_argument("--json", default=os.path.join(HERE, "D8_KILL_V1.json"))
    a = ap.parse_args()
    cm = E.CostModel()
    rng = np.random.default_rng(20260806)

    rows = []
    for mm in D.MONTHS:
        p = os.path.join(a.out, "D8_EMIT_%s.npz" % mm)
        if not os.path.isfile(p):
            continue
        e = np.load(p)
        syms = [str(x) for x in e["syms"]]; fams = [str(x) for x in e["fams"]]
        base = D.base_dt(mm)
        n = e["i"].size
        L = e["long"]; anc = e["anchor"]
        nf = e["conc_nf"]
        keep = np.nonzero((nf >= 4) & np.isfinite(anc) & (anc > 0)
                          & np.isfinite(e["ret_240"]))[0]
        for i in keep:
            s = syms[e["sym"][i]]
            iso = (base + dt.timedelta(minutes=int(e["i"][i]))).isoformat()
            tot, _ = cm.cost_px(s, iso, float(anc[i]), bool(L[i]), hold_min=240)
            g = (1.0 if L[i] else -1.0) * float(e["ret_240"][i])
            rows.append(dict(mm=mm, day=str(e["day"][i]), sym=s, fam=fams[e["fam"][i]],
                             k=int(nf[i]), g=g, t=tot / float(anc[i]) * 1e4,
                             hour=int(e["hour"][i]),
                             at_market=fams[e["fam"][i]] in AT_MARKET,
                             pl=(1.0 if rng.random() < 0.5 else -1.0) * float(e["ret_240"][i])))
        print("load", mm, len(rows), flush=True)

    R = {"n_rows_k_ge_4": len(rows), "cells": {}}
    for k in (4, 5, 6, 7):
        sel = [r for r in rows if r["k"] == k]
        if not sel:
            continue
        g = np.array([r["g"] for r in sel]); t = np.array([r["t"] for r in sel])
        blk = np.array([r["mm"] + ":" + r["day"] for r in sel])
        sy = Counter(r["sym"] for r in sel); mo = Counter(r["mm"] for r in sel)
        fa = Counter(r["fam"] for r in sel); dy = set(blk)
        am = np.array([r["at_market"] for r in sel])
        cell = dict(n=len(sel), net=bs(g - t, blk), gross=bs(g, blk),
                    toll=float(t.mean()),
                    distinct_days=len(dy), distinct_symbols=len(sy),
                    top_symbols=sy.most_common(6), months=dict(mo),
                    families=fa.most_common(10),
                    at_market_share=float(am.mean()))
        if am.sum() >= 20:
            cell["at_market_only"] = dict(n=int(am.sum()),
                                          net=bs((g - t)[am], blk[am]),
                                          gross=bs(g[am], blk[am]))
        if (~am).sum() >= 20:
            cell["poi_only"] = dict(n=int((~am).sum()), net=bs((g - t)[~am], blk[~am]))
        # leave-one-symbol-out on net
        loo = {}
        for s in [x for x, _ in sy.most_common(6)]:
            m = np.array([r["sym"] != s for r in sel])
            if m.sum() > 30:
                loo[s] = float((g - t)[m].mean())
        cell["leave_one_symbol_out_net"] = loo
        # per month net
        cell["per_month_net"] = {m: float((g - t)[[r["mm"] == m for r in sel]].mean())
                                 for m in sorted(mo)}
        R["cells"]["k%d" % k] = cell
        print("k=%d n=%d net %.4f days %d syms %d atmkt %.3f" % (
            k, len(sel), cell["net"]["mean"], len(dy), len(sy), cell["at_market_share"]),
            flush=True)

    # k >= 5 aggregate, and k >= 4
    for lo in (4, 5):
        sel = [r for r in rows if r["k"] >= lo]
        g = np.array([r["g"] for r in sel]); t = np.array([r["t"] for r in sel])
        blk = np.array([r["mm"] + ":" + r["day"] for r in sel])
        am = np.array([r["at_market"] for r in sel])
        R["cells"]["k_ge_%d" % lo] = dict(
            n=len(sel), net=bs(g - t, blk), gross=bs(g, blk), toll=float(t.mean()),
            at_market_share=float(am.mean()),
            at_market_only_net=(bs((g - t)[am], blk[am]) if am.sum() > 30 else None))
        print("k>=%d n=%d net %.4f" % (lo, len(sel), R["cells"]["k_ge_%d" % lo]["net"]["mean"]),
              flush=True)

    with open(a.json, "w") as fh:
        json.dump(R, fh, indent=1, default=float)
    print("wrote", a.json)


if __name__ == "__main__":
    main()
