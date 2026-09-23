#!/usr/bin/env python3
"""B1 — is the top-of-book concentration IMPLEMENTABLE, or is it look-ahead?

b1_concentration.py ranks within decision window among LIMIT candidates THAT FILLED. At decision
time you do not know which will fill, so that rank is not available. This script recomputes the rank
over ALL scored LIMIT candidates in the window -- fills and non-fills alike, which is exactly the
information an order router has -- and then reads the outcome of whichever of them resolved.

That is the implementable statistic. If the concentration survives it, a top-k LIMIT construction is
real; if it collapses, the concentration was an artifact of conditioning on fill.

Also prices the thing a router actually experiences: place the top-k LIMIT orders every window, most
never fill, and measure R PER WINDOW (not per fill) so non-fill is counted at its true value of zero.

Writes B1_IMPLEMENTABLE_RANK.json.
"""
from __future__ import annotations

import gzip
import json
import pickle

import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
CACHE = "/private/tmp/w21-puzzle-cache/rows_{m}.pkl.gz"
LIMIT_FAMILIES = {"current_fvg_fill", "current_ob_retest", "current_breaker_re_entry"}
STATE_OF = {"RESOLVED_FILLED_STOP": "STOP", "RESOLVED_FILLED_TARGET": "TARGET",
            "RESOLVED_FILLED_TIME_STOP": "TIME_STOP"}
SEED = 20260812
COND = {"STOP": 0.045474920021929516, "TARGET": 0.0, "TIME_STOP": 0.01211191127825696}


def boot(v, days, B=4000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float); days = np.asarray(days)
    ud = pd.unique(days); idx = {d: np.where(days == d)[0] for d in ud}
    o = np.empty(B)
    for b in range(B):
        p = rng.choice(len(ud), len(ud), replace=True)
        o[b] = v[np.concatenate([idx[ud[q]] for q in p])].mean()
    return ([float(np.quantile(o, .025)), float(np.quantile(o, .975))], float(o.std(ddof=1)))


rows = []
for m in ["feb", "apr", "may", "jun", "jul"]:
    for r in pickle.load(gzip.open(CACHE.format(m=m), "rb")):
        if str(r.get("origin_family")) not in LIMIT_FAMILIES:
            continue
        if r.get("pred_month_boundary") is None:
            continue                                     # unscored: a router could not rank it
        rows.append((m, str(r["trading_day"]), str(r["decision_window_id"]),
                     STATE_OF.get(str(r.get("lifecycle_label_status"))),
                     str(r.get("lifecycle_label_status")),
                     float(r["pred_month_boundary"]),
                     float(r.get("terminal_net_r") or 0.0), float(r.get("cost_r") or 0.0)))
L = pd.DataFrame(rows, columns=["month", "day", "window", "state", "status", "pred", "net", "cost"])
L["resolved"] = L.state.notna()
L["edge"] = L.net + L.cost
L["charge"] = [COND[s] if s in COND else 0.0 for s in L.state.fillna("")]
L["edge_true"] = np.where(L.resolved, L.edge - L.charge, np.nan)

# RANK OVER ALL SCORED LIMIT CANDIDATES IN THE WINDOW -- fills and non-fills alike
L["rank_all"] = L.groupby("window").pred.rank(ascending=False, method="first")

R = {"schema": "b1_implementable_rank_v1",
     "population": {
         "scored_LIMIT_candidates (rankable at decision time)": int(len(L)),
         "of_which_resolved_filled": int(L.resolved.sum()),
         "fill_rate": float(L.resolved.mean()),
         "n_windows": int(L.window.nunique()),
         "n_days": int(L.day.nunique())},
     "note": "rank_all is computed over every scored LIMIT candidate in the window, so it uses only "
             "decision-time information; b1_concentration.py ranked among fills only (look-ahead)"}

buckets = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 10), (11, 20), (21, 10**9)]
tab = []
for lo, hi in buckets:
    g = L[(L.rank_all >= lo) & (L.rank_all <= hi)]
    gr = g[g.resolved]
    if len(gr) < 30:
        continue
    ci, se = boot(gr.edge_true.values, gr.day.values)
    tab.append(dict(rank_lo=lo, rank_hi=(None if hi > 10**8 else hi),
                    n_candidates=int(len(g)), n_filled=int(len(gr)),
                    fill_rate=float(len(gr) / len(g)),
                    edge_raw=float(gr.edge.mean()), edge_true=float(gr.edge_true.mean()),
                    ci95=ci, se=se, t=float(gr.edge_true.mean() / se)))
R["A_by_decision_time_rank"] = tab

# ---- per-WINDOW economics: place top-k every window, count non-fill as zero ----
per_window = {}
for k in [1, 3, 5, 10, 10**9]:
    g = L[L.rank_all <= k]
    # R per window = sum of realised edge_true over the k orders placed, non-fills contribute 0
    w = g.groupby(["day", "window"]).apply(
        lambda x: float(np.nansum(x.edge_true.values)), include_groups=False).rename("R")
    w = w.reset_index()
    ci, se = boot(w.R.values, w.day.values)
    lab = "ALL" if k > 10**8 else f"top_{k}"
    per_window[lab] = dict(orders_placed=int(len(g)), fills=int(g.resolved.sum()),
                           fill_rate=float(g.resolved.mean()),
                           n_windows=int(len(w)),
                           R_per_window=float(w.R.mean()), ci95=ci, se=se,
                           t=float(w.R.mean() / se),
                           significant=bool(abs(w.R.mean() / se) > 1.959964),
                           total_R=float(w.R.sum()))
R["B_per_window_economics"] = per_window

# ---- does the top-1 result survive month by month? ----
g1 = L[(L.rank_all == 1) & L.resolved]
R["C_top1_by_month"] = {}
for m, gm in g1.groupby("month"):
    ci, se = boot(gm.edge_true.values, gm.day.values)
    R["C_top1_by_month"][m] = dict(n=int(len(gm)), edge_true=float(gm.edge_true.mean()),
                                   ci95=ci, se=se, t=float(gm.edge_true.mean() / se))
# leave-one-month-out
R["C_top1_leave_one_month_out"] = {}
for m in ["feb", "apr", "may", "jun", "jul"]:
    gm = g1[g1.month != m]
    ci, se = boot(gm.edge_true.values, gm.day.values)
    R["C_top1_leave_one_month_out"][f"drop_{m}"] = dict(
        n=int(len(gm)), edge_true=float(gm.edge_true.mean()), ci95=ci, t=float(gm.edge_true.mean() / se))

json.dump(R, open(f"{OUT}/B1_IMPLEMENTABLE_RANK.json", "w"), indent=1)
print(json.dumps(R, indent=1))
