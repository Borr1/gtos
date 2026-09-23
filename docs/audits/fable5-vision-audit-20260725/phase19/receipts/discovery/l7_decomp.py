#!/usr/bin/env python3
"""l7_decomp — separate GEOMETRY from DIRECTION in the at-market inversion.

Directional information content of the signal, measured symmetrically:
    info = (inv_atm_r - orig_atm_r) / 2        (positive => the sign is INVERTED)
because orig and inv are exact mirrors at the same entry with the same risk distance,
so their mean is the coin-flip baseline and half their spread is the whole signal.
"""
import gzip, json, os, collections, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["day"] = r["decision_time_utc"][:10]
mean = lambda v: sum(v)/len(v) if v else float("nan")

def dayboot(v, key="info", B=2000, seed=7):
    """Block bootstrap over decision days -- the honest unit given intraday correlation."""
    rnd = random.Random(seed)
    byday = collections.defaultdict(list)
    for r in v: byday[r["day"]].append(r[key])
    days = list(byday)
    if len(days) < 3: return None
    obs = mean([x for d in days for x in byday[d]])
    out = []
    for _ in range(B):
        s = []
        for _ in range(len(days)): s.extend(byday[rnd.choice(days)])
        out.append(mean(s))
    out.sort()
    return dict(obs=obs, lo=out[int(.025*B)], hi=out[int(.975*B)],
                p_le0=sum(1 for x in out if x <= 0)/B, n_days=len(days))

res = {}
# ---- 1. born_state decomposition, geometry-free cell isolated
tab = []
g = collections.defaultdict(list)
for r in rows: g[r["born_state"]].append(r)
for k, v in sorted(g.items(), key=lambda x: -len(x[1])):
    bb = dayboot(v)
    tab.append(dict(born_state=k, n=len(v), n_first=sum(1 for r in v if r["is_first_emission"]),
        orig_atm=mean([r["orig_atm_r"] for r in v]), inv_atm=mean([r["inv_atm_r"] for r in v]),
        info=mean([r["info"] for r in v]),
        info_first=mean([r["info"] for r in v if r["is_first_emission"]]),
        orig_win=sum(1 for r in v if r["orig_atm_r"] > 1e-9)/len(v),
        inv_win=sum(1 for r in v if r["inv_atm_r"] > 1e-9)/len(v),
        boot=bb))
res["by_born_state"] = tab

# ---- 2. mkt_r bucket sweep: is the resting inversion geometry or signal?
buckets = [(-99,-3),(-3,-2),(-2,-1),(-1,-0.5),(-0.5,-1e-9),(-1e-9,1e-9),(1e-9,0.5),(0.5,1),(1,2),(2,3),(3,5),(5,99)]
tab = []
for lo, hi in buckets:
    v = [r for r in rows if lo < r["mkt_r_prev_close"] <= hi]
    if len(v) < 20: 
        tab.append(dict(lo=lo, hi=hi, n=len(v))); continue
    bb = dayboot(v)
    tab.append(dict(lo=lo, hi=hi, n=len(v),
        orig_atm=mean([r["orig_atm_r"] for r in v]), inv_atm=mean([r["inv_atm_r"] for r in v]),
        info=mean([r["info"] for r in v]),
        inv_win=sum(1 for r in v if r["inv_atm_r"] > 1e-9)/len(v),
        geom_free=bool(hi <= 2.0 and lo >= -2.0), boot=bb))
res["by_mkt_r_bucket"] = tab

# ---- 3. the geometry-free population: mkt_r == 0 exactly (entry IS the market)
atl = [r for r in rows if r["born_state"] == "born_at_limit"]
res["at_limit_headline"] = dict(n=len(atl), orig=mean([r["orig_atm_r"] for r in atl]),
    inv=mean([r["inv_atm_r"] for r in atl]), info=mean([r["info"] for r in atl]),
    boot=dayboot(atl), boot_first=dayboot([r for r in atl if r["is_first_emission"]]))

# ---- 4. family x born_state info
tab = []
g = collections.defaultdict(list)
for r in rows: g[(r["family"], r["born_state"])].append(r)
for (f, b), v in g.items():
    if len(v) < 30: continue
    tab.append(dict(family=f, born_state=b, n=len(v), info=mean([r["info"] for r in v]),
        orig_atm=mean([r["orig_atm_r"] for r in v]), inv_atm=mean([r["inv_atm_r"] for r in v]),
        inv_win=sum(1 for r in v if r["inv_atm_r"] > 1e-9)/len(v)))
tab.sort(key=lambda x: -x["info"])
res["family_x_born"] = tab

json.dump(res, open(os.path.join(HERE, "L7_DECOMP_V1.json"), "w"), indent=1)

print("=== 1. BORN STATE: at-market original vs inverse, and the DIRECTIONAL INFO ===")
print(f"{'born_state':16s} {'n':>6s} {'origATM':>8s} {'oWin':>6s} {'invATM':>8s} {'iWin':>6s} {'INFO':>8s} {'info95lo':>9s} {'info95hi':>9s} {'infoFirst':>9s}")
for t in res["by_born_state"]:
    b = t["boot"] or {}
    print(f"{t['born_state']:16s} {t['n']:6d} {t['orig_atm']:+8.4f} {t['orig_win']:6.2%} {t['inv_atm']:+8.4f} {t['inv_win']:6.2%} "
          f"{t['info']:+8.4f} {b.get('lo',float('nan')):+9.4f} {b.get('hi',float('nan')):+9.4f} {t['info_first']:+9.4f}")
print("\n=== 2. mkt_r BUCKET: geometry (|mkt_r|>2 => inverse target nearer than the limit) vs signal ===")
print(f"{'bucket':>14s} {'n':>6s} {'origATM':>8s} {'invATM':>8s} {'iWin':>7s} {'INFO':>8s} {'95lo':>8s} {'95hi':>8s} {'geomfree':>8s}")
for t in res["by_mkt_r_bucket"]:
    if "info" not in t: print(f"{('(%g,%g]'%(t['lo'],t['hi'])):>14s} {t['n']:6d}   (n<20)"); continue
    b = t["boot"] or {}
    print(f"{('(%g,%g]'%(t['lo'],t['hi'])):>14s} {t['n']:6d} {t['orig_atm']:+8.4f} {t['inv_atm']:+8.4f} {t['inv_win']:7.2%} "
          f"{t['info']:+8.4f} {b.get('lo',float('nan')):+8.4f} {b.get('hi',float('nan')):+8.4f} {str(t['geom_free']):>8s}")
h = res["at_limit_headline"]
print(f"\n=== 3. GEOMETRY-FREE POPULATION (entry == market, mkt_r == 0 exactly), n={h['n']} ===")
print(f"  orig_atm {h['orig']:+.4f}   inv_atm {h['inv']:+.4f}   INFO {h['info']:+.4f}")
print(f"  day-block bootstrap  95% [{h['boot']['lo']:+.4f}, {h['boot']['hi']:+.4f}]  p(<=0)={h['boot']['p_le0']:.4f}  days={h['boot']['n_days']}")
print(f"  first-emission only  95% [{h['boot_first']['lo']:+.4f}, {h['boot_first']['hi']:+.4f}]  p(<=0)={h['boot_first']['p_le0']:.4f}")
