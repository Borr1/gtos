"""b2c — the closed-market rows.

h1 flagged (and did not price) that TEN of the 24 instruments carry ZERO ticks at
broker hour 00 in the 300M-tick archive -- every index CFD, both metals, both oils --
because the instrument is in its daily break. The pool emits candidates on them anyway.
Those rows are priced at the flat-median fallback, which is not a measurement of that
hour: there is no quote to cross.

b2_ger40 found broker hour 00 carrying +1.855 R/trade on 28 GER40 rows. This prices what
happens to every cell when rows generated while the instrument's own exchange is shut are
removed, five months, no-trail contract.
"""
from __future__ import annotations

import json, os, sys, time

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e_lib  # noqa: E402
import b2_verify as V  # noqa: E402

TICK = json.load(open(f"{D}/L10X_TICK_SPREAD_V1.json"))


def zero_tick_hours(sym):
    tk = TICK.get("ftmo:" + e_lib.TMAP.get(sym, sym))
    if not tk:
        return set()
    byh = tk.get("spread_bps_median_by_broker_hour") or {}
    return {h for h in range(24) if str(h) not in byh}


def main():
    t0 = time.time()
    packs = {m: V.load_month(m, p, col="K3_STOPONLY") for m, p in V.MONTHS}
    A = {k: np.concatenate([packs[m][k] for m, _ in V.MONTHS]) for k in
         ("g", "c", "cb", "sym", "day", "mon", "sym", "side", "bh")}
    n = len(A["g"])
    ZT = {s: zero_tick_hours(s) for s in sorted(set(A["sym"].tolist()))}
    out = {"zero_tick_hours_per_symbol": {s: sorted(v) for s, v in ZT.items() if v}}
    closed = np.array([A["bh"][i] in ZT.get(A["sym"][i], set()) for i in range(n)])
    out["closed_market_rows"] = {
        "n": int(closed.sum()), "share": float(closed.mean()),
        "per_symbol": {s: int((closed & (A["sym"] == s)).sum())
                       for s in sorted(set(A["sym"][closed].tolist()))}}
    print(f"rows generated while the instrument has ZERO ticks in its own hour: "
          f"{closed.sum():,} of {n:,} ({closed.mean():.2%})")
    print("  per symbol:", out["closed_market_rows"]["per_symbol"])
    print("  zero-tick hours:", {s: sorted(v) for s, v in ZT.items() if v})

    GATE = A["cb"] <= 0.60 + 1e-12
    HUNT = np.isin(A["mon"], ["2026-01", "2026-02", "2026-03"])
    OOS = np.isin(A["mon"], ["2026-04", "2026-05"])
    OPEN = ~closed

    def S(m):
        return V.stats(A["g"][m], A["c"][m], A["day"][m], A["mon"][m])

    rows = []
    for lab, m in (("BOOK ungated", np.ones(n, bool)),
                   ("gate<=0.60bps (3 index names)", GATE),
                   ("GER40 | gate<=0.60bps", GATE & (A["sym"] == "GER40")),
                   ("GER40 | all hours", A["sym"] == "GER40"),
                   ("US30_cash | gate<=0.60bps", GATE & (A["sym"] == "US30_cash")),
                   ("NAS100 | gate<=0.60bps", GATE & (A["sym"] == "NAS100"))):
        for tag, mm in (("with closed-market rows", m), ("OPEN MARKET ONLY", m & OPEN)):
            a, h, o = S(mm), S(mm & HUNT), S(mm & OOS)
            rows.append({"cell": lab, "arm": tag, "all5": V.rnd(a), "hunt": V.rnd(h),
                         "oos": V.rnd(o)})
            print(f"  {lab:<30} {tag:<24} n {a.get('n',0):>6} net {a.get('net',0):+.5f}"
                  f" r {(a.get('ratio_r') or 0):>7.3f} | hunt {h.get('net',0):+.5f}"
                  f" | oos {o.get('net',0):+.5f} ({o.get('n',0)})")
    out["arms"] = rows

    # what the closed rows are worth on their own
    for lab, m in (("ALL closed rows", closed),
                   ("closed rows inside the 0.60 gate", closed & GATE),
                   ("GER40 closed rows", closed & (A["sym"] == "GER40"))):
        s = S(m)
        out[lab] = V.rnd(s)
        if s.get("n", 0) > 2:
            print(f"  {lab:<34} n {s['n']:>5} gross {s['gross']:+.5f} net {s['net']:+.5f}"
                  f"  total {s['total_net_R']:+.1f} R")
    out["seconds"] = round(time.time() - t0, 1)
    json.dump(out, open(f"{D}/B2_CLOSED_V1.json", "w"), indent=1)
    print(f"\nwrote B2_CLOSED_V1.json ({out['seconds']}s)")


if __name__ == "__main__":
    main()
