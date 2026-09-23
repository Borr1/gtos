#!/usr/bin/env python3
"""l3_scoring_gap3 - which side of the SUSPECT4 disagreement is broken?

If the ENGINE is mis-walking those four symbols we expect its scored gross_r to lose the
discrete +2.0000 / -1.0000 structure that a first-touch 2R/-1R contract must produce.
If the PATH is wrong we expect the engine to keep that structure and the path to disagree
on stops as well as targets. Measure the discreteness of gross_r per symbol, and the full
engine-vs-path agreement matrix per group.
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
SUS = ["XAUUSD", "XAGUSD", "USDJPY", "EURUSD"]
t["grp"] = np.where(t["symbol"].isin(SUS), "SUSPECT4", "OTHER20")

out = {"suspect": SUS}

# 1. discreteness of the ENGINE's own scored gross_r
per = []
for sym, s in t.groupby("symbol"):
    g = s["gross_r"]
    per.append({"symbol": sym, "n": int(len(s)),
                "pct_gross_eq_2R": round(100.0 * float(((g - 2.0).abs() < 1e-3).mean()), 3),
                "pct_gross_eq_minus1R": round(100.0 * float(((g + 1.0).abs() < 1e-3).mean()), 3),
                "pct_gross_discrete": round(100.0 * float((((g - 2.0).abs() < 1e-3) | ((g + 1.0).abs() < 1e-3)).mean()), 3),
                "n_distinct_gross": int(g.round(4).nunique()),
                "mean_gross_r": round(float(g.mean()), 5),
                "path_target_first_rate": round(float((s["which_came_first"] == "target").mean()), 5),
                "path_stop_first_rate": round(float((s["which_came_first"] == "stop").mean()), 5),
                "engine_ge_target_rate": round(float((s["outcome_band"] == "ge_target").mean()), 5),
                "engine_full_stop_rate": round(float((s["outcome_band"] == "full_stop").mean()), 5)})
per.sort(key=lambda d: d["pct_gross_discrete"])
out["per_symbol_discreteness"] = per

# 2. engine band vs path first-touch agreement, per group
agree = {}
for g, s in t.groupby("grp"):
    ct = pd.crosstab(s["outcome_band"], s["fill_honest_which_came_first"])
    agree[g] = {"n": int(len(s)),
                "matrix": {str(i): {str(c): int(ct.loc[i, c]) for c in ct.columns} for i in ct.index},
                "agree_on_target": int(ct.loc["ge_target", "target"]) if ("ge_target" in ct.index and "target" in ct.columns) else 0,
                "agree_on_stop": int(ct.loc["full_stop", "stop"]) if ("full_stop" in ct.index and "stop" in ct.columns) else 0,
                "engine_stop_path_target": int(ct.loc["full_stop", "target"]) if ("full_stop" in ct.index and "target" in ct.columns) else 0,
                "engine_target_path_stop": int(ct.loc["ge_target", "stop"]) if ("ge_target" in ct.index and "stop" in ct.columns) else 0}
    hs = s[s["fill_honest_which_came_first"] == "stop"]
    agree[g]["on_honest_stop_engine_full_stop_pct"] = round(100.0 * float((hs["outcome_band"] == "full_stop").mean()), 3)
    agree[g]["on_honest_stop_engine_gross_r_mean"] = round(float(hs["gross_r"].mean()), 5)
out["agreement_by_group"] = agree

# 3. size of the repair, stated both ways
s4 = t[t["grp"] == "SUSPECT4"]
ht = s4[s4["fill_honest_which_came_first"] == "target"]
lift_r = float((2.0 - ht["gross_r"]).sum())
out["repair_size"] = {
    "n_suspect4_takeable": int(len(s4)),
    "n_suspect4_honest_target": int(len(ht)),
    "engine_books_mean_r": round(float(ht["gross_r"].mean()), 5),
    "path_says_r": 2.0,
    "total_R_not_booked": round(lift_r, 3),
    "per_suspect4_trade_r": round(lift_r / len(s4), 5),
    "per_takeable_pool_trade_r": round(lift_r / len(t), 5),
    "takeable_gross_now": round(float(t["gross_r"].mean()), 5),
    "takeable_gross_if_path_right": round(float(t["gross_r"].mean()) + lift_r / len(t), 5),
    "suspect4_gross_now": round(float(s4["gross_r"].mean()), 5),
    "suspect4_gross_if_path_right": round(float(s4["gross_r"].mean()) + lift_r / len(s4), 5),
}
# 4. the reverse check: on honest-STOP rows does the engine over- or under-book on SUSPECT4?
hs4 = s4[s4["fill_honest_which_came_first"] == "stop"]
ho = t[(t["grp"] == "OTHER20") & (t["fill_honest_which_came_first"] == "stop")]
out["honest_stop_side"] = {
    "SUSPECT4": {"n": int(len(hs4)), "engine_gross_r_mean": round(float(hs4["gross_r"].mean()), 5),
                 "pct_engine_full_stop": round(100.0 * float((hs4["outcome_band"] == "full_stop").mean()), 3)},
    "OTHER20": {"n": int(len(ho)), "engine_gross_r_mean": round(float(ho["gross_r"].mean()), 5),
                "pct_engine_full_stop": round(100.0 * float((ho["outcome_band"] == "full_stop").mean()), 3)},
}
json.dump(out, open(os.path.join(HERE, "l3_SCORING_GAP3_V1.json"), "w"), indent=1, default=str)

print("%-10s %6s %9s %10s %10s %9s %9s %9s" % ("symbol", "n", "disc%", "at+2R%", "at-1R%", "nDistinct", "engTgt%", "pathTgt%"))
for r in per:
    print("%-10s %6d %9.2f %10.2f %10.2f %9d %9.2f %9.2f" % (
        r["symbol"], r["n"], r["pct_gross_discrete"], r["pct_gross_eq_2R"], r["pct_gross_eq_minus1R"],
        r["n_distinct_gross"], 100 * r["engine_ge_target_rate"], 100 * r["path_target_first_rate"]))
print("AGREEMENT:")
for g, a in agree.items():
    print("  %-9s n=%5d agree_target=%4d agree_stop=%5d  engineStop/pathTarget=%3d  onHonestStop engine_full_stop=%.1f%% grossR=%+.4f" % (
        g, a["n"], a["agree_on_target"], a["agree_on_stop"], a["engine_stop_path_target"],
        a["on_honest_stop_engine_full_stop_pct"], a["on_honest_stop_engine_gross_r_mean"]))
print("REPAIR:", json.dumps(out["repair_size"]))
print("HONEST-STOP:", json.dumps(out["honest_stop_side"]))
