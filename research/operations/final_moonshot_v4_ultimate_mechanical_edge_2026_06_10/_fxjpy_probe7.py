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

# Asian-range breakout into London/NY. 
# H4 bars at 0(Asia),4(Asia/early),8(London),12(NY-am),16(NY),20(late)
# Setup: at the London bar (hour 8), if it CLOSES beyond the [0..4] (Asian session) range -> breakout continuation.
# Enter at hour-8 close in breakout direction; stop = other side of asian range; target multiple.
def asian_breakout(symbols, brk_buf, stop_mode, tgt_m, london_hour=8, asia_hours=(0,4), maxbars=12):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        # index by date
        for i in range(110,len(B)-1):
            if T[i].hour!=london_hour: continue
            a=A[i]
            if a<=0: continue
            # find asian bars same calendar day (the 0 and 4 bars preceding i)
            ah=[]; k=i-1
            while k>=0 and (T[i]-T[k]).total_seconds()<=12*3600:
                if T[k].hour in asia_hours: ah.append(k)
                k-=1
            if len(ah)<2: continue
            ahi=max(B[x].h for x in ah); alo=min(B[x].l for x in ah)
            arng=ahi-alo
            if arng<=0: continue
            c=B[i].c
            d=0
            if c>ahi+brk_buf*a: d=1
            elif c<alo-brk_buf*a: d=-1
            if d==0: continue
            if stop_mode=='range':
                sd=(c-alo) if d>0 else (ahi-c)
            else:
                sd=stop_mode*a
            if sd<=0: continue
            r=simulate(B,i,d,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
            trades.append((T[i].year,wins(r),d))
    return trades

print('=== Asian-range breakout @ London (h8) ===')
for grp,name in [(FX,'FX'),(JPY,'JPY'),(PURE_FX,'PUREFX')]:
    for buf in [0.0,0.1]:
        for sm in [0.5,1.0]:
            for tgt in [1.0,1.5,2.0]:
                t=asian_breakout(grp,buf,sm,tgt)
                tr,tn,fr,fn,fw,rep=full_report(t)
                if tn<150: continue
                flag='<<<' if (tr>0 and fr>0) else ''
                print(f'{name} buf{buf} s{sm}/t{tgt}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} fw{fw}% {flag}')

print('=== Asian-range breakout @ NY (h12) ===')
for grp,name in [(FX,'FX'),(JPY,'JPY')]:
    for sm in [0.5,1.0]:
        for tgt in [1.5,2.0]:
            t=asian_breakout(grp,0.0,sm,tgt,london_hour=12,asia_hours=(0,4,8))
            tr,tn,fr,fn,fw,rep=full_report(t)
            if tn<150: continue
            flag='<<<' if (tr>0 and fr>0) else ''
            print(f'{name} s{sm}/t{tgt}: TRAIN {tr:+.3f} n{tn:4d} | FWD {fr:+.3f} n{fn:4d} fw{fw}% {flag}')
