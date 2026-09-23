import sys; sys.path.insert(0,'/Users/borr/Documents/gtos/repo/ai-trading-agent'); sys.path.insert(0,'.')
import os, csv, statistics
from datetime import datetime
from collections import defaultdict
from geometry_lib import simulate, atr14, Bar
import wave1_structure_setups_ict as w1

# ============================================================================
# PROBE 11 (M15, FORWARD-ONLY 2025-06..2026-06): session-timing precision.
# M15 data only exists for the forward window so this is a SINGLE-REGIME test.
# Anything positive here is kept at SMALL confidence-weighted size (breadth),
# explicitly flagged as forward-only / single-regime confound risk.
# Tests:
#   A. Asian-range breakout into London (proper intraday resolution).
#   B. London-open momentum continuation (first London M15 impulse -> ride).
# Server hours: data is in MT5 server time; from H4 we know NY vol peaks at 16:00,
# so London ~ 08:00-12:00 server, Asian ~ 00:00-07:00 server.
# ============================================================================
M15DIR='/Users/borr/Documents/gtos/repo/ai-trading-agent/data/mt5_research_exports/bridge_ftmo_m15_20250601_20260610'
FXSYMS=['AUDJPY','AUDUSD','CHFJPY','EURGBP','EURJPY','EURUSD','GBPJPY','GBPUSD','NZDUSD','USDCAD','USDCHF','USDJPY']
JPY=['AUDJPY','CHFJPY','EURJPY','GBPJPY','USDJPY']

def wins(r): return max(-1.3,min(5.0,r))

_C={}
def load_m15(sym):
    if sym in _C: return _C[sym]
    p=os.path.join(M15DIR,f'{sym}_M15.csv')
    T=[];B=[]
    with open(p) as f:
        for row in csv.DictReader(f):
            try:
                t=datetime.strptime(row['time'],'%Y-%m-%d %H:%M:%S')
                B.append(Bar(float(row['open']),float(row['high']),float(row['low']),float(row['close']),float(row.get('volume',0) or 0)))
                T.append(t)
            except: continue
    A=[atr14(B,i) for i in range(len(B))]
    _C[sym]=(T,B,A); return _C[sym]

def rep(t):
    if not t: return (0,0,0)
    R=statistics.mean(r for r in t); n=len(t); w=round(100*sum(1 for r in t if r>0)/n,1)
    return (round(R,4),n,w)

# --- A: Asian-range breakout into London. Build daily Asian range [00:00..asia_end],
# then on the first M15 bar after london_start that closes beyond the range -> enter breakout.
def asian_breakout_m15(symbols, asia_end_h, london_start_h, london_end_h, stop_mode, tgt_m, brk_buf_atr, maxbars):
    trades=[]
    for sym in symbols:
        T,B,A=load_m15(sym); cost=w1.cost_for(sym)
        # group by date
        byday=defaultdict(list)
        for i,t in enumerate(T): byday[t.date()].append(i)
        for day,idxs in byday.items():
            asia=[i for i in idxs if T[i].hour<asia_end_h]
            if len(asia)<8: continue
            ahi=max(B[i].h for i in asia); alo=min(B[i].l for i in asia)
            arng=ahi-alo
            if arng<=0: continue
            lon=[i for i in idxs if london_start_h<=T[i].hour<london_end_h]
            done=False
            for i in lon:
                if i<20: continue
                a=A[i]
                if a<=0: continue
                c=B[i].c; d=0
                if c>ahi+brk_buf_atr*a: d=1
                elif c<alo-brk_buf_atr*a: d=-1
                if d==0: continue
                if stop_mode=='range': sd=(c-alo) if d>0 else (ahi-c)
                else: sd=stop_mode*a
                if sd<=0: continue
                r=simulate(B,i,d,stop_dist=sd,target_dist=tgt_m*sd,maxbars=maxbars,cost=cost)
                trades.append(wins(r)); done=True; break
            # only first breakout per day
    return trades

print('=== A: Asian-range breakout into London (M15, forward-only) ===')
for ae,ls,le in [(7,7,11),(8,8,12),(6,7,12)]:
    for sm in ['range',1.0]:
        for tgt in [1.0,1.5,2.0]:
            for grp,name in [(FXSYMS,'FX'),(JPY,'JPY')]:
                t=asian_breakout_m15(grp,ae,ls,le,sm,tgt,0.05,40)
                R,n,w=rep(t)
                if n<150: continue
                flag='<<<' if R>0 else ''
                print(f'{name} asiaEnd{ae} lon{ls}-{le} s{sm}/t{tgt}: FWD {R:+.3f} n{n:4d} w{w}% {flag}')

# --- B: London-open momentum continuation. At london_start, take the sign of the
# first impulse M15 bar (or the first hr range) and ride it with ATR geometry.
def london_momentum(symbols, london_start_h, lookwin, stop_m, tgt_m, maxbars):
    trades=[]
    for sym in symbols:
        T,B,A=load_m15(sym); cost=w1.cost_for(sym)
        byday=defaultdict(list)
        for i,t in enumerate(T): byday[t.date()].append(i)
        for day,idxs in byday.items():
            lon=[i for i in idxs if T[i].hour>=london_start_h]
            if len(lon)<lookwin+2: continue
            # impulse over first lookwin bars of london
            i0=lon[0]
            if i0<20: continue
            iw=lon[lookwin-1]
            a=A[iw]
            if a<=0: continue
            d=1 if B[iw].c>B[i0].o else -1
            r=simulate(B,iw,d,stop_dist=stop_m*a,target_dist=tgt_m*a,maxbars=maxbars,cost=cost)
            trades.append(wins(r))
    return trades

print('=== B: London-open momentum continuation (M15, forward-only) ===')
for ls in [7,8]:
    for lw in [2,4]:
        for sm,tm in [(1.0,1.5),(1.0,2.0),(1.5,2.0)]:
            for grp,name in [(FXSYMS,'FX'),(JPY,'JPY')]:
                t=london_momentum(grp,ls,lw,sm,tm,40)
                R,n,w=rep(t)
                if n<150: continue
                flag='<<<' if R>0 else ''
                print(f'{name} lon{ls} lw{lw} s{sm}/t{tm}: FWD {R:+.3f} n{n:4d} w{w}% {flag}')
