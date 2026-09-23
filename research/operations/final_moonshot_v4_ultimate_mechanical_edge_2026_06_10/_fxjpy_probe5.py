import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate

def summ(t):
    rep=report_by_year(t)
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    return trnR,trnn,fwdR,fwdn,rep

# Probe 5a: CONFIRMED reversion. Bar i extended (body>1ATR) AND bar i+1 closes back through bar i's midpoint
# (reversal confirmation). Enter at i+1 close, stop beyond i's extreme, target toward mean.
def conf_rev(symbols, ext, stop_buf, tgt_m, ac_hi=None, maxbars=16):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-2):
            a=A[i]
            if a<=0: continue
            if ac_hi is not None:
                ac=ac60(B,i)
                if ac is None or ac>=ac_hi: continue
            body=B[i].c-B[i].o
            if abs(body)<ext*a: continue
            mid=(B[i].o+B[i].c)/2
            j=i+1
            if body>0:  # up bar -> look for down confirmation -> short
                if B[j].c<mid and B[j].c<B[j].o:
                    sd=(B[i].h-B[j].c)+stop_buf*a
                    if sd<=0: continue
                    r=simulate(B,j,-1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
                    trades.append((T[j].year,wins(r),-1))
            else:
                if B[j].c>mid and B[j].c>B[j].o:
                    sd=(B[j].c-B[i].l)+stop_buf*a
                    if sd<=0: continue
                    r=simulate(B,j,+1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
                    trades.append((T[j].year,wins(r),+1))
    return trades
print('=== 5a: CONFIRMED reversion (i extended, i+1 reverses through mid) ===')
for grp,name in [(FX,'FX'),(JPY,'JPY')]:
    for ext in [1.0,1.5]:
        for tgt in [1.0,1.5,2.0]:
            for ac_hi in [None,0.0]:
                t=conf_rev(grp,ext,0.2,tgt,ac_hi)
                tr,tn,fr,fn,_=summ(t)
                if tn<150: continue
                flag='<<<' if (tr>0 and fr>0) else ''
                print(f'{name} ext{ext} tgt{tgt} ac{ac_hi}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} {flag}')

# Probe 5b: Day-of-week directional drift (JPY long bias overnight Mon/Fri etc) — pure bar return, no geometry
print('=== 5b: Day-of-week mean H4 bar return (raw, *not* tradeable yet) ===')
from collections import defaultdict
for grp,name in [(JPY,'JPY'),(PURE_FX,'PURE_FX')]:
    dow=defaultdict(list)
    for sym in grp:
        T,B,A=get(sym)
        for i in range(1,len(B)):
            a=A[i] if A[i]>0 else 1
            dow[T[i].weekday()].append((B[i].c-B[i-1].c)/a)
    print(name, {d:round(statistics.mean(v),4) for d,v in sorted(dow.items())})
