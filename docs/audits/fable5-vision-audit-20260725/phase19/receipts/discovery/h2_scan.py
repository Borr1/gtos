"""h2_scan — enumerate EVERY cell of the live-expressible book under the repaired contract.

Writes H2_CELLS_V1.json (every cell, every axis) and prints a bounded summary.
"""
from __future__ import annotations

import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h2_lib as H  # noqa: E402

HRBLOCK = {}
for h in range(24):
    HRBLOCK[h] = ("h00_06" if h < 7 else "h07_11" if h < 12 else
                  "h12_16" if h < 17 else "h17_23")


def build():
    rows = H.load()
    H.add_vol_state(rows, key="symbol", n_tiles=3, field="rdp", out="vol")
    H.add_global_tiles(rows, "prob", "probq", 5)
    H.add_global_tiles(rows, "rdp", "rdpq", 10)
    H.add_global_tiles(rows, "cost_true", "costq", 10)
    for r in rows:
        r["hblock"] = HRBLOCK[int(r["hour"])]
        r["cbps_band"] = ("c_lt1" if r["c_bps"] < 1 else "c_1_2" if r["c_bps"] < 2 else
                          "c_2_4" if r["c_bps"] < 4 else "c_4_8" if r["c_bps"] < 8 else "c_ge8")
    return rows


AXES = [
    ("symbol", lambda r: r["symbol"]),
    ("family", lambda r: r["family"]),
    ("session", lambda r: r["session"]),
    ("hour", lambda r: "h%02d" % r["hour"]),
    ("hblock", lambda r: r["hblock"]),
    ("dow", lambda r: r["dow"]),
    ("side", lambda r: r["side"]),
    ("vol", lambda r: r["vol"]),
    ("month", lambda r: r["month"]),
    ("probq", lambda r: r["probq"]),
    ("rdpq", lambda r: r["rdpq"]),
    ("costq", lambda r: r["costq"]),
    ("cbps_band", lambda r: r["cbps_band"]),
    ("efp", lambda r: "efp_%s" % r["efp"]),
]

PAIRS = [
    ("symbol_x_session", lambda r: "%s|%s" % (r["symbol"], r["session"])),
    ("symbol_x_side", lambda r: "%s|%s" % (r["symbol"], r["side"])),
    ("symbol_x_vol", lambda r: "%s|%s" % (r["symbol"], r["vol"])),
    ("symbol_x_hblock", lambda r: "%s|%s" % (r["symbol"], r["hblock"])),
    ("symbol_x_dow", lambda r: "%s|%s" % (r["symbol"], r["dow"])),
    ("symbol_x_family", lambda r: "%s|%s" % (r["symbol"], r["family"])),
    ("family_x_session", lambda r: "%s|%s" % (r["family"], r["session"])),
    ("family_x_side", lambda r: "%s|%s" % (r["family"], r["side"])),
    ("family_x_vol", lambda r: "%s|%s" % (r["family"], r["vol"])),
    ("family_x_hblock", lambda r: "%s|%s" % (r["family"], r["hblock"])),
    ("session_x_side", lambda r: "%s|%s" % (r["session"], r["side"])),
    ("session_x_vol", lambda r: "%s|%s" % (r["session"], r["vol"])),
    ("session_x_hour", lambda r: "%s|h%02d" % (r["session"], r["hour"])),
    ("side_x_vol", lambda r: "%s|%s" % (r["side"], r["vol"])),
    ("dow_x_session", lambda r: "%s|%s" % (r["dow"], r["session"])),
    ("cbps_x_family", lambda r: "%s|%s" % (r["cbps_band"], r["family"])),
    ("cbps_x_session", lambda r: "%s|%s" % (r["cbps_band"], r["session"])),
    ("cbps_x_vol", lambda r: "%s|%s" % (r["cbps_band"], r["vol"])),
]

TRIPLES = [
    ("symbol_x_session_x_side", lambda r: "%s|%s|%s" % (r["symbol"], r["session"], r["side"])),
    ("symbol_x_family_x_session", lambda r: "%s|%s|%s" % (r["symbol"], r["family"], r["session"])),
    ("symbol_x_vol_x_side", lambda r: "%s|%s|%s" % (r["symbol"], r["vol"], r["side"])),
    ("family_x_session_x_side", lambda r: "%s|%s|%s" % (r["family"], r["session"], r["side"])),
    ("symbol_x_hblock_x_side", lambda r: "%s|%s|%s" % (r["symbol"], r["hblock"], r["side"])),
]


def main():
    rows = build()
    out = {"population": {"n": len(rows), "contract": H.GCOL,
                          "months": [m for m, _ in H.MONTHS]},
           "pooled": H.cell_stats(rows), "axes": {}, "pairs": {}, "triples": {}}
    for name, fn in AXES:
        g = H.group(rows, fn)
        out["axes"][name] = {k: H.cell_stats(v) for k, v in sorted(g.items())}
    for name, fn in PAIRS:
        g = H.group(rows, fn)
        out["pairs"][name] = {k: H.cell_stats(v) for k, v in sorted(g.items()) if len(v) >= 20}
    for name, fn in TRIPLES:
        g = H.group(rows, fn)
        out["triples"][name] = {k: H.cell_stats(v) for k, v in sorted(g.items()) if len(v) >= 20}

    # ---- Q3: is edge concentration independent of cost concentration?
    corr = {}
    for scope, book in (("axes", out["axes"]), ("pairs", out["pairs"]), ("triples", out["triples"])):
        for name, cells in book.items():
            ks = [k for k, v in cells.items() if v and v["n"] >= 100]
            if len(ks) < 4:
                continue
            gv = [cells[k]["gross_r"] for k in ks]
            cv = [cells[k]["cost_r"] for k in ks]
            gb = [cells[k]["gross_bps"] for k in ks]
            cb = [cells[k]["cost_bps"] for k in ks]
            nv = [cells[k]["net_r"] for k in ks]
            corr["%s.%s" % (scope, name)] = {
                "cells": len(ks),
                "spearman_gross_cost_r": H.spearman(gv, cv),
                "spearman_gross_cost_bps": H.spearman(gb, cb),
                "spearman_net_cost_r": H.spearman(nv, cv),
                "pearson_gross_cost_bps": H.pearson(gb, cb),
            }
    out["edge_cost_independence"] = corr

    with open(os.path.join(D, "H2_CELLS_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    # ---------- bounded print
    p = out["pooled"]
    print("POOLED n=%d gross=%.6f t=%.2f (clu %.2f) cost=%.6f net=%.6f  bps %.4f/%.4f  ratio_R=%.4f days+ %d/%d"
          % (p["n"], p["gross_r"], p["t_g"], p["t_g_clu"], p["cost_r"], p["net_r"],
             p["gross_bps"], p["cost_bps"], p["edge_cost_r"], p["days_pos_gross"], p["days"]))
    winners = []
    for scope in ("axes", "pairs", "triples"):
        for name, cells in out[scope].items():
            for k, v in cells.items():
                if v and v["n"] >= 100 and v["edge_cost_r"] and v["edge_cost_r"] > 1.0:
                    winners.append((v["edge_cost_r"], scope, name, k, v))
    winners.sort(reverse=True)
    print("CELLS with edge/cost > 1 at n>=100: %d" % len(winners))
    for r_, scope, name, k, v in winners[:40]:
        print("  %-5.2f %-26s %-38s n=%-6d g=%+.5f t=%+5.2f c=%.5f net=%+.5f d+%d/%d m(%s,%s,%s)"
              % (r_, name, k[:38], v["n"], v["gross_r"], v["t_g"] or 0, v["cost_r"], v["net_r"],
                 v["days_pos_gross"], v["days"],
                 v["net_2026-01"], v["net_2026-02"], v["net_2026-03"]))
    print("edge/cost independence (spearman gross vs cost, bps):")
    for k in ("axes.symbol", "axes.family", "axes.session", "axes.hour", "axes.vol",
              "pairs.symbol_x_session", "pairs.symbol_x_vol", "pairs.family_x_session"):
        c = corr.get(k)
        if c:
            print("  %-26s cells=%-4d sp(g,c)_r=%+.3f sp(g,c)_bps=%+.3f sp(net,c)_r=%+.3f"
                  % (k, c["cells"], c["spearman_gross_cost_r"] or 0,
                     c["spearman_gross_cost_bps"] or 0, c["spearman_net_cost_r"] or 0))


if __name__ == "__main__":
    main()
