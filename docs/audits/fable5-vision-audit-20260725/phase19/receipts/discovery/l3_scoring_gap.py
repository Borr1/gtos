#!/usr/bin/env python3
"""l3_scoring_gap - on three symbols the ENGINE's scored outcome and the MEASURED price
path disagree violently: XAUUSD briefed full-target share 5.98 % vs fill-honest 27.28 %.
Establish whether the disagreement is in the engine's gross_r (scoring) or in the path,
per symbol, over the whole takeable population.

gross_r          = opportunity_net_proxy_r + cost_r  -- the ENGINE's scored realized R
which_came_first = first touch of +2R vs -1R on the M1 path, FILL-BLIND
fill_honest_*    = same, but the entry must be traded before the clock starts
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()

rows = []
for sym, s in t.groupby("symbol"):
    if len(s) < 60:
        continue
    eng_tgt = float((s["outcome_band"] == "ge_target").mean())
    path_tgt = float((s["which_came_first"] == "target").mean())
    hon_tgt = float((s["fill_honest_which_came_first"] == "target").mean())
    # of the rows the PATH says hit target, what did the engine score?
    pt = s[s["which_came_first"] == "target"]
    rows.append({
        "symbol": sym, "n": int(len(s)),
        "engine_ge_target_rate": round(eng_tgt, 5),
        "path_target_first_rate": round(path_tgt, 5),
        "honest_target_first_rate": round(hon_tgt, 5),
        "engine_minus_path": round(eng_tgt - path_tgt, 5),
        "mean_gross_r": round(float(s["gross_r"].mean()), 5),
        "mean_fill_honest_walk_r": round(float(s["fill_honest_walk_r"].mean()), 5),
        "mean_plain_walk_r": round(float(s["plain_walk_r"].mean()), 5),
        "gross_minus_plainwalk": round(float((s["gross_r"] - s["plain_walk_r"]).mean()), 5),
        "n_path_target": int(len(pt)),
        "on_path_target_mean_gross_r": (round(float(pt["gross_r"].mean()), 5) if len(pt) else None),
        "on_path_target_engine_scored_ge_target_pct": (round(100.0 * float((pt["outcome_band"] == "ge_target").mean()), 3) if len(pt) else None),
        "mean_mfe_r": round(float(s["mfe_r"].mean()), 5),
        "median_policy_target_r": round(float(s["policy_target_r"].median()), 5),
        "mean_risk_dist_pct": round(float(s["risk_distance_pct_of_price"].mean()), 5),
    })
rows.sort(key=lambda d: d["engine_minus_path"])

# pool-wide reconciliation
recon = {
    "n_takeable": int(len(t)),
    "engine_ge_target_rate": round(float((t["outcome_band"] == "ge_target").mean()), 5),
    "path_target_first_rate": round(float((t["which_came_first"] == "target").mean()), 5),
    "honest_target_first_rate": round(float((t["fill_honest_which_came_first"] == "target").mean()), 5),
    "mean_gross_r": round(float(t["gross_r"].mean()), 5),
    "mean_plain_walk_r": round(float(t["plain_walk_r"].mean()), 5),
    "mean_fill_honest_walk_r": round(float(t["fill_honest_walk_r"].mean()), 5),
}
# cross-tab engine band vs path first touch on the three suspect symbols
susp = {}
for sym in ("XAUUSD", "XAGUSD", "USDJPY", "GER40"):
    s = t[t["symbol"] == sym]
    if not len(s):
        continue
    ct = pd.crosstab(s["outcome_band"], s["which_came_first"])
    susp[sym] = {"n": int(len(s)),
                 "band_x_pathfirst": {str(i): {str(c): int(ct.loc[i, c]) for c in ct.columns} for i in ct.index},
                 "on_path_target_gross_r_quantiles": {
                     q: round(float(s.loc[s["which_came_first"] == "target", "gross_r"].quantile(q)), 5)
                     for q in (0.05, 0.25, 0.5, 0.75, 0.95)} if (s["which_came_first"] == "target").any() else None}

out = {"population": "TAKEABLE", "reconciliation": recon, "per_symbol": rows, "suspect_symbols": susp}
json.dump(out, open(os.path.join(HERE, "l3_SCORING_GAP_V1.json"), "w"), indent=1, default=str)

print("TAKEABLE n=%d  engine ge_target=%.4f  path target-first=%.4f  honest=%.4f" % (
    recon["n_takeable"], recon["engine_ge_target_rate"], recon["path_target_first_rate"], recon["honest_target_first_rate"]))
print("  mean gross_r=%.5f  plain_walk_r=%.5f  fill_honest=%.5f  (gross-plainwalk=%.5f)" % (
    recon["mean_gross_r"], recon["mean_plain_walk_r"], recon["mean_fill_honest_walk_r"],
    recon["mean_gross_r"] - recon["mean_plain_walk_r"]))
print("%-9s %6s %8s %8s %8s %9s %9s %9s %8s" % ("symbol", "n", "engTgt%", "pathTgt%", "honTgt%", "eng-path", "grossR", "plainR", "onPT_gr"))
for r in rows:
    print("%-9s %6d %8.2f %8.2f %8.2f %9.4f %+9.4f %+9.4f %8s" % (
        r["symbol"], r["n"], 100 * r["engine_ge_target_rate"], 100 * r["path_target_first_rate"],
        100 * r["honest_target_first_rate"], r["engine_minus_path"], r["mean_gross_r"],
        r["mean_plain_walk_r"], r["on_path_target_mean_gross_r"]))
