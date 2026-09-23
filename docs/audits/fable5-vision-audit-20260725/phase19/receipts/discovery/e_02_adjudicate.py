#!/usr/bin/env python3
"""e-coherence step 2 — adjudicate the cross-lane contradictions by going back to the data.

A1  Is L8's "first-minute fill" the same phenomenon as w0-capture's "born past stop"?
A2  L5 says broker-true cost is +0.09512; L8 says the same repair is -0.0316; L12 says it
    makes selection WORSE.  Which is it?
A6  L3 says the cost gate ANTI-selects (refused hit target 2.87x more often); L8 says the
    cost gate is doing REAL work (+0.00249 vs -0.05486).  Which is it?
"""
import json, pickle
import numpy as np
import pandas as pd

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["H"] = df["fill_honest_walk_r"].astype(float).fillna(0.0)
df["G"] = df["gross_r"].astype(float)
N = len(df)
MU = float(df["H"].mean())
born = df["born"]
b1 = df["bars_to_entry_touch"] == 1
OUT = {}


def stat(m, label, col="H"):
    k = int(m.sum())
    if k == 0:
        return {"label": label, "n": 0}
    x = df.loc[m, col]
    return {"label": label, "n": k, "mean": round(float(x.mean()), 6),
            "se": round(float(x.std(ddof=1) / np.sqrt(k)), 6),
            "hit_target": round(float((df.loc[m, "fill_honest_which_came_first"] == "target").mean()), 5),
            "full_stop": round(float((df.loc[m, "fill_honest_which_came_first"] == "stop").mean()), 5),
            "median_cost_r": round(float(df.loc[m, "cost_r"].median()), 5),
            "median_riskdist_pct": round(float((df.loc[m, "risk_distance"] / df.loc[m, "entry_price"]).abs().median() * 100), 5)}


# =================================================================== A1
ps = born == "past_stop"
OUT["A1_first_minute_vs_past_stop"] = {
    "past_stop_is_subset_of_bar1": {
        "past_stop_n": int(ps.sum()),
        "past_stop_and_bar1": int((ps & b1).sum()),
        "past_stop_not_bar1": int((ps & ~b1).sum()),
        "bar1_n": int(b1.sum()),
        "bar1_not_past_stop": int((b1 & ~ps).sum()),
    },
    "cohorts": [
        stat(b1, "ALL bar-1 fills"),
        stat(b1 & ps, "bar-1 AND past_stop  (w0-capture's artifact)"),
        stat(b1 & ~ps, "bar-1 but NOT past_stop  (L8's residual)"),
        stat(~b1, "not bar-1"),
        stat(~b1 & ~ps, "not bar-1 and not past_stop"),
    ],
    # decompose L8's headline: how much of "refuse bar-1" is just "refuse past-stop"?
    "attribution": {
        "pool_H": round(MU, 6),
        "per_opp_refuse_bar1": round(float(df.loc[~b1, "H"].sum() / N), 6),
        "per_opp_refuse_past_stop_only": round(float(df.loc[~ps, "H"].sum() / N), 6),
        "per_opp_refuse_bar1_given_past_stop_already_gone": round(
            float(df.loc[~b1 & ~ps, "H"].sum() / N), 6),
        "incremental_of_bar1_over_past_stop": round(
            float(df.loc[~b1 & ~ps, "H"].sum() / N) - float(df.loc[~ps, "H"].sum() / N), 6),
    },
}
# and the same on the TRADE denominator, which is what "edge" means
OUT["A1_per_trade"] = {
    "pool_ex_past_stop_mu": round(float(df.loc[~ps, "H"].mean()), 6),
    "ex_past_stop_and_not_bar1_mu": round(float(df.loc[~ps & ~b1, "H"].mean()), 6),
    "ex_past_stop_and_bar1_mu": round(float(df.loc[~ps & b1, "H"].mean()), 6),
    "n_ex_ps_not_bar1": int((~ps & ~b1).sum()),
    "n_ex_ps_bar1": int((~ps & b1).sum()),
}

# =================================================================== A2
# gross vs net at each cost truth, on the SAME admitted sets.
def book(mask, label):
    k = int(mask.sum())
    if k == 0:
        return None
    sub = df.loc[mask]
    return {
        "label": label, "n": k, "keep_rate": round(k / N, 5),
        "GROSS_per_trade": round(float(sub["H"].mean()), 6),
        "NET_frozen_per_trade": round(float((sub["H"] - sub["cost_r"]).mean()), 6),
        "NET_div7.3_per_trade": round(float((sub["H"] - sub["cost_r_d73"]).mean()), 6),
        "GROSS_per_opportunity": round(float(sub["H"].sum() / N), 6),
        "NET73_per_opportunity": round(float((sub["H"] - sub["cost_r_d73"]).sum() / N), 6),
        "mean_cost_r_frozen": round(float(sub["cost_r"].mean()), 6),
        "mean_cost_r_d73": round(float(sub["cost_r_d73"].mean()), 6),
    }


ex = ~ps  # the sane population everyone agrees on
g_frozen = df["gate_both"]
g_corr = (df["spread_r"] / 7.3 <= 0.10) & (df["cost_r_d73"] <= 0.15)
OUT["A2_cost_repair"] = {
    "population": "ex born_past_stop, n=%d" % int(ex.sum()),
    "arms": [
        book(ex, "no gate"),
        book(ex & g_frozen, "FROZEN gate (as shipped)"),
        book(ex & g_corr, "CORRECTED gate (spread/7.3, same 0.10/0.15 thresholds)"),
        book(ex & g_corr & ~g_frozen, "the candidates the repair ADMITS that frozen refused"),
        book(ex & g_frozen & ~g_corr, "the candidates the repair REFUSES that frozen admitted"),
    ],
}

# =================================================================== A6
# L3 measured HIT RATE, L8 measured R.  Show both sides of the same cut, both metrics,
# on both populations, so the sign flip is visible.
rows = []
for popname, pop in (("ALL", pd.Series(True, index=df.index)), ("ex_past_stop", ex),
                     ("ex_past_stop_and_not_bar1", ex & ~b1)):
    for gname, g in (("gate_both", g_frozen), ("spread_limb", df["gate_spread"]),
                     ("total_limb", df["gate_total"])):
        rows.append({"pop": popname, "gate": gname, "side": "KEPT", **stat(pop & g, "")})
        rows.append({"pop": popname, "gate": gname, "side": "REFUSED", **stat(pop & ~g, "")})
OUT["A6_cost_gate_two_metrics"] = rows

with open("docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/E_ADJUDICATE_V1.json", "w") as fh:
    json.dump(OUT, fh, indent=1)

print("=== A1 past_stop vs bar1 ===")
print(json.dumps(OUT["A1_first_minute_vs_past_stop"]["past_stop_is_subset_of_bar1"]))
for c in OUT["A1_first_minute_vs_past_stop"]["cohorts"]:
    print(f"  {c['label']:42s} n={c['n']:6d} H={c['mean']:+.5f} tgt={c['hit_target']:.4f} stop={c['full_stop']:.4f} costr={c['median_cost_r']:.4f}")
print(json.dumps(OUT["A1_first_minute_vs_past_stop"]["attribution"]))
print(json.dumps(OUT["A1_per_trade"]))
print("=== A2 cost repair ===")
for a in OUT["A2_cost_repair"]["arms"]:
    if a:
        print(f"  {a['label']:52s} n={a['n']:6d} G={a['GROSS_per_trade']:+.5f} Nfz={a['NET_frozen_per_trade']:+.5f} N73={a['NET_div7.3_per_trade']:+.5f} cost73={a['mean_cost_r_d73']:.4f}")
print("=== A6 cost gate, two metrics ===")
for r in OUT["A6_cost_gate_two_metrics"]:
    print(f"  {r['pop']:26s} {r['gate']:12s} {r['side']:8s} n={r['n']:6d} H={r['mean']:+.5f} tgtRate={r['hit_target']:.4f} rdist%={r['median_riskdist_pct']:.4f}")
