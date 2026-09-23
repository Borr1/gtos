"""h2_winners — enumerate EVERY cell that pays, with n, stability and caveat.

Merges the h2_scan stability block (per-month, split-half, day positivity) with the
h2_frontier price-space block (gross_bps, cost_bps, margin_bps, excess over pooled).

Money metric = net_r (R per trade), because live sizing is fixed-fractional risk: R IS money.
Price-space metric = margin_bps = gross_bps - cost_bps, for division against h1's cost work.

Identity: net_r = (gross_bps - cost_bps) / (rdp * 1e4).
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h2_lib as H  # noqa: E402
import h2_scan  # noqa: E402

KS = [0, 1, 2, 3, 5, 10, 15, 20, 30]
POOLED_G = 0.038342


def main():
    rows = h2_scan.build()
    n = len(rows)
    scan = json.load(open(os.path.join(D, "H2_CELLS_V1.json")))
    fr = json.load(open(os.path.join(D, "H2_FRONTIER_V1.json")))
    fmap = {(c["axis"], c["cell"]): c for c in fr["cells"]}

    defs = {name: fn for name, fn in (h2_scan.AXES + h2_scan.PAIRS + h2_scan.TRIPLES)}

    # --- merge
    merged = []
    for scope in ("axes", "pairs", "triples"):
        for axis, cells in scan[scope].items():
            for cell, s in cells.items():
                if not s:
                    continue
                f = fmap.get((axis, cell))
                if not f:
                    continue
                m = dict(s)
                m.update({"axis": axis, "cell": cell, "scope": scope,
                          "gross_bps": f["gross_bps"], "cost_bps": f["cost_bps"],
                          "margin_bps": f["margin_bps"], "rdp_bps": f["rdp_bps"],
                          "t_net_clu": f["t_net_clu"], "t_edge_vs_pooled": f["t_edge_vs_pooled"],
                          "expected_net_flat_edge": f["expected_net_flat_edge"],
                          "excess_over_flat": f["excess_over_flat"]})
                merged.append(m)

    def stable(m):
        """3-month sign consistency AND split-half sign consistency on NET."""
        mm = [m.get("net_2026-01"), m.get("net_2026-02"), m.get("net_2026-03")]
        if any(x is None for x in mm):
            return False
        return (all(x > 0 for x in mm) and (m.get("net_odd") or -1) > 0
                and (m.get("net_even") or -1) > 0)

    winners = [m for m in merged if m["n"] >= 100 and m["net_r"] > 0]
    for m in winners:
        m["months_net_positive"] = sum(1 for k in ("net_2026-01", "net_2026-02", "net_2026-03")
                                       if (m.get(k) or 0) > 0)
        m["splithalf_both_positive"] = bool((m.get("net_odd") or -1) > 0
                                            and (m.get("net_even") or -1) > 0)
        m["STABLE"] = stable(m)
    winners.sort(key=lambda x: -x["net_r"])

    # --- k-ladder robustness for the stable winners and the top-30 by net
    probe = [w for w in winners if w["STABLE"]]
    seen = {(w["axis"], w["cell"]) for w in probe}
    for w in winners[:30]:
        if (w["axis"], w["cell"]) not in seen:
            probe.append(w)
            seen.add((w["axis"], w["cell"]))
    ladders = {}
    for w in probe:
        fn = defs[w["axis"]]
        sub = [r for r in rows if fn(r) == w["cell"]]
        lad = {}
        for k in KS:
            col = "K%d_TRAIL025" % k
            v = [r[col] for r in sub if r.get(col) is not None]
            cst = [r["c"] for r in sub if r.get(col) is not None]
            if len(v) < 20:
                lad["k%d" % k] = None
                continue
            lad["k%d" % k] = {"n": len(v), "gross_r": round(sum(v) / len(v), 6),
                              "net_r": round((sum(v) - sum(cst)) / len(v), 6)}
        # shipped-exit contrast at k=5 and the as-shipped arm k=0/INC
        for col, tag in (("K5_INC", "k5_INC"), ("K0_INC", "k0_INC_asshipped"),
                         ("K5_STOPONLY", "k5_STOPONLY"), ("K5_TS90S1", "k5_TS90S1")):
            v = [r[col] for r in sub if r.get(col) is not None]
            cst = [r["c"] for r in sub if r.get(col) is not None]
            lad[tag] = ({"n": len(v), "gross_r": round(sum(v) / len(v), 6),
                         "net_r": round((sum(v) - sum(cst)) / len(v), 6)} if len(v) >= 20 else None)
        ladders["%s::%s" % (w["axis"], w["cell"])] = lad

    # --- price-space frontier: cells with margin_bps > 0
    margin = [m for m in merged if m["n"] >= 100 and m["margin_bps"] > 0]
    margin.sort(key=lambda x: -x["margin_bps"])

    # --- edge magnitude: cells at >=2x and >=3x the pooled edge
    big_r = sorted([m for m in merged if m["n"] >= 100 and m["gross_r"] >= 2 * POOLED_G],
                   key=lambda x: -x["gross_r"])
    big_bps = sorted([m for m in merged if m["n"] >= 100
                      and m["gross_bps"] >= 2 * fr["pooled_gross_bps"]],
                     key=lambda x: -x["gross_bps"])

    # --- Q3: do edge and cost concentration coincide?  measured in both frames
    big = [m for m in merged if m["n"] >= 100]
    q3 = {"all_cells": {
        "cells": len(big),
        "spearman_gross_r_cost_r": H.spearman([m["gross_r"] for m in big], [m["cost_r"] for m in big]),
        "spearman_gross_bps_cost_bps": H.spearman([m["gross_bps"] for m in big], [m["cost_bps"] for m in big]),
        "spearman_net_r_cost_r": H.spearman([m["net_r"] for m in big], [m["cost_r"] for m in big]),
        "spearman_margin_bps_cost_bps": H.spearman([m["margin_bps"] for m in big], [m["cost_bps"] for m in big]),
    }}
    for axis in sorted({m["axis"] for m in big}):
        sub = [m for m in big if m["axis"] == axis]
        if len(sub) < 5:
            continue
        q3[axis] = {
            "cells": len(sub),
            "spearman_gross_r_cost_r": H.spearman([m["gross_r"] for m in sub], [m["cost_r"] for m in sub]),
            "spearman_gross_bps_cost_bps": H.spearman([m["gross_bps"] for m in sub], [m["cost_bps"] for m in sub]),
            "spearman_net_r_cost_r": H.spearman([m["net_r"] for m in sub], [m["cost_r"] for m in sub]),
        }

    # --- within-symbol cost_bps dispersion (does the cost artifact carry hour structure?)
    bysym = {}
    for r in rows:
        bysym.setdefault(r["symbol"], []).append(r["c_bps"])
    disp = {s: {"n": len(v), "min": round(min(v), 5), "med": round(float(np.median(v)), 5),
                "max": round(max(v), 5), "cv": round(float(np.std(v) / np.mean(v)), 5)}
            for s, v in sorted(bysym.items())}

    # --- family cost dispersion (the swarm's 12.1x closing observation)
    byfam = {}
    for r in rows:
        byfam.setdefault(r["family"], []).append(r)
    fam = {}
    for f, v in sorted(byfam.items()):
        cr = [x["c"] for x in v]
        cbv = [x["c_bps"] for x in v]
        gv = [x["g"] for x in v]
        gbv = [x["g_bps"] for x in v]
        fam[f] = {"n": len(v), "cost_r": round(float(np.mean(cr)), 6),
                  "cost_bps": round(float(np.mean(cbv)), 5),
                  "gross_r": round(float(np.mean(gv)), 6),
                  "gross_bps": round(float(np.mean(gbv)), 5),
                  "net_r": round(float(np.mean(gv) - np.mean(cr)), 6),
                  "margin_bps": round(float(np.mean(gbv) - np.mean(cbv)), 5),
                  "edge_cost_r": round(float(np.mean(gv) / np.mean(cr)), 4),
                  "rdp_bps": round(float(np.mean([x["rdp"] for x in v])) * 1e4, 3)}
    cr_vals = [v["cost_r"] for v in fam.values()]
    cb_vals = [v["cost_bps"] for v in fam.values()]
    fam_disp = {"cost_r_ratio_max_min": round(max(cr_vals) / min(cr_vals), 3),
                "cost_bps_ratio_max_min": round(max(cb_vals) / min(cb_vals), 3)}

    out = {"population": {"n": n, "contract": "K5_TRAIL025 (delay 5 M1 + 0.25R trail)",
                          "months": ["2026-01", "2026-02", "2026-03"],
                          "pooled_gross_r": POOLED_G,
                          "pooled_gross_bps": fr["pooled_gross_bps"],
                          "pooled_cost_r": fr["pooled_cost_r"],
                          "pooled_cost_bps": fr["pooled_cost_bps"],
                          "rows_on_repeated_candidate_id": 198},
           "winners_net_positive_n100": winners,
           "n_winners": len(winners),
           "n_winners_stable": sum(1 for w in winners if w["STABLE"]),
           "price_space_frontier_margin_bps_positive": margin,
           "n_margin_positive": len(margin),
           "edge_ge_2x_pooled_r": big_r, "edge_ge_2x_pooled_bps": big_bps,
           "q3_edge_vs_cost_concentration": q3,
           "within_symbol_cost_bps_dispersion": disp,
           "family_table": fam, "family_cost_dispersion": fam_disp,
           "k_ladders": ladders,
           "winner_decomposition": fr["winner_decomposition"],
           "permutation_null": fr["permutation_null"]}
    with open(os.path.join(D, "H2_WINNERS_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    # ------------------------------------------------------------- bounded print
    print("winners (net_r>0, n>=100): %d ; STABLE (3/3 months + both split-halves): %d"
          % (len(winners), out["n_winners_stable"]))
    print("%-4s %-26s %-38s %6s %9s %9s %9s %7s %7s %7s %7s %s"
          % ("#", "axis", "cell", "n", "gross_r", "cost_r", "net_r", "tnet", "tclu", "gbps", "cbps", "m/3"))
    for i, w in enumerate(winners[:35], 1):
        print("%-4d %-26s %-38s %6d %+9.5f %9.5f %+9.5f %7.2f %7.2f %7.3f %7.3f %d/3%s"
              % (i, w["axis"], w["cell"][:38], w["n"], w["gross_r"], w["cost_r"], w["net_r"],
                 w["t_net"] or 0, w["t_net_clu"] or 0, w["gross_bps"], w["cost_bps"],
                 w["months_net_positive"], " *STABLE*" if w["STABLE"] else ""))
    print("\nSTABLE winners in full:")
    for w in [x for x in winners if x["STABLE"]]:
        print("  %-26s %-36s n=%-5d net=%+.5f tclu=%+.2f jan %+.4f feb %+.4f mar %+.4f odd %+.4f even %+.4f d+%d/%d"
              % (w["axis"], w["cell"][:36], w["n"], w["net_r"], w["t_net_clu"] or 0,
                 w["net_2026-01"], w["net_2026-02"], w["net_2026-03"],
                 w["net_odd"], w["net_even"], w["days_pos_net"], w["days"]))
    print("\nfamily table (cost dispersion max/min: R %.2fx  bps %.2fx):"
          % (fam_disp["cost_r_ratio_max_min"], fam_disp["cost_bps_ratio_max_min"]))
    for f, v in sorted(fam.items(), key=lambda kv: kv[1]["cost_bps"]):
        print("  %-34s n=%-5d gbps=%+7.4f cbps=%7.4f margin=%+8.4f | g_r=%+.5f c_r=%.5f net=%+.5f ratio=%.3f rdp=%.1f"
              % (f, v["n"], v["gross_bps"], v["cost_bps"], v["margin_bps"], v["gross_r"],
                 v["cost_r"], v["net_r"], v["edge_cost_r"], v["rdp_bps"]))
    print("\nQ3 edge-vs-cost concentration:")
    a = q3["all_cells"]
    print("  ALL %d cells: sp(gross_r,cost_r)=%+.3f  sp(gross_bps,cost_bps)=%+.3f  sp(net_r,cost_r)=%+.3f"
          % (a["cells"], a["spearman_gross_r_cost_r"], a["spearman_gross_bps_cost_bps"],
             a["spearman_net_r_cost_r"]))
    for ax in ("symbol", "family", "session", "vol", "hour", "symbol_x_session", "symbol_x_vol"):
        if ax in q3:
            v = q3[ax]
            print("  %-20s cells=%-4d sp(g_r,c_r)=%+.3f sp(g_bps,c_bps)=%+.3f sp(net,c)=%+.3f"
                  % (ax, v["cells"], v["spearman_gross_r_cost_r"],
                     v["spearman_gross_bps_cost_bps"], v["spearman_net_r_cost_r"]))
    print("\nprice-space frontier: %d cells with margin_bps>0 (top 12):" % len(margin))
    for m in margin[:12]:
        print("  %-26s %-36s n=%-5d gbps=%+7.4f cbps=%6.4f margin=%+7.4f net_r=%+.5f rdp=%.1f"
              % (m["axis"], m["cell"][:36], m["n"], m["gross_bps"], m["cost_bps"],
                 m["margin_bps"], m["net_r"], m["rdp_bps"]))


if __name__ == "__main__":
    main()
