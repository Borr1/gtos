"""p2-70 — WHY a coin-flipped trade also gains from deleting the take-profit.

The placebo is worth 71-180 % of the real effect at every resolution. That is a strong claim
and it needs a mechanism, or it is just an odd number.

The delta lives entirely on one subpopulation. On any row where the take-profit arm does NOT
reach its target, both arms resolve identically -- same stop, same time exit, same price -- and
the difference is exactly zero. So:

    delta = P(target reached) * ( E[what the targetless arm booked | target reached] - target )

which makes this a single conditional expectation: **after price has moved +2R in whatever
direction you happen to be positioned, what happens next?** If it is a martingale from there,
the answer is +2R and the delta is zero. It is not, and this file measures by how much, on the
real rows and on the coin-flipped ones, at M1 resolution.

It also prices the two competing explanations, because both were live:

  (a) GRID  -- the coarse {1,2,4,8,16,32,64,96} ladder books a stop where a finer walk would
               have booked the target-then-stop as a target. Measured as the count of rows whose
               exit reason changes between the COARSE and the M1 walk.
  (b) CONTINUATION -- a real property of the price process: conditional on a 2R excursion,
               the forward path is worth more than 2R.

If (a) were the whole story the delta would go to zero at M1. It does not, so (b) carries it.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from p2_20_walk import REGEN, spread_series  # noqa: E402
from p2_40_resolution import COARSE, MONTHS, M1ROOT, geometry, load_m1, walk_steps  # noqa: E402

TARGET_RR = 2.0
FAMS = ("structural_distance_extreme", "liquidity_sweep_reclaim", "range_extreme_reversion")


def main():
    hend = 120  # 2 h in M1 minutes
    rows = {f: {"real": [], "placebo": []} for f in FAMS}
    grid_changes = {f: {"n": 0, "changed": 0} for f in FAMS}

    for p in sorted(REGEN.glob("P2_EMIT_*.npz")):
        sym = p.name[len("P2_EMIT_"):-len(".npz")]
        z = dict(np.load(p, allow_pickle=False))
        m1 = load_m1(sym)
        if m1 is None:
            continue
        mt, mhi, mlo, mcl = m1
        want = np.array([(dt.datetime.fromisoformat(str(x)) + dt.timedelta(minutes=15)).isoformat()
                         for x in z["t"]])
        pos = np.searchsorted(mt, want, side="left")
        ok = (pos < len(mt) - 1441) & (pos > 0) & (np.array(mt[np.minimum(pos, len(mt) - 1)]) == want)
        if not ok.any():
            continue
        n0 = len(z["fam"])
        sub0 = {k: (v[ok] if isinstance(v, np.ndarray) and v.shape and v.shape[0] == n0 else v)
                for k, v in z.items()}
        start = pos[ok] - 1
        sp = spread_series(sym, sub0["t"])
        # the M15 index for the coarse-grid comparison
        m15_idx = sub0["idx"]
        hi15, lo15, cl15 = [], [], []
        from p2_10_regen import TAPE
        with open(TAPE / f"{sym}_M15.csv", newline="") as fh:
            for r in csv.DictReader(fh):
                hi15.append(float(r["high"]))
                lo15.append(float(r["low"]))
                cl15.append(float(r["close"]))
        hi15, lo15, cl15 = np.array(hi15), np.array(lo15), np.array(cl15)

        for fam in FAMS:
            m = sub0["fam"] == fam
            if not m.any():
                continue
            ssub = {k: (v[m] if isinstance(v, np.ndarray) and v.shape
                        and v.shape[0] == len(sub0["fam"]) else v) for k, v in sub0.items()}
            s = sp[m]
            for arm, placebo in (("real", False), ("placebo", True)):
                g = geometry(ssub, s, "LIVE", flip_side=placebo)
                is_long, fill, st, eas, tpt, tpl, shift, c = g
                pa, ka = walk_steps(is_long, fill, st, eas, tpt, tpl, shift,
                                    mhi, mlo, mcl, start[m], list(range(1, hend + 1)), True)
                pb, kb = walk_steps(is_long, fill, st, eas, tpt, tpl, shift,
                                    mhi, mlo, mcl, start[m], list(range(1, hend + 1)), False)
                hit = ka == 2
                if hit.any():
                    tgt_bps = ((np.abs(tpl - fill)) / c * 1e4)[hit]
                    after = (pb / c * 1e4)[hit]
                    rows[fam][arm].append(np.column_stack([tgt_bps, after]))
                if arm == "real":
                    # grid comparison, same geometry, COARSE M15 ladder vs M1
                    pc, kc = walk_steps(is_long, fill, st, eas, tpt, tpl, shift,
                                        hi15, lo15, cl15, m15_idx[m],
                                        [k for k in COARSE if k <= 8], True)
                    grid_changes[fam]["n"] += int(len(kc))
                    grid_changes[fam]["changed"] += int((kc != ka).sum())
        print("done", sym, file=sys.stderr)

    out = {"schema": "gtos.p2.mechanism.v1",
           "horizon": "2h (120 M1 minutes)", "convention": "LIVE", "target_rr": TARGET_RR,
           "families": {}}
    for fam in FAMS:
        rec = {}
        for arm in ("real", "placebo"):
            if not rows[fam][arm]:
                continue
            a = np.vstack(rows[fam][arm])
            tgt, after = a[:, 0], a[:, 1]
            rec[arm] = {
                "n_target_reached": int(len(tgt)),
                "mean_target_bps": float(tgt.mean()),
                "mean_targetless_outcome_on_the_same_rows_bps": float(after.mean()),
                "continuation_premium_bps": float((after - tgt).mean()),
                "share_of_those_rows_that_end_ABOVE_the_target":
                    float((after > tgt).mean()),
                "share_that_end_at_or_below_the_STOP": float((after <= -0.0).mean()),
            }
        rec["grid_vs_m1_exit_reason_changes"] = grid_changes[fam]
        out["families"][fam] = rec
    p = HERE / "P2_MECHANISM_V1.json"
    p.write_text(json.dumps(out, indent=1))
    print(json.dumps(out["families"], indent=1))
    print("WROTE", p)


if __name__ == "__main__":
    main()
