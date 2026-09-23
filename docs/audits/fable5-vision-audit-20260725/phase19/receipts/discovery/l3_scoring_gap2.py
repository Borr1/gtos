#!/usr/bin/env python3
"""l3_scoring_gap2 - four symbols (XAUUSD, XAGUSD, USDJPY, EURUSD) score ge_target on
~2 % of takeable candidates while their own M1 path, with the fill required, reaches the
2R target first on 15-21 %. Every other symbol agrees within ~3 pp. Find what the engine
actually books on those rows.
"""
import json, os
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_pickle(os.path.join(os.environ.get("TMPDIR", "/tmp"), "l3_frame.pkl"))
t = df[df["takeable"]].copy()
SUS = ["XAUUSD", "XAGUSD", "USDJPY", "EURUSD"]
t["grp"] = np.where(t["symbol"].isin(SUS), "SUSPECT4", "OTHER20")

out = {"suspect_symbols": SUS}

# 1. on honest-target rows, what does the engine book?
rows = []
for g, s in t.groupby("grp"):
    ht = s[s["fill_honest_which_came_first"] == "target"]
    rows.append({"group": g, "n": int(len(s)), "n_honest_target": int(len(ht)),
                 "honest_target_rate": round(float(len(ht) / len(s)), 5),
                 "engine_gross_r_mean_on_honest_target": round(float(ht["gross_r"].mean()), 5),
                 "engine_gross_r_median_on_honest_target": round(float(ht["gross_r"].median()), 5),
                 "engine_ge_target_pct_on_honest_target": round(100.0 * float((ht["outcome_band"] == "ge_target").mean()), 3),
                 "engine_band_counts_on_honest_target": ht["outcome_band"].value_counts().astype(int).to_dict(),
                 "fill_honest_walk_r_mean_on_honest_target": round(float(ht["fill_honest_walk_r"].mean()), 5)})
out["on_honest_target_rows"] = rows

# 2. per-symbol: engine gross_r on honest-target rows
per = []
for sym, s in t.groupby("symbol"):
    ht = s[s["fill_honest_which_came_first"] == "target"]
    if len(ht) < 20:
        continue
    per.append({"symbol": sym, "n": int(len(s)), "n_honest_target": int(len(ht)),
                "engine_gross_r_mean": round(float(ht["gross_r"].mean()), 5),
                "engine_gross_r_median": round(float(ht["gross_r"].median()), 5),
                "engine_ge_target_pct": round(100.0 * float((ht["outcome_band"] == "ge_target").mean()), 3),
                "engine_full_stop_pct": round(100.0 * float((ht["outcome_band"] == "full_stop").mean()), 3),
                "engine_partial_loss_pct": round(100.0 * float((ht["outcome_band"] == "partial_loss").mean()), 3),
                "mean_mae_r_before_target": round(float(ht["mae_r_before_target"].mean()), 5),
                "mean_bars_to_target": round(float(ht["bars_to_target"].mean()), 3),
                "cost_r": round(float(ht["cost_r"].mean()), 5)})
per.sort(key=lambda d: d["engine_gross_r_mean"])
out["per_symbol_on_honest_target"] = per

# 3. is it the family mix, or the symbol itself? family x suspect-group
fam = []
for (g, f), s in t.groupby(["grp", "origin_family"]):
    if len(s) < 60:
        continue
    ht = s[s["fill_honest_which_came_first"] == "target"]
    fam.append({"group": g, "family": f, "n": int(len(s)), "n_honest_target": int(len(ht)),
                "honest_target_rate": round(float(len(ht) / len(s)), 5),
                "engine_ge_target_rate": round(float((s["outcome_band"] == "ge_target").mean()), 5),
                "engine_gross_r_on_honest_target": (round(float(ht["gross_r"].mean()), 5) if len(ht) else None),
                "mean_gross_r": round(float(s["gross_r"].mean()), 5)})
out["family_x_group"] = sorted(fam, key=lambda d: (d["family"], d["group"]))

# 4. what is the engine booking instead? mae_r_before_target on suspect vs other
for g, s in t.groupby("grp"):
    ht = s[s["fill_honest_which_came_first"] == "target"]
    out.setdefault("mae_before_target", {})[g] = {
        "n": int(len(ht)),
        "mean_mae_r_before_target": round(float(ht["mae_r_before_target"].mean()), 5),
        "pct_mae_before_target_le_minus1": round(100.0 * float((ht["mae_r_before_target"] <= -1.0 + 1e-9).mean()), 3),
        "mean_bars_to_target": round(float(ht["bars_to_target"].mean()), 3),
        "mean_bars_to_entry_touch": round(float(ht["bars_to_entry_touch"].mean()), 3),
    }

json.dump(out, open(os.path.join(HERE, "l3_SCORING_GAP2_V1.json"), "w"), indent=1, default=str)

for r in rows:
    print("%-9s n=%5d honest_target=%4d (%.4f)  engine books mean=%+.4f median=%+.4f  ge_target on them=%.2f%%" % (
        r["group"], r["n"], r["n_honest_target"], r["honest_target_rate"],
        r["engine_gross_r_mean_on_honest_target"], r["engine_gross_r_median_on_honest_target"],
        r["engine_ge_target_pct_on_honest_target"]))
    print("      engine bands on those rows:", r["engine_band_counts_on_honest_target"])
print("--- per symbol, ENGINE gross_r on rows the honest path says hit target first")
print("%-10s %6s %7s %9s %9s %8s %8s %10s" % ("symbol", "n", "nHonTgt", "engMean", "engMedian", "ge_tgt%", "stop%", "maeBefTgt"))
for r in per:
    print("%-10s %6d %7d %+9.4f %+9.4f %8.2f %8.2f %10.4f" % (
        r["symbol"], r["n"], r["n_honest_target"], r["engine_gross_r_mean"], r["engine_gross_r_median"],
        r["engine_ge_target_pct"], r["engine_full_stop_pct"], r["mean_mae_r_before_target"]))
print("MAE-before-target:", json.dumps(out["mae_before_target"]))
