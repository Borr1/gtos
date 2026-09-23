"""p2-55 — confidence intervals on the estate side-placebo, because it reaches armed money.

`P2_ESTATE_SIDE_PLACEBO_V1.json` reports point estimates on 67-5,597 trades. A claim about
`sub_xvol_pullback` (ARMED, n=88) or `mx_btcusd @ target_5R` (the estate's one standing
admission, n=318) cannot rest on a point estimate.

Estimator: day-block bootstrap, 4,000 reps, days resampled with replacement, PAIRED on the row
(each replicate resamples days once and evaluates the variant, the baseline, and both placebo
arms on the same resampled days), so the CI is on the difference and not on two levels.

Reported per (sleeve, cell):
    delta         variant minus as_walked, on the real directions
    placebo       the same difference with the direction coin-flipped
    earned        delta - placebo, and ITS interval -- the quantity that decides whether the
                  exit cell is evidence about the sleeve
"""

from __future__ import annotations

import collections
import gzip
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
P7 = REPO / "docs/audits/fable5-vision-audit-20260725/phase7/receipts"
sys.path.insert(0, str(P7))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ad_exit_sweep as AD  # noqa: E402
from p2_50_estate_placebo import VARIANTS, flip  # noqa: E402

AA_IN = REPO / "docs/audits/fable5-vision-audit-20260725/phase6/receipts/AA_ESTATE_TRADES.json.gz"
FOCUS = ("crypto", "energy_agri", "sub_xvol_pullback", "sub_mid_dn_revert",
         "mx_btcusd_d1_donchian_20_breakout", "asia_pdl_fade", "asian_fade",
         "metals_core", "idxrev", "fx_jpy")
RNG = np.random.default_rng(31337)
B = 4000


def keyed(rows):
    """(key -> r_gross) so all four arms align row-for-row after resimulation."""
    return {(r["symbol"], r["decision_bar_iso"], r["direction"]): float(r["r_gross"])
            for r in rows}


def main():
    aa = json.load(gzip.open(AA_IN, "rt"))
    series, index, _ = AD.load_bars()
    out = {"schema": "gtos.p2.estate_side_placebo_ci.v1", "reps": B, "seed": 31337,
           "estimator": "day-block bootstrap, days resampled with replacement, paired per row",
           "sleeves": {}}
    for sleeve in FOCUS:
        rows = aa["trades"].get(sleeve)
        if not rows:
            continue
        rows_p = flip(rows)
        arms = {}
        for v in VARIANTS:
            rr, _ = AD.resimulate(rows, v, series, index, None, "FTMO", None)
            pp, _ = AD.resimulate(rows_p, v, series, index, None, "FTMO", None)
            arms[v.name] = (rr, pp)
        base_r, base_p = arms["as_walked"]
        # a common row ordering: AD keeps input order, so index alignment holds
        days = np.array([r["entry_utc"][:10] for r in base_r])
        uk, inv = np.unique(days, return_inverse=True)
        buckets = [np.nonzero(inv == i)[0] for i in range(len(uk))]
        br = np.array([float(r["r_gross"]) for r in base_r])
        bp = np.array([float(r["r_gross"]) for r in base_p])
        cells = {}
        for name, (rr, pp) in arms.items():
            if name == "as_walked":
                continue
            if len(rr) != len(br) or len(pp) != len(bp):
                cells[name] = {"error": "row count differs between arms"}
                continue
            vr = np.array([float(r["r_gross"]) for r in rr])
            vp = np.array([float(r["r_gross"]) for r in pp])
            d_r = vr - br
            d_p = vp - bp
            earned_pt = float(d_r.mean() - d_p.mean())
            boot = np.empty(B)
            bd = np.empty(B)
            for i in range(B):
                pick = RNG.integers(0, len(buckets), len(buckets))
                idx = np.concatenate([buckets[j] for j in pick])
                bd[i] = d_r[idx].mean()
                boot[i] = d_r[idx].mean() - d_p[idx].mean()
            cells[name] = {
                "n": int(len(vr)),
                "delta_R_per_trade": float(d_r.mean()),
                "delta_ci95": [float(np.percentile(bd, 2.5)), float(np.percentile(bd, 97.5))],
                "placebo_delta_R_per_trade": float(d_p.mean()),
                "earned_R_per_trade": earned_pt,
                "earned_ci95": [float(np.percentile(boot, 2.5)),
                                float(np.percentile(boot, 97.5))],
                "p_earned_le_0": float((boot <= 0).mean()),
                "placebo_share_of_delta":
                    None if abs(d_r.mean()) < 1e-12 else float(d_p.mean() / d_r.mean()),
            }
        out["sleeves"][sleeve] = {"n_rows": len(rows), "cells": cells}
        print("done", sleeve, file=sys.stderr)
    p = HERE / "P2_ESTATE_SIDE_PLACEBO_CI_V1.json"
    p.write_text(json.dumps(out, indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
