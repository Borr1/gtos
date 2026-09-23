"""Commodity continuation STATE GATE — choose threshold on TRAIN (<=2024), holdout FWD 2025 & 2026.
State = trailing 60-bar 1-bar-return autocorrelation (leak-free, bars<=i) measuring momentum
persistence. Hypothesis: continuation pays only when recent returns are positively autocorrelated
(trending/sticky regime); when AC is near zero or markets are choppy, the FVG-retest bleeds.
Also test efficiency-ratio gate and the combination. Per-year + per-symbol + win-rate reported."""
import sys
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
EDGE=ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10'
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from geometry_lib import simulate, atr14
import collections, statistics, json

METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD','XCUUSD']
ENERGY = ['USOIL_cash','UKOIL_cash','NATGAS_cash','HEATOIL_c']
AGRI   = ['CORN_c','COTTON_c']
def wins(r): return max(-1.3, min(5.0, r))

def autocorr(B, i, n):
    if i < n+1: return None
    rets=[B[k].c-B[k-1].c for k in range(i-n+1, i+1)]
    m=statistics.mean(rets)
    num=sum((rets[k]-m)*(rets[k-1]-m) for k in range(1,len(rets)))
    den=sum((x-m)**2 for x in rets)
    return num/den if den>0 else 0.0

def eff(B, i, n):
    if i < n: return None
    net = abs(B[i].c - B[i-n].c)
    path = sum(abs(B[k].c-B[k-1].c) for k in range(i-n+1, i+1))
    return net/path if path>0 else 0.0

def build(symbols):
    rows=[]
    for s in symbols:
        T,B = w1.load(s)
        if len(B)<200: continue
        for (t,d,sd,td,i,B2,cost) in g.fvg_signals(s):
            r = wins(simulate(B,i,d,stop_dist=sd,target_dist=td,cost=cost))
            rows.append({'sym':s,'year':t.year,'R':r,
                         'ac60':autocorr(B,i,60),'ac30':autocorr(B,i,30),'ac90':autocorr(B,i,90),
                         'e120':eff(B,i,120)})
    return rows

def stats(rs):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(x['R'] for x in rs)/n; w=sum(1 for x in rs if x['R']>0)/n*100
    return (n,m,w)

def report(rows, gate, name):
    sel=[x for x in rows if gate(x)]
    tr=[x for x in sel if x['year']<=2024]
    f25=[x for x in sel if x['year']==2025]; f26=[x for x in sel if x['year']==2026]
    nt,mt,wt=stats(tr); n25,m25,w25=stats(f25); n26,m26,w26=stats(f26)
    print(f'\n##### {name} #####')
    print(f'  TRAIN<=2024 n={nt:4d} EV={mt:+.4f} win={wt:.1f}%')
    print(f'  FWD 2025    n={n25:4d} EV={m25:+.4f} win={w25:.1f}%')
    print(f'  FWD 2026    n={n26:4d} EV={m26:+.4f} win={w26:.1f}%')
    by=collections.defaultdict(list)
    for x in sel: by[x['year']].append(x)
    pys=[]
    for y in sorted(by):
        n,m,w=stats(by[y]); pys.append(f'{y}:{m:+.3f}(n{n})')
    print('  per-year: '+' '.join(pys))
    bs=collections.defaultdict(list)
    for x in sel: bs[x['sym']].append(x)
    pss=[]
    for s in METALS+ENERGY+AGRI:
        if s in bs:
            n,m,w=stats(bs[s]); pss.append(f'{s}:{m:+.3f}(n{n})')
    print('  per-sym : '+' '.join(pss))
    return {'name':name,'train':{'n':nt,'ev':round(mt,4),'win':round(wt,1)},
            'fwd2025':{'n':n25,'ev':round(m25,4),'win':round(w25,1)},
            'fwd2026':{'n':n26,'ev':round(m26,4),'win':round(w26,1)},
            'per_year':{str(y):{'n':stats(by[y])[0],'ev':round(stats(by[y])[1],4)} for y in sorted(by)}}

if __name__=='__main__':
    rows = build(METALS)
    out={}
    out['baseline'] = report(rows, lambda x: True, 'BASELINE (no state gate, all metals)')
    # choose threshold on TRAIN only
    tr=[x for x in rows if x['year']<=2024 and x['ac60'] is not None]
    for thr in [0.0,0.05,0.10,0.15,0.20]:
        sel=[x for x in tr if x['ac60']>=thr]
        n=len(sel); m=sum(x['R'] for x in sel)/n if n else 0
        print(f'TRAIN ac60>={thr:.2f}: n={n} EV={m:+.4f}')
    print('---')
    out['ac60_010'] = report(rows, lambda x: x['ac60'] is not None and x['ac60']>=0.10, 'GATE ac60>=0.10 (metals)')
    out['ac60_015'] = report(rows, lambda x: x['ac60'] is not None and x['ac60']>=0.15, 'GATE ac60>=0.15 (metals)')
    out['e120_018'] = report(rows, lambda x: x['e120'] is not None and x['e120']>=0.18, 'GATE e120>=0.18 (metals)')
    out['combo'] = report(rows, lambda x: (x['ac60'] is not None and x['ac60']>=0.10) or (x['e120'] is not None and x['e120']>=0.24), 'GATE ac60>=0.10 OR e120>=0.24 (metals)')

    with open(EDGE+'/_KB_COMMODITY_GATE_RESULT.json','w') as f:
        json.dump(out,f,indent=1)
    print('\nwrote _KB_COMMODITY_GATE_RESULT.json')
