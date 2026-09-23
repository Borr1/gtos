import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate
from collections import defaultdict

def full_report(t):
    yr=defaultdict(list)
    for y,r,d in t: yr[y].append(r)
    rep={}
    for y in sorted(yr):
        rs=yr[y]; rep[y]=dict(n=len(rs),R=round(statistics.mean(rs),4),win=round(100*sum(1 for x in rs if x>0)/len(rs),1),tot=round(sum(rs),1))
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    fww=round(100*sum(1 for y,r,d in t if y>=2025 and r>0)/fwdn,1) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    return trnR,trnn,fwdR,fwdn,fww,rep

# Confirm JPY autocorrelation vs pure FX (mean ac60)
print('=== mean ac60 by symbol (persistence) ===')
for grp,name in [(JPY,'JPY'),(PURE_FX,'PUREFX')]:
    acs=[]
    for sym in grp:
        T,B,A=get(sym)
        for i in range(110,len(B),5):
            a=ac60(B,i)
            if a is not None: acs.append(a)
    print(f'{name}: mean ac60={statistics.mean(acs):+.4f} n={len(acs)}')

# TREND-PULLBACK long/short on JPY:
# HTF trend up (htf_trend==1). Wait for a pullback: current bar is a down bar (c<o) closing in lower part,
# but trend still up. Enter LONG next bar resumption (bar closes back up). Tight stop below pullback low, wide target.
def trend_pullback(symbols, lb, pull_min, stop_buf, tgt_m, maxbars=20, use_resume=True):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-2):
            a=A[i]
            if a<=0: continue
            tr=w1.htf_trend(B,i,lb)
            if tr==0: continue
            # pullback bar against trend
            if tr==1:
                if not (B[i].c<B[i].o): continue   # down bar = pullback in uptrend
                # resumption confirm next bar
                j=i+1
                if use_resume:
                    if not (B[j].c>B[i].h): continue  # break of pullback bar high
                    d=1; sd=(B[j].c-B[i].l)+stop_buf*a
                else:
                    d=1; j=i; sd=(B[i].c-B[i].l)+stop_buf*a
            else:
                if not (B[i].c>B[i].o): continue
                j=i+1
                if use_resume:
                    if not (B[j].c<B[i].l): continue
                    d=-1; sd=(B[i].h-B[j].c)+stop_buf*a
                else:
                    d=-1; j=i; sd=(B[i].h-B[i].c)+stop_buf*a
            if sd<=0: continue
            r=simulate(B,j,d,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
            trades.append((T[j].year,wins(r),d))
    return trades

print('=== TREND-PULLBACK (resumption) ===')
for grp,name in [(JPY,'JPY'),(FX,'FX'),(PURE_FX,'PUREFX')]:
    for lb in [20,30]:
        for tgt in [1.5,2.0,3.0]:
            t=trend_pullback(grp,lb,0,0.2,tgt)
            tr,tn,fr,fn,fw,rep=full_report(t)
            if tn<150: continue
            flag='<<<' if (tr>0 and fr>0) else ''
            print(f'{name} lb{lb} tgt{tgt}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} fw{fw}% {flag}')
