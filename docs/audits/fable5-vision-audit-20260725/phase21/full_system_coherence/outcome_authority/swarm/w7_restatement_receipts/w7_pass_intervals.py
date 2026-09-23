#!/usr/bin/env python3
"""W7 INSTRUMENT RESTATEMENT — part 5: intervals on p_pass itself.

Measurement only.

Lane A established there is no confidence interval anywhere in phases 19-21.  Every
published `p_pass` is a point estimate whose only stated uncertainty is MC seed noise
(`se_p_pass` ~ 1e-3), which is the uncertainty of the SIMULATION, not of the EVIDENCE.
The evidence is 117 book-days.  This measures the sampling interval that matters:
a moving-block bootstrap over the book-day series, re-running the full firm-rule MC on
each resample, plus the edge-CI bounds.
"""
from __future__ import annotations

import collections
import json
import math
import random
import statistics
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[8]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

import mc_firm_rules as Q          # noqa: E402
import recost_w7_validation as M   # noqa: E402

HERE = Path(__file__).resolve().parent
ARMED_3 = ["crypto", "energy_agri", "sub_xvol_pullback"]
ARMED_4 = ARMED_3 + ["sub_mid_dn_revert"]
N_BOOT = 400
BLOCK = 5
N_PATHS = 20_000


def pctl(xs, q):
    xs = sorted(xs)
    i = (len(xs) - 1) * q / 100.0
    lo, hi = int(math.floor(i)), int(math.ceil(i))
    return xs[lo] if lo == hi else xs[lo] + (xs[hi] - xs[lo]) * (i - lo)


def moving_block(series, rng, block=BLOCK):
    n = len(series)
    out = []
    while len(out) < n:
        s = rng.randrange(0, n)
        out.extend(series[s:s + block] if s + block <= n
                   else series[s:] + series[:s + block - n])
    return out[:n]


def main():
    st = M.build([])
    rows = st["rows"]
    for r in rows:
        r["R_legacy"] = r["R"]
    _, _, _, sd_book = M.build_matrix_from(rows, "R_legacy")
    out = {"schema": "gtos.wave21.w7_pass_intervals.v1", "measurement_only": True,
           "method": (f"moving-block bootstrap, block={BLOCK} book-days, "
                      f"{N_BOOT} resamples, full firm-rule MC at {N_PATHS} paths each"),
           "books": {}}

    for label, keep in (("ARMED_3", ARMED_3), ("ARMED_4", ARMED_4)):
        for acct in ("FTMO", "redacted_account"):
            pool = collections.defaultdict(list)
            for r in rows:
                c = r[f"cost_{acct}"]
                if c["status"] == "priced":
                    pool[r["sleeve"]].append(c["cost_ex_swap_r"])
            cm = {k: statistics.median(v) for k, v in pool.items()}
            sub = [r for r in rows if r["sleeve"] in keep]
            days, comb, risk, _ = Q.series(sub, acct, cm, "max", sd_book, forward=True,
                                           kelly=Q.KELLY_HALF,
                                           risk_basis=Q.RISK_LIVE_NOMINAL)
            rules, _ = Q.rule_sets(acct)
            P2 = [r for r in rules if r.label == "P2_BOTH_PHASES"][0]
            point = Q.mc(comb, risk, P2, 60_000, seed_base=1)

            rng = random.Random(20260811)
            ps, means = [], []
            for _ in range(N_BOOT):
                bs = moving_block(comb, rng)
                ps.append(Q.mc(bs, risk, P2, N_PATHS, seed_base=1)["p_pass"])
                means.append(statistics.fmean(bs))
            n = len(comb)
            mu = statistics.fmean(comb)
            sd = statistics.stdev(comb)
            se = sd / math.sqrt(n)
            out["books"][f"{acct}:{label}"] = dict(
                book_days=n,
                mean_r_per_book_day=mu, sd_r_per_book_day=sd, se_mean=se,
                ci95_mean_r_per_book_day=[mu - 1.96 * se, mu + 1.96 * se],
                t_stat_mean=mu / se if se else None,
                p_pass_point=point["p_pass"],
                p_pass_mc_seed_se=point["se_p_pass"],
                p_pass_bootstrap=dict(
                    median=pctl(ps, 50), p2_5=pctl(ps, 2.5), p97_5=pctl(ps, 97.5),
                    p10=pctl(ps, 10), p90=pctl(ps, 90),
                    mean=statistics.fmean(ps), n=len(ps)),
                bootstrap_mean_r=dict(median=pctl(means, 50), p2_5=pctl(means, 2.5),
                                      p97_5=pctl(means, 97.5)),
                width_note=("`p_pass_mc_seed_se` is the simulation's own noise; "
                            "`p_pass_bootstrap` is the interval the EVIDENCE supports"))
            b = out["books"][f"{acct}:{label}"]
            print(f"{acct}:{label}  n={n}  meanR/bd={mu:+.5f} "
                  f"CI95[{b['ci95_mean_r_per_book_day'][0]:+.5f},"
                  f"{b['ci95_mean_r_per_book_day'][1]:+.5f}] t={b['t_stat_mean']:.2f}")
            print(f"    p_pass point={point['p_pass']:.5f} (mc se {point['se_p_pass']:.5f})"
                  f"  BOOTSTRAP CI95 [{b['p_pass_bootstrap']['p2_5']:.5f},"
                  f"{b['p_pass_bootstrap']['p97_5']:.5f}] "
                  f"median {b['p_pass_bootstrap']['median']:.5f}")

    (HERE / "W7_PASS_INTERVALS_V1.json").write_text(json.dumps(out, indent=1, default=str))


if __name__ == "__main__":
    main()
