#!/usr/bin/env python3
"""l7_mech — three sharp mechanism questions on the CLEAN at-market population.
 M1 does the inversion depend on stop width (risk distance)?   -- decision-time observable
 M2 the London exception: which families/hours does the ORIGINAL direction actually work in?
 M3 what is the inverse WORTH net of cost, at the frozen model and at the measured 7.3-8.5x
    spread over-charge correction?
"""
import gzip, json, os, collections, random
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["day"] = r["decision_time_utc"][:10]
CLEAN = [r for r in rows if r["born_state"] == "born_at_limit"]
mean = lambda v: sum(v)/len(v) if v else float("nan")
def dayboot(v, f, B=800, seed=5):
    rnd = random.Random(seed); byday = collections.defaultdict(list)
    for r in v: byday[r["day"]].append(r)
    days = list(byday); out = []
    for _ in range(B):
        s = []
        for _ in range(len(days)): s.extend(byday[rnd.choice(days)])
        out.append(f(s))
    out.sort(); return dict(lo=out[int(.025*B)], hi=out[int(.975*B)], p_le0=sum(1 for x in out if x<=0)/B)
res = {}

# ---- M1: risk-distance quintiles, within family (so it is not a family proxy)
byfam = collections.defaultdict(list)
for r in CLEAN: byfam[r["family"]].append(r)
tab = []
for fam, v in byfam.items():
    v2 = sorted([r for r in v if r["rd_pct"] is not None], key=lambda r: r["rd_pct"])
    if len(v2) < 250: continue
    k = len(v2)//5
    for q in range(5):
        s = v2[q*k:(q+1)*k] if q < 4 else v2[4*k:]
        tab.append(dict(family=fam, quintile=q+1, n=len(s),
            rd_pct_med=sorted(r["rd_pct"] for r in s)[len(s)//2],
            orig=mean([r["orig_atm_r"] for r in s]), inv=mean([r["inv_atm_r"] for r in s]),
            info=mean([r["info"] for r in s]), orig_win=sum(1 for r in s if r["orig_atm_r"]>1e-9)/len(s)))
res["M1_risk_distance_quintiles"] = tab
# pooled across families, rank-within-family quintile
pooled = collections.defaultdict(list)
for t in tab: pooled[t["quintile"]].append(t)
res["M1_pooled"] = [dict(quintile=q, n=sum(x["n"] for x in v),
    info=sum(x["info"]*x["n"] for x in v)/sum(x["n"] for x in v),
    orig=sum(x["orig"]*x["n"] for x in v)/sum(x["n"] for x in v),
    inv=sum(x["inv"]*x["n"] for x in v)/sum(x["n"] for x in v)) for q, v in sorted(pooled.items())]

# ---- M2: London exception
tab = []
for sess in ("london","ny","tokyo","off_configured_session"):
    v = [r for r in CLEAN if r["route_session"] == sess]
    b = dayboot(v, lambda s: mean([r["info"] for r in s]))
    tab.append(dict(scope="session", key=sess, n=len(v), orig=mean([r["orig_atm_r"] for r in v]),
        inv=mean([r["inv_atm_r"] for r in v]), info=mean([r["info"] for r in v]), **{"boot":b}))
for fam in byfam:
    for sess in ("london","ny","tokyo","off_configured_session"):
        v = [r for r in CLEAN if r["family"]==fam and r["route_session"]==sess]
        if len(v) < 60: continue
        tab.append(dict(scope="family_x_session", key=f"{fam}|{sess}", n=len(v),
            orig=mean([r["orig_atm_r"] for r in v]), inv=mean([r["inv_atm_r"] for r in v]),
            info=mean([r["info"] for r in v]), boot=None))
res["M2_session"] = tab
hh = []
for h in range(24):
    v = [r for r in CLEAN if r["hour"] == h]
    if len(v) < 60: continue
    hh.append(dict(hour=h, n=len(v), orig=mean([r["orig_atm_r"] for r in v]),
        inv=mean([r["inv_atm_r"] for r in v]), info=mean([r["info"] for r in v]),
        orig_win=sum(1 for r in v if r["orig_atm_r"]>1e-9)/len(v)))
res["M2_hour"] = hh

# ---- M3: net economics of the inverse
def net(v, key, div):
    return mean([r[key] - (r["cost_r"] - r["spread_r"] + r["spread_r"]/div) for r in v])
tab = []
for lab, v in (("CLEAN_at_limit", CLEAN), ("CLEAN_off_session", [r for r in CLEAN if r["route_session"]=="off_configured_session"]),
               ("CLEAN_structural_distance_extreme", [r for r in CLEAN if r["family"]=="structural_distance_extreme"]),
               ("CLEAN_lo_vol", [r for r in CLEAN if r["vol_state"]=="lo_vol"]),
               ("CLEAN_sde_offsession", [r for r in CLEAN if r["family"]=="structural_distance_extreme" and r["route_session"]=="off_configured_session"])):
    tab.append(dict(pop=lab, n=len(v), cost_frozen=mean([r["cost_r"] for r in v]),
        cost_spread=mean([r["spread_r"] for r in v]),
        inv_gross=mean([r["inv_atm_r"] for r in v]), orig_gross=mean([r["orig_atm_r"] for r in v]),
        inv_net_frozen=net(v,"inv_atm_r",1.0), inv_net_sp73=net(v,"inv_atm_r",7.3),
        inv_net_sp85=net(v,"inv_atm_r",8.5), orig_net_sp73=net(v,"orig_atm_r",7.3)))
res["M3_net"] = tab
json.dump(res, open(os.path.join(HERE, "L7_MECH_V1.json"), "w"), indent=1)

print("=== M1 risk-distance quintile WITHIN family (pooled by rank) ===")
print(f"{'q':>2s} {'n':>6s} {'origATM':>9s} {'invATM':>9s} {'INFO':>9s}")
for t in res["M1_pooled"]: print(f"{t['quintile']:2d} {t['n']:6d} {t['orig']:+9.4f} {t['inv']:+9.4f} {t['info']:+9.4f}")
print("\n=== M1 by family, q1(tightest stop) vs q5(widest) ===")
print(f"{'family':34s} {'q1 rd%':>8s} {'q1 info':>8s} {'q5 rd%':>8s} {'q5 info':>8s} {'q5-q1':>8s}")
for fam in sorted(byfam):
    q = {t['quintile']: t for t in res["M1_risk_distance_quintiles"] if t["family"]==fam}
    if 1 not in q: continue
    print(f"{fam:34s} {q[1]['rd_pct_med']:8.4f} {q[1]['info']:+8.4f} {q[5]['rd_pct_med']:8.4f} {q[5]['info']:+8.4f} {q[5]['info']-q[1]['info']:+8.4f}")
print("\n=== M2 session (CLEAN) ===")
for t in [x for x in res["M2_session"] if x["scope"]=="session"]:
    print(f"  {t['key']:24s} n={t['n']:5d} origATM {t['orig']:+.4f} invATM {t['inv']:+.4f} INFO {t['info']:+.4f} 95CI [{t['boot']['lo']:+.4f},{t['boot']['hi']:+.4f}] p<=0 {t['boot']['p_le0']:.3f}")
print("\n=== M2 family x session where the ORIGINAL WORKS (info<0) ===")
for t in sorted([x for x in res["M2_session"] if x["scope"]=="family_x_session" and x["info"]<0], key=lambda x:x["info"]):
    print(f"  {t['key']:52s} n={t['n']:5d} origATM {t['orig']:+.4f} invATM {t['inv']:+.4f} INFO {t['info']:+.4f}")
print("\n=== M3 net economics ===")
print(f"{'population':34s} {'n':>5s} {'invGross':>9s} {'costFroz':>9s} {'invNetFr':>9s} {'invNet/7.3':>10s} {'invNet/8.5':>10s}")
for t in res["M3_net"]:
    print(f"{t['pop']:34s} {t['n']:5d} {t['inv_gross']:+9.4f} {t['cost_frozen']:9.4f} {t['inv_net_frozen']:+9.4f} {t['inv_net_sp73']:+10.4f} {t['inv_net_sp85']:+10.4f}")
