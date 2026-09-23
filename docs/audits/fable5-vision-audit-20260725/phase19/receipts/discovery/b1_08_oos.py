"""b1 step 8 — READ APRIL AND MAY ONCE, at the frozen specification.

April and May 2026 were built by h5 (h5_09_aprmay.py) with the UNMODIFIED
e_build_atmkt.py and were never used to choose any limb of b1-BOOK-V1: the gate came
from h6, the delay from h6, the exit from h6, and my own grid ran on Jan+Feb+Mar only.
h5 did read them for its own leads, which is stated as the one contamination risk.

h1's four-term cost exists for the three hunt months only, so the OOS read is at the
three-term HOUR-TRUE basis. To keep it apples-to-apples the hunt window is re-scored at
that same basis here, and the gate is recomputed on it as well, so the OOS book is
defined by exactly the same arithmetic as the in-window book.
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
M2 = ("2026-04", "2026-05")
K, EXIT, GATE = 3, "STOPONLY", 0.60


def main():
    t0 = time.time()
    M, G, _ = N.load()
    cost = M["cost_hour"]
    cbps = cost * M["bpsfac"]
    g = G[(K, EXIT)]
    gate = cbps <= GATE + 1e-12
    inw = np.isin(M["month"], M3)
    oos = np.isin(M["month"], M2)
    out = {"spec": {"gate_bps": GATE, "gate_cost_model": "hour-true three-term "
                    "(the only basis that exists on Apr/May)", "k": K, "exit": EXIT}}

    out["hunt_window_at_hour_true_cost"] = N.slim(N.score(g, cost, M, inw & gate,
                                                          want_equity=False))
    s = N.score(g, cost, M, oos & gate, want_equity=True)
    out["OOS_equity"] = {"days": s.pop("equity_days"), "cum_net_R": s.pop("equity_net_R"),
                         "day_mean_net_R": s.pop("day_net_R")}
    out["OOS_april_may"] = N.slim(s)
    out["all_five_months"] = N.slim(N.score(g, cost, M, gate))

    for m in M3 + M2:
        out["month_" + m] = N.slim(N.score(g, cost, M, gate & (M["month"] == m)))
    out["OOS_per_symbol"] = {str(u): N.slim(N.score(g, cost, M, oos & gate & (M["symbol"] == u)))
                             for u in np.unique(M["symbol"][oos & gate])}

    # the ungated five-month book, for scale
    out["ungated_five_month_book"] = N.slim(N.score(g, cost, M, np.ones(len(cost), bool)))
    out["ungated_OOS"] = N.slim(N.score(g, cost, M, oos))

    # gate sensitivity, read once, on the OOS window only
    out["OOS_gate_curve"] = []
    for gt in (0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 1.00):
        r = N.score(g, cost, M, oos & (cbps <= gt + 1e-12))
        if r["n"]:
            r["gate_bps"] = gt
            out["OOS_gate_curve"].append(N.slim(r))
    # k sensitivity, OOS
    out["OOS_k_curve"] = []
    for k in N.KS:
        for cx in ("STOPONLY", "TRAIL025", "INC"):
            r = N.score(G[(k, cx)], cost, M, oos & gate)
            if r["n"]:
                r.update({"k": k, "exit": cx})
                out["OOS_k_curve"].append(N.slim(r))

    # day-block bootstrap on the OOS book
    sel = oos & gate & np.isfinite(g)
    net = g[sel] - cost[sel]
    rng = np.random.default_rng(20260806)
    ud, inv = np.unique(M["day"][sel], return_inverse=True)
    Gn = len(ud)
    ssum = np.bincount(inv, weights=net, minlength=Gn)
    scnt = np.bincount(inv, minlength=Gn).astype(float)
    idx = rng.integers(0, Gn, size=(4000, Gn))
    mm = np.sort(ssum[idx].sum(axis=1) / scnt[idx].sum(axis=1))
    out["OOS_bootstrap"] = {"p025": float(mm[100]), "p50": float(mm[2000]),
                            "p975": float(mm[3899]), "p_le_0": float((mm <= 0).mean())}

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_OOS_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("SPEC FROZEN ON JAN-MAR, READ ONCE ON APRIL+MAY  (hour-true 3-term cost)")
    for lab in ("hunt_window_at_hour_true_cost", "OOS_april_may", "all_five_months",
                "ungated_five_month_book"):
        s = out[lab]
        print(f"  {lab:34} n={s['n']:>6} gross={s['gross_R']:>+9.5f} "
              f"cost={s['cost_R']:>8.5f} net={s['net_R']:>+9.5f} "
              f"ratio={(s['ratio_R'] or 0):>7.3f} tday={(s['t_net_day'] or 0):>+6.2f} "
              f"dpos={s['n_days_net_pos']}/{s['n_days']}")
    print("  months:", "  ".join(
        f"{m[-2:]}:{out['month_'+m]['net_R']:+.5f}(n{out['month_'+m]['n']})" for m in M3 + M2))
    print("  OOS bootstrap:", {k: round(v, 5) for k, v in out["OOS_bootstrap"].items()})
    print("  OOS per symbol:", {k: (v["n"], round(v["net_R"], 5), round(v["ratio_R"] or 0, 3))
                                for k, v in out["OOS_per_symbol"].items()})
    print("  OOS gate curve:", [(s["gate_bps"], s["n"], round(s["net_R"], 5))
                                for s in out["OOS_gate_curve"]])
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
