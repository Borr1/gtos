#!/usr/bin/env python3
"""e-coherence step 5 — THE LIVE-REALISABLE BOOK, and the delay repair measured on it.

L10-X3 measured that the live engine has never placed a limit order and cannot: the
requested entry equals the executable quote on 296/296 captures, action=TRADE_ACTION_DEAL.
So of the four born states only `at_limit` (entry == the last knowable price) describes an
order the live system can emit.  The other 46.1% of the pool is a research fiction.

This measures the at_limit book under the MARKET convention (no touch requirement -- a
market order is filled), at broker-true cost, and prices the one implementable repair in
the whole first-minute cluster: delay the entry by k minutes and enter at market then.
"""
import gzip, json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["B"] = df["plain_walk_r"].astype(float)
N = len(df)
born = df["born"]
al = born == "at_limit"
OUT = {}

sub = df.loc[al].copy()
OUT["live_realisable_book"] = {
    "n": int(len(sub)), "share_of_pool": round(float(al.mean()), 5),
    "GROSS_market_convention": round(float(sub["B"].mean()), 6),
    "GROSS_honest_convention": round(float(sub["H"].mean()), 6),
    "ENGINE_gross": round(float(sub["gross_r"].mean()), 6),
    "cost_frozen": round(float(sub["cost_r"].mean()), 6),
    "cost_TRUE": round(float(sub["cost_r_TRUE"].mean()), 6),
    "NET_at_TRUE": round(float((sub["B"] - sub["cost_r_TRUE"]).mean()), 6),
    "NET_at_frozen": round(float((sub["B"] - sub["cost_r"]).mean()), 6),
    "se": round(float(sub["B"].std(ddof=1) / np.sqrt(len(sub))), 6),
    "win_rate": round(float((sub["B"] > 0).mean()), 5),
}
# same book, cost-gated
for gname, g in (("frozen_gate", sub["gate_both"]),
                 ("true_gate", (sub["true_spread_r"] <= 0.10) & (sub["cost_r_TRUE"] <= 0.15))):
    s2 = sub.loc[g]
    OUT["live_realisable_book"][gname] = {
        "n": int(len(s2)), "GROSS": round(float(s2["B"].mean()), 6),
        "cost_TRUE": round(float(s2["cost_r_TRUE"].mean()), 6),
        "NET_at_TRUE": round(float((s2["B"] - s2["cost_r_TRUE"]).mean()), 6)}

# ------------------------------------------------------------------ DELAY REPAIR
# Re-enter at the CLOSE of path bar k, keeping the same risk distance, same +2R/-1R,
# same 120-bar wall.  Entry price at bar k is fully known at the end of bar k.
keys = set(zip(sub["candidate_id"], sub["decision_time_utc"]))
DELAYS = [0, 1, 2, 3, 5, 10, 15, 30]
acc = {k: [] for k in DELAYS}
pt = {}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    pt[kk] = True
    for k in DELAYS:
        if k >= n:
            acc[k].append(None)
            continue
        base = 0.0 if k == 0 else cls[k - 1]      # entry at close of bar k (1-based bar k)
        r = None
        for i in range(k, n):
            f, a = fav[i] - base, adv[i] - base
            if a <= -1.0:
                r = -1.0
                break
            if f >= 2.0:
                r = 2.0
                break
        if r is None:
            r = cls[n - 1] - base
        acc[k].append(r)

rows = []
base_arr = np.array([x for x in acc[0]], dtype=float)
for k in DELAYS:
    a = np.array([np.nan if x is None else x for x in acc[k]], dtype=float)
    ok = ~np.isnan(a) & ~np.isnan(base_arr)
    d = a[ok] - base_arr[ok]
    rows.append({"delay_min": k, "n": int(ok.sum()),
                 "mean_R": round(float(np.nanmean(a)), 6),
                 "paired_delta_vs_0": round(float(d.mean()), 6),
                 "paired_se": round(float(d.std(ddof=1) / np.sqrt(len(d))), 6),
                 "share_changed": round(float((np.abs(d) > 1e-9).mean()), 4)})
OUT["delay_repair_at_market_cohort"] = rows
OUT["delay_repair_note"] = ("k=0 reproduces the MARKET convention on this cohort; the paired "
                            "delta is the value of simply entering later, same side, same geometry")

# net at broker truth for the best delay
best = max(rows[1:], key=lambda r: r["paired_delta_vs_0"])
a_best = np.array([np.nan if x is None else x for x in acc[best["delay_min"]]], dtype=float)
cost = sub["cost_r_TRUE"].to_numpy(dtype=float)
ok = ~np.isnan(a_best)
OUT["delay_repair_net"] = {
    "best_delay_min": best["delay_min"], "n": int(ok.sum()),
    "GROSS": round(float(a_best[ok].mean()), 6),
    "cost_TRUE": round(float(cost[ok].mean()), 6),
    "NET_at_TRUE": round(float((a_best[ok] - cost[ok]).mean()), 6),
    "NET_at_TRUE_baseline_delay0": round(float((base_arr[ok] - cost[ok]).mean()), 6),
}
json.dump(OUT, open(f"{D}/E_LIVEBOOK_V1.json", "w"), indent=1)
print(json.dumps(OUT["live_realisable_book"], indent=1))
print("--- delay repair, at-market cohort ---")
for r in rows:
    print(f"  k={r['delay_min']:3d}min n={r['n']:6d} mean={r['mean_R']:+.5f} paired={r['paired_delta_vs_0']:+.5f} +-{r['paired_se']:.5f} changed={r['share_changed']:.3f}")
print(json.dumps(OUT["delay_repair_net"]))
