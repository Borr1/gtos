"""LANE I addendum — cross-sectional vs WITHIN-WINDOW ranking skill.

Out of sample the models show a small positive top-decile lift measured across
the whole month (a CROSS-SECTIONAL statistic).  The deployed protocol never
uses that: it ranks candidates INSIDE one decision window and takes the argmax.
This file measures the within-window quantity directly, so the two are not
confused for one another.

For every window with >= 2 resolved candidates:
   lift = net R of the model's argmax  -  mean net R of that window's candidates
The mean of `lift` is exactly the per-trade edge the protocol can harvest.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from collections import defaultdict

OUT = Path("/tmp/lane_i")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
info = json.loads((OUT / "PART1_FEATURE_INFORMATION.json").read_text())
df = pd.read_parquet(OUT / "pop.parquet")
rng = np.random.default_rng(20260811)

# predictions are regenerated only for the frozen ridge (stored on the rows);
# the model arms are re-read from the ladder's own stored selections is not
# possible, so recompute the two cheap arms here from the stored column and
# compare against the exhaustive random baseline.
rows = []
for m in MONTHS:
    d = df[(df.month == m) & df.eligible & df.resolved].reset_index(drop=True)
    y = np.nan_to_num(d['terminal_net_r'].to_numpy(float), nan=0.0)
    w = d['decision_window_id'].astype(str).to_numpy()
    pred = d['pred_month_boundary'].to_numpy(float)
    cost = d['cost_r'].to_numpy(float)
    idx = defaultdict(list)
    for i in range(len(d)):
        idx[w[i]].append(i)
    for name, sc in [("ridge_oos_frozen", pred), ("negative_cost", -cost),
                     ("random", rng.random(len(d)))]:
        lifts, tops, means, ns = [], [], [], []
        for k, ii in idx.items():
            if len(ii) < 2:
                continue
            a = np.asarray(ii)
            j = a[int(np.argmax(sc[a]))]
            lifts.append(y[j] - y[a].mean()); tops.append(y[j]); means.append(y[a].mean()); ns.append(len(a))
        lifts = np.asarray(lifts)
        rows.append({"month": m, "arm": name, "windows": int(len(lifts)),
                     "median_candidates_per_window": int(np.median(ns)),
                     "argmax_mean_net_r": round(float(np.mean(tops)), 5),
                     "window_mean_net_r": round(float(np.mean(means)), 5),
                     "within_window_lift_r": round(float(lifts.mean()), 5),
                     "se_r": round(float(lifts.std(ddof=1) / np.sqrt(len(lifts))), 5),
                     "t": round(float(lifts.mean() / (lifts.std(ddof=1) / np.sqrt(len(lifts)))), 3)})
tab = pd.DataFrame(rows)
pd.set_option('display.width', 200)
print(tab.to_string(index=False))
print()
for a in tab.arm.unique():
    s = tab[tab.arm == a]
    pooled = float(s.within_window_lift_r.mean())
    se = float(np.sqrt((s.se_r ** 2).sum()) / len(s))
    print("%-18s pooled within-window lift %+.5f R/trade  (SE %.5f, t %+.2f)  positive months %d/5"
          % (a, pooled, se, pooled / se, int((s.within_window_lift_r > 0).sum())))
(OUT / "PART1_WITHIN_WINDOW_SKILL.json").write_text(json.dumps(rows, indent=1, sort_keys=True))
