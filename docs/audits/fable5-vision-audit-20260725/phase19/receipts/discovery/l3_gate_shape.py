#!/usr/bin/env python3
"""l3_gate_shape - what SHAPE of trade does each live gate keep, and what shape does it throw
away? Measured on the TAKEABLE population (born_past_stop removed) so the answer is about the
gate and not about the untakeable-order artifact."""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR","/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["neither"] = (t["which_came_first"] == "neither").astype(int)
t["hit"] = (t["outcome_band"] == "ge_target").astype(int)
t["stopped"] = (t["outcome_band"] == "full_stop").astype(int)
t["excursion_r"] = t["mfe_r"] - t["mae_r"]

GATES = {
 "spread_cap_0.10 (broker_net_cost_engine.py:859-866)": t["spread_r"] <= 0.10,
 "total_cost_cap_0.15 (broker_net_cost_engine.py:923-927)": t["cost_r"] <= 0.15,
 "BOTH_live_cost_gates": (t["spread_r"] <= 0.10) & (t["cost_r"] <= 0.15),
 "spread_cap_at_7.3x_corrected": (t["spread_r"]/7.3) <= 0.10,
 "spread_cap_at_8.5x_corrected": (t["spread_r"]/8.5) <= 0.10,
 "BOTH_gates_at_7.3x_corrected": ((t["spread_r"]/7.3) <= 0.10) & ((t["cost_r"]-t["spread_r"]+t["spread_r"]/7.3) <= 0.15),
 "scheduler_materialized": t["scheduler_materialization_status"] == "scheduler_option_materialized",
 "selector_action_trade": t["selector_action"] == "trade",
 "effective_order_type_not_none": t["effective_order_type"] != "none",
 "final_blocker_none_or_nonfatal": ~t["final_blocker_class"].isin(["cost_authority"]),
}

def prof(mask, name):
    a, b = t[mask], t[~mask]
    def d(s):
        return {"n": int(len(s)), "share_pct": round(100*len(s)/len(t),3),
                "hit_target_rate": round(float(s["hit"].mean()),5),
                "full_stop_rate": round(float(s["stopped"].mean()),5),
                "neither_rate": round(float(s["neither"].mean()),5),
                "mean_excursion_r": round(float(s["excursion_r"].mean()),4),
                "mean_mfe_r": round(float(s["mfe_r"].mean()),4),
                "mean_gross_r": round(float(s["gross_r"].mean()),5),
                "gross_win_rate": round(float((s["gross_r"]>0).mean()),5),
                "mean_risk_dist_pct": round(float(s["risk_distance_pct_of_price"].mean()),5),
                "median_risk_dist_pct": round(float(s["risk_distance_pct_of_price"].median()),5)}
    return {"gate": name, "KEPT": d(a), "REFUSED": d(b),
            "hit_rate_ratio_refused_over_kept": round(float(b["hit"].mean()/max(1e-9,a["hit"].mean())),4),
            "excursion_ratio_refused_over_kept": round(float(b["excursion_r"].mean()/max(1e-9,a["excursion_r"].mean())),4)}

res = {"population": "TAKEABLE n=%d" % len(t),
       "pool_hit_target_rate": round(float(t["hit"].mean()),5),
       "pool_mean_excursion_r": round(float(t["excursion_r"].mean()),4),
       "gates": [prof(m, n) for n, m in GATES.items()]}
json.dump(res, open(os.path.join(HERE, "l3_GATE_SHAPE_V1.json"), "w"), indent=1, default=str)

print(f"TAKEABLE n={len(t)}  pool hit={t['hit'].mean():.4f}  excursion={res['pool_mean_excursion_r']:.3f}")
print(f"{'gate':46s} {'keptN':>6s} {'kHit':>6s} {'kExc':>6s} {'kGross':>7s} | {'refN':>6s} {'rHit':>6s} {'rExc':>6s} {'rGross':>7s}")
for g in res["gates"]:
    k, r = g["KEPT"], g["REFUSED"]
    print(f"{g['gate'][:46]:46s} {k['n']:6d} {k['hit_target_rate']:6.4f} {k['mean_excursion_r']:6.3f} {k['mean_gross_r']:+7.4f} | {r['n']:6d} {r['hit_target_rate']:6.4f} {r['mean_excursion_r']:6.3f} {r['mean_gross_r']:+7.4f}")
