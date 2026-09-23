#!/usr/bin/env python3
"""x4 step 8 — the honest metric decomposition. Pool-R-per-opportunity rewards ANY refusal of a
negative-mean subset, so it cannot rank filters on its own. Report the REFUSED-set mean (what you
avoided) and the KEPT-set mean (what you are left holding) alongside it."""
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X
recs = X.load_joined(); O = X.outcomes(recs); n = len(recs)
honr = np.nan_to_num(O["honr"], nan=0.0); take = O["takeable"]; b1 = O["bar1"]
days = np.array([r["_day"] for r in recs]); dnum = np.array([int(d[-2:]) for d in days])
c0c = X.col(recs, "c0_close_fav_r"); geo = X.col(recs, "stop_dist_over_bar_range")
cost = np.array([X._num(r["cost_r"]) for r in recs])
out = {}
def dec(refuse, lab, pop=None):
    pop = np.ones(n, bool) if pop is None else pop
    R = refuse & pop; K = (~refuse) & pop
    v = np.where(K, honr, 0.0)[pop]
    m, lo, hi, p = X.day_block_boot(v, days[pop])
    mk, lok, hik, pk = X.day_block_boot(honr[K], days[K])
    if R.sum() > 20:
        mr, lor, hir, pr = X.day_block_boot(honr[R], days[R])
    else:
        lor = hir = float("nan")
    d = {"rule": lab, "n_pop": int(pop.sum()), "n_refused": int(R.sum()), "n_kept": int(K.sum()),
         "refused_share": round(float(R.sum()/pop.sum()), 4),
         "REFUSED_mean_R": round(float(honr[R].mean()), 5) if R.sum() else None,
         "refused_lo95": round(lor, 5), "refused_hi95": round(hir, 5),
         "KEPT_mean_R": round(float(honr[K].mean()), 5),
         "kept_lo95": round(lok, 5), "kept_hi95": round(hik, 5),
         "kept_delta_vs_pop": round(float(honr[K].mean() - honr[pop].mean()), 5),
         "pool_R_per_opportunity": round(float(v.mean()), 5),
         "pool_lo95": round(lo, 5), "pool_hi95": round(hi, 5),
         "kept_odd": round(float(honr[K & (dnum%2==1)].mean()), 5),
         "kept_even": round(float(honr[K & (dnum%2==0)].mean()), 5),
         "refused_odd": round(float(honr[R & (dnum%2==1)].mean()), 5) if (R & (dnum%2==1)).sum() else None,
         "refused_even": round(float(honr[R & (dnum%2==0)].mean()), 5) if (R & (dnum%2==0)).sum() else None,
         "refused_h1": round(float(honr[R & (dnum<=15)].mean()), 5) if (R & (dnum<=15)).sum() else None,
         "refused_h2": round(float(honr[R & (dnum>15)].mean()), 5) if (R & (dnum>15)).sum() else None,
         "refused_median_cost": round(float(np.nanmedian(cost[R])), 4) if R.sum() else None,
         "kept_median_cost": round(float(np.nanmedian(cost[K])), 4)}
    return d
C = np.isfinite(c0c) & (c0c <= -0.15); G = np.isfinite(geo) & (geo <= 0.60)
for lab, ref, pop in (("BASE_none", np.zeros(n, bool), None),
                      ("C_c0_le_-0.15", C, None),
                      ("C_c0_le_-0.05", np.isfinite(c0c) & (c0c <= -0.05), None),
                      ("G_geo_le_0.60", G, None),
                      ("G_geo_le_0.80", np.isfinite(geo) & (geo <= 0.80), None),
                      ("CG_union", C | G, None),
                      ("G_given_C_clean", G, ~C),
                      ("C_given_G_clean", C, ~G),
                      ("C_takeable", C, take),
                      ("G_takeable", G, take),
                      ("C_within_bar1", C, take & b1)):
    out[lab] = dec(ref, lab, pop)
    d = out[lab]
    f = lambda v: (float("nan") if v is None else v)
    print("%-18s pop=%5d ref=%5d (%.3f) REFUSED=%8.5f [%8.5f,%8.5f] KEPT=%8.5f (d%+.5f) pool=%8.5f  refOdd=%8.5f refEven=%8.5f cost r/k %.3f/%.3f"
          % (lab, d["n_pop"], d["n_refused"], d["refused_share"], f(d["REFUSED_mean_R"]),
             f(d["refused_lo95"]), f(d["refused_hi95"]), d["KEPT_mean_R"], d["kept_delta_vs_pop"],
             d["pool_R_per_opportunity"], f(d["refused_odd"]), f(d["refused_even"]),
             f(d["refused_median_cost"]), d["kept_median_cost"]), flush=True)
# monotone joint surface: c0 quintile x geo quintile
cq = np.digitize(c0c, np.nanquantile(c0c, [.2,.4,.6,.8]))
gq = np.digitize(geo, np.nanquantile(geo, [.2,.4,.6,.8]))
surf = {}
print("\nJOINT SURFACE  rows=c0 quintile (0=most adverse)  cols=geo quintile (0=tightest stop)")
print("      " + "".join("%12d" % g for g in range(5)))
for c in range(5):
    line = "c0=%d " % c
    for g in range(5):
        m = np.isfinite(c0c) & np.isfinite(geo) & (cq == c) & (gq == g)
        if m.sum() < 30:
            line += "%12s" % "-"; continue
        surf["%d_%d" % (c, g)] = {"n": int(m.sum()), "honr": round(float(honr[m].mean()), 5)}
        line += "%8.4f/%3d" % (honr[m].mean(), m.sum())
    print(line, flush=True)
out["JOINT_SURFACE"] = surf
with open(os.path.join(D, "X4_FINAL_V1.json"), "w") as f:
    json.dump(out, f, indent=1)
print("wrote X4_FINAL_V1.json")
