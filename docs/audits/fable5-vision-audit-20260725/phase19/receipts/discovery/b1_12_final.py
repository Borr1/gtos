"""b1 step 12 — the consolidated final numbers, one gate definition throughout.

Everything the receipt quotes is produced here, with the gate defined ONCE on the h1
four-term broker-true cost (the strictest basis in the wave, and the one a live book
would actually pay). Adds:
  * the JANUARY-ONLY gate resolution (does a January-only observer get the same three
    instruments? if yes the instrument set is not hindsight)
  * the equal-weight k in {1,2,3} blend, which is the honest way to ship a plateau
  * the full multiplicity bill for the whole wave
  * the per-day equity series for the artefact
"""
import gzip
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")
M3, M2 = MONTHS[:3], MONTHS[3:]
K, EXIT, GATE = 3, "STOPONLY", 0.60
IDX3 = ("US30_cash", "GER40", "NAS100")


def main():
    t0 = time.time()
    M, G, _ = N.load()
    h1c, hrc = M["cost_h1"], M["cost_hour"]
    gate_h1 = (h1c * M["bpsfac"]) <= GATE + 1e-12          # 3 hunt months only
    gate_hr = (hrc * M["bpsfac"]) <= GATE + 1e-12          # all five months
    in3 = np.isin(M["month"], M3)
    in2 = np.isin(M["month"], M2)
    g = G[(K, EXIT)]
    out = {}

    # ---------------------------------------------------------- gate resolution
    res = {}
    for lab, sel in (("january_only", M["month"] == "2026-01"),
                     ("february_only", M["month"] == "2026-02"),
                     ("march_only", M["month"] == "2026-03"),
                     ("april_only", M["month"] == "2026-04"),
                     ("may_only", M["month"] == "2026-05"),
                     ("hunt_3m", in3), ("oos_2m", in2), ("all_5m", np.ones(len(g), bool))):
        m = sel & gate_hr
        syms = sorted(set(M["symbol"][m].tolist()))
        res[lab] = {"instruments": syms, "n": int(m.sum())}
    out["gate_resolution_by_window"] = res
    out["gate_resolves_to_same_3_every_month"] = all(
        set(res[x]["instruments"]) == set(IDX3)
        for x in ("january_only", "february_only", "march_only", "april_only", "may_only"))

    # ---------------------------------------------------------- headline, one basis
    sel = gate_h1 & in3
    s = N.score(g, h1c, M, sel, want_equity=True)
    out["EQUITY"] = {"days": s.pop("equity_days"), "cum_net_R": s.pop("equity_net_R"),
                     "day_mean_net_R": s.pop("day_net_R")}
    out["HEADLINE_hunt3m_h1cost"] = N.slim(s)

    # stress, same population, same gate definition
    stopped = np.abs(g + 1.0) < 1e-9
    exslip = np.where(stopped, 0.032236, 0.0)
    STR = {"base h1 four-term": h1c, "x1.25": h1c * 1.25, "x1.50": h1c * 1.50,
           "x1.75": h1c * 1.75, "x2.00": h1c * 2.00,
           "h4 all-in x1.577": h1c * 1.577,
           "+l10-F9 exit slip on stops": h1c + exslip,
           "+exit slip AND x1.5": h1c * 1.5 + exslip,
           "+exit slip AND x2.0": h1c * 2.0 + exslip,
           "January-era spread regime": M["cost_h1_era"],
           "+entry slip doubled": h1c + 0.1165 / M["bpsfac"]}
    out["STRESS_hunt3m"] = {k2: N.slim(N.score(g, c, M, sel)) for k2, c in STR.items()}

    # ---------------------------------------------------------- k plateau blend
    blend = {}
    for kk in (0, 1, 2, 3, 5):
        blend[f"k={kk}"] = N.slim(N.score(G[(kk, EXIT)], h1c, M, sel))
    gb = np.nanmean(np.vstack([G[(1, EXIT)], G[(2, EXIT)], G[(3, EXIT)]]), axis=0)
    blend["equal weight k in {1,2,3}"] = N.slim(N.score(gb, h1c, M, sel))
    blend["equal weight k in {1,2,3} OOS"] = N.slim(N.score(gb, hrc, M, gate_hr & in2))
    blend["equal weight k in {1,2,3} 5m"] = N.slim(N.score(gb, hrc, M, gate_hr))
    out["K_PLATEAU"] = blend

    # ---------------------------------------------------------- the three books
    books = {
        "BOOK-A  gate<=0.60bps + k=3 + STOPONLY": gate_hr,
        "BOOK-C  3 gate-reachable instruments, ALL hours, k=3 + STOPONLY": np.isin(M["symbol"], IDX3),
        "BASELINE swarm repaired contract, whole book": np.ones(len(g), bool),
    }
    out["BOOKS"] = {}
    for lab, m in books.items():
        gv = G[(5, "TRAIL025")] if "BASELINE" in lab else g
        d = {"hunt_3m": N.slim(N.score(gv, hrc, M, m & in3)),
             "oos_2m": N.slim(N.score(gv, hrc, M, m & in2)),
             "pooled_5m": N.slim(N.score(gv, hrc, M, m))}
        for mm in MONTHS:
            d[mm] = N.slim(N.score(gv, hrc, M, m & (M["month"] == mm)))
        # day-block bootstrap on the pooled five months
        q = m & np.isfinite(gv)
        net = gv[q] - hrc[q]
        rng = np.random.default_rng(20260806)
        ud, inv = np.unique(M["day"][q], return_inverse=True)
        Gn = len(ud)
        ss = np.bincount(inv, weights=net, minlength=Gn)
        sc = np.bincount(inv, minlength=Gn).astype(float)
        idx = rng.integers(0, Gn, size=(4000, Gn))
        mm2 = np.sort(ss[idx].sum(axis=1) / sc[idx].sum(axis=1))
        d["bootstrap_5m"] = {"p025": float(mm2[100]), "p50": float(mm2[2000]),
                             "p975": float(mm2[3899]), "p_le_0": float((mm2 <= 0).mean())}
        out["BOOKS"][lab] = d

    # BOOK-C equity for the artefact
    sC = N.score(g, hrc, M, np.isin(M["symbol"], IDX3), want_equity=True)
    out["EQUITY_BOOK_C"] = {"days": sC.pop("equity_days"), "cum_net_R": sC.pop("equity_net_R")}
    out["BOOK_C_pooled"] = N.slim(sC)

    # ---------------------------------------------------------- multiplicity bill
    ncells = 0
    try:
        for _ in gzip.open(f"{D}/b1_GRID_V1.jsonl.gz", "rt"):
            ncells += 1
    except OSError:
        pass
    out["MULTIPLICITY_BILL"] = {
        "b1_declared_grid": {"declared": 11 * 5 * 12 * 4, "non_empty": ncells,
                             "axes": "k(11) x exit(5) x gate(12) x window(4)"},
        "b1_surface_and_followups": {"gate_curve": 20, "marginal_bands": 11,
                                     "k_x_exit_at_4_gates": 11 * 6 * 4,
                                     "composition_cells": 7 * 24,
                                     "placebo_anchors": 9 + 20,
                                     "stress_variants": 11,
                                     "bookB_m_sweep": 8 + 8,
                                     "limb_decomposition": 5,
                                     "oos_curves": 10 + 33},
        "wave_lanes_as_published": {
            "h1": 3472, "h2": 2421 + 1792, "h3": "cells + composites (H3_CELLS_V1)",
            "h5": 4130 + 39835, "h6": 103200,
            "swarm_discovery_29_lanes": "not enumerated in one place; >10^4"},
        "note": ("b1's own contribution is 2,640 declared + ~700 follow-up cells. The "
                 "wave total is >150,000 cells. h5's Westfall-Young maxT over its own "
                 "4,130 cells already returned ZERO survivors at p<=0.20, and b1's "
                 "specification is drawn from the same pool, so no cell in this receipt "
                 "should be read as multiplicity-corrected significant."),
    }
    out["MULTIPLICITY_BILL"]["b1_total_own_cells"] = (
        out["MULTIPLICITY_BILL"]["b1_declared_grid"]["declared"]
        + sum(out["MULTIPLICITY_BILL"]["b1_surface_and_followups"].values()))

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_FINAL_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("GATE RESOLUTION per window:")
    for k2, v in res.items():
        print(f"  {k2:16} n={v['n']:>6}  {v['instruments']}")
    print("  same three every month:", out["gate_resolves_to_same_3_every_month"])
    print()
    h = out["HEADLINE_hunt3m_h1cost"]
    print(f"HEADLINE Jan+Feb+Mar, h1 four-term cost: n={h['n']} gross={h['gross_R']:+.6f} "
          f"cost={h['cost_R']:.6f} net={h['net_R']:+.6f} ratio={h['ratio_R']:.4f}")
    print()
    print("STRESS (same rows, same gate)")
    for k2, v in out["STRESS_hunt3m"].items():
        print(f"  {k2:30} cost={v['cost_R']:.5f} net={v['net_R']:>+9.5f} "
              f"ratio={(v['ratio_R'] or 0):>7.3f} tday={(v['t_net_day'] or 0):>+6.2f}")
    print()
    print("K PLATEAU")
    for k2, v in out["K_PLATEAU"].items():
        print(f"  {k2:32} n={v['n']:>6} net={v['net_R']:>+9.5f} ratio={(v['ratio_R'] or 0):>7.3f}")
    print()
    print("THE BOOKS  (hour-true cost, common basis across all five months)")
    for lab, d in out["BOOKS"].items():
        print(f"  {lab}")
        print("     " + "  ".join(f"{m[-2:]}:{d[m]['net_R']:+.5f}" for m in MONTHS))
        print(f"     hunt n={d['hunt_3m']['n']} net={d['hunt_3m']['net_R']:+.5f} "
              f"ratio={d['hunt_3m']['ratio_R']:.3f} | OOS n={d['oos_2m']['n']} "
              f"net={d['oos_2m']['net_R']:+.5f} ratio={d['oos_2m']['ratio_R']:.3f} | "
              f"5m n={d['pooled_5m']['n']} net={d['pooled_5m']['net_R']:+.5f} "
              f"ratio={d['pooled_5m']['ratio_R']:.3f} P(<=0)={d['bootstrap_5m']['p_le_0']:.3f}")
    print()
    print("MULTIPLICITY: b1 own cells =", out["MULTIPLICITY_BILL"]["b1_total_own_cells"])
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
