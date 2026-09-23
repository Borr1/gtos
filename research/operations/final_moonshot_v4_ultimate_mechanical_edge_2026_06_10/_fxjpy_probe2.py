import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate

# Probe 2: ac60 regime split. Continuation in HIGH ac, reversion in LOW ac.
# Also require the session bar be "extended" (|c-o| >= 0.8*ATR) so we fade real extension.
def run(symbols, mode, ac_lo, ac_hi, ext_min, stop_m, tgt_m, hours=None):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110, len(B)-1):
            if hours and T[i].hour not in hours: continue
            a=A[i]
            if a<=0: continue
            ac=ac60(B,i)
            if ac is None: continue
            if ac_lo is not None and ac<ac_lo: continue
            if ac_hi is not None and ac>=ac_hi: continue
            body=abs(B[i].c-B[i].o)
            if body < ext_min*a: continue
            bardir = 1 if B[i].c>B[i].o else -1
            d = bardir if mode=='cont' else -bardir
            sd=stop_m*a; td=tgt_m*a
            r=simulate(B,i,d,stop_dist=sd,target_dist=td,maxbars=24,cost=cost)
            trades.append((T[i].year, wins(r), d))
    return trades

def summ(t):
    rep=report_by_year(t)
    fwd=[y for y in rep if y>=2025]; fwdn=sum(rep[y]['n'] for y in fwd)
    fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
    trn=[y for y in rep if y<=2024]; trnn=sum(rep[y]['n'] for y in trn)
    trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
    fwn=round(100*sum(1 for y in fwd for _ in range(0)),1)
    return trnR,trnn,fwdR,fwdn,rep

print('=== REVERSION in LOW ac, extended bars (fade) ===')
for ac_hi in [0.0, -0.05, -0.10]:
    for ext in [0.8, 1.2]:
        for stop_m,tgt_m in [(1.0,1.0),(1.0,1.5),(1.5,1.0)]:
            t=run(FX,'rev',None,ac_hi,ext,stop_m,tgt_m)
            tr,tn,fr,fn,_=summ(t)
            flag='<<<' if (tr>0 and fr>0) else ''
            print(f'ac<{ac_hi:+.2f} ext>{ext} s{stop_m}/t{tgt_m}: TRAIN {tr:+.3f} n{tn:5d} | FWD {fr:+.3f} n{fn:5d} {flag}')

print('=== CONTINUATION in HIGH ac, extended bars ===')
for ac_lo in [0.05, 0.10, 0.15]:
    for ext in [0.8, 1.2]:
        for stop_m,tgt_m in [(1.0,1.5),(1.0,2.0),(0.7,2.0)]:
            t=run(FX,'cont',ac_lo,None,ext,stop_m,tgt_m)
            tr,tn,fr,fn,_=summ(t)
            flag='<<<' if (tr>0 and fr>0) else ''
            print(f'ac>{ac_lo:.2f} ext>{ext} s{stop_m}/t{tgt_m}: TRAIN {tr:+.3f} n{tn:5d} | FWD {fr:+.3f} n{fn:5d} {flag}')
