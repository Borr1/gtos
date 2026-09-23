#!/usr/bin/env python3
"""e-coherence step 1 — THE ABSTENTION/SELECTION DECOMPOSITION.

Every lane that reports "+X R/trade" from a filter is reporting a mixture of two things:
  ABSTENTION  = -(1 - keep_rate) * mu_pool     (free money iff mu_pool<0 and not trading is free)
  SELECTION   = keep_rate * (mu_kept - mu_pool)(genuine discrimination)
per-opportunity delta = SELECTION + ABSTENTION exactly.

Per TRADE only SELECTION is edge.  This script measures both for every mechanism the
swarm found, on ONE population with ONE convention, so the terms can be compared and
de-double-counted.
"""
import json, pickle
import numpy as np
import pandas as pd

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
OUT = {}

# ---- convention ------------------------------------------------------------
# honest outcome: entry must be traded; a never-traded candidate books exactly 0.0 R
h = df["fill_honest_walk_r"].astype(float)
OUT["null_audit"] = {
    "fill_honest_walk_r_nulls": int(h.isna().sum()),
    "plain_walk_r_nulls": int(df["plain_walk_r"].isna().sum()),
    "entry_touched_false": int((~df["entry_touched"].astype(bool)).sum()),
    "honest_mean_on_untouched": (None if (~df["entry_touched"].astype(bool)).sum() == 0
                                 else float(h[~df["entry_touched"].astype(bool)].mean())),
}
h = h.fillna(0.0)
df["H"] = h
df["B"] = df["plain_walk_r"].astype(float)      # fill-BLIND walk
df["G"] = df["gross_r"].astype(float)           # engine's own scored gross

mu = {k: float(df[k].mean()) for k in ("H", "B", "G")}
OUT["pool_means"] = {"n": int(len(df)), **mu}

MU = mu["H"]
N = len(df)


def decomp(mask, label, col="H"):
    k = int(mask.sum())
    if k == 0:
        return None
    kept = df.loc[mask, col]
    mu_k = float(kept.mean())
    keep_rate = k / N
    per_opp = keep_rate * mu_k
    delta = per_opp - MU
    selection = keep_rate * (mu_k - MU)
    abstention = -(1 - keep_rate) * MU
    return {
        "label": label, "n_kept": k, "keep_rate": round(keep_rate, 6),
        "mu_kept_per_trade": round(mu_k, 6),
        "per_opportunity": round(per_opp, 6),
        "delta_vs_pool": round(delta, 6),
        "SELECTION": round(selection, 6),
        "ABSTENTION": round(abstention, 6),
        "selection_share": round(selection / delta, 4) if abs(delta) > 1e-12 else None,
    }


born = df["born"]
b1 = df["bars_to_entry_touch"] == 1

FILTERS = {
    "M1a_drop_past_stop": born != "past_stop",
    "M1b_drop_marketable": born != "marketable",
    "M1ab_drop_both_stale_adverse": ~born.isin(["past_stop", "marketable"]),
    "M1c_drop_resting_too_keep_at_limit_only": born == "at_limit",
    "M5_refuse_bar1_fills": ~b1,
    "M5_refuse_bar1_AND_drop_past_stop": (~b1) & (born != "past_stop"),
    "M2_cost_gate_as_shipped": df["gate_both"],
    "M2_cost_gate_total_limb_only": df["gate_total"],
    "M2_cost_gate_spread_limb_only": df["gate_spread"],
    "M2_cost_gate_at_corrected_spread_7.3": (df["spread_r"] / 7.3 <= 0.10) & (df["cost_r_d73"] <= 0.15),
    "M4_invert_fill_floor_keep_below_0.45": df["execution_fill_probability"].astype(float) < 0.45,
    "M4_as_shipped_fill_floor_0.45": df["execution_fill_probability"].astype(float) >= 0.45,
    "M4_as_shipped_fill_floor_0.80": df["execution_fill_probability"].astype(float) >= 0.80,
    "STACK_past_stop_then_cost_gate": (born != "past_stop") & df["gate_both"],
    "STACK_past_stop_then_bar1_then_cost": (born != "past_stop") & (~b1) & df["gate_both"],
}
OUT["decomposition"] = {k: decomp(v, k) for k, v in FILTERS.items()}

# ---- the same table on the ENGINE'S scored gross, for comparability with published work
OUT["decomposition_on_engine_gross"] = {k: decomp(v, k, col="G") for k, v in FILTERS.items()}

# ---- born-state census, honest AND blind AND engine, one table
cen = []
for b in ["at_limit", "resting", "marketable", "past_stop", "unanchored"]:
    m = born == b
    if m.sum() == 0:
        continue
    cen.append({
        "born": b, "n": int(m.sum()), "share": round(float(m.mean()), 5),
        "H": round(float(df.loc[m, "H"].mean()), 6),
        "B": round(float(df.loc[m, "B"].mean()), 6),
        "G": round(float(df.loc[m, "G"].mean()), 6),
        "contrib_H": round(float(df.loc[m, "H"].sum() / N), 6),
        "contrib_G": round(float(df.loc[m, "G"].sum() / N), 6),
        "bar1_fill_share": round(float((df.loc[m, "bars_to_entry_touch"] == 1).mean()), 4),
        "mean_mkt_r": round(float(df.loc[m, "mkt_r"].mean()), 4),
        "median_cost_r": round(float(df.loc[m, "cost_r"].median()), 5),
    })
OUT["born_census"] = cen

# ---- THE CRITICAL CROSS-TAB: is "bar-1 fill" the same thing as "stale entry"?
ct = pd.crosstab(born, b1)
OUT["bar1_by_born_counts"] = ct.to_dict()
tab = []
for b in ["at_limit", "resting", "marketable", "past_stop"]:
    for flag in (True, False):
        m = (born == b) & (b1 == flag)
        if m.sum() == 0:
            continue
        tab.append({"born": b, "bar1": bool(flag), "n": int(m.sum()),
                    "H": round(float(df.loc[m, "H"].mean()), 6),
                    "G": round(float(df.loc[m, "G"].mean()), 6)})
OUT["bar1_x_born"] = tab

with open("docs/audits/fable5-vision-audit-20260725/phase19/receipts/discovery/E_DECOMP_V1.json", "w") as fh:
    json.dump(OUT, fh, indent=1)

print(json.dumps({"pool": OUT["pool_means"], "nulls": OUT["null_audit"]}, indent=1))
print("--- born census ---")
for r in cen:
    print(f"{r['born']:11s} n={r['n']:6d} {r['share']:.4f}  H={r['H']:+.4f} B={r['B']:+.4f} G={r['G']:+.4f} bar1={r['bar1_fill_share']:.3f} mkt_r={r['mean_mkt_r']:+.3f}")
print("--- decomposition (honest) ---")
for k, v in OUT["decomposition"].items():
    if v:
        print(f"{k:46s} n={v['n_kept']:6d} keep={v['keep_rate']:.3f} muK={v['mu_kept_per_trade']:+.4f} d={v['delta_vs_pool']:+.4f} SEL={v['SELECTION']:+.4f} ABS={v['ABSTENTION']:+.4f} selsh={v['selection_share']}")
