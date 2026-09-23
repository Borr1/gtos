#!/usr/bin/env python3
"""x5_20_ladder - the UNCONDITIONAL confirmation axis.

One rung = "act k minutes after the M15 boundary D".  k=-14 means the system acted after
seeing ONE minute of the trigger bar; k=0 is the shipped contract (the completed bar);
k=+15 means it waited a whole extra M15 bar.  Every rung is priced on THE SAME ROWS.

Emits x5_LADDER_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_LADDER_V1.json")


def main():
    t0 = time.time()
    w = X.W()
    print("n=%d core=%d" % (w.n, w.core.sum()), flush=True)
    days = w.dayi
    res = {"meta": {"n_rows": int(w.n), "n_core": int(w.core.sum()),
                    "rungs": X.RUNGS,
                    "born_counts_core": {w.born_labels[q]: int(((w.born == q) & w.core).sum())
                                         for q in range(5)}}}
    base = {}
    ladder = []
    for horizon in ("MATCH", "WALL"):
        for denom in ("STRUCTSTOP", "SHIFTSTOP"):
            contracts = ("INC", "TRAIL025", "STOPONLY") + (("FIXLEV",) if denom == "STRUCTSTOP" else ())
            for contract in contracts:
                for k in X.RUNGS:
                    o = X.rungs_walk(w, k, horizon=horizon, denom=denom, contract=contract)
                    g = o["good"]
                    r = o["r"]
                    rec = {"horizon": horizon, "denom": denom, "contract": contract, "k": k,
                           "n": int(g.sum()), "mean": float(np.nanmean(r[g])),
                           "total": float(np.nansum(r[g])),
                           "win": float((r[g] > 0).mean()),
                           "tgt_rate": float((o["reason"][g] == 0).mean()),
                           "stop_rate": float((o["reason"][g] == 1).mean()),
                           "mark_rate": float((o["reason"][g] == 2).mean()),
                           "mean_dk_over_d0": float(np.nanmean(o["dk"][g] / w.d0[g])),
                           "mean_exit_bar": float(np.nanmean(o["ebar"][g][o["ebar"][g] >= 0]))}
                    # net of the pool's own frozen cost, re-denominated into d_k
                    cst = w.cost_r * (w.d0 / np.where(o["dk"] > 0, o["dk"], np.nan))
                    net = r - cst
                    gg = g & ~np.isnan(net)
                    rec["net_mean"] = float(np.nanmean(net[gg]))
                    rec["net_total"] = float(np.nansum(net[gg]))
                    rec["mean_cost_r_k"] = float(np.nanmean(cst[gg]))
                    ladder.append(rec)
                    key = "%s|%s|%s" % (horizon, denom, contract)
                    if k == 0:
                        base[key] = r.copy()
                print("  %s %s %s done %.1fs" % (horizon, denom, contract, time.time() - t0),
                      flush=True)
    res["ladder"] = ladder

    # ---- paired bootstrap vs k=0 on the primary arm, plus per-born-state means
    prim = ("MATCH", "STRUCTSTOP", "INC")
    pk = "%s|%s|%s" % prim
    b0 = base[pk]
    boots = []
    born_tab = []
    for k in X.RUNGS:
        o = X.rungs_walk(w, k, horizon=prim[0], denom=prim[1], contract=prim[2])
        g = o["good"] & ~np.isnan(b0)
        bt = X.paired_boot(o["r"][g], b0[g], days[g], B=1000, seed=1013 + k)
        bt["k"] = k
        bt["n"] = int(g.sum())
        boots.append(bt)
        for q in range(4):
            m = g & (w.born == q)
            if m.sum() < 20:
                continue
            born_tab.append({"k": k, "born": w.born_labels[q], "n": int(m.sum()),
                             "mean": float(np.nanmean(o["r"][m])),
                             "delta_vs_k0": float(np.nanmean(o["r"][m] - b0[m]))})
        print("  boot k=%+d %.1fs" % (k, time.time() - t0), flush=True)
    res["paired_boot_vs_k0"] = boots
    res["by_born"] = born_tab
    with open(OUT, "w") as f:
        json.dump(res, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
