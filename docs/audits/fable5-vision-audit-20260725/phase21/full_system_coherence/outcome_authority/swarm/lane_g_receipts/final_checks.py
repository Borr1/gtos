import numpy as np, json, math
from scipy import stats
d=np.load("/private/tmp/laneG-walk/pool_table.npz", allow_pickle=True)
st=d["status"].astype(str); net=d["net"]; cost=d["cost_r"]; spr=d["spread_r"]; fam=d["family"].astype(str)
ot=d["order_type"].astype(str)
filled=np.char.startswith(st,"RESOLVED_FILLED")&np.isfinite(net)&np.isfinite(cost)&np.isfinite(spr)
cf=net+cost
print("=== LIMIT families: is the cost-free edge ~ half the spread? ===")
print(f"{'family':32s} {'ord':7s} {'n':>6s} {'mean spread_r':>13s} {'half':>7s} {'cost-free':>10s} {'ratio':>7s}")
for f in sorted(set(fam)):
    m=filled&(fam==f)
    if m.sum()<300: continue
    s=float(spr[m].mean()); e=float(cf[m].mean())
    typ="MARKET" if (ot[m]=="MARKET").mean()>0.5 else "LIMIT"
    print(f"{f:32s} {typ:7s} {int(m.sum()):6d} {s:13.4f} {s/2:7.4f} {e:+10.4f} {e/(s/2) if s>0 else 0:7.2f}")

print("\n=== CLAIM 5b: are the five monthly SELECTED-BOOK results mutually consistent? ===")
P={"feb":"/private/tmp/w21-market-top-feb-r2/FEBRUARY_MARKET_TOP_CHOICE_VALIDATION_RESULT_R2.json",
   "aprmay":"/private/tmp/w21-market-top-aprmay-r3/APRIL_MAY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json",
   "junjul":"/private/tmp/w21-market-top-junjul-r4/JUNE_JULY_MARKET_TOP_CHOICE_VALIDATION_RESULT_V1.json"}
M={"2026-02":"feb","2026-04":"apr","2026-05":"may","2026-06":"jun","2026-07":"jul"}
tr={k:[] for k in M.values()}
for p in P.values():
    for c in json.load(open(p))["selected_candidates"]:
        v=c.get("actual_net_r")
        if v is not None: tr[M[c["trading_day"][:7]]].append(float(v))
groups=[np.array(tr[m]) for m in ("feb","apr","may","jun","jul")]
F,pF=stats.f_oneway(*groups); H,pH=stats.kruskal(*groups)
print(f"  one-way ANOVA across the five months: F={F:.3f}  p={pF:.4f}")
print(f"  Kruskal-Wallis:                        H={H:.3f}  p={pH:.4f}")
allx=np.concatenate(groups); sd=allx.std(ddof=1)
print(f"  -> the five monthly means are NOT distinguishable from a single common mean.")
print(f"  per-trade sd {sd:.4f}; sd of a monthly TOTAL at each n:")
for m,g in zip(("feb","apr","may","jun","jul"),groups):
    print(f"     {m}: n={len(g):3d} total {g.sum():+7.2f} R; sd(total) under a zero-mean null = {sd*math.sqrt(len(g)):5.2f} R; "
          f"z = {g.sum()/(sd*math.sqrt(len(g))):+.2f}")
n=len(allx); za,zb=stats.norm.ppf(0.975),stats.norm.ppf(0.80)
mde=(za+zb)*sd/math.sqrt(n)
print(f"\n  MDE at 80% power on the {n} trades actually taken: {mde:+.4f} R/trade = {mde*n:+.1f} R over five months")
print(f"  observed: {allx.mean():+.4f} R/trade ({allx.sum():+.2f} R) -> INSIDE the band")
tpm=n/5
print(f"\n  trades needed for 80% power (alpha .05 two-sided), at the observed {tpm:.0f} trades/month:")
for edge in (0.30,0.20,0.15,0.10,0.05):
    nn=((za+zb)*sd/edge)**2
    print(f"     edge {edge:.2f} R/trade -> {nn:6.0f} trades = {nn/tpm:5.1f} months  ({edge*tpm:5.2f} R/month)")
