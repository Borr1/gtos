import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]; rng=np.random.default_rng(11)
def walk(r,H,s,t):
    k=r['risk_bps']
    for hz in HZ:
        if hz>H: break
        if s is not None and r[f'a{hz}']<=-s*k: return -s*k
        if t is not None and r[f'f{hz}']>= t*k: return  t*k
    return r[f'd{H}']
def boot(v,days,B=1500):
    v=np.asarray(v); uk,inv=np.unique(np.asarray(days),return_inverse=True)
    bk=[v[inv==i] for i in range(len(uk))]; n=len(uk); o=np.empty(B)
    for b in range(B): o[b]=np.concatenate([bk[i] for i in rng.integers(0,n,n)]).mean()
    return float(v.mean()),float(np.percentile(o,2.5)),float(np.percentile(o,97.5))
print("=== SIDE SPLIT at the SHIPPED contract, 2h, trade-weighted, bps/trade ===")
for fam in ('range_extreme_reversion','structural_distance_extreme','liquidity_sweep_reclaim'):
    for side in ('LONG','SHORT'):
        sub=[r for r in rows if r['fam']==fam and r['side']==side]
        m,lo,hi=boot([walk(r,8,1.0,2.0) for r in sub],[r['t'][:10] for r in sub])
        byq=collections.defaultdict(list)
        for r in sub:
            y,mo=int(r['t'][:4]),int(r['t'][5:7]); byq[f"{y}Q{(mo-1)//3+1}"].append(walk(r,8,1.0,2.0))
        pos=sum(1 for k in byq if np.mean(byq[k])>0)
        print(f"  {fam:30s} {side:6s} n={len(sub):7d}  {m:+7.4f}  CI[{lo:+7.4f},{hi:+7.4f}]  {pos}/{len(byq)} qtrs+")
print()
print("=== range_extreme_reversion: the 9.04% of emissions with range_pos OUTSIDE [0,1] ===")
rer=[r for r in rows if r['fam']=='range_extreme_reversion']
inb=[r for r in rer if 0.0<=r['rpos']<=1.0]; out=[r for r in rer if not (0.0<=r['rpos']<=1.0)]
for nm,g in (('in [0,1] (a real range extreme)',inb),('OUTSIDE [0,1] (a breakout being faded)',out)):
    m,lo,hi=boot([walk(r,8,1.0,2.0) for r in g],[r['t'][:10] for r in g])
    print(f"  {nm:42s} n={len(g):7d}  {m:+7.4f}  CI[{lo:+7.4f},{hi:+7.4f}]")
print()
print("=== the 10.49% thrust=small emissions the mine never confirmed ===")
for nm,g in (('range/atr14 in [0.5,1.5) = mine thrust=mid',[r for r in rer if 0.5<=r['rngatr']<1.5]),
             ('range/atr14 < 0.5  = mine thrust=small',[r for r in rer if r['rngatr']<0.5])):
    m,lo,hi=boot([walk(r,8,1.0,2.0) for r in g],[r['t'][:10] for r in g])
    print(f"  {nm:42s} n={len(g):7d}  {m:+7.4f}  CI[{lo:+7.4f},{hi:+7.4f}]")
print()
print("=== the fixed 2R TARGET's cost, bps/trade (stop-only minus shipped S1/T2) ===")
for H,lab in ((8,'2h'),(96,'24h')):
    for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
        sub=[r for r in rows if r['fam']==fam]
        d=[walk(r,H,1.0,None)-walk(r,H,1.0,2.0) for r in sub]
        m,lo,hi=boot(d,[r['t'][:10] for r in sub])
        print(f"  {lab:>4s} {fam:30s} {m:+7.4f}  CI[{lo:+7.4f},{hi:+7.4f}]")
