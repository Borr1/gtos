"""Definitive table: TRADE-WEIGHTED mean bps/trade with a DAY-BLOCK bootstrap CI
(2000 reps, days resampled with replacement) + quarter sign consistency.
One estimator, stated once, for every arm."""
import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]
rng=np.random.default_rng(7)
def walk(r,HEND,s,t):
    risk=r['risk_bps']
    for hz in HZ:
        if hz>HEND: break
        if s is not None and r[f'a{hz}']<=-s*risk: return -s*risk
        if t is not None and r[f'f{hz}']>= t*risk: return  t*risk
    return r[f'd{HEND}']
def boot(vals,days,B=2000):
    v=np.asarray(vals); dl=np.asarray(days)
    uk,inv=np.unique(dl,return_inverse=True)
    buckets=[v[inv==i] for i in range(len(uk))]
    n=len(uk); out=np.empty(B)
    for b in range(B):
        pick=rng.integers(0,n,n)
        out[b]=np.concatenate([buckets[i] for i in pick]).mean()
    return float(v.mean()), float(np.percentile(out,2.5)), float(np.percentile(out,97.5)), float((out<=0).mean())
ARMS=[('shipped S1/T2',1.0,2.0),('S2/T4',2.0,4.0),('S3/T6',3.0,6.0),('S6/T12',6.0,12.0),
      ('S12/T24',12.0,24.0),('stop-only S1',1.0,None),('naked hold',None,None)]
def qtr(t):
    y,m=int(t[:4]),int(t[5:7]); return f"{y}Q{(m-1)//3+1}"
TOLL=3.02
for HEND,lab in ((8,'2h'),(96,'24h')):
    print(f"########## horizon {lab} — TRADE-WEIGHTED bps/trade, day-block bootstrap CI95 ##########")
    print(f"{'family':30s} {'arm':14s} {'stop_bps':>8s} {'bps/trade':>10s} {'CI95':>22s} {'p(<=0)':>7s} {'qtr+':>5s} {'vs 3.02bp toll':>15s}")
    for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
        sub=[r for r in rows if r['fam']==fam]; days=[r['t'][:10] for r in sub]
        st=float(np.median([r['risk_bps'] for r in sub]))
        for name,s,t in ARMS:
            v=[walk(r,HEND,s,t) for r in sub]
            m,lo,hi,p=boot(v,days)
            byq=collections.defaultdict(list)
            for r,x in zip(sub,v): byq[qtr(r['t'])].append(x)
            pos=sum(1 for k in byq if np.mean(byq[k])>0)
            sbps = st*(s if s else 1.0)
            print(f"{fam:30s} {name:14s} {sbps:8.2f} {m:10.4f} [{lo:+8.4f},{hi:+8.4f}] {p:7.3f} {pos}/{len(byq):d}   {m-TOLL:+13.3f}")
        print()
