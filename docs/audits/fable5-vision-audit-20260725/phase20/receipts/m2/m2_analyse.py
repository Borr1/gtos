"""m2_analyse — the tick-true adjudication of `structural_distance_extreme`."""
from __future__ import annotations
import glob, json, sys
from collections import defaultdict
import numpy as np

W = sorted(glob.glob("/tmp/m2/walks/*.json"))
rows = []
for p in W:
    d = json.load(open(p))
    rows.extend(d["rows"])
print("rows", len(rows))

MONTHS = ("202510", "202511", "202512", "202601", "202602", "202603", "202604")
SYMS = ("XAUUSD", "XAGUSD", "EURUSD", "USDJPY")
ARMS = ("bar", "tbid", "lvl", "fill")


def dayblock_ci(vals, days, draws=4000, seed=17):
    """Day-block bootstrap of the mean."""
    rng = np.random.default_rng(seed)
    by = defaultdict(list)
    for v, d in zip(vals, days):
        by[d].append(v)
    keys = list(by)
    arrs = [np.asarray(by[k]) for k in keys]
    sums = np.array([a.sum() for a in arrs])
    cnts = np.array([len(a) for a in arrs])
    n = len(keys)
    idx = rng.integers(0, n, size=(draws, n))
    s = sums[idx].sum(1)
    c = cnts[idx].sum(1)
    m = s / c
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)), float((m <= 0).mean())


def agg(sel, key):
    v = np.array([r[key] for r in sel if r.get(key) is not None])
    return len(v), (float(v.mean()) if len(v) else None)


out = {}

# ---------------------------------------------------------------- headline grid
grid = {}
for tr in ("1.5", "2"):
    for hm in (120, 240, 1440):
        k = f"{tr}_{hm}"
        cell = {}
        sel = [r for r in rows if r.get(f"bar_{k}") is not None and r.get(f"fill_{k}") is not None]
        days = [r["day"] for r in sel]
        for a in ARMS:
            n, m = agg(sel, f"{a}_{k}")
            cell[a] = {"n": n, "mean": m}
        for a in ("bar", "fill", "lvl"):
            v = np.array([r[f"{a}_{k}"] for r in sel])
            lo, hi, p = dayblock_ci(v, days)
            cell[a].update({"ci95": [lo, hi], "p_le_0": p})
        d = np.array([r[f"fill_{k}"] - r[f"bar_{k}"] for r in sel])
        lo, hi, p = dayblock_ci(d, days)
        cell["delta_fill_minus_bar"] = {"mean": float(d.mean()), "ci95": [lo, hi],
                                        "p_le_0": p, "n": len(d)}
        cell["n_rows"] = len(sel)
        grid[k] = cell
out["headline_grid"] = grid

K = "1.5_120"       # the shipped target; the family's own contract
K2 = "2_120"        # p3 / d1b's contract, for comparability

# ---------------------------------------------------------------- bar==tbid check
sel = [r for r in rows if r.get(f"bar_{K2}") is not None and r.get(f"tbid_{K2}") is not None]
dd = np.array([r[f"bar_{K2}"] - r[f"tbid_{K2}"] for r in sel])
out["intrabar_ordering"] = {
    "n": len(dd), "mean_bar_minus_tickbid": float(dd.mean()),
    "frac_rows_identical": float((np.abs(dd) < 1e-9).mean()),
    "max_abs": float(np.abs(dd).max()),
    "note": "M1 bar walk vs tick walk with BID on every leg; isolates intrabar ordering",
}

# ---------------------------------------------------------------- per instrument
per_sym = {}
for s in SYMS:
    sel = [r for r in rows if r["sym"] == s and r.get(f"bar_{K}") is not None]
    if not sel:
        continue
    days = [r["day"] for r in sel]
    e = {"n": len(sel), "long_frac": float(np.mean([r["long"] for r in sel])),
         "median_d_bps": float(np.median([r["d_bps"] for r in sel])),
         "median_spread_bps": float(np.median([r["spread_bps"] for r in sel])),
         "median_spread_over_d": float(np.median([r["spread_over_d"] for r in sel]))}
    for a in ARMS:
        n, m = agg(sel, f"{a}_{K}")
        e[a] = m
        n2, m2 = agg(sel, f"{a}_{K2}")
        e[a + "_2R"] = m2
    v = np.array([r[f"fill_{K}"] for r in sel])
    lo, hi, p = dayblock_ci(v, days)
    e["fill_ci95"] = [lo, hi]; e["fill_p_le_0"] = p
    per_sym[s] = e
out["per_instrument"] = per_sym

# ---------------------------------------------------------------- per window
per_mm = {}
for m in MONTHS:
    sel = [r for r in rows if r["mm"] == m and r.get(f"bar_{K}") is not None]
    if not sel:
        continue
    e = {"n": len(sel)}
    for a in ARMS:
        _, v = agg(sel, f"{a}_{K}")
        e[a] = v
        _, v2 = agg(sel, f"{a}_{K2}")
        e[a + "_2R"] = v2
    per_mm[m] = e
out["per_window"] = per_mm
out["persistence"] = {
    "windows_bar_positive_1.5R": sum(1 for m in per_mm if (per_mm[m]["bar"] or 0) > 0),
    "windows_fill_positive_1.5R": sum(1 for m in per_mm if (per_mm[m]["fill"] or 0) > 0),
    "windows_bar_positive_2R": sum(1 for m in per_mm if (per_mm[m]["bar_2R"] or 0) > 0),
    "windows_fill_positive_2R": sum(1 for m in per_mm if (per_mm[m]["fill_2R"] or 0) > 0),
    "n_windows": len(per_mm),
}

# ---------------------------------------------------------------- risk-distance quintiles
sel = [r for r in rows if r.get(f"bar_{K}") is not None]
db = np.array([r["d_bps"] for r in sel])
qs = np.percentile(db, [20, 40, 60, 80])
qidx = np.searchsorted(qs, db, side="right")
quint = {}
for q in range(5):
    sub = [r for r, k in zip(sel, qidx) if k == q]
    if not sub:
        continue
    days = [r["day"] for r in sub]
    e = {"n": len(sub), "median_d_bps": float(np.median([r["d_bps"] for r in sub])),
         "median_spread_over_d": float(np.median([r["spread_over_d"] for r in sub]))}
    for a in ARMS:
        _, v = agg(sub, f"{a}_{K}")
        e[a] = v
        _, v2 = agg(sub, f"{a}_{K2}")
        e[a + "_2R"] = v2
    v = np.array([r[f"fill_{K}"] for r in sub])
    lo, hi, p = dayblock_ci(v, days)
    e["fill_ci95"] = [lo, hi]; e["fill_p_le_0"] = p
    quint[f"Q{q+1}"] = e
out["risk_distance_quintiles"] = quint

# ---------------------------------------------------------------- exit-reason migration
mig = defaultdict(int)
names = {0: "stop", 1: "target", 2: "path_end"}
sel = [r for r in rows if r.get(f"barcode_{K}") is not None and r.get(f"code_{K}") is not None]
for r in sel:
    mig[(names[r[f"barcode_{K}"]], names[r[f"code_{K}"]])] += 1
out["exit_migration_bar_to_tickfill"] = {f"{a}->{b}": v for (a, b), v in sorted(mig.items())}
out["exit_mix"] = {
    "bar": {names[c]: sum(1 for r in sel if r[f"barcode_{K}"] == c) / len(sel) for c in (0, 1, 2)},
    "tick_fill": {names[c]: sum(1 for r in sel if r[f"code_{K}"] == c) / len(sel) for c in (0, 1, 2)},
}

# ---------------------------------------------------------------- accumulation screen
acc = {}
for hh in ("15m", "2h", "8h", "24h", "72h", "160h", "320h"):
    v = np.array([r[f"cap_{hh}"] for r in rows if r.get(f"cap_{hh}") is not None])
    acc[hh] = {"n": int(len(v)), "mean_bps": float(v.mean()) if len(v) else None,
               "median_bps": float(np.median(v)) if len(v) else None}
# a coverage-matched ladder: only rows that have EVERY horizon
full = [r for r in rows if all(r.get(f"cap_{h}") is not None
                               for h in ("2h", "8h", "24h", "72h", "160h", "320h"))]
acc_matched = {}
for hh in ("2h", "8h", "24h", "72h", "160h", "320h"):
    v = np.array([r[f"cap_{hh}"] for r in full])
    acc_matched[hh] = {"n": len(v), "mean_bps": float(v.mean())}
out["accumulation_raw"] = acc
out["accumulation_coverage_matched"] = acc_matched
if acc_matched.get("2h") and acc_matched["2h"]["mean_bps"]:
    out["accumulation_growth_2h_to_320h"] = (acc_matched["320h"]["mean_bps"]
                                             / acc_matched["2h"]["mean_bps"])
out["toll_bps_median_round_trip"] = float(np.median([r["spread_bps"] for r in rows]))

json.dump(out, open("/tmp/m2/M2_TICK_V1.json", "w"), indent=1)
print(json.dumps({k: out[k] for k in ("headline_grid", "persistence", "intrabar_ordering")},
                 indent=1)[:6000])
