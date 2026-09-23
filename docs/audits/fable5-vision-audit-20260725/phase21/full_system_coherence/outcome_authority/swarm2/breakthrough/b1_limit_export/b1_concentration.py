#!/usr/bin/env python3
"""B1 — is the LIMIT edge CONCENTRATED at the top of the book, or SPREAD across it?

This decides the branch. A sibling lane proved argmax-with-abstain cannot harvest this pool
(P(fill) composition migrates the argmax to MARKET; the shipped book's +0.954 R is a
non-transacting result, 81.4 % of argmaxes never fill). So if the LIMIT pool carries edge, the
question is what construction could take it:

  * edge RISING with the estate's own score  -> selection can harvest it (take a slice off the top)
  * edge FLAT across the score               -> only breadth harvests it (equal-weight the eligible pool)
  * edge FALLING with the score              -> the scorer is anti-correlated on this arm; neither works

Ranking uses `pred_month_boundary` -- the frozen prequential ridge's own out-of-sample prediction,
written by puzzle_build_cache.py at each month boundary. Ranks are computed WITHIN decision window,
among LIMIT candidates only (a hypothetical LIMIT-only architecture; the shipped rule ranks across
all candidates and abstains when the top is LIMIT).

Every block states its population explicitly.

Writes B1_CONCENTRATION.json.
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
# measured per-arm exit conditionals (this lane, tick-derived)
COND = {"LIMIT": {"STOP": 0.045474920021929516, "TARGET": 0.0, "TIME_STOP": 0.01211191127825696},
        "MARKET": {"STOP": 0.03931833660245846, "TARGET": 0.0, "TIME_STOP": 0.0014050254936245976}}


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
        fam = str(r.get("origin_family"))
        arm = "LIMIT" if fam in LIMIT_FAMILIES else "MARKET"
        st = STATE_OF.get(str(r.get("lifecycle_label_status")))
        rows.append((m, arm, fam, str(r["trading_day"]), str(r["decision_window_id"]), st,
                     r.get("pred_month_boundary"),
                     float(r.get("terminal_net_r") or 0.0), float(r.get("cost_r") or 0.0)))
A = pd.DataFrame(rows, columns=["month", "arm", "family", "day", "window", "state",
                                "pred", "net", "cost"])

R = {"schema": "b1_concentration_v1",
     "ranking_score": "pred_month_boundary (frozen prequential ridge, out-of-sample at each month "
                      "boundary; puzzle_build_cache.py)",
     "populations": {
         "P0_all_candidates": int(len(A)),
         "P1_resolved_filled_LIMIT (Lane 1's arm)": int(((A.arm == "LIMIT") & A.state.notna()).sum()),
         "P2_resolved_filled_LIMIT_with_ridge_score (rankable)":
             int(((A.arm == "LIMIT") & A.state.notna() & A.pred.notna()).sum()),
         "P1_resolved_filled_MARKET": int(((A.arm == "MARKET") & A.state.notna()).sum()),
     }}

# ---- P2: resolved LIMIT rows carrying a ridge score ----
L = A[(A.arm == "LIMIT") & A.state.notna() & A.pred.notna()].copy()
L["edge"] = L.net + L.cost
L["charge"] = [COND["LIMIT"][s] for s in L.state]
L["edge_true"] = L.edge - L.charge
R["P2_summary"] = dict(n=int(len(L)), n_days=int(L.day.nunique()),
                       n_windows=int(L.window.nunique()),
                       edge_raw=float(L.edge.mean()), edge_true=float(L.edge_true.mean()))

# ---- (a) within-window rank among LIMIT candidates: rank 1 = the LIMIT argmax ----
L["rank"] = L.groupby("window").pred.rank(ascending=False, method="first")
buckets = [(1, 1), (2, 2), (3, 3), (4, 5), (6, 10), (11, 20), (21, 50), (51, 10**9)]
rank_tab = []
for lo, hi in buckets:
    g = L[(L["rank"] >= lo) & (L["rank"] <= hi)]
    if len(g) < 30:
        continue
    ci, se = boot(g.edge_true.values, g.day.values)
    rank_tab.append(dict(rank_lo=lo, rank_hi=(None if hi > 10**8 else hi), n=int(len(g)),
                         edge_raw=float(g.edge.mean()), edge_true=float(g.edge_true.mean()),
                         ci95=ci, se=se, t=float(g.edge_true.mean() / se)))
R["A_by_within_window_rank"] = rank_tab

# ---- (b) decile of the ridge score across the whole rankable population ----
L["dec"] = pd.qcut(L.pred, 10, labels=False, duplicates="drop")
dec_tab = []
for d, g in L.groupby("dec"):
    ci, se = boot(g.edge_true.values, g.day.values)
    dec_tab.append(dict(decile=int(d), n=int(len(g)), pred_median=float(g.pred.median()),
                        edge_raw=float(g.edge.mean()), edge_true=float(g.edge_true.mean()),
                        ci95=ci, se=se, t=float(g.edge_true.mean() / se)))
R["B_by_score_decile"] = dec_tab

# monotonicity: rank correlation between decile and edge, and top-vs-bottom gap
dv = np.array([d["decile"] for d in dec_tab], float)
ev = np.array([d["edge_true"] for d in dec_tab], float)
R["B_monotonicity"] = dict(
    spearman_decile_vs_edge=float(pd.Series(dv).corr(pd.Series(ev), method="spearman")),
    top_decile_edge=float(ev[-1]), bottom_decile_edge=float(ev[0]),
    top_minus_bottom=float(ev[-1] - ev[0]))
# formal test of the top-vs-bottom difference, day-clustered
g9, g0 = L[L.dec == L.dec.max()], L[L.dec == L.dec.min()]
rng = np.random.default_rng(SEED)
days = pd.unique(L.day.values)
i9 = {d: g9.edge_true.values[g9.day.values == d] for d in days}
i0 = {d: g0.edge_true.values[g0.day.values == d] for d in days}
o = np.empty(4000)
for b in range(4000):
    p = rng.choice(len(days), len(days), replace=True)
    sel = days[p]
    a_ = np.concatenate([i9[d] for d in sel]); b_ = np.concatenate([i0[d] for d in sel])
    o[b] = (a_.mean() if len(a_) else 0) - (b_.mean() if len(b_) else 0)
obs = g9.edge_true.mean() - g0.edge_true.mean()
R["B_top_vs_bottom_decile_test"] = dict(diff=float(obs), se=float(o.std(ddof=1)),
                                        t=float(obs / o.std(ddof=1)),
                                        ci95=[float(np.quantile(o, .025)), float(np.quantile(o, .975))],
                                        significant=bool(abs(obs / o.std(ddof=1)) > 1.959964))

# ---- (c) what a top-k slice would earn vs equal-weighting the whole eligible pool ----
slices = {}
for lab, mask in [("top_1_per_window", L["rank"] == 1),
                  ("top_3_per_window", L["rank"] <= 3),
                  ("top_10_per_window", L["rank"] <= 10),
                  ("top_decile_of_score", L.dec == L.dec.max()),
                  ("top_half_of_score", L.dec >= 5),
                  ("ALL_rankable (breadth)", pd.Series(True, index=L.index))]:
    g = L[mask]
    ci, se = boot(g.edge_true.values, g.day.values)
    slices[lab] = dict(n=int(len(g)), share_of_pool=float(len(g) / len(L)),
                       edge_true=float(g.edge_true.mean()), ci95=ci, se=se,
                       t=float(g.edge_true.mean() / se),
                       significant=bool(abs(g.edge_true.mean() / se) > 1.959964),
                       total_R=float(g.edge_true.sum()))
R["C_constructions"] = slices

json.dump(R, open(f"{OUT}/B1_CONCENTRATION.json", "w"), indent=1)
print(json.dumps(R, indent=1))
