"""Confound checks for the ac60 momentum-persistence gate.
(1) XAUUSD-ONLY 2015-2026 (long history, no multi-symbol expansion confound).
(2) Inverted signal under same gate (edge must be directional).
(3) Gate applied to energy & agri (does state generalize across commodity classes?).
(4) Gate vs ANTI-gate (ac60<0.10) to prove the state, not the entries, carries the EV.
(5) 2023 inspection: why does it stay negative even gated?"""
import sys
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
EDGE=ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10'
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from geometry_lib import simulate, atr14
import collections, statistics

METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD','XCUUSD']
ENERGY = ['USOIL_cash','NATGAS_cash','HEATOIL_c']
AGRI   = ['CORN_c','COTTON_c']
def wins(r): return max(-1.3, min(5.0, r))

def autocorr(B, i, n=60):
    if i < n+1: return None
    rets=[B[k].c-B[k-1].c for k in range(i-n+1, i+1)]
    m=statistics.mean(rets)
    num=sum((rets[k]-m)*(rets[k-1]-m) for k in range(1,len(rets)))
    den=sum((x-m)**2 for x in rets)
    return num/den if den>0 else 0.0

def build(symbols, invert=False):
    rows=[]
    for s in symbols:
        T,B = w1.load(s)
        if len(B)<200: continue
        for (t,d,sd,td,i,B2,cost) in g.fvg_signals(s):
            dd = -d if invert else d
            r = wins(simulate(B,i,dd,stop_dist=sd,target_dist=td,cost=cost))
            rows.append({'sym':s,'year':t.year,'R':r,'ac60':autocorr(B,i,60),'i':i})
    return rows

def stats(rs):
    if not rs: return (0,0.0,0.0)
    n=len(rs); m=sum(x['R'] for x in rs)/n; w=sum(1 for x in rs if x['R']>0)/n*100
    return (n,m,w)

def tf(rows,gate,name):
    sel=[x for x in rows if gate(x)]
    tr=[x for x in sel if x['year']<=2024]; f25=[x for x in sel if x['year']==2025]; f26=[x for x in sel if x['year']==2026]
    nt,mt,wt=stats(tr); n25,m25,w25=stats(f25); n26,m26,w26=stats(f26)
    print(f'  {name:38s} TR n={nt:4d} EV={mt:+.3f} w{wt:.0f} | 25 n={n25:3d} EV={m25:+.3f} w{w25:.0f} | 26 n={n26:3d} EV={m26:+.3f} w{w26:.0f}')

GATE = lambda x: x['ac60'] is not None and x['ac60']>=0.10

print('=== (1) XAUUSD ONLY (long history, no expansion confound) ===')
xau=build(['XAUUSD'])
tf(xau, lambda x: True, 'XAUUSD baseline')
tf(xau, GATE, 'XAUUSD ac60>=0.10')
by=collections.defaultdict(list)
for x in xau:
    if GATE(x): by[x['year']].append(x)
print('   XAUUSD gated per-year: '+' '.join(f'{y}:{stats(by[y])[1]:+.2f}(n{stats(by[y])[0]})' for y in sorted(by)))

print('\n=== (2) INVERTED signal under same gate (must be negative) ===')
inv=build(METALS, invert=True)
tf(inv, GATE, 'metals INVERTED ac60>=0.10')

print('\n=== (3) state generalization to other commodity classes ===')
en=build(ENERGY); ag=build(AGRI)
tf(en, lambda x:True, 'energy baseline'); tf(en, GATE, 'energy ac60>=0.10')
tf(ag, lambda x:True, 'agri baseline');   tf(ag, GATE, 'agri ac60>=0.10')

print('\n=== (4) GATE vs ANTI-GATE (proves state carries EV) — metals ===')
met=build(METALS)
tf(met, GATE, 'metals GATE ac60>=0.10')
tf(met, lambda x: x['ac60'] is not None and x['ac60']<0.10, 'metals ANTI-GATE ac60<0.10')

print('\n=== (5) metals ac60>=0.10 EXCLUDING XCUUSD (the bad symbol) ===')
tf([x for x in met if x['sym']!='XCUUSD'], GATE, 'metals(noXCU) ac60>=0.10')
