"""Matched placebo: for every emission, draw random bars of the SAME symbol in the SAME
calendar week and take the SAME side. This absorbs instrument beta, week regime, side mix
and emission clustering at once. Signal = emission drift - matched placebo drift."""
import csv,os,json,gzip,collections,numpy as np
H=("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
   "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
   "bridge_ftmo_m15_20250601_20260610")
HZ=[1,4,8,32,96]; LAB={1:'15m',4:'1h',8:'2h',32:'8h',96:'24h'}
rng=np.random.default_rng(20260807)
BAR={}; IDX={}
for f in sorted(os.listdir(H)):
    if not f.endswith('_M15.csv'): continue
    s=f[:-8]; t=[];c=[]
    with open(os.path.join(H,f),newline='') as fh:
        for r in csv.DictReader(fh): t.append(r['time']); c.append(float(r['close']))
    BAR[s]=(t,np.asarray(c)); IDX[s]={tt:i for i,tt in enumerate(t)}
def isoweek(ts): 
    import datetime as D
    d=D.date(int(ts[:4]),int(ts[5:7]),int(ts[8:10])); y,w,_=d.isocalendar(); return f"{y}W{w:02d}"
WK={}
for s,(t,c) in BAR.items():
    m=collections.defaultdict(list)
    for i,tt in enumerate(t): m[isoweek(tt)].append(i)
    WK[s]={k:np.asarray(v) for k,v in m.items()}
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
def dc(vals,days):
    d=collections.defaultdict(list)
    for v,k in zip(vals,days): d[k].append(v)
    m=np.array([np.mean(v) for v in d.values()])
    return float(m.mean()), float(m.std(ddof=1)/np.sqrt(len(m)))
NREP=5
print("=== EMISSION minus MATCHED PLACEBO (same symbol, same ISO week, same side, 5 draws) ===")
print(f"{'family':30s} {'side':6s} {'n':>7s} "+" ".join(f"{LAB[h]:>16s}" for h in HZ))
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
  for side in ('*','LONG','SHORT'):
    sub=[r for r in rows if r['fam']==fam and (side=='*' or r['side']==side)]
    days=[r['t'][:10] for r in sub]
    cells=[]
    for hz in HZ:
        diff=np.empty(len(sub))
        for i,r in enumerate(sub):
            s=r['sym']; t,c=BAR[s]; n=len(c)
            pool=WK[s][isoweek(r['t'])]
            pool=pool[pool+hz<n]
            sgn=1.0 if r['side']=='LONG' else -1.0
            if len(pool)==0: diff[i]=0.0; continue
            pick=rng.choice(pool,size=min(NREP,len(pool)),replace=len(pool)<NREP)
            pl=np.mean(sgn*(c[pick+hz]-c[pick])/c[pick]*1e4)
            diff[i]=r[f'd{hz}']-pl
        m,se=dc(diff,days)
        cells.append(f"{m:+8.3f}({m/se if se>0 else 0:+5.2f})")
    print(f"{fam:30s} {side:6s} {len(sub):7d} "+" ".join(cells))
  print()
print("=== QUARTERLY STABILITY of the placebo-differenced signal (pooled sides) ===")
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    sub=[r for r in rows if r['fam']==fam]
    for hz in (1,8,96):
        byq=collections.defaultdict(list)
        for r in sub:
            s=r['sym']; t,c=BAR[s]; n=len(c)
            pool=WK[s][isoweek(r['t'])]; pool=pool[pool+hz<n]
            if len(pool)==0: continue
            sgn=1.0 if r['side']=='LONG' else -1.0
            pick=rng.choice(pool,size=min(NREP,len(pool)),replace=len(pool)<NREP)
            pl=np.mean(sgn*(c[pick+hz]-c[pick])/c[pick]*1e4)
            y,mo=int(r['t'][:4]),int(r['t'][5:7]); byq[f"{y}Q{(mo-1)//3+1}"].append(r[f'd{hz}']-pl)
        pos=sum(1 for k,v in byq.items() if np.mean(v)>0)
        print(f"  {fam:30s} {LAB[hz]:>4s}  "+"  ".join(f"{k}:{np.mean(v):+7.3f}" for k,v in sorted(byq.items()))+f"   [{pos}/{len(byq)} quarters +]")
