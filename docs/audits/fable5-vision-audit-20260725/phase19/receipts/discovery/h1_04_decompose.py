"""h1-04 -- term dominance, the bps-vs-R disagreement, the affordability sweep, and the
cost of ENTRY TIMING (at-market vs resting limit vs delayed vs first-minute cancel).

Everything here is the whole population; nothing is sampled.
"""
from __future__ import annotations

import gzip
import json
import math
import os
import statistics as st
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone

D = os.path.dirname(os.path.abspath(__file__))
ROOT = "/Users/borr/GTOSActive/worktrees/wave19-broad-forensic-20260801"
sys.path.insert(0, ROOT)
sys.path.insert(0, D)
from src.utils.broker_clock import resolve_rule, utc_to_broker_naive  # noqa: E402
import h1_01_cost_rows as H1  # noqa: E402

SERVER = resolve_rule("FTMO-Server3")
OUT = f"{D}/H1_DECOMP_V1.json"
EDGE = "K5_TRAIL025"
KS = [0, 1, 2, 3, 5, 10, 15, 20, 30, 45, 60]


def mean(v):
    return sum(v) / len(v) if v else None


def se(v):
    n = len(v)
    if n < 2:
        return None
    m = sum(v) / n
    return math.sqrt(sum((x - m) ** 2 for x in v) / (n - 1) / n)


def spearman(pairs):
    if len(pairs) < 3:
        return None
    def ranks(xs):
        o = sorted(range(len(xs)), key=lambda i: xs[i])
        rk = [0.0] * len(xs)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]:
                j += 1
            a = (i + j) / 2.0 + 1
            for t in range(i, j + 1):
                rk[o[t]] = a
            i = j + 1
        return rk
    a, b = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    ma, mb = mean(a), mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return num / (da * db) if da and db else None


rows = [json.loads(l) for l in gzip.open(f"{D}/h1_COST_ROWS_V1.jsonl.gz", "rt") if l.strip()]
res = {"n_rows": len(rows)}

# ------------------------------------------------------------------ 1. term dominance
def term_block(v):
    return {
        "n": len(v),
        "bps": {t: mean([r[f"{k}_bps"] for r in v]) for t, k in
                (("spread", "spread"), ("commission", "comm"), ("slippage", "slip"),
                 ("swap", "swap"))},
        "R": {t: mean([r[f"{k}_r"] for r in v]) for t, k in
              (("spread", "spread"), ("commission", "comm"), ("slippage", "slip"),
               ("swap", "swap"))},
        "total_bps": mean([r["total_bps"] for r in v]),
        "total_r": mean([r["total_r"] for r in v]),
        "dominant_bps": None, "share_dominant_bps": None,
    }


for axis, fn in (("symbol", lambda r: r["symbol"]),
                 ("class", lambda r: r["instrument_class"]),
                 ("family", lambda r: r["family"]),
                 ("broker_hour", lambda r: "bh%02d" % r["broker_hour"])):
    g = defaultdict(list)
    for r in rows:
        g[fn(r)].append(r)
    tab = {}
    for k, v in g.items():
        b = term_block(v)
        d = max(b["bps"], key=b["bps"].get)
        b["dominant_bps"] = d
        b["share_dominant_bps"] = b["bps"][d] / b["total_bps"] if b["total_bps"] else None
        dr = max(b["R"], key=b["R"].get)
        b["dominant_R"] = dr
        b["share_dominant_R"] = b["R"][dr] / b["total_r"] if b["total_r"] else None
        tab[k] = b
    res.setdefault("TERM_DOMINANCE", {})[axis] = tab

# ---------------------------------------------------------- 2. bps vs R disagreement
for axis, fn in (("symbol", lambda r: r["symbol"]),
                 ("family", lambda r: r["family"]),
                 ("class", lambda r: r["instrument_class"]),
                 ("broker_hour", lambda r: "bh%02d" % r["broker_hour"]),
                 ("kill_zone", lambda r: r.get("kill_zone"))):
    g = defaultdict(list)
    for r in rows:
        g[fn(r)].append(r)
    cells = {k: {"n": len(v), "cost_bps": mean([r["total_bps"] for r in v]),
                 "cost_r": mean([r["total_r"] for r in v]),
                 "rdp": mean([r["rdp"] for r in v])} for k, v in g.items() if len(v) >= 25}
    by_b = sorted(cells, key=lambda k: cells[k]["cost_bps"])
    by_r = sorted(cells, key=lambda k: cells[k]["cost_r"])
    for k in cells:
        cells[k]["rank_bps"] = by_b.index(k) + 1
        cells[k]["rank_R"] = by_r.index(k) + 1
        cells[k]["rank_move"] = cells[k]["rank_bps"] - cells[k]["rank_R"]
    res.setdefault("BPS_VS_R", {})[axis] = {
        "spearman": spearman([(v["cost_bps"], v["cost_r"]) for v in cells.values()]),
        "max_abs_rank_move": max((abs(v["rank_move"]) for v in cells.values()), default=None),
        "range_bps": (min(v["cost_bps"] for v in cells.values()),
                      max(v["cost_bps"] for v in cells.values())),
        "range_R": (min(v["cost_r"] for v in cells.values()),
                    max(v["cost_r"] for v in cells.values())),
        "dispersion_bps": max(v["cost_bps"] for v in cells.values()) / min(v["cost_bps"] for v in cells.values()),
        "dispersion_R": max(v["cost_r"] for v in cells.values()) / min(v["cost_r"] for v in cells.values()),
        "cells": cells,
    }

# ------------------------------------------------------- 3. the affordability sweep
def sweep(rows, key, thresholds, direction="le"):
    out = []
    for t in thresholds:
        v = [r for r in rows if (r[key] <= t if direction == "le" else r[key] >= t)]
        if not v:
            continue
        c = [r["total_r"] for r in v]
        g = [r[EDGE] for r in v]
        cb = [r["total_bps"] for r in v]
        gb = [r[EDGE] * r["rdp"] * 1e4 for r in v]
        net = [a - b for a, b in zip(g, c)]
        byday = defaultdict(list)
        for r, x in zip(v, net):
            byday[r["day"]].append(x)
        dm = {d: mean(x) for d, x in byday.items()}
        out.append({"threshold": t, "n": len(v), "frac": len(v) / len(rows),
                    "cost_r": mean(c), "cost_bps": mean(cb),
                    "gross_r": mean(g), "gross_bps": mean(gb),
                    "net_r": mean(net), "net_bps": mean(gb) - mean(cb),
                    "t_net": (mean(net) / se(net)) if se(net) else None,
                    "edge_over_cost_R": mean(g) / mean(c) if mean(c) else None,
                    "edge_over_cost_bps": mean(gb) / mean(cb) if mean(cb) else None,
                    "days": len(dm),
                    "days_positive": sum(1 for x in dm.values() if x > 0),
                    "n_symbols": len({r["symbol"] for r in v})})
    return out


res["SWEEP_cost_bps_le"] = sweep(rows, "total_bps",
                                 [0.3, 0.4, 0.5, 0.6, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5,
                                  3.0, 4.0, 5.0, 10.0, 100.0])
res["SWEEP_cost_r_le"] = sweep(rows, "total_r",
                               [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.125, 0.15,
                                0.20, 0.25, 0.30, 0.50, 10.0])
res["SWEEP_spread_bps_le"] = sweep(rows, "spread_bps",
                                   [0.2, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 5.0, 100.0])

# ------------------------------------------------------------- 4. ENTRY TIMING: delay
# The toll is a function of the hour you enter, so a delay changes the toll as well as
# the gross. Re-price the spread at the broker hour of (decision + k minutes).
timing = []
for k in KS:
    key = f"K{k}_TRAIL025"
    if key not in rows[0]:
        continue
    cost, gross, cbps, gbps = [], [], [], []
    for r in rows:
        if r.get(key) is None:
            continue
        w = utc_to_broker_naive(
            datetime.fromisoformat(r["dt"]).astimezone(timezone.utc) + timedelta(minutes=k),
            SERVER)
        sp_bps, _, _ = H1.spread_bps(r["symbol"], w.hour)
        sp_px = sp_bps * r["entry_price"] / 1e4
        tot = sp_px + r["comm_px"] + r["slip_px"] + r["swap_px"]
        cost.append(tot / r["risk_distance"])
        cbps.append(tot / r["entry_price"] * 1e4)
        gross.append(r[key])
        gbps.append(r[key] * r["rdp"] * 1e4)
    net = [a - b for a, b in zip(gross, cost)]
    timing.append({"k_minutes": k, "n": len(gross),
                   "cost_r": mean(cost), "cost_bps": mean(cbps),
                   "gross_r": mean(gross), "gross_bps": mean(gbps),
                   "net_r": mean(net), "t_net": mean(net) / se(net),
                   "edge_over_cost_R": mean(gross) / mean(cost),
                   "edge_over_cost_bps": mean(gbps) / mean(cbps)})
res["ENTRY_DELAY_JOINT"] = timing

# --------------------------------------------- 5. at-market vs resting limit (counterfactual)
# A passive limit fill crosses the spread ONCE (on exit) instead of twice (in and out),
# so it pays HALF the round-turn spread. The live engine cannot place one (l10-X3), so
# this prices the CAPABILITY, not a strategy.
half = []
for lbl, f in (("at_market_full_spread", 1.0), ("resting_limit_half_spread", 0.5),
               ("zero_spread_bound", 0.0)):
    cost = [(r["spread_px"] * f + r["comm_px"] + r["slip_px"] + r["swap_px"]) / r["risk_distance"]
            for r in rows]
    cbps = [(r["spread_px"] * f + r["comm_px"] + r["slip_px"] + r["swap_px"]) / r["entry_price"] * 1e4
            for r in rows]
    g = [r[EDGE] for r in rows]
    gb = [r[EDGE] * r["rdp"] * 1e4 for r in rows]
    net = [a - b for a, b in zip(g, cost)]
    half.append({"entry_mode": lbl, "spread_multiplier": f, "n": len(rows),
                 "cost_r": mean(cost), "cost_bps": mean(cbps),
                 "gross_r": mean(g), "net_r": mean(net),
                 "edge_over_cost_R": mean(g) / mean(cost),
                 "edge_over_cost_bps": mean(gb) / mean(cbps)})
res["ENTRY_MODE_SPREAD_INCIDENCE"] = half

# ------------------------------------- 6. first-minute cancel: does the refused cohort cost more?
JAN = f"{D}/w0_WORKING_SET.jsonl.gz"
jrows = []
for line in gzip.open(JAN, "rt"):
    r = json.loads(line)
    sym, ep, rd = r["symbol"], float(r["entry_price"]), float(r["risk_distance"])
    w = H1.broker_wall(r["decision_time_utc"])
    sp_bps, sp_flat, _ = H1.spread_bps(sym, w.hour)
    if sp_bps is None:
        continue
    cm, _ = H1.comm_px(sym, ep)
    cm = cm or 0.0
    sl_bps, _ = H1.SLIP_BPS.get(sym, (0.0, "Z"))
    swn, _ = H1.swap_px_per_night(sym, r["side"], ep)
    ncr, nn = H1.rollover_crossings(r["decision_time_utc"], 120)
    sw = (swn or 0.0) * nn
    tot = sp_bps * ep / 1e4 + cm + sl_bps * ep / 1e4 + sw
    bt = r.get("bars_to_entry_touch")
    jrows.append({"symbol": sym, "family": r["origin_family"], "day": r["decision_time_utc"][:10],
                  "broker_hour": w.hour, "rdp": rd / ep,
                  "cost_r": tot / rd, "cost_bps": tot / ep * 1e4,
                  "spread_bps": sp_bps, "comm_bps": cm / ep * 1e4,
                  "gross_r": r["gross_r"], "plain_walk_r": r["plain_walk_r"],
                  "fill_honest_walk_r": r["fill_honest_walk_r"],
                  "touch_bar": bt,
                  "born_past_stop": (r.get("mae_r") is not None and r.get("mfe_r_before_stop") is not None
                                     and r.get("bars_to_stop") == 1 and r.get("mfe_r_before_stop") < -1.0),
                  "fast_touch": (bt is not None and bt <= 1)})
res["JAN_POOL_COST"] = {"n": len(jrows), "cost_r": mean([r["cost_r"] for r in jrows]),
                        "cost_bps": mean([r["cost_bps"] for r in jrows])}
cut = {}
for lbl, sel in (("fast_touch_le_60s", lambda r: r["fast_touch"]),
                 ("slow_touch_gt_60s", lambda r: not r["fast_touch"])):
    v = [r for r in jrows if sel(r)]
    cut[lbl] = {"n": len(v), "frac": len(v) / len(jrows),
                "cost_r": mean([r["cost_r"] for r in v]),
                "cost_bps": mean([r["cost_bps"] for r in v]),
                "spread_bps": mean([r["spread_bps"] for r in v]),
                "rdp": mean([r["rdp"] for r in v]),
                "gross_r": mean([r["gross_r"] for r in v]),
                "fill_honest_walk_r": mean([r["fill_honest_walk_r"] for r in v])}
res["FIRST_MINUTE_CANCEL_COST"] = cut

# -------------------------------------------------- 7. hour-0 / rollover forensics
h0 = [r for r in rows if r["broker_hour"] == 0]
res["ROLLOVER_HOUR"] = {
    "broker_hour_0": {"n": len(h0), "frac": len(h0) / len(rows),
                      "cost_r": mean([r["total_r"] for r in h0]),
                      "cost_bps": mean([r["total_bps"] for r in h0]),
                      "spread_bps": mean([r["spread_bps"] for r in h0]),
                      "spread_bps_flat_basis": mean([r["spread_bps_flat"] for r in h0]),
                      "share_of_pool_toll_R": (len(h0) * mean([r["total_r"] for r in h0]))
                      / (len(rows) * mean([r["total_r"] for r in rows])),
                      "by_symbol": {s: {"n": len([r for r in h0 if r["symbol"] == s]),
                                        "spread_bps": mean([r["spread_bps"] for r in h0 if r["symbol"] == s]),
                                        "spread_bps_flat": mean([r["spread_bps_flat"] for r in h0 if r["symbol"] == s]),
                                        "cost_r": mean([r["total_r"] for r in h0 if r["symbol"] == s])}
                                    for s in sorted({r["symbol"] for r in h0})}},
    "swap_rows": {"n": sum(1 for r in rows if r["swap_px"] > 0),
                  "frac": sum(1 for r in rows if r["swap_px"] > 0) / len(rows),
                  "mean_swap_r_when_charged": mean([r["swap_r"] for r in rows if r["swap_px"] > 0]),
                  "mean_swap_bps_when_charged": mean([r["swap_bps"] for r in rows if r["swap_px"] > 0]),
                  "share_of_pool_toll_R": sum(r["swap_r"] for r in rows) / sum(r["total_r"] for r in rows),
                  "by_broker_hour": {h: sum(1 for r in rows if r["swap_px"] > 0 and r["broker_hour"] == h)
                                     for h in range(24)}},
    "hour_aware_vs_flat": {
        "cost_r_hour_aware": mean([r["total_r_noswap"] for r in rows]),
        "cost_r_flat": mean([r["total_r_flat"] for r in rows]),
        "delta_r": mean([r["total_r_noswap"] for r in rows]) - mean([r["total_r_flat"] for r in rows]),
        "pct": (mean([r["total_r_noswap"] for r in rows]) / mean([r["total_r_flat"] for r in rows]) - 1) * 100,
    },
}

json.dump(res, open(OUT, "w"), indent=1, default=str)

# ------------------------------------------------------------------------- digest
print("== term share of total, pool ==")
tot_b = mean([r["total_bps"] for r in rows])
tot_r = mean([r["total_r"] for r in rows])
for t, k in (("spread", "spread"), ("commission", "comm"), ("slippage", "slip"), ("swap", "swap")):
    print("  %-11s bps %7.4f (%5.1f%%)   R %8.5f (%5.1f%%)"
          % (t, mean([r[f"{k}_bps"] for r in rows]), 100 * mean([r[f"{k}_bps"] for r in rows]) / tot_b,
             mean([r[f"{k}_r"] for r in rows]), 100 * mean([r[f"{k}_r"] for r in rows]) / tot_r))
print()
print("== dominant term by symbol ==")
for s, b in sorted(res["TERM_DOMINANCE"]["symbol"].items(), key=lambda kv: -kv[1]["total_bps"]):
    print("  %-12s n=%5d tot %8.4f bps  dom=%-11s %5.1f%%   (spr %7.4f comm %7.4f slip %6.4f swap %6.4f)"
          % (s, b["n"], b["total_bps"], b["dominant_bps"], 100 * b["share_dominant_bps"],
             b["bps"]["spread"], b["bps"]["commission"], b["bps"]["slippage"], b["bps"]["swap"]))
print()
print("== affordability sweep, cost_bps <= X ==")
print("  %8s %7s %6s %8s %9s %9s %8s %8s %7s %6s" % ("thr_bps", "n", "frac", "cost_bps",
      "gross_R", "net_R", "e/c_R", "e/c_bps", "t_net", "days+"))
for s in res["SWEEP_cost_bps_le"]:
    print("  %8.2f %7d %6.3f %8.4f %+9.5f %+9.5f %8.3f %8.3f %7.2f %6s"
          % (s["threshold"], s["n"], s["frac"], s["cost_bps"], s["gross_r"], s["net_r"],
             s["edge_over_cost_R"], s["edge_over_cost_bps"], s["t_net"],
             "%d/%d" % (s["days_positive"], s["days"])))
print()
print("== entry delay, joint gross+cost ==")
print("  %3s %9s %9s %9s %9s %8s %8s" % ("k", "cost_R", "cost_bps", "gross_R", "net_R", "e/c_R", "t_net"))
for t in res["ENTRY_DELAY_JOINT"]:
    print("  %3d %9.5f %9.4f %+9.5f %+9.5f %8.3f %+8.2f"
          % (t["k_minutes"], t["cost_r"], t["cost_bps"], t["gross_r"], t["net_r"],
             t["edge_over_cost_R"], t["t_net"]))
print()
print("== entry mode (spread incidence) ==")
for t in res["ENTRY_MODE_SPREAD_INCIDENCE"]:
    print("  %-28s cost_R %.5f  cost_bps %.4f  net_R %+.5f  e/c_R %.3f"
          % (t["entry_mode"], t["cost_r"], t["cost_bps"], t["net_r"], t["edge_over_cost_R"]))
print()
print("== first-minute cancel cohorts (January pool, n=%d) ==" % res["JAN_POOL_COST"]["n"])
for k, v in res["FIRST_MINUTE_CANCEL_COST"].items():
    print("  %-20s n=%6d (%5.2f%%) cost_R %.4f cost_bps %.4f spread_bps %.4f rdp %.5f gross_R %+.5f"
          % (k, v["n"], 100 * v["frac"], v["cost_r"], v["cost_bps"], v["spread_bps"],
             v["rdp"], v["gross_r"]))
print()
r0 = res["ROLLOVER_HOUR"]["broker_hour_0"]
print("== broker hour 0 ==  n=%d (%.2f%%) cost_R %.4f cost_bps %.4f spread_bps %.4f (flat basis %.4f) share of pool toll %.4f"
      % (r0["n"], 100 * r0["frac"], r0["cost_r"], r0["cost_bps"], r0["spread_bps"],
         r0["spread_bps_flat_basis"], r0["share_of_pool_toll_R"]))
sw = res["ROLLOVER_HOUR"]["swap_rows"]
print("== swap ==  charged on %d rows (%.2f%%), mean %.4f R / %.4f bps when charged, %.2f%% of pool toll"
      % (sw["n"], 100 * sw["frac"], sw["mean_swap_r_when_charged"],
         sw["mean_swap_bps_when_charged"], 100 * sw["share_of_pool_toll_R"]))
ha = res["ROLLOVER_HOUR"]["hour_aware_vs_flat"]
print("== hour-aware vs flat-median spread ==  %.6f R vs %.6f R  =  %+.6f R/trade  (%+.2f%%)"
      % (ha["cost_r_hour_aware"], ha["cost_r_flat"], ha["delta_r"], ha["pct"]))
