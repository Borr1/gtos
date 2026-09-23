"""p1 step 5 — THE CANDIDATE REGISTER.

Every wave-19 candidate finding I can measure on the 8-window panel, per window,
decomposed into EDGE (gross) and COST (toll), with the b1 post-mortem arithmetic:

    d_net(m -> m') = d_gross - d_cost

plus chronological split (first four windows vs last four) and an OLS slope in R
per month, and -- for at-market cohorts -- the paired directional SIGNAL against the
exact mirror arm (zero Monte-Carlo control).
"""
from __future__ import annotations
import numpy as np, json, sys
sys.path.insert(0, "/tmp/p1")
import p1_lib as L

ws, SYMS = L.load_all()
NW = len(ws)
SI = {s: i for i, s in enumerate(SYMS)}
FA = L.FAMS

def stat(w, m, label):
    g = w.g[m]; c = w.c[m]
    if len(g) == 0:
        return dict(window=w.w, n=0)
    d = dict(window=w.w, n=int(len(g)), gross=float(g.mean()), cost=float(c.mean()),
             net=float((g - c).mean()), wr=float((g > 0).mean()),
             d_bps=float(np.median(w.d_bps[m])))
    # paired mirror signal, at-market rows only (mirror of a resting limit is an artifact)
    a = m & (w.atm == 1) & (w.fil == 1)
    if a.sum() > 30:
        d["signal_atm"] = float((w.g[a] - w.gm[a]).mean())
        d["n_signal"] = int(a.sum())
    return d

def series(name, maskfn, note=""):
    rows = [stat(w, maskfn(w), name) for w in ws]
    ok = [r for r in rows if r["n"] > 0]
    if len(ok) < 4: return None
    x = np.arange(len(ok), dtype=float)
    def sl(f):
        y = np.array([r[f] for r in ok])
        b = np.polyfit(x, y, 1)[0]
        return float(b)
    first = ok[:len(ok) // 2]; last = ok[len(ok) // 2:]
    W = lambda rs, f: float(np.average([r[f] for r in rs], weights=[r["n"] for r in rs]))
    out = dict(name=name, note=note, per_window=ok,
               pooled=dict(n=int(sum(r["n"] for r in ok)),
                           gross=W(ok, "gross"), cost=W(ok, "cost"), net=W(ok, "net")),
               first_half=dict(gross=W(first, "gross"), cost=W(first, "cost"), net=W(first, "net"),
                               n=int(sum(r["n"] for r in first)), windows=[r["window"] for r in first]),
               last_half=dict(gross=W(last, "gross"), cost=W(last, "cost"), net=W(last, "net"),
                              n=int(sum(r["n"] for r in last)), windows=[r["window"] for r in last]),
               slope_per_month=dict(gross=sl("gross"), cost=sl("cost"), net=sl("net")),
               months_gross_pos=int(sum(1 for r in ok if r["gross"] > 0)),
               months_net_pos=int(sum(1 for r in ok if r["net"] > 0)))
    out["decay"] = dict(d_gross=out["last_half"]["gross"] - out["first_half"]["gross"],
                        d_cost=out["last_half"]["cost"] - out["first_half"]["cost"],
                        d_net=out["last_half"]["net"] - out["first_half"]["net"])
    out["decay"]["cost_share_of_d_net"] = (-out["decay"]["d_cost"] / out["decay"]["d_net"]
                                           if out["decay"]["d_net"] else float("nan"))
    sg = [r.get("signal_atm") for r in ok if "signal_atm" in r]
    if len(sg) >= 4:
        out["signal_atm"] = dict(per_window=sg, mean=float(np.mean(sg)),
                                 months_pos=int(sum(1 for v in sg if v > 0)),
                                 first_half=float(np.mean(sg[:len(sg) // 2])),
                                 last_half=float(np.mean(sg[len(sg) // 2:])))
    return out

F = lambda w: w.fil == 1
CLEAN = lambda w: (w.fil == 1) & (w.past == 0) & (w.fam != 1)
CAND = {}

def add(name, fn, note=""):
    r = series(name, fn, note)
    if r: CAND[name] = r

add("BASE_all_fills", F, "f1 roster, honest fill, target 2.0R")
add("BASE_clean_fills", CLEAN, "f1 clean roster: no born-past-stop, no breaker family")
add("BASE_at_market", lambda w: F(w) & (w.atm == 1), "seven at-market families")
add("BASE_poi", lambda w: F(w) & (w.atm == 0), "three POI resting-limit families")
add("f1_REPAIR_drop_breaker", lambda w: F(w) & (w.fam != 1), "f1: remove current_breaker_re_entry")
add("f1_REPAIR_drop_paststop", lambda w: F(w) & (w.past == 0), "f1: remove born-past-stop rows")
add("f1_DEFECT_breaker_only", lambda w: F(w) & (w.fam == 1), "the defective family alone")
add("d7_REPAIR_poi_level_at_market_removed",
    lambda w: F(w) & ~((w.atm == 0) & (w.rtouch_zero())) if hasattr(w, 'rtouch_zero') else F(w))
for fi, fn in enumerate(FA):
    if fn == "__other__": continue
    add(f"FAMILY_{fn}", lambda w, fi=fi: F(w) & (w.fam == fi), "single family")
# b1's two limbs, now on 8 windows instead of 5
B1I = [SI[s] for s in ("GER40", "NAS100", "US30_cash") if s in SI]
add("b1_LIMB_instruments", lambda w: CLEAN(w) & np.isin(w.sym, B1I),
    "b1-BOOK-V1 instrument limb {GER40,NAS100,US30_cash}, 3 more windows than b1 had")
add("b1_LIMB_inst_cheap_hours", lambda w: CLEAN(w) & np.isin(w.sym, B1I) & (w.c <= np.quantile(w.c[CLEAN(w)], 0.25)),
    "instrument limb AND cheapest cost quartile of that window")
add("b1_LIMB_inst_expensive_hours", lambda w: CLEAN(w) & np.isin(w.sym, B1I) & (w.c > np.quantile(w.c[CLEAN(w)], 0.25)),
    "instrument limb AND the rest")
# affordability thresholds (f2's cost-cap sweep, on the roster)
for cap in (0.30, 0.15, 0.10, 0.05, 0.03):
    add(f"COSTCAP_{cap:.2f}", lambda w, cap=cap: CLEAN(w) & (w.c <= cap), "f2 cost-cap sweep")
# d1b's cheapest-toll decile
add("CHEAPEST_TOLL_DECILE", lambda w: CLEAN(w) & (w.c <= np.quantile(w.c[CLEAN(w)], 0.10)),
    "d1b's killed cheapest-decile result, re-tested for persistence")
# risk-distance deciles as a persistence axis
for lo, hi in ((0.0, 0.1), (0.4, 0.5), (0.9, 1.0)):
    add(f"RISKDIST_{lo:.1f}_{hi:.1f}",
        lambda w, lo=lo, hi=hi: CLEAN(w) & (w.d_bps >= np.quantile(w.d_bps[CLEAN(w)], lo))
                                & (w.d_bps <= np.quantile(w.d_bps[CLEAN(w)], hi)), "stop-width decile")

json.dump(CAND, open("/tmp/p1/P1_CAND_V1.json", "w"))
for k, v in CAND.items():
    p = v["pooled"]; dc = v["decay"]
    sg = v.get("signal_atm", {})
    print(f"{k:42s} n{p['n']:>8d} gross {p['gross']:+.5f} cost {p['cost']:.5f} net {p['net']:+.5f} "
          f"| g+ {v['months_gross_pos']}/8 | first->last dg {dc['d_gross']:+.5f} dc {dc['d_cost']:+.5f} "
          f"dn {dc['d_net']:+.5f} | slope_g {v['slope_per_month']['gross']:+.5f}"
          + (f" | sig {sg['mean']:+.5f} ({sg['months_pos']}/8)" if sg else ""), flush=True)
print("WROTE /tmp/p1/P1_CAND_V1.json")
