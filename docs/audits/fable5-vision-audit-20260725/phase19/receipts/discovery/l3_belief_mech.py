#!/usr/bin/env python3
"""l3_belief_mech - WHY is the engine's belief inverted on the full-target rate?
Hypothesis: candidate_probability is not a probability of winning, it is an inverse proxy
for how much the instrument MOVES relative to its own stop distance. High belief =>
wide stop relative to realised volatility => neither target nor stop inside the 2 h horizon."""
import json, os
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR","/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["neither"] = (t["which_came_first"] == "neither").astype(int)
t["abs_r_end"] = t["r_at_path_end"].abs()
t["excursion_total_r"] = t["mfe_r"] - t["mae_r"]

rows = []
for b in ("candidate_probability","expected_net_r","cost_r"):
    q = pd.qcut(t[b], 10, labels=False, duplicates="drop")
    g = t.assign(_q=q).groupby("_q")
    tab = [{"decile": int(k)+1, "n": int(len(s)),
            "pred": round(float(s[b].mean()),5),
            "neither_rate": round(float(s["neither"].mean()),4),
            "hit_target": round(float((s["outcome_band"]=="ge_target").mean()),4),
            "full_stop": round(float((s["outcome_band"]=="full_stop").mean()),4),
            "mfe_r": round(float(s["mfe_r"].mean()),4),
            "mae_r": round(float(s["mae_r"].mean()),4),
            "excursion_r": round(float(s["excursion_total_r"].mean()),4),
            "risk_dist_pct": round(float(s["risk_distance_pct_of_price"].mean()),5),
            "gross_r": round(float(s["gross_r"].mean()),4)} for k,s in g]
    rows.append((b, tab))

drv = {}
for x in ("risk_distance_pct_of_price","log_risk_distance_pct","cost_r","spread_r","implied_target_r",
          "abs_entry_offset_r","source_bound_signal_r","execution_fill_probability","fill_probability"):
    m = t[["candidate_probability", x]].dropna()
    drv[x] = {"n": int(len(m)), "spearman_with_candidate_probability": round(float(stats.spearmanr(m["candidate_probability"], m[x]).statistic),5)}

ex = {}
for x in ("excursion_total_r","mfe_r","neither"):
    m = t[["candidate_probability", x]].dropna()
    ex[x] = {"n": int(len(m)), "spearman": round(float(stats.spearmanr(m["candidate_probability"], m[x]).statistic),5)}

# partial: does belief predict target-hit WITHIN a movement stratum?
t["exc_bin"] = pd.qcut(t["excursion_total_r"], 5, labels=False, duplicates="drop")
within = []
for k, s in t.groupby("exc_bin"):
    qq = pd.qcut(s["candidate_probability"], 5, labels=False, duplicates="drop")
    sub = s.assign(_p=qq).groupby("_p").apply(lambda z: pd.Series({
        "n": len(z), "hit": (z["outcome_band"]=="ge_target").mean(), "gross": z["gross_r"].mean()}),
        include_groups=False)
    within.append({"excursion_quintile": int(k)+1, "n": int(len(s)),
                   "mean_excursion_r": round(float(s["excursion_total_r"].mean()),4),
                   "belief_q1_hit": round(float(sub["hit"].iloc[0]),4),
                   "belief_q5_hit": round(float(sub["hit"].iloc[-1]),4),
                   "belief_q1_gross": round(float(sub["gross"].iloc[0]),4),
                   "belief_q5_gross": round(float(sub["gross"].iloc[-1]),4)})

out = {"decile_mechanism": {b: tab for b, tab in rows}, "belief_drivers": drv,
       "belief_vs_movement": ex, "belief_within_movement_stratum": within,
       "population": "TAKEABLE n=%d" % len(t)}
json.dump(out, open(os.path.join(HERE, "l3_BELIEF_MECHANISM_V1.json"), "w"), indent=1, default=str)

for b, tab in rows:
    print(f"--- {b}")
    print("  d      n     pred  neither   hitTgt  fullStop    mfe     mae   excurs  riskD%   gross")
    for r in tab:
        print(f"  {r['decile']:2d} {r['n']:6d} {r['pred']:8.4f} {r['neither_rate']:8.4f} {r['hit_target']:8.4f} {r['full_stop']:9.4f} {r['mfe_r']:6.3f} {r['mae_r']:7.3f} {r['excursion_r']:8.3f} {r['risk_dist_pct']:7.4f} {r['gross_r']:+7.4f}")
print("DRIVERS(spearman vs candidate_probability):", {k:v["spearman_with_candidate_probability"] for k,v in drv.items()})
print("MOVEMENT:", {k:v["spearman"] for k,v in ex.items()})
print("WITHIN-MOVEMENT:", json.dumps(within))
