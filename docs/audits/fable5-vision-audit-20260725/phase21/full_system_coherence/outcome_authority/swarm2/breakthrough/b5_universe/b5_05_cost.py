"""B5 step (e) — per-symbol round-trip cost on the expanded universe, in bps of notional.

Built ONLY from artifacts already on disk:
  BROKER_TRUE_COSTS_V1_1.json  (the estate's own broker-truth layer; tick-measured spread for
                                36 FTMO symbols, measured/transferred commission, swap)
  ftmo_symbols_get.jsonl       (MT5 symbol_info at the 2026-07-25 export: spread in POINTS,
                                point, bid/ask, contract size, swap)

Conventions match the cost layer's own (`conventions` block of BROKER_TRUE_COSTS):
  spread     = ONE bid/ask crossing per round trip, in price units -> bps of mid
  commission = round turn, either USD/lot or bp of notional -> bps of notional
  swap       = broker points per night (mode 1) or annual pct (modes 5/6) -> bps/night

Coverage is reported, never imputed silently.  Equity CFD commission is UNKNOWN on this
account (`"no deal rows for this symbol and no measured peer in its class; commission is
UNKNOWN, not zero"`) and is carried as null, not as zero.

Writes <OUT>/B5_SYMBOL_COST_V1.json.  Runtime ~2 s.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "b5_receipts")
REPO = "/Users/borr/GTOSActive/worktrees/claude-opus5-architecture-audit-20260725"
EXP = "/Users/borr/GTOSActive/vps-export-20260725/extracted/09_mt5_api"
COSTS = os.path.join(REPO, "research/operations/broker_truth_layer_2026_07_29/BROKER_TRUE_COSTS_V1_1.json")


def norm(s):
    k = s.upper()
    for suf in (".CASH", "_CASH", ".C", "_C"):
        if k.endswith(suf):
            k = k[: -len(suf)]
            break
    return k.replace(".", "").replace("_", "")


def main():
    trade = json.load(open(os.path.join(OUT, "B5_TRADEABILITY_V1.json")))["symbols"]
    costs = json.load(open(COSTS))
    cft = {norm(k): v for k, v in costs["accounts"]["FTMO"]["instruments"].items()}
    sg = {}
    for line in open(os.path.join(EXP, "ftmo_symbols_get.jsonl")):
        line = line.strip()
        if line:
            d = json.loads(line)
            sg[norm(d["name"])] = d

    rows = {}
    for s, tv in trade.items():
        k = norm(s)
        c = cft.get(k) or {}
        g = sg.get(k) or {}
        bid, ask = g.get("bid"), g.get("ask")
        mid = 0.5 * (bid + ask) if (bid and ask) else None
        spec = c.get("spec") or {}
        contract = spec.get("trade_contract_size") or g.get("trade_contract_size")

        # ---- spread, two independent instruments
        sp = c.get("spread_price")
        spread_bps_tick = None
        if sp and sp.get("mid_price_median"):
            spread_bps_tick = sp["percentiles"]["p50"] / sp["mid_price_median"] * 1e4
        spread_bps_snap = None
        if mid and g.get("spread") is not None and g.get("point"):
            spread_bps_snap = g["spread"] * g["point"] / mid * 1e4
        spread_bps = spread_bps_tick if spread_bps_tick is not None else spread_bps_snap
        spread_src = "tick_p50_MEASURED" if spread_bps_tick is not None else (
            "symbol_info_snapshot_2026-07-25" if spread_bps_snap is not None else None)

        # ---- commission, round turn -> bps of notional
        com = c.get("commission") or {}
        kind, val, cov = com.get("kind"), com.get("value"), com.get("coverage")
        commission_bps = None
        if kind == "notional_bp" and val is not None:
            commission_bps = float(val)
        elif kind == "per_lot" and val is not None and mid and contract:
            commission_bps = float(val) / (contract * mid) * 1e4
        elif kind == "zero":
            commission_bps = 0.0

        rt = None
        if spread_bps is not None and commission_bps is not None:
            rt = spread_bps + commission_bps

        # ---- carry, bps/night (mode 1 = points; mode 5/6 = annual pct)
        def carry_bps(points, mode):
            if points is None or mode is None or not mid:
                return None
            if mode == 1:
                pt = spec.get("point") or g.get("point")
                return None if not pt else points * pt / mid * 1e4
            if mode in (5, 6):
                return points / 100.0 / 360.0 * 1e4
            return None

        mode = spec.get("swap_mode") or g.get("swap_mode")
        rows[s] = {
            "class": tv["class"], "status": tv["status"],
            "ftmo_listed": tv["ftmo_listed"], "redacted_account_listed": tv["redacted_account_listed"],
            "gtos_configured": tv["ftmo_instrument_config"] or tv["redacted_account_instrument_config"],
            "cost_layer_class": c.get("instrument_class"),
            "mid_snapshot": mid,
            "spread_bps": spread_bps, "spread_source": spread_src,
            "spread_bps_tick_measured": spread_bps_tick, "spread_bps_snapshot": spread_bps_snap,
            "commission_bps_round_turn": commission_bps,
            "commission_coverage": cov, "commission_kind": kind,
            "roundtrip_cost_bps": rt,
            "roundtrip_cost_known": rt is not None,
            "swap_mode": mode,
            "carry_long_bps_per_night": carry_bps(spec.get("swap_long"), mode),
            "carry_short_bps_per_night": carry_bps(spec.get("swap_short"), mode),
            "trade_stops_level": (sg.get(k) or {}).get("trade_stops_level"),
            "volume_min": (sg.get(k) or {}).get("volume_min"),
        }

    # ---- rollups: how many symbols clear a hurdle at each cost level
    from collections import Counter, defaultdict
    import statistics as st
    known = {s: v for s, v in rows.items() if v["roundtrip_cost_known"]}
    unknown = sorted(s for s, v in rows.items() if not v["roundtrip_cost_known"])
    by_class = defaultdict(list)
    for s, v in known.items():
        by_class[v["class"]].append(v["roundtrip_cost_bps"])
    ladder = {}
    for thr in (0.5, 1.0, 2.0, 3.0, 5.0, 10.0, 20.0, 50.0):
        ladder[str(thr)] = {
            "n_symbols_at_or_below": sum(1 for v in known.values() if v["roundtrip_cost_bps"] <= thr),
            "n_tradeable_now_at_or_below": sum(1 for v in known.values()
                                               if v["roundtrip_cost_bps"] <= thr and v["gtos_configured"]),
            "by_class": {c: sum(1 for x in xs if x <= thr) for c, xs in by_class.items()},
        }
    roll = {
        "n_symbols": len(rows),
        "n_roundtrip_cost_known": len(known),
        "n_roundtrip_cost_unknown": len(unknown),
        "unknown_symbols": unknown,
        "unknown_reason": "FTMO equity CFD commission is MODELLED/unknown in the estate's own cost layer "
                          "(no deal rows, no measured peer in class) — carried as null, never as zero",
        "spread_coverage": dict(Counter(v["spread_source"] for v in rows.values())),
        "commission_coverage": dict(Counter(v["commission_coverage"] for v in rows.values())),
        "roundtrip_bps_by_class": {c: {"n": len(xs), "median": st.median(xs), "min": min(xs), "max": max(xs)}
                                   for c, xs in sorted(by_class.items())},
        "cost_ladder": ladder,
        "sources": {"broker_true_costs": COSTS, "symbols_get": os.path.join(EXP, "ftmo_symbols_get.jsonl")},
        "caveat_hour": "spread_bps is a p50 over the 2026-06-18..07-26 tick window or a single snapshot; "
                       "Lane 5 measured a 17.6x (cache) / 56.8x (tick, EURUSD) hour-of-day range, so this "
                       "is a typical-hour figure and NOT an upper bound",
    }
    json.dump({"rollup": roll, "symbols": rows}, open(os.path.join(OUT, "B5_SYMBOL_COST_V1.json"), "w"),
              indent=1, sort_keys=True)
    print(json.dumps({k: v for k, v in roll.items() if k not in ("unknown_symbols", "sources")}, indent=1))


if __name__ == "__main__":
    main()
