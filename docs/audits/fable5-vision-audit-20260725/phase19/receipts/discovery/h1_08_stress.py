"""h1-08 -- the joint worst case, and the exact hour map of the surviving cells.

Stress stack, applied together rather than one at a time:
    spread x2 (two crossings)  +  era ratio  +  exit slippage at mult 1.0  +  slip x2
That is every disclosed uncertainty pushed in the expensive direction simultaneously. A
cell that still clears edge:toll 1.0 there is affordable under any convention this estate
can currently defend.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
OUT = f"{D}/H1_STRESS_V1.json"
EDGE = "K5_TRAIL025"
EXIT = json.load(open(f"{D}/H1_EXITSLIP_V1.json"))["EXIT_SLIP_BPS_PER_SYMBOL"]


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


rows = [json.loads(l) for l in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt") if l.strip()]


def price(v, spread_mult=1.0, era=False, exit_mult=0.0, slip_mult=1.0):
    c, cb, g, gb, net = [], [], [], [], []
    bymon, byday = defaultdict(list), defaultdict(list)
    for r in v:
        sp = r["spread_px"] * spread_mult * ((r["era_ratio"] or 1.0) if era else 1.0)
        ex = (EXIT[r["symbol"]]["exit_slip_bps"] or 0.0) * exit_mult * r["entry_price"] / 1e4
        tot = sp + r["comm_px"] + r["slip_px"] * slip_mult + r["swap_px"] + ex
        cr = tot / r["risk_distance"]
        c.append(cr); cb.append(tot / r["entry_price"] * 1e4)
        g.append(r[EDGE]); gb.append(r[EDGE] * r["rdp"] * 1e4)
        net.append(r[EDGE] - cr)
        bymon[r["month"]].append(r[EDGE] - cr)
        byday[r["day"]].append(r[EDGE] - cr)
    dm = {d: mean(x) for d, x in byday.items()}
    return {"n": len(v), "cost_bps": mean(cb), "cost_r": mean(c), "gross_r": mean(g),
            "net_r": mean(net), "t_net": mean(net) / se(net) if se(net) else None,
            "edge_over_cost_R": mean(g) / mean(c) if mean(c) else None,
            "edge_over_cost_bps": mean(gb) / mean(cb) if mean(cb) else None,
            "days": len(dm), "days_positive": sum(1 for x in dm.values() if x > 0),
            "months": {m: round(mean(x), 6) for m, x in sorted(bymon.items())},
            "months_positive": sum(1 for x in bymon.values() if mean(x) > 0)}


COH = {
    "ALL": lambda r: True,
    "cost_bps<=0.50": lambda r: r["total_bps"] <= 0.50,
    "cost_bps<=0.50 & bh8-20": lambda r: r["total_bps"] <= 0.50 and 8 <= r["broker_hour"] <= 20,
    "GER40 cost<=0.50": lambda r: r["symbol"] == "GER40" and r["total_bps"] <= 0.50,
    "NAS100 cost<=0.50": lambda r: r["symbol"] == "NAS100" and r["total_bps"] <= 0.50,
    "GER40+NAS100 cost<=0.50": lambda r: r["symbol"] in ("GER40", "NAS100") and r["total_bps"] <= 0.50,
    "GER40+NAS100 cost<=0.50 bh8-20": lambda r: (r["symbol"] in ("GER40", "NAS100")
                                                 and r["total_bps"] <= 0.50
                                                 and 8 <= r["broker_hour"] <= 20),
    "GER40 london": lambda r: r["symbol"] == "GER40" and r.get("kill_zone") == "london",
    "GER40+NAS100+US30 cost<=0.50": lambda r: (r["symbol"] in ("GER40", "NAS100", "US30_cash")
                                              and r["total_bps"] <= 0.50),
}
STRESS = {
    "base": {},
    "worst_joint": dict(spread_mult=2.0, era=True, exit_mult=1.0, slip_mult=2.0),
    "mid_joint": dict(spread_mult=1.0, era=True, exit_mult=0.544, slip_mult=1.0),
}
res = {"COHORTS": {}}
for cn, sel in COH.items():
    v = [r for r in rows if sel(r)]
    res["COHORTS"][cn] = {sn: price(v, **kw) for sn, kw in STRESS.items()}

# ------------------------------------------- exact hour map of the surviving instruments
g = defaultdict(list)
for r in rows:
    if r["symbol"] in ("GER40", "NAS100", "US30_cash", "SPX500", "UK100", "JP225", "XAUUSD"):
        g[(r["symbol"], r["broker_hour"])].append(r)
res["HOUR_MAP"] = {
    "%s|bh%02d" % k: {**{kk: price(v)[kk] for kk in
                         ("n", "cost_bps", "cost_r", "gross_r", "net_r", "edge_over_cost_R")},
                      "spread_bps": mean([x["spread_bps"] for x in v]),
                      "utc_hours": sorted({x["utc_hour"] for x in v})}
    for k, v in sorted(g.items()) if len(v) >= 15}

json.dump(res, open(OUT, "w"), indent=1, default=str)

print("%-32s %-12s %6s %9s %9s %10s %8s %7s %5s %3s"
      % ("cohort", "stress", "n", "cost_bps", "cost_R", "net_R", "e/c_R", "t_net", "d+", "mo+"))
for cn in COH:
    for sn in STRESS:
        b = res["COHORTS"][cn][sn]
        print("%-32s %-12s %6d %9.4f %9.5f %+10.5f %8.3f %+7.2f %5s %3d"
              % (cn, sn, b["n"], b["cost_bps"], b["cost_r"], b["net_r"],
                 b["edge_over_cost_R"] or 0, b["t_net"] or 0,
                 "%d/%d" % (b["days_positive"], b["days"]), b["months_positive"]))
    print()
print("== hour map, index complex + XAUUSD (broker hour; n>=15) ==")
print("%-18s %5s %9s %9s %10s %10s %8s %s"
      % ("cell", "n", "spr_bps", "cost_bps", "gross_R", "net_R", "e/c_R", "utc_hours"))
for k, v in sorted(res["HOUR_MAP"].items(), key=lambda kv: -(kv[1]["edge_over_cost_R"] or -9))[:45]:
    print("%-18s %5d %9.4f %9.4f %+10.5f %+10.5f %8.3f %s"
          % (k, v["n"], v["spread_bps"], v["cost_bps"], v["gross_r"], v["net_r"],
             v["edge_over_cost_R"] or 0, v["utc_hours"]))
