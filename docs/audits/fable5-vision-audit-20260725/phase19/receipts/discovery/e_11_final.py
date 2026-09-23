#!/usr/bin/env python3
"""e-coherence step 11 — the consolidated, de-double-counted ledger."""
import json, os, pickle, sys
import numpy as np
import pandas as pd

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import w0_ws  # noqa

df = pickle.load(open("/tmp/ecoh/e_base.pkl", "rb"))
df["B"] = df["plain_walk_r"].astype(float)
born = df["born"]
live = born == "at_limit"
N = len(df)
OUT = {}

# ---- where every published mechanism lives: inside or outside the placeable cohort
def where(mask, name):
    n = int(mask.sum())
    return {"mechanism": name, "n_rows": n,
            "share_inside_unplaceable_46pct": (None if n == 0 else round(float((mask & ~live).sum() / n), 5)),
            "n_on_live_cohort": int((mask & live).sum())}


efp = df["execution_fill_probability"].astype(float)
OUT["mechanism_locations"] = [
    where(born == "past_stop", "w0-capture: stop already breached at decision"),
    where(born.isin(["resting", "marketable"]), "L4/L7/W0-F2: entry the market has left"),
    where(efp < 0.80, "L4-F8/L6-F3/L9-F1/L12-F1: below the 0.80 fill floor"),
    where(efp < 0.45, "same four lanes: below the 0.45 fill floor"),
    where(df["setup_dup_count"].astype(float) > 1, "W0-F1/L2-F9/L11: pseudo-replicated rows"),
    where(df["bars_to_entry_touch"] == 1, "L8-F1: entry traded in the first minute"),
    where(df["final_blocker_class"] == "daily_lockout", "the only positive blocker class"),
    where(df["spread_r"] >= 1.0, "L2-F5: stop inside the quoted spread"),
    where(df["symbol"].isin(["NAS100", "SPX500"]), "L10-X5: arithmetically impossible under the spread cap"),
]

# ---- the naive sum vs the honest number
OUT["naive_sum_vs_honest"] = {
    "naive_sum_of_lane_headline_r_per_trade": round(
        0.2776 + 0.11332 + 0.2404 + 0.1266 + 0.1112 + 0.22251 + 0.09512 + 0.473864
        + 0.0455 + 0.0465 + 0.0774 + 0.067 + 0.0157, 5),
    "components_named": ["W0-F2 fiction 0.2776", "w0cap past_stop 0.11332", "L1 fill convention 0.2404",
                         "L1 decline past_stop 0.1266", "L4 staleness 0.1112", "L8 first-minute 0.22251",
                         "L5 cost repair 0.09512", "L10 cost recost 0.473864", "L11 exit contract 0.0455",
                         "L2 trail 0.0465", "L9 fill floor 0.0774", "L7 delay 0.067", "L5/L10 gate 0.0157"],
    "honest_total_measured_here": None,
    "why": "these are not additive: 8 of the 13 are the SAME 46.088% of rows seen from different angles, "
           "2 are accounting corrections that move zero dollars, and 2 reverse sign on the placeable cohort",
}

# ---- the ledger: one population, one convention, incremental
sub = df.loc[live].copy()
lad = []


def push(label, n, gross, cost, note):
    lad.append({"step": label, "n": int(n), "GROSS_R_per_trade": round(float(gross), 6),
                "cost_R_per_trade": round(float(cost), 6),
                "NET_R_per_trade": round(float(gross - cost), 6), "note": note})


push("0 as published (whole pool, engine gross, frozen cost)", N,
     df["gross_r"].mean(), df["cost_r"].mean(), "the number every prior session quotes")
push("1 + broker-true cost (ACCOUNTING ONLY, zero dollars move)", N,
     df["gross_r"].mean(), df["cost_r_TRUE"].mean(), "L10/L5: frozen model is scrambled 0.017x-33.9x per symbol")
push("2 + scope: keep only orders the live engine can place", len(sub),
     sub["B"].mean(), sub["cost_r_TRUE"].mean(), "L10-X3: 296/296 live orders are market orders; 46.088% of rows deleted")
gT = (sub["true_spread_r"] <= 0.10) & (sub["cost_r_TRUE"] <= 0.15)
s2 = sub.loc[gT]
push("3 + broker-true cost gate", len(s2), s2["B"].mean(), s2["cost_r_TRUE"].mean(),
     "discrimination on this cohort is +0.0065 R/trade; the rest is abstention")
OUT["ledger"] = lad

# delay-5 + trail on the gated live cohort, measured together
keys = set(zip(s2["candidate_id"], s2["decision_time_utc"]))
res = {}
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    if n <= 5:
        continue
    base = cls[4]
    peak, r = 0.0, None
    for i in range(5, n):
        f, a = fav[i] - base, adv[i] - base
        lvl = max(peak - 0.25, -1.0) if peak > 0 else -1.0
        if a <= lvl:
            r = lvl
            break
        peak = max(peak, f)
    res[kk] = cls[n - 1] - base if r is None else r
s2 = s2.copy()
s2["_k"] = list(zip(s2["candidate_id"], s2["decision_time_utc"]))
s2["R"] = [res.get(k, np.nan) for k in s2["_k"]]
q = s2.loc[s2["R"].notna()]
push("4 + 5-minute entry delay AND 0.25R trail (both repairs)", len(q),
     q["R"].mean(), q["cost_r_TRUE"].mean(), "the best composed contract this lane can build")
OUT["ledger"] = lad
OUT["final_book"] = {
    "n": int(len(q)),
    "GROSS": round(float(q["R"].mean()), 6),
    "se": round(float(q["R"].std(ddof=1) / np.sqrt(len(q))), 6),
    "t": round(float(q["R"].mean() / (q["R"].std(ddof=1) / np.sqrt(len(q)))), 3),
    "cost_TRUE": round(float(q["cost_r_TRUE"].mean()), 6),
    "NET": round(float((q["R"] - q["cost_r_TRUE"]).mean()), 6),
    "days_positive_of": [int((q.groupby("day")["R"].mean() > 0).sum()), int(q["day"].nunique())],
    "H1_H2": [round(float(q.loc[q["day"] <= "2026-01-15", "R"].mean()), 6),
              round(float(q.loc[q["day"] > "2026-01-15", "R"].mean()), 6)],
}
json.dump(OUT, open(f"{D}/E_FINAL_V1.json", "w"), indent=1)
print("--- where each published mechanism lives ---")
for m in OUT["mechanism_locations"]:
    print(f"  {m['mechanism']:62s} n={m['n_rows']:6d} inUnplaceable={m['share_inside_unplaceable_46pct']} onLive={m['n_on_live_cohort']}")
print("naive sum:", OUT["naive_sum_vs_honest"]["naive_sum_of_lane_headline_r_per_trade"])
print("--- ledger ---")
for l in lad:
    print(f"  {l['step']:56s} n={l['n']:6d} G={l['GROSS_R_per_trade']:+.5f} cost={l['cost_R_per_trade']:.5f} NET={l['NET_R_per_trade']:+.5f}")
print(json.dumps(OUT["final_book"]))
