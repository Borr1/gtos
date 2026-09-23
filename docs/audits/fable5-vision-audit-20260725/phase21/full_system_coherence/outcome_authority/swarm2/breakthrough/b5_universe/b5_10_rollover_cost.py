"""B5 step (e2) — the rollover correction, which is the largest single cost error in this lane.

Every cost figure in B5_SYMBOL_COST_V1 is a typical-hour p50.  But these are BROKER D1 bars:
they close at the broker's server midnight, i.e. broker hour 00.  **A daily close-to-close
strategy therefore transacts at exactly the worst hour of the day.**

Lane 5's tick receipt (LANE5_TICK_MICROSTRUCTURE_V1.json, 30.8 M ticks over 2026-06-18..07-26)
carries time-weighted spread in bps of mid by BROKER hour for six symbols.  This script reads
the hour-00 / median ratio per symbol, forms a class multiplier, applies it to the SPREAD
component only (commission does not vary by hour), and re-prices the cells.

Writes <OUT>/B5_ROLLOVER_COST_V1.json.
"""
import json, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
L5 = os.path.join(HERE, "..", "..", "lane5_receipts", "LANE5_TICK_MICROSTRUCTURE_V1.json")

CLASS_OF = {"EURUSD": "fx", "GBPJPY": "fx", "XAUUSD": "commodity",
            "BTCUSD": "crypto", "US500_cash": "index", "USOIL_cash": "commodity"}


def main():
    tick = json.load(open(L5))
    ratios = {}
    for sym, d in tick.items():
        by = d.get("spread_bps_by_broker_hour") or {}
        if not by:
            continue
        vals = {int(h): v[0] for h, v in by.items()}
        med = st.median(vals.values())
        close_hour = 0 if 0 in vals else min(vals)      # metals/indices have no hour-00 quote
        ratios[sym] = {"class": CLASS_OF.get(sym), "hour_used": close_hour,
                       "spread_at_close_hour_bps": vals[close_hour],
                       "median_hour_spread_bps": med,
                       "rollover_multiplier": vals[close_hour] / med,
                       "n_hours": len(vals)}
    by_class = {}
    for sym, r in ratios.items():
        by_class.setdefault(r["class"], []).append(r["rollover_multiplier"])
    class_mult = {c: st.median(v) for c, v in by_class.items()}
    # classes with no tick coverage inherit the FX multiplier only if they trade the rollover;
    # equity CFDs are closed at broker hour 00, so their D1 close is a session close, not a
    # rollover -- they get 1.0 and that is stated as an assumption, not a measurement.
    class_mult.setdefault("equity", 1.0)

    cost = json.load(open(os.path.join(OUT, "B5_SYMBOL_COST_V1.json")))["symbols"]
    adj = {}
    for s, v in cost.items():
        m = class_mult.get(v["class"])
        sp, cm = v["spread_bps"], v["commission_bps_round_turn"]
        if sp is None or m is None:
            continue
        adj[s] = {"class": v["class"], "spread_bps_typical": sp,
                  "rollover_multiplier": m, "spread_bps_at_close": sp * m,
                  "commission_bps": cm,
                  "roundtrip_typical": (sp + cm) if cm is not None else None,
                  "roundtrip_at_close": (sp * m + cm) if cm is not None else None}

    # re-price the headline cells: cost scales with the spread share of round-trip cost
    cells = {}
    src = json.load(open(os.path.join(OUT, "B5_COSTVOL_AND_KILLS_V1.json")))["cells"]
    xs = {}
    for f in os.listdir(os.path.join(OUT, "xs_cells")):
        d = json.load(open(os.path.join(OUT, "xs_cells", f)))
        for sig, c in d.get("cells", {}).items():
            xs[f"{d['universe']}|{sig}"] = (c, d["symbols"])
    for name, (c, syms) in xs.items():
        if c.get("net_mean_volnorm") is None:
            continue
        g = c["gross_mean_volnorm"]
        cost_typ = abs(g - c["net_mean_volnorm"])
        rows = [adj[s] for s in syms if s in adj and adj[s]["roundtrip_typical"]]
        if not rows:
            continue
        infl = (sum(r["roundtrip_at_close"] for r in rows) / sum(r["roundtrip_typical"] for r in rows))
        cells[name] = {
            "gross_edge": abs(g), "cost_typical_hour": cost_typ,
            "cost_inflation_at_rollover": infl,
            "cost_at_rollover": cost_typ * infl,
            "net_typical_hour": abs(g) - cost_typ,
            "net_at_rollover": abs(g) - cost_typ * infl,
            "cost_over_edge_typical": cost_typ / abs(g),
            "cost_over_edge_at_rollover": cost_typ * infl / abs(g),
            "turnover": c["turnover"],
        }

    res = {"per_symbol_tick_ratios": ratios, "class_multipliers": class_mult,
           "note": "D1 bars close at broker server midnight (America/New_York + 7h), so a daily "
                   "close-to-close strategy transacts AT the rollover. Spread component only is "
                   "inflated; commission is hour-invariant. Equity CFDs are assumed 1.0 because "
                   "the venue is shut at broker hour 00 -- an assumption, not a measurement.",
           "adjusted_symbols": adj, "cells": cells}
    json.dump(res, open(os.path.join(OUT, "B5_ROLLOVER_COST_V1.json"), "w"), indent=1)

    print("per-symbol rollover multipliers (tick-measured):")
    for s, r in sorted(ratios.items()):
        print(f"  {s:12s} {r['class']:10s} hour{r['hour_used']:02d} {r['spread_at_close_hour_bps']:8.3f} bps "
              f"vs median {r['median_hour_spread_bps']:7.3f}  = {r['rollover_multiplier']:6.2f}x")
    print("class multipliers:", {k: round(v, 2) for k, v in class_mult.items()})
    print()
    print(f"{'cell':40s} {'edge':>8s} {'cost_typ':>9s} {'cost_roll':>10s} {'net_typ':>9s} {'net_roll':>9s} {'c/e roll':>9s}")
    for n, v in sorted(cells.items(), key=lambda kv: -kv[1]["net_at_rollover"]):
        print(f"{n:40s} {v['gross_edge']:8.4f} {v['cost_typical_hour']:9.4f} {v['cost_at_rollover']:10.4f} "
              f"{v['net_typical_hour']:+9.4f} {v['net_at_rollover']:+9.4f} {v['cost_over_edge_at_rollover']:9.2f}")


if __name__ == "__main__":
    main()
