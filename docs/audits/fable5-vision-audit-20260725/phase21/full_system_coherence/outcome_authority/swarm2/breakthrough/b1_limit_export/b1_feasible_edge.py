#!/usr/bin/env python3
"""B1 — the deepest adversarial cut: does the LIMIT edge survive on fills the TAPE supports?

b1_adversarial.py TEST 2 found that 23.1 % of resolved LIMIT rows have no intrabar tick at which the
booked limit level was actually available on the executable side. Those are not badly-priced trades;
they are trades that should not exist. The engine decides a resting limit was touched using a
MODELLED ask (bid bar + modelled spread), and on this arm the modelled spread is 31 % too small
(0.1022 vs 0.1336 true, b1_entry_residual.py), so it over-triggers.

Charging them slippage is the wrong repair. The right question is what the arm earns on the subset
whose fills the tape supports -- and, because dropping rows on a tape condition can itself be
outcome-correlated, what the DROPPED rows earn, stated next to it.

edge = terminal_gross_r + spread_r  (Lane 1's identity; reproduced against the puzzle cache here)

Writes B1_FEASIBLE_EDGE.json.
"""
from __future__ import annotations

import gzip
import json
import pickle

import numpy as np
import pandas as pd

OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
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


# ---- rebuild the LIMIT rows with their own edge, straight from B1's export ----
rows = []
for mth in ["jun", "jul"]:
    for r in pickle.load(gzip.open(f"{OUT}/b1_limit_{mth}.pkl.gz", "rb")):
        o = r.get("orig") or {}
        if not o.get("fill_time") or o.get("gross") is None:
            continue
        rows.append(dict(key=r["key"], month=mth, day=r["day"], symbol=r["symbol"],
                         family=r["family"], state=o.get("state"),
                         gross=float(o["gross"]), spread_r=float(r["spread_r_row"])))
E = pd.DataFrame(rows)
E["edge"] = E.gross + E.spread_r

R = {"schema": "b1_feasible_edge_v1",
     "control_edge_identity": {
         "b1_export_junjul_limit_edge": float(E.edge.mean()),
         "puzzle_cache_junjul_limit_edge": 0.03673,
         "n": int(len(E))}}

F = pd.read_pickle(f"{OUT}/limit_feasibility.pkl")[["key", "feasible", "intrabar_opt_r"]]
J = E.merge(F, on="key", how="inner")
R["n_joined"] = int(len(J))

LEG = pd.read_pickle(f"{OUT}/legs_limit.pkl")[["key", "state", "found_cross", "exit_opt_at_cross_r"]]
J = J.merge(LEG[["key", "found_cross", "exit_opt_at_cross_r"]], on="key", how="left")


def block(df, label):
    if not len(df):
        return None
    st = df[(df.state == "STOP") & (df.found_cross == 1)].exit_opt_at_cross_r.mean()
    ts = df[(df.state == "TIME_STOP") & (df.found_cross == 1)].exit_opt_at_cross_r.mean()
    pS = float((df.state == "STOP").mean()); pX = float((df.state == "TIME_STOP").mean())
    st = 0.0 if st != st else float(st)
    ts = 0.0 if ts != ts else float(ts)
    ded = st * pS + ts * pX
    raw = float(df.edge.mean())
    ci, se = boot(df.edge.values, df.day.values)
    edge = raw - ded
    return dict(label=label, n=int(len(df)), edge_raw=raw, edge_raw_ci95=ci,
                stop_cond=st, ts_cond=ts, pS=pS, pX=pX, deduction=ded,
                edge_at_tick_truth=edge, se=se, t=edge / se,
                ci95=[edge - 1.959964 * se, edge + 1.959964 * se],
                significant=bool(abs(edge / se) > 1.959964),
                state_mix={k: float((df.state == k).mean())
                           for k in ["STOP", "TARGET", "TIME_STOP"]})


R["ALL"] = block(J, "all resolved LIMIT rows in window")
R["TAPE_SUPPORTED"] = block(J[J.feasible], "fills the tick tape supports (intrabar touch found)")
R["TAPE_UNSUPPORTED"] = block(J[~J.feasible], "fills the tape does NOT support (phantom)")
R["selection_check"] = {
    "note": "if dropping unsupported rows were outcome-neutral the two raw edges would agree",
    "raw_edge_supported": R["TAPE_SUPPORTED"]["edge_raw"],
    "raw_edge_unsupported": R["TAPE_UNSUPPORTED"]["edge_raw"],
    "difference": R["TAPE_SUPPORTED"]["edge_raw"] - R["TAPE_UNSUPPORTED"]["edge_raw"],
    "frac_unsupported": float((~J.feasible).mean()),
    "stop_share_supported": R["TAPE_SUPPORTED"]["state_mix"]["STOP"],
    "stop_share_unsupported": R["TAPE_UNSUPPORTED"]["state_mix"]["STOP"],
}
json.dump(R, open(f"{OUT}/B1_FEASIBLE_EDGE.json", "w"), indent=1)
print(json.dumps(R, indent=1))
