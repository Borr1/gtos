"""b1 step 7 — THE DECIDING CONTROL: a 20-draw whole-day placebo null.

b1_06 found one shifted anchor (+1 day, same broker hour) that books +0.0759 against the
book's +0.0765. With four draws that cannot be adjudicated. This step builds the null
properly: shift the decision instant by +/- 1..10 CALENDAR DAYS, which preserves the
instrument, the broker hour, the side, the risk unit, the cost and the gate EXACTLY, and
destroys only the intraday timing of the signal.

    H0 : b1-BOOK-V1 is "these instruments, in these hours, in this direction" —
         structure the signal did not supply. Then the null draws should straddle the
         real number.
    H1 : the signal supplies the timing. Then the real number sits in the null's tail.

Reports the empirical p-value P(placebo >= real) over 20 draws, plus the same test on
GROSS (so the cost gate cannot be doing the work) and a side-randomised variant that
also removes the direction.
"""
import bisect
import csv
import gzip
import json
import os
import random
import sys
import time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_06_placebo as P  # noqa: E402

DAYS = [d for d in range(-10, 11) if d != 0]
K, GATE = 3, 0.60


def main():
    t0 = time.time()
    rows = [json.loads(x) for x in gzip.open(f"{D}/h5_SUBSTRATE_5M.jsonl.gz", "rt") if x.strip()]
    h1 = {}
    for ln in gzip.open(f"{D}/b1_COST_JOIN_V1.jsonl.gz", "rt"):
        o = json.loads(ln)
        h1[(o["cid"], o["dt"])] = o
    book = []
    for r in rows:
        o = h1.get((r["cid"], r["dt"]))
        if o is None:
            continue
        if o["cost_h1_r"] * r["rdp"] * 1e4 <= GATE + 1e-12 and r.get("K3_STOPONLY") is not None:
            r["cost_h1_r"] = o["cost_h1_r"]
            book.append(r)

    real = P.stat([(r["K3_STOPONLY"], r) for r in book])
    out = {"real": real, "days_tested": DAYS, "draws": {}}
    print("REAL net", round(real["net_R"], 6), "gross", round(real["gross_R"], 6), flush=True)

    nets, grosses = [], []
    for d in DAYS:
        s = P.stat(P.build(book, d * 1440))
        out["draws"][str(d)] = s
        if s["n"] >= 500:
            nets.append(s["net_R"]); grosses.append(s["gross_R"])
        print(f"  day {d:+3d}  n={s['n']:>5} gross={s['gross_R']:>+9.5f} "
              f"net={s['net_R']:>+9.5f} ratio={s['ratio_R']:>7.3f} t={s['t_net']:>+6.2f}",
              flush=True)

    # side-randomised: destroy the direction too (fixed seed, one draw per day shift)
    rnd = random.Random(20260806)
    sr = []
    for r in book:
        q = dict(r)
        q["side"] = rnd.choice(("LONG", "SHORT"))
        sr.append(q)
    out["side_randomised_shift0"] = P.stat(P.build(sr, 0))

    nets = np.array(nets); grosses = np.array(grosses)
    out["null"] = {
        "n_draws": int(len(nets)),
        "net_mean": float(nets.mean()), "net_sd": float(nets.std(ddof=1)),
        "net_min": float(nets.min()), "net_max": float(nets.max()),
        "net_p90": float(np.quantile(nets, 0.90)), "net_p95": float(np.quantile(nets, 0.95)),
        "p_value_net": float((nets >= real["net_R"]).sum() + 1) / (len(nets) + 1),
        "z_net": float((real["net_R"] - nets.mean()) / nets.std(ddof=1)),
        "gross_mean": float(grosses.mean()), "gross_sd": float(grosses.std(ddof=1)),
        "gross_max": float(grosses.max()),
        "p_value_gross": float((grosses >= real["gross_R"]).sum() + 1) / (len(grosses) + 1),
        "z_gross": float((real["gross_R"] - grosses.mean()) / grosses.std(ddof=1)),
    }
    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_DAYNULL_V1.json", "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out["null"], indent=1))
    print("side-randomised:", {k: round(v, 5) if isinstance(v, float) else v
                               for k, v in out["side_randomised_shift0"].items()})


if __name__ == "__main__":
    main()
