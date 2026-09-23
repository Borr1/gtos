"""B5 step (c3) — the ANCHOR DECOMPOSITION, mandatory for any close-anchored daily signal.

A sibling lane established that Lane 5's 1-day cross-sectional FX reversal is an anchor
artifact: the leg of the forward return that shares the signal's own close price carries the
whole effect, and every tradeable anchor flips the sign.  Root cause is the FX rollover --
tick-measured EURUSD close spread is 3.06 bp at broker hour 00 against 0.09 bp elsewhere, 34x.
A signal that ends on close_i and a forward that starts on close_i share that measurement
error with opposite sign, which manufactures reversal mechanically.

This script splits every reversal/momentum cell into:
    GAP0  forward = lc[i+1] - lc[i]      -- shares the signal's terminal close.  CONTAMINATED.
    GAP1  forward = lc[i+2] - lc[i+1]    -- shares nothing with the signal.  TRADEABLE, primary.
    GAP2  forward = lc[i+3] - lc[i+2]    -- a second clean lag, as a consistency check.

If GAP1 is not significant the pooled GAP0 number is not a finding.

Bucketing note: these D1 bars are the BROKER's daily bars (server midnight =
America/New_York + 7h, per src/utils/broker_clock.py).  They are already broker wall clock;
no UTC conversion is applied anywhere in this lane, so a rollover cannot be smeared across
two buckets by DST.

Writes <OUT>/B5_ANCHOR_DECOMPOSITION_V1.json.
"""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
sys.path.insert(0, HERE)
import b5_06_xs as X


def own_fwd_gap(LC, OWN, S, T, N, syms, hold, gap):
    """Forward return over `hold` own-observations, starting `gap` observations AFTER the
    signal's terminal close.  gap=0 shares that close; gap>=1 does not."""
    out = np.full((T, N), np.nan)
    k = gap + hold
    for s in syms:
        j = S[s]; ts = OWN[s]; lc = LC[ts, j]; L = len(lc)
        if L <= k:
            continue
        out[ts[:L - k], j] = lc[k:] - lc[gap:L - hold]
    return out


def main():
    base = X.load()
    dates, syms, S, LC, OWN, VOL, HC, cls = base
    T, N = len(dates), len(syms)
    cost = json.load(open(os.path.join(OUT, "B5_SYMBOL_COST_V1.json")))["symbols"]
    cost_bps = {S[s]: cost[s]["roundtrip_cost_bps"] for s in syms if s in cost}

    SIGS = [("XS_REV_1D", 1, 0, 1, 120), ("XS_REV_5D", 5, 0, 5, 120), ("XS_MOM_12_1", 252, 21, 21, 300)]
    ctx = {"base": base,
           "sig": {(lb, sk): X.own_cum(LC, OWN, S, T, N, syms, lb, sk) for _, lb, sk, _, _ in SIGS},
           "fwd": {}}

    def C(pred):
        return [S[s] for s in syms if pred(s)]

    kn = lambda s: cost[s]["roundtrip_cost_known"]
    UNIV = {
        "ALL_166": C(lambda s: True),
        "FX_43": C(lambda s: cls.get(s) == "fx"),
        "CRYPTO_31": C(lambda s: cls.get(s) == "crypto"),
        "INDEX_14": C(lambda s: cls.get(s) == "index"),
        "EQUITY_58": C(lambda s: cls.get(s) == "equity"),
        "ALL_KNOWN_COST_84": C(lambda s: kn(s)),
        "TRADEABLE_NOW_41": C(lambda s: cost[s]["gtos_configured"]),
    }
    MINN = {"INDEX_14": 12}
    res = {"design": {"GAP0": "forward shares the signal's terminal close -- CONTAMINATED control",
                      "GAP1": "forward starts one observation later -- TRADEABLE, primary",
                      "GAP2": "second clean lag, consistency check",
                      "clock": "broker daily bars (server midnight = America/New_York + 7h); no UTC conversion",
                      "seed": X.SEED, "nperm": 1000},
           "cells": {}}
    print(f"{'universe':20s} {'signal':12s} {'gap':>3s} {'n':>5s} {'mean':>9s} {'t':>7s} {'permp':>7s} {'net_dir':>9s}")
    for uname, cols in UNIV.items():
        mn = MINN.get(uname, 20)
        if len(cols) < mn:
            continue
        for sname, lb, sk, hold, mh in SIGS:
            for gap in (0, 1, 2):
                key = (hold, gap)
                if key not in ctx["fwd"]:
                    ctx["fwd"][key] = own_fwd_gap(LC, OWN, S, T, N, syms, hold, gap)
                ctx["fwd"][hold] = ctx["fwd"][key]      # backtest() reads ctx["fwd"][hold]
                r = X.backtest(ctx, cols, lb, sk, hold, mh, cost_bps=cost_bps,
                               nperm=1000, min_names=mn)
                if not r:
                    continue
                g = r["gross_mean_volnorm"]; nm = r["net_mean_volnorm"]
                r["net_in_tradeable_direction"] = (abs(g) - abs(g - nm)) if nm is not None else None
                res["cells"][f"{uname}|{sname}|GAP{gap}"] = r
                print(f"{uname:20s} {sname:12s} {gap:3d} {r['n_rebal']:5d} {g:+9.5f} {r['gross_t']:+7.2f} "
                      f"{r['perm_p_two_sided']:7.4f} "
                      f"{(('%+9.5f' % r['net_in_tradeable_direction']) if r['net_in_tradeable_direction'] is not None else '       NA')}")
    json.dump(res, open(os.path.join(OUT, "B5_ANCHOR_DECOMPOSITION_V1.json"), "w"), indent=1)
    print("written")


if __name__ == "__main__":
    main()
