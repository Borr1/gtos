#!/usr/bin/env python3
"""l3_profile_deep - decompose the one rule that tops BOTH split-half rankings,
`cost_r > 0.40 AND session_bucket == london`, and describe it in trader terms.

Also: is `london` doing the work, is `cost_r > 0.40` doing the work, or is it the pair?
And what does the cell look like at the honest fill contract and after cost?
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
t["hit"] = (t["outcome_band"] == "ge_target").astype(int)
t["hhit"] = (t["fill_honest_which_came_first"] == "target").astype(int)
H1 = t["utc_dom"] <= 15
LON = t["session_bucket"].astype(str) == "london"
HC = t["cost_r"] > 0.40

def cell(mask, name):
    s = t[mask]
    if not len(s):
        return None
    s1, s2 = s[H1[mask.index][mask]], s[~H1[mask.index][mask]]
    d = {"name": name, "n": int(len(s)),
         "hit_target_rate": round(float(s["hit"].mean()), 5),
         "honest_target_rate": round(float(s["hhit"].mean()), 5),
         "full_stop_rate": round(float((s["outcome_band"] == "full_stop").mean()), 5),
         "neither_rate": round(float((s["which_came_first"] == "neither").mean()), 5),
         "gross_r": round(float(s["gross_r"].mean()), 5),
         "fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 5),
         "gross_win_rate": round(float((s["gross_r"] > 0).mean()), 5),
         "mean_winner_r": round(float(s.loc[s["gross_r"] > 0, "gross_r"].mean()), 5) if (s["gross_r"] > 0).any() else None,
         "mean_loser_r": round(float(s.loc[s["gross_r"] <= 0, "gross_r"].mean()), 5) if (s["gross_r"] <= 0).any() else None,
         "cost_r_mean": round(float(s["cost_r"].mean()), 5),
         "spread_r_mean": round(float(s["spread_r"].mean()), 5),
         "risk_dist_pct_mean": round(float(s["risk_distance_pct_of_price"].mean()), 5),
         "risk_dist_pct_median": round(float(s["risk_distance_pct_of_price"].median()), 5),
         "mfe_r_mean": round(float(s["mfe_r"].mean()), 5),
         "mae_r_mean": round(float(s["mae_r"].mean()), 5),
         "bars_to_target_median": (round(float(s.loc[s["hit"] == 1, "bars_to_target"].median()), 2) if (s["hit"] == 1).any() else None),
         "cand_prob_mean": round(float(s["candidate_probability"].mean()), 5),
         "utc_hour_mode": int(s["utc_hour"].mode().iloc[0]) if len(s) else None,
         "H1": {"n": int(len(s1)), "hit": round(float(s1["hit"].mean()), 5), "gross": round(float(s1["gross_r"].mean()), 5),
                "fh": round(float(s1["fill_honest_walk_r"].mean()), 5)},
         "H2": {"n": int(len(s2)), "hit": round(float(s2["hit"].mean()), 5), "gross": round(float(s2["gross_r"].mean()), 5),
                "fh": round(float(s2["fill_honest_walk_r"].mean()), 5)},
         }
    # net at the frozen cost model and at the 7.3x / 8.5x corrected spread
    corr73 = s["cost_r"] - s["spread_r"] * (1 - 1 / 7.3)
    corr85 = s["cost_r"] - s["spread_r"] * (1 - 1 / 8.5)
    d["net_at_frozen_cost"] = round(float((s["gross_r"] - s["cost_r"]).mean()), 5)
    d["net_at_spread_over_7.3"] = round(float((s["gross_r"] - corr73).mean()), 5)
    d["net_at_spread_over_8.5"] = round(float((s["gross_r"] - corr85).mean()), 5)
    d["families"] = s["origin_family"].value_counts().head(8).astype(int).to_dict()
    d["symbols"] = s["symbol"].value_counts().head(10).astype(int).to_dict()
    d["sides"] = s["side"].astype(str).value_counts().astype(int).to_dict()
    d["hours"] = s["utc_hour"].value_counts().sort_index().astype(int).to_dict()
    d["born_states"] = s["born_state"].value_counts().astype(int).to_dict()
    return d

out = {"population": "TAKEABLE", "n": int(len(t))}
out["cells"] = {}
for nm, m in [("ALL_TAKEABLE", pd.Series(True, index=t.index)),
              ("london_only", LON), ("cost_r>0.40_only", HC),
              ("RULE_cost>0.40_AND_london", HC & LON),
              ("cost>0.40_NOT_london", HC & ~LON),
              ("london_NOT_cost>0.40", LON & ~HC),
              ("neither", ~HC & ~LON)]:
    out["cells"][nm] = cell(m, nm)

# per-family inside the rule, and the rule's own gate status
r = t[HC & LON]
out["rule_detail"] = {
    "n": int(len(r)),
    "share_of_takeable_pct": round(100.0 * len(r) / len(t), 3),
    "pct_refused_by_live_cost_gates": round(100.0 * float(((r["spread_r"] > 0.10) | (r["cost_r"] > 0.15)).mean()), 3),
    "pct_scheduler_materialized": round(100.0 * float((r["scheduler_materialization_status"] == "scheduler_option_materialized").mean()), 3),
    "pct_selector_action_trade": round(100.0 * float((r["selector_action"].astype(str) == "trade").mean()), 3),
    "final_blocker_class": r["final_blocker_class"].astype(str).value_counts().head(6).astype(int).to_dict(),
}
fam = []
for f, s in r.groupby("origin_family"):
    if len(s) < 25: continue
    fam.append({"family": f, "n": int(len(s)),
                "hit": round(float(s["hit"].mean()), 5), "gross": round(float(s["gross_r"].mean()), 5),
                "fh": round(float(s["fill_honest_walk_r"].mean()), 5),
                "H1_n": int((s["utc_dom"] <= 15).sum()), "H2_n": int((s["utc_dom"] > 15).sum()),
                "H1_gross": round(float(s.loc[s["utc_dom"] <= 15, "gross_r"].mean()), 5),
                "H2_gross": round(float(s.loc[s["utc_dom"] > 15, "gross_r"].mean()), 5)})
out["rule_by_family"] = sorted(fam, key=lambda d: -d["n"])
sym = []
for f, s in r.groupby("symbol"):
    if len(s) < 20: continue
    sym.append({"symbol": f, "n": int(len(s)), "hit": round(float(s["hit"].mean()), 5),
                "gross": round(float(s["gross_r"].mean()), 5), "fh": round(float(s["fill_honest_walk_r"].mean()), 5)})
out["rule_by_symbol"] = sorted(sym, key=lambda d: -d["n"])

json.dump(out, open(os.path.join(HERE, "l3_PROFILE_DEEP_V1.json"), "w"), indent=1, default=str)

print("%-30s %6s %7s %7s %8s %8s %9s %9s %8s" % ("cell", "n", "hit%", "hon%", "gross", "fh", "netFroz", "net/7.3", "riskD%"))
for nm, c in out["cells"].items():
    if not c: continue
    print("%-30s %6d %7.2f %7.2f %+8.4f %+8.4f %+9.4f %+9.4f %8.4f" % (
        nm, c["n"], 100 * c["hit_target_rate"], 100 * c["honest_target_rate"], c["gross_r"], c["fill_honest_walk_r"],
        c["net_at_frozen_cost"], c["net_at_spread_over_7.3"], c["risk_dist_pct_mean"]))
c = out["cells"]["RULE_cost>0.40_AND_london"]
print("RULE halves: H1 n=%d hit=%.4f gross=%+.4f fh=%+.4f | H2 n=%d hit=%.4f gross=%+.4f fh=%+.4f" % (
    c["H1"]["n"], c["H1"]["hit"], c["H1"]["gross"], c["H1"]["fh"], c["H2"]["n"], c["H2"]["hit"], c["H2"]["gross"], c["H2"]["fh"]))
print("RULE detail:", json.dumps(out["rule_detail"]))
print("RULE families:", json.dumps(out["rule_by_family"]))
print("RULE symbols:", json.dumps(out["rule_by_symbol"][:10]))
print("RULE hours:", json.dumps(c["hours"]), "sides:", json.dumps(c["sides"]))
print("RULE stats: winRate=%.4f winMean=%.4f lossMean=%.4f mfe=%.3f mae=%.3f bars_to_tgt_med=%s cand_prob=%.4f" % (
    c["gross_win_rate"], c["mean_winner_r"], c["mean_loser_r"], c["mfe_r_mean"], c["mae_r_mean"], c["bars_to_target_median"], c["cand_prob_mean"]))
