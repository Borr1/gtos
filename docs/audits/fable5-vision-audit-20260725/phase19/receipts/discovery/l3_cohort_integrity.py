#!/usr/bin/env python3
"""l3_cohort_integrity - is the briefed 'winner' cohort real?

The mission names 3,072 full-target winners. outcome_band comes from gross_r, which is the
pool's own FILL-BLIND convention (W0-F2): it scores path value without requiring the entry
limit to be traded first. This step asks how much of the winner cohort survives (a) the
takeability filter (W0-capture) and (b) the fill requirement, and defines the honest cohorts
every later step of lane l3 uses.
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))

W = df["outcome_band"] == "ge_target"
S = df["outcome_band"] == "full_stop"
T = df["takeable"]
FH = df["fill_honest_which_came_first"]

out = {"pool_rows": int(len(df))}
out["briefed_cohorts"] = {"full_target_n": int(W.sum()), "full_stop_n": int(S.sum())}

# --- (a) takeability
out["takeable_filter"] = {
    "winners_takeable": int((W & T).sum()), "winners_untakeable": int((W & ~T).sum()),
    "stops_takeable": int((S & T).sum()), "stops_untakeable": int((S & ~T).sum()),
    "winner_survival_pct": round(100.0 * (W & T).sum() / W.sum(), 3),
    "stop_survival_pct": round(100.0 * (S & T).sum() / S.sum(), 3),
}

# --- (b) fill honesty inside the winner cohort
wf = df[W]
out["winner_fill_audit"] = {
    "n": int(len(wf)),
    "fill_honest_first_touch": wf["fill_honest_which_came_first"].value_counts(dropna=False).astype(int).to_dict(),
    "entry_never_touched": int((~wf["entry_touched"].astype(bool)).sum()),
    "entry_touched_after_target": int((wf["entry_touched"].astype(bool) & ~wf["entry_touch_before_target"].astype(bool)
                                       & ~wf["entry_touch_same_bar_as_target"].astype(bool)).sum()),
    "mean_gross_r": round(float(wf["gross_r"].mean()), 5),
    "mean_fill_honest_walk_r": round(float(wf["fill_honest_walk_r"].mean()), 5),
}
wt = df[W & T]
out["winner_fill_audit_takeable"] = {
    "n": int(len(wt)),
    "fill_honest_first_touch": wt["fill_honest_which_came_first"].value_counts(dropna=False).astype(int).to_dict(),
    "mean_gross_r": round(float(wt["gross_r"].mean()), 5),
    "mean_fill_honest_walk_r": round(float(wt["fill_honest_walk_r"].mean()), 5),
}

# --- the honest cohorts lane l3 uses from here on
t = df[T].copy()
t["HW"] = (t["fill_honest_which_came_first"] == "target")
t["HS"] = (t["fill_honest_which_came_first"] == "stop")
t["HN"] = ~t["HW"] & ~t["HS"]
out["honest_cohorts_takeable"] = {
    "n_takeable": int(len(t)),
    "honest_target_n": int(t["HW"].sum()), "honest_stop_n": int(t["HS"].sum()),
    "honest_other_n": int(t["HN"].sum()),
    "honest_first_touch_counts": t["fill_honest_which_came_first"].value_counts(dropna=False).astype(int).to_dict(),
    "mean_gross_r": round(float(t["gross_r"].mean()), 5),
    "mean_fill_honest_walk_r": round(float(t["fill_honest_walk_r"].mean()), 5),
    "honest_target_rate": round(float(t["HW"].mean()), 5),
}

# --- overlap between briefed cohort and honest cohort, on takeable
ct = pd.crosstab(t["outcome_band"], t["fill_honest_which_came_first"])
out["band_x_fillhonest_takeable"] = {str(i): {str(c): int(ct.loc[i, c]) for c in ct.columns} for i in ct.index}

# --- the anti-correlation the tree exposed, stated exactly
t["hit"] = (t["outcome_band"] == "ge_target").astype(int)
from scipy import stats
out["target_rate_vs_gross_anticorrelation"] = {
    "note": "Within takeable, does hitting the declared target more often coincide with better gross R?",
    "spearman_hit_vs_gross_r": round(float(stats.spearmanr(t["hit"], t["gross_r"]).statistic), 5),
}
# decile of risk_distance: hit rate vs gross
q = pd.qcut(t["risk_distance_pct_of_price"], 10, labels=False, duplicates="drop")
tab = []
for k, s in t.assign(_q=q).groupby("_q"):
    tab.append({"decile": int(k) + 1, "n": int(len(s)),
                "risk_dist_pct_mean": round(float(s["risk_distance_pct_of_price"].mean()), 5),
                "hit_target_rate": round(float(s["hit"].mean()), 5),
                "full_stop_rate": round(float((s["outcome_band"] == "full_stop").mean()), 5),
                "neither_rate": round(float((s["which_came_first"] == "neither").mean()), 5),
                "gross_r": round(float(s["gross_r"].mean()), 5),
                "fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 5),
                "cost_r": round(float(s["cost_r"].mean()), 5),
                "mfe_r": round(float(s["mfe_r"].mean()), 5)})
out["risk_distance_decile_takeable"] = tab

json.dump(out, open(os.path.join(HERE, "l3_COHORT_INTEGRITY_V1.json"), "w"), indent=1, default=str)

print("briefed  win=%d stop=%d" % (W.sum(), S.sum()))
print("takeable win=%d (%.2f%%)  stop=%d (%.2f%%)" % (
    (W & T).sum(), out["takeable_filter"]["winner_survival_pct"],
    (S & T).sum(), out["takeable_filter"]["stop_survival_pct"]))
print("winner cohort fill-honest first touch:", out["winner_fill_audit"]["fill_honest_first_touch"])
print("winner mean gross_r=%.4f  mean fill_honest_walk_r=%.4f" % (
    out["winner_fill_audit"]["mean_gross_r"], out["winner_fill_audit"]["mean_fill_honest_walk_r"]))
print("takeable honest: target=%d stop=%d other=%d  honest_target_rate=%.5f" % (
    out["honest_cohorts_takeable"]["honest_target_n"], out["honest_cohorts_takeable"]["honest_stop_n"],
    out["honest_cohorts_takeable"]["honest_other_n"], out["honest_cohorts_takeable"]["honest_target_rate"]))
print("spearman(hit_target, gross_r) on takeable = %.5f" % out["target_rate_vs_gross_anticorrelation"]["spearman_hit_vs_gross_r"])
print(" d      n  riskD%   hit%  stop% neither%   gross    fhw    cost    mfe")
for r in tab:
    print(" %2d %6d %7.4f %6.2f %6.2f %8.2f %+7.4f %+6.4f %6.4f %6.3f" % (
        r["decile"], r["n"], r["risk_dist_pct_mean"], 100 * r["hit_target_rate"], 100 * r["full_stop_rate"],
        100 * r["neither_rate"], r["gross_r"], r["fill_honest_walk_r"], r["cost_r"], r["mfe_r"]))
