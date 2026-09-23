#!/usr/bin/env python3
"""l1 pass 1 — the money surface: realized pool R/trade over target x stop on the ACTUAL paths."""
from __future__ import annotations
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from l1_lib import *  # noqa

OUT = os.path.join(HERE, "l1_SURFACE_V1.json")


def cost_of(r, mode):
    sp = r["spread_r"] or 0.0
    co = r["commission_r"] or 0.0
    sl = r["slip_r"] or 0.0
    sw = r["swap_r"] or 0.0
    if mode == "frozen":
        return (r["cost_r"] or 0.0)
    if mode == "sp73":
        return sp / 7.3 + co + sl + sw
    if mode == "sp85":
        return sp / 8.5 + co + sl + sw
    raise ValueError(mode)


def surface(recs, conv):
    out = {}
    N = len(recs)
    for T in T_GRID:
        for S in S_GRID:
            tot = 0.0; wins = 0; filled = 0; ntgt = 0; nstp = 0; npe = 0; nnf = 0
            netf = 0.0; net73 = 0.0
            bars = 0; barn = 0
            for r in recs:
                v, why, ib = cell(r, T, S, conv)
                tot += v
                if why == "no_fill":
                    nnf += 1
                    continue
                filled += 1
                if v > 0:
                    wins += 1
                netf += v - cost_of(r, "frozen")
                net73 += v - cost_of(r, "sp73")
                if why == "target":
                    ntgt += 1
                elif why == "stop":
                    nstp += 1
                else:
                    npe += 1
                if ib is not None:
                    bars += ib + 1; barn += 1
            out["T%.2f_S%.2f" % (T, S)] = {
                "T": T, "S": S, "n": N, "filled": filled, "no_fill": nnf,
                "gross_per_candidate": round(tot / N, 6),
                "gross_per_filled": round(tot / filled, 6) if filled else None,
                "win_rate_filled": round(wins / filled, 6) if filled else None,
                "target_rate_filled": round(ntgt / filled, 6) if filled else None,
                "stop_rate_filled": round(nstp / filled, 6) if filled else None,
                "pathend_rate_filled": round(npe / filled, 6) if filled else None,
                "net_frozen_per_candidate": round(netf / N, 6),
                "net_sp73_per_candidate": round(net73 / N, 6),
                "mean_exit_bar": round(bars / barn, 3) if barn else None,
            }
    return out


def main():
    recs = load()
    res = {"n_total": len(recs), "T_GRID": T_GRID, "S_GRID": S_GRID,
           "note": "gross_per_candidate divides by the WHOLE population; a no-fill books 0.0 R. "
                   "Costs are R-denominated on the ORIGINAL risk distance and are held fixed across "
                   "cells (exit management on an unchanged position size), so S<1 cells are NOT re-sized."}
    for popname in ("ALL", "TAKEABLE", "TAKEABLE_FIRSTEM"):
        P = pop(recs, popname)
        for conv, cname in (("r", "REAL"), ("s", "STRICT"), ("b", "BLIND")):
            res["%s|%s" % (popname, cname)] = surface(P, conv)
        res["%s|n" % popname] = len(P)
    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1)

    # compact print: TAKEABLE|REAL surface
    S = res["TAKEABLE|REAL"]
    print("POP TAKEABLE n=%d  (fill convention REAL)  gross R per candidate" % res["TAKEABLE|n"])
    print("  T\\S " + "".join("%9.2f" % s for s in S_GRID))
    best = None
    for T in T_GRID:
        row = "%5.2f" % T
        for s in S_GRID:
            c = S["T%.2f_S%.2f" % (T, s)]
            row += "%9.4f" % c["gross_per_candidate"]
            if best is None or c["gross_per_candidate"] > best[0]:
                best = (c["gross_per_candidate"], T, s, c)
        print(row)
    print("BEST cell T=%.2f S=%.2f gross/cand=%.4f  per_filled=%.4f win=%.4f tgt=%.4f stop=%.4f pe=%.4f nofill=%d"
          % (best[1], best[2], best[0], best[3]["gross_per_filled"], best[3]["win_rate_filled"],
             best[3]["target_rate_filled"], best[3]["stop_rate_filled"], best[3]["pathend_rate_filled"],
             best[3]["no_fill"]))
    base = S["T2.00_S1.00"]
    print("BASELINE T=2.00 S=1.00 gross/cand=%.4f per_filled=%.4f win=%.4f nofill=%d"
          % (base["gross_per_candidate"], base["gross_per_filled"], base["win_rate_filled"], base["no_fill"]))
    for popname in ("ALL", "TAKEABLE"):
        for cname in ("REAL", "STRICT", "BLIND"):
            s = res["%s|%s" % (popname, cname)]
            b = max(s.values(), key=lambda c: c["gross_per_candidate"])
            print("%s|%-6s best T=%.2f S=%.2f = %+.4f | T2/S1 = %+.4f"
                  % (popname, cname, b["T"], b["S"], b["gross_per_candidate"],
                     s["T2.00_S1.00"]["gross_per_candidate"]))


if __name__ == "__main__":
    main()
