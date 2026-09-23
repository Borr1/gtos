#!/usr/bin/env python3
"""x4 step 3 — CONTROLS, then the bar-1 cohort.

Three confounds must die before any intra-bar claim is believable:
  C1 SYMBOL   l3 measured symbol IV = 0.249, the top categorical in the whole schema. A feature
              whose level differs by symbol re-discovers symbol. Fix: rank-transform every
              feature WITHIN symbol (uniform 0..1) and re-measure.
  C2 BORN     `c0_*` correlate 0.94-0.98 with the decision-instant market offset. Report both.
  C3 GEOMETRY every economically-live feature might be one axis. Fix: stratify on
              stop_dist_over_bar_range quintiles and look for a surviving within-stratum gradient.

Then the mission's item 3: inside the 55.65 % whose entry is touched in the first path minute,
what separates CONTINUE (honest target) from REVERT (honest stop)?
"""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

recs = X.load_joined()
O = X.outcomes(recs)
take = O["takeable"]; honr = O["honr"]; hon = O["hon"]
sym = np.array([r["symbol"] for r in recs])
days = np.array([r["_day"] for r in recs])
names = X.feature_names(recs)
res = {}


def rank_within(x, grp, mask):
    """Uniform rank of x within each group, computed on `mask` rows only. NaN elsewhere."""
    out = np.full(len(x), np.nan)
    for g in np.unique(grp[mask]):
        s = mask & (grp == g) & np.isfinite(x)
        if s.sum() < 40:
            continue
        v = x[s]
        order = v.argsort(kind="mergesort")
        rk = np.empty(len(v)); rk[order] = np.arange(len(v))
        out[np.where(s)[0]] = rk / max(1, len(v) - 1)
    return out


# ---------------------------------------------------------------- C1: within-symbol
B_pos = take & (hon == "target"); B_neg = take & (hon == "stop")
rowsC1 = []
for nm in names:
    x = X.col(recs, nm)
    xr = rank_within(x, sym, take)
    d_raw = X.cohens_d(x[B_pos], x[B_neg])
    d_sym = X.cohens_d(xr[B_pos], xr[B_neg])
    a_sym = X.auc(xr[B_pos], xr[B_neg])
    # economic gradient after symbol normalisation
    m = take & np.isfinite(xr)
    spread = rho = None
    if m.sum() > 2000:
        qs = np.quantile(xr[m], np.linspace(0, 1, 11))
        qs = np.unique(qs)
        if len(qs) >= 4:
            idx = np.clip(np.searchsorted(qs, xr, side="right") - 1, 0, len(qs) - 2)
            dm = [float(np.nanmean(honr[m & (idx == b)])) for b in range(len(qs) - 1)
                  if (m & (idx == b)).sum() > 30]
            if len(dm) >= 5:
                spread = round(max(dm) - min(dm), 5)
                rho = round(float(np.corrcoef(np.arange(len(dm)), dm)[0, 1]), 4)
    rowsC1.append({"feature": nm,
                   "cls": "CONFIRM" if nm.startswith("c0_") else "PRE",
                   "d_raw": None if not np.isfinite(d_raw) else round(float(d_raw), 4),
                   "d_within_symbol": None if not np.isfinite(d_sym) else round(float(d_sym), 4),
                   "auc_within_symbol": None if not np.isfinite(a_sym) else round(float(a_sym), 4),
                   "decile_spread_ws": spread, "decile_rho_ws": rho})
rowsC1.sort(key=lambda r: -abs(r["d_within_symbol"] or 0))
res["C1_within_symbol"] = rowsC1
print("=== C1 within-symbol rank-normalised, honest target-vs-stop, takeable ===")
print("%-28s %-7s %8s %8s %8s %8s %8s" % ("feature", "cls", "d_raw", "d_wsym", "auc_wsym",
                                          "spread", "rho"))
for r in rowsC1[:24]:
    print("%-28s %-7s %8s %8s %8s %8s %8s" % (r["feature"], r["cls"], r["d_raw"],
          r["d_within_symbol"], r["auc_within_symbol"], r["decile_spread_ws"], r["decile_rho_ws"]))

# ---------------------------------------------------------------- C3: stratified on geometry
G = X.col(recs, "stop_dist_over_bar_range")
gq = np.quantile(G[take & np.isfinite(G)], [0.2, 0.4, 0.6, 0.8])
gbin = np.digitize(G, gq)
CAND = ["clv_fav", "up_min_frac", "net_min_frac", "late3_r", "late5_r", "dir_eff",
        "retrace_from_fav", "argmax_fav_pos", "vol_late3_share", "vol_centroid",
        "max_run_diff", "n_dir_flips", "entry_touch_minutes", "entry_close_crossings",
        "wick_beyond_close_fav_r", "prior_same_dir_bars", "pos_in_prior60_range",
        "gap_from_prev_close_r", "range_expansion", "vol_expansion", "c0_close_fav_r",
        "c0_ret_r", "c0_clv_fav", "atr16_m15_r", "max_min_range_r", "accel_late_minus_first"]
strat = {}
for nm in CAND:
    x = X.col(recs, nm)
    per = []
    for g in range(5):
        m = take & (gbin == g) & np.isfinite(x)
        if m.sum() < 400:
            per.append(None); continue
        med = np.nanmedian(x[m])
        hi = m & (x > med); lo = m & (x <= med)
        if hi.sum() < 100 or lo.sum() < 100:
            per.append(None); continue
        per.append({"n_hi": int(hi.sum()), "n_lo": int(lo.sum()),
                    "honr_hi": round(float(np.nanmean(honr[hi])), 5),
                    "honr_lo": round(float(np.nanmean(honr[lo])), 5),
                    "delta": round(float(np.nanmean(honr[hi]) - np.nanmean(honr[lo])), 5)})
    ds = [p["delta"] for p in per if p]
    strat[nm] = {"per_stratum": per,
                 "mean_delta": round(float(np.mean(ds)), 5) if ds else None,
                 "n_pos": int(sum(1 for d in ds if d > 0)), "n_strata": len(ds),
                 "all_same_sign": bool(ds and (all(d > 0 for d in ds) or all(d < 0 for d in ds)))}
res["C3_stratified_on_geometry"] = strat
print("\n=== C3 median split WITHIN stop_dist_over_bar_range quintiles (honest R delta) ===")
print("%-28s %9s %6s %6s  %s" % ("feature", "meanDelta", "pos", "of", "per-quintile deltas"))
for nm, v in sorted(strat.items(), key=lambda kv: -abs(kv[1]["mean_delta"] or 0)):
    dl = [p["delta"] if p else None for p in v["per_stratum"]]
    print("%-28s %9s %6d %6d  %s" % (nm, v["mean_delta"], v["n_pos"], v["n_strata"], dl))

# ---------------------------------------------------------------- the bar-1 cohort
b1 = take & O["bar1"]
b1_pos = b1 & (hon == "target"); b1_neg = b1 & (hon == "stop")
res["bar1"] = {"n": int(b1.sum()), "n_target": int(b1_pos.sum()), "n_stop": int(b1_neg.sum()),
               "mean_honr": round(float(np.nanmean(honr[b1])), 5),
               "mean_honr_rest": round(float(np.nanmean(honr[take & ~O["bar1"]])), 5)}
tb = []
for nm in names:
    x = X.col(recs, nm)
    xr = rank_within(x, sym, b1)
    d = X.cohens_d(x[b1_pos], x[b1_neg])
    dws = X.cohens_d(xr[b1_pos], xr[b1_neg])
    a = X.auc(x[b1_pos], x[b1_neg])
    m = b1 & np.isfinite(x)
    spread = rho = None
    if m.sum() > 1200:
        qs = np.unique(np.quantile(x[m], np.linspace(0, 1, 11)))
        if len(qs) >= 4:
            idx = np.clip(np.searchsorted(qs, x, side="right") - 1, 0, len(qs) - 2)
            dm = [float(np.nanmean(honr[m & (idx == b)])) for b in range(len(qs) - 1)
                  if (m & (idx == b)).sum() > 25]
            if len(dm) >= 5:
                spread = round(max(dm) - min(dm), 5)
                rho = round(float(np.corrcoef(np.arange(len(dm)), dm)[0, 1]), 4)
    tb.append({"feature": nm, "cls": "CONFIRM" if nm.startswith("c0_") else "PRE",
               "d": None if not np.isfinite(d) else round(float(d), 4),
               "d_wsym": None if not np.isfinite(dws) else round(float(dws), 4),
               "auc": None if not np.isfinite(a) else round(float(a), 4),
               "spread": spread, "rho": rho})
tb.sort(key=lambda r: -abs(r["d"] or 0))
res["bar1_ranking"] = tb
print("\n=== BAR-1 COHORT (entry touched in the first path minute): n=%d target=%d stop=%d honR=%s ==="
      % (b1.sum(), b1_pos.sum(), b1_neg.sum(), res["bar1"]["mean_honr"]))
print("%-28s %-7s %8s %8s %8s %8s %8s" % ("feature", "cls", "d", "d_wsym", "auc", "spread", "rho"))
for r in tb[:22]:
    print("%-28s %-7s %8s %8s %8s %8s %8s" % (r["feature"], r["cls"], r["d"], r["d_wsym"],
                                              r["auc"], r["spread"], r["rho"]))

with open(os.path.join(D, "X4_CONTROL_V1.json"), "w") as f:
    json.dump(res, f, indent=1)
print("\nwrote X4_CONTROL_V1.json")
