"""If the tape is driftless then for ANY stop/target/horizon contract
   E[terminal_gross_r] = -E[spread_r]   exactly
because P&L = (tape travel to the stopping time) - one spread, and tape travel is a
martingale increment. This is a much stronger and much cleaner test than any hit-rate
benchmark: it needs no barrier distances, no horizon model and no volatility."""
import gzip, pickle, math, json
import numpy as np
from collections import Counter, defaultdict
MONTHS=["feb","apr","may","jun","jul"]
recs=[]
for mo in MONTHS:
    with gzip.open(f"/private/tmp/laneG-walk/lg_{mo}.pkl.gz","rb") as fh:
        for r in pickle.load(fh): r["month"]=mo; recs.append(r)

def rows_of(rows, arm, elig=False):
    out=[]
    for r in rows:
        if elig and not (r["cost_r"]<=0.20): continue
        g=r[arm]["gross"]; s=r["spread_at_fill_price"]
        if g is None or s is None: continue
        sr=s/(r["risk_price"] if arm!="inv" else r["reward_price"])
        out.append((g, sr, r[arm]["net"]))
    return np.array(out) if out else np.zeros((0,3))

def line(tag, rows, arm, elig):
    a=rows_of(rows,arm,elig)
    if len(a)<30: return None
    g,sr,net=a[:,0],a[:,1],a[:,2]
    resid=g+sr
    se=resid.std(ddof=1)/math.sqrt(len(resid))
    return dict(n=len(a), gross=float(g.mean()), spread=float(sr.mean()),
                resid=float(resid.mean()), se=float(se), t=float(resid.mean()/se),
                net=float(net.mean()))

byfam=defaultdict(list)
for r in recs: byfam[r["family"]].append(r)
print("FULL MARKET POPULATION — E[gross] vs -E[spread_r]\n")
print(f"{'family':34s} {'arm':7s} {'n':>6s} {'E[gross]':>9s} {'-E[sprd]':>9s} {'residual':>9s} {'se':>7s} {'t':>7s} {'E[net]':>8s}")
res={}
for fam,rows in list(sorted(byfam.items(), key=lambda kv:-len(kv[1])))+[("_POOLED",recs)]:
    for arm in ("orig","mirror"):
        d=line(fam,rows,arm,False)
        if d is None: continue
        res[f"{fam}|{arm}|all"]=d
        print(f"{fam:34s} {arm:7s} {d['n']:6d} {d['gross']:+9.4f} {-d['spread']:+9.4f} "
              f"{d['resid']:+9.4f} {d['se']:7.4f} {d['t']:+7.2f} {d['net']:+8.4f}")
    print()
print("\nCOST-ELIGIBLE (the funnel's own gate cost_r <= 0.20)\n")
print(f"{'family':34s} {'arm':7s} {'n':>6s} {'E[gross]':>9s} {'-E[sprd]':>9s} {'residual':>9s} {'se':>7s} {'t':>7s} {'E[net]':>8s}")
for fam,rows in list(sorted(byfam.items(), key=lambda kv:-len(kv[1])))+[("_POOLED",recs)]:
    for arm in ("orig","mirror"):
        d=line(fam,rows,arm,True)
        if d is None: continue
        res[f"{fam}|{arm}|elig"]=d
        print(f"{fam:34s} {arm:7s} {d['n']:6d} {d['gross']:+9.4f} {-d['spread']:+9.4f} "
              f"{d['resid']:+9.4f} {d['se']:7.4f} {d['t']:+7.2f} {d['net']:+8.4f}")
    print()
# censoring rates
print("censoring / status mix, orig arm:", Counter(r["orig"]["status"] for r in recs).most_common(8))
print("censoring / status mix, mirror  :", Counter(r["mirror"]["status"] for r in recs).most_common(8))
json.dump(res, open("/tmp/laneG/martingale.json","w"), indent=1)
