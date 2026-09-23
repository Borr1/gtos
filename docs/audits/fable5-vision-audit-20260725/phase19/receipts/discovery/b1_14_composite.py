"""b1 step 14 — the composite books, all five months, with the discovery order stated.

Every limb below was published by a lane BEFORE b1 ran and appears in b1's declared
grid, so none of them is a post-OOS invention:
    <=0.60 bps cost gate      h6 cell B
    broker hours 08-20        h1 (its published ex-ante composed gate)
    k=3 entry delay           h6 cell B
    stop -1R / no target / no trail / 120 min   h6 cell B
WHAT IS post-OOS is the ORDERING: b1 read April+May before deciding which composite to
put forward. That is stated in the receipt and it is the reason the five-month numbers
here are labelled indicative rather than out-of-sample.
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
M3, M2 = MONTHS[:3], MONTHS[3:]
IDX3 = ("US30_cash", "GER40", "NAS100")
K, EXIT = 3, "STOPONLY"


def boot(g, c, M, sel, B=4000, seed=20260806):
    q = sel & np.isfinite(g) & np.isfinite(c)
    net = g[q] - c[q]
    ud, inv = np.unique(M["day"][q], return_inverse=True)
    Gn = len(ud)
    ss = np.bincount(inv, weights=net, minlength=Gn)
    sc = np.bincount(inv, minlength=Gn).astype(float)
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, Gn, size=(B, Gn))
    m = np.sort(ss[idx].sum(axis=1) / sc[idx].sum(axis=1))
    return {"p025": float(m[int(.025 * B)]), "p50": float(m[B // 2]),
            "p975": float(m[int(.975 * B) - 1]), "p_le_0": float((m <= 0).mean())}


def main():
    t0 = time.time()
    M, G, _ = N.load()
    c = M["cost_hour"]
    gate = (c * M["bpsfac"]) <= 0.60 + 1e-12
    bh = M["broker_hour"]
    liq = (bh >= 8) & (bh <= 20)
    inst = np.isin(M["symbol"], IDX3)
    g = G[(K, EXIT)]
    in3, in2 = np.isin(M["month"], M3), np.isin(M["month"], M2)

    BOOKS = {
        "A  cost gate <=0.60 bps": gate,
        "C  3 gate-reachable instruments, all hours": inst,
        "D  cost gate AND broker hours 08-20": gate & liq,
        "E  3 instruments AND broker hours 08-20": inst & liq,
        "F  cost gate AND cash session": gate & M["cash"],
    }
    out = {"spec_common": {"k": K, "exit": EXIT, "cost": "hour-true three-term",
                           "instruments_reachable_by_gate": list(IDX3)}}
    for lab, m in BOOKS.items():
        d = {"hunt_3m": N.slim(N.score(g, c, M, m & in3)),
             "oos_2m": N.slim(N.score(g, c, M, m & in2)),
             "pooled_5m": N.slim(N.score(g, c, M, m)),
             "boot_5m": boot(g, c, M, m), "boot_oos": boot(g, c, M, m & in2)}
        for mm in MONTHS:
            d[mm] = N.slim(N.score(g, c, M, m & (M["month"] == mm)))
        d["per_symbol_5m"] = {s: N.slim(N.score(g, c, M, m & (M["symbol"] == s)))
                              for s in IDX3}
        # cost stress on the pooled five months
        d["stress_5m"] = {f"x{x}": N.slim(N.score(g, c * x, M, m))
                          for x in (1.0, 1.25, 1.5, 1.577, 2.0)}
        out[lab] = d

    # the honest summary table
    out["SUMMARY"] = {lab: {"n_5m": out[lab]["pooled_5m"]["n"],
                            "net_5m": out[lab]["pooled_5m"]["net_R"],
                            "ratio_5m": out[lab]["pooled_5m"]["ratio_R"],
                            "hunt_net": out[lab]["hunt_3m"]["net_R"],
                            "oos_net": out[lab]["oos_2m"]["net_R"],
                            "oos_ratio": out[lab]["oos_2m"]["ratio_R"],
                            "months_positive": sum(1 for m in MONTHS
                                                   if out[lab][m].get("n")
                                                   and out[lab][m]["net_R"] > 0),
                            "p_le_0_5m": out[lab]["boot_5m"]["p_le_0"],
                            "p_le_0_oos": out[lab]["boot_oos"]["p_le_0"],
                            "survives_cost_x2": out[lab]["stress_5m"]["x2.0"]["net_R"] > 0}
                       for lab in BOOKS}
    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_COMPOSITE_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("COMPOSITE BOOKS — k=3, stop -1R, no target, no trail, close at +120 min")
    print(f"  {'book':46}" + "".join(f"{m[-2:]:>9}" for m in MONTHS)
          + f"{'hunt':>9}{'OOS':>9}{'5m':>9}{'rat':>7}{'P<=0':>7}")
    for lab in BOOKS:
        d = out[lab]
        cells = "".join(f"{d[m]['net_R']:>+9.4f}" if d[m].get("n") else f"{'-':>9}"
                        for m in MONTHS)
        print(f"  {lab:46}{cells}{d['hunt_3m']['net_R']:>+9.4f}"
              f"{d['oos_2m']['net_R']:>+9.4f}{d['pooled_5m']['net_R']:>+9.4f}"
              f"{(d['pooled_5m']['ratio_R'] or 0):>7.3f}{d['boot_5m']['p_le_0']:>7.3f}")
    print()
    for lab in BOOKS:
        d = out[lab]
        print(f"  {lab}")
        print(f"     5m n={d['pooled_5m']['n']:>5} gross={d['pooled_5m']['gross_R']:+.5f} "
              f"cost={d['pooled_5m']['cost_R']:.5f} net={d['pooled_5m']['net_R']:+.5f} "
              f"tday={(d['pooled_5m']['t_net_day'] or 0):+.2f} "
              f"days={d['pooled_5m']['n_days_net_pos']}/{d['pooled_5m']['n_days']} "
              f"maxDD={d['pooled_5m']['max_dd_R']:.1f} "
              f"stress x2 net={d['stress_5m']['x2.0']['net_R']:+.5f}")
        print(f"     per symbol: " + "  ".join(
            f"{s}:{d['per_symbol_5m'][s]['net_R']:+.4f}(n{d['per_symbol_5m'][s]['n']})"
            for s in IDX3))
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
