"""h1-05 -- the affordability frontier: what an EX-ANTE broker-true cost gate buys.

Every quantity in the gate is knowable at the decision instant (tick-anchored spread at
the broker hour, the commission schedule, the swap schedule, the measured slippage), so
`cost_bps <= X` is a rule the live engine could evaluate before sending an order. This
script prices it: composition, per-month stability, per-day positivity, and the
alternative R-denominated gate the shipped engine actually uses.
"""
from __future__ import annotations

import gzip
import json
import math
import os
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
OUT = f"{D}/H1_FRONTIER_V1.json"
EDGE = "K5_TRAIL025"


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def block(v, all_days=None):
    if not v:
        return None
    c = [r["total_r"] for r in v]
    cb = [r["total_bps"] for r in v]
    g = [r[EDGE] for r in v]
    gb = [r[EDGE] * r["rdp"] * 1e4 for r in v]
    net = [a - b for a, b in zip(g, c)]
    byday = defaultdict(list)
    bymon = defaultdict(list)
    for r, x in zip(v, net):
        byday[r["day"]].append(x)
        bymon[r["month"]].append(x)
    dm = {d: mean(x) for d, x in byday.items()}
    return {
        "n": len(v), "cost_r": mean(c), "cost_bps": mean(cb),
        "gross_r": mean(g), "gross_bps": mean(gb),
        "net_r": mean(net), "net_bps": mean(gb) - mean(cb),
        "t_net": mean(net) / se(net) if se(net) else None,
        "edge_over_cost_R": mean(g) / mean(c) if mean(c) else None,
        "edge_over_cost_bps": mean(gb) / mean(cb) if mean(cb) else None,
        "days": len(dm), "days_positive": sum(1 for x in dm.values() if x > 0),
        "months": {m: {"n": len(x), "net_r": mean(x),
                       "t": (mean(x) / se(x)) if se(x) else None}
                   for m, x in sorted(bymon.items())},
        "symbols": {s: sum(1 for r in v if r["symbol"] == s)
                    for s in sorted({r["symbol"] for r in v})},
        "families": {s: sum(1 for r in v if r["family"] == s)
                     for s in sorted({r["family"] for r in v})},
        "broker_hours": {str(h): sum(1 for r in v if r["broker_hour"] == h)
                         for h in sorted({r["broker_hour"] for r in v})},
        "trades_per_day": len(v) / len(dm) if dm else None,
        "sum_net_r": sum(net),
    }


rows = [json.loads(l) for l in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt") if l.strip()]
res = {"n_rows": len(rows), "edge_contract": EDGE}

# ---------------------------------------------------------- 1. the money gate, fine grid
grid = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.65, 0.70, 0.80, 0.90, 1.00, 1.20, 1.50]
res["MONEY_GATE"] = {}
for t in grid:
    res["MONEY_GATE"]["%.2f" % t] = block([r for r in rows if r["total_bps"] <= t])

# era-adjusted variant of the same gate (does the January era move the frontier?)
res["MONEY_GATE_ERA"] = {}
for t in grid:
    v = [r for r in rows if r["total_bps_era"] <= t]
    b = block(v)
    if b:
        b["cost_bps_era"] = mean([r["total_bps_era"] for r in v])
        b["net_r_era"] = mean([r[EDGE] - r["total_r_era"] for r in v])
        b["edge_over_cost_R_era"] = (mean([r[EDGE] for r in v])
                                     / mean([r["total_r_era"] for r in v]))
    res["MONEY_GATE_ERA"]["%.2f" % t] = b

# ------------------------------------------------- 2. the shipped R gate, same grid shape
res["R_GATE"] = {}
for t in (0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.15, 0.20):
    res["R_GATE"]["%.3f" % t] = block([r for r in rows if r["total_r"] <= t])

# --------------------------------- 3. the shipped SPREAD-limb gate at broker-true spread
res["SHIPPED_GATE_LIMBS"] = {}
for lbl, sel in (
    ("frozen_spread_le_0.10_and_total_le_0.15",
     lambda r: (r["cost_frozen_r"] is not None)),      # placeholder, filled below
):
    pass
res["SHIPPED_GATE_LIMBS"] = {
    "real_spread_r_le_0.10_and_total_r_le_0.15":
        block([r for r in rows if r["spread_r"] <= 0.10 and r["total_r"] <= 0.15]),
    "real_spread_r_le_0.10": block([r for r in rows if r["spread_r"] <= 0.10]),
    "frozen_cost_r_le_0.15": block([r for r in rows
                                    if (r["cost_frozen_r"] or 9e9) <= 0.15]),
}

# ------------------------------------------ 4. train/test: choose on Jan+Feb, read March
tr = [r for r in rows if r["month"] in ("JAN", "FEB")]
te = [r for r in rows if r["month"] == "MAR"]
res["TRAIN_TEST"] = {}
for t in grid:
    a = block([r for r in tr if r["total_bps"] <= t])
    b = block([r for r in te if r["total_bps"] <= t])
    res["TRAIN_TEST"]["%.2f" % t] = {"train_JANFEB": a, "test_MAR": b}

# -------------------------------- 5. money gate INSIDE each symbol (is it just indices?)
res["MONEY_GATE_BY_SYMBOL"] = {}
for t in (0.50, 0.75, 1.00):
    v = [r for r in rows if r["total_bps"] <= t]
    g = defaultdict(list)
    for r in v:
        g[r["symbol"]].append(r)
    res["MONEY_GATE_BY_SYMBOL"]["%.2f" % t] = {
        s: {k: x[k] for k in ("n", "cost_bps", "cost_r", "gross_r", "net_r",
                              "edge_over_cost_R", "t_net", "days_positive", "days")}
        for s, x in ((s, block(vv)) for s, vv in sorted(g.items(), key=lambda kv: -len(kv[1])))}

# ------------------ 6. the alternative: drop the two structurally expensive hour cohorts
res["HOUR_EXCLUSIONS"] = {
    "all": block(rows),
    "ex_broker_hour_0": block([r for r in rows if r["broker_hour"] != 0]),
    "ex_broker_hour_0_22_23": block([r for r in rows if r["broker_hour"] not in (0, 22, 23)]),
    "ex_rollover_and_swap_rows": block([r for r in rows
                                        if r["broker_hour"] != 0 and r["swap_px"] <= 0]),
    "london_ny_only_bh08_20": block([r for r in rows if 8 <= r["broker_hour"] <= 20]),
}

# ------------------------------------------ 7. composed: money gate AND hour exclusion
res["COMPOSED"] = {}
for t in (0.50, 0.60, 0.75, 1.00):
    res["COMPOSED"]["cost_bps_le_%.2f_and_bh_8_20" % t] = block(
        [r for r in rows if r["total_bps"] <= t and 8 <= r["broker_hour"] <= 20])

json.dump(res, open(OUT, "w"), indent=1, default=str)

# --------------------------------------------------------------------------- digest
def line(lbl, b):
    if not b:
        print("  %-34s --" % lbl)
        return
    print("  %-34s n=%6d cost %7.4fbps/%7.4fR gross %+.5f net %+.5f e/c_R %6.3f e/c_bps %6.3f t %+6.2f d+ %d/%d  %s"
          % (lbl, b["n"], b["cost_bps"], b["cost_r"], b["gross_r"], b["net_r"],
             b["edge_over_cost_R"], b["edge_over_cost_bps"], b["t_net"] or 0,
             b["days_positive"], b["days"],
             "/".join("%s%+.4f" % (m, v["net_r"]) for m, v in b["months"].items())))


print("== EX-ANTE MONEY GATE: broker-true cost_bps <= X ==")
for t, b in res["MONEY_GATE"].items():
    line("cost_bps<=" + t, b)
print()
print("== same gate, ERA-ADJUSTED spread (Jan/Feb/Mar era ratios) ==")
for t in ("0.40", "0.50", "0.60", "0.75" if "0.75" in res["MONEY_GATE_ERA"] else "0.70", "1.00"):
    b = res["MONEY_GATE_ERA"].get(t)
    if b:
        print("  cost_bps_era<=%s n=%6d cost_era %7.4f net_era %+.6f e/c_R_era %6.3f"
              % (t, b["n"], b["cost_bps_era"], b["net_r_era"], b["edge_over_cost_R_era"]))
print()
print("== TRAIN(Jan+Feb) / TEST(Mar) ==")
for t in ("0.40", "0.50", "0.60", "0.70", "0.80", "1.00"):
    a = res["TRAIN_TEST"][t]["train_JANFEB"]
    b = res["TRAIN_TEST"][t]["test_MAR"]
    print("  %s  train n=%5d net %+.5f e/c %5.3f | test n=%5d net %+.5f e/c %5.3f t %+5.2f d+ %d/%d"
          % (t, a["n"], a["net_r"], a["edge_over_cost_R"], b["n"], b["net_r"],
             b["edge_over_cost_R"], b["t_net"] or 0, b["days_positive"], b["days"]))
print()
print("== hour exclusions ==")
for k, b in res["HOUR_EXCLUSIONS"].items():
    line(k, b)
print()
print("== composed ==")
for k, b in res["COMPOSED"].items():
    line(k, b)
print()
print("== the shipped gate's limbs at broker-true cost ==")
for k, b in res["SHIPPED_GATE_LIMBS"].items():
    line(k, b)
print()
print("== composition of the cost_bps<=0.50 cohort ==")
b = res["MONEY_GATE"]["0.50"]
print("  symbols:", b["symbols"])
print("  families:", b["families"])
print("  broker hours:", b["broker_hours"])
print("  trades/day %.2f over %d days" % (b["trades_per_day"], b["days"]))
