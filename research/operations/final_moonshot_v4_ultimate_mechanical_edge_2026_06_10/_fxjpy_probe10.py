import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
from _fxjpy_harness import *
from geometry_lib import simulate
from collections import defaultdict

# ============================================================================
# PROBE 10: SELECTIVE JPY carry-long. The raw early-week drift is real but
# too small per-bar to beat the 0.1148R cost when traded every bar.
# Make it selective: only take EARLY-WEEK LONGS that ALSO have a structural
# pullback-in-uptrend (buy the dip in a carry uptrend, on a carry-favourable day).
# Few trades, higher quality. Train/forward split, per-year, per-symbol.
# Also: test pure OVERNIGHT carry (hold from h20 close to next bar) — the
# classic JPY carry edge is the overnight roll, not intraday.
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

def persym(t):
    d=defaultdict(lambda:defaultdict(list))
    return d

# --- 10a: carry-long PULLBACK in uptrend on early-week days ---
# Setup: htf trend up (close>close[-lb]); current bar is a down/inside pullback bar;
# enter LONG at NEXT bar that closes above the pullback bar high (resumption);
# only on Mon/Tue/Wed (carry tailwind). tight stop below pullback low, ATR-mult target.
def carry_pullback(symbols, days, lb, stop_buf, tgt_m, maxbars=16, require_resume=True):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-2):
            a=A[i]
            if a<=0: continue
            if w1.htf_trend(B,i,lb)!=1: continue
            if not (B[i].c<B[i].o): continue  # pullback (down bar) in uptrend
            j=i+1
            if T[j].weekday() not in days: continue  # carry day on the entry bar
            if require_resume and not (B[j].c>B[i].h): continue
            sd=(B[j].c-B[i].l)+stop_buf*a
            if sd<=0: continue
            r=simulate(B,j,+1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
            trades.append((T[j].year,wins(r),+1))
    return trades

print('=== 10a: carry-long pullback-resumption, early-week (Mon-Wed), JPY ===')
best=None
for lb in [20,30,40]:
    for tgt in [1.5,2.0,2.5,3.0]:
        t=carry_pullback(JPY,{0,1,2},lb,0.2,tgt)
        tr,tn,trw,fr,fn,fw,rep=full_report(t)
        if tn<100: continue
        flag='<<<' if (tr>0 and fr>0) else ''
        print(f'lb{lb} tgt{tgt}: TRAIN {tr:+.3f} n{tn:4d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 10b: same but ALL days (control, to isolate the day effect) ===')
for lb in [30]:
    for tgt in [1.5,2.0,2.5,3.0]:
        t=carry_pullback(JPY,{0,1,2,3,4},lb,0.2,tgt)
        tr,tn,trw,fr,fn,fw,rep=full_report(t)
        flag='<<<' if (tr>0 and fr>0) else ''
        print(f'ALLDAYS lb{lb} tgt{tgt}: TRAIN {tr:+.3f} n{tn:4d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

print('=== 10c: PURE OVERNIGHT carry hold (enter h20 close, exit at maxbars, long carry day) ===')
# carry = long JPY-cross (AUDJPY etc) which has positive carry. Hold 1 bar (overnight).
def overnight(symbols, entry_hours, days, hold_bars, stop_m, tgt_m, dir=1, trend_gate=False):
    trades=[]
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-hold_bars-1):
            if T[i].hour not in entry_hours: continue
            if days is not None and T[i].weekday() not in days: continue
            a=A[i]
            if a<=0: continue
            if trend_gate and w1.htf_trend(B,i,30)!=dir: continue
            r=simulate(B,i,dir,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=hold_bars,cost=cost)
            trades.append((T[i].year,wins(r),dir))
    return trades
# AUDJPY/NZDJPY style positive-carry: AUDJPY only in our set among true high-carry; test all JPY long
for hold in [1,2]:
    for sm,tm in [(2.0,3.0),(3.0,3.0)]:
        t=overnight(['AUDJPY'],{20},{0,1,2,3},hold,sm,tm,dir=1,trend_gate=True)
        tr,tn,trw,fr,fn,fw,rep=full_report(t)
        if tn<50: continue
        flag='<<<' if (tr>0 and fr>0) else ''
        print(f'AUDJPY overnight hold{hold} s{sm}/t{tm}: TRAIN {tr:+.3f} n{tn:4d} w{trw}% | FWD {fr:+.3f} n{fn:4d} w{fw}% {flag}')

# --- 10d: DETAIL for best 10a config if any positive ---
print('=== 10d: per-year + per-symbol detail, JPY carry-pullback lb30 tgt2.0 ===')
def carry_pullback_ps(symbols, days, lb, stop_buf, tgt_m, maxbars=16):
    bysym=defaultdict(list)
    for sym in symbols:
        T,B,A=get(sym); cost=w1.cost_for(sym)
        for i in range(110,len(B)-2):
            a=A[i]
            if a<=0: continue
            if w1.htf_trend(B,i,lb)!=1: continue
            if not (B[i].c<B[i].o): continue
            j=i+1
            if T[j].weekday() not in days: continue
            if not (B[j].c>B[i].h): continue
            sd=(B[j].c-B[i].l)+stop_buf*a
            if sd<=0: continue
            r=simulate(B,j,+1,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
            bysym[sym].append((T[j].year,wins(r),+1))
    return bysym
bs=carry_pullback_ps(JPY,{0,1,2},30,0.2,2.0)
for sym in JPY:
    tt=bs[sym]
    if not tt: continue
    tr,tn,trw,fr,fn,fw,rep=full_report(tt)
    print(f'  {sym}: TRAIN {tr:+.3f} n{tn} | FWD {fr:+.3f} n{fn} w{fw}%')
allt=[x for sym in JPY for x in bs[sym]]
tr,tn,trw,fr,fn,fw,rep=full_report(allt)
print('  --- ALL JPY per-year ---')
for y in sorted(rep): print('   ',y,rep[y])
