"""LANE I bridge — does the bar-archive magnitude structure appear in the
estate's OWN labelled candidate population, and does it predict anything the
row model could have used?

`atr14_over_atr50` is one of the 43 recorded predecision features, and Part 2
shows it carries a perfectly monotone, 13/13-year, 24/24-symbol effect on the
SIZE of forward moves.  If that effect is real it must show up here too -- on
outcome MIX and |net R|, not on signed net R.
"""
import json
from pathlib import Path
import numpy as np, pandas as pd

OUT = Path("/tmp/lane_i")
MONTHS = ["feb", "apr", "may", "jun", "jul"]
df = pd.read_parquet(OUT / "pop.parquet")
d = df[df.eligible].copy()
d['status'] = d['lifecycle_label_status'].astype(str)
d['filled'] = d.status.str.startswith('RESOLVED_FILLED')
d['q'] = d.groupby('symbol', observed=True)['atr14_over_atr50'].transform(
    lambda s: pd.qcut(s.rank(method='first'), 5, labels=False, duplicates='drop'))

report = {"schema": "gtos.lane_i.bridge_vol_regime_in_population.v1",
          "conditioner": "atr14_over_atr50 (one of the 43 recorded predecision features), "
                         "quintiles formed within symbol"}
rows = []
f = d[d.filled].copy()
f['y'] = f['terminal_net_r'].astype(float)
for m in MONTHS + ["ALL"]:
    g = f if m == "ALL" else f[f.month == m]
    for q in range(5):
        s = g[g.q == q]
        if len(s) < 200:
            continue
        rows.append({
            "month": m, "quintile": int(q), "n": int(len(s)),
            "median_atr14_over_atr50": round(float(s['atr14_over_atr50'].median()), 4),
            "mean_net_r": round(float(s.y.mean()), 5),
            "mean_abs_net_r": round(float(s.y.abs().mean()), 5),
            "sd_net_r": round(float(s.y.std()), 5),
            "target_rate": round(float((s.status == 'RESOLVED_FILLED_TARGET').mean()), 5),
            "stop_rate": round(float((s.status == 'RESOLVED_FILLED_STOP').mean()), 5),
            "time_stop_rate": round(float((s.status == 'RESOLVED_FILLED_TIME_STOP').mean()), 5),
            "mean_cost_r": round(float(s['cost_r'].mean()), 5),
        })
report['filled_by_quintile'] = rows
# fill rate (a LIMIT order's chance of being touched) by the same conditioner
fr = []
for m in MONTHS + ["ALL"]:
    g = d if m == "ALL" else d[d.month == m]
    for q in range(5):
        s = g[g.q == q]
        if len(s) < 200:
            continue
        fr.append({"month": m, "quintile": int(q), "n": int(len(s)),
                   "fill_rate": round(float(s.filled.mean()), 5),
                   "censor_rate": round(float((~s['resolved']).mean()), 5)})
report['fill_rate_by_quintile'] = fr

# stability summary over the five months
tab = pd.DataFrame([r for r in rows if r['month'] != 'ALL'])
piv_abs = tab.pivot(index='month', columns='quintile', values='mean_abs_net_r')
piv_sd = tab.pivot(index='month', columns='quintile', values='sd_net_r')
piv_net = tab.pivot(index='month', columns='quintile', values='mean_net_r')
piv_tgt = tab.pivot(index='month', columns='quintile', values='target_rate')
def summarise(p, name):
    ep = (p[4] - p[0])
    return {"metric": name, "months": len(p),
            "endpoint_q4_minus_q0_by_month": [round(float(x), 5) for x in ep],
            "months_with_pooled_sign": int((np.sign(ep) == np.sign(ep.mean())).sum()),
            "mean_endpoint": round(float(ep.mean()), 5),
            "monotone_months": int(sum(
                all(p.loc[mm, i] >= p.loc[mm, i + 1] for i in range(4)) or
                all(p.loc[mm, i] <= p.loc[mm, i + 1] for i in range(4)) for mm in p.index))}
report['stability'] = [summarise(piv_abs, 'mean_abs_net_r'), summarise(piv_sd, 'sd_net_r'),
                       summarise(piv_net, 'mean_net_r'), summarise(piv_tgt, 'target_rate')]
(OUT / "PART3_BRIDGE_VOL_REGIME.json").write_text(json.dumps(report, indent=1, sort_keys=True))
pd.set_option('display.width', 200)
print(pd.DataFrame([r for r in rows if r['month'] == 'ALL']).to_string(index=False))
print()
for s in report['stability']:
    print("%-16s endpoint(Q4-Q0) mean=%+.5f  sign-stable %d/5  monotone %d/5  by month %s" % (
        s['metric'], s['mean_endpoint'], s['months_with_pooled_sign'], s['monotone_months'],
        s['endpoint_q4_minus_q0_by_month']))
print()
print(pd.DataFrame([r for r in fr if r['month'] == 'ALL']).to_string(index=False))
