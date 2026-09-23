import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate

# Probe 3: PULLBACK-entry reversion. In LOW ac regime, after price makes an N-bar high/low (extreme),
# WAIT for a pullback of >= pb*ATR back into the range, then enter the fade with a tight stop beyond the extreme.
# This is the proper R:R structure (stop = distance to extreme, target = back toward mean).
def run(symbols, ac_hi, ext_lb, pb_frac, stop_buf, tgt_m, maxbars=20):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        i=ext_lb+110
        while i < len(B)-1:
            a=A[i]
            if a<=0: i+=1; continue
            ac=ac60(B,i)
            if ac is None or ac>=ac_hi: i+=1; continue
            # recent extreme over ext_lb bars
            hh=max(B[k].h for k in range(i-ext_lb,i+1)); ll=min(B[k].l for k in range(i-ext_lb,i+1))
            rng=hh-ll
            if rng < 1.0*a: i+=1; continue
            c=B[i].c
            # Is price near the HIGH extreme (fade short) ?
            if (hh-c) <= pb_frac*rng and (c-ll) > 0.5*rng:
                # short fade: stop above hh
                sd = (hh - c) + stop_buf*a
                if sd<=0: i+=1; continue
                r=simulate(B,i,-1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
                trades.append((T[i].year, wins(r), -1)); i+=1; continue
            if (c-ll) <= pb_frac*rng and (hh-c) > 0.5*rng:
                sd = (c - ll) + stop_buf*a
                if sd<=0: i+=1; continue
                r=simulate(B,i,+1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
                trades.append((T[i].year, wins(r), +1)); i+=1; continue
            i+=1
    return trades

def summ(t):
    rep=report_by_year(t)
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    return trnR,trnn,fwdR,fwdn,rep

for ac_hi in [0.0,-0.05]:
    for lb in [6,10]:
        for pb in [0.15,0.25]:
            for tgt in [1.5,2.0,3.0]:
                t=run(FX,ac_hi,lb,pb,0.25,tgt)
                tr,tn,fr,fn,_=summ(t)
                flag='<<<' if (tr>0 and fr>0) else ''
                print(f'ac<{ac_hi:+.2f} lb{lb} pb{pb} tgt{tgt}: TRAIN {tr:+.3f} n{tn:5d} | FWD {fr:+.3f} n{fn:5d} {flag}')
