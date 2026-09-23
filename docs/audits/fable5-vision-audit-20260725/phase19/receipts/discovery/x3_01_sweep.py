#!/usr/bin/env python3
"""x3_01_sweep — THE ENTRY-OFFSET CURVE.  -15 min (inside the forming bar) .. +30 min.

Arms are on COMMON SUPPORT: only rows tradable at every offset in the sweep are counted,
so the curve is a like-for-like comparison and cannot move because n moved.
"""
from __future__ import annotations
import json, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import x3_lib as X

OFFSETS = list(range(-15, 31)) + [35, 40, 45, 50, 60]


def main():
    t = X.Tape()
    atm = t.born == "born_at_limit"
    # common support: entry bar present at every offset, and >=1 walk bar at the latest
    sup = np.ones(t.n, bool)
    for k in OFFSETS:
        sup &= t.valid[:, t.j(k) - 1]
    sup &= t.valid[:, t.j(max(OFFSETS)):].any(axis=1)
    print("rows %d  at-market %d  common-support %d  at-market&support %d"
          % (t.n, atm.sum(), sup.sum(), (atm & sup).sum()))

    out = {"offsets": OFFSETS, "n_rows": int(t.n), "n_at_market": int(atm.sum()),
           "n_common_support": int(sup.sum()),
           "n_at_market_common_support": int((atm & sup).sum()), "arms": {}}
    cohorts = {
        "at_market_support": atm & sup,
        "at_market_all": atm,
        "all_support": sup,
        "poi_resting_support": (t.born == "born_resting") & sup,
        "poi_marketable_support": (t.born == "born_marketable") & sup,
        "poi_past_stop_support": (t.born == "born_past_stop") & sup,
    }
    raw = {}
    for contract in ("pool", "trail"):
        for k in OFFSETS:
            res = X.walk(t, k, contract=contract)
            raw[(contract, k)] = res
            for cname, cmask in cohorts.items():
                key = f"{contract}|{cname}|{k}"
                out["arms"][key] = X.summarise(t, res, cmask, key)
        print("done", contract)

    # headline curve print
    for contract in ("pool", "trail"):
        print(f"\n=== {contract.upper()} contract, at-market cohort, common support ===")
        print(f"{'k(min)':>7s} {'n':>6s} {'grossR':>9s} {'netR':>9s} {'win':>6s} "
              f"{'tgt':>6s} {'stop':>6s} {'t':>7s} {'grossbps':>9s} {'netbps':>8s}")
        for k in OFFSETS:
            a = out["arms"][f"{contract}|at_market_support|{k}"]
            print(f"{k:7d} {a['n']:6d} {a['gross_R']:+9.5f} {a['net_R']:+9.5f} "
                  f"{a['win_rate']:6.4f} {a['target_rate']:6.4f} {a['stop_rate']:6.4f} "
                  f"{a['t'] if a['t'] is None else round(a['t'],2):>7} "
                  f"{a['gross_bps']:+9.4f} {a['net_bps']:+8.4f}")

    # paired deltas vs k=0 with day-block bootstrap, at-market cohort
    boots = {}
    for contract in ("pool", "trail"):
        r0 = raw[(contract, 0)]["r"]
        m0 = cohorts["at_market_support"]
        for k in OFFSETS:
            if k == 0:
                continue
            rk = raw[(contract, k)]["r"]
            m = m0 & ~np.isnan(rk) & ~np.isnan(r0)
            d = rk[m] - r0[m]
            b = X.dayboot(t.day[m], d, reps=1000)
            b["n"] = int(m.sum())
            b["contract"] = contract; b["k"] = k
            boots[f"{contract}|delta_vs_k0|{k}"] = b
    out["paired_delta_vs_k0"] = boots
    print("\n=== paired delta vs k=0 (at-market, common support), day-block boot 1000 ===")
    for contract in ("pool", "trail"):
        print(f"-- {contract}")
        for k in OFFSETS:
            if k == 0:
                continue
            b = boots[f"{contract}|delta_vs_k0|{k}"]
            print(f"  k={k:+4d} n={b['n']:6d} delta={b['mean']:+.5f} "
                  f"CI95[{b['lo95']:+.5f},{b['hi95']:+.5f}] P(<=0)={b['p_le_0']:.3f}")

    json.dump(out, open(os.path.join(HERE, "X3_SWEEP_V1.json"), "w"), indent=1)
    np.savez_compressed(os.path.join(HERE, "x3_SWEEP_RAW.npz"),
                        **{f"{c}_{k}": raw[(c, k)]["r"] for c in ("pool", "trail")
                           for k in OFFSETS},
                        **{f"reason_{c}_{k}": raw[(c, k)]["reason"] for c in ("pool", "trail")
                           for k in OFFSETS},
                        support=sup, atm=atm)
    print("\nwrote X3_SWEEP_V1.json")


if __name__ == "__main__":
    main()
