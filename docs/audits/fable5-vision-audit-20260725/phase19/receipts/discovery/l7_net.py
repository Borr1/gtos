#!/usr/bin/env python3
"""l7_net — is the inversion HARVESTABLE? Cost is R-denominated, so the tightest-stop cells
carry both the biggest inversion and the biggest cost. Sweep the same cells on NET."""
import gzip, json, os, collections, random, math
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in gzip.open(os.path.join(HERE, "l7_BASE.jsonl.gz"), "rt")]
rows = [r for r in rows if r["orig_atm_r"] is not None]
for r in rows:
    r["info"] = (r["inv_atm_r"] - r["orig_atm_r"]) / 2.0
    r["day"] = r["decision_time_utc"][:10]
    sp = r["spread_r"] or 0.0
    r["cost73"] = (r["cost_r"] - sp) + sp/7.3      # measured 7.3-8.5x spread over-charge, low end
    r["cost85"] = (r["cost_r"] - sp) + sp/8.5
    r["inv_net73"] = r["inv_atm_r"] - r["cost73"]
    r["inv_net85"] = r["inv_atm_r"] - r["cost85"]
    r["orig_net73"] = r["orig_atm_r"] - r["cost73"]
CLEAN = [r for r in rows if r["born_state"] == "born_at_limit"]
mean = lambda v: sum(v)/len(v) if v else float("nan")
def dayboot(v, f, B=800, seed=9):
    rnd = random.Random(seed); d = collections.defaultdict(list)
    for r in v: d[r["day"]].append(r)
    ks = list(d); out = []
    for _ in range(B):
        s = []
        for _ in range(len(ks)): s.extend(d[rnd.choice(ks)])
        out.append(f(s))
    out.sort(); return dict(lo=out[int(.025*B)], hi=out[int(.975*B)], p_le0=sum(1 for x in out if x <= 0)/B)
res = {}
# --- net by within-family risk-distance quintile
byfam = collections.defaultdict(list)
for r in CLEAN: byfam[r["family"]].append(r)
q = collections.defaultdict(list)
for fam, v in byfam.items():
    v2 = sorted([r for r in v if r["rd_pct"] is not None], key=lambda r: r["rd_pct"])
    if len(v2) < 250: continue
    k = len(v2)//5
    for i in range(5): q[i+1].extend(v2[i*k:(i+1)*k] if i < 4 else v2[4*k:])
res["net_by_quintile"] = [dict(quintile=i, n=len(v), rd_pct_med=sorted(r["rd_pct"] for r in v)[len(v)//2],
    info=mean([r["info"] for r in v]), inv_gross=mean([r["inv_atm_r"] for r in v]),
    cost_frozen=mean([r["cost_r"] for r in v]), cost73=mean([r["cost73"] for r in v]),
    inv_net73=mean([r["inv_net73"] for r in v]), inv_net85=mean([r["inv_net85"] for r in v]),
    orig_net73=mean([r["orig_net73"] for r in v]),
    boot=dayboot(v, lambda s: mean([x["inv_net73"] for x in s]))) for i, v in sorted(q.items())]
# --- full cell sweep on NET
DIMS = {"family": lambda r: r["family"], "symbol": lambda r: r["symbol"], "side": lambda r: r["side"],
        "session": lambda r: r["route_session"], "hour": lambda r: "h%02d" % r["hour"], "vol": lambda r: r["vol_state"]}
COMBOS = [("family",),("symbol",),("side",),("session",),("hour",),("vol",),("family","side"),("family","session"),
 ("family","symbol"),("family","hour"),("family","vol"),("symbol","side"),("symbol","session"),("symbol","vol"),
 ("side","session"),("side","vol"),("session","vol"),("session","hour"),("family","side","session"),
 ("family","side","vol"),("family","session","vol"),("family","symbol","side"),("symbol","side","session")]
cells = []
for combo in COMBOS:
    g = collections.defaultdict(list)
    for r in CLEAN: g[tuple(DIMS[d](r) for d in combo)].append(r)
    for kv, v in g.items():
        if len(v) < 40: continue
        cells.append(dict(dims="|".join(combo), key="|".join(map(str, kv)), n=len(v),
            info=mean([r["info"] for r in v]), inv_gross=mean([r["inv_atm_r"] for r in v]),
            cost73=mean([r["cost73"] for r in v]), inv_net73=mean([r["inv_net73"] for r in v]),
            inv_net85=mean([r["inv_net85"] for r in v]), orig_net73=mean([r["orig_net73"] for r in v]),
            rd_pct_med=sorted(r["rd_pct"] for r in v)[len(v)//2]))
cells.sort(key=lambda c: -c["inv_net73"])
for c in cells[:60]:
    combo = tuple(c["dims"].split("|")); kv = tuple(c["key"].split("|"))
    v = [r for r in CLEAN if tuple(str(DIMS[d](r)) for d in combo) == kv]
    c["boot"] = dayboot(v, lambda s: mean([x["inv_net73"] for x in s]))
res["net_cells"] = cells
json.dump(res, open(os.path.join(HERE, "L7_NET_V1.json"), "w"), indent=1)
print("=== NET by within-family risk-distance quintile (CLEAN at-market) ===")
print(f"{'q':>2s} {'n':>6s} {'rd%med':>8s} {'INFO':>8s} {'invGross':>9s} {'costFroz':>9s} {'cost/7.3':>9s} {'invNet73':>9s} {'95lo':>8s} {'origNet73':>10s}")
for t in res["net_by_quintile"]:
    print(f"{t['quintile']:2d} {t['n']:6d} {t['rd_pct_med']:8.4f} {t['info']:+8.4f} {t['inv_gross']:+9.4f} {t['cost_frozen']:9.4f} "
          f"{t['cost73']:9.4f} {t['inv_net73']:+9.4f} {t['boot']['lo']:+8.4f} {t['orig_net73']:+10.4f}")
print(f"\n=== TOP 22 CELLS BY NET INVERSE (spread/7.3), n>=40, of {len(cells)} cells ===")
print(f"{'dims':26s} {'key':32s} {'n':>5s} {'rd%':>7s} {'invG':>7s} {'cost':>6s} {'NET':>8s} {'95lo':>8s} {'totR':>7s}")
for c in cells[:22]:
    b = c.get("boot") or {}
    print(f"{c['dims'][:26]:26s} {c['key'][:32]:32s} {c['n']:5d} {c['rd_pct_med']:7.3f} {c['inv_gross']:+7.3f} "
          f"{c['cost73']:6.3f} {c['inv_net73']:+8.4f} {b.get('lo',float('nan')):+8.4f} {c['inv_net73']*c['n']:+7.1f}")
pos = [c for c in cells if c["inv_net73"] > 0]
print(f"\ncells with POSITIVE net inverse at spread/7.3: {len(pos)} of {len(cells)}")
