import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate

def full_report(t):
    rep=report_by_year(t)
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    fww=round(100*sum(1 for _,r,_ in t if (_>=2025 and r>0))/fwdn,1) if fwdn else 0
    return trnR,trnn,fwdR,fwdn,fww,rep

# Confirmed-reversion with TRAIL runner (capture the reversal run). 
# Mechanic: bar i body>=ext*ATR; bar i+1 closes back through bar i midpoint and against bar i; enter at i+1 close.
# stop beyond bar i extreme; use trail (arm, gap) instead of fixed target to ride the swing.
def conf_rev_trail(symbols, ext, stop_buf, arm_m, gap_m, ac_hi=None, maxbars=24, fixed_tgt=None, dow_filter=False):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym); isjpy = (sym in JPY)
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
            d=0; sd=0
            if body>0 and B[j].c<mid and B[j].c<B[j].o:
                d=-1; sd=(B[i].h-B[j].c)+stop_buf*a
            elif body<0 and B[j].c>mid and B[j].c>B[j].o:
                d=+1; sd=(B[j].c-B[i].l)+stop_buf*a
            if d==0 or sd<=0: continue
            if dow_filter and isjpy:
                # JPY early-week long bias: allow shorts only Thu/Fri, longs only Mon-Wed
                wd=T[j].weekday()
                if d==1 and wd>=3: continue
                if d==-1 and wd<3: continue
            if fixed_tgt is not None:
                r=simulate(B,j,d,stop_dist=sd,target_dist=fixed_tgt*sd,maxbars=maxbars,cost=cost)
            else:
                r=simulate(B,j,d,stop_dist=sd,trail_arm=arm_m*sd,trail_gap=gap_m*sd,maxbars=maxbars,cost=cost)
            trades.append((T[j].year,wins(r),d))
    return trades

print('=== Confirmed-rev with TRAIL runner, JPY ===')
for ext in [1.0,1.2]:
    for arm,gap in [(1.0,1.0),(1.5,1.0),(2.0,1.5)]:
        t=conf_rev_trail(JPY,ext,0.2,arm,gap,ac_hi=None)
        tr,tn,fr,fn,fw,rep=full_report(t)
        if tn<150: continue
        flag='<<<' if (tr>-0.02 and fr>0) else ''
        print(f'JPY ext{ext} arm{arm}/gap{gap}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} win{fw}% {flag}')

print('=== Confirmed-rev fixed wide target, FULL FX+JPY, per-year detail for best ===')
allfx=FX
for ext in [1.0,1.2,1.5]:
    for tgt in [2.0,2.5,3.0]:
        t=conf_rev_trail(allfx,ext,0.2,0,0,ac_hi=None,fixed_tgt=tgt)
        tr,tn,fr,fn,fw,rep=full_report(t)
        if tn<150: continue
        flag='<<<' if (tr>-0.02 and fr>0) else ''
        print(f'ALLFX ext{ext} tgt{tgt}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} win{fw}% {flag}')

# detail dump for the headline JPY config
print('=== DETAIL: JPY ext1.0 fixed tgt2.0 ===')
t=conf_rev_trail(JPY,1.0,0.2,0,0,ac_hi=None,fixed_tgt=2.0)
tr,tn,fr,fn,fw,rep=full_report(t)
for y in sorted(rep): print(' ',y,rep[y])
