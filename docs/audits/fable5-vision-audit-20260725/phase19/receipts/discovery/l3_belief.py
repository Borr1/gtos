#!/usr/bin/env python3
"""l3_belief - does the engine's OWN belief predict what happens?
Rank-correlate every belief/forecast field against realized outcome, on three populations
and three realized measures, plus a decile table (predicted vs realized) for each."""
import json, os
import numpy as np, pandas as pd
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR","/tmp"), "l3_frame.pkl"))
df["hit_target"] = (df["outcome_band"] == "ge_target").astype(int)
df["is_full_stop"] = (df["outcome_band"] == "full_stop").astype(int)

BELIEF = ["candidate_probability","candidate_ev_r","expectancy_r","expected_net_r","candidate_confidence",
          "fill_probability","entry_quality_fill_probability","execution_fill_probability",
          "limit_fillability_probability","source_bound_signal_r","cost_r","spread_r",
          "broker_pretrade_diag_expected_cost_r","risk_finalizer_rank","matched_sleeve_count",
          "effective_admission_count","ev_minus_cost_r"]
REAL = ["gross_r","hit_target","is_full_stop","fill_honest_walk_r","mfe_r","plain_walk_r"]
POPS = {"ALL": df, "TAKEABLE": df[df["takeable"]],
        "WIN_VS_STOP": df[df["outcome_band"].isin(["ge_target","full_stop"])],
        "TAKEABLE_WIN_VS_STOP": df[df["takeable"] & df["outcome_band"].isin(["ge_target","full_stop"])]}

out = {"correlations": {}, "deciles": {}, "calibration": {}}
for pn, p in POPS.items():
    out["correlations"][pn] = {}
    for b in BELIEF:
        if b not in p or p[b].notna().sum() < 50: continue
        row = {"n_nonnull": int(p[b].notna().sum()), "n_distinct": int(p[b].nunique())}
        for r in REAL:
            m = p[[b, r]].dropna()
            if len(m) < 50 or m[b].nunique() < 2: continue
            sp = stats.spearmanr(m[b], m[r])
            pe = stats.pearsonr(m[b], m[r])
            row[r] = {"n": int(len(m)), "spearman": round(float(sp.statistic), 5),
                      "spearman_p": float(sp.pvalue), "pearson": round(float(pe.statistic), 5)}
        out["correlations"][pn][b] = row

# decile tables on ALL and TAKEABLE
for pn in ("ALL", "TAKEABLE"):
    p = POPS[pn]; out["deciles"][pn] = {}
    for b in BELIEF:
        s = p[b]
        if s.notna().sum() < 500 or s.nunique() < 10: continue
        try: q = pd.qcut(s, 10, labels=False, duplicates="drop")
        except Exception: continue
        g = p.assign(_q=q).dropna(subset=["_q"]).groupby("_q")
        tab = []
        for k, sub in g:
            tab.append({"decile": int(k)+1, "n": int(len(sub)),
                        "pred_mean": round(float(sub[b].mean()), 6),
                        "pred_min": round(float(sub[b].min()), 6), "pred_max": round(float(sub[b].max()), 6),
                        "realized_gross_r": round(float(sub["gross_r"].mean()), 5),
                        "hit_target_rate": round(float(sub["hit_target"].mean()), 5),
                        "full_stop_rate": round(float(sub["is_full_stop"].mean()), 5),
                        "win_rate_gross_pos": round(float((sub["gross_r"] > 0).mean()), 5)})
        if tab:
            lo, hi = tab[0], tab[-1]
            out["deciles"][pn][b] = {"table": tab,
                "top_minus_bottom_gross_r": round(hi["realized_gross_r"]-lo["realized_gross_r"], 5),
                "top_minus_bottom_hit_rate": round(hi["hit_target_rate"]-lo["hit_target_rate"], 5),
                "monotone_gross": bool(all(tab[i]["realized_gross_r"] <= tab[i+1]["realized_gross_r"] for i in range(len(tab)-1)))}

# probability calibration
for pn in ("ALL", "TAKEABLE"):
    p = POPS[pn]; out["calibration"][pn] = {}
    for b in ("candidate_probability","fill_probability","execution_fill_probability"):
        s = p[b].dropna()
        if len(s) < 500: continue
        sub = p.loc[s.index]
        out["calibration"][pn][b] = {
            "n": int(len(sub)), "mean_predicted": round(float(sub[b].mean()), 6),
            "min_predicted": round(float(sub[b].min()), 6), "max_predicted": round(float(sub[b].max()), 6),
            "realized_gross_win_rate": round(float((sub["gross_r"] > 0).mean()), 6),
            "realized_hit_target_rate": round(float(sub["hit_target"].mean()), 6),
            "overconfidence_vs_gross_win": round(float(sub[b].mean()/max(1e-9,(sub["gross_r"] > 0).mean())), 4),
            "brier_vs_gross_win": round(float(((sub[b]-(sub["gross_r"] > 0).astype(float))**2).mean()), 6),
            "brier_of_base_rate": round(float((((sub["gross_r"]>0).mean()-(sub["gross_r"]>0).astype(float))**2).mean()), 6)}

json.dump(out, open(os.path.join(HERE, "l3_BELIEF_V1.json"), "w"), indent=1, default=str)

print("SPEARMAN(belief, realized gross_r) / (belief, hit_target)")
print(f"{'belief':36s} {'ALL_g':>8s} {'ALL_h':>8s} {'TAKE_g':>8s} {'TAKE_h':>8s} {'n_dist':>7s}")
for b in BELIEF:
    a = out["correlations"]["ALL"].get(b, {}); t = out["correlations"]["TAKEABLE"].get(b, {})
    if not a: continue
    g = lambda d, k: (d.get(k, {}) or {}).get("spearman", float("nan"))
    print(f"{b:36s} {g(a,'gross_r'):8.4f} {g(a,'hit_target'):8.4f} {g(t,'gross_r'):8.4f} {g(t,'hit_target'):8.4f} {a['n_distinct']:7d}")
