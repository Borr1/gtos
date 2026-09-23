#!/usr/bin/env python3
"""e-coherence step 6 — THE DENOMINATION-FREE TEST.

Every lane argued about R, and R is contaminated: cost_r = cost_price / risk_distance, so
the cost gate is a stop-width filter (L5-F3), the fill model is a distance proxy (L6/L9/L12),
belief tracks quietness (L3-F1), and widening the stop divides gross and cost by the same k
so the sign can never change (L2-F6).  All of that disappears in PRICE units.

signal_bps = R x risk_distance / entry_price x 1e4      (what the trade earned, in bps)
toll_bps   = broker-true (spread + commission + slippage) in bps    (~constant per symbol)

The question no lane asked in this form: on the cohort that could actually exist live
(at-market orders), is there ANY symbol / family / hour where signal_bps > toll_bps?
"""
import json, os, pickle
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["B"] = df["plain_walk_r"].astype(float)
born = df["born"]
OUT = {}

df["rd_bps"] = (df["risk_distance"] / df["entry_price"]) * 1e4
df["signal_bps"] = df["B"] * df["rd_bps"]
df["toll_bps"] = df["cost_r_TRUE"] * df["rd_bps"]
df["edge_bps"] = df["signal_bps"] - df["toll_bps"]

pops = {"POOL_all": pd.Series(True, index=df.index),
        "LIVE_REALISABLE_at_market": born == "at_limit",
        "at_market_ex_index_impossible": (born == "at_limit") & (~df["symbol"].isin(["NAS100", "SPX500"]))}


def blk(m, label):
    s = df.loc[m]
    n = len(s)
    return {"pop": label, "n": n,
            "signal_bps": round(float(s["signal_bps"].mean()), 4),
            "signal_bps_se": round(float(s["signal_bps"].std(ddof=1) / np.sqrt(n)), 4),
            "toll_bps": round(float(s["toll_bps"].mean()), 4),
            "edge_bps": round(float(s["edge_bps"].mean()), 4),
            "median_rd_bps": round(float(s["rd_bps"].median()), 3),
            "R_gross": round(float(s["B"].mean()), 5),
            "R_net_true": round(float((s["B"] - s["cost_r_TRUE"]).mean()), 5)}


OUT["headline"] = [blk(m, k) for k, m in pops.items()]

live = born == "at_limit"
# --- per symbol on the live-realisable cohort
per = []
for sym, g in df.loc[live].groupby("symbol"):
    n = len(g)
    per.append({"symbol": sym, "n": n,
                "signal_bps": round(float(g["signal_bps"].mean()), 4),
                "se": round(float(g["signal_bps"].std(ddof=1) / np.sqrt(n)), 4),
                "toll_bps": round(float(g["toll_bps"].mean()), 4),
                "edge_bps": round(float(g["edge_bps"].mean()), 4),
                "t_edge": round(float(g["edge_bps"].mean() / (g["edge_bps"].std(ddof=1) / np.sqrt(n))), 3),
                "median_rd_bps": round(float(g["rd_bps"].median()), 2),
                "toll_as_share_of_risk": round(float((g["toll_bps"] / g["rd_bps"]).mean()), 4)})
per.sort(key=lambda r: -r["edge_bps"])
OUT["per_symbol_live_realisable"] = per

# --- per family
perf = []
for fam, g in df.loc[live].groupby("origin_family"):
    n = len(g)
    perf.append({"family": fam, "n": n,
                 "signal_bps": round(float(g["signal_bps"].mean()), 4),
                 "toll_bps": round(float(g["toll_bps"].mean()), 4),
                 "edge_bps": round(float(g["edge_bps"].mean()), 4),
                 "t_edge": round(float(g["edge_bps"].mean() / (g["edge_bps"].std(ddof=1) / np.sqrt(n))), 3),
                 "median_rd_bps": round(float(g["rd_bps"].median()), 2)})
perf.sort(key=lambda r: -r["edge_bps"])
OUT["per_family_live_realisable"] = perf

# --- the affordability frontier: does a MINIMUM risk distance help?  (price-space, so this
#     is a real filter, not a denominator trick)
front = []
for thr in [0, 2, 4, 6, 8, 10, 15, 20, 30, 50, 80, 120, 200]:
    m = live & (df["rd_bps"] >= thr)
    if m.sum() < 30:
        continue
    s = df.loc[m]
    front.append({"min_rd_bps": thr, "n": int(m.sum()),
                  "signal_bps": round(float(s["signal_bps"].mean()), 4),
                  "toll_bps": round(float(s["toll_bps"].mean()), 4),
                  "edge_bps": round(float(s["edge_bps"].mean()), 4),
                  "R_net_true": round(float((s["B"] - s["cost_r_TRUE"]).mean()), 5),
                  "toll_over_risk": round(float((s["toll_bps"] / s["rd_bps"]).mean()), 4)})
OUT["min_risk_distance_frontier"] = front

# --- the toll/risk ratio census: how much of the risk taken is eaten by the broker
r = df.loc[live, "toll_bps"] / df.loc[live, "rd_bps"]
OUT["toll_over_risk_census"] = {
    "n": int(live.sum()), "mean": round(float(r.mean()), 5), "median": round(float(r.median()), 5),
    "p10": round(float(r.quantile(0.10)), 5), "p25": round(float(r.quantile(0.25)), 5),
    "p75": round(float(r.quantile(0.75)), 5), "p90": round(float(r.quantile(0.90)), 5),
    "share_over_10pct": round(float((r > 0.10).mean()), 5),
    "share_over_25pct": round(float((r > 0.25).mean()), 5),
    "share_over_50pct": round(float((r > 0.50).mean()), 5),
    "share_over_100pct": round(float((r > 1.0).mean()), 5),
}
json.dump(OUT, open(f"{D}/E_PRICESPACE_V1.json", "w"), indent=1)
for h in OUT["headline"]:
    print(f"{h['pop']:34s} n={h['n']:6d} signal={h['signal_bps']:+.3f}bps +-{h['signal_bps_se']:.3f} toll={h['toll_bps']:.3f} edge={h['edge_bps']:+.3f} rd={h['median_rd_bps']:.1f}bps")
print("--- per symbol (live-realisable), top and bottom ---")
for p in per[:8] + [{"symbol": "...", "n": 0, "signal_bps": 0, "toll_bps": 0, "edge_bps": 0, "t_edge": 0, "median_rd_bps": 0, "se": 0, "toll_as_share_of_risk": 0}] + per[-6:]:
    print(f"  {p['symbol']:12s} n={p['n']:5d} sig={p['signal_bps']:+8.3f} +-{p['se']:6.3f} toll={p['toll_bps']:7.3f} edge={p['edge_bps']:+8.3f} t={p['t_edge']:+6.2f} rd={p['median_rd_bps']:7.2f} toll/risk={p['toll_as_share_of_risk']:.3f}")
print("--- families ---")
for p in perf:
    print(f"  {p['family']:32s} n={p['n']:5d} sig={p['signal_bps']:+7.3f} toll={p['toll_bps']:6.3f} edge={p['edge_bps']:+7.3f} t={p['t_edge']:+6.2f} rd={p['median_rd_bps']:7.2f}")
print("--- min risk-distance frontier ---")
for p in front:
    print(f"  >={p['min_rd_bps']:4d}bps n={p['n']:6d} sig={p['signal_bps']:+7.3f} toll={p['toll_bps']:6.3f} edge={p['edge_bps']:+7.3f} Rnet={p['R_net_true']:+.5f} toll/risk={p['toll_over_risk']:.4f}")
print(json.dumps(OUT["toll_over_risk_census"]))
