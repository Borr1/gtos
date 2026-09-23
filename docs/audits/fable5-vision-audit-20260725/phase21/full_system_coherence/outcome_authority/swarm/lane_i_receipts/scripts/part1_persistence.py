"""LANE I Part 1.4 — cell persistence.

The row-level model failing out of sample does not by itself rule out LEVEL
structure: "the symbol x family cell that paid last month pays this month".
That is the estate's own working hypothesis whenever it proposes a sleeve.
Test it directly on the filled population: does a cell's mean net R in the
months read BEFORE month M predict its mean net R in month M?
"""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import spearmanr

OUT = Path("/tmp/lane_i")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
CELLS = {
    "origin_family": ["origin_family"],
    "symbol": ["symbol"],
    "utc_hour": ["utc_hour"],
    "utc_session": ["utc_session"],
    "side": ["side"],
    "symbol_x_family": ["symbol", "origin_family"],
    "family_x_side": ["origin_family", "side"],
    "family_x_session": ["origin_family", "utc_session"],
    "symbol_x_family_x_side": ["symbol", "origin_family", "side"],
}
MIN_N = 30

df = pd.read_parquet(OUT / "pop.parquet")
d = df[df.eligible & df['lifecycle_label_status'].astype(str).str.startswith('RESOLVED_FILLED')].copy()
d['y'] = d['terminal_net_r'].astype(float)
report = {"schema": "gtos.lane_i.cell_persistence.v1", "min_cell_n": MIN_N,
          "population": "eligible & RESOLVED_FILLED", "rows": int(len(d)), "cells": {}}

for name, keys in CELLS.items():
    pairs, rows = [], []
    for i, m in enumerate(MONTHS[1:], start=1):
        prior = d[d.month.isin(MONTHS[:i])]
        cur = d[d.month == m]
        gp = prior.groupby(keys, observed=True)['y'].agg(['mean', 'size'])
        gc = cur.groupby(keys, observed=True)['y'].agg(['mean', 'size'])
        j = gp.join(gc, lsuffix='_prior', rsuffix='_cur', how='inner')
        j = j[(j['size_prior'] >= MIN_N) & (j['size_cur'] >= MIN_N)]
        if len(j) < 5:
            continue
        rho = float(spearmanr(j['mean_prior'], j['mean_cur']).statistic)
        sign = float(np.mean(np.sign(j['mean_prior']) == np.sign(j['mean_cur'])))
        # economic test: pick the prior-window top tercile of cells, what do they earn now?
        k = max(1, len(j) // 3)
        top = j.sort_values('mean_prior', ascending=False).head(k)
        bot = j.sort_values('mean_prior', ascending=True).head(k)
        wtop = float((top['mean_cur'] * top['size_cur']).sum() / top['size_cur'].sum())
        wbot = float((bot['mean_cur'] * bot['size_cur']).sum() / bot['size_cur'].sum())
        pop = float((j['mean_cur'] * j['size_cur']).sum() / j['size_cur'].sum())
        rows.append({"month": m, "cells": int(len(j)), "spearman_prior_vs_current": round(rho, 4),
                     "sign_persistence": round(sign, 4),
                     "prior_top_tercile_current_mean_r": round(wtop, 5),
                     "prior_bottom_tercile_current_mean_r": round(wbot, 5),
                     "current_population_mean_r": round(pop, 5),
                     "top_minus_bottom_r": round(wtop - wbot, 5),
                     "top_minus_population_r": round(wtop - pop, 5)})
        pairs.append((rho, sign, wtop - wbot, wtop - pop))
    if not rows:
        continue
    arr = np.asarray(pairs)
    report["cells"][name] = {
        "keys": keys, "months_tested": len(rows), "per_month": rows,
        "mean_spearman": round(float(arr[:, 0].mean()), 4),
        "months_with_positive_spearman": int((arr[:, 0] > 0).sum()),
        "mean_sign_persistence": round(float(arr[:, 1].mean()), 4),
        "mean_top_minus_bottom_r": round(float(arr[:, 2].mean()), 5),
        "months_top_beats_bottom": int((arr[:, 2] > 0).sum()),
        "mean_top_minus_population_r": round(float(arr[:, 3].mean()), 5),
        "months_top_beats_population": int((arr[:, 3] > 0).sum()),
    }
    print("%-24s n_mo=%d meanRho=%+.4f pos=%d/%d  top-bot=%+.4f (%d/%d)  top-pop=%+.4f (%d/%d)" % (
        name, len(rows), arr[:, 0].mean(), int((arr[:, 0] > 0).sum()), len(rows),
        arr[:, 2].mean(), int((arr[:, 2] > 0).sum()), len(rows),
        arr[:, 3].mean(), int((arr[:, 3] > 0).sum()), len(rows)), flush=True)

(OUT / "PART1_CELL_PERSISTENCE.json").write_text(json.dumps(report, indent=1, sort_keys=True))
print("DONE")
