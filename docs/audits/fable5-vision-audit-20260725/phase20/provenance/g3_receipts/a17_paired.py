"""THE ESTATE'S OWN NATURAL EXPERIMENT: 76.8% of structural_distance_extreme emissions are
a same-side range_extreme_reversion emission on the SAME bar. Identical entry, identical
side, identical instant -- ONLY the stop differs (0.25xATR14 + wick vs 1.00xATR14).
Paired, same rows, both directions."""
import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]; rng=np.random.default_rng(3)
idx=collections.defaultdict(dict)
for r in rows: idx[(r['sym'],r['t'],r['side'])][r['fam']]=r
pairs=[(v['structural_distance_extreme'],v['range_extreme_reversion'])
       for v in idx.values() if 'structural_distance_extreme' in v and 'range_extreme_reversion' in v]
print("paired rows:",len(pairs))
def walk(r,H,s,t):
    k=r['risk_bps']
    for hz in HZ:
        if hz>H: break
        if s is not None and r[f'a{hz}']<=-s*k: return -s*k
        if t is not None and r[f'f{hz}']>= t*k: return  t*k
    return r[f'd{H}']
def boot(v,days,B=2000):
    v=np.asarray(v); uk,inv=np.unique(np.asarray(days),return_inverse=True)
    bk=[v[inv==i] for i in range(len(uk))]; n=len(uk); o=np.empty(B)
    for b in range(B): o[b]=np.concatenate([bk[i] for i in rng.integers(0,n,n)]).mean()
    return float(v.mean()),float(np.percentile(o,2.5)),float(np.percentile(o,97.5))
days=[a['t'][:10] for a,b in pairs]
print(f"  median stop  SDE {np.median([a['risk_bps'] for a,b in pairs]):.2f} bps   RER {np.median([b['risk_bps'] for a,b in pairs]):.2f} bps"
      f"   ratio {np.median([b['risk_bps']/a['risk_bps'] for a,b in pairs]):.2f}x")
for H,lab in ((8,'2h'),(96,'24h')):
    sd=[walk(a,H,1.0,2.0) for a,b in pairs]; rr=[walk(b,H,1.0,2.0) for a,b in pairs]
    m1,l1,h1=boot(sd,days); m2,l2,h2=boot(rr,days); md,ld,hd=boot([y-x for x,y in zip(sd,rr)],days)
    print(f"  {lab:>4s}  SDE geometry (tight stop) {m1:+7.4f} [{l1:+7.4f},{h1:+7.4f}]"
          f"   RER geometry (1.0xATR stop) {m2:+7.4f} [{l2:+7.4f},{h2:+7.4f}]"
          f"   PAIRED DIFF {md:+7.4f} [{ld:+7.4f},{hd:+7.4f}]")
    # and stop-only on both
    sd2=[walk(a,H,1.0,None) for a,b in pairs]; rr2=[walk(b,H,1.0,None) for a,b in pairs]
    m1,l1,h1=boot(sd2,days); m2,l2,h2=boot(rr2,days); md,ld,hd=boot([y-x for x,y in zip(sd2,rr2)],days)
    print(f"        no-target  SDE stop {m1:+7.4f} [{l1:+7.4f},{h1:+7.4f}]   RER stop {m2:+7.4f} [{l2:+7.4f},{h2:+7.4f}]   DIFF {md:+7.4f} [{ld:+7.4f},{hd:+7.4f}]")
