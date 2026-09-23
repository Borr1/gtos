"""b1 step 13 — daily economics, and the last hour-rule question.

1. R/day and trades/day for each book, in and out of window. A book earning several R
   per day would be extraordinary against this estate's best armed sleeve (+0.3 R/day),
   so the number is a sanity check on the whole exercise as much as an output.
2. Is ANY hour rule stable? The cost-defined hour limb inverted out of sample. Test the
   two mechanism-defined alternatives that need no outcome column:
     - h2's exchange cash-session rule
     - the instrument's own cash open +/- a fixed band
   on all five months, inside the three gate-reachable instruments.
3. Concurrency: how many of these trades are open at once, which decides whether R/day
   is bankable at all.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import b1_np as N  # noqa: E402

MONTHS = ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05")
M3, M2 = MONTHS[:3], MONTHS[3:]
IDX3 = ("US30_cash", "GER40", "NAS100")
K, EXIT = 3, "STOPONLY"


def daily(g, c, M, sel):
    q = sel & np.isfinite(g) & np.isfinite(c)
    if not q.any():
        return {}
    net = g[q] - c[q]
    ud, inv = np.unique(M["day"][q], return_inverse=True)
    Gn = len(ud)
    ds = np.bincount(inv, weights=net, minlength=Gn)
    dc = np.bincount(inv, minlength=Gn)
    return {"n": int(q.sum()), "days": Gn,
            "trades_per_day": float(q.sum() / Gn),
            "R_per_day_mean": float(ds.mean()),
            "R_per_day_median": float(np.median(ds)),
            "R_per_day_sd": float(ds.std(ddof=1)),
            "R_per_day_p05": float(np.quantile(ds, 0.05)),
            "R_per_day_p95": float(np.quantile(ds, 0.95)),
            "worst_day_R": float(ds.min()), "best_day_R": float(ds.max()),
            "days_positive": int((ds > 0).sum()),
            "total_R": float(ds.sum()),
            "sharpe_daily": (float(ds.mean() / ds.std(ddof=1)) if ds.std(ddof=1) > 0 else None),
            "annualised_sharpe_252": (float(ds.mean() / ds.std(ddof=1) * np.sqrt(252))
                                      if ds.std(ddof=1) > 0 else None)}


def main():
    t0 = time.time()
    M, G, rows = N.load()
    hrc = M["cost_hour"]
    gate = (hrc * M["bpsfac"]) <= 0.60 + 1e-12
    in3, in2 = np.isin(M["month"], M3), np.isin(M["month"], M2)
    g = G[(K, EXIT)]
    out = {}

    POPS = {"BOOK-A gate<=0.60": gate,
            "BOOK-C 3 instruments all hours": np.isin(M["symbol"], IDX3),
            "BOOK-C ∩ cash session": np.isin(M["symbol"], IDX3) & M["cash"],
            "whole book (swarm contract)": np.ones(len(g), bool)}
    out["DAILY"] = {}
    for lab, m in POPS.items():
        gv = G[(5, "TRAIL025")] if lab.startswith("whole") else g
        out["DAILY"][lab] = {"hunt_3m": daily(gv, hrc, M, m & in3),
                             "oos_2m": daily(gv, hrc, M, m & in2),
                             "pooled_5m": daily(gv, hrc, M, m)}

    # ---------------------------------------------------------------- hour rules
    hr = {}
    inst = np.isin(M["symbol"], IDX3)
    RULES = {
        "no hour rule": inst,
        "cost gate <=0.60 bps (b1-BOOK-V1)": gate,
        "h2 exchange cash session": inst & M["cash"],
        "cash session AND cost gate": inst & M["cash"] & gate,
        "broker hours 08-20": inst & (M["broker_hour"] >= 8) & (M["broker_hour"] <= 20),
        "broker hours 10-18": inst & (M["broker_hour"] >= 10) & (M["broker_hour"] <= 18),
        "outside cash session": inst & ~M["cash"],
    }
    for lab, m in RULES.items():
        d = {"hunt_3m": N.slim(N.score(g, hrc, M, m & in3)),
             "oos_2m": N.slim(N.score(g, hrc, M, m & in2)),
             "pooled_5m": N.slim(N.score(g, hrc, M, m))}
        for mm in MONTHS:
            d[mm] = N.slim(N.score(g, hrc, M, m & (M["month"] == mm)))
        hr[lab] = d
    out["HOUR_RULES"] = hr

    # ---------------------------------------------------------------- concurrency
    for lab, m in (("BOOK-A", gate), ("BOOK-C", inst)):
        q = m & np.isfinite(g)
        dts = [datetime.fromisoformat(r["dt"]) for r, keep in zip(rows, q) if keep]
        ev = []
        for d0 in dts:
            ev.append((d0, 1)); ev.append((d0 + timedelta(minutes=120), -1))
        ev.sort()
        cur = mx = 0
        area = 0.0
        prev = None
        for tt, delta in ev:
            if prev is not None:
                area += cur * (tt - prev).total_seconds() / 60.0
            cur += delta
            mx = max(mx, cur)
            prev = tt
        span = (max(dts) - min(dts)).total_seconds() / 60.0
        out.setdefault("CONCURRENCY", {})[lab] = {
            "n": len(dts), "max_concurrent_positions": mx,
            "mean_concurrent_over_span": round(area / span, 3),
            "note": "each trade occupies 120 minutes; a constant-R book at 3 open "
                    "positions is running 3x the nominal per-trade risk"}

    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(f"{D}/B1_DAILY_V1.json", "w") as f:
        json.dump(out, f, indent=1)

    print("DAILY ECONOMICS (hour-true cost)")
    for lab, d in out["DAILY"].items():
        for w in ("hunt_3m", "oos_2m", "pooled_5m"):
            v = d[w]
            if not v:
                continue
            print(f"  {lab:32} {w:10} {v['trades_per_day']:>6.1f} trades/day  "
                  f"{v['R_per_day_mean']:>+8.3f} R/day  sd {v['R_per_day_sd']:>7.3f}  "
                  f"worst {v['worst_day_R']:>+8.2f}  sharpe {(v['sharpe_daily'] or 0):>+6.3f}")
    print()
    print("HOUR RULES inside the 3 gate-reachable instruments (net R/trade)")
    print(f"  {'rule':38}" + "".join(f"{m[-2:]:>9}" for m in MONTHS)
          + f"{'hunt':>9}{'OOS':>9}{'5m':>9}{'5m rat':>8}")
    for lab, d in out["HOUR_RULES"].items():
        cells = "".join(f"{d[m]['net_R']:>+9.4f}" if d[m].get("n") else f"{'-':>9}"
                        for m in MONTHS)
        print(f"  {lab:38}{cells}{d['hunt_3m']['net_R']:>+9.4f}"
              f"{d['oos_2m']['net_R']:>+9.4f}{d['pooled_5m']['net_R']:>+9.4f}"
              f"{(d['pooled_5m']['ratio_R'] or 0):>8.3f}")
    print()
    print("CONCURRENCY:", json.dumps(out["CONCURRENCY"], indent=1, default=str)[:600])
    print("elapsed", out["elapsed_s"])


if __name__ == "__main__":
    main()
