#!/usr/bin/env python3
"""B1 — the no-extrapolation statement.

The headline restatement deducts a slippage measured on jun+jul from an edge measured over five
months. That is one transfer short of the adjudication's, but it is still a transfer: the two weakest
edge months (jun +0.0200, jul +0.0172, Lane 1 §1.3) are exactly the months the tick archive covers.

This script removes the last transfer. It recomputes the fair-value edge from the puzzle cache
restricted to the SAME rows the slippage was measured on, and deducts the slippage measured on those
rows, with those rows' own barrier shares. Everything is then in-window and measured.

edge = terminal_net_r + cost_r  (Lane 1's exact identity, LANE1_SUMMARY_V1.json /A_headline/identity)

Writes B1_INWINDOW.json.
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


def boot(v, days, B=4000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float); days = np.asarray(days)
    ud = pd.unique(days); idx = {d: np.where(days == d)[0] for d in ud}
    o = np.empty(B)
    for b in range(B):
        p = rng.choice(len(ud), len(ud), replace=True)
        o[b] = v[np.concatenate([idx[ud[q]] for q in p])].mean()
    return [float(np.quantile(o, .025)), float(np.quantile(o, .975))], float(o.std(ddof=1))


rows = []
for m in ["feb", "apr", "may", "jun", "jul"]:
    for r in pickle.load(gzip.open(CACHE.format(m=m), "rb")):
        st = STATE_OF.get(str(r.get("lifecycle_label_status")))
        if st is None:
            continue
        fam = str(r.get("origin_family"))
        rows.append((m, "LIMIT" if fam in LIMIT_FAMILIES else "MARKET", str(r["trading_day"]),
                     float(r.get("terminal_net_r") or 0.0), float(r.get("cost_r") or 0.0), st))
C = pd.DataFrame(rows, columns=["month", "arm", "day", "net", "cost", "state"])
C["edge"] = C.net + C.cost

R = {"schema": "b1_inwindow_v1",
     "identity_check_pooled_edge": float(C.edge.mean()),
     "lane1_pooled_edge": 0.030867,
     "n": int(len(C))}

# --- per arm, five months (reproduces Lane 1) and jun+jul only ---
for arm in ["LIMIT", "MARKET"]:
    g5 = C[C.arm == arm]
    gj = C[(C.arm == arm) & (C.month.isin(["jun", "jul"]))]
    c5, s5 = boot(g5.edge.values, g5.day.values)
    cj, sj = boot(gj.edge.values, gj.day.values)
    R[arm] = {
        "five_month": dict(n=int(len(g5)), edge=float(g5.edge.mean()), CI95=c5, se=s5,
                           shares={k: float((g5.state == k).mean()) for k in
                                   ["STOP", "TARGET", "TIME_STOP"]}),
        "jun_jul": dict(n=int(len(gj)), edge=float(gj.edge.mean()), CI95=cj, se=sj,
                        shares={k: float((gj.state == k).mean()) for k in
                                ["STOP", "TARGET", "TIME_STOP"]}),
        "by_month": {m: dict(n=int((C[(C.arm == arm) & (C.month == m)]).shape[0]),
                             edge=float(C[(C.arm == arm) & (C.month == m)].edge.mean()))
                     for m in ["feb", "apr", "may", "jun", "jul"]},
    }

# --- the fully in-window restatement ---
legs = {"LIMIT": pd.read_pickle(f"{OUT}/legs_limit.pkl"),
        "MARKET": pd.read_pickle(f"{OUT}/legs_ctrlB_lg_market.pkl")}
for arm in ["LIMIT", "MARKET"]:
    D = legs[arm]
    st = D[(D.state == "STOP") & (D.found_cross == 1)].exit_opt_at_cross_r.mean()
    ts = D[(D.state == "TIME_STOP") & (D.found_cross == 1)].exit_opt_at_cross_r.mean()
    # barrier shares of the MEASURED rows themselves -- no transfer of any kind
    pS = float((D.state == "STOP").mean()); pX = float((D.state == "TIME_STOP").mean())
    ded = float(st * pS + ts * pX)
    e = R[arm]["jun_jul"]
    edge = e["edge"] - ded
    se = float(np.hypot(e["se"], 0.0011))   # deduction SE, conservative (see b1_agg bootstrap)
    R[arm]["FULLY_IN_WINDOW"] = dict(
        note="jun+jul edge minus jun+jul measured slippage at the measured rows' own barrier shares",
        edge_raw=e["edge"], stop_cond=float(st), ts_cond=float(ts), pS=pS, pX=pX,
        deduction=ded, edge_at_tick_truth=edge, se=se, t=edge / se,
        ci95=[edge - 1.959964 * se, edge + 1.959964 * se],
        significant=bool(abs(edge / se) > 1.959964))

json.dump(R, open(f"{OUT}/B1_INWINDOW.json", "w"), indent=1)
print(json.dumps(R, indent=1))
