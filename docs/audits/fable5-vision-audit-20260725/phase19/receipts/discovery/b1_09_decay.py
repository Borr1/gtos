"""b1 step 9 — WHAT collapsed out of sample? Three candidate mechanisms, separated.

The book's April+May gross is +0.00308 against +0.11498 in the hunt window while its
cost barely moves (0.04778 vs 0.04646). So it is an EDGE failure, not a cost failure.
Three things could produce it, and they have different consequences:

  M1  the CONTRACT stopped working everywhere  -> the ungated 24-instrument cohort's
      k=3/STOPONLY gross also collapses in Apr/May. Nothing to do with selection.
  M2  the SELECTION stopped working            -> the ungated cohort holds and only the
      gated cells collapse. The cheap cells were a January-February accident.
  M3  a monotone TIME DECAY across all five months, in both populations.

Also measured: month-by-month for every limb, so the decay can be attributed to the
gate, the delay or the exit; and the same five-month read for the two rival books the
wave produced (h2's cash-session GER40+NAS100, h3's cheapest-two-instrument book).
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")
IDX3 = ("US30_cash", "GER40", "NAS100")


def row(lab, s):
    return (f"  {lab:44} n={s['n']:>6} gross={s['gross_R']:>+9.5f} "
            f"cost={s['cost_R']:>8.5f} net={s['net_R']:>+9.5f} "
            f"ratio={(s['ratio_R'] if s['ratio_R'] is not None else 0):>7.3f}")


def main():
    t0 = time.time()
    M, G, _ = N.load()
    cost = M["cost_hour"]
    cbps = cost * M["bpsfac"]
    gate = cbps <= 0.60 + 1e-12
    ALL = np.ones(len(cost), dtype=bool)
    out = {}

    POPS = {
        "GATED_BOOK (b1-BOOK-V1)": gate,
        "UNGATED all 24 instruments": ALL,
        "3 index instruments, ALL hours": np.isin(M["symbol"], IDX3),
        "3 index instruments, cash session": np.isin(M["symbol"], IDX3) & M["cash"],
        "everything the gate REJECTS": ~gate,
        "h2 book: GER40+NAS100 in cash session": (np.isin(M["symbol"], ("GER40", "NAS100"))
                                                  & M["cash"]),
        "h3 book: US30_cash+GER40 (2 cheapest)": np.isin(M["symbol"], ("US30_cash", "GER40")),
    }
    CONS = {"b1 exit (k=3, STOPONLY)": (3, "STOPONLY"),
            "swarm (k=5, TRAIL025)": (5, "TRAIL025"),
            "shipped (k=0, INC 2R)": (0, "INC")}

    for pl, pm in POPS.items():
        for cl, (k, cx) in CONS.items():
            g = G[(k, cx)]
            key = f"{pl} | {cl}"
            d = {"pooled_5m": N.slim(N.score(g, cost, M, pm))}
            for m in MONTHS:
                d[m] = N.slim(N.score(g, cost, M, pm & (M["month"] == m)))
            d["hunt_3m"] = N.slim(N.score(g, cost, M, pm & np.isin(M["month"], MONTHS[:3])))
            d["oos_2m"] = N.slim(N.score(g, cost, M, pm & np.isin(M["month"], MONTHS[3:])))
            out[key] = d

    # ---- the decay test itself: OLS of monthly mean gross on month index, per population
    dec = {}
    for pl, pm in POPS.items():
        for cl, (k, cx) in CONS.items():
            key = f"{pl} | {cl}"
            y = [out[key][m]["gross_R"] for m in MONTHS if out[key][m]["n"]]
            yn = [out[key][m]["net_R"] for m in MONTHS if out[key][m]["n"]]
            x = np.arange(len(y), dtype=float)
            if len(y) < 3:
                continue
            bg = np.polyfit(x, y, 1)[0]
            bn = np.polyfit(x, yn, 1)[0]
            dec[key] = {"gross_slope_per_month": float(bg),
                        "net_slope_per_month": float(bn),
                        "gross_by_month": [round(v, 6) for v in y],
                        "net_by_month": [round(v, 6) for v in yn]}
    out["_DECAY_SLOPES"] = dec

    # ---- is the cost rank stable while the edge rank is not? (h5's control, re-run on
    #      this book's own three instruments and on all 24, at this contract)
    g = G[(3, "STOPONLY")]
    h3m = np.isin(M["month"], MONTHS[:3])
    o2m = np.isin(M["month"], MONTHS[3:])
    syms = sorted(set(M["symbol"].tolist()))
    ga, gb, ca, cb = [], [], [], []
    for s in syms:
        a = h3m & (M["symbol"] == s) & np.isfinite(g)
        b = o2m & (M["symbol"] == s) & np.isfinite(g)
        if a.sum() < 50 or b.sum() < 50:
            continue
        ga.append(float(g[a].mean())); gb.append(float(g[b].mean()))
        ca.append(float(cbps[a].mean())); cb.append(float(cbps[b].mean()))

    def spearman(u, v):
        u = np.asarray(u, float); v = np.asarray(v, float)
        ru = np.argsort(np.argsort(u)).astype(float)
        rv = np.argsort(np.argsort(v)).astype(float)
        return float(np.corrcoef(ru, rv)[0, 1])

    out["_RANK_PERSISTENCE"] = {
        "n_symbols": len(ga),
        "spearman_gross_hunt_vs_oos": spearman(ga, gb),
        "spearman_cost_hunt_vs_oos": spearman(ca, cb),
        "pearson_gross": float(np.corrcoef(ga, gb)[0, 1]),
        "pearson_cost": float(np.corrcoef(ca, cb)[0, 1]),
        "note": "at b1's own contract (k=3 STOPONLY), all 24 instruments, n>=50 per window",
    }

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_DECAY_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("MONTH CHAIN — mean NET R/trade, hour-true cost  [Jan Feb Mar | Apr May]")
    print(f"  {'population | contract':60} " + "".join(f"{m[-2:]:>9}" for m in MONTHS)
          + f"{'slope':>9}")
    for key in out:
        if key.startswith("_") or key == "elapsed_s":
            continue
        d = out[key]
        cells = "".join(f"{d[m]['net_R']:>+9.4f}" if d[m]["n"] else f"{'-':>9}" for m in MONTHS)
        sl = dec.get(key, {}).get("net_slope_per_month")
        print(f"  {key:60} {cells}{(sl if sl is not None else 0):>+9.4f}")
    print()
    print("MONTH CHAIN — mean GROSS R/trade (the same rows, cost removed)")
    for key in out:
        if key.startswith("_") or key == "elapsed_s" or "b1 exit" not in key:
            continue
        d = out[key]
        cells = "".join(f"{d[m]['gross_R']:>+9.4f}" if d[m]["n"] else f"{'-':>9}" for m in MONTHS)
        sl = dec.get(key, {}).get("gross_slope_per_month")
        print(f"  {key:60} {cells}{(sl if sl is not None else 0):>+9.4f}")
    print()
    print("RANK PERSISTENCE (hunt -> OOS, per instrument):",
          json.dumps({k: (round(v, 4) if isinstance(v, float) else v)
                      for k, v in out["_RANK_PERSISTENCE"].items() if k != "note"}))
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
