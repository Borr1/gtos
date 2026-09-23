"""m2_oos_analyse — the never-read window, tick-true."""
from __future__ import annotations
import glob, json
from collections import defaultdict
import numpy as np

rows, meta = [], {}
for p in sorted(glob.glob("/tmp/m2/oos/*.json")):
    d = json.load(open(p))
    meta[d["symbol"]] = {k: d[k] for k in ("status", "bid_identity_n", "bid_identity_frac",
                                           "n_ticks", "tick_first_utc", "tick_last_utc")}
    rows.extend(d["rows"])
print("rows", len(rows), "symbols", len(meta))


def dayblock_ci(vals, days, draws=4000, seed=23):
    rng = np.random.default_rng(seed)
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    keys = list(by)
    sums = np.array([np.sum(by[k]) for k in keys])
    cnts = np.array([len(by[k]) for k in keys])
    idx = rng.integers(0, len(keys), size=(draws, len(keys)))
    m = sums[idx].sum(1) / cnts[idx].sum(1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m <= 0).mean())


out = {"meta": meta, "n_rows": len(rows)}
grid = {}
for tr in ("1.5", "2"):
    for hm in (120, 240, 1440):
        k = f"{tr}_{hm}"
        sel = [r for r in rows if r.get(f"bar_{k}") is not None and r.get(f"fill_{k}") is not None]
        if not sel:
            continue
        days = [r["day"] for r in sel]
        cell = {"n": len(sel)}
        for a in ("bar", "tbid", "lvl", "fill"):
            v = np.array([r[f"{a}_{k}"] for r in sel if r.get(f"{a}_{k}") is not None])
            cell[a] = float(v.mean())
        for a in ("bar", "fill"):
            v = np.array([r[f"{a}_{k}"] for r in sel])
            lo, hi, p = dayblock_ci(v, days)
            cell[a + "_ci95"] = [lo, hi]; cell[a + "_p_le_0"] = p
        dd = np.array([r[f"fill_{k}"] - r[f"bar_{k}"] for r in sel])
        cell["delta"] = float(dd.mean())
        grid[k] = cell
out["headline_grid"] = grid

K, K2 = "1.5_120", "2_120"
per_sym = {}
for s in sorted(meta):
    sel = [r for r in rows if r["sym"] == s and r.get(f"bar_{K}") is not None
           and r.get(f"fill_{K}") is not None and r.get(f"bar_{K2}") is not None
           and r.get(f"fill_{K2}") is not None]
    if not sel:
        continue
    per_sym[s] = {
        "n": len(sel),
        "median_d_bps": float(np.median([r["d_bps"] for r in sel])),
        "median_spread_bps": float(np.median([r["spread_bps"] for r in sel])),
        "median_spread_over_d": float(np.median([r["spread_over_d"] for r in sel])),
        "long_frac": float(np.mean([r["long"] for r in sel])),
        "bar": float(np.mean([r[f"bar_{K}"] for r in sel])),
        "fill": float(np.mean([r[f"fill_{K}"] for r in sel])),
        "bar_2R": float(np.mean([r[f"bar_{K2}"] for r in sel])),
        "fill_2R": float(np.mean([r[f"fill_{K2}"] for r in sel])),
    }
out["per_instrument"] = per_sym
out["symbols_bar_positive"] = sum(1 for v in per_sym.values() if v["bar"] > 0)
out["symbols_fill_positive"] = sum(1 for v in per_sym.values() if v["fill"] > 0)
out["symbols_bar_positive_2R"] = sum(1 for v in per_sym.values() if v["bar_2R"] > 0)
out["symbols_fill_positive_2R"] = sum(1 for v in per_sym.values() if v["fill_2R"] > 0)

# weekly blocks -> a within-window persistence read
per_wk = defaultdict(list)
for r in rows:
    if r.get(f"bar_{K}") is None or r.get(f"fill_{K}") is None or r.get(f"bar_{K2}") is None or r.get(f"fill_{K2}") is None:
        continue
    y, m, d = (int(x) for x in r["day"].split("-"))
    import datetime as dt
    wk = dt.date(y, m, d).isocalendar()[1]
    per_wk[wk].append(r)
out["per_week"] = {str(w): {"n": len(v),
                            "bar": float(np.mean([r[f"bar_{K}"] for r in v])),
                            "fill": float(np.mean([r[f"fill_{K}"] for r in v])),
                            "bar_2R": float(np.mean([r[f"bar_{K2}"] for r in v])),
                            "fill_2R": float(np.mean([r[f"fill_{K2}"] for r in v]))}
                   for w, v in sorted(per_wk.items())}

# quintiles
sel = [r for r in rows if r.get(f"bar_{K}") is not None and r.get(f"fill_{K}") is not None
       and r.get(f"bar_{K2}") is not None and r.get(f"fill_{K2}") is not None]
db = np.array([r["d_bps"] for r in sel])
qs = np.percentile(db, [20, 40, 60, 80])
qi = np.searchsorted(qs, db, side="right")
quint = {}
for q in range(5):
    sub = [r for r, k in zip(sel, qi) if k == q]
    if not sub:
        continue
    days = [r["day"] for r in sub]
    v = np.array([r[f"fill_{K}"] for r in sub])
    lo, hi, p = dayblock_ci(v, days)
    quint[f"Q{q+1}"] = {"n": len(sub),
                        "median_d_bps": float(np.median([r["d_bps"] for r in sub])),
                        "median_spread_over_d": float(np.median([r["spread_over_d"] for r in sub])),
                        "bar": float(np.mean([r[f"bar_{K}"] for r in sub])),
                        "fill": float(v.mean()), "fill_ci95": [lo, hi], "fill_p_le_0": p,
                        "bar_2R": float(np.mean([r[f"bar_{K2}"] for r in sub])),
                        "fill_2R": float(np.mean([r[f"fill_{K2}"] for r in sub]))}
out["risk_distance_quintiles"] = quint

# exit migration
names = {0: "stop", 1: "target", 2: "path_end"}
mig = defaultdict(int)
sel = [r for r in rows if r.get(f"barcode_{K}") is not None and r.get(f"code_{K}") is not None]
for r in sel:
    mig[f"{names[r[f'barcode_{K}']]}->{names[r[f'code_{K}']]}"] += 1
out["exit_migration"] = dict(sorted(mig.items()))

# accumulation ladder, three units
for tag, pre in (("transacted", "cap_"), ("bid_tape", "capg_"), ("mid", "capm_")):
    acc = {}
    full = [r for r in rows if all(r.get(pre + h) is not None
                                   for h in ("2h", "8h", "24h", "72h", "160h", "320h"))]
    for hh in ("15m", "2h", "8h", "24h", "72h", "160h", "320h"):
        v = np.array([r[pre + hh] for r in full if r.get(pre + hh) is not None])
        acc[hh] = {"n": int(len(v)), "mean_bps": float(v.mean()) if len(v) else None}
    out[f"accumulation_{tag}"] = acc
    out[f"accumulation_{tag}_n_matched"] = len(full)
out["toll_median_spread_bps"] = float(np.median([r["spread_bps"] for r in rows]))

json.dump(out, open("/tmp/m2/M2_OOS_V1.json", "w"), indent=1)
print(json.dumps({"headline_grid": out["headline_grid"],
                  "symbols_bar_positive": out["symbols_bar_positive"],
                  "symbols_fill_positive": out["symbols_fill_positive"],
                  "symbols_bar_positive_2R": out["symbols_bar_positive_2R"],
                  "symbols_fill_positive_2R": out["symbols_fill_positive_2R"],
                  "exit_migration": out["exit_migration"]}, indent=1))
