import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]
def walk(r,HEND,stopR,tgtR):
    risk=r['risk_bps']
    for hz in HZ:
        if hz>HEND: break
        if stopR is not None and r[f'a{hz}']<=-stopR*risk: return -stopR*risk
        if tgtR  is not None and r[f'f{hz}']>= tgtR*risk: return  tgtR*risk
    return r[f'd{HEND}']
def dc(v,days):
    d=collections.defaultdict(list)
    for x,k in zip(v,days): d[k].append(x)
    m=np.array([np.mean(x) for x in d.values()]); return float(m.mean()), float(m.std(ddof=1)/np.sqrt(len(m))), len(m)
def qtr(t): 
    y,m=int(t[:4]),int(t[5:7]); return f"{y}Q{(m-1)//3+1}"
ARMS=[('shipped S1/T2',1.0,2.0),('S3/T6',3.0,6.0),('S6/T12',6.0,12.0),('S12/T24',12.0,24.0),('naked',None,None)]
print("=== PER-QUARTER, horizon 2h, bps/trade ===")
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    sub=[r for r in rows if r['fam']==fam]
    print(f"--- {fam} ---")
    for name,s,t in ARMS:
        byq=collections.defaultdict(list)
        for r in sub: byq[qtr(r['t'])].append(walk(r,8,s,t))
        v=[walk(r,8,s,t) for r in sub]; m,se,nd=dc(v,[r['t'][:10] for r in sub])
        pos=sum(1 for k in byq if np.mean(byq[k])>0)
        print(f"   {name:14s} all {m:+7.3f}(t{m/se if se>0 else 0:+5.2f})  "+"  ".join(f"{k}:{np.mean(byq[k]):+6.2f}" for k in sorted(byq))+f"  [{pos}/{len(byq)}+]")
print()
print("=== HELD-OUT SPLIT: choose the arm on 2025Q2+Q3, score it on 2025Q4+2026Q1+Q2 (horizon 2h) ===")
TR={'2025Q2','2025Q3'}
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    sub=[r for r in rows if r['fam']==fam]
    tr=[r for r in sub if qtr(r['t']) in TR]; te=[r for r in sub if qtr(r['t']) not in TR]
    best=None
    for name,s,t in ARMS:
        m,_,_=dc([walk(r,8,s,t) for r in tr],[r['t'][:10] for r in tr])
        if best is None or m>best[1]: best=(name,m,s,t)
    m2,se2,nd2=dc([walk(r,8,best[2],best[3]) for r in te],[r['t'][:10] for r in te])
    ms,ses,_=dc([walk(r,8,1.0,2.0) for r in te],[r['t'][:10] for r in te])
    print(f"  {fam:30s} TRAIN pick={best[0]:14s} ({best[1]:+.3f})  ->  TEST n={len(te):6d} {m2:+7.3f} bps (t{m2/se2:+5.2f}, {nd2} days) | shipped on same TEST {ms:+7.3f} (t{ms/ses:+5.2f})")
print()
print("=== SDE S6/T12 @2h — symbol concentration and asset-class split ===")
sub=[r for r in rows if r['fam']=='structural_distance_extreme']
bysym=collections.defaultdict(list)
for r in sub: bysym[r['sym']].append(walk(r,8,6.0,12.0))
tot=np.mean([v for vs in bysym.values() for v in vs])
items=sorted(((s,np.mean(v),len(v)) for s,v in bysym.items()),key=lambda x:-x[1]*x[2])
print("   top contributors (mean*n):", "  ".join(f"{s}:{m:+.2f}(n={n})" for s,m,n in items[:6]))
print("   worst:", "  ".join(f"{s}:{m:+.2f}(n={n})" for s,m,n in items[-5:]))
pos=sum(1 for s,m,n in items if m>0)
print(f"   symbols with positive mean: {pos}/{len(items)}")
