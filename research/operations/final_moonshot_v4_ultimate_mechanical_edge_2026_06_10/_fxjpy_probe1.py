import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate

# Probe 1: SESSION-OF-DAY directional bias.
# For each H4 session bar (hour in {0,4,8,12,16,20}), test:
#   continuation: enter in direction of the just-closed bar (c>o => long)
#   reversion: fade it
# gated by ac60 regime (persist vs range), with simple geometry stop=1ATR target=1.5ATR.
# leak-free: at close of bar i we know its direction (closed); we enter next bar open ~ B[i].c approx (simulate from i).

def run(symbols, mode, hour, ac_lo=None, ac_hi=None, stop_m=1.0, tgt_m=1.5):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110, len(B)-1):
            if T[i].hour!=hour: continue
            a=A[i]
            if a<=0: continue
            ac=ac60(B,i)
            if ac is None: continue
            if ac_lo is not None and ac<ac_lo: continue
            if ac_hi is not None and ac>=ac_hi: continue
            bardir = 1 if B[i].c>B[i].o else (-1 if B[i].c<B[i].o else 0)
            if bardir==0: continue
            d = bardir if mode=='cont' else -bardir
            sd=stop_m*a; td=tgt_m*a
            r=simulate(B,i,d,stop_dist=sd,target_dist=td,maxbars=24,cost=cost)
            trades.append((T[i].year, wins(r), d))
    return trades

results={}
for mode in ['cont','rev']:
    for hour in [0,4,8,12,16,20]:
        # all regimes
        t=run(FX,mode,hour)
        rep=report_by_year(t)
        fwd=[y for y in rep if y>=2025]
        fwdn=sum(rep[y]['n'] for y in fwd); fwdR=round(sum(rep[y]['R']*rep[y]['n'] for y in fwd)/fwdn,4) if fwdn else 0
        trn=[y for y in rep if y<=2024]
        trnn=sum(rep[y]['n'] for y in trn); trnR=round(sum(rep[y]['R']*rep[y]['n'] for y in trn)/trnn,4) if trnn else 0
        results[f'{mode}_h{hour}']=dict(trainR=trnR,trainN=trnn,fwdR=fwdR,fwdN=fwdn)
        print(f'{mode} h{hour:2d}: TRAIN R={trnR:+.3f} n={trnn:5d} | FWD R={fwdR:+.3f} n={fwdn:5d}')
