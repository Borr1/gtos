#!/usr/bin/env python3
"""h5 step 12 — the two leads, stressed every way the substrate allows.

Only two things came out of this lane with a five-month record worth writing down:
  L1  GER40 at UTC hour 14 — the one cell positive in all five months
  L2  cost_true_hour <= 0.02 — a rule containing NO outcome information at all

Stresses applied to each:
  contract invariance   the same cell under all 6 exit contracts x 11 entry delays that
                        e_build_atmkt wrote.  A cell whose sign lives in one (k, contract)
                        is a fit; one that holds across the menu is structure.
  toll stress           x1.0 / x1.5 / x2.0 broker-true cost, and hour-aware vs flat
  concentration         best-day share, net with best 1 / best 3 days dropped, 10% trim
  neighbour hours       the same symbol at h13 and h15 (a real hour effect has a shape)
  day economics         trades per calendar day and net R per calendar day

out: h5_LEADS_V1.json
"""
import gzip
import json
import os
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h5_lib  # noqa: E402

h5_lib.COST = "cost_true_hour"
rows = [json.loads(x) for x in gzip.open(os.path.join(D, "h5_SUBSTRATE_5M.jsonl.gz"), "rt") if x.strip()]
KS = [0, 1, 2, 3, 5, 10, 15, 20, 30, 45, 60]
CS = ["INC", "TRAIL025", "TS90S1", "STOPONLY", "T3S1", "TS60S1"]
OUT = {"n_rows_5m": len(rows)}

LEADS = {
    "L1_GER40_h14": lambda r: r["symbol"] == "GER40" and r["hour"] == 14,
    "L1b_GER40_h13": lambda r: r["symbol"] == "GER40" and r["hour"] == 13,
    "L1c_GER40_h15": lambda r: r["symbol"] == "GER40" and r["hour"] == 15,
    "L1d_GER40_h08": lambda r: r["symbol"] == "GER40" and r["hour"] == 8,
    "L2_costhour_le_002": lambda r: r["cost_true_hour"] <= 0.02,
    "L2b_costhour_le_001": lambda r: r["cost_true_hour"] <= 0.01,
    "L3_h14_x_cost_dec0": lambda r: r["hour"] == 14 and r["cost_dec"] == 0,
    "BOOK": lambda r: True,
}


def concentration(rs, cost_key="cost_true_hour"):
    net = [r["K5_TRAIL025"] - r[cost_key] for r in rs]
    n = len(net)
    byday = {}
    for r, x in zip(rs, net):
        byday.setdefault(r["day"], []).append(x)
    tot = sum(net)
    ds = sorted(byday.items(), key=lambda kv: -sum(kv[1]))
    d1 = [x for _d, v in ds[1:] for x in v]
    d3 = [x for _d, v in ds[3:] for x in v]
    s = sorted(net)
    k = int(0.10 * n)
    trim = s[k:n - k] if n - 2 * k >= 5 else s
    return {"total_net_R": round(tot, 3),
            "best_day_share": round(sum(ds[0][1]) / tot, 4) if tot else None,
            "best3_share": round(sum(x for _d, v in ds[:3] for x in v) / tot, 4) if tot else None,
            "net_drop_best_day": round(sum(d1) / len(d1), 6) if d1 else None,
            "net_drop_best_3_days": round(sum(d3) / len(d3), 6) if d3 else None,
            "net_trim10": round(sum(trim) / len(trim), 6),
            "net_median": round(s[n // 2], 6),
            "days": len(byday), "days_net_pos": sum(1 for v in byday.values() if sum(v) > 0),
            "trades_per_calendar_day": round(n / 105.0, 3),
            "net_R_per_calendar_day": round(tot / 105.0, 4)}


res = {}
for name, fn in LEADS.items():
    rs = [r for r in rows if fn(r)]
    if len(rs) < 20:
        continue
    rec = {"n": len(rs)}
    for lab, ck in (("hour_aware", "cost_true_hour"), ("flat", "cost_true")):
        s = h5_lib.cell_stats(rs, cost_key=ck)
        rec[lab] = {"gross_R": s["gross_R"], "cost_R": s["cost_R"], "net_R": s["net_R"],
                    "ratio_R": s["ratio_R"], "t_net": s["t_net"], "t_net_day": s["t_net_day"],
                    "days": s["days"], "days_net_pos": s["days_net_pos"],
                    **{m: (s["m_" + m]["ratio_R"] if s["m_" + m] else None)
                       for m in ("2026-01", "2026-02", "2026-03")}}
    for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"):
        sub = [r for r in rs if r["month"] == m]
        rec["month_" + m] = (None if len(sub) < 10 else
                             {k: h5_lib.cell_stats(sub)[k] for k in
                              ("n", "gross_R", "cost_R", "net_R", "ratio_R", "t_net_day")})
    for mult in (1.0, 1.5, 2.0):
        for r in rs:
            r["_stress"] = r["cost_true_hour"] * mult
        s = h5_lib.cell_stats(rs, cost_key="_stress")
        rec["toll_x%.1f" % mult] = {"net_R": s["net_R"], "ratio_R": s["ratio_R"],
                                    "t_net_day": s["t_net_day"]}
    rec["concentration"] = concentration(rs)
    grid = []
    for k in KS:
        for c in CS:
            col = "K%d_%s" % (k, c)
            v = [r for r in rs if r.get(col) is not None]
            if len(v) < 30:
                continue
            s = h5_lib.cell_stats(v, gross_key=col)
            grid.append({"k": k, "contract": c, "n": s["n"], "gross_R": s["gross_R"],
                         "net_R": s["net_R"], "ratio_R": s["ratio_R"], "t_net_day": s["t_net_day"]})
    rec["contract_grid"] = grid
    rec["contract_grid_summary"] = {
        "n_arms": len(grid),
        "n_arms_net_positive": sum(1 for g in grid if g["net_R"] > 0),
        "n_arms_ratio_gt_1": sum(1 for g in grid if g["ratio_R"] and g["ratio_R"] > 1),
        "median_ratio": round(sorted(g["ratio_R"] for g in grid if g["ratio_R"] is not None)[len(grid) // 2], 4)
        if grid else None,
        "best": max(grid, key=lambda g: g["net_R"]) if grid else None,
        "worst": min(grid, key=lambda g: g["net_R"]) if grid else None}
    res[name] = rec
OUT["leads"] = res

json.dump(OUT, open(os.path.join(D, "h5_LEADS_V1.json"), "w"), indent=1)

for name, rec in res.items():
    h = rec["hour_aware"]
    c = rec["concentration"]
    g = rec["contract_grid_summary"]
    print("== %-22s n=%5d" % (name, rec["n"]))
    print("   hour-aware  net %+.5f ratio %6.2f t_day %+5.2f   flat net %+.5f ratio %6.2f" %
          (h["net_R"], h["ratio_R"] or 0, h["t_net_day"] or 0,
           rec["flat"]["net_R"], rec["flat"]["ratio_R"] or 0))
    mm = " ".join("%s:%s" % (m[-2:], ("%.2f" % rec["month_" + m]["ratio_R"]) if rec.get("month_" + m) else "-")
                  for m in ("2026-01", "2026-02", "2026-03", "2026-04", "2026-05"))
    print("   by month ratio  " + mm)
    print("   toll x1.0 %+.5f  x1.5 %+.5f  x2.0 %+.5f" %
          (rec["toll_x1.0"]["net_R"], rec["toll_x1.5"]["net_R"], rec["toll_x2.0"]["net_R"]))
    print("   concentration  bestday %5.3f  drop1 %+.5f  drop3 %+.5f  trim10 %+.5f  d+/d %d/%d  %.2f tr/day  %+.4f R/day" %
          (c["best_day_share"] or 0, c["net_drop_best_day"] or 0, c["net_drop_best_3_days"] or 0,
           c["net_trim10"], c["days_net_pos"], c["days"], c["trades_per_calendar_day"],
           c["net_R_per_calendar_day"]))
    print("   contract grid  %d arms, %d net-positive, %d ratio>1, median ratio %s; best %s k=%d net %+.5f" %
          (g["n_arms"], g["n_arms_net_positive"], g["n_arms_ratio_gt_1"], g["median_ratio"],
           g["best"]["contract"], g["best"]["k"], g["best"]["net_R"]))
