"""B5 step (c2) — the nearest CONSTRUCTIVE variant, and the adversarial kill attempts.

Constructive variant.  The 1-day reversal fails on cost, but "cheap" was defined in bps and
that is the wrong metric.  What the strategy pays is cost divided by the volatility it is
harvesting: c_vol = (rt_bps/1e4) / sigma.  A 6 bps crypto at 4 %/day vol is CHEAPER in the
unit that matters than a 2 bps FX cross at 0.4 %/day.  Selecting on c_vol instead of bps is a
genuinely different universe and it had not been tried.

Kill attempts on whatever survives:
  K1  currency-overlap restatement (Lane 5's named residual threat): restrict FX to a set in
      which no two symbols share a non-USD currency, so a "cross-sectional" position cannot be
      a restatement of one currency's move.
  K2  era split, already in step (c).
  K3  the reversed book charged honestly -- the tradeable direction of a reversal cell is
      long-the-losers, so report sign-corrected net, not the raw negative.

Writes <OUT>/B5_COSTVOL_AND_KILLS_V1.json.
"""
import json, math, os, pickle, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
sys.path.insert(0, HERE)
import b5_06_xs as X

# K1: a maximal set of FX symbols sharing no currency other than USD.
USD_SPOKES = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
              "USDMXN", "USDNOK", "USDPLN", "USDSEK", "USDSGD", "USDZAR", "USDCZK",
              "USDHUF", "USDILS", "USDCNH", "USDHKD"]


def main():
    base = X.load()
    dates, syms, S, LC, OWN, VOL, HC, cls = base
    T, N = len(dates), len(syms)
    cost = json.load(open(os.path.join(OUT, "B5_SYMBOL_COST_V1.json")))["symbols"]
    trade = json.load(open(os.path.join(OUT, "B5_TRADEABILITY_V1.json")))["symbols"]
    ctx = {"base": base,
           "sig": {(lb, sk): X.own_cum(LC, OWN, S, T, N, syms, lb, sk) for _, lb, sk, _, _ in X.SIGNALS},
           "fwd": {h: X.own_fwd(LC, OWN, S, T, N, syms, h) for _, _, _, h, _ in X.SIGNALS}}
    cost_bps = {S[s]: cost[s]["roundtrip_cost_bps"] for s in syms if s in cost}

    # median trailing vol per symbol, and cost expressed in vol units
    medvol, cvol = {}, {}
    for s in syms:
        j = S[s]
        v = VOL[:, j]; v = v[np.isfinite(v) & (v > 0)]
        if len(v) < 100:
            continue
        medvol[s] = float(np.median(v))
        rt = cost[s]["roundtrip_cost_bps"] if s in cost else None
        if rt is not None:
            cvol[s] = (rt / 1e4) / medvol[s]

    ranked = sorted(cvol.items(), key=lambda kv: kv[1])
    res = {"cost_in_vol_units": {s: round(v, 5) for s, v in ranked},
           "median_daily_vol": {s: round(medvol[s], 5) for s, _ in ranked},
           "note": "c_vol = (roundtrip_bps/1e4) / median trailing daily log-return SD; "
                   "this is the cost the vol-normalised book actually pays per round trip",
           "cells": {}}
    print("cheapest 15 by cost/vol:", [(s, round(v, 4)) for s, v in ranked[:15]])
    print("dearest 8 by cost/vol:", [(s, round(v, 4)) for s, v in ranked[-8:]])

    def run(name, cols, min_names=20):
        if len(cols) < min_names:
            print(f"{name:26s} SKIP ({len(cols)} symbols < {min_names})"); return
        for sig, lb, sk, hold, mh in X.SIGNALS:
            r = X.backtest(ctx, cols, lb, sk, hold, mh, cost_bps=cost_bps,
                           nperm=1000, min_names=min_names)
            if not r:
                continue
            # K3: sign-corrected -- the tradeable direction of a reversal is long-the-losers
            g, n_ = r["gross_mean_volnorm"], r["net_mean_volnorm"]
            r["tradeable_direction"] = "long_losers(reversed)" if g < 0 else "long_winners"
            r["gross_edge_abs"] = abs(g)
            r["cost_per_rebal_volunits"] = (abs(g - n_) if n_ is not None else None)
            r["cost_over_gross_edge"] = ((abs(g - n_) / abs(g)) if (n_ is not None and g) else None)
            r["net_in_tradeable_direction"] = (abs(g) - abs(g - n_)) if n_ is not None else None
            res["cells"][f"{name}|{sig}"] = r
            cog = r["cost_over_gross_edge"]
            print(f"{name:26s} {sig:12s} n={r['n_rebal']:5d} u={r['median_universe']:3d} "
                  f"|g|={abs(g):.5f} t={r['gross_t']:+.2f} p={r['perm_p_two_sided']:.4f} "
                  f"cost={r['cost_per_rebal_volunits'] if r['cost_per_rebal_volunits'] is None else round(r['cost_per_rebal_volunits'],5)} "
                  f"cost/edge={('%.2f' % cog) if cog else 'NA'} "
                  f"NET={r['net_in_tradeable_direction'] if r['net_in_tradeable_direction'] is None else round(r['net_in_tradeable_direction'],5)} "
                  f"turn={r['turnover']:.2f}")

    def C(pred):
        return [S[s] for s in syms if pred(s)]

    k = len(ranked)
    cheap_half = {s for s, _ in ranked[: k // 2]}
    cheap_third = {s for s, _ in ranked[: k // 3]}
    run("COSTVOL_CHEAPEST_HALF", C(lambda s: s in cheap_half))
    run("COSTVOL_CHEAPEST_THIRD", C(lambda s: s in cheap_third))
    run("COSTVOL_CHEAP_TRADEABLE", C(lambda s: s in cheap_half and cost[s]["gtos_configured"]), min_names=14)
    # K1 currency-overlap control
    run("K1_USD_SPOKES_ONLY", C(lambda s: s in set(USD_SPOKES) and cost[s]["roundtrip_cost_known"]), min_names=12)
    run("K1_USD_SPOKES_ALL", C(lambda s: s in set(USD_SPOKES)), min_names=12)

    json.dump(res, open(os.path.join(OUT, "B5_COSTVOL_AND_KILLS_V1.json"), "w"), indent=1)
    print("written")


if __name__ == "__main__":
    main()
