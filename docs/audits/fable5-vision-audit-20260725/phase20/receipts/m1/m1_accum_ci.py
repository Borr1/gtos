"""m1 — is the ACCUMULATION RATIO a measurable quantity at all?

d3 published `growth 2h -> 320h = 0.965x` for the broad family and `37.58x` for the live
sleeves, and made the ratio the estate's pre-economic admission screen.  The broad arm was
published with NO interval.  This puts one on it — day-block bootstrap over the 172 trading
days, resampling the SAME days for both endpoints so the ratio's own correlation is kept —
and reports the ratio, the 320h-minus-2h difference, and the level, in three units:

  R                  the estate's own unit
  bps (per row)      each row's own stop width, the unit that cannot be gamed
  bps (d3's form)    signal_R x the cohort's median stop width, exactly d3's constant

The control is the deterministic MIRROR (every row walked both sides, difference halved),
not d3's coin flip: a coin discards half the pairs and its draw is worth about a quarter of
the published signal, which is the first thing this script measures.
"""
from __future__ import annotations

import json
import sys

import numpy as np

HOR = [8, 32, 96, 288, 640, 1280]
HH = [2, 8, 24, 72, 160, 320]
NB = 4000
SEED = 20260807


def blocks(vals, days):
    ud, inv = np.unique(days, return_inverse=True)
    return (np.bincount(inv, weights=vals, minlength=ud.size),
            np.bincount(inv, minlength=ud.size).astype(float))


def main(out_path):
    z = np.load("/tmp/m1/M1_ACCUM.npz", allow_pickle=True)
    days = np.load("/tmp/m1/ACCUM_DAY.npy")
    is_poi, kept = z["is_poi"], z["kept"]
    n = z["dbps"].size
    rng = np.random.default_rng(SEED)

    cohorts = {
        "at_market_LEGACY": ~is_poi,
        "at_market_REPAIRED": (~is_poi) & kept,
        "all_families_REPAIRED": kept,
    }
    out = {"what": "growth-ratio intervals for the accumulation screen",
           "construction": {
               "control": "deterministic mirror, (REAL - MIRROR)/2",
               "bootstrap": "day-block over 172 trading days, 4000 replicates, the SAME "
                            "resampled days used for every horizon so the ratio keeps its "
                            "own correlation",
           },
           "results": {}}

    for cname, mask in cohorts.items():
        for arm in ("old", "cor"):
            dbps = z["dbps"][mask]
            med = float(np.median(dbps))
            dd = days[mask]
            ud = np.unique(dd)
            k = ud.size
            ix = rng.integers(0, k, size=(NB, k))
            per_h = {}
            bs_r, bs_b = {}, {}
            for h, hh in zip(HOR, HH):
                a = z[f"{arm}_REAL_{h}"][mask].astype(np.float64)
                b = z[f"{arm}_MIRROR_{h}"][mask].astype(np.float64)
                m = np.isfinite(a) & np.isfinite(b)
                dr = ((a - b) * 0.5)[m]
                db = dr * dbps[m]
                sr, cr = blocks(dr, dd[m])
                sb, _ = blocks(db, dd[m])
                # NB: the row counts differ per horizon only where a bar is missing;
                # resample on the union index so ratios pair the same days.
                cnt = cr[ix].sum(axis=1)
                bs_r[hh] = sr[ix].sum(axis=1) / cnt
                bs_b[hh] = sb[ix].sum(axis=1) / cnt
                per_h[hh] = {
                    "n": int(m.sum()),
                    "signal_r": float(dr.mean()),
                    "signal_r_ci95": [float(np.percentile(bs_r[hh], 2.5)),
                                      float(np.percentile(bs_r[hh], 97.5))],
                    "signal_r_p_le0": float((bs_r[hh] <= 0).mean()),
                    "signal_bps_perrow": float(db.mean()),
                    "signal_bps_perrow_ci95": [float(np.percentile(bs_b[hh], 2.5)),
                                               float(np.percentile(bs_b[hh], 97.5))],
                    "signal_bps_d3_form": float(dr.mean() * med),
                    "signal_bps_d3_form_ci95": [float(np.percentile(bs_r[hh], 2.5) * med),
                                                float(np.percentile(bs_r[hh], 97.5) * med)],
                }
            ratio = bs_r[320] / bs_r[2]
            diff = bs_r[320] - bs_r[2]
            out["results"][f"{cname}|{arm}"] = {
                "median_stop_bps": med,
                "per_horizon": per_h,
                "growth_ratio_point": per_h[320]["signal_r"] / per_h[2]["signal_r"],
                "growth_ratio_ci95": [float(np.percentile(ratio, 2.5)),
                                      float(np.percentile(ratio, 97.5))],
                "growth_ratio_iqr": [float(np.percentile(ratio, 25)),
                                     float(np.percentile(ratio, 75))],
                "share_of_replicates_with_ratio_ge_10": float((ratio >= 10).mean()),
                "share_of_replicates_with_ratio_ge_3": float((ratio >= 3).mean()),
                "share_of_replicates_with_2h_signal_le0": float((bs_r[2] <= 0).mean()),
                "diff_320h_minus_2h_r": float(per_h[320]["signal_r"] - per_h[2]["signal_r"]),
                "diff_ci95": [float(np.percentile(diff, 2.5)),
                              float(np.percentile(diff, 97.5))],
                "diff_p_ge0": float((diff >= 0).mean()),
            }

    json.dump(out, open(out_path, "w"), indent=1)
    for k, v in out["results"].items():
        print(f"\n=== {k}   median_stop {v['median_stop_bps']:.3f} bps")
        print(f"{'h':>5s} {'signal_R':>10s} {'R ci95':>22s} {'p<=0':>6s} "
              f"{'bps(d3 form)':>13s} {'bps(per row)':>13s}")
        for hh in HH:
            r = v["per_horizon"][hh]
            print(f"{hh:5d} {r['signal_r']:10.5f} "
                  f"[{r['signal_r_ci95'][0]:+9.5f},{r['signal_r_ci95'][1]:+9.5f}] "
                  f"{r['signal_r_p_le0']:6.3f} {r['signal_bps_d3_form']:13.4f} "
                  f"{r['signal_bps_perrow']:13.4f}")
        print(f"  growth ratio {v['growth_ratio_point']:.3f}x  CI95 "
              f"[{v['growth_ratio_ci95'][0]:.2f}, {v['growth_ratio_ci95'][1]:.2f}]  "
              f"IQR [{v['growth_ratio_iqr'][0]:.2f}, {v['growth_ratio_iqr'][1]:.2f}]")
        print(f"  P(ratio >= 10) = {v['share_of_replicates_with_ratio_ge_10']:.4f}   "
              f"P(ratio >= 3) = {v['share_of_replicates_with_ratio_ge_3']:.4f}   "
              f"P(2h signal <= 0) = {v['share_of_replicates_with_2h_signal_le0']:.4f}")
        print(f"  320h - 2h = {v['diff_320h_minus_2h_r']:+.5f} R  CI95 "
              f"[{v['diff_ci95'][0]:+.5f}, {v['diff_ci95'][1]:+.5f}]  "
              f"P(>=0) = {v['diff_p_ge0']:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
