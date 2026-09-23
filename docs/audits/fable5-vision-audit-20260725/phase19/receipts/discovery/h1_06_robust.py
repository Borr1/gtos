"""h1-06 -- robustness of the affordable cells, and the sensitivities that could kill them.

Four checks, each of which could overturn the h1 headline:
  A. SPREAD CONVENTION. Everything here charges ONE full bid/ask crossing per round turn
     (the repo's own convention). If the true incidence is two crossings, every edge:toll
     roughly halves. Priced.
  B. ERA. The tick anchor is a 37-day 2026Q2/Q3 window; the pool is Q1. Same cohort,
     re-priced at each month's measured era ratio.
  C. DEPTH. Same cells at n floors, per month, per day.
  D. SLIPPAGE BASIS. 12 of 24 symbols carry a MODELLED class-median slippage. Re-price
     with slippage set to zero and to 2x, to bound its influence.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
OUT = f"{D}/H1_ROBUST_V1.json"
EDGE = "K5_TRAIL025"


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


rows = [json.loads(l) for l in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt") if l.strip()]
res = {"n_rows": len(rows)}


def price(v, spread_mult=1.0, use_era=False, slip_mult=1.0, swap_mult=1.0):
    out = []
    for r in v:
        sp = r["spread_px"] * spread_mult * ((r["era_ratio"] or 1.0) if use_era else 1.0)
        tot = sp + r["comm_px"] + r["slip_px"] * slip_mult + r["swap_px"] * swap_mult
        out.append((tot / r["risk_distance"], tot / r["entry_price"] * 1e4, r[EDGE],
                    r[EDGE] * r["rdp"] * 1e4, r["day"], r["month"]))
    c = [x[0] for x in out]
    cb = [x[1] for x in out]
    g = [x[2] for x in out]
    gb = [x[3] for x in out]
    net = [a - b for a, b in zip(g, c)]
    byday, bymon = defaultdict(list), defaultdict(list)
    for x, nn in zip(out, net):
        byday[x[4]].append(nn)
        bymon[x[5]].append(nn)
    dm = {d: mean(z) for d, z in byday.items()}
    return {"n": len(v), "cost_r": mean(c), "cost_bps": mean(cb), "gross_r": mean(g),
            "net_r": mean(net), "t_net": mean(net) / se(net) if se(net) else None,
            "edge_over_cost_R": mean(g) / mean(c) if mean(c) else None,
            "edge_over_cost_bps": mean(gb) / mean(cb) if mean(cb) else None,
            "days": len(dm), "days_positive": sum(1 for z in dm.values() if z > 0),
            "months": {m: round(mean(z), 6) for m, z in sorted(bymon.items())}}


COHORTS = {
    "ALL": rows,
    "money_gate_0.50": [r for r in rows if r["total_bps"] <= 0.50],
    "money_gate_0.50_bh8_20": [r for r in rows if r["total_bps"] <= 0.50 and 8 <= r["broker_hour"] <= 20],
    "GER40_cheap": [r for r in rows if r["symbol"] == "GER40" and r["total_bps"] <= 0.50],
    "NAS100_cheap": [r for r in rows if r["symbol"] == "NAS100" and r["total_bps"] <= 0.50],
    "GER40+NAS100_cheap": [r for r in rows if r["symbol"] in ("GER40", "NAS100") and r["total_bps"] <= 0.50],
    "GER40_london": [r for r in rows if r["symbol"] == "GER40" and r.get("kill_zone") == "london"],
    "index_class": [r for r in rows if r["instrument_class"] == "index"],
    "index_cheap": [r for r in rows if r["instrument_class"] == "index" and r["total_bps"] <= 0.60],
    "regime_transition_break": [r for r in rows if r["family"] == "regime_transition_break"],
    "R_gate_0.02": [r for r in rows if r["total_r"] <= 0.02],
}

SENS = {
    "base_1x_spread": dict(spread_mult=1.0),
    "2x_spread_two_crossings": dict(spread_mult=2.0),
    "0.5x_spread_passive_entry": dict(spread_mult=0.5),
    "era_adjusted": dict(use_era=True),
    "era_adjusted_2x_spread": dict(use_era=True, spread_mult=2.0),
    "slip_zero": dict(slip_mult=0.0),
    "slip_2x": dict(slip_mult=2.0),
    "swap_zero": dict(swap_mult=0.0),
}

res["SENSITIVITY"] = {}
for cname, cv in COHORTS.items():
    res["SENSITIVITY"][cname] = {sname: price(cv, **kw) for sname, kw in SENS.items()}

# ---------------------------------------------------------- per-symbol x hour, deep grid
g = defaultdict(list)
for r in rows:
    g[(r["symbol"], r["broker_hour"])].append(r)
res["SYMBOL_X_BROKER_HOUR"] = {
    "%s|bh%02d" % k: {"n": len(v), "cost_bps": mean([x["total_bps"] for x in v]),
                      "cost_r": mean([x["total_r"] for x in v]),
                      "spread_bps": mean([x["spread_bps"] for x in v]),
                      "gross_r": mean([x[EDGE] for x in v]),
                      "net_r": mean([x[EDGE] - x["total_r"] for x in v]),
                      "e_over_c": (mean([x[EDGE] for x in v]) / mean([x["total_r"] for x in v]))
                      if mean([x["total_r"] for x in v]) else None}
    for k, v in sorted(g.items()) if len(v) >= 20}

# ------------------------------------------------------------------ dow, both clocks
for lbl, fn in (("broker_dow", lambda r: r["broker_dow"]), ("utc_dow", lambda r: r["utc_dow"])):
    gg = defaultdict(list)
    for r in rows:
        gg[fn(r)].append(r)
    res.setdefault("DOW", {})[lbl] = {
        str(k): {"n": len(v), "cost_bps": mean([x["total_bps"] for x in v]),
                 "cost_r": mean([x["total_r"] for x in v]),
                 "gross_r": mean([x[EDGE] for x in v]),
                 "net_r": mean([x[EDGE] - x["total_r"] for x in v])}
        for k, v in sorted(gg.items())}

json.dump(res, open(OUT, "w"), indent=1, default=str)

print("%-26s %-26s %6s %9s %9s %9s %8s %6s %s"
      % ("cohort", "sensitivity", "n", "cost_bps", "cost_R", "net_R", "e/c_R", "t", "months"))
for cname in COHORTS:
    for sname in SENS:
        b = res["SENSITIVITY"][cname][sname]
        print("%-26s %-26s %6d %9.4f %9.5f %+9.5f %8.3f %+6.2f %s"
              % (cname, sname, b["n"], b["cost_bps"], b["cost_r"], b["net_r"],
                 b["edge_over_cost_R"] or 0, b["t_net"] or 0,
                 " ".join("%s%+.4f" % (m, v) for m, v in b["months"].items())))
    print()
print("== day of week (broker clock) ==")
for k, v in res["DOW"]["broker_dow"].items():
    print("  dow%s n=%6d cost %7.4fbps/%7.5fR gross %+.5f net %+.5f"
          % (k, v["n"], v["cost_bps"], v["cost_r"], v["gross_r"], v["net_r"]))
