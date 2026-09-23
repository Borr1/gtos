#!/usr/bin/env python3
"""e-coherence step 10 — NESTING TESTS.  Do the other lanes' mechanisms survive on the
cohort that can actually be traded, or are they properties of the 46% that cannot exist?

T1  the fill-probability inversion (L4-F8, L6-F3, L9-F1, L12-F1) on at-market rows only
T2  pseudo-replication (W0-F1, L2-F9, L11) -- how much of it is inside the dead 46%
T3  the exit contract's cost (L1, L2, L4, L11) on the live-realisable cohort
T4  the cost gate's selection (L3-F2 vs L8-F2) on the live-realisable cohort
T5  the belief layer's inversion (L3-F1) on the live-realisable cohort
"""
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
OUT = {}
efp = df["execution_fill_probability"].astype(float)

# --------------------------------------------------------- T1 fill probability
OUT["T1_fill_probability"] = {
    "pool_distinct_values": int(efp.nunique()),
    "at_market_distinct_values": int(efp[live].nunique()),
    "at_market_value_counts_top5": efp[live].round(6).value_counts().head(5).to_dict(),
    "at_market_share_exactly_0.92": round(float((efp[live] == 0.92).mean()), 5),
    "at_market_min": float(efp[live].min()), "at_market_max": float(efp[live].max()),
    "unplaceable_distinct_values": int(efp[~live].nunique()),
    "unplaceable_min": float(efp[~live].min()), "unplaceable_max": float(efp[~live].max()),
}
for thr in (0.45, 0.70, 0.80):
    for popname, pop in (("POOL", pd.Series(True, index=df.index)), ("LIVE_at_market", live)):
        kept, ref = pop & (efp >= thr), pop & (efp < thr)
        OUT["T1_fill_probability"][f"floor_{thr}_{popname}"] = {
            "n_kept": int(kept.sum()), "n_refused": int(ref.sum()),
            "kept_H": (None if kept.sum() == 0 else round(float(df.loc[kept, "H"].mean()), 6)),
            "refused_H": (None if ref.sum() == 0 else round(float(df.loc[ref, "H"].mean()), 6)),
            "inversion": (None if (kept.sum() == 0 or ref.sum() == 0)
                          else round(float(df.loc[ref, "H"].mean() - df.loc[kept, "H"].mean()), 6)),
        }

# --------------------------------------------------------- T2 pseudo-replication
rep = df["setup_dup_count"].astype(float) > 1
OUT["T2_pseudo_replication"] = {
    "pool_repeat_rows": int(rep.sum()), "pool_share": round(float(rep.mean()), 5),
    "repeats_inside_unplaceable": int((rep & ~live).sum()),
    "repeats_share_inside_unplaceable": round(float((rep & ~live).sum() / rep.sum()), 5),
    "repeat_rows_on_live_cohort": int((rep & live).sum()),
    "live_cohort_repeat_share": round(float((rep & live).sum() / live.sum()), 5),
    "live_B_all": round(float(df.loc[live, "B"].mean()), 6),
    "live_B_first_emission_only": round(float(df.loc[live & df["is_first_emission"].astype(bool), "B"].mean()), 6),
    "dedup_bias_on_live_cohort": round(float(
        df.loc[live & df["is_first_emission"].astype(bool), "B"].mean() - df.loc[live, "B"].mean()), 6),
}

# --------------------------------------------------------- T3 exit contract on live cohort
keys = set(zip(df.loc[live, "candidate_id"], df.loc[live, "decision_time_utc"]))
hold, t2, tr25 = [], [], []
for rp in w0_ws.iter_rpaths():
    kk = (rp["candidate_id"], rp["decision_time_utc"])
    if kk not in keys:
        continue
    fav, adv, cls = rp["fav"], rp["adv"], rp["cls"]
    n = len(cls)
    hold.append(cls[-1])
    r = None
    for i in range(n):
        if adv[i] <= -1.0:
            r = -1.0
            break
        if fav[i] >= 2.0:
            r = 2.0
            break
    t2.append(cls[-1] if r is None else r)
    # 0.25R trail, lagged (honest): trail level set from the PREVIOUS bar's peak
    peak, r2 = 0.0, None
    for i in range(n):
        lvl = peak - 0.25 if peak > 0 else -1.0
        if adv[i] <= max(lvl, -1.0):
            r2 = max(lvl, -1.0)
            break
        peak = max(peak, fav[i])
    tr25.append(cls[-1] if r2 is None else r2)
OUT["T3_exit_on_live_cohort"] = {
    "n": len(hold),
    "INCUMBENT_T2_S1": round(float(np.mean(t2)), 6),
    "HOLD_to_wall": round(float(np.mean(hold)), 6),
    "TRAIL_0.25R": round(float(np.mean(tr25)), 6),
    "incumbent_cost_vs_hold": round(float(np.mean(t2) - np.mean(hold)), 6),
    "best_variant_gain_vs_incumbent": round(float(max(np.mean(hold), np.mean(tr25)) - np.mean(t2)), 6),
    "comparison_L11_incumbent_cost_vs_hold": -0.045504,
}

# --------------------------------------------------------- T4 cost gate on live cohort
sub = df.loc[live]
gT = (sub["true_spread_r"] <= 0.10) & (sub["cost_r_TRUE"] <= 0.15)
for gname, g in (("frozen", sub["gate_both"]), ("broker_true", gT)):
    k, r = sub.loc[g], sub.loc[~g]
    OUT[f"T4_costgate_{gname}_on_live"] = {
        "n_kept": int(len(k)), "kept_B": round(float(k["B"].mean()), 6),
        "n_ref": int(len(r)), "refused_B": round(float(r["B"].mean()), 6),
        "discrimination": round(float(k["B"].mean() - r["B"].mean()), 6),
        "kept_target_rate": round(float((k["which_came_first"] == "target").mean()), 5),
        "refused_target_rate": round(float((r["which_came_first"] == "target").mean()), 5),
        "kept_median_rd_bps": round(float((k["risk_distance"] / k["entry_price"] * 1e4).median()), 3),
        "refused_median_rd_bps": round(float((r["risk_distance"] / r["entry_price"] * 1e4).median()), 3),
    }

# --------------------------------------------------------- T5 belief on live cohort
q = pd.qcut(sub["candidate_probability"].astype(float), 10, labels=False, duplicates="drop")
dec = []
for i in sorted(pd.unique(q.dropna())):
    m = q == i
    dec.append({"decile": int(i) + 1, "n": int(m.sum()),
                "mean_prob": round(float(sub.loc[m, "candidate_probability"].mean()), 5),
                "B": round(float(sub.loc[m, "B"].mean()), 6),
                "target_rate": round(float((sub.loc[m, "which_came_first"] == "target").mean()), 5)})
OUT["T5_belief_deciles_live_cohort"] = dec
OUT["T5_spread"] = {"D1_minus_D10_B": round(dec[0]["B"] - dec[-1]["B"], 6),
                    "D1_minus_D10_target_rate": round(dec[0]["target_rate"] - dec[-1]["target_rate"], 5)}

json.dump(OUT, open(f"{D}/E_NESTING_V1.json", "w"), indent=1)
print("T1:", json.dumps({k: v for k, v in OUT["T1_fill_probability"].items() if not k.startswith("floor")}))
for thr in (0.45, 0.80):
    for p in ("POOL", "LIVE_at_market"):
        print("   floor", thr, p, json.dumps(OUT["T1_fill_probability"][f"floor_{thr}_{p}"]))
print("T2:", json.dumps(OUT["T2_pseudo_replication"]))
print("T3:", json.dumps(OUT["T3_exit_on_live_cohort"]))
print("T4f:", json.dumps(OUT["T4_costgate_frozen_on_live"]))
print("T4t:", json.dumps(OUT["T4_costgate_broker_true_on_live"]))
print("T5:", json.dumps(OUT["T5_spread"]), [f"{d['decile']}:{d['B']:+.4f}" for d in dec])
