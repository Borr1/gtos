"""h2_hourcost — re-cost every trade at its OWN broker hour, then re-run the hunt.

`e_lib.real_cost_parts` charges `spread_bps_median` -- ONE constant per symbol -- so the
cost side of the whole swarm has no intra-symbol structure.  The very same tick artifact
(`L10X_TICK_SPREAD_V1.json`) already carries `spread_bps_median_by_broker_hour`, and the
within-symbol dispersion in it is up to **34.67x** (EURUSD 0.0881 -> 3.0549 bps), which
dwarfs the 12.1x cross-family dispersion the swarm closed on.

Broker hour comes from `src/utils/broker_clock.py` NEW_YORK_PLUS_7 (UTC+2 on EST, UTC+3 on
EDT) -- the measured FTMO-Server3 rule, not the EET assumption.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime

import numpy as np

D = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(D, "..", "..", "..", "..", "..", ".."))
sys.path.insert(0, D)
sys.path.insert(0, REPO)
import h2_lib as H  # noqa: E402
import h2_scan  # noqa: E402
import e_lib  # noqa: E402
from src.utils.broker_clock import NEW_YORK_PLUS_7, utc_to_broker_naive  # noqa: E402

TICK = json.load(open(os.path.join(D, "L10X_TICK_SPREAD_V1.json")))


def attach(rows):
    """Add broker_hour and the hour-true cost.  Returns coverage stats."""
    hrmap = {}
    for sym, mapped in e_lib.TMAP.items():
        tk = TICK.get("ftmo:" + mapped, {})
        h = tk.get("spread_bps_median_by_broker_hour") or {}
        if h:
            hrmap[sym] = {int(k): float(v) for k, v in h.items()}
    miss = 0
    for r in rows:
        dt = datetime.fromisoformat(r["dt"])
        bh = utc_to_broker_naive(dt, NEW_YORK_PLUS_7).hour
        r["bhour"] = bh
        hm = hrmap.get(r["symbol"])
        if not hm or bh not in hm:
            miss += 1
            r["c_hr"] = r["c"]
            r["c_hr_bps"] = r["c_bps"]
            r["spread_hr_bps"] = None
            continue
        sp_bps = hm[bh]
        sp_r = sp_bps * float(r["entry_price"]) / 1e4 / float(r["risk_distance"])
        r["spread_hr_bps"] = sp_bps
        r["c_hr"] = sp_r + float(r["real_comm_r"]) + float(r["real_slip_r"])
        r["c_hr_bps"] = r["c_hr"] * float(r["rdp"]) * 1e4
    return {"rows": len(rows), "rows_without_hour_map": miss,
            "symbols_with_hour_map": len(hrmap)}


def restat(sub, use_hr=True):
    if not sub:
        return None
    g = np.array([r["g"] for r in sub])
    c = np.array([r["c_hr"] if use_hr else r["c"] for r in sub])
    gb = np.array([r["g_bps"] for r in sub])
    cb = np.array([r["c_hr_bps"] if use_hr else r["c_bps"] for r in sub])
    nt = g - c
    days = {}
    for x, r in zip(nt, sub):
        days.setdefault(r["day"], []).append(x)
    dpos = sum(1 for v in days.values() if sum(v) / len(v) > 0)
    dm = nt - nt.mean()
    agg = {}
    for x, r in zip(dm, sub):
        agg[r["day"]] = agg.get(r["day"], 0.0) + x
    G = len(agg)
    cse = (float(np.sqrt(sum(a * a for a in agg.values()) * G / (G - 1))) / len(nt)) if G > 1 else float("nan")
    bym = {}
    for x, r in zip(nt, sub):
        bym.setdefault(r["month"], []).append(x)
    return {"n": len(sub), "gross_r": round(float(g.mean()), 6),
            "cost_r": round(float(c.mean()), 6), "net_r": round(float(nt.mean()), 6),
            "gross_bps": round(float(gb.mean()), 5), "cost_bps": round(float(cb.mean()), 5),
            "margin_bps": round(float(gb.mean() - cb.mean()), 5),
            "edge_cost_r": round(float(g.mean() / c.mean()), 4) if c.mean() > 0 else None,
            "t_net": round(float(nt.mean() / (nt.std(ddof=1) / np.sqrt(len(nt)))), 3) if len(nt) > 1 else None,
            "t_net_clu": round(float(nt.mean() / cse), 3) if cse == cse and cse > 0 else None,
            "days": len(days), "days_pos_net": dpos,
            "day_pos_frac": round(dpos / len(days), 4),
            "months": {m: round(float(np.mean(v)), 6) for m, v in sorted(bym.items())},
            "n_months": {m: len(v) for m, v in sorted(bym.items())}}


def main():
    rows = h2_scan.build()
    cov = attach(rows)
    out = {"coverage": cov,
           "pooled_flat_cost": restat(rows, False), "pooled_hour_cost": restat(rows, True)}

    # ------- per symbol, both cost frames
    sy = H.group(rows, lambda r: r["symbol"])
    out["symbols"] = {s: {"flat": restat(v, False), "hour": restat(v, True)}
                      for s, v in sorted(sy.items())}

    # ------- the full cell scan, hour-true
    defs = h2_scan.AXES + h2_scan.PAIRS + h2_scan.TRIPLES
    defs = defs + [("symbol_x_bhour", lambda r: "%s|b%02d" % (r["symbol"], r["bhour"])),
                   ("bhour", lambda r: "b%02d" % r["bhour"]),
                   ("symbol_x_bhblock", lambda r: "%s|%s" % (
                       r["symbol"], "b00_07" if r["bhour"] < 8 else "b08_12" if r["bhour"] < 13
                       else "b13_17" if r["bhour"] < 18 else "b18_23")),
                   ("symbol_x_bhblock_x_side", lambda r: "%s|%s|%s" % (
                       r["symbol"], "b00_07" if r["bhour"] < 8 else "b08_12" if r["bhour"] < 13
                       else "b13_17" if r["bhour"] < 18 else "b18_23", r["side"]))]
    cells = []
    for name, fn in defs:
        for k, v in H.group(rows, fn).items():
            if len(v) < 50:
                continue
            s = restat(v, True)
            s0 = restat(v, False)
            s["axis"] = name
            s["cell"] = k
            s["net_r_flatcost"] = s0["net_r"]
            s["cost_r_flatcost"] = s0["cost_r"]
            s["cost_bps_flatcost"] = s0["cost_bps"]
            cells.append(s)
    out["cells_hour_true"] = cells
    win = [c for c in cells if c["net_r"] > 0]
    win.sort(key=lambda x: -x["net_r"])
    out["winners_hour_true_n50"] = win
    out["n_cells_scanned"] = len(cells)
    out["n_winners"] = len(win)
    out["n_winners_n100"] = sum(1 for c in win if c["n"] >= 100)

    # winners that SURVIVE the re-cost vs winners CREATED by it
    out["recost_effect"] = {
        "won_under_both": sum(1 for c in cells if c["net_r"] > 0 and c["net_r_flatcost"] > 0),
        "won_only_hour_true": sum(1 for c in cells if c["net_r"] > 0 and c["net_r_flatcost"] <= 0),
        "lost_to_hour_true": sum(1 for c in cells if c["net_r"] <= 0 and c["net_r_flatcost"] > 0),
    }

    # ------- OOS: select on January (hour-true), read on Feb+Mar
    jan = [r for r in rows if r["month"] == "2026-01"]
    oos = [r for r in rows if r["month"] != "2026-01"]
    jt = {s: restat(v, True) for s, v in H.group(jan, lambda r: r["symbol"]).items()}
    pos = sorted([s for s in jt if jt[s]["net_r"] > 0])
    out["oos_symbol"] = {"jan_positive": pos, "jan_detail": {s: jt[s] for s in pos},
                         "read_febmar": restat([r for r in oos if r["symbol"] in set(pos)], True)}
    picked = []
    for name, fn in defs:
        gj = H.group(jan, fn)
        for k, v in gj.items():
            if len(v) < 40:
                continue
            s = restat(v, True)
            if s["net_r"] > 0:
                picked.append((name, k))
    reads = []
    for name, fn in defs:
        go = H.group(oos, fn)
        sel = {k for (nm, k) in picked if nm == name}
        for k in sel:
            v = go.get(k)
            if not v or len(v) < 20:
                continue
            s = restat(v, True)
            reads.append({"axis": name, "cell": k, "n_oos": s["n"], "net_oos": s["net_r"]})
    allc = []
    for name, fn in defs:
        for k, v in H.group(oos, fn).items():
            if len(v) >= 20:
                allc.append(restat(v, True)["net_r"])
    out["oos_cells"] = {
        "selected_on_jan": len(picked), "read": len(reads),
        "still_positive": sum(1 for x in reads if x["net_oos"] > 0),
        "hit_rate": round(sum(1 for x in reads if x["net_oos"] > 0) / len(reads), 4) if reads else None,
        "mean_oos_net": round(float(np.mean([x["net_oos"] for x in reads])), 6) if reads else None,
        "baseline_cells": len(allc),
        "baseline_hit_rate": round(float(np.mean([1 if x > 0 else 0 for x in allc])), 4),
        "baseline_mean_net": round(float(np.mean(allc)), 6),
        "detail": sorted(reads, key=lambda x: -x["net_oos"]),
    }

    with open(os.path.join(D, "H2_HOURCOST_V1.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    # ---------------------------------------------------------------- print
    print("coverage: %s" % cov)
    a, b = out["pooled_flat_cost"], out["pooled_hour_cost"]
    print("POOLED  flat-cost: cost %.5f R (%.4f bps) net %+.6f | HOUR-TRUE: cost %.5f R (%.4f bps) net %+.6f"
          % (a["cost_r"], a["cost_bps"], a["net_r"], b["cost_r"], b["cost_bps"], b["net_r"]))
    print("\nper-symbol, hour-true (sorted by hour-true net):")
    print("%-11s %5s %9s %9s %9s %9s %8s %8s %7s %6s %s"
          % ("symbol", "n", "gross_r", "cost_flat", "cost_hour", "net_hour", "gbps", "cbps_hr",
             "margin", "tclu", "months"))
    for s, v in sorted(out["symbols"].items(), key=lambda kv: -kv[1]["hour"]["net_r"]):
        h, f = v["hour"], v["flat"]
        print("%-11s %5d %+9.5f %9.5f %9.5f %+9.5f %+8.4f %8.4f %+7.4f %6.2f %d/3"
              % (s, h["n"], h["gross_r"], f["cost_r"], h["cost_r"], h["net_r"], h["gross_bps"],
                 h["cost_bps"], h["margin_bps"], h["t_net_clu"] or 0,
                 sum(1 for x in h["months"].values() if x > 0)))
    r = out["recost_effect"]
    print("\ncells n>=50: %d scanned, %d pay hour-true (%d at n>=100) | won under both %d, created by re-cost %d, killed by re-cost %d"
          % (out["n_cells_scanned"], out["n_winners"], out["n_winners_n100"],
             r["won_under_both"], r["won_only_hour_true"], r["lost_to_hour_true"]))
    print("\ntop 25 hour-true paying cells:")
    print("%-28s %-36s %6s %9s %9s %8s %7s %6s %s"
          % ("axis", "cell", "n", "gross_r", "net_hr", "net_flat", "margin", "tclu", "m+"))
    for c in win[:25]:
        print("%-28s %-36s %6d %+9.5f %+9.5f %+8.5f %+7.3f %6.2f %d/3"
              % (c["axis"], c["cell"][:36], c["n"], c["gross_r"], c["net_r"], c["net_r_flatcost"],
                 c["margin_bps"], c["t_net_clu"] or 0,
                 sum(1 for x in c["months"].values() if x > 0)))
    o = out["oos_symbol"]
    print("\nOOS hour-true: Jan-positive symbols = %s" % (", ".join(o["jan_positive"]) or "NONE"))
    if o["read_febmar"]:
        rf = o["read_febmar"]
        print("   -> Feb+Mar n=%d net=%+.6f tclu=%+.2f d+%d/%d months %s"
              % (rf["n"], rf["net_r"], rf["t_net_clu"] or 0, rf["days_pos_net"], rf["days"], rf["months"]))
    oc = out["oos_cells"]
    print("   CELLS: %d selected on Jan, %d read, %d positive (hit %.3f, baseline %.3f); mean OOS net %+.6f vs baseline %+.6f"
          % (oc["selected_on_jan"], oc["read"], oc["still_positive"], oc["hit_rate"],
             oc["baseline_hit_rate"], oc["mean_oos_net"], oc["baseline_mean_net"]))


if __name__ == "__main__":
    main()
