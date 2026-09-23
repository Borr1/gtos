#!/usr/bin/env python3
"""x4 step 6 — the conditional policy, the cost interaction, and the CEILING.

Three things:
 1. CONDITIONAL policy. Refusing books 0.0; re-anchoring books a real trade at the T+1m market.
    Neither dominates everywhere -- re-anchoring is worth +0.36 R on the cohort that ran away
    and NEGATIVE where it did not. Sweep the conditional form.
 2. COST. Both filters are also cost filters (median cost_r 0.553 -> 0.223 across the geometry
    quintiles). Report net as well as gross so the improvement is not double-counted or hidden.
 3. CEILING. Cross-fitted (GroupKFold by trading day, so no day leaks) AUC and policy R from
    EVERYTHING inside the bar. This is the number that tells the owner where not to spend.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from sklearn.preprocessing import StandardScaler

recs = X.load_joined()
O = X.outcomes(recs)
n = len(recs)
honr = np.nan_to_num(O["honr"], nan=0.0)
hon = O["hon"]; take = O["takeable"]; b1 = O["bar1"]
cost = np.array([X._num(r["cost_r"]) for r in recs])
days = np.array([r["_day"] for r in recs])
sym = np.array([r["symbol"] for r in recs])
fam = np.array([str(r.get("origin_family")) for r in recs])
sess = np.array([str(r.get("session_bucket")) for r in recs])
dnum = np.array([int(d[-2:]) for d in days])
c0c = X.col(recs, "c0_close_fav_r"); geo = X.col(recs, "stop_dist_over_bar_range")
r1 = np.load(os.path.join(D, "x4_reanchor_r1.npy"))
r5 = np.load(os.path.join(D, "x4_reanchor_r5.npy"))
res = {}

def rep(v, label, extra=None):
    m, lo, hi, p = X.day_block_boot(v, days)
    d = {"policy": label, "pool_r": round(float(np.mean(v)), 5),
         "lo95": round(lo, 5), "hi95": round(hi, 5), "p_le_0": round(p, 4),
         "odd": round(float(v[dnum % 2 == 1].mean()), 5),
         "even": round(float(v[dnum % 2 == 0].mean()), 5),
         "h1": round(float(v[dnum <= 15].mean()), 5),
         "h2": round(float(v[dnum > 15].mean()), 5)}
    if extra:
        d.update(extra)
    return d

# ---------------------------------------------------------------- 1. conditional policy
res["POLICY"] = {}
base = honr.copy()
res["POLICY"]["P0_rest_limit_as_today"] = rep(base, "P0")
for th in [-0.40, -0.30, -0.20, -0.15, -0.10, -0.05, 0.0]:
    bad = np.isfinite(c0c) & (c0c <= th)
    v_ref = np.where(bad, 0.0, base)
    v_ran = np.where(bad & np.isfinite(r1), r1, base)
    v_ra5 = np.where(bad & np.isfinite(r5), r5, base)
    res["POLICY"]["P1_refuse_%.2f" % th] = rep(v_ref, "refuse c0<=%.2f" % th,
                                               {"n_touched": int(bad.sum())})
    res["POLICY"]["P2_reanchor1_%.2f" % th] = rep(v_ran, "reanchor@1m c0<=%.2f" % th,
                                                  {"n_touched": int(bad.sum())})
    res["POLICY"]["P3_reanchor5_%.2f" % th] = rep(v_ra5, "reanchor@5m c0<=%.2f" % th,
                                                  {"n_touched": int(bad.sum())})
    print("th=%6.2f n=%5d | refuse %8.5f [%s,%s] | reanchor1 %8.5f | reanchor5 %8.5f" % (
        th, bad.sum(), res["POLICY"]["P1_refuse_%.2f" % th]["pool_r"],
        res["POLICY"]["P1_refuse_%.2f" % th]["lo95"], res["POLICY"]["P1_refuse_%.2f" % th]["hi95"],
        res["POLICY"]["P2_reanchor1_%.2f" % th]["pool_r"],
        res["POLICY"]["P3_reanchor5_%.2f" % th]["pool_r"]), flush=True)

# two-sided: refuse the very bad, re-anchor the middle
bad = np.isfinite(c0c) & (c0c <= -0.30)
mid = np.isfinite(c0c) & (c0c > -0.30) & (c0c <= -0.05)
v = np.where(bad, 0.0, np.where(mid & np.isfinite(r5), r5, base))
res["POLICY"]["P4_refuse_lt_-0.30_reanchor5_mid"] = rep(v, "P4")
print("P4 refuse<=-0.30 + reanchor5 mid: %s" % json.dumps(res["POLICY"]["P4_refuse_lt_-0.30_reanchor5_mid"]), flush=True)
# geometry stack on top of the best refuse
best = np.where(np.isfinite(c0c) & (c0c <= -0.15), 0.0, base)
g = np.isfinite(geo) & (geo <= 0.60)
res["POLICY"]["P5_refuse_c0_and_geo"] = rep(np.where(g, 0.0, best), "P5")
print("P5 +geo<=0.60: %s" % json.dumps(res["POLICY"]["P5_refuse_c0_and_geo"]), flush=True)

# ---------------------------------------------------------------- 2. cost
res["COST"] = {}
for lab, keep in (("all", np.ones(n, bool)),
                  ("c0_gt_-0.15", ~(np.isfinite(c0c) & (c0c <= -0.15))),
                  ("geo_gt_0.60", ~(np.isfinite(geo) & (geo <= 0.60))),
                  ("both", ~((np.isfinite(c0c) & (c0c <= -0.15)) | (np.isfinite(geo) & (geo <= 0.60))))):
    net = np.where(keep, honr - np.nan_to_num(cost, nan=0.0), 0.0)
    res["COST"][lab] = {
        "n_kept": int(keep.sum()),
        "gross_pool_r": round(float(np.where(keep, honr, 0.0).mean()), 5),
        "median_cost_kept": round(float(np.nanmedian(cost[keep])), 5),
        "mean_cost_kept": round(float(np.nanmean(cost[keep])), 5),
        "net_pool_r": round(float(net.mean()), 5),
        "net_kept_mean": round(float(np.nanmean((honr - cost)[keep])), 5)}
    print(lab, json.dumps(res["COST"][lab]), flush=True)

# ---------------------------------------------------------------- 3. breakdowns of the headline split
res["HEADLINE_SPLIT"] = {}
ok = take & b1 & np.isfinite(c0c) & (c0c > -0.15)
badb = take & b1 & np.isfinite(c0c) & (c0c <= -0.15)
for axis, arr in (("symbol", sym), ("family", fam), ("session", sess)):
    t = {}
    for u in np.unique(arr):
        a, b = ok & (arr == u), badb & (arr == u)
        if a.sum() < 40 or b.sum() < 40:
            continue
        t[u] = {"n_ok": int(a.sum()), "n_bad": int(b.sum()),
                "honr_ok": round(float(np.nanmean(honr[a])), 5),
                "honr_bad": round(float(np.nanmean(honr[b])), 5),
                "gap": round(float(np.nanmean(honr[a]) - np.nanmean(honr[b])), 5)}
    res["HEADLINE_SPLIT"][axis] = t
    pos = sum(1 for v in t.values() if v["gap"] > 0)
    print("split holds on %d/%d %s cells" % (pos, len(t), axis), flush=True)

# ---------------------------------------------------------------- 4. CEILING, cross-fitted
names = [nm for nm in X.feature_names(recs)]
PRE = [nm for nm in names if not nm.startswith("c0_")]
Mfull = np.column_stack([X.col(recs, nm) for nm in names])
Mpre = np.column_stack([X.col(recs, nm) for nm in PRE])
resolved = take & ((hon == "target") | (hon == "stop"))
y = (hon == "target").astype(int)
gkf = GroupKFold(n_splits=5)
res["CEILING"] = {}
for lab, M in (("PRE_only", Mpre), ("PRE_plus_CONFIRM", Mfull)):
    for mdl_lab in ("logistic", "gbm"):
        idx = np.where(resolved)[0]
        oof = np.full(len(idx), np.nan)
        for tr, te in gkf.split(idx, y[idx], groups=days[idx]):
            Xtr, Xte = M[idx[tr]], M[idx[te]]
            if mdl_lab == "logistic":
                mu = np.nanmean(Xtr, axis=0)
                Xtr2 = np.where(np.isfinite(Xtr), Xtr, mu); Xte2 = np.where(np.isfinite(Xte), Xte, mu)
                sc = StandardScaler().fit(Xtr2)
                m = LogisticRegression(max_iter=2000, C=0.1).fit(sc.transform(Xtr2), y[idx[tr]])
                oof[te] = m.predict_proba(sc.transform(Xte2))[:, 1]
            else:
                m = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06,
                                                   max_leaf_nodes=15, l2_regularization=1.0,
                                                   random_state=0).fit(Xtr, y[idx[tr]])
                oof[te] = m.predict_proba(Xte)[:, 1]
        a = roc_auc_score(y[idx], oof)
        # economic: trade only the top half / top decile of the cross-fitted score
        sc_all = np.full(n, np.nan); sc_all[idx] = oof
        econ = {}
        for q, qn in ((0.5, "top50"), (0.25, "top25"), (0.1, "top10")):
            thr = np.nanquantile(oof, 1 - q)
            keep = np.isfinite(sc_all) & (sc_all >= thr)
            econ[qn] = {"n": int(keep.sum()),
                        "honr": round(float(np.nanmean(honr[keep])), 5),
                        "target_rate": round(float((hon[keep] == "target").mean()), 4)}
        res["CEILING"]["%s_%s" % (lab, mdl_lab)] = {
            "n": len(idx), "cross_fitted_auc": round(float(a), 4),
            "base_rate": round(float(y[idx].mean()), 4), "econ": econ}
        print("CEILING %-18s %-9s AUC=%.4f  base=%.4f  %s" % (
            lab, mdl_lab, a, y[idx].mean(), json.dumps(econ)), flush=True)

with open(os.path.join(D, "X4_POLICY_V1.json"), "w") as f:
    json.dump(res, f, indent=1)
print("wrote X4_POLICY_V1.json")
