#!/usr/bin/env python3
"""x4 step 5 — RE-ANCHOR. The owner's question, answered directly.

If the entry LEVEL is stale by the time the system can act, the repair is not only "refuse";
it is "keep the signal, keep the risk distance, and enter where the market actually IS k
minutes later". That is a market order at T+k with stop re-anchored to the same distance.

Arithmetic on the existing R paths (no new data):
    fav(i) = s*(high_i - e)/d     (w0 convention)
    re-anchor to price p_k, same risk distance d  ->  shift = s*(p_k - e)/d
    fav'(i) = fav(i) - shift,  adv'(i) = adv(i) - shift,  cls'(i) = cls(i) - shift
p_k is the CLOSE of the minute that ends at T+k, so k=1 uses the minute [T, T+1m) that the
sidecar omits (from x4's own M1 build) and k>=2 uses path bar k-1's close.

VARIANT A  keep risk distance d      (stop level moves with the entry)   <- primary
VARIANT B  keep the original STOP LEVEL (risk distance becomes d*(1+shift)) and renormalise R
"""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X
import w0_ws

recs = X.load_joined()
O = X.outcomes(recs)
idx = {w0_ws.key(r): i for i, r in enumerate(recs)}
n = len(recs)
honr = np.nan_to_num(O["honr"], nan=0.0)
days = np.array([r["_day"] for r in recs])
sym = np.array([r["symbol"] for r in recs])
fam = np.array([str(r.get("origin_family")) for r in recs])
dnum = np.array([int(d[-2:]) for d in days])
take = O["takeable"]
c0c = X.col(recs, "c0_close_fav_r")
geo = X.col(recs, "stop_dist_over_bar_range")

FAV = [None] * n; ADV = [None] * n; CLS = [None] * n
for rp in w0_ws.iter_rpaths():
    i = idx.get(w0_ws.key(rp))
    if i is None:
        continue
    FAV[i] = np.asarray(rp["fav"], float); ADV[i] = np.asarray(rp["adv"], float)
    CLS[i] = np.asarray(rp["cls"], float)
print("paths loaded", sum(1 for x in FAV if x is not None), flush=True)


def walk_shift(i, shift, start, target=2.0, stop=-1.0, scale=1.0):
    """First-touch walk on the re-anchored path. Market entry => always filled.
    Conservative same-bar tie to the stop, identical to w0_ws.walk."""
    fav = FAV[i]; adv = ADV[i]; cls = CLS[i]
    if fav is None or start >= len(fav):
        return None, "no_path"
    for j in range(start, len(fav)):
        a = (adv[j] - shift) / scale
        f = (fav[j] - shift) / scale
        if a <= stop + 1e-12:
            return stop, "stop"
        if f >= target - 1e-12:
            return target, "target"
    return float((cls[len(fav) - 1] - shift) / scale), "path_end"


res = {"n": n}
DELAYS = [0, 1, 2, 3, 5, 10, 15, 30]
res["reanchor"] = {}
store = {}
for k in DELAYS:
    r_a = np.full(n, np.nan); r_b = np.full(n, np.nan); reason = np.array([""] * n, dtype=object)
    for i in range(n):
        if FAV[i] is None:
            continue
        if k == 0:
            shift = 0.0; start = 0
        elif k == 1:
            if not np.isfinite(c0c[i]):
                continue
            shift = float(c0c[i]); start = 0
        else:
            if len(CLS[i]) < k - 1:
                continue
            shift = float(CLS[i][k - 2]); start = k - 1
        v, why = walk_shift(i, shift, start)
        if v is None:
            continue
        r_a[i] = v; reason[i] = why
        sc = 1.0 + shift
        if sc > 0.05:
            vb, _ = walk_shift(i, shift, start, scale=sc)
            r_b[i] = vb if vb is not None else np.nan
    store[k] = (r_a, r_b, reason)
    m = np.isfinite(r_a)
    bm, lo, hi, p = X.day_block_boot(r_a[m], days[m])
    d = {"delay_min": k, "n": int(m.sum()),
         "mean_r_variantA": round(float(np.nanmean(r_a)), 5),
         "boot_lo95": round(lo, 5), "boot_hi95": round(hi, 5), "p_le_0": round(p, 4),
         "mean_r_variantB": round(float(np.nanmean(r_b)), 5),
         "target_rate": round(float((reason[m] == "target").mean()), 4),
         "stop_rate": round(float((reason[m] == "stop").mean()), 4),
         "mark_rate": round(float((reason[m] == "path_end").mean()), 4),
         "mean_r_takeable": round(float(np.nanmean(r_a[take])), 5)}
    res["reanchor"][k] = d
    print("delay=%3d min  n=%5d  A=%8.5f [%8.5f,%8.5f] p=%.3f  B=%8.5f  tgt=%.3f stop=%.3f mark=%.3f"
          % (k, d["n"], d["mean_r_variantA"], lo, hi, p, d["mean_r_variantB"],
             d["target_rate"], d["stop_rate"], d["mark_rate"]), flush=True)

res["baselines"] = {
    "pool_fill_honest_stale_level": round(float(np.nanmean(honr)), 5),
    "pool_gross_r": round(float(np.nanmean(O["gross"])), 5),
}
print(json.dumps(res["baselines"], indent=1), flush=True)

# ---- paired delta vs delay 0, day-block bootstrapped, and stability
res["paired_vs_delay0"] = {}
r0 = store[0][0]
for k in DELAYS[1:]:
    rk = store[k][0]
    m = np.isfinite(r0) & np.isfinite(rk)
    dlt = rk[m] - r0[m]
    bm, lo, hi, p = X.day_block_boot(dlt, days[m])
    per_sym = sum(1 for s in np.unique(sym) if np.nanmean(rk[m & (sym == s)]) >
                  np.nanmean(r0[m & (sym == s)]))
    fams = [s for s in np.unique(fam) if (fam == s).sum() > 100]
    per_fam = sum(1 for s in fams if np.nanmean(rk[m & (fam == s)]) > np.nanmean(r0[m & (fam == s)]))
    res["paired_vs_delay0"][k] = {
        "n": int(m.sum()), "delta": round(float(dlt.mean()), 5),
        "lo95": round(lo, 5), "hi95": round(hi, 5), "p_le_0": round(p, 4),
        "changed_share": round(float((np.abs(dlt) > 1e-9).mean()), 4),
        "odd": round(float((rk - r0)[m & (dnum % 2 == 1)].mean()), 5),
        "even": round(float((rk - r0)[m & (dnum % 2 == 0)].mean()), 5),
        "h1": round(float((rk - r0)[m & (dnum <= 15)].mean()), 5),
        "h2": round(float((rk - r0)[m & (dnum > 15)].mean()), 5),
        "symbols_improved": "%d/%d" % (per_sym, len(np.unique(sym))),
        "families_improved": "%d/%d" % (per_fam, len(fams)),
    }
    v = res["paired_vs_delay0"][k]
    print("k=%3d  delta=%8.5f [%8.5f,%8.5f] p=%.3f moved=%.3f odd=%8.5f even=%8.5f h1=%8.5f h2=%8.5f sym %s fam %s"
          % (k, v["delta"], v["lo95"], v["hi95"], v["p_le_0"], v["changed_share"],
             v["odd"], v["even"], v["h1"], v["h2"], v["symbols_improved"],
             v["families_improved"]), flush=True)

# ---- re-anchor COMBINED with the confirm filter and the geometry filter
res["combined"] = {}
r1 = store[1][0]
for nm, keep in (("reanchor1_all", np.ones(n, bool)),
                 ("reanchor1_confirm_gt_-0.15", ~(np.isfinite(c0c) & (c0c <= -0.15))),
                 ("reanchor1_confirm_gt_-0.30", ~(np.isfinite(c0c) & (c0c <= -0.30))),
                 ("reanchor1_geo_gt_0.60", ~(np.isfinite(geo) & (geo <= 0.60))),
                 ("reanchor1_confirm_and_geo", ~((np.isfinite(c0c) & (c0c <= -0.15)) |
                                                 (np.isfinite(geo) & (geo <= 0.60)))),
                 ("reanchor5_all", None)):
    rr = store[5][0] if nm == "reanchor5_all" else r1
    kk = np.ones(n, bool) if keep is None else keep
    booked = np.where(kk & np.isfinite(rr), rr, 0.0)
    bm, lo, hi, p = X.day_block_boot(booked, days)
    res["combined"][nm] = {"n_kept": int((kk & np.isfinite(rr)).sum()),
                           "pool_r_per_candidate": round(float(booked.mean()), 5),
                           "kept_mean": round(float(np.nanmean(rr[kk])), 5),
                           "lo95": round(lo, 5), "hi95": round(hi, 5), "p_le_0": round(p, 4)}
    v = res["combined"][nm]
    print("%-30s kept=%5d poolR=%8.5f [%8.5f,%8.5f] p=%.4f keptMean=%8.5f"
          % (nm, v["n_kept"], v["pool_r_per_candidate"], v["lo95"], v["hi95"],
             v["p_le_0"], v["kept_mean"]), flush=True)

# ---- inside the bar-1 cohort: does the confirm minute separate continue from revert?
b1 = O["bar1"]
res["BAR1_SPLIT"] = {}
for lab, m in (("bar1_all", take & b1),
               ("bar1_confirm_ok", take & b1 & np.isfinite(c0c) & (c0c > -0.15)),
               ("bar1_confirm_bad", take & b1 & np.isfinite(c0c) & (c0c <= -0.15)),
               ("bar1_confirm_ok_strict", take & b1 & np.isfinite(c0c) & (c0c > -0.05)),
               ("bar1_confirm_bad_strict", take & b1 & np.isfinite(c0c) & (c0c <= -0.05))):
    if m.sum() < 50:
        continue
    bm, lo, hi, p = X.day_block_boot(honr[m], days[m])
    res["BAR1_SPLIT"][lab] = {
        "n": int(m.sum()), "honr": round(float(np.nanmean(honr[m])), 5),
        "lo95": round(lo, 5), "hi95": round(hi, 5),
        "target_rate": round(float((O["hon"][m] == "target").mean()), 4),
        "stop_rate": round(float((O["hon"][m] == "stop").mean()), 4),
        "reanchor1_mean": round(float(np.nanmean(r1[m])), 5),
        "odd": round(float(np.nanmean(honr[m & (dnum % 2 == 1)])), 5),
        "even": round(float(np.nanmean(honr[m & (dnum % 2 == 0)])), 5)}
    v = res["BAR1_SPLIT"][lab]
    print("%-26s n=%5d honR=%8.5f [%8.5f,%8.5f] tgt=%.3f stop=%.3f reanchor=%8.5f odd=%8.5f even=%8.5f"
          % (lab, v["n"], v["honr"], v["lo95"], v["hi95"], v["target_rate"], v["stop_rate"],
             v["reanchor1_mean"], v["odd"], v["even"]), flush=True)

np.save(os.path.join(D, "x4_reanchor_r1.npy"), store[1][0])
np.save(os.path.join(D, "x4_reanchor_r0.npy"), store[0][0])
np.save(os.path.join(D, "x4_reanchor_r5.npy"), store[5][0])
with open(os.path.join(D, "X4_REANCHOR_V1.json"), "w") as f:
    json.dump(res, f, indent=1)
print("wrote X4_REANCHOR_V1.json")
