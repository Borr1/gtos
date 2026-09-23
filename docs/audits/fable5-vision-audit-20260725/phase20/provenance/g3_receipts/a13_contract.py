"""WITHIN-POPULATION CONTRACT ABLATION. Same emissions, same tape, same horizon; only the
exit contract changes. Everything (beta, side mix, clustering, symbol mix) is held fixed,
so the DIFFERENCE between rows is attributable to the contract alone."""
import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]; LAB={1:'15m',2:'30m',4:'1h',8:'2h',16:'4h',32:'8h',64:'16h',96:'24h'}
def dc(v,days):
    d=collections.defaultdict(list)
    for x,k in zip(v,days): d[k].append(x)
    m=np.array([np.mean(x) for x in d.values()]); return float(m.mean()), float(m.std(ddof=1)/np.sqrt(len(m)))
def walk(r,HEND,stopR,tgtR):
    """coarse first-touch on the M15 running extremes; conservative tie -> stop."""
    risk=r['risk_bps']
    for hz in HZ:
        if hz>HEND: break
        hit_s = (stopR is not None) and (r[f'a{hz}'] <= -stopR*risk)
        hit_t = (tgtR  is not None) and (r[f'f{hz}'] >=  tgtR*risk)
        if hit_s: return -stopR*risk
        if hit_t: return  tgtR*risk
    return r[f'd{HEND}']
ARMS=[('shipped  S1/T2',1.0,2.0),('stop only S1',1.0,None),('target only T2',None,2.0),
      ('naked hold',None,None),('S3/T6',3.0,6.0),('S6/T12',6.0,12.0),('S12/T24',12.0,24.0)]
for HEND in (8,32,96):
    print(f"=== horizon {LAB[HEND]} — mean price captured, bps/trade (day-clustered t) ===")
    print(f"{'family':30s} {'stop_bps':>9s} "+" ".join(f"{a[0]:>19s}" for a in ARMS))
    for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
        sub=[r for r in rows if r['fam']==fam]; days=[r['t'][:10] for r in sub]
        cells=[]
        for name,s,t in ARMS:
            v=[walk(r,HEND,s,t) for r in sub]; m,se=dc(v,days)
            cells.append(f"{m:+9.3f}({m/se if se>0 else 0:+5.2f})")
        print(f"{fam:30s} {np.median([r['risk_bps'] for r in sub]):9.2f} "+" ".join(cells))
    print()
print("=== THE COST OF THE FAMILY'S OWN STOP, in bps/trade (naked hold minus shipped S1/T2) ===")
for HEND in (8,32,96):
    for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
        sub=[r for r in rows if r['fam']==fam]; days=[r['t'][:10] for r in sub]
        d=[walk(r,HEND,None,None)-walk(r,HEND,1.0,2.0) for r in sub]
        m,se=dc(d,days)
        print(f"  {LAB[HEND]:>4s} {fam:30s} {m:+8.3f} bps  (t {m/se if se>0 else 0:+5.2f})   stop-hit rate {100*np.mean([r[f'a{HEND}']<=-r['risk_bps'] for r in sub]):5.1f}%   tgt-reach {100*np.mean([r[f'f{HEND}']>=2*r['risk_bps'] for r in sub]):5.1f}%")
    print()
