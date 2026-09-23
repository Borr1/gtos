#!/usr/bin/env python3
"""l7_sweep — hunt every inverted cell across family x session x symbol x side x hour x vol.

Two bases, always reported side by side:
  POOL   = gross_r, the fill-BLIND convention every published number in the brief uses.
  HONEST = orig_honest_r, +2R/-1R first touch requiring the entry limit to be traded first.
And the inverse of each cell measured the same two ways (inv_blind_r / inv_honest_r).

A cell is only a GENUINE inversion if inv_honest_r > 0 with the past-stop artifact removed.
"""
import gzip, json, os, math, collections, itertools, sys
HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(HERE, "l7_BASE.jsonl.gz")
OUT = os.path.join(HERE, "L7_SWEEP_V1.json")

def mean(v): return sum(v) / len(v) if v else None
def be_realized(v):
    w = [x for x in v if x > 1e-9]; l = [x for x in v if x <= 1e-9]
    if not w or not l: return None
    wm, lm = mean(w), mean(l)
    if wm - lm == 0: return None
    return -lm / (wm - lm)

def binom_p_less(k, n, p):
    """P(X <= k) under Binomial(n,p) -- one-sided, win rate BELOW breakeven."""
    if n == 0: return None
    lg = math.lgamma
    tot = 0.0
    for i in range(0, k + 1):
        tot += math.exp(lg(n+1)-lg(i+1)-lg(n-i+1) + i*math.log(max(p,1e-15)) + (n-i)*math.log(max(1-p,1e-15)))
    return min(1.0, tot)

def stats(v, basis):
    """v = list of rows. basis = column name."""
    x = [r[basis] for r in v]
    n = len(x)
    w = sum(1 for a in x if a > 1e-9)
    tgt = mean([r["policy_target_r"] for r in v if r["policy_target_r"] is not None]) or 2.0
    be_decl = 1.0 / (1.0 + tgt)
    wr = w / n
    return dict(n=n, win=wr, mean=mean(x), be_declared=be_decl,
                be_realized=be_realized(x), deficit=be_decl - wr, score=(be_decl - wr) * n,
                p_below=binom_p_less(w, n, be_decl))

DIMS = {
 "family": lambda r: r["family"],
 "symbol": lambda r: r["symbol"],
 "side": lambda r: r["side"],
 "session": lambda r: r["route_session"],
 "hour": lambda r: "h%02d" % r["hour"],
 "vol": lambda r: r["vol_state"],
}
COMBOS = [
 ("family",), ("symbol",), ("side",), ("session",), ("hour",), ("vol",),
 ("family","side"), ("family","session"), ("family","symbol"), ("family","hour"), ("family","vol"),
 ("symbol","side"), ("symbol","session"), ("symbol","hour"), ("symbol","vol"),
 ("side","session"), ("side","hour"), ("side","vol"), ("session","hour"), ("session","vol"),
 ("family","side","session"), ("family","symbol","side"), ("family","side","vol"),
 ("family","session","vol"), ("symbol","side","session"), ("symbol","side","vol"),
 ("family","symbol","session"), ("family","symbol","vol"),
 ("family","symbol","side","session"), ("family","symbol","side","vol"),
 ("family","symbol","side","session","vol"),
]
MINN = 30

def main():
    rows = [json.loads(l) for l in gzip.open(BASE, "rt")]
    pops = {
      "ALL": rows,
      "TRADEABLE": [r for r in rows if r["born_state"] != "born_past_stop"],
      "TRADEABLE_FIRSTEM": [r for r in rows if r["born_state"] != "born_past_stop" and r["is_first_emission"]],
    }
    res = {"population_sizes": {k: len(v) for k, v in pops.items()}, "cells": {}}
    for popname, pop in pops.items():
        cells = []
        for combo in COMBOS:
            g = collections.defaultdict(list)
            for r in pop:
                g[tuple(DIMS[d](r) for d in combo)].append(r)
            for kv, v in g.items():
                if len(v) < MINN: continue
                sp = stats(v, "gross_r")
                sh = stats(v, "orig_honest_r")
                si = stats(v, "inv_honest_r")
                sib = stats(v, "inv_blind_r")
                ps = sum(1 for r in v if r["born_state"] == "born_past_stop")
                cells.append(dict(
                    dims="|".join(combo), key="|".join(map(str, kv)), n=len(v),
                    n_first=sum(1 for r in v if r["is_first_emission"]),
                    past_stop_n=ps, past_stop_share=ps/len(v),
                    pool_win=sp["win"], pool_mean=sp["mean"], be_declared=sp["be_declared"],
                    pool_deficit=sp["deficit"], pool_score=sp["score"], pool_p_below=sp["p_below"],
                    pool_be_realized=sp["be_realized"],
                    honest_win=sh["win"], honest_mean=sh["mean"], honest_deficit=sh["deficit"],
                    honest_score=sh["score"], honest_p_below=sh["p_below"],
                    inv_honest_mean=si["mean"], inv_honest_win=si["win"],
                    inv_blind_mean=sib["mean"], inv_blind_win=sib["win"],
                ))
        cells.sort(key=lambda c: -c["pool_score"])
        res["cells"][popname] = cells
    with open(OUT, "w") as fh: json.dump(res, fh, indent=1)
    print("cells:", {k: len(v) for k, v in res["cells"].items()})
    print("\n=== TOP 25 by pool_score (population ALL) ===")
    print(f"{'dims':34s} {'key':40s} {'n':>6s} {'ps%':>5s} {'win':>7s} {'be':>6s} {'defc':>7s} {'score':>7s} {'poolR':>8s} {'honR':>8s} {'invHR':>8s}")
    for c in res["cells"]["ALL"][:25]:
        print(f"{c['dims'][:34]:34s} {c['key'][:40]:40s} {c['n']:6d} {100*c['past_stop_share']:5.1f} "
              f"{100*c['pool_win']:7.2f} {100*c['be_declared']:6.2f} {100*c['pool_deficit']:7.2f} {c['pool_score']:7.1f} "
              f"{c['pool_mean']:+8.4f} {c['honest_mean']:+8.4f} {c['inv_honest_mean']:+8.4f}")

if __name__ == "__main__":
    main()
