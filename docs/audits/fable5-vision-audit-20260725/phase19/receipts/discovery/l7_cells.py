#!/usr/bin/env python3
"""l7_cells — the definitive inversion table, on the population where an inversion MEANS something.

CLEAN population = born_at_limit (entry_price == the decision-instant market price, mkt_r == 0):
  * geometry-free  -- the inverse target is exactly 2R away, same as the original's
  * selection-free -- the fill is instantaneous, so the pool's fill-conditioning (path_final_r
                      :60309-60310 returns None for anything not `filled*`, and the pool filter
                      drops None) cannot have selected on the path
  * both sides fill at bar 1, same risk distance, +2R/-1R, same conservative same-bar tie rule
So info = (inv_atm_r - orig_atm_r)/2 is the whole directional content of the signal, sign-flipped.
"""
import gzip, json, os, collections, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["day"] = r["decision_time_utc"][:10]
mean = lambda v: sum(v)/len(v) if v else float("nan")
BE = 1.0/3.0   # flat +2R/-1R at market

def binom_p_less(k, n, p):
    lg = math.lgamma; t = 0.0
    for i in range(k+1):
        t += math.exp(lg(n+1)-lg(i+1)-lg(n-i+1)+i*math.log(p)+(n-i)*math.log(1-p))
    return min(1.0, t)

def dayboot(v, B=1000, seed=3):
    rnd = random.Random(seed); byday = collections.defaultdict(list)
    for r in v: byday[r["day"]].append(r["info"])
    days = list(byday)
    if len(days) < 4: return None
    out = []
    for _ in range(B):
        s = []
        for _ in range(len(days)): s.extend(byday[rnd.choice(days)])
        out.append(sum(s)/len(s))
    out.sort()
    return dict(lo=out[int(.025*B)], hi=out[int(.975*B)], p_le0=sum(1 for x in out if x <= 0)/B, days=len(days))

DIMS = {"family": lambda r: r["family"], "symbol": lambda r: r["symbol"], "side": lambda r: r["side"],
        "session": lambda r: r["route_session"], "hour": lambda r: "h%02d" % r["hour"], "vol": lambda r: r["vol_state"]}
COMBOS = [("family",),("symbol",),("side",),("session",),("hour",),("vol",),
 ("family","side"),("family","session"),("family","symbol"),("family","hour"),("family","vol"),
 ("symbol","side"),("symbol","session"),("symbol","hour"),("symbol","vol"),
 ("side","session"),("side","hour"),("side","vol"),("session","hour"),("session","vol"),("hour","vol"),
 ("family","side","session"),("family","symbol","side"),("family","side","vol"),("family","session","vol"),
 ("family","symbol","session"),("family","symbol","vol"),("family","side","hour"),
 ("symbol","side","session"),("symbol","side","vol"),("symbol","session","vol"),
 ("family","symbol","side","session"),("family","symbol","side","vol"),("family","symbol","side","session","vol")]
MINN = 30

def sweep(pop, label, boot_top=140):
    cells = []
    for combo in COMBOS:
        g = collections.defaultdict(list)
        for r in pop: g[tuple(DIMS[d](r) for d in combo)].append(r)
        for kv, v in g.items():
            if len(v) < MINN: continue
            ow = sum(1 for r in v if r["orig_atm_r"] > 1e-9); n = len(v)
            iw = sum(1 for r in v if r["inv_atm_r"] > 1e-9)
            cells.append(dict(dims="|".join(combo), key="|".join(map(str, kv)), n=n,
                n_first=sum(1 for r in v if r["is_first_emission"]), n_days=len({r["day"] for r in v}),
                orig_atm=mean([r["orig_atm_r"] for r in v]), inv_atm=mean([r["inv_atm_r"] for r in v]),
                orig_win=ow/n, inv_win=iw/n, be=BE, deficit=BE-ow/n, score=(BE-ow/n)*n,
                p_win_below_be=binom_p_less(ow, n, BE),
                info=mean([r["info"] for r in v]), info_total_R=mean([r["info"] for r in v])*n,
                info_first=mean([r["info"] for r in v if r["is_first_emission"]]) if any(r["is_first_emission"] for r in v) else None,
                past_stop_share=sum(1 for r in v if r["born_state"]=="born_past_stop")/n,
                resting_share=sum(1 for r in v if r["born_state"]=="born_resting")/n))
    cells.sort(key=lambda c: -abs(c["info"])*c["n"])
    idx = {(c["dims"], c["key"]): c for c in cells}
    for c in cells[:boot_top]:
        combo = tuple(c["dims"].split("|")); kv = tuple(c["key"].split("|"))
        v = [r for r in pop if tuple(str(DIMS[d](r)) for d in combo) == kv]
        c["boot"] = dayboot(v)
    # BH q over the bootstrap-tested set
    tested = [c for c in cells[:boot_top] if c.get("boot")]
    tested.sort(key=lambda c: c["boot"]["p_le0"])
    m = len(tested)
    for i, c in enumerate(tested, 1):
        c["bh_q"] = min(1.0, c["boot"]["p_le0"]*m/i)
    return dict(label=label, n_cells=len(cells), n_tested=m, cells=cells)

pops = {"CLEAN_at_limit": [r for r in rows if r["born_state"] == "born_at_limit"],
        "ALL": rows,
        "EX_PAST_STOP": [r for r in rows if r["born_state"] != "born_past_stop"]}
out = {k: sweep(v, k) for k, v in pops.items()}
json.dump(out, open(os.path.join(HERE, "L7_CELLS_V1.json"), "w"), indent=1)
for k in out: print(k, "cells", out[k]["n_cells"], "bootstrapped", out[k]["n_tested"])
c = out["CLEAN_at_limit"]["cells"]
print(f"\n=== CLEAN (born_at_limit, n={len(pops['CLEAN_at_limit'])}) TOP 26 by |info|*n ===")
print(f"{'dims':28s} {'key':34s} {'n':>5s} {'oATM':>7s} {'oWin':>6s} {'iATM':>7s} {'iWin':>6s} {'INFO':>7s} {'95lo':>7s} {'totR':>7s} {'q':>6s}")
for x in c[:26]:
    b = x.get("boot") or {}
    print(f"{x['dims'][:28]:28s} {x['key'][:34]:34s} {x['n']:5d} {x['orig_atm']:+7.3f} {x['orig_win']:6.1%} "
          f"{x['inv_atm']:+7.3f} {x['inv_win']:6.1%} {x['info']:+7.4f} {b.get('lo',float('nan')):+7.4f} "
          f"{x['info_total_R']:+7.1f} {x.get('bh_q',float('nan')):6.3f}")
