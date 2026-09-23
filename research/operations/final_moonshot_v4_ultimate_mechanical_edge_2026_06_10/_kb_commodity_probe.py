"""Commodity continuation regime probe — feature contrast of winning vs losing regimes.
Investigation scratch for KB_commodity_regime.md. No lookahead in any feature (all use bars<=i)."""
import sys
ROOT='/Users/borr/Documents/gtos/repo/ai-trading-agent'
EDGE=ROOT+'/research/operations/final_moonshot_v4_ultimate_mechanical_edge_2026_06_10'
sys.path.insert(0,ROOT); sys.path.insert(0,EDGE)
import gold_sleeve_strategy as g
import wave1_structure_setups_ict as w1
from geometry_lib import simulate, atr14
import collections, statistics

METALS = ['XAUUSD','XAGUSD','XAUEUR','XAGEUR','XAUAUD','XAGAUD','XCUUSD']
ENERGY = ['USOIL_cash','UKOIL_cash','NATGAS_cash','HEATOIL_c']
AGRI   = ['CORN_c','COTTON_c']
def wins(r): return max(-1.3, min(5.0, r))

def feats(B, atrs, i, d):
    a = atrs[i]; f = {}
    f['trend30'] = (B[i].c - B[i-30].c)/a if a>0 else 0.0
    f['trend60'] = (B[i].c - B[i-60].c)/a if (a>0 and i>=60) else 0.0
    ups = sum(1 for k in range(i-29,i+1) if B[k].c > B[k].o)
    f['frac_up30'] = ups/30.0
    f['trend30_dir'] = f['trend30']*d
    f['trend60_dir'] = f['trend60']*d
    if i>=100:
        sma100 = sum(atrs[i-99:i+1])/100
        f['atr_ratio'] = a/sma100 if sma100>0 else 1.0
    else:
        f['atr_ratio'] = 1.0
    f['atr_chg20'] = a/atrs[i-20] if (i>=20 and atrs[i-20]>0) else 1.0
    ma50 = sum(B[k].c for k in range(i-49,i+1))/50 if i>=50 else B[i].c
    f['dist_ma50'] = (B[i].c - ma50)/a if a>0 else 0.0
    f['dist_ma50_dir'] = f['dist_ma50']*d
    net = abs(B[i].c - B[i-30].c)
    path = sum(abs(B[k].c-B[k-1].c) for k in range(i-29,i+1))
    f['eff30'] = net/path if path>0 else 0.0
    mom3 = sum(1 for k in range(i-2,i+1) if (B[k].c-B[k].o)*d>0)
    f['mom3_dir'] = mom3
    return f

def build(symbols):
    rows=[]
    for s in symbols:
        T,B = w1.load(s)
        if len(B)<200: continue
        atrs=[atr14(B,k) for k in range(len(B))]
        for (t,d,sd,td,i,B2,cost) in g.fvg_signals(s):
            r = wins(simulate(B,i,d,stop_dist=sd,target_dist=td,cost=cost))
            f = feats(B, atrs, i, d)
            f.update({'sym':s,'year':t.year,'month':t.month,'dir':d,'R':r,'i':i,'cls':'metals'})
            rows.append(f)
    return rows

if __name__=='__main__':
    rows = build(METALS)
    featkeys=['trend30_dir','trend60_dir','frac_up30','atr_ratio','atr_chg20','dist_ma50_dir','eff30','mom3_dir']
    print('=== XAUUSD-only regime contrast (apples-to-apples) ===')
    for grp,yrs in [('WIN(17,18,24)',[2017,2018,2024]),('LOSE(15,23)',[2015,2023])]:
        sub=[x for x in rows if x['sym']=='XAUUSD' and x['year'] in yrs]
        ev = sum(x['R'] for x in sub)/max(1,len(sub))
        print(f'\n{grp}  n={len(sub)} EV={ev:+.3f}')
        for k in featkeys:
            vals=[x[k] for x in sub]
            print(f'   {k:14s} mean={statistics.mean(vals):+.3f} med={statistics.median(vals):+.3f}')

    print('\n=== ALL metals: winners vs losers (R>0 vs R<=0) feature means ===')
    W=[x for x in rows if x['R']>0]; L=[x for x in rows if x['R']<=0]
    print(f'  winners n={len(W)}  losers n={len(L)}')
    for k in featkeys:
        print(f'   {k:14s} win={statistics.mean([x[k] for x in W]):+.3f} lose={statistics.mean([x[k] for x in L]):+.3f}')
