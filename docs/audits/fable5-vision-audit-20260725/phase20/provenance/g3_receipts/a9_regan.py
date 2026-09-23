import gzip,json,collections,numpy as np,statistics
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
print("n",len(rows))
def q(v,p):
    v=np.asarray(v); return float(np.percentile(v,p*100))
FAM=collections.Counter(r['fam'] for r in rows)
print(FAM)
print()
print("=== STOP DECOMPOSITION (whole archive, 24 symbols, 2025-06-01..2026-06-10) ===")
print(f"{'family':30s} {'side':6s} {'n':>7s} {'risk_bps_med':>12s} {'wick_bps_med':>12s} {'atr_term_med':>12s} {'atr_share_med%':>14s} {'atr14_bps_med':>13s}")
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    for side in ('SHORT','LONG','*'):
        sub=[r for r in rows if r['fam']==fam and (side=='*' or r['side']==side)]
        if not sub: continue
        rb=[r['risk_bps'] for r in sub]; wb=[r['wick_bps'] for r in sub]; ab=[r['atrterm_bps'] for r in sub]
        sh=[100*r['atrterm_bps']/r['risk_bps'] for r in sub if r['risk_bps']>0]
        at=[r['atr14_bps'] for r in sub]
        print(f"{fam:30s} {side:6s} {len(sub):7d} {q(rb,.5):12.3f} {q(wb,.5):12.3f} {q(ab,.5):12.3f} {q(sh,.5):14.1f} {q(at,.5):13.3f}")
print()
print("=== RANGE_EXTREME_REVERSION predicate audit (shipped prior-50 EXCLUSIVE vs mine V2's 48-bar INCLUSIVE) ===")
rer=[r for r in rows if r['fam']=='range_extreme_reversion']
rp=np.array([r['rpos'] for r in rer]); p48=np.array([r['pos48'] for r in rer if r['pos48'] is not None])
print(f"n={len(rer)}  shipped range_pos: min {rp.min():.3f} p1 {q(rp,.01):.3f} med {q(rp,.5):.3f} p99 {q(rp,.99):.3f} max {rp.max():.3f}")
print(f"  OUTSIDE [0,1] (impossible under the mine's own definition): {100*np.mean((rp<0)|(rp>1)):.2f}%  ( >1: {100*np.mean(rp>1):.2f}%,  <0: {100*np.mean(rp<0):.2f}% )")
# agreement with the mine's bucket
agree=0; tot=0
for r in rer:
    if r['pos48'] is None: continue
    tot+=1
    mine = 'low' if r['pos48']<0.25 else ('high' if r['pos48']>0.75 else 'mid')
    ship = 'low' if r['side']=='LONG' else 'high'
    if mine==ship: agree+=1
print(f"  shipped side agrees with mine V2's own pos48 bucket on {100*agree/tot:.2f}% of emissions (n={tot})")
print(f"  thrust filter: shipped admits range/atr < 1.5 (mine confirmed cells were thrust=mid = 0.5..1.5)")
ra=np.array([r['rngatr'] for r in rer])
print(f"    of shipped RER emissions, range/atr14 < 0.5 (mine's 'small', only 1 of 166 confirmed cells): {100*np.mean(ra<0.5):.2f}%")
