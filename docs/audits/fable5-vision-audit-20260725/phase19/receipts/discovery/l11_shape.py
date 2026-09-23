#!/usr/bin/env python3
"""l11 step 1 — the shape of the favourable excursion over time, per family.

No exit logic anywhere in this pass. Everything is measured on the post-FILL clock
(t = M1 bars since the fill bar), population TAKEABLE, fill convention REAL.

Objects produced, per family and for the pool:
  drift[t]        mean / median mark-to-market R at t bars after fill (fixed cohort n>=t)
  incr[t]         E[r(t) - r(t-1)] with SE -- the LOCAL drift, i.e. the value of the next minute
  hold[t]         E[r(end) - r(t)] with SE -- the value of CONTINUING to hold from t
  peak            distribution of argmax bar of the running favourable excursion
  giveback        MFE - r(end), and MFE - r at the wall
"""
from __future__ import annotations

import json
import os

import numpy as np

import l11_lib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_SHAPE_V1.json")
MARKS = [1, 2, 3, 5, 8, 10, 15, 20, 30, 45, 60, 75, 90, 105, 119]


def qs(x, ps=(5, 25, 50, 75, 90, 95)):
    if len(x) == 0:
        return {}
    v = np.percentile(x, ps)
    return {"p%d" % p: round(float(vv), 5) for p, vv in zip(ps, v)}


def shape(s, m):
    """m = boolean row mask. Returns the whole time-shape bundle."""
    idx = np.where(m & s.takeable & s.filled)[0]
    n = len(idx)
    if n == 0:
        return {"n": 0}
    fill = s.fill[idx]
    nb = s.nb[idx].astype(int)
    rem = nb - fill                      # bars available after (and including) the fill bar
    cls, fav, adv = s.cls[idx], s.fav[idx], s.adv[idx]

    # ---- build a fill-aligned close matrix A[i, t] = cls[i, fill_i + t], t = 0..119
    T = 120
    A = np.full((n, T), np.nan, dtype=np.float32)
    F = np.full((n, T), np.nan, dtype=np.float32)
    D = np.full((n, T), np.nan, dtype=np.float32)
    ar = np.arange(T)
    for i in range(n):
        k = int(rem[i])
        if k <= 0:
            continue
        A[i, :k] = cls[i, fill[i]:fill[i] + k]
        F[i, :k] = fav[i, fill[i]:fill[i] + k]
        D[i, :k] = adv[i, fill[i]:fill[i] + k]
    ok = ~np.isnan(A)
    r_end = np.array([A[i, int(rem[i]) - 1] if rem[i] > 0 else np.nan for i in range(n)],
                     dtype=np.float64)

    drift, incr, hold = {}, {}, {}
    for t in MARKS:
        sel = ok[:, t]
        k = int(sel.sum())
        if k < 30:
            continue
        v = A[sel, t].astype(np.float64)
        drift[t] = {"n": k, "mean": round(float(v.mean()), 5),
                    "se": round(float(v.std(ddof=1) / np.sqrt(k)), 5),
                    "median": round(float(np.median(v)), 5)}
        # local drift over the *previous* bar
        sel2 = ok[:, t] & ok[:, t - 1]
        d = (A[sel2, t] - A[sel2, t - 1]).astype(np.float64)
        kk = len(d)
        incr[t] = {"n": kk, "mean": round(float(d.mean()), 6),
                   "se": round(float(d.std(ddof=1) / np.sqrt(kk)), 6)}
        # value of continuing to hold from t to the wall, on the cohort alive at t
        h = (r_end[sel] - v)
        h = h[~np.isnan(h)]
        hold[t] = {"n": len(h), "mean": round(float(h.mean()), 5),
                   "se": round(float(h.std(ddof=1) / np.sqrt(len(h))), 5),
                   "t_stat": round(float(h.mean() / (h.std(ddof=1) / np.sqrt(len(h)))), 3)}

    # ---- running favourable excursion peak timing (bars after fill)
    Frun = np.fmax.accumulate(np.where(np.isnan(F), -1e9, F), axis=1)
    mfe = np.array([Frun[i, int(rem[i]) - 1] if rem[i] > 0 else np.nan for i in range(n)])
    peakbar = np.array([int(np.nanargmax(np.where(np.isnan(F[i, :int(rem[i])]), -1e9,
                                                  F[i, :int(rem[i])]))) if rem[i] > 0 else -1
                        for i in range(n)], dtype=float)
    mae = np.array([np.nanmin(D[i, :int(rem[i])]) if rem[i] > 0 else np.nan for i in range(n)])

    # give-back: MFE reached vs where it ended
    gb = mfe - r_end
    frac_kept = np.where(mfe > 1e-9, r_end / np.maximum(mfe, 1e-9), np.nan)

    # per-bar hazard of a first touch of +1R and of -1R, on the fill clock
    def first_touch_bar(M, lvl, sign):
        hit = (M >= lvl) if sign > 0 else (M <= lvl)
        hit &= ~np.isnan(M)
        any_ = hit.any(1)
        return np.where(any_, hit.argmax(1), -1)

    b1 = first_touch_bar(F, 1.0, 1)
    bm1 = first_touch_bar(D, -1.0, -1)

    return {
        "n": n,
        "mean_bars_available_after_fill": round(float(rem.mean()), 2),
        "share_filled_at_bar0": round(float((fill == 0).mean()), 5),
        "median_fill_bar": float(np.median(fill)),
        "r_end": {"mean": round(float(np.nanmean(r_end)), 5),
                  "median": round(float(np.nanmedian(r_end)), 5), **qs(r_end[~np.isnan(r_end)])},
        "mfe": {"mean": round(float(np.nanmean(mfe)), 5),
                "median": round(float(np.nanmedian(mfe)), 5), **qs(mfe[~np.isnan(mfe)])},
        "mae": {"mean": round(float(np.nanmean(mae)), 5),
                "median": round(float(np.nanmedian(mae)), 5), **qs(mae[~np.isnan(mae)])},
        "peak_bar": {"mean": round(float(np.nanmean(peakbar)), 2),
                     "median": float(np.nanmedian(peakbar)), **qs(peakbar[peakbar >= 0]),
                     "share_peak_in_first_5": round(float((peakbar <= 4).mean()), 5),
                     "share_peak_in_first_15": round(float((peakbar <= 14).mean()), 5),
                     "share_peak_in_first_30": round(float((peakbar <= 29).mean()), 5),
                     "share_peak_last_10pct": round(float((peakbar >= rem - 12).mean()), 5)},
        "giveback_mfe_minus_end": {"mean": round(float(np.nanmean(gb)), 5),
                                   "median": round(float(np.nanmedian(gb)), 5)},
        "frac_of_mfe_kept": {"mean": round(float(np.nanmean(frac_kept)), 5),
                             "median": round(float(np.nanmedian(frac_kept)), 5)},
        "share_touch_plus1R": round(float((b1 >= 0).mean()), 5),
        "share_touch_minus1R": round(float((bm1 >= 0).mean()), 5),
        "median_bar_touch_plus1R": float(np.median(b1[b1 >= 0])) if (b1 >= 0).any() else None,
        "median_bar_touch_minus1R": float(np.median(bm1[bm1 >= 0])) if (bm1 >= 0).any() else None,
        "drift": drift, "incr": incr, "hold": hold,
    }


def main():
    s = l11_lib.load()
    out = {"lane": "l11", "pass": "SHAPE",
           "population": "TAKEABLE (born != born_past_stop)", "fill": "REAL",
           "clock": "M1 bars since the FILL bar", "horizon": "hard 2h wall"}
    all_m = np.ones(s.N, bool)
    out["POOL"] = shape(s, all_m)
    fams = sorted(set(s.fam[s.takeable].tolist()))
    out["by_family"] = {f: shape(s, s.fam == f) for f in fams}
    out["by_born"] = {b: shape(s, s.born == b)
                      for b in ["born_at_limit", "born_marketable", "born_resting"]}
    out["by_side"] = {sd: shape(s, s.side == sd) for sd in ["LONG", "SHORT"]}
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    p = out["POOL"]
    print("POOL n=%d r_end=%.4f mfe_med=%.3f mae_med=%.3f peak_med=%.0f kept_med=%.3f"
          % (p["n"], p["r_end"]["mean"], p["mfe"]["median"], p["mae"]["median"],
             p["peak_bar"]["median"], p["frac_of_mfe_kept"]["median"]))
    print("t  drift_mean  incr_mean(se)   hold_mean(se) t")
    for t in MARKS:
        if t in p["drift"]:
            print("%3d %8.4f  %+8.5f(%.5f) %+8.4f(%.4f) %6.2f"
                  % (t, p["drift"][t]["mean"], p["incr"][t]["mean"], p["incr"][t]["se"],
                     p["hold"][t]["mean"], p["hold"][t]["se"], p["hold"][t]["t_stat"]))
    print("family  n  r_end  mfe_med  peak_med  hold@1  hold@30  hold@60")
    for f, v in out["by_family"].items():
        print("%-30s %5d %+7.4f %6.3f %5.0f %+7.4f %+7.4f %+7.4f"
              % (f[:30], v["n"], v["r_end"]["mean"], v["mfe"]["median"],
                 v["peak_bar"]["median"], v["hold"].get(1, {}).get("mean", float("nan")),
                 v["hold"].get(30, {}).get("mean", float("nan")),
                 v["hold"].get(60, {}).get("mean", float("nan"))))


if __name__ == "__main__":
    main()
