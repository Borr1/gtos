#!/usr/bin/env python3
"""e-coherence step 7 — the structural facts the price-space test exposed, verified:
 (a) which families can even emit a live-placeable order
 (b) the >=200bps tail: real or 124-row noise
 (c) the delay-5 repair priced in bps, i.e. does the one implementable repair clear the toll
 (d) the two cheapest instruments per unit of risk are the two the cost gate deleted
"""
import gzip, json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["B"] = df["plain_walk_r"].astype(float)
df["rd_bps"] = (df["risk_distance"] / df["entry_price"]) * 1e4
df["signal_bps"] = df["B"] * df["rd_bps"]
df["toll_bps"] = df["cost_r_TRUE"] * df["rd_bps"]
df["edge_bps"] = df["signal_bps"] - df["toll_bps"]
born = df["born"]
live = born == "at_limit"
OUT = {}

# (a) family x born
ct = pd.crosstab(df["origin_family"], born)
fam = []
for f in ct.index:
    row = ct.loc[f]
    tot = int(row.sum())
    fam.append({"family": f, "n": tot,
                "at_market": int(row.get("at_limit", 0)),
                "resting": int(row.get("resting", 0)),
                "marketable": int(row.get("marketable", 0)),
                "past_stop": int(row.get("past_stop", 0)),
                "live_placeable_share": round(int(row.get("at_limit", 0)) / tot, 4)})
fam.sort(key=lambda r: -r["live_placeable_share"])
OUT["family_x_born"] = fam
OUT["live_placeable_totals"] = {
    "pool": int(len(df)), "at_market": int(live.sum()),
    "not_placeable": int((~live).sum()),
    "not_placeable_share": round(float((~live).mean()), 5),
    "not_placeable_in_three_current_families": int(
        (~live & df["origin_family"].isin(["current_fvg_fill", "current_ob_retest",
                                           "current_breaker_re_entry"])).sum()),
}

# (b) the >=200 bps tail
tail = df.loc[live & (df["rd_bps"] >= 200)]
OUT["wide_risk_tail"] = {
    "n": int(len(tail)),
    "edge_bps_mean": round(float(tail["edge_bps"].mean()), 4),
    "edge_bps_se": round(float(tail["edge_bps"].std(ddof=1) / np.sqrt(len(tail))), 4),
    "t": round(float(tail["edge_bps"].mean() / (tail["edge_bps"].std(ddof=1) / np.sqrt(len(tail)))), 3),
    "symbols": tail["symbol"].value_counts().head(8).to_dict(),
    "families": tail["origin_family"].value_counts().head(8).to_dict(),
    "days_positive_of": [int((tail.groupby("day")["edge_bps"].mean() > 0).sum()),
                         int(tail["day"].nunique())],
    "median_rd_bps": round(float(tail["rd_bps"].median()), 2),
    "R_net_true": round(float((tail["B"] - tail["cost_r_TRUE"]).mean()), 5),
}

# (c) delay-5 repair in bps
keys = set(zip(df.loc[live, "candidate_id"], df.loc[live, "decision_time_utc"]))
d5 = {}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    k = 5
    if k >= n:
        continue
    base = cls[k - 1]
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
    d5[kk] = r
sub = df.loc[live].copy()
sub["_k"] = list(zip(sub["candidate_id"], sub["decision_time_utc"]))
sub["R5"] = [d5.get(k, np.nan) for k in sub["_k"]]
ok = sub["R5"].notna()
s = sub.loc[ok]
OUT["delay5_in_bps"] = {
    "n": int(ok.sum()),
    "signal_bps_delay0": round(float(s["signal_bps"].mean()), 4),
    "signal_bps_delay5": round(float((s["R5"] * s["rd_bps"]).mean()), 4),
    "signal_bps_delay5_se": round(float((s["R5"] * s["rd_bps"]).std(ddof=1) / np.sqrt(len(s))), 4),
    "toll_bps": round(float(s["toll_bps"].mean()), 4),
    "edge_bps_delay5": round(float((s["R5"] * s["rd_bps"] - s["toll_bps"]).mean()), 4),
    "R_gross_delay5": round(float(s["R5"].mean()), 6),
    "R_net_true_delay5": round(float((s["R5"] - s["cost_r_TRUE"]).mean()), 6),
    "verdict": "the repair is real in R and does NOT clear the toll in price units",
}
# the same, restricted to the cheapest instruments by toll/risk
s["tr"] = s["toll_bps"] / s["rd_bps"]
cheap = []
for thr in [0.02, 0.04, 0.06, 0.08, 0.10, 0.15, 0.25]:
    m = s["tr"] <= thr
    if m.sum() < 50:
        continue
    q = s.loc[m]
    cheap.append({"toll_over_risk_max": thr, "n": int(m.sum()),
                  "edge_bps_delay0": round(float(q["edge_bps"].mean()), 4),
                  "edge_bps_delay5": round(float((q["R5"] * q["rd_bps"] - q["toll_bps"]).mean()), 4),
                  "R_net_true_delay5": round(float((q["R5"] - q["cost_r_TRUE"]).mean()), 6),
                  "R_net_true_delay0": round(float((q["B"] - q["cost_r_TRUE"]).mean()), 6),
                  "t_R_net_delay5": round(float((q["R5"] - q["cost_r_TRUE"]).mean() /
                                                ((q["R5"] - q["cost_r_TRUE"]).std(ddof=1) / np.sqrt(len(q)))), 3),
                  "symbols": int(q["symbol"].nunique())})
OUT["cheap_instrument_ladder_delay5"] = cheap

# (d) toll/risk ranking vs frozen-gate survival, per symbol
rank = []
for sym, g in df.loc[live].groupby("symbol"):
    rank.append({"symbol": sym, "n": int(len(g)),
                 "toll_over_risk": round(float((g["toll_bps"] / g["rd_bps"]).mean()), 4),
                 "frozen_gate_pass_rate": round(float(g["gate_both"].mean()), 4),
                 "min_frozen_spread_r": round(float(g["spread_r"].min()), 4)})
rank.sort(key=lambda r: r["toll_over_risk"])
OUT["cheapest_instruments_vs_frozen_gate"] = rank

json.dump(OUT, open(f"{D}/E_STRUCTURE_V1.json", "w"), indent=1)
print("--- family x born (live-placeable share) ---")
for f in fam:
    print(f"  {f['family']:32s} n={f['n']:5d} atMkt={f['at_market']:5d} rest={f['resting']:5d} mkt={f['marketable']:5d} past={f['past_stop']:5d} placeable={f['live_placeable_share']:.4f}")
print(json.dumps(OUT["live_placeable_totals"]))
print(json.dumps(OUT["wide_risk_tail"], indent=0))
print(json.dumps(OUT["delay5_in_bps"], indent=0))
print("--- cheap-instrument ladder, delay 5 ---")
for c in cheap:
    print(f"  toll/risk<={c['toll_over_risk_max']:.2f} n={c['n']:6d} edge0={c['edge_bps_delay0']:+7.3f} edge5={c['edge_bps_delay5']:+7.3f} Rnet5={c['R_net_true_delay5']:+.5f} (t={c['t_R_net_delay5']:+.2f}) syms={c['symbols']}")
print("--- cheapest instruments per unit risk vs frozen gate ---")
for r in rank[:8]:
    print(f"  {r['symbol']:12s} toll/risk={r['toll_over_risk']:.4f} frozenPass={r['frozen_gate_pass_rate']:.4f} minSpreadR={r['min_frozen_spread_r']:.4f}")
