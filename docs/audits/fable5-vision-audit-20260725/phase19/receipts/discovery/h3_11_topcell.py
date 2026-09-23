"""h3-11 -- forensics on the surviving cells: is any of this one symbol, one day, one month?

The lead cell is convention-INVARIANT by construction: entry is a MARKET order sent when
price trades back through the decision price, so the full quoted spread is charged whether
the archived bars are bid or mid (verified algebraically in h3_RESULT.md S6). Everything
that needs a passive fill is reported separately and never leads.

Checks run on every surviving cell:
  per-symbol, per-month, per-day concentration
  leave-one-symbol-out and leave-one-month-out
  R-space as well as bps-space (they can disagree in SIGN -- h3-F9)
  a 2,000-resample day-block bootstrap
  the no-retrace threshold curve, so the reader sees the whole shape and not the argmax
"""
import gzip
import json
import os
import random
import sys

D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import h3_lib as H  # noqa: E402

C = "TRAIL025"
rows = [json.loads(x) for x in gzip.open(os.path.join(D, "H3_STRICT_ROWS_V1.jsonl.gz"), "rt")
        if x.strip()]
H.add_hour_cost(rows)
N = len(rows)
sy = {}
for r in rows:
    sy.setdefault(r["symbol"], []).append(r)
symcost = sorted(sy, key=lambda s: H.mean([x["cost_true"] * x["rdp"] * 1e4 for x in sy[s]]))
CH6 = set(symcost[:6])
out = {"lane": "h3", "step": "topcell", "n": N, "cheap6": symcost[:6],
       "convention_note": "market-on-touch: full spread charged, bid/mid invariant"}


def stat(sub, valk, tollk="cost_true", B=2000, seed=11):
    g = [r[valk] * r["rdp"] * 1e4 for r in sub if r.get(valk) is not None]
    t = [r[tollk] * r["rdp"] * 1e4 for r in sub if r.get(valk) is not None]
    keep = [r for r in sub if r.get(valk) is not None]
    n = [a - b for a, b in zip(g, t)]
    if len(g) < 10:
        return None
    d = {"n": len(g), "edge_bps": H.mean(g), "toll_bps": H.mean(t), "net_bps": H.mean(n),
         "edge_over_toll": H.mean(g) / H.mean(t),
         "gross_r": H.mean([r[valk] for r in keep]),
         "cost_r": H.mean([r[tollk] for r in keep]),
         "net_r": H.mean([r[valk] - r[tollk] for r in keep]),
         "t_net_trade": H.tstat(n)}
    bd = {}
    for r, v in zip(keep, n):
        bd.setdefault(r["day"], []).append(v)
    bdr = {}
    for r in keep:
        bdr.setdefault(r["day"], []).append(r[valk] - r[tollk])
    d["days"] = len(bd)
    d["days_net_positive"] = sum(1 for v in bd.values() if sum(v) / len(v) > 0)
    rnd = random.Random(seed)
    ks = list(bd)
    ms, mr = [], []
    for _ in range(B):
        s = [rnd.choice(ks) for _ in ks]
        tot = cnt = 0
        totr = 0.0
        for k in s:
            tot += sum(bd[k]); cnt += len(bd[k]); totr += sum(bdr[k])
        ms.append(tot / cnt); mr.append(totr / cnt)
    ms.sort(); mr.sort()
    d["boot_net_bps"] = {"lo95": ms[50], "hi95": ms[-51], "p_le_0": sum(1 for x in ms if x <= 0) / B}
    d["boot_net_r"] = {"lo95": mr[50], "hi95": mr[-51], "p_le_0": sum(1 for x in mr if x <= 0) / B}
    return d


def sel_noretrace(c, cheap=True):
    return [r for r in rows if r["j_mid"] is not None and r["j_mid"] >= c
            and (r["symbol"] in CH6 if cheap else True)]


# ---- the whole threshold curve, not the argmax
curve = []
for c in range(0, 31):
    for cheap in (True, False):
        sub = sel_noretrace(c, cheap)
        d = stat(sub, "mid_r")
        if d:
            d["cond_min"] = c
            d["universe"] = "CHEAP6" if cheap else "ALL24"
            curve.append(d)
out["threshold_curve"] = curve

LEAD = {"cond_min": 10, "universe": "CHEAP6", "entry": "market on touch",
        "toll": "full broker-true"}
out["lead_cell_spec"] = LEAD
lead = sel_noretrace(10, True)
out["lead_cell"] = stat(lead, "mid_r")
out["lead_cell_hour_aware"] = stat(lead, "mid_r", "cost_true_hour")

# ---- concentration
out["lead_by_symbol"] = {s: stat([r for r in lead if r["symbol"] == s], "mid_r", B=200)
                         for s in sorted({r["symbol"] for r in lead})}
out["lead_by_month"] = {m: stat([r for r in lead if r["month"] == m], "mid_r", B=500)
                        for m in sorted(H.MONTHS)}
out["lead_by_side"] = {s: stat([r for r in lead if r["side"] == s], "mid_r", B=500)
                       for s in sorted({r["side"] for r in lead})}
out["lead_leave_one_symbol_out"] = {
    s: stat([r for r in lead if r["symbol"] != s], "mid_r", B=500)
    for s in sorted({r["symbol"] for r in lead})}
out["lead_leave_one_month_out"] = {
    m: stat([r for r in lead if r["month"] != m], "mid_r", B=500) for m in sorted(H.MONTHS)}

# day concentration: share of total net carried by the best day
bd = {}
for r in lead:
    if r.get("mid_r") is None:
        continue
    bd.setdefault(r["day"], []).append((r["mid_r"] - r["cost_true"]) * r["rdp"] * 1e4)
tot = sum(sum(v) for v in bd.values())
byday = sorted(((k, sum(v), len(v)) for k, v in bd.items()), key=lambda x: -x[1])
out["lead_day_concentration"] = {
    "n_days": len(bd), "total_net_bps": tot,
    "top_day": byday[0][0], "top_day_net_bps": byday[0][1],
    "top_day_share_of_total": byday[0][1] / tot if tot else None,
    "top3_share_of_total": sum(x[1] for x in byday[:3]) / tot if tot else None,
    "days_positive": sum(1 for k, v, n in byday if v > 0)}

# ---- also carry the other surviving cells through the same forensics
others = {
    "CHEAP2_at_market_k5": [r for r in rows if r["symbol"] in set(symcost[:2])],
    "GER40_at_market_k5": [r for r in rows if r["symbol"] == "GER40"],
    "regime_transition_break_k5": [r for r in rows if r.get("family") == "regime_transition_break"],
    "NY13_at_market_k5": [r for r in rows if r["ny_hour"] == 13],
}
oc = {}
for k, sub in others.items():
    oc[k] = {"flat": stat(sub, "K5_" + C), "hour_aware": stat(sub, "K5_" + C, "cost_true_hour"),
             "by_month": {m: stat([r for r in sub if r["month"] == m], "K5_" + C, B=500)
                          for m in sorted(H.MONTHS)}}
out["other_cells"] = oc

p = H.dump(out, "H3_TOPCELL_V1.json")
L = out["lead_cell"]
print("LEAD CELL: no-retrace>=10 min, market on touch, 6 cheapest instruments")
print(json.dumps({k: L[k] for k in ("n", "edge_bps", "toll_bps", "net_bps", "edge_over_toll",
                                    "gross_r", "cost_r", "net_r", "days", "days_net_positive",
                                    "boot_net_bps", "boot_net_r")}, indent=1))
print("hour-aware:", json.dumps({k: out["lead_cell_hour_aware"][k]
                                 for k in ("toll_bps", "net_bps", "edge_over_toll", "net_r",
                                           "boot_net_bps")}, indent=1))
print("\nday concentration", json.dumps(out["lead_day_concentration"], indent=1))
print("\nper symbol:")
for s, d in out["lead_by_symbol"].items():
    if d:
        print("  %-12s n=%4d e/t=%6.3f net_bps=%+8.4f net_r=%+.5f" %
              (s, d["n"], d["edge_over_toll"], d["net_bps"], d["net_r"]))
print("leave-one-symbol-out:")
for s, d in out["lead_leave_one_symbol_out"].items():
    if d:
        print("  drop %-12s n=%4d e/t=%6.3f net_bps=%+8.4f net_r=%+.5f" %
              (s, d["n"], d["edge_over_toll"], d["net_bps"], d["net_r"]))
print("per month:")
for m, d in out["lead_by_month"].items():
    if d:
        print("  %s n=%4d e/t=%6.3f net_bps=%+8.4f net_r=%+.5f" %
              (m, d["n"], d["edge_over_toll"], d["net_bps"], d["net_r"]))
print("\nthreshold curve (CHEAP6):")
for d in curve:
    if d["universe"] == "CHEAP6" and d["cond_min"] in (0, 1, 2, 3, 5, 7, 8, 9, 10, 11, 12, 15, 20, 25, 30):
        print("  c=%2d n=%5d e/t=%6.3f net_bps=%+8.4f net_r=%+.5f p<=0 %.3f" %
              (d["cond_min"], d["n"], d["edge_over_toll"], d["net_bps"], d["net_r"],
               d["boot_net_bps"]["p_le_0"]))
print("->", p)
