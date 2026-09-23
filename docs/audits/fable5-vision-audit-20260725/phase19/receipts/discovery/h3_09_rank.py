"""h3-09 -- rank every toll lever by bps recovered per unit of opportunity lost, and price
the composite JOINTLY (item 6).

A lever is scored against ONE baseline: the synthesis headline arm -- at-market entry
delayed 5 minutes, 0.25R trailing exit, all 24 instruments, all hours, broker-true cost,
43,755 live-expressible opportunities, toll 2.4571 bps, edge 0.2312 bps, e/t 0.0941.

For each lever:
    keep_rate         share of the 43,755 opportunities that survive
    d_toll_bps        toll saved per surviving TRADE (positive = cheaper)
    d_edge_bps        edge change per surviving trade (positive = better)
    efficiency        d_toll_bps / (1 - keep_rate)   -- bps of toll bought per unit of
                      opportunity surrendered. Infinite when nothing is surrendered.
    net_bps_per_opp   the only number that composes: net bps per ORIGINAL opportunity.

The composite is measured, never summed: e-stack proved a naive sum over this estate's
levers over-counts by 66.8 %.
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

C = "TRAIL025"
pas = []
for mm in ("202601", "202602", "202603"):
    for line in gzip.open(os.path.join(D, f"H3_PASSIVE_ROWS_{mm}.jsonl.gz"), "rt"):
        if line.strip():
            pas.append(json.loads(line))
PJ = {(r["cid"], r["dt"]): r for r in pas}
rows = H.load_atmkt()
H.add_hour_cost(rows)
for r in rows:
    p = PJ.get((r["cid"], r["dt"]))
    r["j0"] = p.get("u000_j0") if p else None
    r["pas_r"] = p.get("u000_j0_" + C) if p else None
    r["spread_ratio"] = (r["spread_bps_hour"] / H.TICK["ftmo:" + H.e_lib.TMAP.get(r["symbol"], r["symbol"])]["spread_bps_median"]) if r.get("spread_bps_hour") else None
N = len(rows)

TOLL_MKT = lambda r: r["cost_true"]                                             # noqa: E731
TOLL_MKT_H = lambda r: r["cost_true_hour"]                                      # noqa: E731
TOLL_PAS = lambda r: 0.5 * r["real_spread_r"] + r["real_comm_r"]                # noqa: E731

# per-symbol ex-ante cost order (deterministic: rank Spearman 0.994-0.999 across months)
sy = {}
for r in rows:
    sy.setdefault(r["symbol"], []).append(r)
symcost = sorted(sy, key=lambda s: H.mean([x["cost_true"] * x["rdp"] * 1e4 for x in sy[s]]))
hr = {}
for r in rows:
    hr.setdefault(r["ny_hour"], []).append(r)
hourcost = sorted(hr, key=lambda h: H.mean([x["cost_true_hour"] * x["rdp"] * 1e4 for x in hr[h]]))


def arm(sel, valf, tollf, label, extra=None):
    g, t, n, keep = [], [], [], []
    for r in rows:
        if not sel(r):
            continue
        v = valf(r)
        if v is None or tollf(r) is None:
            continue
        gb = v * r["rdp"] * 1e4
        tb = tollf(r) * r["rdp"] * 1e4
        g.append(gb); t.append(tb); n.append(gb - tb); keep.append(r)
    if len(g) < 10:
        return None
    d = {"label": label, "n": len(g), "keep_rate": len(g) / N,
         "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t) if H.mean(t) else None,
         "net_bps_per_opportunity": H.mean(n) * len(g) / N,
         "net_r": H.mean([valf(r) - tollf(r) for r in keep]),
         "net_r_per_opportunity": H.mean([valf(r) - tollf(r) for r in keep]) * len(g) / N,
         "t_net_trade": H.tstat(n), "t_gross_trade": H.tstat(g)}
    bm = {}
    for m in sorted(H.MONTHS):
        k2 = [r for r in keep if r["month"] == m]
        if len(k2) >= 20:
            gg = [valf(r) * r["rdp"] * 1e4 for r in k2]
            tt = [tollf(r) * r["rdp"] * 1e4 for r in k2]
            bm[m] = {"n": len(k2), "edge_bps": H.mean(gg), "toll_bps": H.mean(tt),
                     "net_bps": H.mean(gg) - H.mean(tt),
                     "edge_over_toll": H.mean(gg) / H.mean(tt) if H.mean(tt) else None}
    d["by_month"] = bm
    d["months_e_over_t_ge_1"] = sum(1 for v in bm.values()
                                    if v["edge_over_toll"] and v["edge_over_toll"] >= 1)
    d["months_measured"] = len(bm)
    if extra:
        d.update(extra)
    return d


BASE = arm(lambda r: True, lambda r: r["K5_" + C], TOLL_MKT, "BASELINE headline arm")
out = {"lane": "h3", "step": "rank", "n_opportunities": N, "baseline": BASE,
       "symbol_cost_order_exante": symcost, "hour_cost_order_exante": hourcost}

levers = []


def rec(d, family, mechanism, live_today):
    if d is None:
        return
    d["lever_family"] = family
    d["mechanism"] = mechanism
    d["live_implementable_today"] = live_today
    d["d_toll_bps"] = BASE["toll_bps"] - d["toll_bps"]
    d["d_edge_bps"] = d["edge_bps"] - BASE["edge_bps"]
    d["d_net_bps"] = d["net_bps"] - BASE["net_bps"]
    d["d_net_bps_per_opportunity"] = d["net_bps_per_opportunity"] - BASE["net_bps_per_opportunity"]
    lost = 1.0 - d["keep_rate"]
    d["opportunity_lost"] = lost
    d["efficiency_toll_bps_per_opportunity_lost"] = (d["d_toll_bps"] / lost) if lost > 1e-9 else None
    levers.append(d)


# ------------------------------------------------------------------ toll levers
for k in (1, 2, 3, 4, 6, 8, 12, 18, 24):
    ks = set(symcost[:k])
    rec(arm(lambda r, ks=ks: r["symbol"] in ks, lambda r: r["K5_" + C], TOLL_MKT,
            f"INSTRUMENT: keep {k} cheapest instruments (ex ante)",
            extra={"k": k, "kept": symcost[:k]}),
        "instrument", "drop instruments whose broker-true toll is high", True)

for th in (1.2, 1.5, 2.0, 3.0, 5.0):
    rec(arm(lambda r, th=th: r["spread_ratio"] is not None and r["spread_ratio"] <= th,
            lambda r: r["K5_" + C], TOLL_MKT_H,
            f"HOUR: refuse when quoted spread > {th}x the symbol's own median (ex ante)",
            extra={"threshold": th}),
        "hour", "within-symbol hour spread ratio, deterministic from the tick archive", True)

for k in (2, 4, 6, 8, 12, 18, 24):
    ks = set(hourcost[:k])
    rec(arm(lambda r, ks=ks: r["ny_hour"] in ks, lambda r: r["K5_" + C], TOLL_MKT_H,
            f"HOUR: keep {k} cheapest NY hours (ex ante)", extra={"k": k, "kept": sorted(ks)}),
        "hour", "pooled hour cost ranking", True)

rec(arm(lambda r: r["ny_hour"] != 17, lambda r: r["K5_" + C], TOLL_MKT_H,
        "HOUR: drop the rollover hour (NY 17) only"),
    "hour", "one hour, the broker daily rollover", True)

rec(arm(lambda r: r["pas_r"] is not None, lambda r: r["pas_r"], TOLL_PAS,
        "PASSIVE ENTRY: resting limit at the decision price, take first touch"),
    "entry", "stop crossing the spread on entry; needs TRADE_ACTION_PENDING", False)

for c in (5, 10, 15):
    rec(arm(lambda r, c=c: r["j0"] is not None and r["j0"] >= c, lambda r: r["pas_r"], TOLL_PAS,
            f"PASSIVE ENTRY + NO-RETRACE >= {c} min", extra={"cond_min": c}),
        "entry", "passive fill AND a momentum filter", False)
    rec(arm(lambda r, c=c: r["j0"] is not None and r["j0"] >= c, lambda r: r["pas_r"], TOLL_MKT,
            f"NO-RETRACE >= {c} min, entry at market on the touch", extra={"cond_min": c}),
        "entry", "same filter, market order on the touch -- pays the full spread", True)

# ------------------------------------------------------------ zero-toll (edge) levers
for k in (0, 2, 10, 20, 30):
    rec(arm(lambda r: True, lambda r, k=k: r[f"K{k}_" + C], TOLL_MKT,
            f"DELAY: at-market entry at minute {k}", extra={"delay_min": k}),
        "entry_timing", "pure edge lever -- toll is identical at every delay", True)

for cc in ("INC", "STOPONLY", "T3S1", "TS90S1"):
    rec(arm(lambda r: True, lambda r, cc=cc: r["K5_" + cc], TOLL_MKT,
            f"EXIT CONTRACT: {cc} instead of TRAIL025"),
        "exit", "pure edge lever -- one round trip is charged whatever the exit", True)

# stop widening, stated as the identity it is
rec(arm(lambda r: True, lambda r: r["K5_" + C], TOLL_MKT,
        "STOP WIDTH: any widening factor (toll_bps is invariant BY IDENTITY)"),
    "stop_width", "cost_r = cost_price/risk_distance; widening moves the denominator only",
    True)

# swap
rec(arm(lambda r: True, lambda r: r["K5_" + C], TOLL_MKT,
        "SWAP: avoid the rollover (broker-true swap already 0 on a 2 h horizon)"),
    "swap", "0.83 % of trades can even reach a rollover; broker-true swap charged is 0.0 bps",
    True)

out["levers"] = levers

# ------------------------------------------------------------------- COMPOSITES
comp = []
CH2, CH3, CH6 = set(symcost[:2]), set(symcost[:3]), set(symcost[:6])
specs = [
    ("A. instruments(2)", lambda r: r["symbol"] in CH2, lambda r: r["K5_" + C], TOLL_MKT, True),
    ("B. instruments(2) + drop NY17", lambda r: r["symbol"] in CH2 and r["ny_hour"] != 17,
     lambda r: r["K5_" + C], TOLL_MKT_H, True),
    ("C. instruments(2) + delay 20", lambda r: r["symbol"] in CH2, lambda r: r["K20_" + C], TOLL_MKT, True),
    ("D. instruments(3) + delay 20", lambda r: r["symbol"] in CH3, lambda r: r["K20_" + C], TOLL_MKT, True),
    ("E. instruments(6) + delay 20", lambda r: r["symbol"] in CH6, lambda r: r["K20_" + C], TOLL_MKT, True),
    ("F. instruments(2) + delay 20 + drop NY17",
     lambda r: r["symbol"] in CH2 and r["ny_hour"] != 17, lambda r: r["K20_" + C], TOLL_MKT_H, True),
    ("G. no-retrace>=10 + market on touch, all instruments",
     lambda r: r["j0"] is not None and r["j0"] >= 10, lambda r: r["pas_r"], TOLL_MKT, True),
    ("H. no-retrace>=10 + market on touch + instruments(6)",
     lambda r: r["j0"] is not None and r["j0"] >= 10 and r["symbol"] in CH6,
     lambda r: r["pas_r"], TOLL_MKT, True),
    ("I. PASSIVE no-retrace>=10, all instruments",
     lambda r: r["j0"] is not None and r["j0"] >= 10, lambda r: r["pas_r"], TOLL_PAS, False),
    ("J. PASSIVE no-retrace>=10 + instruments(6)",
     lambda r: r["j0"] is not None and r["j0"] >= 10 and r["symbol"] in CH6,
     lambda r: r["pas_r"], TOLL_PAS, False),
    ("K. PASSIVE no-retrace>=10 + instruments(12)",
     lambda r: r["j0"] is not None and r["j0"] >= 10 and r["symbol"] in set(symcost[:12]),
     lambda r: r["pas_r"], TOLL_PAS, False),
]
for lab, sel, vf, tf, live in specs:
    d = arm(sel, vf, tf, lab)
    if d:
        d["live_implementable_today"] = live
        comp.append(d)
out["composites"] = comp

# ---- the theoretical floor: what if the whole toll were removed except commission
floor = arm(lambda r: True, lambda r: r["K5_" + C], lambda r: r["real_comm_r"],
            "FLOOR: commission only (zero spread, zero slippage -- unattainable)")
out["theoretical_floor_commission_only"] = floor
out["answer_to_the_lane_question"] = {
    "toll_bps_now": BASE["toll_bps"],
    "toll_bps_if_entry_leg_passive": BASE["toll_bps"] - (
        H.mean([(0.5 * r["real_spread_r"] + r["real_slip_r"]) * r["rdp"] * 1e4 for r in rows])),
    "toll_bps_if_both_legs_passive_and_no_slippage": H.mean(
        [r["real_comm_r"] * r["rdp"] * 1e4 for r in rows]),
    "max_removable_pct": 1 - H.mean([r["real_comm_r"] * r["rdp"] * 1e4 for r in rows]) / BASE["toll_bps"],
    "max_reduction_factor": BASE["toll_bps"] / H.mean([r["real_comm_r"] * r["rdp"] * 1e4 for r in rows]),
    "reduction_factor_required_to_pay_at_current_edge": BASE["toll_bps"] / BASE["edge_bps"],
    "edge_over_toll_at_the_absolute_floor": BASE["edge_bps"] / H.mean(
        [r["real_comm_r"] * r["rdp"] * 1e4 for r in rows]),
}

p = H.dump(out, "H3_RANK_V1.json")
print("BASELINE edge=%.4f toll=%.4f net=%.4f e/t=%.4f"
      % (BASE["edge_bps"], BASE["toll_bps"], BASE["net_bps"], BASE["edge_over_toll"]))
print("\nANSWER", json.dumps(out["answer_to_the_lane_question"], indent=1))
print("\n%-62s %6s %6s %8s %8s %7s %9s %9s %4s %s" %
      ("lever", "n", "keep", "d_toll", "d_edge", "e/t", "net/opp", "eff", "m>=1", "live"))
for d in sorted(levers, key=lambda x: -x["net_bps_per_opportunity"]):
    print("%-62s %6d %6.3f %+8.4f %+8.4f %7.3f %+9.5f %9s %2d/%d %s" %
          (d["label"][:62], d["n"], d["keep_rate"], d["d_toll_bps"], d["d_edge_bps"],
           d["edge_over_toll"] or 0, d["net_bps_per_opportunity"],
           ("%.4f" % d["efficiency_toll_bps_per_opportunity_lost"])
           if d["efficiency_toll_bps_per_opportunity_lost"] is not None else "inf",
           d["months_e_over_t_ge_1"], d["months_measured"],
           "YES" if d["live_implementable_today"] else "no"))
print("\nCOMPOSITES")
print("%-52s %6s %6s %8s %8s %8s %7s %10s %4s %s" %
      ("arm", "n", "keep", "edge", "toll", "net", "e/t", "net/opp", "m>=1", "live"))
for d in comp:
    print("%-52s %6d %6.3f %8.4f %8.4f %8.4f %7.3f %+10.5f %2d/%d %s" %
          (d["label"][:52], d["n"], d["keep_rate"], d["edge_bps"], d["toll_bps"],
           d["net_bps"], d["edge_over_toll"], d["net_bps_per_opportunity"],
           d["months_e_over_t_ge_1"], d["months_measured"],
           "YES" if d["live_implementable_today"] else "no"))
print("->", p)
