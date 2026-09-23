"""b1 step 4 — is the winner a plateau or a spike?

Three surfaces around the grid's argmax, all at h1's four-term broker-true cost on
Jan+Feb+Mar:
  A. the GATE curve at k=3 / STOPONLY / all hours (is there a cliff, and where)
  B. the (k x exit) surface at the chosen gate
  C. per-symbol and per-broker-hour composition of the admitted set

A specification that only pays at one grid point is a fit. A specification that pays
across a contiguous region is a mechanism. This step decides which one this is.
"""
import json
import os
import sys
import time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

M3 = ("2026-01", "2026-02", "2026-03")


def main():
    t0 = time.time()
    M, G, rows = N.load()
    base = np.isin(M["month"], M3) & np.isfinite(M["cost_h1"])
    cost = M["cost_h1"]
    cbps = cost * M["bpsfac"]
    out = {}

    # ---------------------------------------------------------------- A gate curve
    fine = [0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70,
            0.75, 0.80, 0.90, 1.00, 1.25, 1.50, 2.00, 3.00, 1e9]
    A = []
    for gt in fine:
        sel = base & (cbps <= gt + 1e-12)
        s = N.score(G[(3, "STOPONLY")], cost, M, sel)
        if s["n"]:
            s["gate_bps"] = None if gt > 1e8 else gt
            A.append(N.slim(s))
    out["A_gate_curve_k3_stoponly"] = A

    # marginal band economics: what does each successive slice of toll buy?
    bands = [(0.0, 0.30), (0.30, 0.40), (0.40, 0.50), (0.50, 0.55), (0.55, 0.60),
             (0.60, 0.70), (0.70, 0.80), (0.80, 1.00), (1.00, 1.50), (1.50, 3.00),
             (3.00, 1e9)]
    Bd = []
    for lo, hi in bands:
        sel = base & (cbps > lo) & (cbps <= hi)
        s = N.score(G[(3, "STOPONLY")], cost, M, sel)
        if s["n"]:
            s["band"] = [lo, (None if hi > 1e8 else hi)]
            Bd.append(N.slim(s))
    out["A2_marginal_bands_k3_stoponly"] = Bd

    # ---------------------------------------------------------------- B k x exit
    for gt in (0.50, 0.55, 0.60, 0.65):
        sel0 = base & (cbps <= gt + 1e-12)
        tab = []
        for k in N.KS:
            for cx in N.TRAIL_FREE + ("TRAIL025",):
                s = N.score(G[(k, cx)], cost, M, sel0)
                if s["n"]:
                    s.update({"k": k, "exit": cx})
                    tab.append(N.slim(s))
        out[f"B_k_x_exit_gate{gt}"] = tab

    # ---------------------------------------------------------------- C composition
    for gt in (0.55, 0.60):
        sel = base & (cbps <= gt + 1e-12)
        g = G[(3, "STOPONLY")]
        comp = {}
        for axis in ("symbol", "broker_hour", "family", "side", "month", "session", "dow"):
            v = M[axis]
            d = {}
            for u in np.unique(v[sel & np.isfinite(g)]):
                s = N.score(g, cost, M, sel & (v == u))
                if s["n"]:
                    d[str(u)] = N.slim(s)
            comp[axis] = d
        # what fraction of each symbol's own rows the gate admits
        adm = {}
        for u in np.unique(M["symbol"][base]):
            tot = int((base & (M["symbol"] == u)).sum())
            kept = int((sel & (M["symbol"] == u)).sum())
            adm[str(u)] = {"total": tot, "admitted": kept,
                           "share": round(kept / tot, 4) if tot else None,
                           "mean_cost_bps": float(np.nanmean(cbps[base & (M["symbol"] == u)]))}
        comp["admission_share_by_symbol"] = adm
        out[f"C_composition_gate{gt}"] = comp

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_SURFACE_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("GATE CURVE  k=3 STOPONLY, h1 broker-true cost, Jan+Feb+Mar")
    print(f"{'gate':>6} {'n':>6} {'share':>6} {'gross':>9} {'cost':>8} {'net':>9} "
          f"{'ratio':>6} {'tday':>6} {'mo+':>4}")
    tot = int(base.sum())
    for s in A:
        mp = sum(1 for i in (1, 2, 3)
                 if s.get(f"m_2026-0{i}") and s[f"m_2026-0{i}"]["net_R"] > 0)
        print(f"{str(s['gate_bps']):>6} {s['n']:>6} {s['n']/tot:>6.3f} "
              f"{s['gross_R']:>+9.5f} {s['cost_R']:>8.5f} {s['net_R']:>+9.5f} "
              f"{s['ratio_R']:>6.3f} {s['t_net_day'] or 0:>6.2f} {mp:>4}")
    print()
    print("MARGINAL COST BANDS (k=3 STOPONLY)")
    for s in Bd:
        print(f"  {str(s['band']):>16} n={s['n']:>6} gross={s['gross_R']:>+8.5f} "
              f"cost={s['cost_R']:>7.5f} net={s['net_R']:>+8.5f} ratio={s['ratio_R']:>6.3f}")
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
