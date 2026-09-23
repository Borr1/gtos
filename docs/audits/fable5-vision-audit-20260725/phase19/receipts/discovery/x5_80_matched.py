#!/usr/bin/env python3
"""x5_80_matched - THE TEST THAT SEPARATES 'CONFIRMATION' FROM 'CLOCK'.

Every conditional rung enters at a different minute from the incumbent, so its advantage
could be nothing but the clock.  The control is an ENTRY-TIME-MATCHED counterfactual: for
each rung, price the whole core population at the SAME distribution of entry stamps and
compare.

    matched_control(rung) = sum_s  w_s * mean_core[ r(entry at stamp s) ]
    where w_s is the rung's own share of taken rows entering at stamp s.

    CONFIRMATION_VALUE = mean_taken - matched_control

A positive CONFIRMATION_VALUE is the part of the rung that a clock change cannot buy.
Also emits the per-day and per-symbol positivity of the honest delay lever.
Emits x5_MATCHED_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_MATCHED_V1.json")
STAMPS = list(range(-14, 30))
NS = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 18, 21, 25, 30]


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    n = w.n
    # unconditional mean at every entry stamp (k = stamp+1 in the rung convention:
    # entry price = close of bar stamped k-1, so a rung entering at the close of stamp s
    # is rung k = s+1)
    uncond = {}
    for s in STAMPS:
        k = s + 1
        if k > 60:
            continue
        o = X.rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
        g = core & o["good"] & ~np.isnan(o["r"])
        uncond[s] = {"k": k, "n": int(g.sum()), "mean": float(o["r"][g].mean())}
    print("uncond stamps done %.1fs" % (time.time() - t0), flush=True)

    st = np.array(list(range(-15, 30)), dtype=np.int32)
    cols = [X.sidx(x) for x in st]
    Cw = w.C[:, cols].astype(np.float64)
    Hw = w.H[:, cols].astype(np.float64); Lw = w.L[:, cols].astype(np.float64)
    Otrig = w.O[:, X.sidx(-15)].astype(np.float64)
    e0 = w.entry_at(0)
    valid = ~np.isnan(Cw) & core[:, None] & ~np.isnan(Otrig)[:, None]
    post_only = (st >= 0)[None, :] & valid
    prog = w.sgn[:, None] * (Cw - Otrig[:, None]) / w.d0[:, None]
    progp = w.sgn[:, None] * (Cw - e0[:, None]) / w.d0[:, None]
    reach = np.maximum(w.sgn[:, None] * (Hw - w.entry0[:, None]),
                       w.sgn[:, None] * (Lw - w.entry0[:, None])) / w.d0[:, None]
    wrong_open = (w.sgn * (Otrig - w.entry0) / w.d0) < 0.0
    lvlx = (reach >= 0.0) & wrong_open[:, None]

    def first_run(cond, vmask, N):
        run = np.zeros(n, dtype=np.int32); out = np.full(n, -1, dtype=np.int32)
        for j in range(cond.shape[1]):
            c = cond[:, j] & vmask[:, j]
            run = np.where(c, run + 1, 0)
            hit = (out < 0) & (run >= N)
            out[hit] = j
        return out

    tab = []
    FAM = [("DIR", prog, valid, [0.0, 0.25]), ("ANTI", -prog, valid, [0.0, 0.25]),
           ("POST", progp, post_only, [0.0, 0.25]), ("POSTANTI", -progp, post_only, [0.0, 0.25]),
           ("LEVELXM", None, valid, [0.0])]
    for cname, arr, vmask, ths in FAM:
        for th in ths:
            cond = (arr >= th) if arr is not None else lvlx
            for N in NS:
                jj = first_run(cond, vmask, N)
                surv = jj >= 0
                jc = np.clip(jj, 0, len(st) - 1)
                s_entry = st[jc]
                ent = np.where(surv, Cw[np.arange(n), jc], np.nan)
                o = X.rungs_walk(w, 0, horizon="MATCH", denom="STRUCTSTOP", contract="INC",
                                 entry_px=ent, start_stamp=(s_entry + 1).astype(np.int32))
                g = o["good"] & surv & core & ~np.isnan(o["r"])
                if g.sum() < 200:
                    continue
                ss = s_entry[g]
                ctrl = 0.0; tot = 0
                for s in np.unique(ss):
                    if int(s) not in uncond:
                        continue
                    cnt = int((ss == s).sum())
                    ctrl += cnt * uncond[int(s)]["mean"]
                    tot += cnt
                ctrl = ctrl / max(1, tot)
                mt = float(o["r"][g].mean())
                tab.append({"cond": cname, "theta": th, "N": N, "n_taken": int(g.sum()),
                            "mean_taken": mt, "matched_control": ctrl,
                            "CONFIRMATION_VALUE": mt - ctrl,
                            "median_entry_stamp": float(np.median(ss)),
                            "coverage_of_stamps": tot / max(1, int(g.sum()))})
            print("  %s th=%.2f %.1fs" % (cname, th, time.time() - t0), flush=True)

    # honest delay lever robustness: k=+5 vs k=0, at-market cell, per day and per symbol
    atm = core & (w.born == 0)
    a = X.rungs_walk(w, 5, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
    b = X.rungs_walk(w, 0, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
    g = atm & a["good"] & b["good"] & ~np.isnan(a["r"]) & ~np.isnan(b["r"])
    dlt = a["r"] - b["r"]
    days = np.unique(w.dayi[g]); syms = np.unique(w.symi[g])
    dpos = sum(1 for d in days if dlt[g & (w.dayi == d)].mean() > 0)
    spos = sum(1 for s in syms if dlt[g & (w.symi == s)].mean() > 0)
    bt = X.dayblock_boot(dlt[g], w.dayi[g], B=2000, seed=99)
    out = {"uncond_by_stamp": uncond, "matched": tab,
           "delay5_atmkt": {"n": int(g.sum()), "delta": float(dlt[g].mean()),
                            "boot": bt, "days_positive": dpos, "days": len(days),
                            "symbols_positive": spos, "symbols": len(syms),
                            "k0_mean": float(b["r"][g].mean()),
                            "k5_mean": float(a["r"][g].mean())}}
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
