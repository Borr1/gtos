#!/usr/bin/env python3
"""h5 step 4 — PRE-DECLARED rules, the instrument affordability table, and the GER40 dossier.

Every rule below is declared in this file BEFORE it is read, and each is labelled with the
basis it was chosen on:
    COST     chosen from broker-true cost alone (never from an outcome) -> no selection bill
    SWARM    the lead the 29-agent swarm already published (GER40) -> 1-of-24 bill, known
    HUNT     came out of h5's own 4,130-cell grid -> carries the full multiplicity bill
For each: n, trades/day, gross, cost, net, ratio (R and bps), iid and day-clustered t,
days positive, and the month-by-month read with January separated from the Feb+Mar holdout.

out: h5_RULES_V1.json
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402

rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_V1.jsonl.gz"), "rt") if x.strip()]
BOOK = h5_lib.cell_stats(rows)
OUT = {"book": BOOK}

# ---------------------------------------------------------------- symbol table
per = []
for sym in sorted({r["symbol"] for r in rows}):
    rs = [r for r in rows if r["symbol"] == sym]
    st = h5_lib.cell_stats(rs)
    rdp = sorted(r["rdp"] for r in rs)
    sp = sorted(r["real_spread_r"] * r["rdp"] * 1e4 for r in rs)
    ct = sorted(r["cost_true"] * r["rdp"] * 1e4 for r in rs)
    per.append({"symbol": sym, "n": st["n"],
                "median_stop_bps": round(rdp[len(rdp) // 2] * 1e4, 2),
                "median_spread_bps": round(sp[len(sp) // 2], 4),
                "median_cost_bps": round(ct[len(ct) // 2], 4),
                "gross_R": st["gross_R"], "cost_R": st["cost_R"], "net_R": st["net_R"],
                "ratio_R": st["ratio_R"], "ratio_bps": st["ratio_bps"],
                "t_net": st["t_net"], "t_net_day": st["t_net_day"],
                "days_net_pos": st["days_net_pos"], "days": st["days"],
                "jan": st["m_2026-01"]["ratio_R"], "feb": st["m_2026-02"]["ratio_R"],
                "mar": st["m_2026-03"]["ratio_R"],
                "jan_net": st["m_2026-01"]["net_R"], "feb_net": st["m_2026-02"]["net_R"],
                "mar_net": st["m_2026-03"]["net_R"]})
per.sort(key=lambda r: -(r["ratio_R"] or 0))
OUT["per_symbol"] = per

CHEAP6 = [p["symbol"] for p in sorted(per, key=lambda r: r["median_cost_bps"])[:6]]
CHEAPR6 = [p["symbol"] for p in sorted(per, key=lambda r: r["cost_R"])[:6]]
OUT["cheapest_6_by_median_cost_bps"] = CHEAP6
OUT["cheapest_6_by_mean_cost_R"] = CHEAPR6
INDEX = ["GER40", "US30_cash", "NAS100", "UK100", "SPX500", "JP225"]

SURV12 = [("hour", "cost_dec", "14", "0"), ("family", "cost_dec", "regime_transition_break", "0"),
          ("symbol", "hour", "GER40", "8"), ("symbol", "hour", "GER40", "14"),
          ("rdp_dec", "cost_dec", "4", "1"), ("symbol", "hour", "NAS100", "16"),
          ("symbol", "family", "GER40", "structural_distance_extreme"),
          ("symbol", "rv_q", "GER40", "2"), ("symbol", "rdp_dec", "UK100", "4"),
          ("symbol", "cost_dec", "UK100", "3"), ("hour", "rdp_dec", "20", "9"),
          ("symbol", "hour", "UK100", "15")]


def in_surv12(r):
    for a, b, va, vb in SURV12:
        if str(r.get(a)) == va and str(r.get(b)) == vb:
            return True
    return False


RULES = [
    ("R1_GER40_only", "SWARM", lambda r: r["symbol"] == "GER40"),
    ("R2_index_cluster_6", "COST", lambda r: r["symbol"] in INDEX),
    ("R3_cost_le_breakeven_0.0383", "COST", lambda r: r["cost_true"] <= 0.038342),
    ("R4_cost_le_0.0075", "COST", lambda r: r["cost_true"] <= 0.0075),
    ("R4b_cost_le_0.0125", "COST", lambda r: r["cost_true"] <= 0.0125),
    ("R5_cost_le_0.02", "COST", lambda r: r["cost_true"] <= 0.02),
    ("R6_cheapest6_by_bps", "COST", lambda r: r["symbol"] in CHEAP6),
    ("R7_cheapest6_by_costR", "COST", lambda r: r["symbol"] in CHEAPR6),
    ("R8_index_AND_cost_le_be", "COST", lambda r: r["symbol"] in INDEX and r["cost_true"] <= 0.038342),
    ("R9_GER40_hours_8_14", "HUNT", lambda r: r["symbol"] == "GER40" and r["hour"] in (8, 14)),
    ("R10_regime_break_costdec0", "HUNT", lambda r: r["family"] == "regime_transition_break" and r["cost_dec"] == 0),
    ("R11_union_of_12_survivors", "HUNT", in_surv12),
    ("R12_index_cluster_cost_le_0.02", "COST", lambda r: r["symbol"] in INDEX and r["cost_true"] <= 0.02),
]


def read(rs, label, basis):
    if len(rs) < 20:
        return None
    st = h5_lib.cell_stats(rs)
    hold = [r for r in rs if r["month"] != "2026-01"]
    sh = h5_lib.cell_stats(hold) if len(hold) >= 20 else None
    return {"rule": label, "basis": basis, "n": st["n"],
            "share_of_book": round(st["n"] / len(rows), 4),
            "trades_per_active_day": round(st["n"] / st["days"], 2),
            "trades_per_calendar_day": round(st["n"] / 63.0, 2),
            "gross_R": st["gross_R"], "cost_R": st["cost_R"], "net_R": st["net_R"],
            "ratio_R": st["ratio_R"], "ratio_bps": st["ratio_bps"],
            "edge_bps": st["edge_bps"], "toll_bps": st["toll_bps"],
            "t_gross": st["t_gross"], "t_net": st["t_net"], "t_net_day": st["t_net_day"],
            "days": st["days"], "days_net_pos": st["days_net_pos"],
            "net_R_per_calendar_day": round(st["net_R"] * st["n"] / 63.0, 5),
            "n_symbols": st["n_symbols"],
            "jan": st["m_2026-01"], "feb": st["m_2026-02"], "mar": st["m_2026-03"],
            "FEB_MAR_holdout": (None if sh is None else
                                {"n": sh["n"], "gross_R": sh["gross_R"], "cost_R": sh["cost_R"],
                                 "net_R": sh["net_R"], "ratio_R": sh["ratio_R"],
                                 "t_net": sh["t_net"], "t_net_day": sh["t_net_day"],
                                 "days": sh["days"], "days_net_pos": sh["days_net_pos"]})}


res = []
for label, basis, fn in RULES:
    res.append(read([r for r in rows if fn(r)], label, basis))
OUT["rules"] = [r for r in res if r]

# ------------------------------------------------------------- GER40 dossier
g = [r for r in rows if r["symbol"] == "GER40"]
DOS = {"n": len(g), "whole": h5_lib.cell_stats(g)}
for ax in ("hour", "family", "session", "side", "dow", "rv_q", "rdp_dec", "month"):
    d = {}
    for r in g:
        d.setdefault(str(r.get(ax)), []).append(r)
    DOS["by_" + ax] = sorted(
        [{"cell": k, "n": len(v), **{kk: h5_lib.cell_stats(v)[kk] for kk in
                                     ("gross_R", "cost_R", "net_R", "ratio_R", "t_net", "t_net_day")}}
         for k, v in d.items() if len(v) >= 20], key=lambda r: -r["n"])
# concentration: how much of GER40's total net R comes from its best day / best 5 days
byday = {}
for r in g:
    byday.setdefault(r["day"], 0.0)
    byday[r["day"]] += r[h5_lib.GROSS] - r[h5_lib.COST]
tot = sum(byday.values())
ds = sorted(byday.values(), reverse=True)
DOS["net_R_total"] = round(tot, 4)
DOS["best_day_share"] = round(ds[0] / tot, 4) if tot else None
DOS["best5_day_share"] = round(sum(ds[:5]) / tot, 4) if tot else None
DOS["days_positive"] = sum(1 for v in byday.values() if v > 0)
DOS["days"] = len(byday)
# equity curve by day, and max drawdown in R
eq, peak, mdd = 0.0, 0.0, 0.0
curve = []
for d in sorted(byday):
    eq += byday[d]
    peak = max(peak, eq)
    mdd = min(mdd, eq - peak)
    curve.append([d, round(eq, 4)])
DOS["equity_curve_R"] = curve
DOS["max_drawdown_R"] = round(mdd, 4)
OUT["GER40_dossier"] = DOS

json.dump(OUT, open(os.path.join(D, "h5_RULES_V1.json"), "w"), indent=1)

print("%-12s %6s %10s %10s %10s %8s %8s %8s %7s %7s %6s   jan/feb/mar ratio" %
      ("symbol", "n", "stop_bps", "cost_bps", "cost_R", "gross_R", "net_R", "ratio_R", "rat_bps", "t_day", "d+/d"))
for p in per:
    print("%-12s %6d %10.2f %10.4f %10.5f %8.5f %+8.5f %8.3f %7.3f %7.2f %3d/%d   %.2f/%.2f/%.2f" %
          (p["symbol"], p["n"], p["median_stop_bps"], p["median_cost_bps"], p["cost_R"],
           p["gross_R"], p["net_R"], p["ratio_R"], p["ratio_bps"] or 0, p["t_net_day"] or 0,
           p["days_net_pos"], p["days"], p["jan"] or 0, p["feb"] or 0, p["mar"] or 0))
print("\ncheapest 6 by median cost bps:", CHEAP6)
print("cheapest 6 by mean cost R    :", CHEAPR6)
print("\n%-30s %-6s %6s %6s %9s %9s %10s %7s %7s %7s %6s  hold_net hold_t" %
      ("rule", "basis", "n", "t/day", "gross", "cost", "net", "ratio", "t_net", "t_day", "d+/d"))
for r in OUT["rules"]:
    h = r["FEB_MAR_holdout"] or {}
    print("%-30s %-6s %6d %6.2f %9.5f %9.5f %+10.5f %7.3f %7.2f %7.2f %3d/%d  %+8.5f %6.2f" %
          (r["rule"], r["basis"], r["n"], r["trades_per_calendar_day"], r["gross_R"], r["cost_R"],
           r["net_R"], r["ratio_R"] or 0, r["t_net"] or 0, r["t_net_day"] or 0,
           r["days_net_pos"], r["days"], h.get("net_R") or 0, h.get("t_net_day") or 0))
print("\nGER40: net_R total %.3f  best-day share %.3f  best-5 share %.3f  days+ %d/%d  maxDD %.2f R"
      % (DOS["net_R_total"], DOS["best_day_share"], DOS["best5_day_share"],
         DOS["days_positive"], DOS["days"], DOS["max_drawdown_R"]))
