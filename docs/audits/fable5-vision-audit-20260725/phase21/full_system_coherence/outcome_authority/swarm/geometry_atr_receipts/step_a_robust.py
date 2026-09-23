"""Step A supplement -- the three things that decide whether beta is real.

(1) DIVISION-ARTIFACT DECOMPOSITION.  y = travel/ATR14 and v = ATR14/ATR50 share
    ATR14, in opposite positions.  If forward travel were driven ONLY by the slow
    vol (travel proportional to ATR50) the regression would return beta = -1
    mechanically; if travel tracked the fast vol one-for-one it would return 0.  So
    beta interpolates two economic hypotheses rather than being spurious -- but the
    reader must be able to see where it sits.  Reported here:
        gamma  : elasticity of RAW travel to v           (log travel ~ log v)
        beta50 : elasticity of travel/ATR50 to v         (log(travel/ATR50) ~ log v)
    beta = gamma - 1 by construction; beta50 is a genuinely different specification.

(2) DISJOINT-WINDOW DENOMINATOR.  Normalise travel by an ATR14 measured over the
    STRICTLY EARLIER, non-overlapping window [i-27, i-14], so the measurement noise
    in ATR14(i) is no longer in both sides.  If beta survives, the relationship is a
    regime fact; if it collapses toward 0, it was mostly ATR14 estimation noise.
    (Both readings still justify the same rescaling -- a stop pegged to a noisy
    ATR14 is mis-scaled either way -- but they differ in how much persistence to
    expect.)

(3) HORIZON SENSITIVITY / the published quintile reproduction.  The prior finding is
    quoted at 1.26x over a 4-HOUR forward window and 1.42x over a 5-DAY one; Step A
    uses 80 bars of the trade's own timeframe, which is 20 h (M15), 13.3 d (H4) and
    ~80 sessions (D1).  Those are not the same windows, so this sweeps the forward
    horizon and reports Q0/Q4 at each, including the 4 h and 5 d equivalents.
"""

from __future__ import annotations

import collections
import json
import pickle
import sys
import time
from pathlib import Path

import numpy as np

REPO = "/Users/borr/GTOSActive/worktrees/swarm-geom-20260811"
sys.path.insert(0, REPO)
sys.path.insert(0, REPO + "/docs/audits/fable5-vision-audit-20260725/phase20/receipts/r1")

from step_a_beta import (  # noqa: E402
    NBOOT, N_FAST, N_SLOW, SEED, TF_NAME, _atr_vec, _true_range, fit, quintiles,
)

OUTDIR = Path("/private/tmp/atr-scaling-20260811")
HORIZONS = {15: (16, 80, 480), 16388: (1, 30, 80), 16408: (5, 20, 80)}
HORIZON_LABEL = {15: {16: "4h", 80: "20h", 480: "5d"},
                 16388: {1: "4h", 30: "5d", 80: "13.3d"},
                 16408: {5: "5d", 20: "20d", 80: "80d"}}
MAIN_H = 80
LAG_LO, LAG_HI = 27, 14   # ATR14 over [i-27, i-14]: disjoint from [i-13, i]


def main() -> int:
    t0 = time.time()
    series, _ = pickle.load(open(OUTDIR / "series.pkl", "rb"))
    rng = np.random.default_rng(SEED)
    per_tf = collections.defaultdict(lambda: collections.defaultdict(list))
    sym_ids = {}

    for (sym, tf), (bars, _times) in sorted(series.items()):
        if tf not in TF_NAME:
            continue
        n = len(bars)
        h = np.fromiter((b.h for b in bars), np.float64, n)
        l = np.fromiter((b.l for b in bars), np.float64, n)
        c = np.fromiter((b.c for b in bars), np.float64, n)
        hz = sorted(set(HORIZONS[tf]) | {MAIN_H})
        if n < N_SLOW + max(hz) + 2:
            continue
        tr = _true_range(h, l, c)
        a14 = _atr_vec(tr, N_FAST)
        a50 = _atr_vec(tr, N_SLOW)
        sid = sym_ids.setdefault(sym, len(sym_ids))
        for H in hz:
            sw_h = np.lib.stride_tricks.sliding_window_view(h, H)
            sw_l = np.lib.stride_tricks.sliding_window_view(l, H)
            fmax = sw_h.max(axis=1)
            fmin = sw_l.min(axis=1)
            i_lo = max(N_SLOW, LAG_LO)
            i_hi = n - 1 - H
            if i_hi < i_lo:
                continue
            idx = np.arange(i_lo, i_hi + 1)
            A14 = a14[idx]; A50 = a50[idx]
            A14lag = a14[idx - LAG_HI]          # ATR14 over [i-27, i-14]
            ok = (A50 > 0) & (A14 > 0) & (A14lag > 0)
            idx = idx[ok]; A14 = A14[ok]; A50 = A50[ok]; A14lag = A14lag[ok]
            travel = fmax[idx + 1] - fmin[idx + 1]
            good = travel > 0
            idx, A14, A50, A14lag, travel = (idx[good], A14[good], A50[good],
                                             A14lag[good], travel[good])
            v = A14 / A50
            d = per_tf[(tf, H)]
            d["v"].append(v)
            d["travel"].append(travel)
            d["y"].append(travel / A14)
            d["y50"].append(travel / A50)
            d["ylag"].append(travel / A14lag)
            d["sym"].append(np.full(len(v), sid, np.int32))
        print(f"  {sym:12s} {TF_NAME[tf]:4s} ({time.time()-t0:.0f}s)", flush=True)

    out = {"what": "Step A robustness: division-artifact decomposition, disjoint-window "
                   "denominator, and horizon sensitivity of the quintile check",
           "lag_window_for_disjoint_atr14": f"[i-{LAG_LO}, i-{LAG_HI}] (no overlap with [i-13, i])",
           "cells": {}}

    for (tf, H) in sorted(per_tf):
        d = per_tf[(tf, H)]
        v = np.concatenate(d["v"]); trv = np.concatenate(d["travel"])
        y = np.concatenate(d["y"]); y50 = np.concatenate(d["y50"])
        ylag = np.concatenate(d["ylag"]); sym = np.concatenate(d["sym"])
        lv = np.log(v)
        nb = 400
        rec = {
            "timeframe": TF_NAME[tf], "horizon_bars": H,
            "horizon_label": HORIZON_LABEL.get(tf, {}).get(H, f"{H}bars"),
            "beta_travel_per_atr14": fit(lv, np.log(y), sym, rng, nboot=nb),
            "gamma_raw_travel": fit(lv, np.log(trv), sym, rng, nboot=nb),
            "beta50_travel_per_atr50": fit(lv, np.log(y50), sym, rng, nboot=nb),
            "beta_lag_travel_per_disjoint_atr14": fit(lv, np.log(ylag), sym, rng, nboot=nb),
            "quintiles_travel_per_atr14": quintiles(v, y),
            "quintiles_travel_per_disjoint_atr14": quintiles(v, ylag),
        }
        out["cells"][f"{TF_NAME[tf]}|h{H}"] = rec
        print(f"{TF_NAME[tf]} h={H:3d} ({rec['horizon_label']:6s}) "
              f"beta={rec['beta_travel_per_atr14']['beta']:+.4f} "
              f"gamma={rec['gamma_raw_travel']['beta']:+.4f} "
              f"beta50={rec['beta50_travel_per_atr50']['beta']:+.4f} "
              f"beta_lag={rec['beta_lag_travel_per_disjoint_atr14']['beta']:+.4f} "
              f"Q0/Q4={rec['quintiles_travel_per_atr14']['Q0_over_Q4_mean_y']:.4f} "
              f"Q0/Q4_lag={rec['quintiles_travel_per_disjoint_atr14']['Q0_over_Q4_mean_y']:.4f}",
              flush=True)

    out["elapsed_s"] = round(time.time() - t0, 1)
    (OUTDIR / "STEP_A_ROBUST_V1.json").write_text(json.dumps(out, indent=1))
    print("WROTE", OUTDIR / "STEP_A_ROBUST_V1.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
