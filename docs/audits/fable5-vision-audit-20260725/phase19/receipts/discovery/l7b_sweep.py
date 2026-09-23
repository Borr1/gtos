#!/usr/bin/env python3
"""l7 pass 2 (V2) — the inversion sweep, on the symmetric arena.

Supersedes the dead prior agent's L7_SWEEP_V1.json (same substrate, independently written
walker, agrees to 4 dp; this one adds the coin-flip decomposition, the paired delta, the
per-day stability check and the de-duplicated variant).

POPULATIONS
  ATLIMIT  mkt_r_prev_close == 0  -- entry IS the decision-instant market. Both directions
           fill at the same instant at the same price. Zero fill asymmetry. PUREST.
  SYM      |mkt_r_prev_close| < 1 -- neither side's stop was already breached at the
           decision instant, so the inversion question is well posed.
  CLEAN    mkt > -1 (w0-capture's tradeable set; the inverse is NOT symmetric here).
  ALL      whole pool, reference only.

METRICS per cell
  o_mean/i_mean   fill-honest walked R per FILLED order (2R target, -1R stop, tie->stop)
  coin            (o+i)/2  = the direction-free value of the geometry on these paths
  dirsig          (i-o)/2  = the magnitude of the direction signal; the system holds the
                  WRONG sign wherever this is positive
  deficit_decl    1/3 - o_win  (win rate below the DECLARED 2R breakeven)
  score_decl      deficit_decl * n  -- the task's requested ranking
"""
import json, os, sys, math, collections

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import l7_lib as L

MINN = 30
BE_DECL = 1.0 / 3.0


def volstate(rows):
    bysym = collections.defaultdict(list)
    for r in rows:
        if r["rd_pct"] is not None:
            bysym[r["sym"]].append(r["rd_pct"])
    cuts = {}
    for s, v in bysym.items():
        v = sorted(v)
        cuts[s] = (v[len(v) // 3], v[2 * len(v) // 3])
    for r in rows:
        c = cuts.get(r["sym"])
        r["vol"] = None if (c is None or r["rd_pct"] is None) else (
            "vTIGHT" if r["rd_pct"] <= c[0] else ("vMID" if r["rd_pct"] <= c[1] else "vWIDE"))
    return cuts


def tstat(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in v) / n)
    return round(m / (sd / math.sqrt(n)), 3) if sd > 0 else None


def cell(rs):
    of = [r for r in rs if r["om_x"] != "no_fill"]
    inf = [r for r in rs if r["im_x"] != "no_fill"]
    both = [r for r in rs if r["om_x"] != "no_fill" and r["im_x"] != "no_fill"]
    o = [r["om_r"] for r in of]
    i = [r["im_r"] for r in inf]
    coin = [(r["om_r"] + r["im_r"]) / 2 for r in both]
    dsg = [(r["im_r"] - r["om_r"]) / 2 for r in both]
    ow = sum(1 for x in o if x > 0) / len(o) if o else None
    iw = sum(1 for x in i if x > 0) / len(i) if i else None
    owin = [x for x in o if x > 0]
    olos = [x for x in o if x <= 0]
    wm = sum(owin) / len(owin) if owin else 0.0
    lm = sum(olos) / len(olos) if olos else 0.0
    be_real = abs(lm) / (wm + abs(lm)) if (wm + abs(lm)) > 0 else None
    out = {
        "n": len(rs), "n_of": len(o), "n_if": len(i),
        "o_mean": round(sum(o) / len(o), 5) if o else None, "o_win": round(ow, 5) if ow is not None else None,
        "o_t": tstat(o),
        "i_mean": round(sum(i) / len(i), 5) if i else None, "i_win": round(iw, 5) if iw is not None else None,
        "i_t": tstat(i),
        "coin": round(sum(coin) / len(coin), 5) if coin else None, "coin_t": tstat(coin),
        "dirsig": round(sum(dsg) / len(dsg), 5) if dsg else None, "dirsig_t": tstat(dsg),
        "o_payoff": round(wm / abs(lm), 4) if lm else None,
        "be_real": round(be_real, 5) if be_real else None,
        "cost_r": round(L.mean([r["cost_r"] for r in rs]) or 0.0, 5),
        "i_net_frozen": round((sum(i) / len(i) - (L.mean([r["cost_r"] for r in rs]) or 0.0)), 5) if i else None,
        "i_tgt_rate": round(sum(1 for r in inf if r["im_x"] == "target") / len(inf), 5) if inf else None,
        "o_tgt_rate": round(sum(1 for r in of if r["om_x"] == "target") / len(of), 5) if of else None,
    }
    if ow is not None:
        out["deficit_decl"] = round(BE_DECL - ow, 5)
        out["score_decl"] = round((BE_DECL - ow) * len(o), 2)
    if be_real is not None and ow is not None:
        out["deficit_real"] = round(be_real - ow, 5)
        out["score_real"] = round((be_real - ow) * len(o), 2)
    return out


DIMS = {
    "fam": lambda r: r["fam"], "sym": lambda r: r["sym"], "side": lambda r: r["side"],
    "sess": lambda r: r["sess"], "kz": lambda r: r["kz"], "hour": lambda r: "h%02d" % r["hour"],
    "vol": lambda r: r["vol"], "born": lambda r: r["born"], "tf": lambda r: r["tf"],
    "abucket": lambda r: r["abucket"], "blocker": lambda r: r["blocker"],
}

COMBOS = [
    ("fam",), ("sym",), ("side",), ("sess",), ("kz",), ("hour",), ("vol",), ("born",), ("tf",),
    ("abucket",), ("blocker",),
    ("fam", "side"), ("fam", "sess"), ("fam", "sym"), ("fam", "hour"), ("fam", "vol"), ("fam", "kz"),
    ("sym", "side"), ("sym", "sess"), ("sess", "side"), ("side", "hour"), ("sym", "hour"),
    ("side", "vol"), ("sym", "vol"), ("sess", "vol"), ("fam", "tf"), ("fam", "blocker"),
    ("fam", "sess", "side"), ("fam", "sym", "side"), ("fam", "vol", "side"), ("fam", "sess", "vol"),
    ("sym", "sess", "side"), ("fam", "sym", "sess"), ("fam", "hour", "side"),
]


def sweep(rows, popname, minn=MINN):
    out = []
    for combo in COMBOS:
        g = collections.defaultdict(list)
        for r in rows:
            k = tuple(DIMS[d](r) for d in combo)
            if any(x is None for x in k):
                continue
            g[k].append(r)
        for k, v in g.items():
            if len(v) < minn:
                continue
            c = cell(v)
            c["pop"] = popname
            c["dims"] = "|".join(combo)
            c["cell"] = "|".join(str(x) for x in k)
            out.append(c)
    return out


def main():
    rows = L.load()
    cuts = volstate(rows)
    ok = [r for r in rows if r["mkt"] is not None]
    pops = {
        "ATLIMIT": [r for r in ok if r["mkt"] == 0.0],
        "SYM": [r for r in ok if abs(r["mkt"]) < 1.0],
        "SYM_DEDUP": [r for r in ok if abs(r["mkt"]) < 1.0 and r["first"]],
        "CLEAN": [r for r in ok if r["mkt"] > -1.0],
        "ALL": rows,
    }
    res = {"minn": MINN,
           "vol_cuts": {k: [round(a, 6), round(b, 6)] for k, (a, b) in cuts.items()},
           "pop_sizes": {k: len(v) for k, v in pops.items()},
           "pop_headline": {k: cell(v) for k, v in pops.items()},
           "cells": []}
    for p, v in pops.items():
        res["cells"] += sweep(v, p)
    with open(os.path.join(D, "L7_SWEEP_V2.json"), "w") as f:
        json.dump(res, f, indent=1)
    print("cells", len(res["cells"]), res["pop_sizes"])
    for k, v in res["pop_headline"].items():
        print("%-10s n=%6d o=%+.5f(win %.4f) i=%+.5f(win %.4f) coin=%+.5f dir=%+.5f t=%s"
              % (k, v["n"], v["o_mean"], v["o_win"], v["i_mean"], v["i_win"], v["coin"], v["dirsig"], v["dirsig_t"]))


if __name__ == "__main__":
    main()
