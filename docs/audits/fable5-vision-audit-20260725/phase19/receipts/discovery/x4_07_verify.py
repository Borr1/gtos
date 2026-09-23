#!/usr/bin/env python3
"""x4 step 7 — adversarial verification of x4's own claims, and the residual question.

V1 Is c0_close_fav_r the SAME variable as the w0cap2 anchor's mkt_r_close? If so x4 did not
   find a new field; it found where an existing one lives. Say so.
V2 Is the bar-1 split an artifact of entry_is_bar_close (at-market vs level orders)?
V3 Is the geometry feature circular -- does the generator derive the stop FROM the bar range?
V4 After the confirm filter, is there RESIDUAL structure, or is the confirm minute the whole story?
V5 The missing-minute defect: how many of the invisible rows does the honest walk book as no_fill?
V6 The PRE-only rule in full, with bootstrap and split halves.
V7 Multiplicity: how many cells did x4 look at?
"""
from __future__ import annotations
import gzip, json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X
import w0_ws

recs = X.load_joined()
O = X.outcomes(recs)
n = len(recs)
honr = np.nan_to_num(O["honr"], nan=0.0)
hon = O["hon"]; take = O["takeable"]; b1 = O["bar1"]
days = np.array([r["_day"] for r in recs]); dnum = np.array([int(d[-2:]) for d in days])
sym = np.array([r["symbol"] for r in recs])
c0c = X.col(recs, "c0_close_fav_r"); geo = X.col(recs, "stop_dist_over_bar_range")
atmkt = X.col(recs, "entry_is_bar_close") == 1.0
res = {}

# ---- V1 identity with the existing anchor variable
mk = np.array([X._num(r["_mkt_r_close"]) for r in recs])
m = np.isfinite(mk) & np.isfinite(c0c)
res["V1_identity_with_anchor"] = {
    "n_compared": int(m.sum()),
    "max_abs_diff": round(float(np.nanmax(np.abs(mk[m] - c0c[m]))), 8),
    "share_within_1e-6": round(float((np.abs(mk[m] - c0c[m]) < 1e-6).mean()), 6),
    "pearson": round(float(np.corrcoef(mk[m], c0c[m])[0, 1]), 8),
    "verdict": None}
res["V1_identity_with_anchor"]["verdict"] = (
    "IDENTICAL - c0_close_fav_r IS w0cap2's mkt_r_close; x4 did not find a new field"
    if res["V1_identity_with_anchor"]["share_within_1e-6"] > 0.99 else
    "DISTINCT")
print("V1", json.dumps(res["V1_identity_with_anchor"]), flush=True)

# ---- V2 at-market vs level orders
res["V2_atmkt_split"] = {}
for lab, base in (("at_market", atmkt), ("level_order", ~atmkt)):
    ok = take & b1 & base & np.isfinite(c0c) & (c0c > -0.15)
    bad = take & b1 & base & np.isfinite(c0c) & (c0c <= -0.15)
    if ok.sum() < 50 or bad.sum() < 50:
        continue
    res["V2_atmkt_split"][lab] = {
        "n_ok": int(ok.sum()), "honr_ok": round(float(np.nanmean(honr[ok])), 5),
        "n_bad": int(bad.sum()), "honr_bad": round(float(np.nanmean(honr[bad])), 5),
        "gap": round(float(np.nanmean(honr[ok]) - np.nanmean(honr[bad])), 5)}
    print("V2", lab, json.dumps(res["V2_atmkt_split"][lab]), flush=True)

# ---- V3 is the stop derived from the bar range?
rd = np.array([X._num(r["risk_distance"]) for r in recs])
bar_rng = X.col(recs, "bar_range_r") * rd  # price units
si = X.col(recs, "stop_inside_bar")
res["V3_geometry_circularity"] = {
    "geo_min": round(float(np.nanmin(geo)), 4), "geo_p05": round(float(np.nanpercentile(geo, 5)), 4),
    "geo_median": round(float(np.nanmedian(geo)), 4), "geo_p95": round(float(np.nanpercentile(geo, 95)), 4),
    "geo_max": round(float(np.nanmax(geo)), 4),
    "share_geo_in_0.95_1.05": round(float(np.nanmean((geo > 0.95) & (geo < 1.05))), 5),
    "share_stop_inside_decision_bar": round(float(np.nanmean(si)), 5),
    "corr_risk_distance_vs_bar_range_price_units": round(
        float(np.corrcoef(rd[np.isfinite(rd) & np.isfinite(bar_rng)],
                          bar_rng[np.isfinite(rd) & np.isfinite(bar_rng)])[0, 1]), 4)}
print("V3", json.dumps(res["V3_geometry_circularity"]), flush=True)

# ---- V4 residual structure after the confirm filter
keepc = take & np.isfinite(c0c) & (c0c > -0.15)
kp = keepc & (hon == "target"); kn = keepc & (hon == "stop")
tb = []
for nm in X.feature_names(recs):
    x = X.col(recs, nm)
    d = X.cohens_d(x[kp], x[kn]); a = X.auc(x[kp], x[kn])
    mm = keepc & np.isfinite(x)
    spread = None
    if mm.sum() > 2000:
        qs = np.unique(np.quantile(x[mm], np.linspace(0, 1, 11)))
        if len(qs) >= 4:
            ix = np.clip(np.searchsorted(qs, x, side="right") - 1, 0, len(qs) - 2)
            dm = [float(np.nanmean(honr[mm & (ix == b)])) for b in range(len(qs) - 1)
                  if (mm & (ix == b)).sum() > 30]
            if len(dm) >= 5:
                spread = round(max(dm) - min(dm), 5)
    tb.append({"feature": nm, "d": None if not np.isfinite(d) else round(float(d), 4),
               "auc": None if not np.isfinite(a) else round(float(a), 4), "spread": spread})
tb.sort(key=lambda r: -abs(r["d"] or 0))
res["V4_residual_after_confirm"] = {"n_pop": int(keepc.sum()), "n_target": int(kp.sum()),
                                    "n_stop": int(kn.sum()), "top": tb[:15]}
print("V4 residual pop n=%d target=%d stop=%d" % (keepc.sum(), kp.sum(), kn.sum()))
for r in tb[:12]:
    print("   %-28s d=%7s auc=%7s spread=%8s" % (r["feature"], r["d"], r["auc"], r["spread"]))

# ---- V5 the missing minute vs the honest walk's fill
c0a = X.col(recs, "c0_adv_r")
mm_touch = np.isfinite(c0a) & (c0a <= 0.0)
inv = mm_touch & ~b1
res["V5_missing_minute"] = {
    "n_invisible": int(inv.sum()),
    "share_of_pool": round(float(inv.mean()), 5),
    "honest_walk_verdicts": {k: int((hon[inv] == k).sum())
                             for k in ("no_fill", "target", "stop", "neither")},
    "no_fill_share": round(float((hon[inv] == "no_fill").mean()), 5),
    "honr_booked": round(float(np.nanmean(honr[inv])), 5),
    "pool_gross_r_of_these": round(float(np.nanmean(O["gross"][inv])), 5),
    "note": ("these entries WERE traded inside [T,T+1m) but the sidecar path starts at T+1m, "
             "so the fill-honest contract cannot see the fill and books what it sees")}
print("V5", json.dumps(res["V5_missing_minute"]), flush=True)

# ---- V6 the PRE-only rule in full
res["V6_pre_only_rule"] = {}
for th in [0.5, 0.6, 0.7, 0.8]:
    keep = ~(np.isfinite(geo) & (geo <= th))
    v = np.where(keep, honr, 0.0)
    mm, lo, hi, p = X.day_block_boot(v, days)
    dlt = v - honr
    m2, lo2, hi2, p2 = X.day_block_boot(dlt, days)
    imp = sum(1 for s in np.unique(sym)
              if np.where(keep & (sym == s), honr, 0.0).mean() > honr[sym == s].mean())
    res["V6_pre_only_rule"]["geo_gt_%.1f" % th] = {
        "n_kept": int(keep.sum()), "kept_share": round(float(keep.mean()), 4),
        "pool_r": round(float(v.mean()), 5), "lo95": round(lo, 5), "hi95": round(hi, 5),
        "delta_vs_base": round(float(dlt.mean()), 5), "delta_lo95": round(lo2, 5),
        "delta_hi95": round(hi2, 5), "delta_p_le_0": round(p2, 4),
        "odd": round(float(v[dnum % 2 == 1].mean()), 5),
        "even": round(float(v[dnum % 2 == 0].mean()), 5),
        "h1": round(float(v[dnum <= 15].mean()), 5), "h2": round(float(v[dnum > 15].mean()), 5),
        "symbols_improved": "%d/24" % imp}
    print("V6 geo>%.1f %s" % (th, json.dumps(res["V6_pre_only_rule"]["geo_gt_%.1f" % th])), flush=True)

res["V7_multiplicity"] = {
    "features_built": len(X.feature_names(recs)),
    "ranked_cells_step1": len(X.feature_names(recs)) * 6,
    "stratified_cells_step3": 26 * 5,
    "sweep_cells_step4_5_6": 10 + 8 + 6 + 8 + 7 * 3 + 4,
    "note": ("DISCOVERY lane: no multiplicity correction applied anywhere. Every headline is "
             "reported with an odd/even-day and first/second-half split and a day-block "
             "bootstrap; none of that is a substitute for an out-of-window test.")}

with open(os.path.join(D, "X4_VERIFY_V1.json"), "w") as f:
    json.dump(res, f, indent=1)
print("wrote X4_VERIFY_V1.json")
