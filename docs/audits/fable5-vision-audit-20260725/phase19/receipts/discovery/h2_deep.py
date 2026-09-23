"""h2_deep — the parts of the hunt that need more than a cell table.

  A  GER40 anatomy: every axis inside the one instrument that pays.
  B  the affordable-book ladder: what a book restricted to the cheapest/best k instruments earns.
  C  the cost-reduction frontier: how far must the toll fall before N instruments pay?
  D  OUT-OF-SAMPLE selection: choose on January, read on February+March.
  E  edge magnitude census: where is gross 2x / 3x the pooled average, in R and in bps.
  F  every cell that pays at n>=50 (no censoring).
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

POOLED_G = 0.038342
POOLED_GB = 0.23119


def stats(sub, label=""):
    if not sub:
        return None
    g = np.array([r["g"] for r in sub])
    c = np.array([r["c"] for r in sub])
    nt = g - c
    gb = np.array([r["g_bps"] for r in sub])
    cb = np.array([r["c_bps"] for r in sub])
    days = {}
    for r in sub:
        days.setdefault(r["day"], []).append(r["net"])
    dpos = sum(1 for v in days.values() if sum(v) / len(v) > 0)
    bym = {}
    for r in sub:
        bym.setdefault(r["month"], []).append(r["net"])
    sd = nt.std(ddof=1) if len(nt) > 1 else float("nan")
    # day-clustered
    dm = nt - nt.mean()
    agg = {}
    for x, r in zip(dm, sub):
        agg[r["day"]] = agg.get(r["day"], 0.0) + x
    G = len(agg)
    cse = (math.sqrt(sum(a * a for a in agg.values()) * G / (G - 1)) / len(nt)) if G > 1 else float("nan")
    return {"label": label, "n": len(sub),
            "gross_r": round(float(g.mean()), 6), "cost_r": round(float(c.mean()), 6),
            "net_r": round(float(nt.mean()), 6),
            "t_net": round(float(nt.mean() / (sd / math.sqrt(len(nt)))), 3) if sd > 0 else None,
            "t_net_clu": round(float(nt.mean() / cse), 3) if cse == cse and cse > 0 else None,
            "gross_bps": round(float(gb.mean()), 5), "cost_bps": round(float(cb.mean()), 5),
            "margin_bps": round(float(gb.mean() - cb.mean()), 5),
            "edge_cost_r": round(float(g.mean() / c.mean()), 4) if c.mean() > 0 else None,
            "days": len(days), "days_pos_net": dpos,
            "day_pos_frac": round(dpos / len(days), 4),
            "rdp_bps": round(float(np.mean([r["rdp"] for r in sub])) * 1e4, 3),
            "months": {m: round(float(np.mean(v)), 6) for m, v in sorted(bym.items())},
            "n_months": {m: len(v) for m, v in sorted(bym.items())}}


def main():
    rows = h2_scan.build()
    out = {}

    # ---------------------------------------------------------------- A  GER40 anatomy
    g40 = [r for r in rows if r["symbol"] == "GER40"]
    A = {"ALL": stats(g40, "GER40 all")}
    for ax, fn in (("session", lambda r: r["session"]), ("hour", lambda r: "h%02d" % r["hour"]),
                   ("hblock", lambda r: r["hblock"]), ("family", lambda r: r["family"]),
                   ("side", lambda r: r["side"]), ("dow", lambda r: r["dow"]),
                   ("vol", lambda r: r["vol"]), ("month", lambda r: r["month"])):
        A[ax] = {k: stats(v, k) for k, v in sorted(H.group(g40, fn).items())}
    out["A_ger40_anatomy"] = A

    # ---------------------------------------------------------------- B  affordable book
    sy = {}
    for r in rows:
        sy.setdefault(r["symbol"], []).append(r)
    tab = {s: stats(v, s) for s, v in sy.items()}
    by_cost = sorted(tab, key=lambda s: tab[s]["cost_bps"])
    by_net = sorted(tab, key=lambda s: -tab[s]["net_r"])
    by_margin = sorted(tab, key=lambda s: -tab[s]["margin_bps"])
    B = {"symbol_table": tab, "ladders": {}}
    for name, order in (("cheapest_cost_bps", by_cost), ("best_net_r", by_net),
                        ("best_margin_bps", by_margin)):
        lad = []
        for k in range(1, 25):
            keep = set(order[:k])
            sub = [r for r in rows if r["symbol"] in keep]
            s = stats(sub, "top%d_%s" % (k, name))
            s["symbols"] = order[:k]
            lad.append(s)
        B["ladders"][name] = lad
    out["B_affordable_book"] = B

    # ---------------------------------------------------------------- C  cost-reduction frontier
    C = []
    for f in [1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.25, 0.2, 0.15, 0.1]:
        pay = [s for s in tab if tab[s]["gross_bps"] > f * tab[s]["cost_bps"]]
        payr = [s for s in tab if tab[s]["gross_r"] > f * tab[s]["cost_r"]]
        sub = [r for r in rows if r["symbol"] in set(payr)]
        allbook = np.array([r["g"] - f * r["c"] for r in rows])
        C.append({"cost_factor": f,
                  "symbols_paying_bps": len(pay), "symbols_paying_r": len(payr),
                  "which_r": sorted(payr),
                  "book_net_r_all24": round(float(allbook.mean()), 6),
                  "selected_book_n": len(sub),
                  "selected_book_net_r": round(float(np.mean([r["g"] - f * r["c"] for r in sub])), 6)
                  if sub else None})
    out["C_cost_reduction_frontier"] = C

    # ---------------------------------------------------------------- D  OOS selection
    jan = [r for r in rows if r["month"] == "2026-01"]
    oos = [r for r in rows if r["month"] in ("2026-02", "2026-03")]
    D_ = {}
    # D1 instrument selection
    jt = {s: stats(v, s) for s, v in H.group(jan, lambda r: r["symbol"]).items()}
    lad = []
    for k in range(1, 25):
        pick = sorted(jt, key=lambda s: -jt[s]["net_r"])[:k]
        sub = [r for r in oos if r["symbol"] in set(pick)]
        s = stats(sub, "jan_top%d" % k)
        s["picked"] = pick
        lad.append(s)
    D_["instrument_selection_jan_to_febmar"] = lad
    # D1b: instruments that were net-positive in Jan
    pos = [s for s in jt if jt[s]["net_r"] > 0]
    D_["jan_net_positive_symbols"] = {"symbols": sorted(pos), "count": len(pos),
                                      "oos": stats([r for r in oos if r["symbol"] in set(pos)],
                                                   "jan-positive symbols on Feb+Mar")}
    # D2 cell selection: every cell definition, winners chosen on Jan, read on Feb+Mar
    defs = h2_scan.AXES + h2_scan.PAIRS + h2_scan.TRIPLES
    picked, oosrows = [], []
    seen = set()
    for name, fn in defs:
        gj = H.group(jan, fn)
        for k, v in gj.items():
            if len(v) < 40:
                continue
            gg = np.array([r["g"] for r in v])
            cc = np.array([r["c"] for r in v])
            if (gg - cc).mean() > 0:
                picked.append((name, k, len(v), round(float((gg - cc).mean()), 6)))
    D_["cells_selected_on_jan"] = len(picked)
    # honest read: for each selected cell, its Feb+Mar net
    reads = []
    for name, fn in defs:
        go = H.group(oos, fn)
        sel = {k for (nm, k, _n, _v) in picked if nm == name}
        for k in sel:
            v = go.get(k)
            if not v or len(v) < 20:
                continue
            gg = np.array([r["g"] for r in v])
            cc = np.array([r["c"] for r in v])
            reads.append({"axis": name, "cell": k, "n_oos": len(v),
                          "net_oos": round(float((gg - cc).mean()), 6)})
    D_["cell_reads_on_febmar"] = {
        "cells_read": len(reads),
        "cells_still_positive": sum(1 for x in reads if x["net_oos"] > 0),
        "hit_rate": round(sum(1 for x in reads if x["net_oos"] > 0) / len(reads), 4) if reads else None,
        "mean_oos_net": round(float(np.mean([x["net_oos"] for x in reads])), 6) if reads else None,
        "detail": sorted(reads, key=lambda x: -x["net_oos"]),
    }
    # baseline: hit rate of ALL cells (not just Jan-selected)
    allc, allpos = 0, 0
    vals = []
    for name, fn in defs:
        go = H.group(oos, fn)
        for k, v in go.items():
            if len(v) < 20:
                continue
            gg = np.array([r["g"] for r in v])
            cc = np.array([r["c"] for r in v])
            allc += 1
            vals.append(float((gg - cc).mean()))
            if (gg - cc).mean() > 0:
                allpos += 1
    D_["baseline_all_cells_febmar"] = {"cells": allc, "positive": allpos,
                                       "hit_rate": round(allpos / allc, 4) if allc else None,
                                       "mean_net": round(float(np.mean(vals)), 6)}
    out["D_out_of_sample"] = D_

    # ---------------------------------------------------------------- E  edge magnitude census
    E = {"pooled_gross_r": POOLED_G, "pooled_gross_bps": POOLED_GB, "axes": {}}
    for name, fn in defs:
        g_ = H.group(rows, fn)
        cells = []
        for k, v in g_.items():
            if len(v) < 100:
                continue
            s = stats(v, k)
            s["x_pooled_r"] = round(s["gross_r"] / POOLED_G, 3)
            s["x_pooled_bps"] = round(s["gross_bps"] / POOLED_GB, 3)
            cells.append(s)
        E["axes"][name] = cells
    allcells = [c for v in E["axes"].values() for c in v]
    E["summary"] = {
        "cells_ge100": len(allcells),
        "ge_2x_pooled_r": sum(1 for c in allcells if c["x_pooled_r"] >= 2),
        "ge_3x_pooled_r": sum(1 for c in allcells if c["x_pooled_r"] >= 3),
        "ge_2x_pooled_bps": sum(1 for c in allcells if c["x_pooled_bps"] >= 2),
        "ge_3x_pooled_bps": sum(1 for c in allcells if c["x_pooled_bps"] >= 3),
        "ge_2x_r_and_net_positive": sum(1 for c in allcells if c["x_pooled_r"] >= 2 and c["net_r"] > 0),
        "ge_2x_bps_and_net_positive": sum(1 for c in allcells if c["x_pooled_bps"] >= 2 and c["net_r"] > 0),
    }
    out["E_edge_magnitude"] = E

    # ---------------------------------------------------------------- F  everything that pays, n>=50
    F = []
    for name, fn in defs:
        g_ = H.group(rows, fn)
        for k, v in g_.items():
            if len(v) < 50:
                continue
            s = stats(v, k)
            if s["net_r"] > 0:
                s["axis"] = name
                s["cell"] = k
                F.append(s)
    F.sort(key=lambda x: -x["net_r"])
    out["F_all_paying_cells_n50"] = F
    out["F_count"] = len(F)
    tot = 0
    for name, fn in defs:
        g_ = H.group(rows, fn)
        tot += sum(1 for v in g_.values() if len(v) >= 50)
    out["F_cells_scanned_n50"] = tot

    with open(os.path.join(D, "H2_DEEP_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    # ------------------------------------------------------------------- print
    a = out["A_ger40_anatomy"]
    print("A. GER40 (n=%d) net=%+.5f tclu=%+.2f d+%d/%d  months %s"
          % (a["ALL"]["n"], a["ALL"]["net_r"], a["ALL"]["t_net_clu"], a["ALL"]["days_pos_net"],
             a["ALL"]["days"], a["ALL"]["months"]))
    for ax in ("session", "hblock", "family", "side", "vol"):
        print("  %s:" % ax)
        for k, s in sorted(a[ax].items(), key=lambda kv: -(kv[1]["net_r"])):
            print("    %-34s n=%-5d g=%+.5f c=%.5f net=%+.5f tclu=%+5.2f gbps=%+7.3f d+%d/%d"
                  % (k[:34], s["n"], s["gross_r"], s["cost_r"], s["net_r"], s["t_net_clu"] or 0,
                     s["gross_bps"], s["days_pos_net"], s["days"]))
    print("\nB. affordable-book ladder (order = best net_r in-sample):")
    for s in out["B_affordable_book"]["ladders"]["best_net_r"][:8]:
        print("   %-10s n=%-6d net=%+.6f tclu=%+5.2f  cbps=%.3f gbps=%.3f  d+%d/%d  %s"
              % (s["label"], s["n"], s["net_r"], s["t_net_clu"] or 0, s["cost_bps"],
                 s["gross_bps"], s["days_pos_net"], s["days"], ",".join(s["symbols"][:6])))
    print("\nC. cost-reduction frontier:")
    for c in out["C_cost_reduction_frontier"]:
        print("   x%.2f cost -> %2d/24 symbols pay (bps frame %2d) | whole-book net %+.6f | selected book n=%-6d net %+.6f"
              % (c["cost_factor"], c["symbols_paying_r"], c["symbols_paying_bps"],
                 c["book_net_r_all24"], c["selected_book_n"], c["selected_book_net_r"] or 0))
    d = out["D_out_of_sample"]
    print("\nD. OUT OF SAMPLE (select on January, read on February+March):")
    print("   Jan net-positive symbols: %s" % ", ".join(d["jan_net_positive_symbols"]["symbols"]))
    o = d["jan_net_positive_symbols"]["oos"]
    print("     -> Feb+Mar n=%d net=%+.6f tclu=%+.2f d+%d/%d months %s"
          % (o["n"], o["net_r"], o["t_net_clu"] or 0, o["days_pos_net"], o["days"], o["months"]))
    for s in d["instrument_selection_jan_to_febmar"][:6]:
        print("   jan-top%-2d -> Feb+Mar n=%-6d net=%+.6f tclu=%+5.2f  picked %s"
              % (len(s["picked"]), s["n"], s["net_r"], s["t_net_clu"] or 0, ",".join(s["picked"])))
    cr = d["cell_reads_on_febmar"]
    print("   CELLS: %d selected on Jan, %d read on Feb+Mar, %d still positive (hit %.3f), mean OOS net %+.6f"
          % (d["cells_selected_on_jan"], cr["cells_read"], cr["cells_still_positive"],
             cr["hit_rate"], cr["mean_oos_net"]))
    b = d["baseline_all_cells_febmar"]
    print("   BASELINE (all Feb+Mar cells, no selection): %d cells, %d positive (hit %.3f), mean net %+.6f"
          % (b["cells"], b["positive"], b["hit_rate"], b["mean_net"]))
    e = out["E_edge_magnitude"]["summary"]
    print("\nE. edge magnitude: of %d cells n>=100 -- >=2x pooled R %d, >=3x %d | >=2x pooled bps %d, >=3x %d"
          % (e["cells_ge100"], e["ge_2x_pooled_r"], e["ge_3x_pooled_r"],
             e["ge_2x_pooled_bps"], e["ge_3x_pooled_bps"]))
    print("   of those, net-positive: %d (R frame) / %d (bps frame)"
          % (e["ge_2x_r_and_net_positive"], e["ge_2x_bps_and_net_positive"]))
    print("\nF. cells that pay at n>=50: %d of %d scanned" % (out["F_count"], out["F_cells_scanned_n50"]))


if __name__ == "__main__":
    main()
