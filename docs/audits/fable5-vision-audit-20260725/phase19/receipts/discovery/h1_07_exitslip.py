"""h1-07 -- the FIFTH cost term this lane's headline does NOT charge: EXIT slippage.

l10-F9 measured, on 167 clean live stop exits, that a stop fills **+0.032236 R worse than
the recorded stop** on average (83.83 % adverse, only 13.17 % exact), by class:
    fx 0.059002 (n=69) | crypto 0.026603 (n=25) | metals 0.011636 (n=27) | index 0.007240 (n=46)
Those R values are denominated in the LIVE book's stop distances, which are 0.19-1.77 % of
price against the January pool's 0.03-0.75 %, so they DO NOT transfer as R. They transfer as
PRICE: exit_slip_price = class_R x live_stop_pct_of_price x price.

That is a real charge and it is not in H1_SURFACE. It is quarantined here rather than folded
in for two reasons, both stated so the reader can overrule them:
  1. It is an EXIT-instant microstructure quantity measured on 167 exits, 46 of them index,
     against 43,755 candidates -- one to two orders of magnitude thinner than the spread
     anchor (300 M ticks).
  2. Its incidence depends on the exit contract. Under `TRAIL025` nearly every exit is a
     trailing-stop market order, so the right multiplier is close to 1.0 per trade; under a
     limit target it applies only to the stop-out fraction. This script prices BOTH bounds.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import statistics as st
from collections import defaultdict

D = os.path.dirname(os.path.abspath(__file__))
OUT = f"{D}/H1_EXITSLIP_V1.json"
EDGE = "K5_TRAIL025"

# l10-F9 class means, R at LIVE stop geometry
F9_CLASS_R = {"fx": 0.059002, "jpy_fx": 0.059002, "crypto": 0.026603,
              "metals": 0.011636, "index": 0.007240}
F9_POOLED_R = 0.032236

GEO = json.load(open(f"{D}/L10X_STOP_GEOMETRY_V1.json"))["live_by_symbol"]
LIVEKEY = {"XAUUSD": "XAUUSD", "SPX500": "US500.cash", "NAS100": "US100.cash",
           "US30_cash": "US30.cash", "UK100": "UK100.cash", "GER40": "GER40.cash",
           "JP225": "JP225.cash", "BTCUSD": "BTCUSD", "ETHUSD": "ETHUSD",
           "EURUSD": "EURUSD", "GBPUSD": "GBPUSD", "USDJPY": "USDJPY",
           "GBPJPY": "GBPJPY", "AUDUSD": "AUDUSD"}


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


rows = [json.loads(l) for l in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt") if l.strip()]

# class median live stop pct, for symbols with no live capture
by_class = defaultdict(list)
for sym, k in LIVEKEY.items():
    if k in GEO:
        cls = next((r["instrument_class"] for r in rows if r["symbol"] == sym), None)
        by_class[cls].append(GEO[k]["median_pct"] / 100.0)
CLASS_STOP = {c: st.median(v) for c, v in by_class.items() if v}

EXIT_BPS = {}
for sym in sorted({r["symbol"] for r in rows}):
    cls = next(r["instrument_class"] for r in rows if r["symbol"] == sym)
    k = LIVEKEY.get(sym)
    stop_frac = (GEO[k]["median_pct"] / 100.0) if (k and k in GEO) else CLASS_STOP.get(cls)
    basis = "LIVE_SYMBOL" if (k and k in GEO) else f"CLASS_MEDIAN[{cls}]"
    rr = F9_CLASS_R.get(cls, F9_POOLED_R)
    EXIT_BPS[sym] = {"exit_slip_bps": rr * stop_frac * 1e4 if stop_frac else None,
                     "class": cls, "f9_class_r": rr, "live_stop_frac": stop_frac,
                     "basis": basis}

res = {"EXIT_SLIP_BPS_PER_SYMBOL": EXIT_BPS, "class_stop_frac": CLASS_STOP,
       "f9_class_r": F9_CLASS_R}


def price(v, mult):
    """mult = expected number of market-order exits charged this slippage (0, 0.544, 1)."""
    c, g, cb, gb, net = [], [], [], [], []
    byday, bymon = defaultdict(list), defaultdict(list)
    for r in v:
        ex = (EXIT_BPS[r["symbol"]]["exit_slip_bps"] or 0.0) * mult * r["entry_price"] / 1e4
        tot = r["spread_px"] + r["comm_px"] + r["slip_px"] + r["swap_px"] + ex
        cr = tot / r["risk_distance"]
        c.append(cr)
        cb.append(tot / r["entry_price"] * 1e4)
        g.append(r[EDGE])
        gb.append(r[EDGE] * r["rdp"] * 1e4)
        net.append(r[EDGE] - cr)
        byday[r["day"]].append(r[EDGE] - cr)
        bymon[r["month"]].append(r[EDGE] - cr)
    dm = {d: mean(x) for d, x in byday.items()}
    return {"n": len(v), "exit_slip_mult": mult, "cost_r": mean(c), "cost_bps": mean(cb),
            "gross_r": mean(g), "net_r": mean(net),
            "t_net": mean(net) / se(net) if se(net) else None,
            "edge_over_cost_R": mean(g) / mean(c) if mean(c) else None,
            "edge_over_cost_bps": mean(gb) / mean(cb) if mean(cb) else None,
            "days": len(dm), "days_positive": sum(1 for x in dm.values() if x > 0),
            "months": {m: round(mean(x), 6) for m, x in sorted(bymon.items())}}


COHORTS = {
    "ALL": rows,
    "money_gate_0.50": [r for r in rows if r["total_bps"] <= 0.50],
    "money_gate_0.50_bh8_20": [r for r in rows if r["total_bps"] <= 0.50 and 8 <= r["broker_hour"] <= 20],
    "GER40+NAS100_cheap": [r for r in rows if r["symbol"] in ("GER40", "NAS100") and r["total_bps"] <= 0.50],
    "GER40_london": [r for r in rows if r["symbol"] == "GER40" and r.get("kill_zone") == "london"],
    "GER40_all": [r for r in rows if r["symbol"] == "GER40"],
    "NAS100_all": [r for r in rows if r["symbol"] == "NAS100"],
    "US30_all": [r for r in rows if r["symbol"] == "US30_cash"],
    "regime_transition_break": [r for r in rows if r["family"] == "regime_transition_break"],
}
res["PRICED"] = {c: {("mult_%.3f" % m): price(v, m) for m in (0.0, 0.544, 1.0)}
                 for c, v in COHORTS.items()}

json.dump(res, open(OUT, "w"), indent=1, default=str)

print("== exit-slippage charge implied per symbol (bps of notional, one market exit) ==")
for s, v in sorted(EXIT_BPS.items(), key=lambda kv: -(kv[1]["exit_slip_bps"] or 0)):
    print("  %-12s %8.4f bps   class=%-7s f9_R=%.6f live_stop=%.5f  %s"
          % (s, v["exit_slip_bps"] or 0, v["class"], v["f9_class_r"],
             v["live_stop_frac"] or 0, v["basis"]))
print()
print("%-26s %6s %6s %9s %9s %9s %8s %6s %s"
      % ("cohort", "mult", "n", "cost_bps", "cost_R", "net_R", "e/c_R", "t", "months"))
for c in COHORTS:
    for m in ("mult_0.000", "mult_0.544", "mult_1.000"):
        b = res["PRICED"][c][m]
        print("%-26s %6s %6d %9.4f %9.5f %+9.5f %8.3f %+6.2f %s"
              % (c, m.split("_")[1], b["n"], b["cost_bps"], b["cost_r"], b["net_r"],
                 b["edge_over_cost_R"] or 0, b["t_net"] or 0,
                 " ".join("%s%+.4f" % (k, x) for k, x in b["months"].items())))
    print()
