import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate
from collections import defaultdict

# ============================================================================
# PROBE 9: JPY EARLY-WEEK / CARRY long bias as a tradeable geometry sleeve.
# Lead from probe5b: JPY mean H4 bar return Mon +0.042, Tue +0.017, Wed +0.030,
#   Thu -0.009, Fri -0.009 (ATR units). Carry pairs drift UP early week.
# Build it properly: entry on a specific day/hour, in trend-aligned direction,
# with ATR geometry, train(<=2024)/forward(2025-26) split, per-year, per-symbol.
# ============================================================================

def full_report(t):
    yr=defaultdict(list)
    for y,r,d in t: yr[y].append(r)
    rep={}
    for y in sorted(yr):
        rs=yr[y]; rep[y]=dict(n=len(rs),R=round(statistics.mean(rs),4),
            win=round(100*sum(1 for x in rs if x>0)/len(rs),1),tot=round(sum(rs),1))
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    fww=round(100*sum(1 for y,r,d in t if y>=2025 and r>0)/fwdn,1) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    trw=round(100*sum(1 for y,r,d in t if y<=2024 and r>0)/trnn,1) if trnn else 0
    return trnR,trnn,trw,fwdR,fwdn,fww,rep

# Long-only on early-week days, optionally gated by htf trend up. Geometry stop/target ATR mult.
def dow_long(symbols, days, hours, stop_m, tgt_m, trend_gate=False, trend_lb=30, maxbars=12, longonly=True, dir_override=None):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-1):
            if T[i].weekday() not in days: continue
            if hours is not None and T[i].hour not in hours: continue
            a=A[i]
            if a<=0: continue
            d=1 if longonly else dir_override
            if trend_gate:
                tr=w1.htf_trend(B,i,trend_lb)
                if tr!=d: continue
            r=simulate(B,i,d,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=maxbars,cost=cost)
            trades.append((T[i].year,wins(r),d))
    return trades

print('=== 9a: JPY long, early-week days {Mon,Tue,Wed}, ALL hours, geometry sweep ===')
for sm,tm in [(1.0,1.0),(1.0,1.5),(1.0,2.0),(1.5,1.5),(1.5,2.0),(2.0,2.0)]:
    t=dow_long(JPY,{0,1,2},None,sm,tm)
    tr,tn,trw,fr,fn,fw,rep=full_report(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f's{sm}/t{tm}: TRAIN {tr:+.3f} n{tn:5d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 9b: JPY long early-week + HTF TREND-UP gate (carry+momentum) ===')
for lb in [20,30]:
    for sm,tm in [(1.0,1.5),(1.0,2.0),(1.5,2.0)]:
        t=dow_long(JPY,{0,1,2},None,sm,tm,trend_gate=True,trend_lb=lb)
        tr,tn,trw,fr,fn,fw,rep=full_report(t)
        flag='<<<' if (tr>0 and fr>0) else ''
        print(f'lb{lb} s{sm}/t{tm}: TRAIN {tr:+.3f} n{tn:5d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 9c: which ENTRY HOUR carries the early-week drift? (long, {Mon,Tue,Wed}) ===')
for hr in [0,4,8,12,16,20]:
    t=dow_long(JPY,{0,1,2},{hr},1.0,1.5)
    tr,tn,trw,fr,fn,fw,rep=full_report(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f'h{hr:2d} s1.0/t1.5: TRAIN {tr:+.3f} n{tn:5d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 9d: per-DAY isolation (long, all hours, s1/t1.5) ===')
for dname,dset in [('Mon',{0}),('Tue',{1}),('Wed',{2}),('Thu',{3}),('Fri',{4})]:
    t=dow_long(JPY,dset,None,1.0,1.5)
    tr,tn,trw,fr,fn,fw,rep=full_report(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f'{dname} long: TRAIN {tr:+.3f} n{tn:5d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 9e: late-week SHORT (Thu/Fri), JPY ===')
for sm,tm in [(1.0,1.0),(1.0,1.5),(1.0,2.0)]:
    t=dow_long(JPY,{3,4},None,sm,tm,longonly=False,dir_override=-1)
    tr,tn,trw,fr,fn,fw,rep=full_report(t)
    flag='<<<' if (tr>0 and fr>0) else ''
    print(f'short s{sm}/t{tm}: TRAIN {tr:+.3f} n{tn:5d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')
