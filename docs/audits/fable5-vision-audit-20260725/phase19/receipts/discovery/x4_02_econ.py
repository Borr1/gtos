#!/usr/bin/env python3
"""x4 step 2 — economics of the headline intra-bar features, with the artifact controls.

Controls that matter:
  * takeable only (born_past_stop removed) -- the W0-capture artifact
  * `entry_is_bar_close` split: 82 %+ of rows enter at the decision bar's own close (at market).
    Level-offset rows carry the born-state artifact; splitting kills it.
  * FILLED-only: a feature that predicts NO FILL books 0.0 R, which flatters it. Decompose.
  * `fill_honest_walk_r` already starts at path bar 1 = [T+1m, T+2m), so a CONFIRM feature
    measured on [T, T+1m) is NOT look-ahead for it. Stated and used deliberately.
"""
from __future__ import annotations
import json, os, sys
import numpy as np
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import x4_lib as X

recs = X.load_joined()
O = X.outcomes(recs)
days = np.array([r["_day"] for r in recs])
take = O["takeable"]
honr = O["honr"]; gross = O["gross"]
hon = O["hon"]
filled = hon != "no_fill"
atmkt = X.col(recs, "entry_is_bar_close") == 1.0
res = {}

res["coverage"] = {
    "pool_rows": 27658, "joined_with_intrabar": len(recs),
    "dropped_thin_bar": 27658 - len(recs),
    "takeable_n": int(take.sum()),
    "entry_is_bar_close_share": float(np.nanmean(atmkt)),
    "filled_share_takeable": float(filled[take].mean()),
    "bar1_share_takeable": float(O["bar1"][take].mean()),
}
print(json.dumps(res["coverage"], indent=1))


def decile_table(x, mask, nb=10, label=""):
    m = mask & np.isfinite(x)
    xv = x[m]
    if m.sum() < 500:
        return None
    qs = np.unique(np.quantile(xv, np.linspace(0, 1, nb + 1)))
    if len(qs) < 4:
        return None
    idx = np.clip(np.searchsorted(qs, x, side="right") - 1, 0, len(qs) - 2)
    out = []
    for b in range(len(qs) - 1):
        s = m & (idx == b)
        if s.sum() < 20:
            continue
        out.append({
            "bin": b, "lo": round(float(qs[b]), 6), "hi": round(float(qs[b + 1]), 6),
            "n": int(s.sum()),
            "honr": round(float(np.nanmean(honr[s])), 5),
            "gross": round(float(np.nanmean(gross[s])), 5),
            "fill_rate": round(float(filled[s].mean()), 4),
            "target_rate": round(float((hon[s] == "target").mean()), 4),
            "stop_rate": round(float((hon[s] == "stop").mean()), 4),
            "bar1_rate": round(float(O["bar1"][s].mean()), 4),
            "honr_filled": round(float(np.nanmean(honr[s & filled])), 5) if (s & filled).sum() > 20 else None,
        })
    return out


HEAD = ["stop_dist_over_bar_range", "target_dist_over_bar_range", "atr16_m15_r",
        "bar_range_over_atr16", "max_min_range_r", "c0_close_fav_r", "c0_fav_r",
        "c0_adv_r", "c0_ret_r", "c0_clv_fav", "clv_fav", "up_min_frac", "net_min_frac",
        "late3_r", "late5_r", "dir_eff", "retrace_from_fav", "vol_late3_share",
        "argmax_fav_pos", "pos_in_prior60_range", "entry_touch_minutes",
        "prior_same_dir_bars", "mkt_at_bar_close_r"]
res["deciles"] = {}
for nm in HEAD:
    x = X.col(recs, nm)
    res["deciles"][nm] = {
        "takeable": decile_table(x, take),
        "takeable_atmkt": decile_table(x, take & atmkt),
        "takeable_filled": decile_table(x, take & filled),
        "takeable_bar1": decile_table(x, take & O["bar1"]),
    }

# ------- correlation of each headline feature with the known born-state artifact -------
mk = X.col(recs, "mkt_at_bar_close_r")
res["corr_with_mkt_artifact"] = {}
for nm in HEAD:
    x = X.col(recs, nm)
    m = take & np.isfinite(x) & np.isfinite(mk)
    if m.sum() > 500:
        res["corr_with_mkt_artifact"][nm] = round(float(np.corrcoef(x[m], mk[m])[0, 1]), 4)

with open(os.path.join(D, "X4_ECON_V1.json"), "w") as f:
    json.dump(res, f, indent=1)

def show(nm, key="takeable"):
    t = res["deciles"][nm][key]
    if not t:
        print(nm, key, "n/a"); return
    print("\n== %s [%s]  corr_with_mkt=%s" % (nm, key, res["corr_with_mkt_artifact"].get(nm)))
    print("  %-3s %10s %10s %6s %8s %8s %6s %6s %6s %9s" % ("bin","lo","hi","n","honR","gross","fill","tgt","stop","honR|fill"))
    for r in t:
        print("  %-3d %10.4f %10.4f %6d %8.4f %8.4f %6.3f %6.3f %6.3f %9s" % (
            r["bin"], r["lo"], r["hi"], r["n"], r["honr"], r["gross"], r["fill_rate"],
            r["target_rate"], r["stop_rate"], r["honr_filled"]))

for nm in ["stop_dist_over_bar_range", "c0_close_fav_r", "atr16_m15_r", "clv_fav",
           "up_min_frac", "late3_r"]:
    show(nm)
show("c0_close_fav_r", "takeable_atmkt")
show("stop_dist_over_bar_range", "takeable_atmkt")
show("c0_close_fav_r", "takeable_filled")
