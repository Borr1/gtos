"""b1 step 3 — THE DECLARED GRID.

Four axes, every combination scored on Jan+Feb+Mar at h1's four-term broker-true cost.
The grid is written down here in full so the multiplicity bill is exact and countable:

    k         11  (0,1,2,3,5,10,15,20,30,45,60)          entry delay, minutes
    exit       5  (STOPONLY,INC,T3S1,TS90S1,TS60S1)      TRAIL-FREE contracts only
    gate      12  (0.35..1.50 bps, plus no gate)         ex-ante broker-true toll cap
    window     4  (all, bh08-20, bh07-21, cash-session)  ex-ante time restriction
    ------------------------------------------------------------------
    2,640 cells.  Every one is emitted to b1_GRID_V1.jsonl.gz.

Nothing here consults April or May.  The gate is computed on the row's OWN cost, which
is knowable at the decision instant (per-symbol-per-broker-hour tick spread median +
broker commission schedule + measured per-symbol slippage + risk distance).
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

GATES = (0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 1.00, 1.50, 1e9)
WINDOWS = ("all", "bh08_20", "bh07_21", "cash")


def main():
    t0 = time.time()
    M, G, rows = N.load()
    m3 = np.isin(M["month"], list(N.KS and ("2026-01", "2026-02", "2026-03")))
    base = m3 & np.isfinite(M["cost_h1"])
    cost = M["cost_h1"]
    cbps = cost * M["bpsfac"]
    bh = M["broker_hour"]
    wins = {"all": np.ones(len(cost), dtype=bool),
            "bh08_20": (bh >= 8) & (bh <= 20),
            "bh07_21": (bh >= 7) & (bh <= 21),
            "cash": M["cash"]}

    out = []
    for k in N.KS:
        for cx in N.TRAIL_FREE:
            g = G[(k, cx)]
            for gt in GATES:
                gm = base & (cbps <= gt + 1e-12)
                for wn in WINDOWS:
                    sel = gm & wins[wn]
                    s = N.score(g, cost, M, sel)
                    if s["n"] == 0:
                        continue
                    s.update({"k": k, "exit": cx, "gate_bps": (None if gt > 1e8 else gt),
                              "window": wn})
                    out.append(s)
    with gzip.open(f"{D}/b1_GRID_V1.jsonl.gz", "wt") as f:
        for s in out:
            f.write(json.dumps(N.slim(s)) + "\n")

    # ---- the pre-declared selection rule, stated before the grid was read:
    #   ratio_R > 1 AND net_R > 0 AND all three months net-positive AND n >= 1000
    #   AND day-clustered t on net R >= 1.5 ; rank the survivors by (ratio-1)*n.
    def ok(s):
        ms = [s.get("m_2026-01"), s.get("m_2026-02"), s.get("m_2026-03")]
        return (s["n"] >= 1000 and s["net_R"] and s["net_R"] > 0
                and s["ratio_R"] and s["ratio_R"] > 1
                and all(x and x["net_R"] > 0 for x in ms)
                and s["t_net_day"] is not None and s["t_net_day"] >= 1.5)

    surv = [s for s in out if ok(s)]
    surv.sort(key=lambda s: -(s["ratio_R"] - 1) * s["n"])
    rec = {"grid": {"k": list(N.KS), "exit": list(N.TRAIL_FREE),
                    "gates": [None if g > 1e8 else g for g in GATES],
                    "windows": list(WINDOWS),
                    "cells_declared": len(N.KS) * len(N.TRAIL_FREE) * len(GATES) * len(WINDOWS),
                    "cells_nonempty": len(out)},
           "cost_basis": "h1 four-term broker-true (hour spread + broker comm + live slip + swap)",
           "selection_rule": ("ratio_R>1 & net_R>0 & 3/3 months net-positive & n>=1000 "
                              "& t_net_day>=1.5 ; rank by (ratio-1)*n"),
           "n_pass_rule": len(surv),
           "n_ratio_gt1": sum(1 for s in out if s["ratio_R"] and s["ratio_R"] > 1),
           "n_ratio_gt1_n500": sum(1 for s in out
                                   if s["ratio_R"] and s["ratio_R"] > 1 and s["n"] >= 500),
           "top40_by_rule": [N.slim(s) for s in surv[:40]],
           "top40_by_ratio_n500": [N.slim(s) for s in
                                   sorted([x for x in out if x["n"] >= 500],
                                          key=lambda s: -(s["ratio_R"] or 0))[:40]],
           "elapsed_s": round(time.time() - t0, 1)}
    with open(f"{D}/B1_GRID_V1.json", "w") as f:
        json.dump(rec, f, indent=1)

    print(f"cells {rec['grid']['cells_declared']} declared / {len(out)} non-empty; "
          f"ratio>1 {rec['n_ratio_gt1']} ({rec['n_ratio_gt1_n500']} at n>=500); "
          f"pass rule {len(surv)}")
    print(f"{'k':>3} {'exit':9} {'gate':>5} {'win':8} {'n':>6} {'gross':>9} {'cost':>8} "
          f"{'net':>9} {'ratio':>6} {'tday':>6} {'dpos':>7} {'mo+':>3}")
    for s in surv[:25]:
        ms = [s.get(f"m_2026-0{i}") for i in (1, 2, 3)]
        mp = sum(1 for x in ms if x and x["net_R"] > 0)
        print(f"{s['k']:>3} {s['exit']:9} {str(s['gate_bps']):>5} {s['window']:8} "
              f"{s['n']:>6} {s['gross_R']:>+9.5f} {s['cost_R']:>8.5f} {s['net_R']:>+9.5f} "
              f"{s['ratio_R']:>6.3f} {s['t_net_day']:>6.2f} "
              f"{s['n_days_net_pos']:>3}/{s['n_days']:<3} {mp:>3}")
    print("elapsed", rec["elapsed_s"])


if __name__ == "__main__":
    main()
