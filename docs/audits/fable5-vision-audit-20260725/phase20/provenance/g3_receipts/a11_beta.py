"""BETA CONTROL. The 2025-06..2026-06 archive has a large long-side drift; a family that
emits more LONGs than SHORTs (or emits them in risen instruments) inherits it. Subtract,
per symbol and per horizon, the instrument's own UNCONDITIONAL forward return over the
identical bar population, signed to the trade's side."""
import csv,os,gzip,json,collections,numpy as np
H=("/Users/borr/GTOSActive/lane-inputs-true-utc-hold-20260805/.hermes/evidence/"
   "phase16/cj-rematerialization/LANE_INPUTS_TRUE_UTC_V1/sources/bars/"
   "bridge_ftmo_m15_20250601_20260610")
HZ=[1,2,4,8,16,32,64,96]; LAB={1:'15m',2:'30m',4:'1h',8:'2h',16:'4h',32:'8h',64:'16h',96:'24h'}
UNC={}
for f in sorted(os.listdir(H)):
    if not f.endswith('_M15.csv'): continue
    s=f[:-8]; c=[]
    with open(os.path.join(H,f),newline='') as fh:
        for r in csv.DictReader(fh): c.append(float(r['close']))
    c=np.asarray(c); UNC[s]={}
    for hz in HZ:
        if len(c)>hz:
            UNC[s][hz]=float(np.mean((c[hz:]-c[:-hz])/c[:-hz]*1e4))
        else: UNC[s][hz]=0.0
rows=[json.loads(l) for l in gzip.open('/tmp/g3/REGEN_V1.jsonl.gz','rt')]
def dc(vals,days):
    d=collections.defaultdict(list)
    for v,k in zip(vals,days): d[k].append(v)
    m=np.array([np.mean(v) for v in d.values()])
    return float(m.mean()), float(m.std(ddof=1)/np.sqrt(len(m)))
print("=== EXCESS DRIFT over the instrument's own unconditional drift (bps, day-clustered) ===")
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    for side in ('*','LONG','SHORT'):
        sub=[r for r in rows if r['fam']==fam and (side=='*' or r['side']==side)]
        days=[r['t'][:10] for r in sub]
        cells=[]
        for hz in HZ:
            ex=[r[f'd{hz}'] - (1 if r['side']=='LONG' else -1)*UNC[r['sym']][hz] for r in sub]
            m,se=dc(ex,days); cells.append(f"{m:+7.3f}({m/se if se>0 else 0:+5.2f})")
        print(f"{fam:30s} {side:6s} n={len(sub):7d} "+" ".join(cells))
    print(f"{'':30s} {'hz':6s} {'':9s} "+" ".join(f"{LAB[h]:>14s}" for h in HZ))
    print()
print("=== side mix (why the raw table looked positive) ===")
for fam in ('structural_distance_extreme','liquidity_sweep_reclaim','range_extreme_reversion'):
    sub=[r for r in rows if r['fam']==fam]
    n=len(sub); nl=sum(1 for r in sub if r['side']=='LONG')
    print(f"  {fam:30s} LONG {100*nl/n:5.1f}%   SHORT {100*(n-nl)/n:5.1f}%")
print()
print("=== the instrument beta itself (mean unconditional 24h drift, bps) ===")
u=sorted(((s,UNC[s][96]) for s in UNC), key=lambda x:-x[1])
print("  ".join(f"{s}:{v:+.1f}" for s,v in u))
