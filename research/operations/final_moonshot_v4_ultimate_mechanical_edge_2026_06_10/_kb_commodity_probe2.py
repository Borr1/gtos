"""Probe 2: is the regime a MACRO trend-persistence / autocorrelation state, not a local setup state?
Measure, per year per symbol, the realised trendiness of the underlying (efficiency ratio of the
whole year, and 1-bar return autocorrelation) and correlate with FVG continuation EV that year.
Also test a LEAK-FREE rolling macro state: efficiency ratio of close over the last N bars BEFORE
entry at a longer horizon, and ADX-like directional persistence.
No lookahead: macro state uses only bars <= i."""
import sys
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
EDGE=ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10'
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from geometry_lib import simulate, atr14
import collections, statistics

METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD','XCUUSD']
def wins(r): return max(-1.3, min(5.0, r))

def eff(B, i, n):
    if i < n: return None
    net = abs(B[i].c - B[i-n].c)
    path = sum(abs(B[k].c-B[k-1].c) for k in range(i-n+1, i+1))
    return net/path if path>0 else 0.0

# 1-bar return autocorrelation over trailing window (trend-following pays when AC>0)
def autocorr(B, i, n):
    if i < n+1: return None
    rets=[B[k].c-B[k-1].c for k in range(i-n+1, i+1)]
    m=statistics.mean(rets)
    num=sum((rets[k]-m)*(rets[k-1]-m) for k in range(1,len(rets)))
    den=sum((x-m)**2 for x in rets)
    return num/den if den>0 else 0.0

rows=[]
for s in METALS:
    T,B = w1.load(s)
    if len(B)<200: continue
    for (t,d,sd,td,i,B2,cost) in g.fvg_signals(s):
        r = wins(simulate(B,i,d,stop_dist=sd,target_dist=td,cost=cost))
        e120 = eff(B,i,120)   # ~20 trading days of H4 = macro efficiency
        e240 = eff(B,i,240)
        ac60 = autocorr(B,i,60)
        rows.append({'sym':s,'year':t.year,'R':r,'e120':e120,'e240':e240,'ac60':ac60})

# Per-year mean of macro states vs that year's EV (metals aggregate)
print('=== Per-year: FVG EV vs trailing macro-efficiency / autocorr state ===')
by=collections.defaultdict(list)
for x in rows: by[x['year']].append(x)
print(f"{'yr':>4} {'n':>4} {'EV':>7} {'e120':>7} {'e240':>7} {'ac60':>7}")
for y in sorted(by):
    sub=by[y]; n=len(sub)
    ev=sum(x['R'] for x in sub)/n
    def mn(k):
        vs=[x[k] for x in sub if x[k] is not None]
        return statistics.mean(vs) if vs else float('nan')
    print(f"{y:>4} {n:>4} {ev:>+7.3f} {mn('e120'):>7.3f} {mn('e240'):>7.3f} {mn('ac60'):>+7.3f}")

# Pooled: does e120 separate winners from losers? Bucket by e120.
print('\n=== Pooled metals: EV by trailing-120-bar efficiency bucket (leak-free state) ===')
valid=[x for x in rows if x['e120'] is not None]
valid.sort(key=lambda x:x['e120'])
nb=5; per=len(valid)//nb
for b in range(nb):
    seg=valid[b*per:(b+1)*per] if b<nb-1 else valid[b*per:]
    lo=seg[0]['e120']; hi=seg[-1]['e120']
    ev=sum(x['R'] for x in seg)/len(seg)
    w=sum(1 for x in seg if x['R']>0)/len(seg)*100
    print(f"  e120 [{lo:.3f},{hi:.3f}] n={len(seg):4d} EV={ev:+.4f} win={w:.1f}%")

print('\n=== Pooled metals: EV by trailing-60-bar return autocorr bucket ===')
valid=[x for x in rows if x['ac60'] is not None]
valid.sort(key=lambda x:x['ac60'])
per=len(valid)//nb
for b in range(nb):
    seg=valid[b*per:(b+1)*per] if b<nb-1 else valid[b*per:]
    lo=seg[0]['ac60']; hi=seg[-1]['ac60']
    ev=sum(x['R'] for x in seg)/len(seg)
    w=sum(1 for x in seg if x['R']>0)/len(seg)*100
    print(f"  ac60 [{lo:+.3f},{hi:+.3f}] n={len(seg):4d} EV={ev:+.4f} win={w:.1f}%")
