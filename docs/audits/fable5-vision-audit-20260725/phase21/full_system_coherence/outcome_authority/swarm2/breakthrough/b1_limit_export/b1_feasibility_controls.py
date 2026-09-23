#!/usr/bin/env python3
"""B1 — controls on the phantom-fill finding, because it is the finding that decides the lane.

Two ways the 23.1 % "tape does not support this fill" result could be an artifact rather than a
defect, and both are tested here against the tape:

  C1 TIMING.   b1_adversarial.py searches [fill_time, fill_time+60s) -- exactly the M1 bar the engine
               booked. If modelled_fill_time_utc is offset by a bar, real touches sit outside that
               window and read as phantom. Widen the search and watch the feasible fraction: a timing
               artifact collapses, a real defect plateaus.
  C2 DENSITY.  A sparse minute in the tick archive can miss a touch that happened. Stratify by ticks
               in the fill minute and re-run the edge split inside the densest strata, where a missed
               touch is essentially impossible.

Writes B1_FEASIBILITY_CONTROLS.json.
"""
from __future__ import annotations

import gzip
import json
import os
import pickle

import numpy as np
import pandas as pd

TICK = "/Users/borr/GTOSActive/vps-ticks-20260726/ftmo"
MAP = {"NAS100": "US100_cash", "SPX500": "US500_cash", "GER40": "GER40_cash",
       "JP225": "JP225_cash", "UK100": "UK100_cash"}
OUT = "/Users/borr/.claude/jobs/adb9e69b/tmp/b1"
SEED = 20260812
WINDOWS_S = [(0, 60), (0, 120), (-60, 120), (-60, 300), (-300, 600)]

rows = []
for mth in ["jun", "jul"]:
    for r in pickle.load(gzip.open(f"{OUT}/b1_limit_{mth}.pkl.gz", "rb")):
        o = r.get("orig") or {}
        if not o.get("fill_time") or o.get("gross") is None:
            continue
        rows.append(dict(key=r["key"], day=r["day"], symbol=r["symbol"], side=r["side"],
                         risk=r["risk_price"], fill_price=o["fill_price"],
                         fill_time=o["fill_time"], state=o.get("state"),
                         gross=float(o["gross"]), spread_r=float(r["spread_r_row"])))
E = pd.DataFrame(rows)
E["edge"] = E.gross + E.spread_r
E["ft"] = pd.to_datetime(E.fill_time, utc=True)
E["d"] = np.where(E.side == "LONG", 1.0, -1.0)
keep = set(pd.read_pickle(f"{OUT}/legs_limit.pkl").key)          # the in-window measured rows
E = E[E.key.isin(keep)].copy()

res = []
for sym, g in E.groupby("symbol"):
    bs = MAP.get(sym, sym)
    f = f"{TICK}/FTMO_{bs}_ticks_20260618_to_20260726.csv.gz"
    if not os.path.exists(f):
        continue
    t = pd.read_csv(f, usecols=["time_msc", "bid", "ask"])
    bn = pd.to_datetime(t.time_msc / 1000.0, unit="s")
    t["tu"] = (bn - pd.Timedelta(hours=7)).dt.tz_localize(
        "America/New_York", ambiguous=False, nonexistent="shift_forward").dt.tz_convert("UTC")
    t = t.sort_values("tu")
    t = t[(t.ask >= t.bid) & (t.bid > 0)]
    tv = t.tu.values.astype("datetime64[ns]")
    bid = t.bid.values.astype("float64"); ask = t.ask.values.astype("float64")
    n_t = len(tv)
    for r in g.itertuples():
        ftn = np.datetime64(r.ft.tz_localize(None))
        rec = dict(key=r.key)
        for lo, hi in WINDOWS_S:
            a = int(np.searchsorted(tv, ftn + np.timedelta64(lo, "s")))
            z = int(np.searchsorted(tv, ftn + np.timedelta64(hi, "s")))
            if a >= n_t or z <= a:
                rec[f"feas_{lo}_{hi}"] = None
                continue
            best = ask[a:z].min() if r.d > 0 else bid[a:z].max()
            rec[f"feas_{lo}_{hi}"] = bool((best <= r.fill_price + 1e-12) if r.d > 0
                                          else (best >= r.fill_price - 1e-12))
            if (lo, hi) == (0, 60):
                rec["n_ticks"] = int(z - a)
        res.append(rec)
F = pd.DataFrame(res)
J = E.merge(F, on="key", how="inner")

R = {"schema": "b1_feasibility_controls_v1", "n": int(len(J))}

# ---- C1 timing ----
R["C1_timing_widen_search_window"] = {
    f"[{lo}s,{hi}s)": {
        "frac_feasible": float(J[f"feas_{lo}_{hi}"].dropna().mean()),
        "n": int(J[f"feas_{lo}_{hi}"].notna().sum())}
    for lo, hi in WINDOWS_S}

# ---- C2 density-stratified edge split ----
def boot(v, days, B=2000, seed=SEED):
    rng = np.random.default_rng(seed)
    v = np.asarray(v, float); days = np.asarray(days)
    ud = pd.unique(days); idx = {d: np.where(days == d)[0] for d in ud}
    o = np.empty(B)
    for b in range(B):
        p = rng.choice(len(ud), len(ud), replace=True)
        o[b] = v[np.concatenate([idx[ud[q]] for q in p])].mean()
    return float(o.std(ddof=1))

J["dec"] = pd.qcut(J.n_ticks, 10, labels=False, duplicates="drop")
strata = {}
for dec, g in J.groupby("dec"):
    fe = g[g["feas_0_60"] == True]
    ph = g[g["feas_0_60"] == False]
    if len(fe) < 30 or len(ph) < 30:
        continue
    strata[int(dec)] = dict(
        median_ticks=float(g.n_ticks.median()), n=int(len(g)),
        frac_phantom=float((g["feas_0_60"] == False).mean()),
        edge_supported=float(fe.edge.mean()), edge_phantom=float(ph.edge.mean()),
        gap=float(ph.edge.mean() - fe.edge.mean()),
        target_share_supported=float((fe.state == "TARGET").mean()),
        target_share_phantom=float((ph.state == "TARGET").mean()))
R["C2_density_stratified_edge_split"] = strata

top = J[J.dec >= 8]
fe, ph = top[top["feas_0_60"] == True], top[top["feas_0_60"] == False]
R["C2_densest_20pct"] = dict(
    n=int(len(top)), median_ticks=float(top.n_ticks.median()),
    frac_phantom=float((top["feas_0_60"] == False).mean()),
    edge_supported=float(fe.edge.mean()), se_supported=boot(fe.edge.values, fe.day.values),
    edge_phantom=float(ph.edge.mean()), se_phantom=boot(ph.edge.values, ph.day.values),
    gap=float(ph.edge.mean() - fe.edge.mean()),
    target_share_supported=float((fe.state == "TARGET").mean()),
    target_share_phantom=float((ph.state == "TARGET").mean()))

# ---- the strictest version: phantom under the WIDEST search window ----
col = "feas_-300_600"
w = J[J[col].notna()]
fe, ph = w[w[col] == True], w[w[col] == False]
R["strictest_phantom_widest_window"] = dict(
    n=int(len(w)), frac_phantom=float((w[col] == False).mean()),
    edge_supported=float(fe.edge.mean()), edge_phantom=float(ph.edge.mean()) if len(ph) else None,
    n_phantom=int(len(ph)),
    se_supported=boot(fe.edge.values, fe.day.values),
    se_phantom=boot(ph.edge.values, ph.day.values) if len(ph) > 30 else None)

json.dump(R, open(f"{OUT}/B1_FEASIBILITY_CONTROLS.json", "w"), indent=1)
print(json.dumps(R, indent=1))
