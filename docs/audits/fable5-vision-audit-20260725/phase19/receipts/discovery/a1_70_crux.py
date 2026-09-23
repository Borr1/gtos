#!/usr/bin/env python3
"""a1 step 70 - the crux, and the two corrections it forces.

 X1 EXECUTABILITY OF THE CONFIRM GATE.  c0 is the close of the minute [D, D+1min);
    it is knowable at D+60s.  A book that ACTS on it cannot fill at the D price -
    that price is 60 s stale by the time the gate can be read.  Price the gate at
    both fills and report the marginal value of the gate at each, paired.

 X2 THE ENTRY-CONVENTION DELTA on b1's own book rows: b1's k=3 is the 3rd available
    M1 bar; a live book waking on a 60 s clock gets D+3 MINUTES.  How much of b1's
    headline is the convention?

 X3 THE FRONTIER: every honest, executable arm ranked by its worst window.
"""
from __future__ import annotations
import json
import os
import sys

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import a1_lib as A  # noqa: E402
from a1_30_book import Arms, MONTHS, IS, OOS, OOS2  # noqa: E402
from a1_20_validate import h5_barcount_walk  # noqa: E402


def main():
    arms = {mm: Arms(mm) for mm in MONTHS}
    R = {}

    # -------------------------------------------------------------- X1 executability
    x1 = {}
    for mm in MONTHS:
        a = arms[mm]
        M = a.M
        rec = {}
        for th in (-0.15, -0.05, 0.0):
            g = M.c0 > th
            for k in (0, 1, 2, 5):
                for cn in ("STOPONLY", "INC"):
                    r, _ = a.gross(k, cn)
                    ug = A.summarize(r, M.cost, M.day, M.rdp, label="ungated")
                    gg = A.summarize(r[g], M.cost[g], M.day[g], M.rdp[g], label="gated")
                    rec["th%.2f|k%d_%s" % (th, k, cn)] = {
                        "ungated_n": ug["n"], "ungated_gross": ug["gross_R"],
                        "ungated_net": ug["net_R"],
                        "gated_n": gg["n"], "gated_gross": gg["gross_R"],
                        "gated_net": gg["net_R"],
                        "gate_marginal_gross": gg["gross_R"] - ug["gross_R"],
                        "gate_marginal_net": gg["net_R"] - ug["net_R"],
                        "refused_gross": float(r[~g].mean()),
                        "refused_net": float((r - M.cost)[~g].mean()),
                        "refused_cost": float(M.cost[~g].mean()),
                        "kept_cost": float(M.cost[g].mean()),
                        "executable": k >= 1,
                    }
        x1[mm] = rec
        print("X1 %s done" % mm, flush=True)
    R["X1_confirm_gate_executability"] = x1

    # pooled headline for the crux
    def pooled_cell(mms, th, k, cn, gated):
        g_, c_, d_, q_ = [], [], [], []
        for mm in mms:
            a = arms[mm]
            M = a.M
            r, _ = a.gross(k, cn)
            m = (M.c0 > th) if gated else np.ones(M.n, bool)
            g_.append(r[m]); c_.append(M.cost[m]); d_.append(M.day[m]); q_.append(M.rdp[m])
        return A.summarize(np.concatenate(g_), np.concatenate(c_),
                           np.concatenate(d_), np.concatenate(q_), B=3000)

    crux = {}
    for w, mms in (("IS_jan", IS), ("OOS_febmar", OOS), ("OOS2_aprmay", OOS2),
                   ("all5", MONTHS)):
        crux[w] = {
            "A_k0_ungated_SHIPPED": pooled_cell(mms, None, 0, "INC", False),
            "B_k0_gated_NOT_EXECUTABLE": pooled_cell(mms, -0.15, 0, "INC", True),
            "B2_k0_gated_c0gt0_NOT_EXECUTABLE": pooled_cell(mms, 0.0, 0, "INC", True),
            "C_k1_ungated_EXECUTABLE": pooled_cell(mms, None, 1, "INC", False),
            "D_k1_gated_EXECUTABLE": pooled_cell(mms, -0.15, 1, "INC", True),
            "E_k5_ungated_EXECUTABLE": pooled_cell(mms, None, 5, "STOPONLY", False),
            "F_k5_gated_EXECUTABLE": pooled_cell(mms, -0.15, 5, "STOPONLY", True),
            "G_k0_ungated_STOPONLY": pooled_cell(mms, None, 0, "STOPONLY", False),
        }
    R["crux_pooled"] = crux

    # -------------------------------------------------------------- X2 convention
    x2 = {}
    for mm in MONTHS[:3]:
        a = arms[mm]
        M = a.M
        tb = M.cost * M.rdp * 1e4
        m = tb <= 0.60
        for k in (3, 5):
            rs, _ = a.gross(k, "STOPONLY")            # wall clock D+k minutes
            rb, ok = h5_barcount_walk(M, k, target=None)[0], h5_barcount_walk(M, k, target=None)[2]
            mm_ = m & ok
            x2["%s_k%d" % (mm, k)] = {
                "n": int(mm_.sum()),
                "wallclock_gross": float(rs[mm_].mean()),
                "barcount_gross": float(rb[mm_].mean()),
                "wallclock_net": float((rs - M.cost)[mm_].mean()),
                "barcount_net": float((rb - M.cost)[mm_].mean()),
                "delta_net": float((rs - rb)[mm_].mean()),
                "share_identical": float((np.abs(rs[mm_] - rb[mm_]) < 1e-9).mean()),
            }
        print("X2 %s done" % mm, flush=True)
    # pooled over the b1 hunt window
    for k in (3, 5):
        g_w, g_b, c_, d_ = [], [], [], []
        for mm in MONTHS[:3]:
            a = arms[mm]
            M = a.M
            tb = M.cost * M.rdp * 1e4
            rs, _ = a.gross(k, "STOPONLY")
            rb, _, ok = h5_barcount_walk(M, k, target=None)
            m = (tb <= 0.60) & ok
            g_w.append(rs[m]); g_b.append(rb[m]); c_.append(M.cost[m]); d_.append(M.day[m])
        gw = np.concatenate(g_w); gb = np.concatenate(g_b)
        cc = np.concatenate(c_); dd = np.concatenate(d_)
        x2["b1_hunt3m_k%d" % k] = {
            "n": int(len(gw)),
            "wallclock_net": float((gw - cc).mean()),
            "barcount_net": float((gb - cc).mean()),
            "delta_net": float((gw - gb).mean()),
            "delta_ci": A.dayboot(gw - gb, dd)[1:3],
            "share_identical": float((np.abs(gw - gb) < 1e-9).mean()),
        }
    R["X2_entry_convention_on_b1_book"] = x2

    with open(os.path.join(D, "A1_CRUX_V1.json"), "w") as f:
        json.dump(R, f, indent=1)

    print("\n=== THE CRUX: the confirm gate at an executable fill ===")
    for w in ("IS_jan", "OOS_febmar", "OOS2_aprmay", "all5"):
        print("--- %s" % w)
        for k, v in crux[w].items():
            print("  %-36s n=%6d gross %+.5f net %+.5f  t_day %+.2f"
                  % (k, v["n"], v["gross_R"], v["net_R"], v["t_day"]))
    print("\n=== X2 entry convention on b1's book ===")
    for k, v in x2.items():
        if k.startswith("b1_"):
            print(k, json.dumps(v))


if __name__ == "__main__":
    main()
