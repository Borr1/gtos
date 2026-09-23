import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate
import gold_sleeve_strategy as g

def summ(t):
    rep=report_by_year(t)
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    fww=round(100*sum(1 for y in fwd for x in [0])/1,1) if fwdn else 0
    return trnR,trnn,fwdR,fwdn,rep

# A: FVG mechanic on FX with ac60 gate (the EXACT baseline mechanic, just on FX)
print('=== A: FVG-retest continuation on FX, ac60 gate, scale-out exit ===')
import compounding_sleeve as cs
def fvg_ac(symbols, ac_lo):
    trades=[]
    for sym in symbols:
        sigs=g.fvg_signals(sym)
        T,B,A=get(sym)
        for (t,d,sd,td,i,Bx,cost) in sigs:
            ac=ac60(B,i)
            if ac is None or ac<ac_lo: continue
            vr=cs.vol_ratio(A,i)
            res=cs.exit_state_d(B,i,d,sd,vr,cost)
            trades.append((t.year, wins(res['R']), d))
    return trades
for ac_lo in [-1, 0.0, 0.10]:
    t=fvg_ac(FX,ac_lo); tr,tn,fr,fn,rep=summ(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f'FX ac>={ac_lo}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} {flag}')
for ac_lo in [-1, 0.10]:
    t=fvg_ac(JPY,ac_lo); tr,tn,fr,fn,rep=summ(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f'JPY ac>={ac_lo}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} {flag}')

# B: trend-following long-only metals-style structure on FX/JPY
# enter in direction of htf trend at each bar, but only fresh trend onset; geometry 0.5/2.0
print('=== B: HTF-trend continuation (metals-style 0.5stop/2.0tgt), per regime ===')
def trendfollow(symbols, stop_m, tgt_m, lb=10, maxbars=24, longonly=False):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-1):
            a=A[i]
            if a<=0: continue
            d = 1 if B[i].c>B[i-lb].c else -1
            if longonly and d<0: continue
            r=simulate(B,i,d,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=maxbars,cost=cost)
            trades.append((T[i].year, wins(r), d))
    return trades
for grp,name in [(FX,'FX'),(JPY,'JPY')]:
    for sm,tm in [(0.5,2.0),(1.0,2.0),(0.5,3.0)]:
        t=trendfollow(grp,sm,tm); tr,tn,fr,fn,_=summ(t)
        flag='<<<' if (tr>0 and fr>0) else ''
        print(f'{name} s{sm}/t{tm}: TRAIN {tr:+.3f} n{tn:5d} | FWD {fr:+.3f} n{fn:5d} {flag}')
