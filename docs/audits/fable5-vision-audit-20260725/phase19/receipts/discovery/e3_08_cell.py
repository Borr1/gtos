"""e3 step 8 -- the one cell that is NOT deleted by the cost gate but IS deleted by the
fill floor, priced across five months; and the 2-hour-wall objection settled by re-walking
the same candidates to 8 h and 24 h on raw M1 bars.

Cell:  takeable  AND  cost_r <= 0.15 (the shipped total-cost gate PASSES it)
                 AND  dist_r >= THR   (the shipped fill floor DELETES it)
"""
import bisect, collections, gzip, json, os, sys
D = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, D)
import e3_lib as E

MONTHS = [("JAN", "202601"), ("FEB", "202602"), ("MAR", "202603"), ("APR", "202604"), ("MAY", "202605")]
THR = 1.4175          # dist_r threshold calibrated to the shipped fp<0.45 floor on January
COSTCAP = 0.15        # config/agent_config.yaml:716  total_cost_r limit
HORIZONS = [120, 480, 1440]
OUT = {"dist_r_threshold": THR, "cost_cap": COSTCAP, "horizons_minutes": HORIZONS}

rows = {}
for m, ym in MONTHS:
    rows[m] = [json.loads(l) for l in gzip.open(os.path.join(D, f"e3_slim_{m}.jsonl.gz"), "rt")]


def cell(v, label=None):
    s = E.stats([r["fill_honest_walk_r"] for r in v])
    if not s["n"]:
        return {"n": 0}
    cost = E.mean([r.get("cost_r") or 0 for r in v]); spr = E.mean([r.get("spread_r") or 0 for r in v])
    hon = s["mean"]; zn = E.mean([E.hz(r) for r in v])
    res = [r for r in v if r["fill_honest_which_came_first"] in ("stop", "target")]
    return {"n": s["n"], "honest": hon, "se": s["se"], "t": s["t"], "zn": zn,
            "resolved_n": len(res), "resolved_mean": E.mean([r["fill_honest_walk_r"] for r in res]),
            "resolved_win": (sum(1 for r in res if r["fill_honest_which_came_first"] == "target") / len(res)) if res else None,
            "mean_cost_r": cost, "mean_spread_r": spr,
            "net_at_frozen": hon - cost,
            "net_at_spread_div_7p3": hon - (cost - spr * (1 - 1 / 7.3)),
            "net_at_spread_div_8p5": hon - (cost - spr * (1 - 1 / 8.5)),
            "zn_net_at_spread_div_7p3": zn - (cost - spr * (1 - 1 / 7.3))}


FAR = lambda r: (r.get("dist_r") or -9) >= THR
CHEAP = lambda r: (r.get("cost_r") if r.get("cost_r") is not None else 9) <= COSTCAP

for m, _ in MONTHS:
    tk = [r for r in rows[m] if r["takeable"]]
    OUT.setdefault("by_month", {})[m] = {
        "takeable": cell(tk),
        "cheap_far_CELL": cell([r for r in tk if CHEAP(r) and FAR(r)]),
        "cheap_near": cell([r for r in tk if CHEAP(r) and not FAR(r)]),
        "expensive_far": cell([r for r in tk if not CHEAP(r) and FAR(r)]),
        "expensive_near": cell([r for r in tk if not CHEAP(r) and not FAR(r)]),
        "cheap_far_FRESH_FIRST": cell([r for r in tk if CHEAP(r) and FAR(r)
                                       and r.get("entry_traded_prior_24h") and r.get("is_first_emission")]),
    }
allt = [r for m, _ in MONTHS for r in rows[m] if r["takeable"]]
OUT["pooled"] = {k: cell([r for r in allt if f(r)]) for k, f in (
    ("takeable", lambda r: True),
    ("cheap_far_CELL", lambda r: CHEAP(r) and FAR(r)),
    ("cheap_near", lambda r: CHEAP(r) and not FAR(r)),
    ("expensive_far", lambda r: not CHEAP(r) and FAR(r)),
    ("expensive_near", lambda r: not CHEAP(r) and not FAR(r)),
    ("cheap_far_FRESH_FIRST", lambda r: CHEAP(r) and FAR(r) and r.get("entry_traded_prior_24h") and r.get("is_first_emission")),
)}

# ------------------------------------------------------------ extended horizons on raw M1
def rewalk(sub, ym, horizons):
    acc = {h: [] for h in horizons}
    which = {h: collections.Counter() for h in horizons}
    for r in sub:
        b = E.bars(r["symbol"], ym)
        if b is None:
            continue
        T = b["t"]; dt = r["decision_time_utc"]
        entry = r["entry_price"]; d = r["risk_distance"]
        if not d:
            continue
        is_long = (r.get("side") or "").upper() == "LONG"
        tgt = r.get("policy_target_r_used") or 2.0
        j0 = bisect.bisect_right(T, dt)
        for h in horizons:
            wall = E._plus_minutes(dt, h)
            j1 = min(len(T), bisect.bisect_right(T, wall))
            fi = None; val = 0.0; w = "no_fill"; lastc = None
            for k in range(j0, j1):
                hi, lo, cl = b["h"][k], b["l"][k], b["c"][k]
                if is_long:
                    f, a, cr = (hi - entry) / d, (lo - entry) / d, (cl - entry) / d
                else:
                    f, a, cr = (entry - lo) / d, (entry - hi) / d, (entry - cl) / d
                f = round(f, 4); a = round(a, 4); cr = round(cr, 4)
                lastc = cr
                if fi is None:
                    if a <= 1e-12:
                        fi = k
                    else:
                        continue
                if a <= -1.0 + 1e-12:
                    val, w = -1.0, "stop"
                    break
                if f >= tgt - 1e-12:
                    val, w = tgt, "target"
                    break
            else:
                if fi is not None:
                    val, w = (lastc if lastc is not None else 0.0), "neither"
            acc[h].append(val)
            which[h][w] += 1
    return {str(h): {"n": len(acc[h]), "mean": E.mean(acc[h]),
                     "zn": E.mean([0.0 if wv in ("neither", "no_fill") else v
                                   for v, wv in zip(acc[h], [])]) if False else None,
                     "which": dict(which[h])} for h in horizons}


for m, ym in MONTHS:
    tk = [r for r in rows[m] if r["takeable"]]
    OUT.setdefault("horizon", {}).setdefault(m, {})["cheap_far_CELL"] = rewalk(
        [r for r in tk if CHEAP(r) and FAR(r)], ym, HORIZONS)
    OUT["horizon"][m]["cheap_near"] = rewalk([r for r in tk if CHEAP(r) and not FAR(r)], ym, HORIZONS)
    E.drop_cache()

json.dump(OUT, open(os.path.join(D, "E3_CELL_V1.json"), "w"), indent=1, default=str)

print(f"{'month':>6} {'cell n':>7} {'honest':>8} {'t':>6} {'zn':>8} {'resWin%':>7} {'cost':>6} {'net@/7.3':>9} | "
      f"{'cheapNear n':>11} {'honest':>8} {'net@/7.3':>9}")
for m, _ in MONTHS:
    a = OUT["by_month"][m]["cheap_far_CELL"]; b = OUT["by_month"][m]["cheap_near"]
    print(f"{m:>6} {a['n']:>7} {a['honest']:>+8.4f} {(a['t'] or 0):>+6.2f} {a['zn']:>+8.4f} "
          f"{100*(a['resolved_win'] or 0):>7.1f} {a['mean_cost_r']:>6.3f} {a['net_at_spread_div_7p3']:>+9.4f} | "
          f"{b['n']:>11} {b['honest']:>+8.4f} {b['net_at_spread_div_7p3']:>+9.4f}")
print("POOLED:")
for k, v in OUT["pooled"].items():
    if not v.get("n"):
        continue
    print(f"   {k:>24} n {v['n']:>6} hon {v['honest']:+.4f} t {(v['t'] or 0):+.2f} zn {v['zn']:+.4f} "
          f"resWin {100*(v['resolved_win'] or 0):.1f}% cost {v['mean_cost_r']:.3f} net@/7.3 {v['net_at_spread_div_7p3']:+.4f}")
print("HORIZON (mean R, fill-honest, raw M1 beyond the 2 h wall):")
for m, _ in MONTHS:
    for coh in ("cheap_far_CELL", "cheap_near"):
        h = OUT["horizon"][m][coh]
        print(f"   {m} {coh:>16} " + " ".join(f"{k}m n{v['n']} {v['mean']:+.4f}" for k, v in h.items()))
