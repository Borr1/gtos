#!/usr/bin/env python3
"""x5_50_cost - DOES EARLINESS GET A BETTER PRICE, AND WHAT DOES IT DO TO COST?

Measured in bps of price as well as R, because the two disagree in SIGN on this pool: the
mean R improvement at k=-14 is NEGATIVE while the mean bps improvement is POSITIVE (a fat
left tail of small-risk-distance rows).

Cost accounting.  The pool's frozen cost `cost_r` is denominated in d0.  Moving the entry
does not change the cost in PRICE, it changes the denominator:

        cost_price = cost_r * d0            cost_R(k) = cost_price / d_k

so a rung that enters closer to the structural stop pays the SAME spread over a SMALLER
risk unit and is therefore MORE expensive in R -- fixed-fractional sizing scales the
position up by exactly d0/d_k.  That interaction is the whole of deliverable 4.

Winsorised and median statistics are reported alongside means because d_k/d0 has a heavy
right tail (born_resting/past_stop rows sit many R from their own stop).
Emits x5_COST_V1.json.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import x5_lib as X  # noqa: E402

OUT = os.path.join(D, "x5_COST_V1.json")


def q(v, p):
    return float(np.nanpercentile(v, p))


def main():
    t0 = time.time()
    w = X.W()
    core = w.core
    e0 = w.entry_at(0)
    tab = []
    for k in X.RUNGS:
        ek = w.entry_at(k)
        o = X.rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
        g = core & o["good"] & ~np.isnan(ek) & ~np.isnan(o["r"])
        dk = o["dk"]
        # sane-geometry subset: the rung's risk distance stays within 4x of the original
        sane = g & (dk / w.d0 > 0.25) & (dk / w.d0 < 4.0)
        imp_bps = w.sgn * (e0 - ek) / e0 * 1e4
        imp_R = w.sgn * (e0 - ek) / w.d0
        cost_price = w.cost_r * w.d0
        cost_k = cost_price / np.where(dk > 0, dk, np.nan)
        spread_price = w.spread_r * w.d0
        spread_k = spread_price / np.where(dk > 0, dk, np.nan)
        net = o["r"] - cost_k
        rec = {"k": k, "n": int(g.sum()), "n_sane": int(sane.sum()),
               "imp_bps_mean": float(imp_bps[g].mean()), "imp_bps_med": q(imp_bps[g], 50),
               "imp_bps_p25": q(imp_bps[g], 25), "imp_bps_p75": q(imp_bps[g], 75),
               "imp_R_mean": float(imp_R[g].mean()), "imp_R_med": q(imp_R[g], 50),
               "share_price_better": float((imp_bps[g] > 0).mean()),
               "dk_over_d0_mean": float((dk / w.d0)[g].mean()),
               "dk_over_d0_med": q((dk / w.d0)[g], 50),
               "cost_r0_mean": float(w.cost_r[g].mean()),
               "cost_rk_mean": float(np.nanmean(cost_k[g])),
               "cost_rk_med": q(cost_k[g], 50),
               "cost_rk_mean_sane": float(np.nanmean(cost_k[sane])),
               "spread_rk_med": q(spread_k[g], 50),
               "gross_mean": float(o["r"][g].mean()),
               "gross_mean_sane": float(o["r"][sane].mean()),
               "net_mean_sane": float(np.nanmean(net[sane])),
               "net_med": q(net[g], 50),
               "net_total_sane": float(np.nansum(net[sane]))}
        # bps of the ORIGINAL risk distance, and of price, for the cost itself
        rec["cost_bps_of_price_med"] = q((cost_price / e0 * 1e4)[g], 50)
        rec["spread_bps_of_price_med"] = q((spread_price / e0 * 1e4)[g], 50)
        tab.append(rec)
        if k % 5 == 0:
            print("  k=%+d %.1fs" % (k, time.time() - t0), flush=True)
    out = {"meta": {"n_core": int(core.sum())}, "cost": tab}

    # by symbol at three rungs, to see whether the price gain is instrument-wide
    per_sym = []
    for k in (-14, -5, 0, 5, 15, 60):
        ek = w.entry_at(k)
        imp_bps = w.sgn * (e0 - ek) / e0 * 1e4
        o = X.rungs_walk(w, k, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
        for si, s in enumerate(w.symbols):
            m = core & (w.symi == si) & ~np.isnan(imp_bps) & o["good"] & ~np.isnan(o["r"])
            if m.sum() < 50:
                continue
            per_sym.append({"k": k, "symbol": s, "n": int(m.sum()),
                            "imp_bps_med": q(imp_bps[m], 50),
                            "share_better": float((imp_bps[m] > 0).mean()),
                            "shiftstop_mean": float(o["r"][m].mean())})
    out["by_symbol"] = per_sym

    # by born state at every rung (SHIFTSTOP, the geometry-free instrument)
    per_born = []
    for k in X.RUNGS:
        o = X.rungs_walk(w, k, horizon="MATCH", denom="SHIFTSTOP", contract="INC")
        os_ = X.rungs_walk(w, k, horizon="MATCH", denom="STRUCTSTOP", contract="INC")
        for qq in range(4):
            m = core & (w.born == qq) & o["good"] & ~np.isnan(o["r"])
            if m.sum() < 20:
                continue
            per_born.append({"k": k, "born": w.born_labels[qq], "n": int(m.sum()),
                             "shiftstop_mean": float(o["r"][m].mean()),
                             "structstop_mean": float(np.nanmean(os_["r"][m]))})
    out["by_born"] = per_born
    with open(OUT, "w") as f:
        json.dump(out, f)
    print("WROTE %s (%.1fs)" % (OUT, time.time() - t0), flush=True)


if __name__ == "__main__":
    main()
