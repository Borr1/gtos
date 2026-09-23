"""m1 — the accumulation curve, old instrument vs repaired, with a day-block bootstrap.

The curve is the load-bearing measurement of wave 19's verdict.  d3 measured it with a
walker that never crossed the spread, on a roster still carrying the generator's malformed
emissions, and reported the broad family at 0.97x growth from 2 h to 320 h against a live
sleeve's 37.58x.  This re-derives it on the repaired instrument.

The interval is a DAY-BLOCK bootstrap over the 172 trading days (resample days with
replacement, weight by that day's own row count), not a row bootstrap: rows inside a day
share a market and are not independent.
"""
from __future__ import annotations

import json
import sys

import numpy as np

HOR = [8, 32, 96, 288, 640, 1280]
HH = [2, 8, 24, 72, 160, 320]
W8 = ["2025-10", "2025-11", "2025-12", "2026-01", "2026-02", "2026-03", "2026-04", "2026-05"]
NB = 4000
SEED = 20260807


def dayblock_ci(vals, days, rng, nb=NB):
    """Mean of `vals` with a day-block bootstrap CI, from per-day (sum, n) aggregates."""
    if vals.size == 0:
        return float("nan"), float("nan"), float("nan"), float("nan")
    ud, inv = np.unique(days, return_inverse=True)
    s = np.bincount(inv, weights=vals, minlength=ud.size)
    c = np.bincount(inv, minlength=ud.size).astype(float)
    k = ud.size
    ix = rng.integers(0, k, size=(nb, k))
    bs = s[ix].sum(axis=1) / c[ix].sum(axis=1)
    return (float(vals.mean()), float(np.percentile(bs, 2.5)),
            float(np.percentile(bs, 97.5)), float((bs <= 0).mean()))


def curve(z, days, mask, arm, label, rng, control="PLACEBO"):
    """`control="PLACEBO"` is d3's coin flip; `control="MIRROR"` walks every row on BOTH
    sides and halves the difference — the same estimand with zero draw variance."""
    dbps = z["dbps"][mask]
    dd = days[mask]
    out = []
    half = 0.5 if control == "MIRROR" else 1.0
    for h, hh in zip(HOR, HH):
        a = z[f"{arm}_REAL_{h}"][mask].astype(np.float64)
        b = z[f"{arm}_{control}_{h}"][mask].astype(np.float64)
        m = np.isfinite(a) & np.isfinite(b)
        dr = ((a - b) * half)[m]
        db = ((a - b) * half * dbps)[m]
        mean_bps, lo, hi, p = dayblock_ci(db, dd[m], rng)
        out.append({
            "hours": hh, "n": int(m.sum()),
            "signal_r": float(dr.mean()), "signal_bps": mean_bps,
            "signal_bps_const_multiplier": float(dr.mean() * np.median(dbps[m])),
            "ci_lo_bps": lo, "ci_hi_bps": hi, "p_le0": p,
            "gross_r_real": float(a[m].mean()), "gross_r_placebo": float(b[m].mean()),
        })
    g = out[-1]["signal_bps"] / out[0]["signal_bps"] if out[0]["signal_bps"] else float("nan")
    gr = out[-1]["signal_r"] / out[0]["signal_r"] if out[0]["signal_r"] else float("nan")
    return {"label": label, "n": out[0]["n"], "rows": out,
            "growth_2h_to_320h_bps": g, "growth_2h_to_320h_r": gr,
            "median_stop_bps": float(np.median(dbps))}


def main(out_path):
    z = np.load("/tmp/m1/M1_ACCUM.npz", allow_pickle=True)
    days = np.load("/tmp/m1/ACCUM_DAY.npy")
    rng = np.random.default_rng(SEED)
    is_poi, kept = z["is_poi"], z["kept"]
    n = z["dbps"].size

    cohorts = {
        "at_market_LEGACY": ~is_poi,
        "at_market_REPAIRED": (~is_poi) & kept,
        "all_families_LEGACY": np.ones(n, bool),
        "all_families_REPAIRED": kept,
        "poi_REPAIRED": is_poi & kept,
    }
    out = {
        "what": "the accumulation curve on the repaired instrument",
        "construction": {
            "horizons_printed_m15_bars": HOR, "trading_hours": HH, "target_r": 3.0,
            "stop": "native (the generator's own risk distance)",
            "paired": "REAL side minus a coin-flip PLACEBO side, seed 20260806, same rows",
            "interval": "day-block bootstrap over 172 trading days, 4000 replicates",
            "arms": {"old": "no spread crossing (what d3 walked)",
                     "cor": "quote_side FILL anchoring at the hour-aware tick spread",
                     "era": "same, at the era-aware spread model"},
            "note": "measured at market for every family: the screen is about the SIGNAL",
        },
        "population": {"rows": int(n), "kept_by_repaired_contract": int(kept.sum()),
                       "at_market": int((~is_poi).sum()), "poi": int(is_poi.sum()),
                       "trading_days": int(np.unique(days).size)},
        "curves": {},
    }
    for cname, m in cohorts.items():
        for arm in ("old", "cor", "era"):
            for ctl in ("PLACEBO", "MIRROR"):
                if arm == "era" and ctl == "PLACEBO":
                    continue
                out["curves"][f"{cname}|{arm}|{ctl}"] = curve(
                    z, days, m, arm, f"{cname}|{arm}|{ctl}", rng, control=ctl)

    pw = {}
    for w in W8:
        m = (~is_poi) & kept & (z["win"] == w)
        if m.sum() < 100:
            continue
        c = curve(z, days, m, "cor", w, rng, control="MIRROR")
        pw[w] = {"n": c["n"], "signal_bps_2h": c["rows"][0]["signal_bps"],
                 "signal_bps_320h": c["rows"][-1]["signal_bps"],
                 "growth": c["growth_2h_to_320h_bps"]}
    out["per_window_at_market_repaired_cor"] = pw

    json.dump(out, open(out_path, "w"), indent=1)

    for k in ("at_market_LEGACY|old|PLACEBO", "at_market_LEGACY|old|MIRROR",
              "at_market_REPAIRED|old|MIRROR", "at_market_REPAIRED|cor|MIRROR",
              "at_market_REPAIRED|era|MIRROR", "at_market_REPAIRED|cor|PLACEBO",
              "all_families_LEGACY|old|MIRROR", "all_families_REPAIRED|old|MIRROR",
              "all_families_REPAIRED|cor|MIRROR", "poi_REPAIRED|cor|MIRROR"):
        c = out["curves"][k]
        print(f"\n{k}   n={c['n']}  median_stop={c['median_stop_bps']:.3f} bps")
        print(f"{'h':>5s} {'signal_R':>10s} {'signal_bps':>11s} {'ci_lo':>9s} {'ci_hi':>9s} "
              f"{'p<=0':>7s} {'real_R':>9s} {'plac_R':>9s}")
        for r in c["rows"]:
            print(f"{r['hours']:5d} {r['signal_r']:10.5f} {r['signal_bps']:11.4f} "
                  f"{r['ci_lo_bps']:9.4f} {r['ci_hi_bps']:9.4f} {r['p_le0']:7.4f} "
                  f"{r['gross_r_real']:9.5f} {r['gross_r_placebo']:9.5f}")
        print(f"GROWTH 2h->320h  bps {c['growth_2h_to_320h_bps']:.4f}x   "
              f"R {c['growth_2h_to_320h_r']:.4f}x")
    print("\nPER WINDOW (at_market repaired, corrected):")
    for w, v in pw.items():
        print(f"  {w} n={v['n']:7d} 2h={v['signal_bps_2h']:+.4f} "
              f"320h={v['signal_bps_320h']:+.4f} growth={v['growth']:.3f}x")


if __name__ == "__main__":
    main(sys.argv[1])
