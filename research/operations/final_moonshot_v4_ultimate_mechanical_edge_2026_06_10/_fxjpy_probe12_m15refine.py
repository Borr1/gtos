import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
import os, csv, statistics
from datetime import datetime
from collections import defaultdict
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1

# PROBE 12: refine the JPY London-open momentum (lon8, 1hr impulse -> ride).
# Check per-SYMBOL, per-MONTH stability (no train window, so robustness = stability).
# Try trend-gate (only ride impulses aligned with H4-ish trend), trail exit, and
# an impulse-strength filter (only ride when the 1hr impulse is large enough).
M15DIR='/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/bridge_ftmo_m15_20250601_20260610'
JPY=['AUDJPY','CHFJPY','EURJPY','GBPJPY','USDJPY']
def wins(r): return max(-1.3,min(5.0,r))
_C={}
def load_m15(sym):
    if sym in _C: return _C[sym]
    p=os.path.join(M15DIR,f'{sym}_M15.csv'); T=[];B=[]
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t=datetime.strptime(row['time'],'%Y-%m-%d %H:%M:%S')
                B.append(Bar(float(row['open']),float(row['high']),float(row['low']),float(row['close']),float(row.get('volume',0) or 0))); T.append(t)
            except: continue
    A=[atr14(B,i) for i in range(len(B))]; _C[sym]=(T,B,A); return _C[sym]

# returns list of (date, sym, netR)
def london_mom(symbols, ls, lw, stop_m, tgt_m, maxbars, trail=None, imp_min=0.0, trend_lb=0):
    out=[]
    for sym in symbols:
        T,B,A=load_m15(sym); cost=w1.cost_for(sym)
        byday=defaultdict(list)
        for i,t in enumerate(T): byday[t.date()].append(i)
        for day,idxs in sorted(byday.items()):
            lon=[i for i in idxs if T[i].hour>=ls]
            if len(lon)<lw+2: continue
            i0=lon[0]; iw=lon[lw-1]
            if i0<max(20,trend_lb): continue
            a=A[iw]
            if a<=0: continue
            imp=B[iw].c-B[i0].o
            if abs(imp)<imp_min*a: continue
            d=1 if imp>0 else -1
            if trend_lb>0:
                tr=1 if B[iw].c>B[iw-trend_lb].c else -1
                if tr!=d: continue
            if trail is not None:
                arm,gap=trail
                r=simulate(B,iw,d,stop_dist=stop_m*a,trail_arm=arm*stop_m*a,trail_gap=gap*stop_m*a,maxbars=maxbars,cost=cost)
            else:
                r=simulate(B,iw,d,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=maxbars,cost=cost)
            out.append((day,sym,wins(r)))
    return out

def summarize(out,label):
    if not out: print(label,'NO TRADES'); return
    rs=[r for _,_,r in out]; R=statistics.mean(rs); n=len(rs); w=100*sum(1 for r in rs if r>0)/n
    print(f'{label}: R={R:+.4f} n={n} win={w:.1f}%')
    return R,n,w

print('=== headline: JPY lon8 lw4 s1.0/t2.0 ===')
base=london_mom(JPY,8,4,1.0,2.0,40)
summarize(base,'BASE')
# per-symbol
print(' per-symbol:')
bs=defaultdict(list)
for day,sym,r in base: bs[sym].append(r)
for sym in JPY:
    rs=bs[sym]
    if rs: print(f'   {sym}: R={statistics.mean(rs):+.4f} n={len(rs)} win={100*sum(1 for x in rs if x>0)/len(rs):.1f}%')
# per-month
print(' per-month:')
bm=defaultdict(list)
for day,sym,r in base: bm[(day.year,day.month)].append(r)
for k in sorted(bm):
    rs=bm[k]; print(f'   {k}: R={statistics.mean(rs):+.4f} n={len(rs)}')

print('=== variants ===')
summarize(london_mom(JPY,8,4,1.0,2.5,40),'t2.5')
summarize(london_mom(JPY,8,4,1.0,3.0,48),'t3.0 mb48')
summarize(london_mom(JPY,8,4,1.0,2.0,40,trail=(1.5,1.0)),'trail arm1.5 gap1.0')
summarize(london_mom(JPY,8,4,1.0,2.0,40,trail=(2.0,1.0)),'trail arm2.0 gap1.0')
print('--- impulse-strength filter (only ride strong 1hr impulses) ---')
for im in [0.5,0.8,1.0,1.2]:
    summarize(london_mom(JPY,8,4,1.0,2.0,40,imp_min=im),f'imp>={im}ATR')
print('--- trend-gate (M15 trend over N bars aligned) ---')
for lb in [20,40]:
    summarize(london_mom(JPY,8,4,1.0,2.0,40,trend_lb=lb),f'trend_lb{lb}')
print('--- best combo: strong impulse + wider target/trail ---')
for im in [0.8,1.0]:
    summarize(london_mom(JPY,8,4,1.0,2.5,48,imp_min=im),f'imp>={im} t2.5')
    summarize(london_mom(JPY,8,4,1.0,2.0,48,imp_min=im,trail=(2.0,1.0)),f'imp>={im} trail2/1')
print('=== sanity: same on PURE FX (should be ~flat/neg) ===')
PUREFX=['AUDUSD','EURGBP','EURUSD','GBPUSD','NZDUSD','USDCAD','USDCHF']
summarize(london_mom(PUREFX,8,4,1.0,2.0,40),'PUREFX base')
summarize(london_mom(PUREFX,8,4,1.0,2.0,40,imp_min=1.0),'PUREFX imp>=1.0')
