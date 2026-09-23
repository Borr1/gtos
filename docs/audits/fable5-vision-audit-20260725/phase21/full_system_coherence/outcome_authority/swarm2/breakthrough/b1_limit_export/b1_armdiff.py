#!/usr/bin/env python3
"""B1 — the decision-relevant statistic: the ARM DIFFERENCE at measured cost.

The estate's frozen rule is a CHOICE between arms, not a bet on one arm's absolute level. The
statistic that answers "is the rule trading the wrong half of its own book?" is therefore

    (LIMIT edge - LIMIT measured cost) - (MARKET edge - MARKET measured cost)

paired on trading day, which cancels every common day effect (vol regime, news, spread regime) and
is far more powerful than comparing two absolute levels with overlapping CIs.

Also produces the per-origin-family restatement, since order type is a deterministic function of
family (candidate_funnel_analysis.py:81) and the three LIMIT families have very different slippage.

Writes B1_ARMDIFF.json.
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

rows = []
for m in ["feb", "apr", "may", "jun", "jul"]:
    for r in pickle.load(gzip.open(CACHE.format(m=m), "rb")):
        st = STATE_OF.get(str(r.get("lifecycle_label_status")))
        if st is None:
            continue
        fam = str(r.get("origin_family"))
        rows.append((m, "LIMIT" if fam in LIMIT_FAMILIES else "MARKET", fam,
                     str(r["trading_day"]), float(r.get("terminal_net_r") or 0.0),
                     float(r.get("cost_r") or 0.0), st))
C = pd.DataFrame(rows, columns=["month", "arm", "family", "day", "net", "cost", "state"])
C["edge"] = C.net + C.cost

# measured per-arm conditionals (from the tick walk)
LG = {"LIMIT": pd.read_pickle(f"{OUT}/legs_limit.pkl"),
      "MARKET": pd.read_pickle(f"{OUT}/legs_ctrlB_lg_market.pkl")}
COND = {}
for a, D in LG.items():
    COND[a] = dict(
        STOP=float(D[(D.state == "STOP") & (D.found_cross == 1)].exit_opt_at_cross_r.mean()),
        TARGET=0.0,   # resting TP limit fills at the level -- credit correctly declined
        TIME_STOP=float(D[(D.state == "TIME_STOP") & (D.found_cross == 1)].exit_opt_at_cross_r.mean()))
# per-family STOP / TIME_STOP conditionals within the LIMIT arm
FAMCOND = {}
D = LG["LIMIT"]
for fam, g in D.groupby("family"):
    s = g[(g.state == "STOP") & (g.found_cross == 1)]
    t = g[(g.state == "TIME_STOP") & (g.found_cross == 1)]
    FAMCOND[fam] = dict(STOP=float(s.exit_opt_at_cross_r.mean()) if len(s) else 0.0,
                        TARGET=0.0,
                        TIME_STOP=float(t.exit_opt_at_cross_r.mean()) if len(t) else 0.0,
                        n_stop=int(len(s)))

# charge every row its own state's measured conditional -> a per-row net edge
C["charge"] = [COND[a][s] for a, s in zip(C.arm, C.state)]
C["edge_true"] = C.edge - C.charge

R = {"schema": "b1_armdiff_v1", "conditionals": COND, "family_conditionals": FAMCOND,
     "note": "charge is applied per row at its own barrier state; TARGET leg = 0 by design"}


def day_paired_diff(df, B=4000, seed=SEED):
    """Bootstrap the LIMIT-minus-MARKET difference, resampling whole trading days."""
    rng = np.random.default_rng(seed)
    days = pd.unique(df.day.values)
    byday = {}
    for d, g in df.groupby("day"):
        L = g[g.arm == "LIMIT"].edge_true.values
        M = g[g.arm == "MARKET"].edge_true.values
        if len(L) and len(M):
            byday[d] = (L, M)
    days = np.array(list(byday))
    obs_L = np.concatenate([byday[d][0] for d in days])
    obs_M = np.concatenate([byday[d][1] for d in days])
    obs = obs_L.mean() - obs_M.mean()
    out = np.empty(B)
    for b in range(B):
        p = rng.choice(len(days), len(days), replace=True)
        sel = days[p]
        out[b] = (np.concatenate([byday[d][0] for d in sel]).mean()
                  - np.concatenate([byday[d][1] for d in sel]).mean())
    se = float(out.std(ddof=1))
    return dict(n_days=int(len(days)), n_limit=int(len(obs_L)), n_market=int(len(obs_M)),
                limit_edge_true=float(obs_L.mean()), market_edge_true=float(obs_M.mean()),
                diff=float(obs), se=se, t=float(obs / se),
                ci95=[float(np.quantile(out, .025)), float(np.quantile(out, .975))],
                significant=bool(abs(obs / se) > 1.959964))


R["arm_difference_five_month"] = day_paired_diff(C)
R["arm_difference_jun_jul_only"] = day_paired_diff(C[C.month.isin(["jun", "jul"])])
R["arm_difference_by_month"] = {m: day_paired_diff(C[C.month == m], B=2000)
                                for m in ["feb", "apr", "may", "jun", "jul"]}

# ---- per-family restatement inside the LIMIT arm ----
fam_out = {}
for fam in sorted(LIMIT_FAMILIES):
    g = C[C.family == fam].copy()
    if not len(g):
        continue
    fc = FAMCOND.get(fam, COND["LIMIT"])
    g["charge"] = [fc[s] for s in g.state]
    g["edge_true"] = g.edge - g.charge
    rng = np.random.default_rng(SEED)
    days = pd.unique(g.day.values)
    idx = {d: np.where(g.day.values == d)[0] for d in days}
    v = g.edge_true.values
    o = np.empty(4000)
    for b in range(4000):
        p = rng.choice(len(days), len(days), replace=True)
        o[b] = v[np.concatenate([idx[days[q]] for q in p])].mean()
    fam_out[fam] = dict(n=int(len(g)), edge_raw=float(g.edge.mean()),
                        stop_cond=fc["STOP"], ts_cond=fc["TIME_STOP"],
                        n_stop_measured=fc.get("n_stop"),
                        deduction=float(g.charge.mean()),
                        edge_at_tick_truth=float(g.edge_true.mean()),
                        se=float(o.std(ddof=1)),
                        t=float(g.edge_true.mean() / o.std(ddof=1)),
                        ci95=[float(np.quantile(o, .025)), float(np.quantile(o, .975))],
                        significant=bool(abs(g.edge_true.mean() / o.std(ddof=1)) > 1.959964))
R["limit_families_restated"] = fam_out

json.dump(R, open(f"{OUT}/B1_ARMDIFF.json", "w"), indent=1)
print(json.dumps(R, indent=1))
