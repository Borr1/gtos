import gzip,json,collections,numpy as np
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
HZ=[1,2,4,8,16,32,64,96]; LAB={1:'15m',2:'30m',4:'1h',8:'2h',16:'4h',32:'8h',64:'16h',96:'24h'}
FAMS=['structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion']
def daycluster(vals,days):
    d=collections.defaultdict(list)
    for v,k in zip(vals,days): d[k].append(v)
    m=np.array([np.mean(v) for v in d.values()])
    return float(m.mean()), float(m.std(ddof=1)/np.sqrt(len(m))), len(m)
print("=== FORWARD DRIFT in bps of price, signed for the trade's own side, whole 12-month archive ===")
print("    (day-clustered mean +- se over trading days; a day is one calendar date pooled across symbols)")
print()
for fam in FAMS:
    sub=[r for r in rows if r['fam']==fam]
    days=[r['t'][:10] for r in sub]
    print(f"--- {fam}  n={len(sub)}  median stop {np.median([r['risk_bps'] for r in sub]):.2f} bps ---")
    print(f"{'horizon':>8s} {'drift_bps':>11s} {'se':>7s} {'t':>7s} {'MFE_bps':>9s} {'MAE_bps':>9s} {'MFE/stop':>9s}")
    st=np.median([r['risk_bps'] for r in sub])
    for hz in HZ:
        v=[r[f'd{hz}'] for r in sub]
        m,se,nd=daycluster(v,days)
        f=np.mean([r[f'f{hz}'] for r in sub]); a=np.mean([r[f'a{hz}'] for r in sub])
        print(f"{LAB[hz]:>8s} {m:11.4f} {se:7.4f} {m/se if se>0 else 0:7.2f} {f:9.3f} {a:9.3f} {f/st:9.2f}")
    print()
print("=== SIDE SPLIT (is it a directional idea or a side artifact?) ===")
for fam in FAMS:
    for side in ('LONG','SHORT'):
        sub=[r for r in rows if r['fam']==fam and r['side']==side]
        days=[r['t'][:10] for r in sub]
        line=[]
        for hz in (1,4,8,32,96):
            m,se,_=daycluster([r[f'd{hz}'] for r in sub],days); line.append(f"{LAB[hz]}={m:+.3f}({m/se if se>0 else 0:+.1f})")
        print(f"  {fam:30s} {side:6s} n={len(sub):7d}  "+"  ".join(line))
print()
print("=== STABILITY: drift at 1h by calendar quarter ===")
for fam in FAMS:
    sub=[r for r in rows if r['fam']==fam]
    byq=collections.defaultdict(list)
    for r in sub:
        y,m=int(r['t'][:4]),int(r['t'][5:7]); byq[f"{y}Q{(m-1)//3+1}"].append(r['d4'])
    print(f"  {fam:30s} "+"  ".join(f"{k}:{np.mean(v):+.3f}(n={len(v)})" for k,v in sorted(byq.items())))
