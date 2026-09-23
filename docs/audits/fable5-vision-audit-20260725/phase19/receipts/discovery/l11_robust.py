#!/usr/bin/env python3
"""l11 step 4 — is the per-family DESIGNED contract real, and how far can it be wrong?

Five attacks, in the order that would kill it fastest:

  DEDUP        re-run on first-emission rows only (W0-F1: 24.4% of the pool is the same
               setup re-emitted, 91.9% of it in current_fvg_fill, which is one of the two
               families carrying the result)
  DAY BOOTSTRAP  resample TEST days with replacement -- the unit of independence is a day,
               not a trade
  PERMUTATION  shuffle the family labels, re-derive the SAME design procedure on train,
               read it on test, 400x.  This prices the procedure itself on noise.
  COST/SLIP    spread divisor 1..8.5, slippage x0..x3, and a stop that fills `stop_slip_r`
               worse than its level
  FILL         REAL vs STRICT (never assume a bar-0 fill; wait for adv<=0 for everyone)
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

import l11_analytic
import l11_lib
import l11_walk

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "L11_ROBUST_V1.json")
SPLIT = "2026-01-16"
RNG = np.random.default_rng(20260801)


def design(e, tr_mask):
    """The DESIGNED contract: the two analytic level choices, on TRAIN rows only."""
    tab = l11_analytic.table(e.F[tr_mask], e.D[tr_mask], e.A[tr_mask], e.rem[tr_mask], "x")
    bt = max(tab["TARGET_LEVELS"].items(), key=lambda kv: kv[1]["value_per_candidate"])
    bs = max(tab["STOP_LEVELS"].items(), key=lambda kv: kv[1]["value_per_candidate"])
    return {"target": bt[1]["level"] if bt[1]["value_per_candidate"] > 0 else None,
            "stop": -bs[1]["level"] if bs[1]["value_per_candidate"] > 0 else None,
            "arm_bar": 1, "trail_arm": None, "trail_gap": None, "max_bars": 120}


def portfolio(e, s, fams, take, day, extra_mask=None, **runkw):
    """Design per family on train, read on test; returns (r_test, mask_test_idx)."""
    tr_all = take & (day < SPLIT)
    te_all = take & (day >= SPLIT)
    if extra_mask is not None:
        tr_all = tr_all & extra_mask
        te_all = te_all & extra_mask
    rs, idxs, specs = [], [], {}
    for f in sorted(set(fams[take].tolist())):
        tr = tr_all & (fams == f)
        te = te_all & (fams == f)
        if tr.sum() < 60 or te.sum() < 40:
            continue
        c = design(e, tr)
        specs[f] = c
        r, rc, _ = e.run(rows=te, **{**c, **runkw})
        rs.append(r)
        idxs.append(np.where(te)[0])
    return np.concatenate(rs), np.concatenate(idxs), specs


def main():
    s = l11_lib.load()
    e = l11_walk.Engine(s)
    take, fams, day = s.takeable, s.fam, s.day
    cost = s.cost_r()
    out = {"lane": "l11", "pass": "ROBUST", "split": SPLIT}

    # ------------------------------------------------------------------ 0 headline
    r, idx, specs = portfolio(e, s, fams, take, day)
    base_gross = float(r.mean())
    out["HEADLINE"] = {"n": len(r), "gross": round(base_gross, 6),
                       "net73": round(float((r - cost[idx]).mean()), 6),
                       "specs": {k: {"target": v["target"], "stop": v["stop"]}
                                 for k, v in specs.items()}}

    # ------------------------------------------------------------------ 1 dedup
    r2, idx2, _ = portfolio(e, s, fams, take, day, extra_mask=s.firstem)
    out["DEDUP_FIRST_EMISSION_ONLY"] = {
        "n": len(r2), "gross": round(float(r2.mean()), 6),
        "net73": round(float((r2 - cost[idx2]).mean()), 6),
        "delta_vs_headline": round(float(r2.mean() - base_gross), 6)}

    # ------------------------------------------------------------------ 2 day bootstrap
    d_te = day[idx]
    udays = sorted(set(d_te.tolist()))
    per_day = {u: r[d_te == u] for u in udays}
    boots = []
    for _ in range(4000):
        pick = RNG.choice(len(udays), len(udays), replace=True)
        v = np.concatenate([per_day[udays[i]] for i in pick])
        boots.append(v.mean())
    boots = np.array(boots)
    out["DAY_BOOTSTRAP"] = {
        "n_days": len(udays), "n_boot": 4000,
        "mean": round(base_gross, 6),
        "ci05": round(float(np.percentile(boots, 5)), 6),
        "ci50": round(float(np.percentile(boots, 50)), 6),
        "ci95": round(float(np.percentile(boots, 95)), 6),
        "share_boot_positive": round(float((boots > 0).mean()), 4),
        "per_day_mean": {u: round(float(per_day[u].mean()), 5) for u in udays},
        "days_positive": int(sum(1 for u in udays if per_day[u].mean() > 0))}

    # ------------------------------------------------------------------ 3 permutation
    perm = []
    fam_take = fams.copy()
    for _ in range(400):
        sh = fam_take.copy()
        pos = np.where(take)[0]
        sh[pos] = RNG.permutation(fam_take[pos])
        try:
            rp, ip, _ = portfolio(e, s, sh, take, day)
            perm.append(float(rp.mean()))
        except ValueError:
            continue
    perm = np.array(perm)
    out["PERMUTATION_FAMILY_LABELS"] = {
        "n_perm": len(perm), "observed": round(base_gross, 6),
        "null_mean": round(float(perm.mean()), 6), "null_sd": round(float(perm.std()), 6),
        "null_p95": round(float(np.percentile(perm, 95)), 6),
        "p_value_one_sided": round(float((perm >= base_gross).mean()), 5)}

    # ------------------------------------------------------------------ 4 cost / slip
    sens = {}
    for div in (1.0, 2.0, 4.0, 7.3, 8.5, 1e9):
        for sm in (0.0, 1.0, 2.0, 3.0):
            c = s.cost_r(spread_div=div, slip_mult=sm)[idx]
            sens["spreaddiv%.1f_slipx%.1f" % (div, sm)] = round(float((r - c).mean()), 6)
    out["COST_SENSITIVITY_net_of_designed_portfolio"] = sens
    slipsens = {}
    for ss in (0.0, 0.02, 0.05, 0.10, 0.20):
        rr, ii, _ = portfolio(e, s, fams, take, day, stop_slip_r=ss)
        slipsens["stop_slip_%.2fR" % ss] = {
            "gross": round(float(rr.mean()), 6),
            "net73": round(float((rr - cost[ii]).mean()), 6)}
    out["STOP_FILL_SLIPPAGE"] = slipsens

    # ------------------------------------------------------------------ 5 fill convention
    es = l11_walk.Engine(s, fill_mode="strict")
    rs2, is2, _ = portfolio(es, s, fams, take, day)
    out["FILL_STRICT"] = {"n": len(rs2), "gross": round(float(rs2.mean()), 6),
                          "net73": round(float((rs2 - cost[is2]).mean()), 6),
                          "delta_vs_REAL": round(float(rs2.mean() - base_gross), 6)}

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items()
                      if k not in ("COST_SENSITIVITY_net_of_designed_portfolio",)},
                     default=str)[:2400])
    print("COST GRID:", json.dumps(sens))


if __name__ == "__main__":
    main()
